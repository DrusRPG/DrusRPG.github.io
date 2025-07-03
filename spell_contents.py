import os
import string
import pathlib

def save(fname, data):
    with open(fname, "w") as f:
        f.write(data)


school_template = open("templates/school_of_magic_header.md").read()



input_files = [
    ("Magie Času", "cas", "clock.jpg"),
    ("Magie Prostoru", "prostor", "prostor.jpg"),
    ("Magie Života", "zivot", "light.jpg"),
    ("Magie Smrti", "smrt", "dark.jpg"),
    ("Magie Hmoty", "hmota", "matter.jpg"),
    ("Magie Mysli", "mysl", "neural.jpg"),
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



out_path = pathlib.Path("DrusMagie/content/magic")
out_path.mkdir(parents=True, exist_ok=True)

for magic_school_name, magic_school_file, magic_school_image in input_files:
    school_out = school_template.replace("$NAME", magic_school_name).replace("$IMAGE", f"{magic_school_image}")

    spells = split_spells(open(f"lists/{magic_school_file}.txt").read().splitlines())
    

    for spell_tier, spell_list in spells.items():
        school_out += '\n'.join([f"\n## {spell_tier.title()}", *["* " + spell.title() for spell in spell_list]]) 

    save(out_path/f"{magic_school_file}.md", school_out)



    

