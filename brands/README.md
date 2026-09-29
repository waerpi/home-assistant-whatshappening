# Brand assets

Source and exports for the `whatshappening` icon and logo.

| File | Size | Goes to |
| --- | --- | --- |
| `icon.png` | 256×256 | `custom_integrations/whatshappening/icon.png` |
| `icon@2x.png` | 512×512 | `custom_integrations/whatshappening/icon@2x.png` |
| `logo.png` | 256×94 | `custom_integrations/whatshappening/logo.png` |
| `logo@2x.png` | 512×188 | `custom_integrations/whatshappening/logo@2x.png` |

`icon.svg` and `logo.svg` are the masters — change those, never the PNGs.

## The mark

A clock whose ring is open towards the upper right, with the hand pointing out
through the gap into three dots that shrink and fade: the next few minutes, more
certain up close than further out. Gradient `#1E63FF → #16C9F0`, white glyph, so
it holds up on both the light and the dark Home Assistant theme.

## Re-exporting

```bash
pip install cairosvg pillow
python3 export.py
```

## Submitting to home-assistant/brands

The images have to live in [home-assistant/brands][brands], not here — the
frontend loads them from `brands.home-assistant.io`.

Fork the repository on GitHub, then, from a clone of *this* repository:

```bash
git clone git@github.com:<you>/brands.git ../brands
cd ../brands
git checkout -b whatshappening
mkdir -p custom_integrations/whatshappening
cp ../home-assistant-whatshappening/brands/{icon,icon@2x,logo,logo@2x}.png \
   custom_integrations/whatshappening/
git add custom_integrations/whatshappening
git commit -m "Add What's happening next? brand assets"
git push -u origin whatshappening
```

Then open the pull request against `home-assistant/brands`, titled
`Add What's happening next? (whatshappening)`. Their CI checks the sizes and
that the domain resolves to a real integration, so nothing else is needed.

Once it is merged, drop the `ignore: brands` line from
`.github/workflows/ci.yml` so the HACS check covers it again.

[brands]: https://github.com/home-assistant/brands
