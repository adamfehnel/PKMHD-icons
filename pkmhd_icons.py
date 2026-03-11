"""
PKMHD Icons — Wallpaper Generator
==================================
Creates an MKBHD "Icons"-style wallpaper using retro video game creature sprites.
Sprites are sourced from a public sprite database and rendered as subtle
silhouettes on a dark gradient background in a staggered brick-pattern grid.

Usage:
    python pkmhd_icons.py

The generated wallpaper will be saved to the same directory as this script.
All configuration options are at the top of this file — tweak freely!
"""

import os
import io
import re
import math
import random
import requests
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from concurrent.futures import ThreadPoolExecutor, as_completed


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION — Edit these values to customize your wallpaper
# ═══════════════════════════════════════════════════════════════

# ── Output Dimensions ──────────────────────────────────────────
WALLPAPER_WIDTH = 3840       # Output width in pixels (3840 = 4K)
WALLPAPER_HEIGHT = 2160      # Output height in pixels (2160 = 4K)

# ── Sprite Grid Layout ────────────────────────────────────────
ICON_SIZE = 36               # Size to scale each sprite to (px)
GRID_SPACING_X = 64          # Horizontal distance between sprite centers (px)
GRID_SPACING_Y = 58          # Vertical distance between sprite centers (px)
ROW_OFFSET = 32              # Horizontal offset for alternating rows (brick pattern)

# ── Sprite Appearance ─────────────────────────────────────────
ICON_BRIGHTNESS = 52         # Silhouette brightness (0 = invisible, 255 = full)
ICON_COLOR = (255, 255, 255) # Silhouette tint color as (R, G, B) tuple

# ── Background Gradient ───────────────────────────────────────
# Supported types: "none" (solid), "radial", "linear", "diagonal"
GRADIENT_TYPE = "radial"
# Center/start color for the gradient
GRADIENT_COLOR_CENTER = (38, 38, 42)
# Edge/end color for the gradient
GRADIENT_COLOR_EDGE = (18, 18, 20)
# Direction for "linear" gradient (degrees: 0=left→right, 90=top→bottom)
LINEAR_GRADIENT_ANGLE = 90

# ── Vignette ──────────────────────────────────────────────────
# Extra radial darkening on top of the gradient (0.0 = off, 1.0 = full black corners)
VIGNETTE_STRENGTH = 0.15

# ── File Paths ────────────────────────────────────────────────
SPRITE_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite_cache")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pkmhd_icons_wallpaper.png")

# ── Sprite Source ─────────────────────────────────────────────
# URL template for individual sprite images (Black & White generation pixel art)
_SPRITE_DB_BASE = "https://img.pokemondb.net"
SPRITE_URL = f"{_SPRITE_DB_BASE}/sprites/black-white/normal/{{name}}.png"
# Index page used to discover all available creature names
_SPRITE_INDEX_URL = "https://pokemondb.net/sprites"


# ═══════════════════════════════════════════════════════════════
# SPRITE FETCHING
# ═══════════════════════════════════════════════════════════════

def fetch_creature_names():
    """
    Scrape the sprite index page to build a list of all available creature names.
    Returns a deduplicated list of lowercase name slugs (e.g. ['bulbasaur', 'ivysaur', ...]).
    """
    print("Fetching creature name list from sprite database...")
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    resp = requests.get(_SPRITE_INDEX_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    # Parse name slugs out of links like: /sprites/bulbasaur
    raw_names = re.findall(r'/sprites/([a-z0-9-]+)"', resp.text)

    # Deduplicate while preserving the original Pokedex order
    seen = set()
    unique = []
    for name in raw_names:
        if name not in seen:
            seen.add(name)
            unique.append(name)

    print(f"  Found {len(unique)} unique creatures")
    return unique


def download_sprite(name):
    """
    Download a single sprite PNG by creature name.
    Uses a local file cache to avoid repeated downloads.
    Returns (name, bytes) on success, or None on failure.
    """
    cache_path = os.path.join(SPRITE_CACHE_DIR, f"{name}.png")

    # Return cached version if it exists
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return (name, f.read())

    # Download from the sprite database
    url = SPRITE_URL.format(name=name)
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        # Only accept valid PNGs (> 100 bytes filters out error pages)
        if resp.status_code == 200 and len(resp.content) > 100:
            with open(cache_path, "wb") as f:
                f.write(resp.content)
            return (name, resp.content)
    except Exception:
        pass
    return None


def download_all_sprites(names):
    """
    Download all sprites in parallel using a thread pool.
    Sprites that are already cached locally will load instantly.
    Returns a dict of {name: image_bytes}.
    """
    os.makedirs(SPRITE_CACHE_DIR, exist_ok=True)

    sprites = {}
    total = len(names)
    completed = 0

    print(f"Downloading {total} sprites (cached = instant)...")

    # Use 8 threads for parallel downloads
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_sprite, name): name for name in names}
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                name, data = result
                sprites[name] = data
            # Print progress every 50 sprites
            if completed % 50 == 0:
                print(f"  Progress: {completed}/{total} ({len(sprites)} successful)")

    print(f"  Total downloaded: {len(sprites)} sprites")
    return sprites


