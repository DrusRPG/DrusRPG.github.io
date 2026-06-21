import base64
import json
import re
from pathlib import Path
from typing import NamedTuple


def capitalize_title(title: str) -> str:
    words = re.split(r"([ /])", title)
    no_capitalize = ["v", "do", "na", "ke", "ve", "k"]
    return "".join(
        [word.capitalize() if word not in no_capitalize else word for word in words]
    )


class Spell(NamedTuple):
    name: str
    tags: list[str]
    description: list[str]
    secret: bool = False

    def formatted_description(self) -> str:
        joined = "<br><br>".join(self.description)
        return re.sub(r"\*\*\*(.*?)\*\*\*", r"<strong>\1</strong>", joined)


class SpellCategory:
    def __init__(self, spells: list[Spell]):
        self.spells = spells

    def is_secret(self) -> bool:
        return all(spell.secret for spell in self.spells)


def parse_spell_block(block: str, secret: bool) -> SpellCategory:
    spell_headers = re.findall(r"\t(\w.*)\n", block)
    desc_blocks = re.split(r"\t\w.*\n", block)[1:]
    spells = []
    for header, desc_block in zip(spell_headers, desc_blocks):
        parts = header.split(" -- ")
        spells.append(
            Spell(
                name=capitalize_title(parts[0]),
                tags=parts[1:],
                description=re.findall(r"\t\t- (.*)\n", desc_block),
                secret=secret,
            )
        )
    return SpellCategory(spells)


class MagicSchool:
    def __init__(self, spells: dict[str, SpellCategory]):
        self._spells = spells

    def spells_flat(self) -> list[Spell]:
        return [
            spell
            for spell_category in self._spells.values()
            for spell in spell_category.spells
        ]

    def spells(self):
        return self._spells


def parse_magic_file(filename: Path, secret: bool = False) -> MagicSchool:
    contents = filename.read_text()
    return parse_magic_file_s(contents, secret)


def parse_magic_file_s(data: str, secret: bool = False) -> MagicSchool:
    tier_names = re.findall(r"(\w+):\n", data)
    tier_blocks = re.split(r"\w+:\n", data)[1:]
    return MagicSchool(
        {
            tier: parse_spell_block(block, secret)
            for tier, block in zip(tier_names, tier_blocks)
        }
    )


def parse_secrets(*secret_keys: str) -> str | list[str]:
    secrets = json.load(open("lists/secrets.json"))
    decoded = [base64.b32decode(secrets[key]).decode("utf-8") for key in secret_keys]
    return decoded[0] if len(secret_keys) == 1 else decoded


# A wrapper for the magic school markdown template, `templates/school_of_magic_header.md`
class MagicSchoolTemplate:
    def __init__(self):
        self.template = open("templates/school_of_magic_header.md").read()

    def get_school_markdown(
        self, name: str, image_first: str, image_second: str, contents: str
    ) -> str:
        replacements = {
            "NAME": name,
            "IMAGE_FIRST": image_first,
            "IMAGE_SECOND": image_second,
            "CONTENTS": contents,
        }
        school_out = self.template
        for key, value in replacements.items():
            school_out = school_out.replace(f"${key}", value)
        return school_out
