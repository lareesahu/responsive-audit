#!/usr/bin/env python3
"""Measure real responsive geometry at every width in the ladder.

    python responsive_audit.py --url http://127.0.0.1:5173 --out ./audit
    python responsive_audit.py --url https://example.com --widths 320,390,768,1440

Checks per width: horizontal overflow (and the element causing it), text clipped by fixed heights,
interactive targets under 44px / under 24px, inputs that trigger iOS zoom-on-focus, images distorted by
`object-fit: fill`, tiny type, fixed chrome eating the viewport, and the viewport meta tag.
Writes screenshots + report.json, prints a table, exits 1 when the gate fails.

Requires: playwright (python -m playwright install chromium once).
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_WIDTHS = [320, 375, 390, 430, 768, 1024, 1440, 1920, 2560]

# Real device sizes (CSS px). Height matters: a 667px SE breaks designs a 932px Pro Max hides.
# CSS viewports (device pixels / DPR 3), verified against Apple's published specs, Oct 2026.
SIZE_PRESETS = {
    # iPhone Duo: one physical device, two live layouts. Closed = 5.4" outer display
    # (1398x2034 @460ppi); open = 7.6" inner folding display (1878x2670 @430ppi).
    # A responsive page must survive both, and both again rotated.
    "duo": [(466, 678), (626, 890)],                      # closed, open
    "duo-land": [(678, 466), (890, 626)],                 # closed, open, rotated
    "iphone": [(402, 874), (440, 956)],                   # 18 Pro, 18 Pro Max
    "phone+tablet": [(440, 956), (768, 1024)],
    "wide": [(1440, 900), (1920, 1080), (2560, 1440), (3440, 1440)],   # laptop to ultrawide
    "full": [(320, 568), (466, 678), (626, 890), (768, 1024),
             (1024, 768), (1440, 900), (1920, 1080), (2560, 1440)],
}

PROBE = r"""(vwExpected) => {
  const vh = window.innerHeight;
  // Mobile emulation can widen the layout viewport to fit fixed-width content; measure against the
  // width we asked for, and record the difference, or overflow silently reads as zero.
  const reported = window.innerWidth;
  const vw = vwExpected || reported;
  const de = document.documentElement;
  const scrollW = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0);
  const overflow = scrollW - vw;

  const styleCache = new Map();
  const cs = (el) => { if (!styleCache.has(el)) styleCache.set(el, getComputedStyle(el)); return styleCache.get(el); };
  const visible = (el) => {
    const r = el.getBoundingClientRect(), s = cs(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'
      && parseFloat(s.opacity || '1') > 0.01 && r.bottom > -vh * 4;
  };
  const pathOf = (el) => {
    const parts = [];
    let n = el, depth = 0;
    while (n && n.nodeType === 1 && depth < 4) {
      let s = n.tagName.toLowerCase();
      if (n.id && /^[A-Za-z]/.test(n.id)) { parts.unshift('#' + n.id); break; }
      const cls = (n.className && typeof n.className === 'string') ? n.className.trim().split(/\s+/)[0] : '';
      if (cls) s += '.' + cls;
      parts.unshift(s); n = n.parentElement; depth++;
    }
    return parts.join(' > ');
  };
  const inScroller = (el) => {
    let n = el.parentElement;
    while (n && n !== document.body) {
      const ox = cs(n).overflowX;
      if (ox === 'auto' || ox === 'scroll') return true;
      n = n.parentElement;
    }
    return false;
  };
  const textOf = (el) => (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 70);

  const offenders = [], clippedByAncestor = [], clipped = [], small = [], tiny = [], zoomers = [], distorted = [];
  let unmeasured = 0;
  const nodes = document.querySelectorAll('body *');
  const limit = Math.min(nodes.length, 5000);

  for (let i = 0; i < limit; i++) {
    const el = nodes[i];
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect(), s = cs(el);

    if ((r.right > vw + 1 || r.left < -1) && !inScroller(el)) {
      const item = { sel: pathOf(el), left: Math.round(r.left), right: Math.round(r.right),
        width: Math.round(r.width), text: textOf(el) };
      // An element wider than the viewport inside an overflow:hidden parent is clipped, not scrollable.
      // It still matters (content may be cut off) but it is not what makes the page scroll sideways.
      let hiddenAncestor = false, n = el.parentElement;
      while (n && n !== document.body) {
        const ox = cs(n).overflowX;
        if (ox === 'hidden' || ox === 'clip') { hiddenAncestor = true; break; }
        n = n.parentElement;
      }
      (hiddenAncestor ? clippedByAncestor : offenders).push(item);
    }

    const hasText = el.childNodes && Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 3);
    if (hasText) {
      if (el.scrollHeight > el.clientHeight + 2 && (s.overflowY === 'hidden' || s.overflowY === 'clip')
          && el.clientHeight >= 8 && el.clientWidth >= 8) {
        clipped.push({ sel: pathOf(el), client: el.clientHeight, scroll: el.scrollHeight, text: textOf(el) });
      }
      const fs = parseFloat(s.fontSize);
      if (fs && fs < 12 && r.width > 8) tiny.push({ sel: pathOf(el), px: +fs.toFixed(1), text: textOf(el) });
    }

    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute('role') || '';
    const interactive = ['a', 'button', 'select', 'textarea', 'summary'].includes(tag)
      || (tag === 'input' && (el.getAttribute('type') || 'text') !== 'hidden')
      || ['button', 'link', 'tab', 'menuitem', 'checkbox', 'switch'].includes(role)
      || el.hasAttribute('onclick') || el.hasAttribute('tabindex') && el.getAttribute('tabindex') !== '-1';
    if (interactive) {
      const w = Math.round(r.width), h = Math.round(r.height);
      // WCAG 2.5.8 exempts targets inside a sentence; a link whose box is inline text is not a control.
      const inlineInText = s.display === 'inline' && !!el.closest('p, li, dd, td, span, small, figcaption');
      const pending = Array.from(el.querySelectorAll('img')).some(im => im.naturalWidth === 0 && im.loading !== 'lazy');
      if (pending) { unmeasured++; }
      else if (w && h && !inlineInText && (w < 44 || h < 44)) {
        const name = (el.getAttribute('aria-label') || el.textContent || '').trim();
        const hasGlyph = !!el.querySelector('img, svg, i, picture');
        const iconOnly = !name && hasGlyph;
        // Hard failure is reserved for controls a user must hit: form fields, buttons, icon-only buttons.
        // A small text or logo link is a real finding, but it is advisory, not a broken page.
        const control = ['button', 'input', 'select', 'textarea'].includes(tag) || role === 'button';
        small.push({ sel: pathOf(el), w, h, text: name.slice(0, 40), iconOnly,
          severe: (control && (w < 24 || h < 24)) || (w < 24 && h < 24 && !iconOnly && !name) });
      }
    }

    if (['input', 'select', 'textarea'].includes(tag)) {
      const fs = parseFloat(s.fontSize);
      if (fs && fs < 16) zoomers.push({ sel: pathOf(el), px: +fs.toFixed(1), type: el.getAttribute('type') || tag });
    }

    if (tag === 'img' && el.naturalWidth > 0 && s.objectFit !== 'cover' && s.objectFit !== 'contain'
        && s.width !== 'auto' && s.height !== 'auto' && r.width >= 40 && r.height >= 16) {
      const natural = el.naturalWidth / el.naturalHeight;
      const shown = r.width / r.height;
      // small logos round to whole px, so allow 8% before calling it a squash
      if (natural && shown && Math.abs(natural - shown) / natural > 0.08) {
        distorted.push({ sel: pathOf(el), natural: +natural.toFixed(2), shown: +shown.toFixed(2),
          px: Math.round(r.width) + 'x' + Math.round(r.height) });
      }
    }
  }

  let fixedArea = 0;
  document.querySelectorAll('body *').forEach((el) => {
    if (cs(el).position !== 'fixed') return;
    const r = el.getBoundingClientRect();
    if (r.width && r.height) fixedArea = Math.max(fixedArea, (r.width * r.height) / (vw * vh));
  });

  // --- wide-screen checks -------------------------------------------------
  // 1. Measure: WCAG 1.4.8 caps a line of text at 80 characters (40 for CJK). A layout that simply
  //    stretches at 2560px breaks readability without breaking any box.
  const longs = [];
  document.querySelectorAll('p, li, blockquote, dd, figcaption, article div').forEach((el) => {
    if (longs.length > 120) return;
    const txt = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (txt.length < 140) return;
    if (el.querySelector('p, div, li, table, ul, ol')) return;
    const r = el.getBoundingClientRect();
    if (r.width < 200) return;
    try {
      const range = document.createRange();
      range.selectNodeContents(el);
      const rects = Array.from(range.getClientRects()).filter(x => x.width > 4 && x.height > 4);
      if (rects.length < 2) return;
      const tops = new Set(rects.map(x => Math.round(x.top)));
      const lines = tops.size;
      if (lines < 3) return;
      const cjk = (txt.match(/[\u3040-\u30ff\u3400-\u9fff]/g) || []).length / txt.length;
      const perLine = txt.length / lines;
      longs.push({ sel: pathOf(el), perLine: Math.round(perLine), lines,
        limit: cjk > 0.3 ? 40 : 80, width: Math.round(r.width) });
    } catch (e) {}
  });

  // 2. Pixels: an image stretched past its natural width is blurry, however tidy the box looks.
  const upscaled = [];
  document.querySelectorAll('img').forEach((el) => {
    if (!el.naturalWidth || el.naturalWidth < 40) return;
    const r = el.getBoundingClientRect();
    if (!r.width) return;
    const ratio = (r.width * (window.devicePixelRatio || 1)) / el.naturalWidth;
    if (ratio > 1.05) {
      upscaled.push({ sel: pathOf(el), shownWidth: Math.round(r.width), natural: el.naturalWidth,
        ratio: +ratio.toFixed(2) });
    }
  });

  // 3. Where the content actually ends. Full-bleed art is legitimate, so this measures the extent of
  //    every visible text block and image rather than trusting a wrapper's own width.
  let deadMargin = 0, deadRight = 0, contentWidth = vw, textCol = 0;
  if (document.body) {
    let minL = 1e9, maxR = -1e9;
    const paras = [];
    document.querySelectorAll('h1, h2, h3, h4, p, li, img, button, a, table, figure, video').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 40 || r.height < 8) return;
      const st = getComputedStyle(el);
      if (st.visibility === 'hidden' || st.display === 'none' || +st.opacity === 0) return;
      if (r.bottom < -2000 || r.top > 20000) return;
      minL = Math.min(minL, r.left + window.scrollX);
      maxR = Math.max(maxR, r.right + window.scrollX);
      if (el.tagName === 'P') paras.push(Math.round(r.width));
    });
    if (maxR > minL) {
      contentWidth = Math.round(maxR - minL);
      deadMargin = Math.round(Math.max(0, minL));
      deadRight = Math.round(Math.max(0, vw - maxR));
    }
    if (paras.length) {
      paras.sort((a, b) => a - b);
      textCol = paras[Math.floor(paras.length / 2)];
    }
  }

  const meta = document.querySelector('meta[name="viewport"]');
  const metaContent = meta ? meta.getAttribute('content') || '' : '';

  const dedupe = (arr, key) => {
    const seen = new Set();
    return arr.filter((x) => { const k = key(x); if (seen.has(k)) return false; seen.add(k); return true; });
  };

  return {
    width: vw, reportedWidth: reported, viewportExpanded: Math.max(0, reported - vw),
    height: vh, overflow,
    offenders: dedupe(offenders, x => x.sel).slice(0, 12),
    clippedByAncestor: dedupe(clippedByAncestor, x => x.sel).slice(0, 8),
    clipped: dedupe(clipped, x => x.sel).slice(0, 10),
    small: dedupe(small, x => x.sel + x.w + x.h).slice(0, 20),
    unmeasured,
    longLines: longs.slice(0, 8),
    upscaledImages: upscaled.slice(0, 8),
    contentWidth, deadMargin, deadRight, textCol,
    tiny: dedupe(tiny, x => x.sel).slice(0, 8),
    zoomRisk: dedupe(zoomers, x => x.sel).slice(0, 8),
    distorted: dedupe(distorted, x => x.sel).slice(0, 8),
    fixedCoverage: +fixedArea.toFixed(2),
    viewportMeta: metaContent,
    hasDeviceWidth: /width\s*=\s*device-width/i.test(metaContent),
    hasCover: /viewport-fit\s*=\s*cover/i.test(metaContent),
    bodyBg: getComputedStyle(document.body).backgroundColor,
  };
}"""


def settle(page, wait_ms):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(150)
    page.evaluate("""async () => {
      const step = Math.max(400, Math.round(window.innerHeight * 0.9));
      const max = document.documentElement.scrollHeight;
      for (let y = 0; y < max; y += step) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
      window.scrollTo(0, 0);
      await Promise.all(Array.from(document.images).filter(i => !i.complete)
        .map(i => new Promise(r => { i.onload = i.onerror = r; setTimeout(r, 2500); })));
      if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch (e) {} }
    }""")
    page.wait_for_timeout(wait_ms)


def audit(url, sizes, out_dir, wait_ms, shots):
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    slug = url.split('://')[-1].split('/')[0].replace(':', '_')
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for (w, h) in sizes:
            ctx = browser.new_context(
                viewport={"width": w, "height": h},
                is_mobile=w <= 430,
                has_touch=w <= 430,
                device_scale_factor=1,
            )
            page = ctx.new_page()
            try:
                try:
                    page.goto(url, wait_until="load", timeout=45000)
                except Exception:
                    # heavy pages and third-party beacons miss `load`; DOM + settle is enough to measure
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=6000)
                except Exception:
                    pass
                settle(page, wait_ms)
                data = page.evaluate(PROBE, w)
                data["target"] = url
                if shots:
                    shot = out_dir / f"{slug}_{w}.png"
                    try:
                        page.screenshot(path=str(shot), full_page=True, timeout=90000)
                        data["screenshot"] = str(shot)
                    except Exception as exc:
                        data["screenshot_error"] = str(exc)[:160]
            except Exception as exc:
                data = {"width": w, "target": url, "error": str(exc)[:300]}
            finally:
                ctx.close()
            results.append(data)
            print(f"  measured {w}px", flush=True)
        browser.close()
    return results


# Hard failures are things that break the page for a real user.
# Advisory findings (tiny eyebrow text, targets under 44px in desktop layouts, a tall sticky header)
# are reported but do not fail the gate on their own unless touch is the primary input.


def verdicts(row, strict_touch=False):
    if row.get("error"):
        return False, ["error"]
    fails = []
    if (row.get("overflow") or 0) > 1:
        fails.append(f"overflow +{row['overflow']}px")
    if (row.get("viewportExpanded") or 0) > 1:
        fails.append(f"layout widened {row['viewportExpanded']}px")
    if row.get("clipped"):
        fails.append(f"{len(row['clipped'])} clipped")
    if row.get("zoomRisk") and row["width"] <= 430:
        fails.append(f"{len(row['zoomRisk'])} input<16px")
    if row.get("distorted"):
        fails.append(f"{len(row['distorted'])} distorted img")
    for ln in row.get("longLines", []):
        if ln["perLine"] > ln["limit"] * 1.25:
            fails.append(f"{ln['perLine']} chars/line")
            break
    for im in row.get("upscaledImages", []):
        if im["ratio"] > 1.25:
            fails.append(f"image upscaled {im['ratio']}x")
            break
    severe = [t for t in row.get("small", []) if t.get("severe")]
    if severe and (row["width"] <= 768 or strict_touch):
        fails.append("target<24px")
    if row.get("hasDeviceWidth") is False and row.get("viewportMeta") is not None:
        fails.append("viewport meta")
    return (not fails), fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="page to audit")
    ap.add_argument("--widths", default=None,
                    help="comma separated widths, desktop height assumed (default ladder)")
    ap.add_argument("--sizes", default=None, help="explicit WxH pairs, e.g. 375x667,430x932")
    ap.add_argument("--devices", default=None, help="preset: iphone, duo, phone+tablet")
    ap.add_argument("--out", default="audit")
    ap.add_argument("--wait", type=int, default=600, help="ms to wait after scrolling, per width")
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    if args.sizes:
        sizes = []
        for pair in str(args.sizes).split(","):
            if not pair.strip():
                continue
            w, h = pair.lower().split("x")
            sizes.append((int(w), int(h)))
    elif args.devices:
        key = str(args.devices).strip().lower()
        if key not in SIZE_PRESETS:
            ap.error(f"unknown preset {key}; choose from {', '.join(SIZE_PRESETS)}")
        sizes = SIZE_PRESETS[key]
    else:
        widths = [int(w) for w in str(args.widths or ",".join(str(x) for x in DEFAULT_WIDTHS)).split(",") if w.strip()]
        sizes = [(w, 844 if w <= 430 else (1024 if w <= 1024 else 900)) for w in widths]

    out_dir = Path(args.out)
    started = time.time()
    label = ", ".join(f"{w}x{h}" for w, h in sizes)
    print(f"Auditing {args.url} at {label}")

    rows = audit(args.url, sizes, out_dir, args.wait, not args.no_shots)
    widths = [w for w, _ in sizes]

    report = {"url": args.url, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "engine": "chromium emulation", "widths": widths,
              "sizes": [{"width": w, "height": h} for w, h in sizes], "results": rows}
    json_path = Path(args.json) if args.json else out_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    head = f"{'w':>5} {'overflow':>9} {'clip':>5} {'<44px':>6} {'<24px':>6} {'tiny':>5} {'zoom':>5} {'img':>4} {'long':>5} {'up':>3}  verdict"
    print("\n" + head)
    print("-" * len(head))
    failures = 0
    for row in rows:
        ok, fails = verdicts(row)
        if not ok:
            failures += 1
        severe = sum(1 for t in row.get("small", []) if t.get("severe"))
        print(f"{row['width']:>5} {row.get('overflow', 0):>9} {len(row.get('clipped', [])):>5} "
              f"{len(row.get('small', [])):>6} {severe:>6} {len(row.get('tiny', [])):>5} "
              f"{len(row.get('zoomRisk', [])):>5} {len(row.get('distorted', [])):>4} "
              f"{max([l['perLine'] for l in row.get('longLines', [])], default=0):>5} "
              f"{len(row.get('upscaledImages', [])):>3}  "
              + ("PASS" if ok else "FAIL " + "; ".join(fails)))
    print("\nADVISORY (reported, does not fail the gate): targets under 44px, type under 12px, "
          "fixed chrome over 35% of the viewport.")

    for row in rows:
        if verdicts(row)[0]:
            continue
        print(f"\n--- {row['width']}px detail ---")
        if row.get("error"):
            print("  error:", row["error"])
            continue
        for label, key in (("overflows", "offenders"), ("clipped", "clipped"),
                           ("tiny text", "tiny"), ("inputs <16px", "zoomRisk"),
                           ("distorted images", "distorted"), ("long lines", "longLines"),
                           ("upscaled images", "upscaledImages")):
            for item in row.get(key, [])[:4]:
                print(f"  {label}: {item}")
        bad = [t for t in row.get("small", []) if t.get("severe")][:4]
        for t in bad:
            print(f"  target <24px: {t['w']}x{t['h']} {t['sel']} {t['text'][:40]}")
        if row.get("hasDeviceWidth") is False:
            print(f"  viewport meta: {row.get('viewportMeta')!r}")
        if row.get("deadMargin"):
            print(f"  content {row.get('contentWidth')}px of {row['width']}px "
                  f"({row['deadMargin']}px dead each side)")

    # does the layout actually change at all once it has room? A column that stops growing is a
    # decision — fine for prose, a waste on a 3440px display — so name it rather than guess.
    capped = [r for r in rows if r.get("contentWidth")]
    if len(capped) >= 2:
        widest = max(capped, key=lambda r: r["width"])
        narrowest = min(capped, key=lambda r: r["width"])
        if widest["width"] >= 1600 and abs(widest["contentWidth"] - narrowest["contentWidth"]) <= 12:
            print(f"\nNOTE layout plateaus: content spans {narrowest['contentWidth']}px at "
                  f"{narrowest['width']}px and {widest['contentWidth']}px at {widest['width']}px "
                  f"({widest.get('deadMargin', 0)}px dead left, {widest.get('deadRight', 0)}px right). "
                  f"Fine for prose, a waste for anything that could add columns.")
        tc = [r for r in rows if r.get("textCol")]
        if tc:
            w = max(tc, key=lambda r: r["width"])
            if w["width"] >= 1600 and w["textCol"] and w["textCol"] / w["width"] < 0.45:
                print(f"NOTE text column is {w['textCol']}px on a {w['width']}px screen "
                      f"({round(100 * w['textCol'] / w['width'])}%) — readable, but check the layout is composed, "
                      f"not just centred.")

    print(f"\nJSON: {json_path}")
    print(f"Screenshots: {out_dir}")
    print(f"{len(rows) - failures}/{len(rows)} widths pass in {time.time() - started:.1f}s")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
