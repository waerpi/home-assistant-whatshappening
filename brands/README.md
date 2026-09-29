# Brand assets

`icon.svg` and `logo.svg` are the masters — change those, never the PNGs.
`export.py` renders them into `custom_components/whatshappening/brand/`, which
is where Home Assistant looks.

## The mark

A clock whose ring is open towards the upper right, with the hand pointing out
through the gap into three dots that shrink and fade: the next few minutes, more
certain up close than further out. Gradient `#1E63FF → #16C9F0`, white glyph, so
it holds up on both the light and the dark Home Assistant theme.

## Where the images live

Since Home Assistant 2026.3.0 a custom integration ships its own brand images.
The `brands` integration serves them straight from the component folder:
`Integration.has_branding` is true when the component has a top-level `brand`
directory, and `homeassistant/components/brands` then reads
`custom_components/whatshappening/brand/<image>.png`, falling back to the
brands CDN only for domains that have none.

So the four images belong in `custom_components/whatshappening/brand/`:

| File | Size |
| --- | --- |
| `icon.png` | 256×256 |
| `icon@2x.png` | 512×512 |
| `logo.png` | 697×256 |
| `logo@2x.png` | 1394×512 |

Dark-theme variants (`dark_icon.png`, `dark_logo.png` and their `@2x` versions)
are possible but unnecessary here: the badge carries its own background and
reads on either theme.

## Not a pull request to home-assistant/brands

`home-assistant/brands` **no longer accepts custom integrations**. Its
`custom_integrations/` folder is legacy, and
`.github/workflows/close-new-custom-integrations.yml` automatically comments on
and closes any pull request that adds a folder there. Nothing has to be
submitted anywhere — shipping `brand/` in this repository is the whole job.

## Re-exporting

```bash
pip install cairosvg pillow pyoxipng
python3 brands/export.py
```

Sizes follow the brand image specification in
[home-assistant/brands](https://github.com/home-assistant/brands): the icon is
square at 256 and 512 pixels, and the logo's *shortest* side is 256 and 512 —
the maximum the specification allows, which it prefers. The images are trimmed
to their content and losslessly optimized.
