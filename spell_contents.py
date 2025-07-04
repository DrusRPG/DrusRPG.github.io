import os
import string
import pathlib

def save(fname, data):
    with open(fname, "w") as f:
        f.write(data)


school_template = open("templates/school_of_magic_header.md").read()



input_files = [
    ("Magie Času", "cas", "clock.jpg", "ancient_times1.jpeg"),
    ("Magie Prostoru", "prostor", "prostor.jpg", "ancient_times2.jpeg"),
    ("Magie Života", "zivot", "light.jpg", "ancient_times3.jpeg"),
    ("Magie Smrti", "smrt", "dark.jpg", "ancient_times4.jpeg"),
    ("Magie Hmoty", "hmota", "matter.jpg", "ancient_times2.jpeg"),
    ("Magie Mysli", "mysl", "neural.jpg", "ancient_times1.jpeg"),
]

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


touch_spell_replace = "{{<dotyk_tooltip>}}"
see_spell_replace = "{{<pohled_tooltip>}}"


out_path = pathlib.Path("DrusMagie/content/magic")
out_path.mkdir(parents=True, exist_ok=True)

for magic_school_name, magic_school_file, magic_school_image, magic_school_image_2 in input_files:
    school_out = school_template.replace("$NAME", magic_school_name).replace("$IMAGE_FIRST", f"{magic_school_image}").replace("$IMAGE_SECOND", f"/images/{magic_school_image_2}")

    spells = split_spells(open(f"lists/{magic_school_file}.txt").read().splitlines())
        
    for spell_tier_list in spells.values():
        for i in range(len(spell_tier_list)):
            spell = spell_tier_list[i]
            parts = spell.split("-")
            if len(parts) == 1:
                result = spell.title()
            else:
                if "dotyk" in parts[-1]:
                    result = " ".join(map(lambda x: x.title(), parts[:-1])) + f" {touch_spell_replace}"
                elif "dohled" in parts[-1]:
                    result = " ".join(map(lambda x: x.title(), parts[:-1])) + f" {see_spell_replace}"
                else:
                    result = " ".join(map(lambda x: x.title(), parts[:-1]))
            spell_tier_list[i] = result     

    for spell_tier, spell_list in spells.items():
        school_out += '\n'.join([f"\n## {spell_tier.title()}", *["* " + spell for spell in spell_list]]) 

    save(out_path/f"{magic_school_file}.md", school_out)



    

