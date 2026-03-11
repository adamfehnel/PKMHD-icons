"""
PKMHD Icons — Batch Sample Generator
=====================================
Generates sample wallpapers across multiple resolutions and color schemes.
"""

import os
import sys

# Import the main generator module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pkmhd_icons as gen

# ── Output directory ───────────────────────────────────────────
SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

# ── Curated Samples ────────────────────────────────────────────
# 20 specific (design, resolution) pairings spread across device types.
# (name, width, height, icon_color, grad_center, grad_edge, brightness,
#  icon_size, spacing_x, spacing_y, gradient_type, vignette)
SAMPLES = [
    # ── Desktop 16:9 ──────────────────────────────────────────
    # 4K — neon pink on black, tight grid
    ("neon-pink_4K",        3840, 2160, (255, 40, 180),  (18, 8, 22),    (5, 2, 8),     120, 28, 48, 44, "radial", 0.2),
    # 4K — black on white, classic inverted
    ("ink-on-paper_4K",     3840, 2160, (0, 0, 0),       (255, 255, 255),(235, 235, 240), 60, 36, 64, 58, "radial", 0.05),
    # 4K — orange on yellow
    ("citrus_4K",           3840, 2160, (230, 100, 0),   (255, 220, 40), (245, 195, 20),  90, 42, 72, 66, "radial", 0.1),
    # 1440p — hot pink on deep purple
    ("candy_1440p",         2560, 1440, (255, 80, 180),  (55, 10, 80),   (25, 2, 45),    130, 30, 50, 46, "radial", 0.2),
    # 1440p — stealth dark MKBHD style
    ("stealth_1440p",       2560, 1440, (255, 255, 255), (38, 38, 42),   (18, 18, 20),    52, 24, 42, 38, "radial", 0.15),
    # 1080p — white on deep red
    ("valentine_1080p",     1920, 1080, (255, 255, 255), (180, 20, 40),  (120, 8, 20),    80, 18, 32, 29, "radial", 0.15),
    # 1080p — electric green matrix
    ("matrix_1080p",        1920, 1080, (0, 255, 70),    (5, 12, 5),     (0, 4, 0),       90, 11, 19, 17, "none", 0.0),

    # ── Ultrawide 21:9 ───────────────────────────────────────
    # UW 1440p — gold on royal blue
    ("royalty_UW1440p",     3440, 1440, (255, 200, 40),  (15, 25, 80),   (5, 10, 45),    120, 26, 44, 40, "radial", 0.15),
    # UW 1440p — coral on teal
    ("reef_UW1440p",        3440, 1440, (255, 100, 80),  (20, 80, 80),   (8, 50, 55),    110, 26, 46, 42, "radial", 0.12),
    # UW 1080p — cyan tron on navy
    ("tron_UW1080p",        2560, 1080, (0, 240, 255),   (8, 14, 30),    (2, 4, 14),     110, 16, 28, 25, "radial", 0.25),
    # UW 4K — big bold orange on black
    ("hot-orange_UW4K",     5120, 2160, (255, 140, 20),  (15, 10, 5),    (5, 3, 0),      100, 48, 80, 72, "radial", 0.15),

    # ── Mobile (portrait) ────────────────────────────────────
    # iPhone 15 Pro — lime green on hot pink
    ("tropical_iPhone15",   1179, 2556, (120, 255, 40),  (220, 50, 120), (180, 20, 80),   100, 20, 36, 32, "radial", 0.1),
    # iPhone 15 Pro Max — ultraviolet purple on navy
    ("ultraviolet_iPM",     1290, 2796, (160, 60, 255),  (12, 8, 35),    (4, 2, 16),     100, 22, 38, 35, "radial", 0.15),
    # iPhone 15 PM — warm amber on chocolate, big icons
    ("ember-glow_iPM",      1290, 2796, (255, 160, 60),  (30, 15, 8),    (12, 5, 0),      70, 30, 50, 46, "radial", 0.3),
    # Galaxy S — crimson on black
    ("crimson_GalaxyS",     1440, 3200, (220, 15, 25),   (20, 5, 5),     (8, 0, 0),      130, 34, 58, 52, "radial", 0.1),
    # Galaxy S — parchment dark on cream
    ("parchment_GalaxyS",   1440, 3200, (60, 50, 40),    (250, 242, 230),(235, 225, 210), 80, 26, 46, 42, "none", 0.08),
    # Android FHD — frozen ice blue on near-black
    ("frozen_FHD",          1080, 1920, (140, 200, 255), (14, 18, 28),   (4, 6, 14),      65, 28, 48, 44, "radial", 0.2),
    # Android FHD — blueprint navy on light blue
    ("blueprint_FHD",       1080, 1920, (20, 40, 100),   (210, 225, 245),(185, 200, 230), 90, 15, 26, 24, "linear", 0.05),
    # iPhone 15 — neon pink on black (mobile version)
    ("neon-pink_iPhone15",  1179, 2556, (255, 40, 180),  (18, 8, 22),    (5, 2, 8),      120, 17, 28, 26, "radial", 0.2),
    # Galaxy S — candy pink on purple
    ("candy_GalaxyS",       1440, 3200, (255, 80, 180),  (55, 10, 80),   (25, 2, 45),    130, 28, 48, 44, "radial", 0.2),
]


def generate_all():
    """Generate wallpapers for every combination of resolution and color scheme."""
    os.makedirs(SAMPLES_DIR, exist_ok=True)

    # Step 1: Download sprites once (reused across all variants)
    names = gen.fetch_creature_names()
    sprites = gen.download_all_sprites(names)

    if len(sprites) < 10:
        print("Not enough sprites. Check your connection.")
        return

    total = len(SAMPLES)
    current = 0

    for (name, width, height, icon_color, grad_center, grad_edge,
         brightness, icon_size, spacing_x, spacing_y,
         grad_type, vignette) in SAMPLES:

        current += 1
        filename = f"{name}_{width}x{height}.png"
        filepath = os.path.join(SAMPLES_DIR, filename)

        print(f"\n[{current}/{total}] {filename}")

        # Apply all settings
        gen.WALLPAPER_WIDTH = width
        gen.WALLPAPER_HEIGHT = height
        gen.ICON_SIZE = icon_size
        gen.GRID_SPACING_X = spacing_x
        gen.GRID_SPACING_Y = spacing_y
        gen.ROW_OFFSET = spacing_x // 2
        gen.ICON_BRIGHTNESS = brightness
        gen.ICON_COLOR = icon_color
        gen.GRADIENT_COLOR_CENTER = grad_center
        gen.GRADIENT_COLOR_EDGE = grad_edge
        gen.GRADIENT_TYPE = grad_type
        gen.VIGNETTE_STRENGTH = vignette

        # Generate
        wallpaper = gen.create_wallpaper(sprites, names)
        if wallpaper is None:
            print("  FAILED — skipping")
            continue

        if vignette > 0:
            wallpaper = gen.add_vignette(wallpaper, vignette)
        wallpaper.save(filepath, "PNG", optimize=True)
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  Saved ({size_kb:.0f} KB)")

    print(f"\n{'=' * 50}")
    print(f"Generated {current} wallpapers in: {SAMPLES_DIR}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    generate_all()
