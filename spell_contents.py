import string
import pathlib
import html


# save the given string with the given filename
def save(fname, data):
    with open(fname, "w") as f:
        f.write(data)


# a Hugo markdown template for rendering a magic school
school_template = open("templates/school_of_magic_header.md").read()


# input files: (School name, spell list name, first header image, second header image) 
input_files = [
    ("Magie Času", "cas", "clock.jpg", "ancient_times1.jpeg"),
    ("Magie Prostoru", "prostor", "prostor.jpg", "ancient_times2.jpeg"),
    ("Magie Života", "zivot", "light.jpg", "ancient_times3.jpeg"),
    ("Magie Smrti", "smrt", "dark.jpg", "ancient_times4.jpeg"),
    ("Magie Hmoty", "hmota", "matter.jpg", "ancient_times5.jpeg"),
    ("Magie Mysli", "mysl", "neural.jpg", "ancient_times6.jpeg"),
]

description_files = [
    ("Magie Času", "cas-popisky"),
    ("Magie Prostoru", "prostor-popisky"),
    ("Magie Života", "zivot-popisky"),
    ("Magie Smrti", "smrt-popisky"),
    ("Magie Hmoty", "hmota-popisky"),
    ("Magie Mysli", "mysl-popisky"),
]

def split_descriptions(description_file_lines):
    description_dict = {}
    current_spell = None
    current_spell_description = []
    for line in description_file_lines:
        # skip pure-whitespace lines
        if line.isspace():
            continue
        if len(line) == 0:
            continue
        # skip lines with spell ranks (e.g. "Základní:")
        if line.strip().endswith(":"):
            continue
        
        if line.strip().startswith("- "):
            current_spell_description.append(line.strip()[2:])
            if current_spell is not None:
                description_dict[current_spell] = "<br><br>".join(current_spell_description).strip()
        else:
            current_spell = line.strip()
            current_spell_description = []
            
    return description_dict

# ... take the lines of the read spell file, and split them into a dictionary of type
# {
#       spell_tier_1: [spell1, spell2, ...],
#       spell_tier_2: [...],
#       ...
# }
# Spell tiers have no defined names - each line that has no indentation is considered to be a spell type, ...
# ... and all lines below it are considered to be spells in that category.
def split_spells(spell_file_lines):
    split = {}
    current = []
    current_name = None
    for line in spell_file_lines:
        # skip pure-whitespace lines
        if line.isspace():
            continue
        if len(line) == 0:
            continue

        if line[0] in string.whitespace:
            current.append(line.strip())
        else:
            if current_name is not None:
                split[current_name] = current
            current_name = line.strip()
            current = []
    if current_name is not None:
        split[current_name] = current

    return split

def replace_spell_tags(spellpart):
    for replace_keyword, replacement in replace_keywords.items():
        # see whether the selected part matches a replacement keyword
        if replace_keyword in spellpart:
            result = f" {replacement}"
            break
        else:
            # if not, just join the parts back together
            result = spellpart
    return result


