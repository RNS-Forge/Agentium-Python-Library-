"""
Generator for Agentium Orbital Companion retro pixel-art animated GIF (Light Retro Edition).
Matches the exact visual style of the attached reference image:
White background, crisp cobalt blue outlines, cross-hatch dithering, and animated pixel data-rain.
"""
import math
import os
from PIL import Image, ImageDraw

def create_companion_retro_gif(output_path: str, num_frames: int = 24, scale: int = 4):
    width, height = 96, 96
    frames = []

    # Palette inspired directly by the reference image:
    # Background: Crisp White (#FFFFFF)
    # Outline: Deep Cobalt Blue (#0022AA)
    # Primary Body: Electric Cyan/Blue (#0088FF)
    # Accent/Visor: Electric Red/Coral (#FF2244)
    c_bg = (255, 255, 255)
    c_outline = (0, 34, 170)
    c_blue = (0, 136, 255)
    c_red = (255, 34, 68)

    # 2x2 Bayer dither matrix
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

        # 1. Background vertical data rain streaks (like reference rain)
        for i in range(12):
            px = (i * 8 + int(t * 12)) % (width - 6) + 3
            py_base = (int(t * 48) + i * 17) % height
            streak_len = (i % 3) + 3
            for s in range(streak_len):
                sy = (py_base + s) % height
                img.putpixel((px, sy), c_outline)

        # 2. Ground puddle ripples beneath bot
        shadow_w = max(8, 20 - abs(hover_offset) * 2)
        shadow_y = 82
        for dx in range(-shadow_w, shadow_w + 1):
            if (dx + shadow_y) % 2 == 0:
                if 0 <= center_x + dx < width:
                    img.putpixel((center_x + dx, shadow_y), c_blue)

        # 3. Dual Thruster Pods below
        thruster_xs = [center_x - 10, center_x + 10]
        thruster_y = center_y + 16
        for tx in thruster_xs:
            draw.rectangle([tx - 2, thruster_y - 2, tx + 2, thruster_y], fill=c_blue, outline=c_outline)
            flame_len = 3 + int((math.sin(angle * 2 + tx) + 1) * 3)
            for fl in range(flame_len):
                fy = thruster_y + 1 + fl
                spread = fl // 2
                for fx in range(tx - spread, tx + spread + 1):
                    if (fx + fy + frame_idx) % 2 == 0 or fl == 0:
                        color = c_red if fl < 2 else c_blue
                        if 0 <= fx < width and 0 <= fy < height:
                            img.putpixel((fx, fy), color)

        # 4. Spherical Bot Body with Bayer Dithering
        for y in range(center_y - bot_radius - 2, center_y + bot_radius + 3):
            for x in range(center_x - bot_radius - 2, center_x + bot_radius + 3):
                dist_sq = (x - center_x) ** 2 + (y - center_y) ** 2
                r_sq = bot_radius ** 2

                if dist_sq <= r_sq:
                    lx = (x - center_x) / bot_radius + 0.3
                    ly = (y - center_y) / bot_radius + 0.4
                    light = 1.0 - math.sqrt(max(0.0, lx*lx + ly*ly))
                    
                    b_val = bayer_2x2[y % 2][x % 2] / 4.0
                    dithered = light + (b_val - 0.5) * 0.45

                    if dist_sq >= (bot_radius - 1.5) ** 2:
                        img.putpixel((x, y), c_outline)
                    elif dithered > 0.70:
                        img.putpixel((x, y), c_bg)
                    elif dithered > 0.35:
                        img.putpixel((x, y), c_blue)
                    else:
                        img.putpixel((x, y), c_outline)

        # 5. Top Antenna / Sensor Horns
        draw.line([center_x - 8, center_y - bot_radius + 2, center_x - 12, center_y - bot_radius - 4], fill=c_outline, width=1)
        draw.line([center_x + 8, center_y - bot_radius + 2, center_x + 12, center_y - bot_radius - 4], fill=c_outline, width=1)
        img.putpixel((center_x - 12, center_y - bot_radius - 5), c_red)
        img.putpixel((center_x + 12, center_y - bot_radius - 5), c_red)

        # 6. Digital Screen Face (Elliptical Visor)
        visor_rx, visor_ry = 11, 8
        for vy in range(center_y - visor_ry, center_y + visor_ry + 1):
            for vx in range(center_x - visor_rx, center_x + visor_rx + 1):
                if ((vx - center_x) / visor_rx) ** 2 + ((vy - center_y) / visor_ry) ** 2 <= 1.0:
                    img.putpixel((vx, vy), c_bg)

        for deg in range(0, 360, 6):
            rad = math.radians(deg)
            vx = int(center_x + visor_rx * math.cos(rad))
            vy = int(center_y + visor_ry * math.sin(rad))
            img.putpixel((vx, vy), c_outline)

        # 7. Animated Visor Eyes (Blinking companion)
        is_blinking = 12 <= frame_idx <= 14
        eye_y = center_y - 1
        left_eye_x = center_x - 5
        right_eye_x = center_x + 5

        if is_blinking:
            draw.line([left_eye_x - 2, eye_y, left_eye_x + 1, eye_y], fill=c_outline)
            draw.line([right_eye_x - 1, eye_y, right_eye_x + 2, eye_y], fill=c_outline)
        else:
            for ey in range(eye_y - 2, eye_y + 3):
                for ex in range(left_eye_x - 1, left_eye_x + 2):
                    img.putpixel((ex, ey), c_outline)
                for ex in range(right_eye_x - 1, right_eye_x + 2):
                    img.putpixel((ex, ey), c_outline)
            # Eye glint
            img.putpixel((left_eye_x, eye_y - 1), c_bg)
            img.putpixel((right_eye_x, eye_y - 1), c_bg)

        # 8. Smile mouth
        mouth_y = center_y + 4
        img.putpixel((center_x - 2, mouth_y - 1), c_red)
        img.putpixel((center_x - 1, mouth_y), c_red)
        img.putpixel((center_x, mouth_y + 1), c_red)
        img.putpixel((center_x + 1, mouth_y), c_red)
        img.putpixel((center_x + 2, mouth_y - 1), c_red)

        # 9. Orbiting Data Shield Node & Ring
        orbit_rx, orbit_ry = 26, 9
        for d in range(0, 360, 15):
            rad = math.radians(d)
            ox = int(center_x + orbit_rx * math.cos(rad))
            oy = int(center_y + orbit_ry * math.sin(rad))
            is_foreground = math.sin(rad) >= 0
            if (ox - center_x)**2 + (oy - center_y)**2 > (bot_radius - 1)**2 or is_foreground:
                img.putpixel((ox, oy), c_blue if (d // 15) % 2 == 0 else c_outline)

        # Rotating Shield Node
        node_x = int(center_x + orbit_rx * math.cos(angle))
        node_y = int(center_y + orbit_ry * math.sin(angle))
        for ndy in range(node_y - 2, node_y + 3):
            for ndx in range(node_x - 2, node_x + 3):
                if 0 <= ndx < width and 0 <= ndy < height:
                    if abs(ndx - node_x) + abs(ndy - node_y) <= 2:
                        img.putpixel((ndx, ndy), c_red if ndx == node_x and ndy == node_y else c_outline)

        scaled_frame = img.resize((width * scale, height * scale), Image.NEAREST)
        frames.append(scaled_frame)

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
    out_file = os.path.join(out_dir, "agentium_companion_retro.gif")
    create_companion_retro_gif(out_file)
