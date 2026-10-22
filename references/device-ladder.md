# Device ladder — what to actually test

Widths in CSS pixels. The ladder runs from the reflow floor to the widest display in use, because a
layout has two failure directions. Test the ends first: Apple's own guidance is to preview the largest and
the smallest layouts, since the middle sizes inherit whichever ones you fix.

Sizes below are device pixels / 3 (iOS DPR), taken from Apple's published technical specifications
(October 2026). Re-check Apple's spec pages when a new iPhone ships — a stale ladder silently tests
devices nobody owns.

## The current iPhone set (verified against Apple specs)

| Device | Pixel resolution | CSS viewport | Note |
|---|---|---|---|
| iPhone 18 Pro | 1206 x 2622 @ 460 ppi | **402 x 874** | smallest current iPhone |
| iPhone 18 Pro Max | 1320 x 2868 @ 460 ppi | **440 x 956** | largest slab iPhone |
| iPhone Duo, closed | 1398 x 2034 @ 460 ppi | **466 x 678** | 5.4" outer display, short |
| iPhone Duo, open | 1878 x 2670 @ 430 ppi | **626 x 890** | 7.6" inner folding display |
| iPhone Duo, open and rotated | - | **890 x 626** | wide but very short; defeats `100vh` heroes |

Retired, no longer a standard target: iPhone SE 2/3 (375 x 667), 13 mini (375 x 812), 12-14 (390 x 844),
15/16 (393 x 852), 16 Pro Max (430 x 932). Keep one only as a *legacy* check when a product still supports
an older iOS floor - never as the definition of "small phone".

## The foldable case (the one people forget)

The iPhone Duo is **one device with two live layouts**, and the page has to hold in both:

1. **Closed (466 x 678).** Wider than the old 375 floor but shorter than any iPhone in years - bottom bars,
   sticky headers, `100vh` heroes and full-screen modals break here first.
2. **Open (626 x 890).** Lands in the Medium window class (600-839). This is the trap: a layout with a single
   `min-width: 768px` breakpoint keeps its phone presentation on a 7.6" screen, so the user unfolds the device
   and gets the same one-column phone view.
3. **Open, rotated (890 x 626).** Wide but short: desktop nav and any `height: 100vh` section clip.

Design rule: if the layout has a real two-column or side-rail state, it must arrive at **626**, not only at
768. If it cannot arrive by 626, say so and state the fallback - never ship the phone layout silently to a
tablet-sized screen.

Emulation limits, stated plainly: Chromium reproduces the viewport, not the hardware. The crease, per-display
safe areas, the under-display camera, hinge handling and app continuity when folding are **unverified** by
this tool. Real-device check required before claiming foldable support.

## Width classes (Android / Material, the cleanest published ladder)

| Class | Width | What it means in practice |
|---|---|---|
| Compact | < 600 | one column, stacked, thumb reach |
| Medium | 600-839 | two columns start to fit; tablet portrait, **open foldable** |
| Expanded | 840-1199 | persistent side rail, 2-3 columns |
| Large | 1200-1599 | laptop; full nav, 3-4 columns |
| Extra-large | >= 1600 | desktop display; density, 4+ columns, wider measures |

Apple splits the same space into size classes that follow the *window* rather than the device: an iPad in
Split View is compact width, a Slide Over panel is even narrower, a Mac window can be dragged from phone
width to ultrawide, and the Duo crosses from compact to medium by being unfolded. Design for the window,
not for the product name.

## The ladder

| Width | Represents | Why it is on the list |
|---|---|---|
| **320** | WCAG reflow floor, 1280 at 400 % zoom | Hard floor. Failing here fails SC 1.4.10. No current iPhone is this narrow, so it is a robustness test, not a device. |
| **402** | iPhone 18 Pro | smallest real iPhone |
| **440** | iPhone 18 Pro Max | catches rules keyed to a `max-width: 400px` |
| **466** | iPhone Duo, closed | short viewport, bottom chrome |
| **600** | compact to medium boundary | the breakpoint an open foldable must have crossed |
| **626** | iPhone Duo, open | the real "phone becomes tablet" case |
| **768** | iPad portrait | where rows want to become columns |
| **834 / 1024** | iPad landscape, small laptop | sticky sidebars and 2-column heroes usually break here |
| **1280** | laptop | default desktop design width |
| **1440** | desktop | delivery screenshot width |
| **1920** | 1080p display | first width where a 1200 px column looks lost |
| **2560** | 1440p / QHD | measure and density problems become obvious |
| **3440** | ultrawide | line length, plateaued grids, dead margins |
| **3840** | 4K at 100 % scale | pixel upscaling, type that stopped scaling |

Minimum gate: **320, 402, 440, 466, 626, 768, 1024, 1440, 1920, 2560**. Add 3440 for anything with a hero
or a full-bleed band. Add the rotated pair (678 x 466, 890 x 626) when the product is used in landscape.

## Height also matters

- **956** - iPhone 18 Pro Max, the tallest slab.
- **678** - iPhone Duo closed: the shortest current viewport. Sticky bars and `100vh` heroes clip.
- **626** - iPhone Duo open, rotated: `100vh` sections and desktop nav overflow.
- **1080 / 1440** - desktop heights; a wide x short window is the common laptop case and breaks sticky
  columns that assume vertical room.

## Wide-specific checks (the numbers)

| Check | Threshold | Source |
|---|---|---|
| Characters per line | <= 80 (<= 40 CJK) | WCAG 1.4.8 |
| Content width at >= 1600 | at least ~60 % of the viewport, or a deliberate column with a real second region | Apple layout guides / readable width |
| Rendered image width | <= 1.05 x natural width at the device pixel ratio | else it is upscaled |
| Body type at >= 1920 | scales with the layout (`clamp()`), not frozen at phone size | readability |
| Navigation | expands to a real nav by 1024; no hamburger on a desktop | affordance |
| Grid columns | grow with `auto-fit`/`minmax()` rather than staying 3-wide at 2560 | density |

## What each size check must produce

1. No horizontal scrollbar (`scrollWidth` <= `innerWidth`).
2. No element crossing either edge.
3. No text clipped by a fixed height.
4. Every interactive target >= 44 px, never < 24 px.
5. Body text >= 16 px, inputs >= 16 px.
6. No line longer than the measure limit.
7. No image rendered wider than its own pixels.
8. A screenshot at that size, reviewed by eye at 466, 626, 1024 and one wide frame.
