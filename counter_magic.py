import json
import math
import common
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CounterMagicConfig:
    canvas_width: int = 100
    canvas_height: int = 100
    node_radius: int = 7.5
    grid_aspect: float = 0.7  # must match CSS aspect-ratio of .skill-tree-grid
    divider_rows: list = field(default_factory=lambda: [37, 70])
    secret_divider_row: int = 102
    color_bg: dict = field(
        default_factory=lambda: {
            "defense": "rgb(30,45,70)",
            "cancel": "rgb(62,30,34)",
            "sense": "rgb(24,56,64)",
            "ritual": "rgb(67,50,34)",
            "tracking": "rgb(30,56,34)",
        }
    )
    category_color: dict = field(
        default_factory=lambda: {
            "defense": "#0000cc",
            "cancel": "#cc0000",
            "sense": "#00cccc",
            "ritual": "#cc8400",
            "tracking": "#006600",
        }
    )

    @property
    def node_y_radius(self):
        # circle Y-extent in SVG units differs from X due to non-square grid
        return self.node_radius * self.grid_aspect

    def get_glow_class(self, pos_y: int) -> str:
        if pos_y < self.divider_rows[0]:
            return "glow-low"
        if pos_y < self.divider_rows[1]:
            return "glow-mid"
        if pos_y < self.secret_divider_row:
            return "glow-huge"
        return "glow-insane"


class CounterMagicHTML:
    def __init__(self, config: CounterMagicConfig):
        self._config = config

    def _create_circles(self, nodes, spell_dict: dict[str, common.Spell]):
        pieces = []
        for node in nodes:
            cx = node["pos_x"]
            cy = node["pos_y"]
            left = cx - self._config.node_radius
            top = cy - self._config.node_y_radius
            color = node["category"]
            name = node["name"]
            node_id = node["id"]
            bg = self._config.color_bg[color]
            icon_html = f'<img class="skill-icon" src="/icons/{color}.png" alt="">'
            glow_class = self._config.get_glow_class(cy)
            glow_class_str = f" {glow_class}" if glow_class else ""
            glow_color = self._config.category_color[color]
            spell = spell_dict[node_id]
            desc_html = spell.formatted_description()
            popup_html = (
                f'<div class="skill-popup">'
                f"<strong>{node_id}</strong>"
                f"{'<br><br>' + desc_html if desc_html else ''}"
                f"</div>"
            )
            secret_class = " skill-node-secret" if spell.secret else ""
            pieces.append(
                f'<div class="skill-node{secret_class}" style="left:{left}%;top:{top}%;">'
                f'<div class="skill-circle color-{color}{glow_class_str}" style="--glow-color:{glow_color};border-color:{self._config.category_color[color]};background:{bg};">{icon_html}</div>'
                f'<span class="skill-label">{name}</span>'
                f"{popup_html}"
                f"</div>"
            )
        return "".join(pieces)

    @staticmethod
    def _create_section_label(label, is_secret, pos):
        secret_class = " skill-node-secret" if is_secret else ""
        return (
            f'<div class="skill-tree-section-label{secret_class}" style="top:{pos:.1f}%;">'
            f"<strong>{label}</strong>"
            f"</div>"
        )

    def _create_section_labels(self):
        sections = [
            (0, self._config.divider_rows[0], "Základní (1)"),
            (
                self._config.divider_rows[0],
                self._config.divider_rows[1],
                "Pokročilá (2)",
            ),
            (
                self._config.divider_rows[1],
                self._config.canvas_height,
                "Mistrovská (3)",
            ),
        ]
        parts = [
            self._create_section_label(label, False, (y0 + y1) / 2)
            for y0, y1, label in sections
        ]
        parts.append(self._create_section_label("Velmistrovská", True, 110))
        return "".join(parts)

    def create_html(self, nodes, spell_dict: dict[str, common.Spell]):
        return self._create_circles(nodes, spell_dict) + self._create_section_labels()


