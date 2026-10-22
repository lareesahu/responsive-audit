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

DEFAULT_WIDTHS = [320, 375, 390, 430, 768, 1024, 1280, 1440]

# Real device sizes (CSS px). Height matters: a 667px SE breaks designs a 932px Pro Max hides.
SIZE_PRESETS = {
    "iphone": [(375, 667), (390, 844), (430, 932)],          # SE 2/3, 13, 16 Pro Max
    "duo": [(375, 667), (430, 932)],                         # the two-phone comparison
    "phone+tablet": [(390, 844), (768, 1024)],
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

  const offenders = [], clipped = [], small = [], tiny = [], zoomers = [], distorted = [];
  const nodes = document.querySelectorAll('body *');
  const limit = Math.min(nodes.length, 5000);

  for (let i = 0; i < limit; i++) {
    const el = nodes[i];
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect(), s = cs(el);

    if ((r.right > vw + 1 || r.left < -1) && !inScroller(el)) {
      offenders.push({ sel: pathOf(el), left: Math.round(r.left), right: Math.round(r.right),
        width: Math.round(r.width), text: textOf(el) });
    }

    const hasText = el.childNodes && Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 3);
    if (hasText) {
      if (el.scrollHeight > el.clientHeight + 2 && (s.overflowY === 'hidden' || s.overflowY === 'clip')) {
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
      if (w && h && !inlineInText && (w < 44 || h < 44)) {
        small.push({ sel: pathOf(el), w, h, text: textOf(el),
          label: el.getAttribute('aria-label') || '', severe: (w < 24 || h < 24) });
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
    clipped: dedupe(clipped, x => x.sel).slice(0, 10),
    small: dedupe(small, x => x.sel + x.w + x.h).slice(0, 20),
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
                page.goto(url, wait_until="load", timeout=45000)
                try:
                    page.wait_for_load_state("networkidle", timeout=6000)
                except Exception:
                    pass
                settle(page, wait_ms)
                data = page.evaluate(PROBE, w)
                data["target"] = url
                if shots:
                    shot = out_dir / f"{slug}_{w}.png"
                    page.screenshot(path=str(shot), full_page=True)
                    data["screenshot"] = str(shot)
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
    if row.get("overflow", 0) > 1:
        fails.append(f"overflow +{row['overflow']}px")
    if row.get("viewportExpanded", 0) > 1:
        fails.append(f"layout widened {row['viewportExpanded']}px")
    if row.get("clipped"):
        fails.append(f"{len(row['clipped'])} clipped")
    if row.get("zoomRisk") and row["width"] <= 430:
        fails.append(f"{len(row['zoomRisk'])} input<16px")
    if row.get("distorted"):
        fails.append(f"{len(row['distorted'])} distorted img")
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

    head = f"{'w':>5} {'overflow':>9} {'clip':>5} {'<44px':>6} {'<24px':>6} {'tiny':>5} {'zoom':>5} {'img':>4}  verdict"
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
              f"{len(row.get('zoomRisk', [])):>5} {len(row.get('distorted', [])):>4}  "
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
                           ("distorted images", "distorted")):
            for item in row.get(key, [])[:4]:
                print(f"  {label}: {item}")
        bad = [t for t in row.get("small", []) if t.get("severe")][:4]
        for t in bad:
            print(f"  target <24px: {t['w']}x{t['h']} {t['sel']} {t['text'][:40]}")
        if row.get("hasDeviceWidth") is False:
            print(f"  viewport meta: {row.get('viewportMeta')!r}")

    print(f"\nJSON: {json_path}")
    print(f"Screenshots: {out_dir}")
    print(f"{len(rows) - failures}/{len(rows)} widths pass in {time.time() - started:.1f}s")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
