import base64
import json
import math
import re
import spell_contents

CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 1000
NODE_RADIUS = 75
GRID_ASPECT = 0.7  # must match CSS aspect-ratio of .skill-tree-grid
NODE_Y_RADIUS = (
    NODE_RADIUS * GRID_ASPECT
)  # circle Y-extent in SVG units differs from X due to non-square grid
DIVIDER_ROWS = [370, 700]
SECRET_DIVIDER_ROW = 1020
CORNER_RADIUS = 20

COLOR_BG = {
    "defense": "rgb(30,45,70)",
    "cancel": "rgb(62,30,34)",
    "sense": "rgb(24,56,64)",
    "ritual": "rgb(67,50,34)",
    "tracking": "rgb(30,56,34)",
}

CATEGORY_COLOR = {
    "defense": "#0000cc",
    "cancel": "#cc0000",
    "sense": "#00cccc",
    "ritual": "#cc8400",
    "tracking": "#006600",
}


def load_nodes(path="lists/kontramagove.json"):
    return json.load(open(path))


def node_cy(row_y):
    return 100 + row_y * 165


GLOW_CLASS_BY_ROW = {
    0: "glow-low",
    1: "glow-low",
    2: "glow-mid",
    3: "glow-mid",
    4: "glow-huge",
    5: "glow-huge",
    6: "glow-huge",
}


def build_absolute_html(nodes, descriptions):
    pieces = []
    for node in nodes:
        cx = node["pos_x"]
        pos_y = node["pos_y"]
        cy = node_cy(pos_y)
        left = (cx - NODE_RADIUS) / 10
        top = (cy - NODE_Y_RADIUS) / 10
        color = node["category"]
        name = node["name"]
        node_id = node["id"]
        bg = COLOR_BG[color]
        icon_html = f'<img class="skill-icon" src="/icons/{color}.png" alt="">'
        glow_class = GLOW_CLASS_BY_ROW.get(pos_y, "")
        glow_class_str = f" {glow_class}" if glow_class else ""
        glow_color = CATEGORY_COLOR[color]
        desc_lines = descriptions.get(node_id, [])
        desc_html = "<br><br>".join(desc_lines)
        popup_html = (
            f'<div class="skill-popup">'
            f"<strong>{node_id}</strong>"
            f"{'<br><br>' + desc_html if desc_html else ''}"
            f"</div>"
        )
        secret_class = " skill-node-secret" if node.get("secret") else ""
        pieces.append(
            f'<div class="skill-node{secret_class}" style="left:{left}%;top:{top}%;">'
            f'<div class="skill-circle color-{color}{glow_class_str}" style="--glow-color:{glow_color};border-color:{CATEGORY_COLOR[color]};background:{bg};">{icon_html}</div>'
            f'<span class="skill-label">{name}</span>'
            f"{popup_html}"
            f"</div>"
        )
    return "".join(pieces)


def _norm(dx, dy):
    length = (dx * dx + dy * dy) ** 0.5
    return (dx / length, dy / length) if length else (0, 0)


def build_arrow_path(waypoints):
    pts = [(w[0], w[1]) for w in waypoints]
    if len(pts) < 2:
        return ""
    d = [f"M {pts[0][0]} {pts[0][1]}"]
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        nx, ny = _norm(px - pts[i - 1][0], py - pts[i - 1][1])
        ox, oy = _norm(pts[i + 1][0] - px, pts[i + 1][1] - py)
        ax, ay = px - nx * CORNER_RADIUS, py - ny * CORNER_RADIUS
        bx, by = px + ox * CORNER_RADIUS, py + oy * CORNER_RADIUS
        d.append(f"L {ax} {ay} C {px} {py} {px} {py} {bx} {by}")
    d.append(f"L {pts[-1][0]} {pts[-1][1]}")
    return " ".join(d)


def _ellipse_border(cx, cy, dx, dy, rx, ry):
    """Return the point on the ellipse border at (cx,cy) in direction (dx,dy)."""
    length = (dx * dx + dy * dy) ** 0.5
    if not length:
        return cx, cy
    ndx, ndy = dx / length, dy / length
    t = 1.0 / ((ndx / rx) ** 2 + (ndy / ry) ** 2) ** 0.5
    return cx + ndx * t, cy + ndy * t


def _angle_to_dir(angle_deg):
    """0=right, 90=down, 180=left, 270=up (SVG convention, Y-down)."""
    rad = math.radians(angle_deg)
    return math.cos(rad), math.sin(rad)


def _cubic_bezier(sx, sy, ex, ey, src_dir, dst_approach_dir, handle_scale=0.4):
    """Return SVG 'd' for a cubic bezier. dst_approach_dir is the direction from outside INTO the target."""
    dist = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    h = dist * handle_scale
    c1x, c1y = sx + src_dir[0] * h, sy + src_dir[1] * h
    c2x, c2y = ex + dst_approach_dir[0] * h, ey + dst_approach_dir[1] * h
    return f"M {sx:.2f} {sy:.2f} C {c1x:.2f} {c1y:.2f} {c2x:.2f} {c2y:.2f} {ex:.2f} {ey:.2f}"


