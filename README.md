# pixelspark — restaurant landing page (reference rebuild)

Rebuilt **section-for-section from your mockup**, with the hero treated as the centrepiece.

Deliverable: **`index.html`** — one self-contained file (~1.1 MB). The Poppins webfont and all
photography are inlined as data URIs, so it renders identically offline and inside sandboxed
previews without a single network request.

---

## Matched to the reference

Everything below was measured off the mockup rather than eyeballed:

| Item | Reference | Build |
| --- | --- | --- |
| Accent | `#FE9F05` (sampled) | `#FE9F05` → `#FFB02A` gradient on the wedge only |
| Typeface | geometric sans, single-storey `a` | **Poppins** (embedded, 4 weights) |
| Hero wedge | organic curve: 38 % across at the top, bulging to ~78 % then curving to the bottom-right | SVG path traced through 11 sampled boundary points |
| Small plates | cluster of 3 on the far right, descending (18.6 % / 17.5 % / 11 % of the plate area) | same three positions, measured as % of the stage box |
| Big plate | white ceramic plate, thin rim, left of the small plates | one-to-one |
| About | orange tab + **dark plate** of tacos + ketchup bottle on the left, copy right, pill "View more" | same, with the dark plate |
| Most Popular | 3 cards, middle one raised & wider-looking, "Add to cart" pills, stars, prices `$120.4 / $220.4 / $250.4`, 3-dot pager | same, including the raised middle card |
| Why choose | **left-aligned** cards, middle one a tall white card, icons in soft orange circles | same |
| Customers Say | avatar + name + stars + quote, arrows + 3 avatars (3rd highlighted), orange rounded tab with dark plate + bottle on the right | same |
| Footer | **light** (not dark), 4 columns: logo · Opening Hours · Contact us · Subscribe Us with an orange-outlined pill input, plate bottom-left, chicken bottom-right | same |
| Copy | kept verbatim, including the mockup's typos ("mroe", "moe kely") | preserved |

Side-by-side proof: `screenshots/compare-reference-vs-build.png` (hero) and
`screenshots/compare-hero.png`.

---

## The hero interaction

**Swiping / dragging** anywhere on the plate area advances the carousel. The reference shows one
big dish plus three small ones, so the small plates behave as a rotating queue:

- the big plate cross-fades + scales into the next dish,
- each small plate rolls forward one slot, so the next three dishes are always previewed,
- the glass name/price pill animates on every change,
- dots underneath track the position.

Also supported: clicking any small plate, ← → keys, autoplay every 5.6 s (pauses on hover/drag),
and a full `prefers-reduced-motion` fallback.

## Motion elsewhere

Masked line-by-line headline reveal · scroll-progress bar · nav that frosts on scroll with
active-link scrollspy · IntersectionObserver reveals with stagger · parallax on the wedge, tab,
plate and bottle · subtle cursor tilt on cards and plates · animated add-to-cart toasts ·
ripple on the CTA · full-screen clip-path mobile menu.

## Responsive

Verified at 1440 px, 768 px and 390 px. On small screens the hero stacks: plate block on top of
the orange band, copy on white beneath it.

## Push to GitHub

The repo is initialised and committed on `main`. See **[GITHUB.md](GITHUB.md)** for the full
walkthrough — creating a **fine-grained** personal access token (Contents: Read and write),
pushing without ever writing the token to disk, the common error messages, and turning on
GitHub Pages.

Target repo: **https://github.com/amanikanu/must-restaurant-template** (already set as `origin`).

```bash
read -rsp "GitHub token: " GH_TOKEN && export GH_TOKEN && echo
./tools/deploy.sh amanikanu must-restaurant-template
```

## Files

```
index.html                        ← the deliverable
screenshots/                      ← hero, full-page, mobile/tablet, reference comparisons
tools/src-v2.html                 ← readable source (references build/v2/*.webp)
tools/make.py                     ← inlines font + images → index.html
tools/prep_images.py              ← rebuilds build/v2 from assets (incl. the chroma key)
tools/render.py                   ← screenshot helper (Playwright)
tools/deploy.sh                   ← one-shot push with a PAT (no token on disk)
GITHUB.md                         ← token + push walkthrough
build/v2/                         ← optimised webp photography
assets/                           ← original generated image masters
fonts/v2/poppins.css              ← embedded Poppins (base64 woff2)
```

Rebuild after editing the source:

```bash
python3 tools/make.py
```

## Product cutouts (the ketchup bottle)

The bottle is keyed properly rather than by thresholding white:

1. shot on a flat chroma-green backdrop with no floor shadow,
2. the backdrop is flood-filled from the frame edges (4-connected), so only the true
   background is removed — never the white label,
3. the matte is antialiased with a 2 px ramp that **excludes greenish pixels**, so no
   coloured fringe can survive,
4. green de-spill is applied only where the green is strong, so the label stays neutral,
5. the matte is eroded ~1 px and blurred to kill any halo, giving a crisp outline,
6. transparent glass keeps its alpha, so it reads correctly over both the orange tab and white.

`screenshots/qa-ketchup.png` composites the cutout over white, orange and charcoal as proof,
and `screenshots/bottle-about.png` / `bottle-say.png` show it in place in both sections.
Re-key at any time with `python3 tools/prep_images.py`.

## Known deltas (asset-limited, not layout)

- Food photos are AI-generated stand-ins styled to match the mockup's framing. The reference's
  exact dishes aren't reproducible, so the specific plates differ while position, size and shape match.
- The mockup's leftover carousel dots directly under the section heading (leftover from its own
  artboard) sit above *Why choose* here too, since you asked for the layout as drawn.