# if a spell is of the form **** -- keyword, we replace the ' -- keyword' with the given replacement template
# this can be a simple string, or a {{<XXX>}} for a hugo template in 'DrusMagie/layouts/_shortcodes/*'
replace_keywords = {
    "dotyk": "{{<dotyk_tooltip>}}",
    "dohled": "{{<dohled_tooltip>}}",
    "paměť": "{{<pamet_tooltip>}}",
    "sesílatel": "{{<sesilatel_tooltip>}}",
    "zbraň": "{{<zbran_tooltip>}}",
    "požehnání": "{{<pozehnani_tooltip>}}",
    "léčení": "{{<leceni_tooltip>}}",
    "neživý": "{{<nezivy_tooltip>}}",
    "prokletí": "{{<prokleti_tooltip>}}",
    "nemrtvý": "{{<nemrtvy_tooltip>}}",
    "jed": "{{<jed_tooltip>}}",
    "hypnóza": "{{<hypnoza_tooltip>}}",
    "iluze": "{{<iluze_tooltip>}}",
    "sugesce": "{{<sugesce_tooltip>}}",
    "mentální_magie": "{{<mentalni_magie_tooltip>}}",
    "blesk": "{{<blesk_tooltip>}}",
    "oheň": "{{<ohen_tooltip>}}",
    "led": "{{<led_tooltip>}}",
    "země": "{{<zeme_tooltip>}}",
    "voda": "{{<voda_tooltip>}}",
    "vzduch": "{{<vzduch_tooltip>}}",
    "soustředění": "{{<soustredeni_tooltip>}}",
    "bariéra": "{{<bariera_tooltip>}}",
    "zakřivení": "{{<zakriveni_tooltip>}}",
    "vysátí": "{{<vysati_tooltip>}}",
    "projektil": "{{<projektil_tooltip>}}",
    "duše": "{{<duse_tooltip>}}",
    "nahlížení": "{{<nahlizeni_tooltip>}}"
}

# create the output directory
out_path = pathlib.Path("DrusMagie/content/magic")
out_path.mkdir(parents=True, exist_ok=True)

# first, process all description files to create a mapping of spell name -> description
spell_descriptions = {}
spell_names = {}
for magic_school_name, description_file in description_files:
    descriptions = split_descriptions(open(f"lists/descriptions/{description_file}.txt").read().splitlines())
    spell_descriptions.update(descriptions)


# go over all individual schools
for magic_school_name, magic_school_file, magic_school_image, magic_school_image_2 in input_files:
    school_out = school_template.replace("$NAME", magic_school_name).replace("$IMAGE_FIRST", f"{magic_school_image}").replace("$IMAGE_SECOND", f"/images/{magic_school_image_2}")

    # split the spells into dict[spell_tier_string : str, spells : list]
    spells = split_spells(open(f"lists/{magic_school_file}.txt").read().splitlines())
    
    
    for spell_tier_list in spells.values():
        # go over all spells in this tier
        for i in range(len(spell_tier_list)):
            spell = spell_tier_list[i]
            # split around --
            parts = spell.split("--")
            # only one part -> nothing to replace anyway.
            if len(parts) == 1:
                result = spell.title()
            else:
                # see whether the last part matches a replacement keyword
                spell_name = parts[0]
                tags = parts[1:]
                replaced_tags = list(map(lambda x: replace_spell_tags(x), tags))
                result = " ".join([spell_name] + replaced_tags[:])
            
            # save the result
            spell_tier_list[i] = result
            spell_names[result] = spell

    # save the spells as hugo markdown. This includes a header for each spell tier and a markdown list for all the individual spells
    for spell_tier, spell_list in spells.items():
        # Build a list for this tier where each spell may have a hover tooltip
        items = []
        for spell in spell_list:
            # Lookup the original/raw spell name to find a description
            desc_key = spell_names[spell]
            if desc_key:
                desc = spell_descriptions[desc_key]

            if desc:
                # Keep Hugo shortcodes ({{<...>}}) intact by splitting them off from the visible text
                if "{{" in spell:
                    visible, suffix = spell.split("{{", 1)
                    suffix = "{{" + suffix
                else:
                    visible = spell
                    suffix = ""

                # Escape the description for safe inclusion in a title attribute and collapse newlines
                escaped_desc = desc # html.escape(desc, quote=True).replace('\n', ' ')

                item = f"* <span data-html=\"true\" class=\"tooltip\">{visible.strip()} <span class=\"tooltiptext\">{escaped_desc}</span></span>{suffix}"
            else:
                item = f"* {spell}"

            items.append(item)

        school_out += '\n'.join([f"\n## {spell_tier.title()}", *items])

    # save the resulting markdown
    save(out_path/f"{magic_school_file}.md", school_out)