class CounterMagicSVG:
    """Holds connecting lines and dividing lines for the counter magic grid SVG."""

    @staticmethod
    def __norm(dx, dy):
        length = (dx * dx + dy * dy) ** 0.5
        return (dx / length, dy / length) if length else (0, 0)

    @staticmethod
    def __build_line(x0, y0, x1, y1):
        return f"M {x0} {y0} L {x1} {y1}"

    @staticmethod
    def __ellipse_border(cx, cy, dx, dy, rx, ry):
        """Return the point on the ellipse border at (cx,cy) in direction (dx,dy)."""
        length = (dx * dx + dy * dy) ** 0.5
        if not length:
            return cx, cy
        ndx, ndy = dx / length, dy / length
        t = 1.0 / ((ndx / rx) ** 2 + (ndy / ry) ** 2) ** 0.5
        return cx + ndx * t, cy + ndy * t

    @staticmethod
    def __angle_to_dir(angle_deg):
        """0=right, 90=down, 180=left, 270=up (SVG convention, Y-down)."""
        rad = math.radians(angle_deg)
        return math.cos(rad), math.sin(rad)

    @staticmethod
    def __cubic_bezier(sx, sy, ex, ey, src_dir, dst_approach_dir, handle_scale=0.4):
        """Return SVG 'd' for a cubic bezier. dst_approach_dir is the direction from outside INTO the target."""
        dist = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        h = dist * handle_scale
        c1x, c1y = sx + src_dir[0] * h, sy + src_dir[1] * h
        c2x, c2y = ex + dst_approach_dir[0] * h, ey + dst_approach_dir[1] * h
        return f"M {sx:.2f} {sy:.2f} C {c1x:.2f} {c1y:.2f} {c2x:.2f} {c2y:.2f} {ex:.2f} {ey:.2f}"

    @staticmethod
    def __create_line(
        start_circle_x,
        start_circle_y,
        end_circle_x,
        end_circle_y,
        color,
        node_radius,
        node_y_radius,
        src_angle=None,
        dst_angle=None,
        secret=False,
    ):
        dx, dy = end_circle_x - start_circle_x, end_circle_y - start_circle_y

        if src_angle is not None:
            src_dir = CounterMagicSVG.__angle_to_dir(src_angle)
            sx, sy = CounterMagicSVG.__ellipse_border(
                start_circle_x,
                start_circle_y,
                src_dir[0],
                src_dir[1],
                node_radius,
                node_y_radius,
            )
        else:
            src_dir = CounterMagicSVG.__norm(dx, dy)
            sx, sy = CounterMagicSVG.__ellipse_border(
                start_circle_x, start_circle_y, dx, dy, node_radius, node_y_radius
            )

        if dst_angle is not None:
            # target_angle = direction from target center to entry point;
            # arrow approaches from outside so its travel direction is the opposite
            entry_dir = CounterMagicSVG.__angle_to_dir(dst_angle)
            ex, ey = CounterMagicSVG.__ellipse_border(
                end_circle_x,
                end_circle_y,
                entry_dir[0],
                entry_dir[1],
                node_radius,
                node_y_radius,
            )
            dst_approach_dir = (entry_dir[0], entry_dir[1])
        else:
            ex, ey = CounterMagicSVG.__ellipse_border(
                end_circle_x, end_circle_y, -dx, -dy, node_radius, node_y_radius
            )
            dst_approach_dir = CounterMagicSVG.__norm(-dx, -dy)

        if src_angle is not None or dst_angle is not None:
            d = CounterMagicSVG.__cubic_bezier(
                sx, sy, ex, ey, src_dir, dst_approach_dir
            )
        else:
            d = CounterMagicSVG.__build_line(sx, sy, ex, ey)

        secret_attr = ' class="skill-arrow-secret"' if secret else ""
        return f'<path{secret_attr} d="{d}" stroke="{color}" stroke-width="0.2" fill="none" marker-end="url(#arrow)"/>'

    @staticmethod
    def __create_divider_row(y_pos, canvas_width, secret=False):
        cls = (
            'class="skill-tree-divider-line skill-arrow-secret"'
            if secret
            else 'class="skill-tree-divider-line"'
        )
        return f'<line x1="0" y1="{y_pos}" x2="{canvas_width}" y2="{y_pos}" {cls}/>'

    def create_svg(self, nodes, config: CounterMagicConfig):
        node_by_id = {n["id"]: n for n in nodes}
        parts = [
            f'<svg viewBox="0 0 {config.canvas_width} {config.canvas_height}" preserveAspectRatio="none" overflow="visible" class="skill-tree-svg" xmlns="http://www.w3.org/2000/svg">',
            "<defs>",
            '<path d="M0,0 L0,6 L8,3 z" fill="context-stroke"/></marker></defs>',
        ]
        # Create node arrows
        for node in nodes:
            dst_secret = node.get("secret", False)
            for dep in node.get("depends_on", []):
                src = node_by_id[dep["id"]]
                line_svg = self.__create_line(
                    src["pos_x"],
                    src["pos_y"],
                    node["pos_x"],
                    node["pos_y"],
                    config.category_color[src["category"]],
                    config.node_radius,
                    config.node_y_radius,
                    src_angle=dep.get("source_angle"),
                    dst_angle=dep.get("target_angle"),
                    secret=dst_secret,
                )
                parts.append(line_svg)

        # Create divider rows
        for y in config.divider_rows:
            parts.append(self.__create_divider_row(y, config.canvas_width))
        parts.append(
            self.__create_divider_row(
                config.secret_divider_row, config.canvas_width, secret=True
            )
        )
        parts.append("</svg>")
        return "".join(parts)


def generate_counter_magic_page():
    # load normal files
    config = CounterMagicConfig()
    nodes = json.load(open("lists/kontramagie_layout.json"))
    spells = common.parse_magic_file(Path("lists/kontramagie.txt")).spells_flat()

    # load secrets
    secret_layout_str, secret_text_raw = common.parse_secrets(
        "kontramagie_layout", "kontramagie"
    )
    secret_nodes = json.loads(secret_layout_str)
    secret_spells = common.parse_magic_file_s(
        secret_text_raw, secret=True
    ).spells_flat()

    nodes.extend(secret_nodes)
    spells.extend(secret_spells)

    spell_dict = {}
    for spell in spells:
        spell_dict[spell.name] = spell
    contents = f"""
<div class="skill-tree-container">
    <div class="skill-tree-grid">
        {CounterMagicSVG().create_svg(nodes, config)}
        {CounterMagicHTML(config).create_html(nodes, spell_dict)}
    </div>
</div>
<div class="skill-node-secret" style="height:20vh;"></div>
"""
    return common.MagicSchoolTemplate().get_school_markdown(
        name="Kontramágové",
        image_first="kontramag.png",
        image_second="better_times.jpg",
        contents=contents,
    )


def main():
    out_path = Path("DrusMagie/content/magic")
    out_path.mkdir(parents=True, exist_ok=True)
    with open(out_path / "kontramagie.md", "w") as f:
        f.write(generate_counter_magic_page())
