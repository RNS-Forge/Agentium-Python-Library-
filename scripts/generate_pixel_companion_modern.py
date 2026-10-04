"""
Modern Retro Pixel Art Animator for Agentium Orbital Companion.
Combines 2-bit classic cross-hatch dithering with smooth modern animation dynamics:
- Multi-frame easing (30 fps smooth hover)
- Visor eye animations (steady -> soft blink -> cheerful smile curve)
- Dynamic thruster exhaust sparks
- Expanding ground telemetry ripples
- Orbiting holographic shield node with trailing pixel sparks
- Vertical digital matrix rain streaks
"""
import math
import os
from PIL import Image, ImageDraw

def create_modern_retro_companion(output_path: str, num_frames: int = 32, scale: int = 4):
    width, height = 100, 100
    frames = []

    # Modernized Retro Palette (Crisp High-Contrast):
    # Background: Pure Clean White (#FFFFFF)
    # Primary Outline / Contrast: Deep Midnight Cobalt (#001A70)
    # Secondary Tone / Shading: Vibrant Electric Azure (#0077FF)
    # Accent / Visor Glow: Coral Red (#FF204E)
    # Soft Dither Tone: Sky Blue Tint (#88CCFF)
    c_bg = (255, 255, 255)
    c_outline = (0, 26, 112)
    c_azure = (0, 119, 255)
    c_coral = (255, 32, 78)
    c_sky = (136, 204, 255)

    # 4x4 Ordered Bayer Matrix for silky smooth retro gradients
    bayer_4x4 = [
        [ 0,  8,  2, 10],
        [12,  4, 14,  6],
        [ 3, 11,  1,  9],
        [15,  7, 13,  5]
    ]

    for frame_idx in range(num_frames):
        t = frame_idx / num_frames
        angle = 2 * math.pi * t

        # Hover physics: primary sine + small secondary harmonic for organic buoyancy
        hover = math.sin(angle) * 3.5 + math.sin(angle * 2) * 0.5
        center_x = 50
        center_y = 44 + int(round(hover))
        bot_radius = 18

        img = Image.new("RGB", (width, height), c_bg)
        draw = ImageDraw.Draw(img)

        # 1. Background Digital Telemetry Rain (Vertical data streaks)
        rain_lanes = [8, 16, 25, 35, 65, 75, 84, 92]
        for lane_idx, lx in enumerate(rain_lanes):
            speed = 1.0 + (lane_idx % 3) * 0.4
            phase = (t * speed * height + lane_idx * 19) % height
            streak_len = 4 + (lane_idx % 4)
            for s in range(streak_len):
                sy = int((phase + s) % height)
                # Dithered trail
                if s == streak_len - 1:
                    img.putpixel((lx, sy), c_azure)
                elif s == streak_len - 2:
                    img.putpixel((lx, sy), c_sky)
                elif s % 2 == 0:
                    img.putpixel((lx, sy), c_sky)

        # 2. Expanding Ground Telemetry Ripples beneath bot
        ripple_radius = 12 + int((t * 22) % 18)
        ground_y = 82
        for rx in range(-ripple_radius, ripple_radius + 1):
            if abs(rx) % 2 == 0 and abs(rx) > 4:
                px = center_x + rx
                if 0 <= px < width:
                    # Fade toward edge
                    c = c_azure if abs(rx) < ripple_radius - 4 else c_sky
                    img.putpixel((px, ground_y), c)

        # Static ground reference line
        for gx in range(center_x - 16, center_x + 17):
            if (gx + ground_y) % 2 == 0:
                img.putpixel((gx, ground_y), c_outline)

        # 3. Thruster Pods and Exhaust Animation
        thruster_offsets = [-11, 11]
        for tox in thruster_offsets:
            tx = center_x + tox
            ty = center_y + 15
            # Pod housing
            draw.rectangle([tx - 2, ty - 2, tx + 2, ty + 1], fill=c_azure, outline=c_outline)
            
            # Exhaust flame plume (animated length and spread)
            flame_h = 4 + int((math.sin(angle * 3 + tox) + 1.0) * 3)
            for fl in range(flame_h):
                fy = ty + 2 + fl
                spread = fl // 2
                for fx in range(tx - spread, tx + spread + 1):
                    if (fx + fy + frame_idx) % 2 == 0 or fl <= 1:
                        col = c_coral if fl < 2 else (c_azure if fl < 4 else c_sky)
                        if 0 <= fx < width and 0 <= fy < height:
                            img.putpixel((fx, fy), col)

        # 4. Spherical Bot Chassis with 4x4 Bayer Dither Shading
        for y in range(center_y - bot_radius - 2, center_y + bot_radius + 3):
            for x in range(center_x - bot_radius - 2, center_x + bot_radius + 3):
                dist_sq = (x - center_x) ** 2 + (y - center_y) ** 2
                r_sq = bot_radius ** 2

                if dist_sq <= r_sq:
                    # Light calculation (top-left key light)
                    lx = (x - center_x) / bot_radius + 0.35
                    ly = (y - center_y) / bot_radius + 0.45
                    light_dist = math.sqrt(max(0.0, lx * lx + ly * ly))
                    illumination = max(0.0, min(1.0, 1.05 - light_dist * 0.95))

                    b_thresh = bayer_4x4[y % 4][x % 4] / 16.0
                    dither_level = illumination + (b_thresh - 0.5) * 0.50

                    if dist_sq >= (bot_radius - 1.5) ** 2:
                        # Solid outer border
                        img.putpixel((x, y), c_outline)
                    elif dither_level > 0.72:
                        img.putpixel((x, y), c_bg)
                    elif dither_level > 0.40:
                        img.putpixel((x, y), c_azure)
                    elif dither_level > 0.18:
                        img.putpixel((x, y), c_sky)
                    else:
                        img.putpixel((x, y), c_outline)

        # 5. Sensor Horns / Antennas
        draw.line([center_x - 8, center_y - bot_radius + 2, center_x - 13, center_y - bot_radius - 5], fill=c_outline, width=1)
        draw.line([center_x + 8, center_y - bot_radius + 2, center_x + 13, center_y - bot_radius - 5], fill=c_outline, width=1)
        img.putpixel((center_x - 13, center_y - bot_radius - 6), c_coral)
        img.putpixel((center_x + 13, center_y - bot_radius - 6), c_coral)

        # 6. Oval Digital Visor
        visor_w, visor_h = 11, 8
        for vy in range(center_y - visor_h, center_y + visor_h + 1):
            for vx in range(center_x - visor_w, center_x + visor_w + 1):
                if ((vx - center_x) / visor_w) ** 2 + ((vy - center_y) / visor_h) ** 2 <= 1.0:
                    img.putpixel((vx, vy), c_bg)

        # Smooth visor border
        for deg in range(0, 360, 5):
            rad = math.radians(deg)
            vx = int(center_x + visor_w * math.cos(rad))
            vy = int(center_y + visor_h * math.sin(rad))
            img.putpixel((vx, vy), c_outline)

        # 7. Animated Facial Visor Expressions
        # Frames 0..18: Observant Eyes
        # Frames 19..22: Fast Blink
        # Frames 23..29: Happy Cheerful Eyes (^_^)
        # Frames 30..31: Transition back
        eye_y = center_y - 1
        lx, rx = center_x - 5, center_x + 5

        if 19 <= frame_idx <= 22:
            # Flat blink (-)
            draw.line([lx - 2, eye_y, lx + 2, eye_y], fill=c_outline)
            draw.line([rx - 2, eye_y, rx + 2, eye_y], fill=c_outline)
        elif 23 <= frame_idx <= 29:
            # Cheerful curved eyes (^)
            img.putpixel((lx - 2, eye_y + 1), c_outline)
            img.putpixel((lx - 1, eye_y), c_outline)
            img.putpixel((lx, eye_y - 1), c_outline)
            img.putpixel((lx + 1, eye_y), c_outline)
            img.putpixel((lx + 2, eye_y + 1), c_outline)

            img.putpixel((rx - 2, eye_y + 1), c_outline)
            img.putpixel((rx - 1, eye_y), c_outline)
            img.putpixel((rx, eye_y - 1), c_outline)
            img.putpixel((rx + 1, eye_y), c_outline)
            img.putpixel((rx + 2, eye_y + 1), c_outline)
        else:
            # Round big pixel eyes with glint
            for ey in range(eye_y - 2, eye_y + 3):
                for ex in range(lx - 1, lx + 2):
                    img.putpixel((ex, ey), c_outline)
                for ex in range(rx - 1, rx + 2):
                    img.putpixel((ex, ey), c_outline)
            img.putpixel((lx, eye_y - 1), c_coral)
            img.putpixel((rx, eye_y - 1), c_coral)

        # Smile
        my = center_y + 4
        img.putpixel((center_x - 2, my - 1), c_coral)
        img.putpixel((center_x - 1, my), c_coral)
        img.putpixel((center_x, my), c_coral)
        img.putpixel((center_x + 1, my), c_coral)
        img.putpixel((center_x + 2, my - 1), c_coral)

        # 8. Orbiting Holographic Shield Ring with Rotating Satellite Node
        orbit_rx, orbit_ry = 28, 9
        # Ring rotation
        for d in range(0, 360, 10):
            rad = math.radians(d)
            ox = int(center_x + orbit_rx * math.cos(rad))
            oy = int(center_y + orbit_ry * math.sin(rad))
            is_foreground = math.sin(rad) >= 0
            if (ox - center_x)**2 + (oy - center_y)**2 > (bot_radius - 1)**2 or is_foreground:
                img.putpixel((ox, oy), c_azure if (d // 10) % 2 == 0 else c_outline)

        # Revolving Node
        node_angle = angle
        nx = int(center_x + orbit_rx * math.cos(node_angle))
        ny = int(center_y + orbit_ry * math.sin(node_angle))
        
        # Shield diamond node with sparkles
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) + abs(dy) <= 2:
                    px, py = nx + dx, ny + dy
                    if 0 <= px < width and 0 <= py < height:
                        col = c_coral if abs(dx) + abs(dy) <= 1 else c_outline
                        img.putpixel((px, py), col)

        # Trailing sparkle behind the node
        trail_ang = node_angle - 0.25
        tx = int(center_x + orbit_rx * math.cos(trail_ang))
        ty = int(center_y + orbit_ry * math.sin(trail_ang))
        if 0 <= tx < width and 0 <= ty < height:
            img.putpixel((tx, ty), c_azure)

        # Scale with nearest-neighbor for razor-sharp pixel crispness
        scaled = img.resize((width * scale, height * scale), Image.NEAREST)
        frames.append(scaled)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=50,  # 20 FPS silky animation
        loop=0,
        optimize=False
    )
    print(f"Rendered {output_path} ({len(frames)} frames @ {width*scale}x{height*scale})")

if __name__ == "__main__":
    out_file = os.path.join("assets", "agentium_companion.gif")
    create_modern_retro_companion(out_file)
