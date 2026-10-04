"""
Generator for Agentium Orbital Companion retro pixel-art animated GIF.
Inspired by classic 2-bit dithered pixel animations (Bayer dithering, sharp contour outlines,
hovering animation, blinking facial visor, thruster exhaust particles, and orbital data rings).
"""
import math
import os
from PIL import Image, ImageDraw

def create_companion_gif(output_path: str, num_frames: int = 24, scale: int = 4):
    width, height = 96, 96
    frames = []

    # 4-level retro cyan/blue/dark cyber palette:
    # 0: Deep background (#0c1017)
    # 1: Dark cobalt (#1d3557)
    # 2: Vibrant cyan (#00d2ff)
    # 3: Crisp white highlight (#ffffff)
    c_bg = (12, 16, 23)
    c_dark = (29, 53, 87)
    c_cyan = (0, 210, 255)
    c_white = (255, 255, 255)

    # 2x2 Bayer dither matrix for authentic retro shading
    bayer_2x2 = [
        [0, 2],
        [3, 1]
    ]

    for frame_idx in range(num_frames):
        t = frame_idx / num_frames
        angle = 2 * math.pi * t
        
        # Smooth bobbing up and down
        hover_offset = int(math.sin(angle) * 3)
        center_x = 48
        center_y = 44 + hover_offset
        bot_radius = 18

        img = Image.new("RGB", (width, height), c_bg)
        draw = ImageDraw.Draw(img)

        # 1. Background falling data particles / matrix rain effect (retro streaks)
        for i in range(12):
            px = (i * 8 + int(t * 16)) % (width - 4) + 2
            py_base = (int(t * 48) + i * 17) % height
            streak_len = (i % 3) + 2
            for s in range(streak_len):
                sy = (py_base + s) % height
                c = c_cyan if s == streak_len - 1 else c_dark
                img.putpixel((px, sy), c)

        # 2. Ground pulse / shadow beneath bot
        shadow_width = max(10, 22 - abs(hover_offset) * 2)
        shadow_y = 80
        for dx in range(-shadow_width, shadow_width + 1):
            if (dx + shadow_y) % 2 == 0:  # checkerboard ground dither
                if 0 <= center_x + dx < width:
                    img.putpixel((center_x + dx, shadow_y), c_dark)

        # 3. Thruster exhaust flame/spark particles below bot
        # Dual thrusters at (-11, +14) and (+11, +14) relative to center
        thruster_xs = [center_x - 10, center_x + 10]
        thruster_y = center_y + 16
        for tx in thruster_xs:
            # Thruster pod body
            draw.rectangle([tx - 2, thruster_y - 2, tx + 2, thruster_y], fill=c_dark, outline=c_cyan)
            # Exhaust animated flame
            flame_len = 3 + int((math.sin(angle * 2 + tx) + 1) * 3)
            for fl in range(flame_len):
                fy = thruster_y + 1 + fl
                spread = (fl // 2)
                for fx in range(tx - spread, tx + spread + 1):
                    # Dithered flame tip
                    thresh = (fl * 4) // max(flame_len, 1)
                    if (fx + fy + frame_idx) % 2 == 0 or fl == 0:
                        color = c_white if fl < 2 else (c_cyan if fl < 4 else c_dark)
                        if 0 <= fx < width and 0 <= fy < height:
                            img.putpixel((fx, fy), color)

        # 4. Spherical Companion Bot Body
        for y in range(center_y - bot_radius - 2, center_y + bot_radius + 3):
            for x in range(center_x - bot_radius - 2, center_x + bot_radius + 3):
                dist_sq = (x - center_x) ** 2 + (y - center_y) ** 2
                r_sq = bot_radius ** 2

                if dist_sq <= r_sq:
                    # Inner sphere
                    # Shading based on light source from top-left (-0.5, -0.6)
                    lx = (x - center_x) / bot_radius + 0.3
                    ly = (y - center_y) / bot_radius + 0.4
                    light = 1.0 - math.sqrt(max(0.0, lx*lx + ly*ly))
                    
                    # Bayer 2x2 dithering
                    b_val = bayer_2x2[y % 2][x % 2] / 4.0
                    dithered_light = light + (b_val - 0.5) * 0.4

                    if dist_sq >= (bot_radius - 1) ** 2:
                        # Outline
                        img.putpixel((x, y), c_cyan)
                    elif dithered_light > 0.82:
                        img.putpixel((x, y), c_white)
                    elif dithered_light > 0.45:
                        img.putpixel((x, y), c_cyan)
                    elif dithered_light > 0.20:
                        img.putpixel((x, y), c_dark)
                    else:
                        img.putpixel((x, y), c_bg)

        # 5. Top Antenna / Sensor Horns
        draw.line([center_x - 8, center_y - bot_radius + 2, center_x - 12, center_y - bot_radius - 4], fill=c_cyan, width=1)
        draw.line([center_x + 8, center_y - bot_radius + 2, center_x + 12, center_y - bot_radius - 4], fill=c_cyan, width=1)
        # Antenna tips
        img.putpixel((center_x - 12, center_y - bot_radius - 5), c_white)
        img.putpixel((center_x + 12, center_y - bot_radius - 5), c_white)

        # 6. Digital Screen Face (Elliptical Visor)
        visor_rx = 11
        visor_ry = 8
        for vy in range(center_y - visor_ry, center_y + visor_ry + 1):
            for vx in range(center_x - visor_rx, center_x + visor_rx + 1):
                if ((vx - center_x) / visor_rx) ** 2 + ((vy - center_y) / visor_ry) ** 2 <= 1.0:
                    img.putpixel((vx, vy), c_bg)

        # Visor border outline
        for deg in range(0, 360, 5):
            rad = math.radians(deg)
            vx = int(center_x + visor_rx * math.cos(rad))
            vy = int(center_y + visor_ry * math.sin(rad))
            img.putpixel((vx, vy), c_cyan)

        # 7. Animated Visor Eyes (Happy blinking / expressive companion)
        # Blink during frames 12 to 14
        is_blinking = 12 <= frame_idx <= 14
        eye_y = center_y - 1
        left_eye_x = center_x - 5
        right_eye_x = center_x + 5

        if is_blinking:
            # Flat closed eyes (-)
            draw.line([left_eye_x - 2, eye_y, left_eye_x + 1, eye_y], fill=c_white)
            draw.line([right_eye_x - 1, eye_y, right_eye_x + 2, eye_y], fill=c_white)
        else:
            # Big retro oval pixel eyes (^)
            for ey in range(eye_y - 2, eye_y + 3):
                for ex in range(left_eye_x - 1, left_eye_x + 2):
                    img.putpixel((ex, ey), c_white)
                for ex in range(right_eye_x - 1, right_eye_x + 2):
                    img.putpixel((ex, ey), c_white)
            # Pupil sparkles
            img.putpixel((left_eye_x + 1, eye_y + 1), c_cyan)
            img.putpixel((right_eye_x + 1, eye_y + 1), c_cyan)

        # 8. Companion Smile / Chevron mouth (v)
        mouth_y = center_y + 4
        img.putpixel((center_x - 2, mouth_y - 1), c_cyan)
        img.putpixel((center_x - 1, mouth_y), c_cyan)
        img.putpixel((center_x, mouth_y + 1), c_white)
        img.putpixel((center_x + 1, mouth_y), c_cyan)
        img.putpixel((center_x + 2, mouth_y - 1), c_cyan)

        # 9. Orbiting Data Shield Rings / Holographic Satellite Lock
        orbit_rx = 26
        orbit_ry = 9
        # Orbit particle angle rotates continuously
        orbit_angle = angle
        # Draw dotted ellipse ring in background (behind bot) and foreground (in front of bot)
        for d in range(0, 360, 15):
            rad = math.radians(d)
            ox = int(center_x + orbit_rx * math.cos(rad))
            oy = int(center_y + orbit_ry * math.sin(rad))
            # If in front (sin >= 0) or behind (sin < 0)
            is_foreground = math.sin(rad) >= 0
            if (ox - center_x)**2 + (oy - center_y)**2 > (bot_radius - 1)**2 or is_foreground:
                img.putpixel((ox, oy), c_cyan if (d // 15) % 2 == 0 else c_dark)

        # Rotating Shield Node on the orbit
        node_x = int(center_x + orbit_rx * math.cos(orbit_angle))
        node_y = int(center_y + orbit_ry * math.sin(orbit_angle))
        # Draw micro shield node
        for ndy in range(node_y - 2, node_y + 3):
            for ndx in range(node_x - 2, node_x + 3):
                if 0 <= ndx < width and 0 <= ndy < height:
                    if abs(ndx - node_x) + abs(ndy - node_y) <= 2:
                        img.putpixel((ndx, ndy), c_white if ndx == node_x and ndy == node_y else c_cyan)

        # Scale up cleanly with Nearest Neighbor to preserve perfect pixel edges
        scaled_frame = img.resize((width * scale, height * scale), Image.NEAREST)
        frames.append(scaled_frame)

    # Save animated GIF with loop=0 (infinite) and duration=60ms per frame (~16.6 FPS)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=65,
        loop=0,
        optimize=False
    )
    print(f"Generated {output_path} ({len(frames)} frames, {width*scale}x{height*scale})")

if __name__ == "__main__":
    out_dir = "assets"
    out_file = os.path.join(out_dir, "agentium_companion.gif")
    create_companion_gif(out_file)
