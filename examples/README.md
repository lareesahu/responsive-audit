# Examples

`broken-page.html` fails every check on purpose: a fixed 520px block, a rigid two-column row, text clipped
by a 40px box, a 12px input that makes iOS zoom, a squashed image, and an 18px button.

```bash
python scripts/responsive_audit.py --url "file://$PWD/examples/broken-page.html" --sizes 320x568,390x844
```

Expected: overflow at both widths, with the offending selectors named. Use it to confirm the tool works
after changing it — if this page ever passes, the detector is broken, not the page.
