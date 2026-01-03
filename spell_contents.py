import re
import pathlib


    








# Capitalize a spell or category title
# Tries to use the english capitalization, (Using Camel Case for Everything Except Czech Prepositions)
def capitalize_title(title: str):
    # split by or slashes
    words = re.split(r"([ /])", title)
    # the prepositions that should not be capitalized
    no_capitalize = ["v", "do", "na", "ke", "ve", "k"]
    # capitalize each word unless it's in the no_capitalize list
    return "".join([word.capitalize() if word not in no_capitalize else word for word in words])





# A wrapper for the tooltip HTML template, `templates/tooltip.html`
class TooltipTemplate:
    def __init__(self):
        self.template = open("templates/tooltip.html").read().replace("\n", "")

    # Get the HTML for a single tooltip, from the tooltip name (e.g., "dotyk", "dohled", etc.)
    def get_tooltip_html(self, name: str) -> str:
        tooltip_out = self.template
        tooltip_out = tooltip_out.replace("$NAME", capitalize_title(name))
        tooltip_out = tooltip_out.replace("$ICON", TooltipTemplate.spell_tooltips[name])
        return tooltip_out
    
    # Get the HTML for several tooltips, from a list of tooltip names
    def get_tooltips_html(self, names: list[str]) -> str:
        return " ".join([self.get_tooltip_html(name) for name in names])
    
    # This is the list of available spell tooltips and their corresponding icons
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


# A wrapper for the spell line HTML template, `templates/spell_line.html`
# This will produce markdown corresponding to a single spell
class SpellLineTemplate:
    def __init__(self):
        self.template = open("templates/spell_line.html").read().replace("\n", "")
        self.tooltip_template = TooltipTemplate()

    # Get the markdown string for a single spell line, given name, modifiers, and description
    def get_spell_line_md(self, name: str, modifiers: str, description: str) -> str:
        spell_out = self.template
        spell_out = spell_out.replace("$NAME", name)
        spell_out = spell_out.replace("$ICONS", self.tooltip_template.get_tooltips_html(self.modifiers))
        spell_out = spell_out.replace("$DESCRIPTION", description)
        return f"* {spell_out}"


# A wrapper for the magic school markdown template, `templates/school_of_magic_header.md`
# This will produce markdown corresponding to an entire magic school
class MagicSchoolTemplate:
    def __init__(self):
        self.template = open("templates/school_of_magic_header.md").read()

    # Get the markdown string for an entire magic school, given name, background images, and a markdown listing all the spells
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










# Represents a single, parsed spell - includes name, modifiers (icons), and description lines
class Spell:
    # A template for a single spell line
    spell_line_template = SpellLineTemplate()

    def __init__(self, name: str, description_lines: str):
        """
        Create a spell from a part of the spell list file.
        
        :param name: The spell name (with modifiers separated by " -- ")
        :type name: str
        :param description_lines: The spell description lines (each line starting with "\t\t- ")
        :type description_lines: str
        """
        name_and_modifiers = name.split(" -- ")
        self.name = capitalize_title(name_and_modifiers[0])
        self.modifiers = name_and_modifiers[1:]
        self.description_lines = re.findall(r"\t\t- (.*)\n", description_lines)

    def to_markdown(self) -> str:
        return Spell.spell_line_template.get_spell_line_md(self.name, self.modifiers, "<br><br>".join(self.description_lines))
    

# A spell category - e.g., Základní, Pokročilé, Mistrovské, etc. with all the included spells
class SpellCategory:
    def __init__(self, name: str, contents: str):
        """
        Create a spell category (e.g., Základní, Pokročilé, Mistrovské) from a part of the spell list file.
        
        :param name: The category name
        :type name: str
        :param contents: The part of the spell list file corresponding to this category
        :type contents: str
        """
        self.name = capitalize_title(name)
        spell_names, descriptions = split_by_category(contents, r"\t(\w.*)\n")
        self.spells = [
            Spell(name, description)
            for name, description in zip(spell_names, descriptions)
        ]

    # Convert the entire category to markdown. This includes a header and all the spells
    def to_markdown(self) -> str:
        items = [spell.to_markdown() for spell in self.spells]
        return f"\n## {self.name}\n\n" + "\n".join(items)


