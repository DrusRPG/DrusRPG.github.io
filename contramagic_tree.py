import json

GRID_COLS = 5
GRID_ROWS = 6
CELL_WIDTH_PX = 300
CELL_HEIGHT_PX = 200
DIVIDER_ROWS = [2, 4]
CORNER_RADIUS = 20


def load_nodes(path="lists/kontramagove.json"):
    return json.load(open(path))


def build_grid_html(nodes):
    pieces = ['<div class="skill-tree-container"><div class="skill-tree-grid">']
    for node in nodes:
        col, row = node["pos_x"], node["pos_y"]
        color = node.get("border_color", "#888")
        name = node["name"]
        pieces.append(
            f'<div class="skill-box" style="grid-column:{col};grid-row:{row};border-color:{color};">{name}</div>'
        )
    pieces.append("</div>")
    return "".join(pieces)


def grid_to_px(x, y):
    return ((x - 1) * CELL_WIDTH_PX + CELL_WIDTH_PX / 2,
            (y - 1) * CELL_HEIGHT_PX + CELL_HEIGHT_PX / 2)


def _norm(dx, dy):
    length = (dx * dx + dy * dy) ** 0.5
    return (dx / length, dy / length) if length else (0, 0)


def build_arrow_path(waypoints):
    pts = [grid_to_px(w[0], w[1]) for w in waypoints]
    if len(pts) < 2:
        return ""
    d = [f"M {pts[0][0]} {pts[0][1]}"]
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        nx, ny = _norm(px - pts[i-1][0], py - pts[i-1][1])
        ox, oy = _norm(pts[i+1][0] - px, pts[i+1][1] - py)
        ax, ay = px - nx * CORNER_RADIUS, py - ny * CORNER_RADIUS
        bx, by = px + ox * CORNER_RADIUS, py + oy * CORNER_RADIUS
        d.append(f"L {ax} {ay} C {px} {py} {px} {py} {bx} {by}")
    d.append(f"L {pts[-1][0]} {pts[-1][1]}")
    return " ".join(d)


def build_svg_overlay(nodes):
    w = GRID_COLS * CELL_WIDTH_PX
    h = GRID_ROWS * CELL_HEIGHT_PX
    parts = [
        f'<svg viewBox="0 0 {w} {h}" class="skill-tree-svg" xmlns="http://www.w3.org/2000/svg">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L8,3 z" fill="context-stroke"/></marker></defs>',
    ]
    for row in DIVIDER_ROWS:
        y = row * CELL_HEIGHT_PX
        parts.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" class="skill-tree-divider-line"/>')
    for node in nodes:
        color = node.get("border_color", "#888")
        for dep in node.get("depends_on", []):
            d = build_arrow_path(dep.get("arrow_parameters", []))
            if d:
                parts.append(
                    f'<path d="{d}" stroke="{color}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>'
                )
    parts.append("</svg>")
    return "".join(parts)


def generate_contramagic_page():
    template = open("templates/school_of_magic_header.md").read()
    nodes = load_nodes()
    contents = build_grid_html(nodes) + build_svg_overlay(nodes) + "</div>"
    return (template
            .replace("$NAME", "Kontramágové")
            .replace("$IMAGE_FIRST", "clock.jpg")
            .replace("$IMAGE_SECOND", "ancient_times1.jpg")
            .replace("$CONTENTS", contents))
