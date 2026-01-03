import re
import pathlib


    



# input files: (School name, spell list name, first header image, second header image) 
input_files = [
    ("Magie Času", "cas", "clock.jpg", "ancient_times1.jpeg"),
    ("Magie Prostoru", "prostor", "prostor.jpg", "ancient_times2.jpeg"),
    ("Magie Života", "zivot", "light.jpg", "ancient_times3.jpeg"),
    ("Magie Smrti", "smrt", "dark.jpg", "ancient_times4.jpeg"),
    ("Magie Hmoty", "hmota", "matter.jpg", "ancient_times5.jpeg"),
    ("Magie Mysli", "mysl", "neural.jpg", "ancient_times6.jpeg"),
]




class TooltipTemplate:
    def __init__(self):
        self.template = open("templates/tooltip.html").read().replace("\n", "")

    def get_tooltip_html(self, name: str) -> str:
        tooltip_out = self.template
        tooltip_out = tooltip_out.replace("$NAME", capitalize_title(name))
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
        "neživý": "💀",
        "prokletí": "🐈‍⬛",
        "nemrtvý": "🧟",
        "jed": "☠️",
        "hypnóza": "🧿",
        "iluze": "🌀",
        "sugesce": "💡",
        "mentální magie": "🧠",
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
        "vysátí": "🧛🏻‍♀️"
    }



def capitalize_title(title: str):
    words = re.split(r"([ /])", title)
    no_capitalize = ["v", "do", "na", "ke", "ve", "k"]
    result = "".join([word.capitalize() if word not in no_capitalize else word for word in words])
    return result


class SpellLineTemplate:
    def __init__(self):
        self.template = open("templates/spell_line.html").read().replace("\n", "")

    def get_spell_line_md(self, name: str, modifiers: str, description: str) -> str:
        spell_out = self.template
        spell_out = spell_out.replace("$NAME", name)
        spell_out = spell_out.replace("$ICONS", modifiers)
        spell_out = spell_out.replace("$DESCRIPTION", description)
        return f"* {spell_out}"



class MagicSchoolTemplate:
    def __init__(self):
        self.template = open("templates/school_of_magic_header.md").read()

    def get_school_markdown(self, name: str, image_first: str, image_second: str, contents: str) -> str:
        replacements = {
            "NAME": name,
            "IMAGE_FIRST": image_first,
            "IMAGE_SECOND": image_second,
            "CONTENTS": contents
        }

        school_out = self.template
        for key, value in replacements.items():
            school_out = school_out.replace(f"${key}", value)
        
        return school_out






class Spell:
    # A template for a single spell tooltip
    tooltip_template = TooltipTemplate()

    def __init__(self, name: str, description_lines: str):
        name_and_modifiers = name.split(" -- ")
        self.name = capitalize_title(name_and_modifiers[0])
        self.modifiers = name_and_modifiers[1:]
        self.description_lines = re.findall(r"\t\t- (.*)\n", description_lines)

    def to_markdown(self) -> str:
        icons = Spell.tooltip_template.get_tooltips_html(self.modifiers)
        return spell_line_template.get_spell_line_md(self.name, icons, "<br><br>".join(self.description_lines))
    

class SpellCategory:
    def __init__(self, name: str, contents: str):
        self.name = capitalize_title(name)
        spell_names, descriptions = split_by_category(contents, r"\t(\w.*)\n")
        self.spells = [
            Spell(name, description)
            for name, description in zip(spell_names, descriptions)
        ]

    def to_markdown(self) -> str:
        items = [spell.to_markdown() for spell in self.spells]
        return f"\n## {self.name}\n\n" + "\n".join(items)


class SchoolOfMagic:
    # a Hugo markdown template for rendering a magic school
    magic_school_template = MagicSchoolTemplate()
    
    def __init__(self, name: str, image_first: str, image_second: str, contents: str):
        self.name = name
        self.image_first = image_first
        self.image_second = image_second
        
        # This regex gets all the category names (Základní, Pokročilé, Mistrovské)
        category_names, spells = split_by_category(contents, r"(\w+):\n")
        self.spell_categories = [
            SpellCategory(category, spell_block)
            for category, spell_block in zip(category_names, spells)
        ]

    def to_markdown(self) -> str:
        return SchoolOfMagic.magic_school_template.get_school_markdown(
            name=self.name,
            image_first=self.image_first,
            image_second=self.image_second,
            contents="\n\n".join([category.to_markdown() for category in self.spell_categories])
        )  



def regex_split(contents: str, regex: str):
    # This splits the file into several blocks of spells based on the category names
    split_rows = re.split(regex.replace("(", "").replace(")", ""), contents)[1:]
    return split_rows

def split_by_category(contents: str, regex: str):
    # This regex gets all the category names (Základní, Pokročilé, Mistrovské)
    split_words = re.findall(regex, contents)
    # This splits the file into several blocks of spells based on the category names
    split_rows = regex_split(contents, regex)

    return split_words, split_rows




# A template for a single spell line
spell_line_template = SpellLineTemplate()


def main():
    # create the output directory
    out_path = pathlib.Path("DrusMagie/content/magic")
    out_path.mkdir(parents=True, exist_ok=True)

    # go over all individual schools
    for magic_school_name, magic_school_file, magic_school_image, magic_school_image_2 in input_files:
        school = SchoolOfMagic(
            magic_school_name,
            magic_school_image,
            magic_school_image_2,
            open(f"lists/{magic_school_file}.txt").read()
        )
        # save the resulting markdown
        with open(out_path/f"{magic_school_file}.md", "w") as f:
            f.write(school.to_markdown())

if __name__ == "__main__":
    main()