# ═══════════════════════════════════════════════════════════════
# IMAGE PROCESSING
# ═══════════════════════════════════════════════════════════════

def sprite_to_silhouette(sprite_bytes, size, brightness):
    """
    Convert a color sprite into a tinted silhouette icon.

    The process:
    1. Load the sprite and resize to the target icon size
    2. For each opaque pixel, calculate a brightness value that preserves
       some of the original sprite's depth/detail (not a flat fill)
    3. Apply the configured ICON_COLOR tint at the calculated brightness

    Args:
        sprite_bytes: Raw PNG bytes of the sprite
        size: Target square size in pixels
        brightness: Base brightness level (0-255)

    Returns:
        RGBA Image with the silhouette on a transparent background
    """
    # Load sprite with alpha channel
    img = Image.open(io.BytesIO(sprite_bytes)).convert("RGBA")

    # Use nearest-neighbor resampling to keep pixel art crisp (no blurring)
    img = img.resize((size, size), Image.NEAREST)

    pixels = img.load()
    # Start with a fully transparent canvas
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result_pixels = result.load()

    for y in range(size):
        for x in range(size):
            r, g, b, a = pixels[x, y]

            # Skip transparent/near-transparent pixels
            if a > 30:
                # Factor 1: Alpha-based brightness (preserves shape edges)
                detail_factor = a / 255.0
                pixel_brightness = int(brightness * detail_factor)

                # Factor 2: Original pixel luminance adds subtle depth
                # Uses standard BT.601 luma coefficients
                original_luma = int(0.299 * r + 0.587 * g + 0.114 * b)
                detail_boost = int((original_luma / 255.0) * (brightness * 0.3))

                # Combine both factors into final brightness
                final_brightness = min(255, pixel_brightness + detail_boost)

                # Apply the icon tint color scaled by brightness
                fb = final_brightness / 255.0
                result_pixels[x, y] = (
                    int(ICON_COLOR[0] * fb),
                    int(ICON_COLOR[1] * fb),
                    int(ICON_COLOR[2] * fb),
                    255  # Fully opaque
                )

    return result


# ═══════════════════════════════════════════════════════════════
# BACKGROUND GENERATION
# ═══════════════════════════════════════════════════════════════

def _lerp_color(color_a, color_b, t):
    """Linearly interpolate between two RGB color tuples at parameter t (0.0–1.0)."""
    return (
        int(color_a[0] + (color_b[0] - color_a[0]) * t),
        int(color_a[1] + (color_b[1] - color_a[1]) * t),
        int(color_a[2] + (color_b[2] - color_a[2]) * t),
    )


def create_gradient_background(width, height):
    """
    Generate the wallpaper background with the configured gradient.

    Supported gradient types:
    - "none":     Solid fill using GRADIENT_COLOR_CENTER
    - "radial":   Center→edge radial gradient
    - "linear":   Directional gradient at LINEAR_GRADIENT_ANGLE degrees
    - "diagonal": Top-left→bottom-right diagonal gradient
    """
    bg = Image.new("RGB", (width, height), GRADIENT_COLOR_CENTER)

    # Solid color — nothing more to do
    if GRADIENT_TYPE == "none":
        return bg

    pixels = bg.load()
    cx, cy = width / 2, height / 2  # Center point

    if GRADIENT_TYPE == "radial":
        # Distance from center to the farthest corner
        max_dist = math.sqrt(cx ** 2 + cy ** 2)
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                t = min(1.0, dist / max_dist)  # 0 at center, 1 at corners
                pixels[x, y] = _lerp_color(GRADIENT_COLOR_CENTER, GRADIENT_COLOR_EDGE, t)

    elif GRADIENT_TYPE == "linear":
        # Project each pixel onto the gradient direction vector
        angle_rad = math.radians(LINEAR_GRADIENT_ANGLE)
        dx, dy = math.cos(angle_rad), math.sin(angle_rad)
        # Find the full projection range across all four corners
        corners = [(0, 0), (width, 0), (0, height), (width, height)]
        projections = [cx_p * dx + cy_p * dy for cx_p, cy_p in corners]
        min_proj, max_proj = min(projections), max(projections)
        span = max_proj - min_proj if max_proj != min_proj else 1
        for y in range(height):
            for x in range(width):
                proj = x * dx + y * dy
                t = (proj - min_proj) / span  # Normalize to 0–1
                pixels[x, y] = _lerp_color(GRADIENT_COLOR_CENTER, GRADIENT_COLOR_EDGE, t)

    elif GRADIENT_TYPE == "diagonal":
        # Simple top-left to bottom-right gradient
        max_dist = width + height
        for y in range(height):
            for x in range(width):
                t = (x + y) / max_dist
                pixels[x, y] = _lerp_color(GRADIENT_COLOR_CENTER, GRADIENT_COLOR_EDGE, t)

    return bg


# ═══════════════════════════════════════════════════════════════
# WALLPAPER COMPOSITION
# ═══════════════════════════════════════════════════════════════