def build_svg_overlay(nodes):
    node_by_id = {n["id"]: n for n in nodes}
    parts = [
        f'<svg viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" preserveAspectRatio="none" overflow="visible" class="skill-tree-svg" xmlns="http://www.w3.org/2000/svg">',
        "<defs>",
        '<path d="M0,0 L0,6 L8,3 z" fill="context-stroke"/></marker></defs>',
    ]

    for node in nodes:
        dst_cx = node["pos_x"]
        dst_cy = node_cy(node["pos_y"])
        dst_secret = node.get("secret", False)
        for dep in node.get("depends_on", []):
            src = node_by_id[dep["id"]]
            src_color = CATEGORY_COLOR[src["category"]]
            src_cx = src["pos_x"]
            src_cy = node_cy(src["pos_y"])
            dx, dy = dst_cx - src_cx, dst_cy - src_cy
            src_angle = dep.get("source_angle")
            dst_angle = dep.get("target_angle")

            if src_angle is not None:
                src_dir = _angle_to_dir(src_angle)
                sx, sy = _ellipse_border(
                    src_cx, src_cy, src_dir[0], src_dir[1], NODE_RADIUS, NODE_Y_RADIUS
                )
            else:
                src_dir = _norm(dx, dy)
                sx, sy = _ellipse_border(
                    src_cx, src_cy, dx, dy, NODE_RADIUS, NODE_Y_RADIUS
                )

            if dst_angle is not None:
                # target_angle = direction from target center to entry point;
                # arrow approaches from outside so its travel direction is the opposite
                entry_dir = _angle_to_dir(dst_angle)
                ex, ey = _ellipse_border(
                    dst_cx,
                    dst_cy,
                    entry_dir[0],
                    entry_dir[1],
                    NODE_RADIUS,
                    NODE_Y_RADIUS,
                )
                dst_approach_dir = (entry_dir[0], entry_dir[1])
            else:
                ex, ey = _ellipse_border(
                    dst_cx, dst_cy, -dx, -dy, NODE_RADIUS, NODE_Y_RADIUS
                )
                dst_approach_dir = _norm(-dx, -dy)

            if src_angle is not None or dst_angle is not None:
                d = _cubic_bezier(sx, sy, ex, ey, src_dir, dst_approach_dir)
            else:
                d = build_arrow_path([(sx, sy), (ex, ey)])
            if d:
                secret_attr = ' class="skill-arrow-secret"' if dst_secret else ""
                parts.append(
                    f'<path{secret_attr} d="{d}" stroke="{src_color}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>'
                )
    for y in DIVIDER_ROWS:
        parts.append(
            f'<line x1="0" y1="{y}" x2="{CANVAS_WIDTH}" y2="{y}" class="skill-tree-divider-line"/>'
        )
    parts.append(
        f'<line x1="0" y1="{SECRET_DIVIDER_ROW}" x2="{CANVAS_WIDTH}" y2="{SECRET_DIVIDER_ROW}" class="skill-tree-divider-line skill-arrow-secret"/>'
    )
    parts.append("</svg>")
    return "".join(parts)


def build_section_labels_html():
    # Section boundaries in SVG units, converted to % (canvas height = 1000)
    sections = [
        (0, DIVIDER_ROWS[0], "Základní (1)"),
        (DIVIDER_ROWS[0], DIVIDER_ROWS[1], "Pokročilá (2)"),
        (DIVIDER_ROWS[1], CANVAS_HEIGHT, "Mistrovská (3)"),
    ]
    parts = []
    for y0, y1, label in sections:
        center_pct = (y0 + y1) / 2 / 10
        parts.append(
            f'<div class="skill-tree-section-label" style="top:{center_pct}%;">'
            f"<strong>{label}</strong>"
            f"</div>"
        )
    secret_center_pct = 1100 / 10
    parts.append(
        f'<div class="skill-tree-section-label skill-node-secret" style="top:{secret_center_pct:.1f}%;">'
        f"<strong>Velmistrovská</strong>"
        f"</div>"
    )
    return "".join(parts)


def generate_contramagic_page():
    template = open("templates/school_of_magic_header.md").read()
    nodes = load_nodes()
    descriptions = spell_contents.parse_contramagic_descriptions()
    secrets = json.load(open("lists/secrets.json"))
    secret_layout = json.loads(
        base64.b64decode(secrets["kontramagie_layout"]).decode("utf-8")
    )
    if isinstance(secret_layout, dict):
        secret_layout = [secret_layout]
    for node in secret_layout:
        node["secret"] = True
        nodes.append(node)
    secret_text = base64.b64decode(secrets["kontramagie"]).decode("utf-8") + "\n"
    names, desc_blocks = spell_contents.split_by_category(secret_text, r"\t(\w.*)\n")
    for name, desc_block in zip(names, desc_blocks):
        descriptions[spell_contents.capitalize_title(name)] = re.findall(
            r"\t\t- (.*)\n", desc_block
        )
    contents = (
        '<div class="skill-tree-container"><div class="skill-tree-grid">'
        + build_svg_overlay(nodes)
        + build_absolute_html(nodes, descriptions)
        + build_section_labels_html()
        + "</div></div>"
        + '<div class="skill-node-secret" style="height:20vh;"></div>'
    )
    return (
        template.replace("$NAME", "Kontramágové")
        .replace("$IMAGE_FIRST", "kontramag.png")
        .replace("$IMAGE_SECOND", "better_times.jpg")
        .replace("$CONTENTS", contents)
    )
