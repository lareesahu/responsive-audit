# Device ladder — what to actually test

Widths in CSS pixels. The ladder runs from the reflow floor to the widest display in use, because a
layout has two failure directions. Test the ends first: Apple's own guidance is to preview the largest and
the smallest layouts, since the middle sizes inherit whichever ones you fix.

## Width classes (Android / Material, the cleanest published ladder)

| Class | Width | What it means in practice |
|---|---|---|
| Compact | < 600 | one column, stacked, thumb reach |
| Medium | 600–839 | two columns start to fit; tablet portrait |
| Expanded | 840–1199 | persistent side rail, 2–3 columns |
| Large | 1200–1599 | laptop; full nav, 3–4 columns |
| Extra-large | ≥ 1600 | desktop display; density, 4+ columns, wider measures |

Apple splits the same space into size classes that follow the *window* rather than the device: an iPad in
Split View is compact width, a Slide Over panel is even narrower, and a Mac window can be dragged from
phone width to ultrawide. Design for the window, not for the product name.

## The ladder

| Width | Represents | Why it is on the list |
|---|---|---|
| **320** | iPhone SE 1st gen, WCAG reflow floor, 1280 at 400% zoom | Hard floor. Failing here fails SC 1.4.10. |
| **375** | iPhone SE 2/3, 13 mini | Smallest phone most people still hold. |
| **390** | iPhone 12–14 | The modal iPhone size — always screenshot it. |
| **393 / 402** | iPhone 15/16, 16 Pro | Catches rules keyed to exactly 390. |
| **430** | iPhone 16 Pro Max | Catches rules keyed to a `max-width: 400px`. |
| **600** | small tablet / large foldable | Compact→medium boundary. |
| **768** | iPad portrait | Where rows want to become columns. |
| **834 / 1024** | iPad landscape, small laptop | Sticky sidebars and 2-column heroes usually break here. |
| **1280** | laptop | Default desktop design width. |
| **1440** | desktop | Delivery screenshot width. |
| **1920** | 1080p display | First width where a 1200 px column looks lost. |
| **2560** | 1440p / QHD | Measure and density problems become obvious. |
| **3440** | ultrawide | Line length, plateaued grids, dead margins. |
| **3840** | 4K at 100% scale | Pixel upscaling, type that stopped scaling. |

Minimum gate: **320, 375, 390, 430, 768, 1024, 1440, 1920, 2560**. Add 3440 for anything with a hero or a
full-bleed band, and 600 for tablet-led products.

## Height also matters

- **844** — iPhone 12–16 default.
- **667** — iPhone SE: bottom bars lose their safe area, heroes clip.
- **480 landscape** — a 390 px tall viewport defeats `100vh` heroes and full-screen modals.
- **1080 / 1440** — desktop heights; a 1440 wide × **short** window is the common laptop case and breaks
  sticky columns that assume vertical room.

## Wide-specific checks (the numbers)

| Check | Threshold | Source |
|---|---|---|
| Characters per line | ≤ 80 (≤ 40 CJK) | WCAG 1.4.8 |
| Content width at ≥ 1600 | at least ~60% of the viewport, or a deliberate column with a real second region | Apple layout guides / readable width |
| Rendered image width | ≤ 1.05 × natural width at the device pixel ratio | else it is upscaled |
| Body type at ≥ 1920 | scales with the layout (`clamp()`), not frozen at phone size | readability |
| Navigation | expands to a real nav by 1024; no hamburger on a desktop | affordance |
| Grid columns | grow with `auto-fit`/`minmax()` rather than staying 3-wide at 2560 | density |

## What each width check must produce

1. No horizontal scrollbar (`scrollWidth` ≤ `innerWidth`).
2. No element crossing either edge.
3. No text clipped by a fixed height.
4. Every interactive target ≥ 44 px, never < 24 px.
5. Body text ≥ 16 px, inputs ≥ 16 px.
6. No line longer than the measure limit.
7. No image rendered wider than its own pixels.
8. A screenshot at that width, reviewed by eye at 320, 390, 768, 1440 and one wide frame.
