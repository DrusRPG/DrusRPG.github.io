import base64
import json
import re
from pathlib import Path
from typing import NamedTuple


def capitalize_title(title: str) -> str:
    words = re.split(r"([ /])", title)
    no_capitalize = ["v", "do", "na", "ke", "ve", "k"]
    return "".join([word.capitalize() if word not in no_capitalize else word for word in words])


class Spell(NamedTuple):
    name: str
    tags: list[str]
    description: list[str]


MagicCategory = list[Spell]


def parse_spell_block(block: str) -> MagicCategory:
    spell_headers = re.findall(r"\t(\w.*)\n", block)
    desc_blocks = re.split(r"\t\w.*\n", block)[1:]
    spells = []
    for header, desc_block in zip(spell_headers, desc_blocks):
        parts = header.split(" -- ")
        spells.append(Spell(
            name=capitalize_title(parts[0]),
            tags=parts[1:],
            description=re.findall(r"\t\t- (.*)\n", desc_block),
        ))
    return spells


def parse_magic_file(filename: Path) -> dict[str, MagicCategory]:
    contents = filename.read_text()
    tier_names = re.findall(r"(\w+):\n", contents)
    tier_blocks = re.split(r"\w+:\n", contents)[1:]
    return {tier: parse_spell_block(block) for tier, block in zip(tier_names, tier_blocks)}


def parse_secrets(*secret_keys: str) -> str | list[str]:
    secrets = json.load(open("lists/secrets.json"))
    decoded = [base64.b64decode(secrets[key]).decode("utf-8") for key in secret_keys]
    return decoded[0] if len(secret_keys) == 1 else decoded