# A full school of magic, with name, images, and all the spell categories
class SchoolOfMagic:
    # a Hugo markdown template for rendering a magic school
    magic_school_template = MagicSchoolTemplate()
    
    def __init__(self, name: str, image_first: str, image_second: str, contents: str):
        """
        Docstring for __init__
        
        :param name: The name of the school of magic
        :type name: str
        :param image_first: The filename of the header image
        :type image_first: str
        :param image_second: The filename of the secret (Drus) image
        :type image_second: str
        :param contents: The full contents of the spell list file
        :type contents: str
        """
        self.name = name
        self.image_first = image_first
        self.image_second = image_second
        
        # This regex gets all the category names (Základní, Pokročilé, Mistrovské)
        category_names, spells = split_by_category(contents, r"(\w+):\n")
        self.spell_categories = [
            SpellCategory(category, spell_block)
            for category, spell_block in zip(category_names, spells)
        ]

    # Convert the entire school of magic to markdown
    def to_markdown(self) -> str:
        return SchoolOfMagic.magic_school_template.get_school_markdown(
            name=self.name,
            image_first=self.image_first,
            image_second=self.image_second,
            contents="\n\n".join([category.to_markdown() for category in self.spell_categories])
        )  



def regex_split(contents: str, regex: str):
    """
    Split the contents string by the given regex. We assume a form of (REGEX)(CONTENT)(REGEX)(CONTENT)... and return only the CONTENT parts.
    
    :param contents: The full string to split
    :type contents: str
    :param regex: The regex pattern to split by
    :type regex: str
    """
    # This splits the file into several blocks of spells based on the category names
    split_rows = re.split(regex.replace("(", "").replace(")", ""), contents)[1:]
    return split_rows

def split_by_category(contents: str, regex: str):
    """
    Split the contents string into categories based on the given regex. For (REGEX1)(CONTENT1)(REGEX2)(CONTENT2)..., we return ([REGEX1, REGEX2,...], [CONTENT1, CONTENT2,...])
    
    :param contents: The full string to split
    :type contents: str
    :param regex: The regex pattern to identify categories
    :type regex: str
    """
    # This regex gets all the category names (Základní, Pokročilé, Mistrovské)
    split_words = re.findall(regex, contents)
    # This splits the file into several blocks of spells based on the category names
    split_rows = regex_split(contents, regex)

    return split_words, split_rows





def main():
    # input files: (School name, spell list name, first header image, second header image) 
    input_files = [
        ("Magie Času", "cas", "clock.jpg", "ancient_times1.jpeg"),
        ("Magie Prostoru", "prostor", "prostor.jpg", "ancient_times2.jpeg"),
        ("Magie Života", "zivot", "light.jpg", "ancient_times3.jpeg"),
        ("Magie Smrti", "smrt", "dark.jpg", "ancient_times4.jpeg"),
        ("Magie Hmoty", "hmota", "matter.jpg", "ancient_times5.jpeg"),
        ("Magie Mysli", "mysl", "neural.jpg", "ancient_times6.jpeg"),
    ]

    # create the output directory
    out_path = pathlib.Path("DrusMagie/content/magic")
    out_path.mkdir(parents=True, exist_ok=True)

    # go over all individual schools
    for magic_school_name, magic_school_file, magic_school_image, magic_school_image_2 in input_files:
        # Create a school of magic from the corresponding spell list file
        school = SchoolOfMagic(
            magic_school_name,
            magic_school_image,
            magic_school_image_2,
            open(f"lists/{magic_school_file}.txt").read()
        )
        # Save the markdown of the magic school
        with open(out_path/f"{magic_school_file}.md", "w") as f:
            f.write(school.to_markdown())

if __name__ == "__main__":
    main()