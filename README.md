# PKMHD Icons

An MKBHD **"Icons"**-style wallpaper generator using retro video game creature sprites.

Downloads pixel art sprites from a public sprite database, converts them into subtle dark silhouettes, and arranges them in a staggered brick-pattern grid on a gradient background — just like the iconic MKBHD wallpaper, but with pocket monsters.

![Example wallpaper preview](preview.png)

## Quick Start

```bash
# Install the one dependency
pip install Pillow requests

# Generate the wallpaper
python pkmhd_icons.py
```

The wallpaper will be saved as `pkmhd_icons_wallpaper.png` in the same directory.

Sprites are cached locally in `sprite_cache/` after the first run, so subsequent runs are much faster.

## Configuration

All options are at the top of `pkmhd_icons.py`. No command-line args needed — just edit and re-run.

### Output

| Variable | Default | Description |
|---|---|---|
| `WALLPAPER_WIDTH` | `3840` | Output width in pixels |
| `WALLPAPER_HEIGHT` | `2160` | Output height in pixels |

### Sprite Grid

| Variable | Default | Description |
|---|---|---|
| `ICON_SIZE` | `36` | Sprite size in pixels |
| `GRID_SPACING_X` | `64` | Horizontal spacing between sprite centers |
| `GRID_SPACING_Y` | `58` | Vertical spacing between sprite centers |
| `ROW_OFFSET` | `32` | Brick-pattern stagger offset for alternating rows |

### Sprite Appearance

| Variable | Default | Description |
|---|---|---|
| `ICON_BRIGHTNESS` | `52` | Silhouette brightness (0 = invisible, 255 = full) |
| `ICON_COLOR` | `(255, 255, 255)` | Silhouette tint as RGB tuple — try `(0, 255, 100)` for green! |

### Background Gradient

| Variable | Default | Description |
|---|---|---|
| `GRADIENT_TYPE` | `"radial"` | `"none"`, `"radial"`, `"linear"`, or `"diagonal"` |
| `GRADIENT_COLOR_CENTER` | `(38, 38, 42)` | Center/start color |
| `GRADIENT_COLOR_EDGE` | `(18, 18, 20)` | Edge/end color |
| `LINEAR_GRADIENT_ANGLE` | `90` | Degrees for linear gradient (0=left→right, 90=top→bottom) |

### Vignette

| Variable | Default | Description |
|---|---|---|
| `VIGNETTE_STRENGTH` | `0.15` | Edge darkening (0.0 = off, 1.0 = full black at corners) |

## Examples

**Default (dark charcoal, subtle gray sprites):**
```python
ICON_COLOR = (255, 255, 255)
GRADIENT_COLOR_CENTER = (38, 38, 42)
GRADIENT_COLOR_EDGE = (18, 18, 20)
```

**Green on pink:**
```python
ICON_COLOR = (0, 255, 100)
GRADIENT_COLOR_CENTER = (60, 20, 40)
GRADIENT_COLOR_EDGE = (30, 10, 20)
```

**Blue ice:**
```python
ICON_COLOR = (100, 180, 255)
GRADIENT_COLOR_CENTER = (15, 20, 35)
GRADIENT_COLOR_EDGE = (5, 8, 18)
```

## Requirements

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/)
- [Requests](https://pypi.org/project/requests/)

## License

MIT
