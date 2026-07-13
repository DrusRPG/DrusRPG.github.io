import pathlib
import common


# A wrapper for the tooltip HTML template, `templates/tooltip.html`
class TooltipTemplate:
    def __init__(self):
        self.template = open("templates/tooltip.html").read().replace("\n", "")

    def get_tooltip_html(self, name: str) -> str:
        tooltip_out = self.template
        tooltip_out = tooltip_out.replace("$NAME", common.capitalize_title(name))
        tooltip_out = tooltip_out.replace("$ICON", TooltipTemplate.spell_tooltips[name])
        return tooltip_out

    def get_tooltips_html(self, names: list[str]) -> str:
        return " ".join([self.get_tooltip_html(name) for name in names])

    spell_tooltips = {
        "dotyk": "🖐️",
        "dohled": "👁️",
        "paměť": "💭",
        "sesílatel": "🧙‍♂️",
        "zbraň": "🗡️",
        "požehnání": "🙏",
        "léčení": "❤️",
        "neživý": "🗿",
        "prokletí": "🐈‍⬛",
        "nemrtvý": "🧟",
        "jed": "☠️",
        "hypnóza": "🧿",
        "iluze": "🌀",
        "sugesce": "💡",
        "mentální magie": "🧠",
        "mentální obrana": "🛡️",
        "blesk": "⚡",
        "oheň": "🔥",
        "led": "❄️",
        "země": "🪨",
        "voda": "💧",
        "vzduch": "💨",
        "soustředění": "🧘",
        "bariéra": "🧱",
        "zakřivení": "𖣐",
        "nahlížení": "🔮",
        "projektil": "🏹",
        "duše": "👻",
        "vysátí": "🧛🏻‍♀️",
        "zpomalení": "🐢",
        "zrychlení": "🐇",
        "informace": "🔍",
        "teleportace": "🌀",
        "zestárnutí": "👴",
        "omládnutí": "👶",
        "telekineze": "🎈",
    }


# A wrapper for the spell line HTML template, `templates/spell_line.html`
class SpellLineTemplate:
    def __init__(self):
        self.template = open("templates/spell_line.html").read().replace("\n", "")
        self.tooltip_template = TooltipTemplate()

    def get_spell_line_md(
        self, name: str, modifiers: list[str], description: str, is_secret: bool
    ) -> str:
        spell_out = self.template
        spell_out = spell_out.replace("$NAME", name)
        spell_out = spell_out.replace(
            "$ICONS", self.tooltip_template.get_tooltips_html(modifiers)
        )
        spell_out = spell_out.replace("$DESCRIPTION", description)
        spell_out = spell_out.replace(
            "$GLOW_CLASS", SpellLineTemplate.get_glow_class(modifiers)
        )
        spell_out = spell_out.replace(
            "$SECRET_CLASS", "secret_spell" if is_secret else ""
        )
        spell_out = spell_out.replace("$TAGS", ",".join(modifiers))
        return f"* {spell_out}"

    glow_mapping = {
        "death_glow": {"jed", "vysátí", "duše"},
        "curse_glow": {"prokletí"},
        "undead_glow": {"nemrtvý"},
        "blessing_glow": {"požehnání"},
        "light_glow": {"neživý"},
        "heal_glow": {"léčení"},
        "mental_glow": {"mentální magie", "hypnóza", "sugesce", "nahlížení"},
        "illusion_glow": {"iluze"},
        "fire_glow": {"oheň"},
        "ice_glow": {"led"},
        "lightning_glow": {"blesk"},
        "earth_glow": {"země"},
        "water_glow": {"voda"},
        "air_glow": {"vzduch"},
        "barrier_glow": {"bariéra"},
        "distortion_glow": {"zakřivení"},
    }

    @staticmethod
    def get_glow_class(modifiers: list[str]) -> str:
        for glow_class, keywords in SpellLineTemplate.glow_mapping.items():
            if any(modifier in keywords for modifier in modifiers):
                return glow_class
        return "neutral_glow"