def create_wallpaper(sprites_dict, names_order):
    """
    Compose the final wallpaper by placing silhouette sprites on the gradient
    background in a staggered (brick-pattern) grid.
    """
    print("Creating wallpaper...")

    # Step A: Generate the gradient background
    print(f"  Generating '{GRADIENT_TYPE}' gradient background...")
    wallpaper = create_gradient_background(WALLPAPER_WIDTH, WALLPAPER_HEIGHT)

    # Step B: Calculate the grid dimensions (with 2 extra rows/cols for bleed)
    cols = (WALLPAPER_WIDTH // GRID_SPACING_X) + 2
    rows = (WALLPAPER_HEIGHT // GRID_SPACING_Y) + 2
    print(f"  Grid: {cols} cols × {rows} rows = {cols * rows} slots")

    # Only use sprites we successfully downloaded
    available = [n for n in names_order if n in sprites_dict]
    if not available:
        print("ERROR: No sprites available!")
        return None

    # Step C: Convert all sprites to silhouettes
    print(f"  Processing {len(available)} sprites into silhouettes...")
    silhouettes = {}
    for i, name in enumerate(available):
        silhouettes[name] = sprite_to_silhouette(
            sprites_dict[name], ICON_SIZE, ICON_BRIGHTNESS
        )
        if (i + 1) % 50 == 0:
            print(f"    {i + 1}/{len(available)} done")

    # Shuffle sprites so the wallpaper has a nice random distribution
    # Seed is fixed for reproducible output — change it for a different arrangement
    sprite_list = list(silhouettes.keys())
    random.seed(42)
    random.shuffle(sprite_list)

    # Step D: Place sprites on the grid
    sprite_idx = 0
    # Start one cell off-screen so edge sprites aren't cut off
    start_x = -GRID_SPACING_X
    start_y = -GRID_SPACING_Y

    for row in range(rows):
        for col in range(cols):
            # Calculate the grid position
            x = start_x + col * GRID_SPACING_X
            # Stagger every other row for the brick pattern effect
            if row % 2 == 1:
                x += ROW_OFFSET
            y = start_y + row * GRID_SPACING_Y

            # Center the sprite on the grid point
            paste_x = x - ICON_SIZE // 2
            paste_y = y - ICON_SIZE // 2

            # Cycle through all sprites (wraps around if grid > sprite count)
            name = sprite_list[sprite_idx % len(sprite_list)]
            sprite_idx += 1

            silhouette = silhouettes[name]

            # Only paste if the sprite overlaps the visible area
            if (paste_x + ICON_SIZE > 0 and paste_x < WALLPAPER_WIDTH and
                    paste_y + ICON_SIZE > 0 and paste_y < WALLPAPER_HEIGHT):
                # Use the sprite's alpha channel as the paste mask
                wallpaper.paste(silhouette, (paste_x, paste_y), silhouette)

    return wallpaper


def add_vignette(wallpaper, strength):
    """
    Apply a radial vignette (edge-darkening) effect to the wallpaper.

    Args:
        wallpaper: The PIL Image to apply the vignette to
        strength: 0.0 = no effect, 1.0 = full black at corners
    """
    if strength <= 0:
        return wallpaper

    width, height = wallpaper.size
    # Build a grayscale mask where brighter = more darkening
    vignette = Image.new("L", (width, height), 0)
    pixels = vignette.load()

    cx, cy = width / 2, height / 2
    max_dist = math.sqrt(cx ** 2 + cy ** 2)  # Distance to corner
    max_darkness = int(255 * min(1.0, strength))

    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            ratio = dist / max_dist
            # Ease-in curve (ratio^1.5) for a natural-looking falloff
            darkness = int(max_darkness * (ratio ** 1.5))
            pixels[x, y] = min(255, darkness)

    # Smooth the vignette mask so it's not pixelated
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=30))

    # Subtract the vignette from the wallpaper to darken edges
    vignette_rgb = Image.merge("RGB", [vignette, vignette, vignette])
    return ImageChops.subtract(wallpaper, vignette_rgb)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 50)
    print("  PKMHD Icons — Wallpaper Generator")
    print("=" * 50)
    print()

    # 1. Discover all available creature names from the sprite database
    names = fetch_creature_names()

    # 2. Download all sprite images (uses local cache for speed)
    sprites = download_all_sprites(names)

    if len(sprites) < 10:
        print("Not enough sprites downloaded. Check your internet connection.")
        return

    # 3. Compose the wallpaper
    wallpaper = create_wallpaper(sprites, names)
    if wallpaper is None:
        return

    # 4. Apply vignette if enabled
    if VIGNETTE_STRENGTH > 0:
        print(f"  Applying vignette (strength={VIGNETTE_STRENGTH})...")
        wallpaper = add_vignette(wallpaper, VIGNETTE_STRENGTH)

    # 5. Save the final image
    wallpaper.save(OUTPUT_PATH, "PNG", optimize=True)
    print()
    print(f"Wallpaper saved: {OUTPUT_PATH}")
    print(f"Resolution:      {WALLPAPER_WIDTH}×{WALLPAPER_HEIGHT}")
    print(f"Sprites used:    {len(sprites)}")
    print("Done!")


if __name__ == "__main__":
    main()
