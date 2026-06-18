import json

CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 1000
NODE_RADIUS = 75
GRID_ASPECT = 0.7  # must match CSS aspect-ratio of .skill-tree-grid
NODE_Y_RADIUS = (
    NODE_RADIUS * GRID_ASPECT
)  # circle Y-extent in SVG units differs from X due to non-square grid
DIVIDER_ROWS = [350, 720]
CORNER_RADIUS = 20

COLOR_ICON = {
    "blue": "defense.png",
    "red": "cancel.png",
    "black": "sense.png",
    "orange": "ritual.png",
    "green": "tracking.png",
}

COLOR_BG = {
    "blue": "rgb(38,56,88)",
    "red": "rgb(77,38,42)",
    "black": "rgb(32,32,34)",
    "orange": "rgb(84,63,42)",
    "green": "rgb(38,70,42)",
}


def load_nodes(path="lists/kontramagove.json"):
    return json.load(open(path))


def node_cy(row_y):
    return 100 + row_y * 180


def build_absolute_html(nodes):
    pieces = []
    for node in nodes:
        cx = node["pos_x"]
        cy = node_cy(node["pos_y"])
        left = (cx - NODE_RADIUS) / 10
        top = (cy - NODE_RADIUS) / 10
        color = node.get("border_color", "#888")
        name = node["name"]
        icon = COLOR_ICON.get(color, "")
        bg = COLOR_BG.get(color, "rgba(0,0,0,0.3)")
        icon_html = (
            f'<img class="skill-icon" src="/icons/{icon}" alt="">' if icon else ""
        )
        pieces.append(
            f'<div class="skill-node" style="left:{left}%;top:{top}%;">'
            f'<div class="skill-circle color-{color}" style="border-color:{color};background:{bg};">{icon_html}</div>'
            f'<span class="skill-label">{name}</span>'
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


def build_svg_overlay(nodes):
    node_by_id = {n["id"]: n for n in nodes}
    parts = [
        f'<svg viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" preserveAspectRatio="none" class="skill-tree-svg" xmlns="http://www.w3.org/2000/svg">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L8,3 z" fill="context-stroke"/></marker></defs>',
    ]
    for y in DIVIDER_ROWS:
        parts.append(
            f'<line x1="0" y1="{y}" x2="{CANVAS_WIDTH}" y2="{y}" class="skill-tree-divider-line"/>'
        )
    for node in nodes:
        dst_cx = node["pos_x"]
        dst_cy = node_cy(node["pos_y"])
        dst_top = dst_cy - NODE_RADIUS
        for dep in node.get("depends_on", []):
            src = node_by_id[dep["id"]]
            src_color = src.get("border_color", "#888")
            src_cx = src["pos_x"]
            src_cy = node_cy(src["pos_y"])
            src_bottom = src_cy - NODE_RADIUS + 2 * NODE_Y_RADIUS
            d = build_arrow_path([(src_cx, src_bottom), (dst_cx, dst_top)])
            if d:
                parts.append(
                    f'<path d="{d}" stroke="{src_color}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>'
                )
    parts.append("</svg>")
    return "".join(parts)


def generate_contramagic_page():
    template = open("templates/school_of_magic_header.md").read()
    nodes = load_nodes()
    contents = (
        '<div class="skill-tree-container"><div class="skill-tree-grid">'
        + build_svg_overlay(nodes)
        + build_absolute_html(nodes)
        + "</div></div>"
    )
    return (
        template.replace("$NAME", "Kontramágové")
        .replace("$IMAGE_FIRST", "kontramag.png")
        .replace("$IMAGE_SECOND", "ancient_times1.jpg")
        .replace("$CONTENTS", contents)
    )