_spell_line_template = SpellLineTemplate()
_magic_school_template = common.MagicSchoolTemplate()


def spell_to_markdown(spell: common.Spell) -> str:
    return _spell_line_template.get_spell_line_md(
        spell.name, spell.tags, spell.formatted_description(), spell.secret
    )


def category_to_markdown(name: str, spell_category: common.SpellCategory) -> str:
    items = [spell_to_markdown(spell) for spell in spell_category.spells]
    return (
        f"\n<h2{' class="secret_header"' if spell_category.is_secret() else ''}>{common.capitalize_title(name)}</h2>\n\n"
        + "\n".join(items)
    )


def filter_bar_to_html(filter_tags: list[str]) -> str:
    tooltip_template = _spell_line_template.tooltip_template
    buttons = "".join(
        f'<button class="filter-btn active" data-filter="{tag}">'
        f"{tooltip_template.get_tooltip_html(tag)}</button>"
        for tag in filter_tags
    )
    return f'<div class="spell-filter-bar" data-filters="{",".join(filter_tags)}">{buttons}</div>'


def school_to_markdown(
    name: str,
    image_first: str,
    image_second: str,
    spells_by_tier: dict[str, list[common.Spell]],
    filter_tags: list[str] | None = None,
) -> str:
    categories_md = [
        category_to_markdown(tier, spells) for tier, spells in spells_by_tier.items()
    ]
    filter_bar = filter_bar_to_html(filter_tags) + "\n\n" if filter_tags else ""
    return _magic_school_template.get_school_markdown(
        name=name,
        image_first=image_first,
        image_second=image_second,
        contents=filter_bar + "\n\n".join(categories_md),
        nav_group="Magie",
    )


class MagicSettings:
    def __init__(
        self,
        header: str,
        filename: str,
        image_first: str,
        image_second: str,
        filter_tags: list[str],
    ):
        self.header = header
        self.filename = filename
        self.image_first = image_first
        self.image_second = image_second
        self.filter_tags = filter_tags


school_settings = [
    MagicSettings(
        "Magie Času",
        "cas",
        "clock.jpg",
        "ancient_times1.jpeg",
        [
            "nahlížení",
            "zrychlení",
            "zpomalení",
            "zestárnutí",
            "omládnutí",
            "teleportace",
        ],
    ),
    MagicSettings(
        "Magie Prostoru",
        "prostor",
        "prostor.jpg",
        "ancient_times2.jpeg",
        ["bariéra", "zakřivení", "teleportace"],
    ),
    MagicSettings(
        "Magie Života",
        "zivot",
        "light.jpg",
        "ancient_times3.jpeg",
        ["požehnání", "léčení", "informace", "neživý"],
    ),
    MagicSettings(
        "Magie Smrti",
        "smrt",
        "dark.jpg",
        "ancient_times4.jpeg",
        ["prokletí", "jed", "nemrtvý", "duše", "vysátí"],
    ),
    MagicSettings(
        "Magie Hmoty",
        "hmota",
        "matter.jpg",
        "ancient_times5.jpeg",
        ["projektil", "zbraň", "oheň", "vzduch", "země", "voda", "led", "blesk"],
    ),
    MagicSettings(
        "Magie Mysli",
        "mysl",
        "neural.jpg",
        "ancient_times6.jpeg",
        [
            "mentální magie",
            "hypnóza",
            "sugesce",
            "iluze",
            "mentální obrana",
            "telekineze",
        ],
    ),
]


def main():
    out_path = pathlib.Path("DrusMagie/content/magic")
    out_path.mkdir(parents=True, exist_ok=True)

    for s in school_settings:
        spells = common.parse_magic_file(pathlib.Path(f"lists/{s.filename}.txt"))
        spells_secret = common.parse_magic_file_s(
            common.parse_secrets(s.filename), secret=True
        )

        md = school_to_markdown(
            s.header,
            s.image_first,
            s.image_second,
            spells.spells() | spells_secret.spells(),
            s.filter_tags,
        )
        with open(out_path / f"{s.filename}.md", "w") as f:
            f.write(md)
