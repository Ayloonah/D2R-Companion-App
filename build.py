"""
Allows us to convert game data into JSON files our program can use.
"""

import csv
import json
import os

GAME_DATA = "Game_Data"
OUT_DIR = "data"

# Maps the game's body locations to our slot names
BODYLOC_TO_SLOT = {
    "head": "helm", "tors": "chest", "glov": "gloves", "feet": "boots",
    "belt": "belt", "rarm": "offhand", "neck": "amulet", "rrin": "ring",
}

# Maps the game's misc item types to our slot names
MISC_TYPE_TO_SLOT = {
    "ring": "ring", "amul": "amulet",
    "scha": "charm", "mcha": "charm", "lcha": "charm",
    "jewl": "jewel", "cjwl": "jewel", "csch": "charm",
    "bowq": "offhand", "xboq": "offhand",
}

def load_table(file):
    """
    Reads a TSV file and returns a list of row dicts
    """

    path = os.path.join(GAME_DATA, file)

    with open(path, mode="r", encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)

def load_strings(*files):
    """
    Reads a JSON file containing strings and returns a dict of keys -> string
    """

    strings = {}

    for file in files:
        with open(file, mode="r", encoding="utf-8-sig") as f:
            entries = json.load(f)

            for entry in entries:
                strings[entry["Key"]] = entry["enUS"]

    return strings

def build_uniques(strings, base_names):
    """
    Takes in item strings and a dict of base code -> base name, returns a list
    of dicts containing item names and bases for each unique item
    """

    items = []

    uniques_table = load_table("uniqueitems.txt")

    for row in uniques_table:
        if not row["code"].strip():
            continue

        if row["disabled"] == "1":
            continue

        item = {}
        item["name"] = strings[row["index"]]
        item["base"] = base_names.get(row["code"], row["code"])
        items.append(item)

    return items

def build_sets(strings, base_names):
    """
    Return a list of {"name", "set", "base"} for every set item, plus a dict
    of set name -> list of its item names
    """

    items = []
    sets = {}

    set_table = load_table("setitems.txt")

    for row in set_table:
        if not row["item"].strip():
            continue

        item = {}
        item["name"] = strings[row["index"]]
        item["set"] = strings[row["set"]]
        item["base"] = base_names.get(row["item"], row["item"])
        items.append(item)
        sets.setdefault(item["set"], []).append(item["name"])

    return items, sets

def build_runewords(strings):
    """
    Return a list of {"name", "runes"} for every runeword in the game
    """

    runewords = []

    runewords_table = load_table("runes.txt")

    for row in runewords_table:
        if row["complete"] != "1":
            continue

        runeword = {}
        runeword["name"] = strings[row["Name"]]

        runes = ""
        for i in range(1, 7):
            if not row[f"Rune{i}"].strip():
                continue

            rune_code = row[f"Rune{i}"] + "L"
            rune_name = strings[rune_code]

            runes += rune_name

        runeword["runes"] = runes
        runewords.append(runeword)

    return runewords

def build_item_slots():
    """
    Return a dict of item type code -> our slot name (helm, chest, ...)
    Must remember not to use for weapons, only armor, as all weapons are marked as offhand
    """

    slots = {}
    
    slots_table = load_table("itemtypes.txt")

    for row in slots_table:
        if row["BodyLoc1"] not in BODYLOC_TO_SLOT:
            continue

        slots[row["Code"]] = BODYLOC_TO_SLOT[row["BodyLoc1"]]

    return slots

def build_bases(strings, type_to_slot):
    """
    Return a list of {"name", "code", "slot"} for every base item
    Names are looked up by "namestr" (what the game displays), not "code"
    """

    weapons = []
    armor = []
    misc = []

    weapons_table = load_table("weapons.txt")
    armor_table = load_table("armor.txt")
    misc_table = load_table("misc.txt")

    for row in weapons_table:
        if not row["code"].strip():
            continue

        weapon = {}
        weapon["name"] = strings.get(row["namestr"], row["name"])
        weapon["code"] = row["code"]
        weapon["slot"] = "weapon"
        weapons.append(weapon)

    for row in armor_table:
        if not row["code"].strip():
            continue

        armr = {}
        armr["name"] = strings.get(row["namestr"], row["name"])
        armr["code"] = row["code"]

        if row["type"] in type_to_slot:
            armr["slot"] = type_to_slot[row["type"]]
        else:
            armr["slot"] = None
            print(f"ERROR: no slot for armor type {row['type']} ({row['code']})")

        armor.append(armr)

    for row in misc_table:
        if not row["code"].strip():
            continue

        if row["type"] in MISC_TYPE_TO_SLOT:

            msc = {}
            msc["name"] = strings.get(row["namestr"], row["name"])
            msc["code"] = row["code"]
            msc["slot"] = MISC_TYPE_TO_SLOT[row["type"]]
            misc.append(msc)

    bases = weapons + armor + misc

    return bases

def build_runes_and_gems(strings):
    """
    Return two lists of names: runes and gems
    """

    runes = []
    gems = []

    rg_table = load_table("misc.txt")

    for row in rg_table:
        if row["type"] == "rune":
            runes.append(strings.get(row["code"], row["name"]))
        elif row["type"].startswith("gem"):
            gems.append(strings.get(row["code"], row["name"]))

    return runes, gems

def build_stat_templates(strings):
    """
    Return a list of stat display templates from itemstatcost.txt
    """

    stats = []

    stats_table = load_table("itemstatcost.txt")

    for row in stats_table:
        if not row["descstrpos"].strip():
            continue

        stat_template = {}

        stat_template["stat"] = row["Stat"]
        stat_template["priority"] = row["descpriority"]
        stat_template["func"] = row["descfunc"]
        stat_template["val"] = row["descval"]
        stat_template["pos"] = strings.get(row["descstrpos"])
        stat_template["neg"] = strings.get(row["descstrneg"])
        stat_template["str2"] = strings.get(row["descstr2"])

        if not row["dgrp"].strip():
            stat_template["grp"] = None
            stat_template["grpfunc"] = None
            stat_template["grpval"] = None
            stat_template["grpstrpos"] = None
            stat_template["grpstrneg"] = None
            stat_template["grpstr2"] = None
            stats.append(stat_template)
            continue
        
        stat_template["grp"] = row["dgrp"]
        stat_template["grpfunc"] = row["dgrpfunc"]
        stat_template["grpval"] = row["dgrpval"]
        stat_template["grpstrpos"] = strings.get(row["dgrpstrpos"])
        stat_template["grpstrneg"] = strings.get(row["dgrpstrneg"])
        stat_template["grpstr2"] = strings.get(row["dgrpstr2"])
        stats.append(stat_template)

    return stats

def build_affix_names(strings):
    """
    Return a dict of magic and rare affix name lists:
    {"magic_prefixes", "magic_suffixes", "rare_prefixes", "rare_suffixes"}
    """

    names = {}

    def collect(file, col):
        found = set()

        f = load_table(file)

        for row in f:
            data = row[col].strip()
            # Skip empty rows and the "Expansion" divider row
            if not data or data == "Expansion":
                continue

            found.add(strings.get(data, data))

        return sorted(found)

    names["magic_prefixes"] = collect("magicprefix.txt", "Name")
    names["magic_suffixes"] = collect("magicsuffix.txt", "Name")
    names["rare_prefixes"] = collect("rareprefix.txt", "name")
    names["rare_suffixes"] = collect("raresuffix.txt", "name")

    return names

def save_json(data, file):
    """
    Write data to OUT_DIR/filename as pretty JSON
    """

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, file)

    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {path}")

def main():
    # Grab the strings
    item_str = load_strings(os.path.join(GAME_DATA, "item-names.json"),
                            os.path.join(GAME_DATA, "item-runes.json"),
                            os.path.join(GAME_DATA, "item-nameaffixes.json"))
    mod_strings = load_strings(os.path.join(GAME_DATA, "item-modifiers.json"))

    # Build everything (bases first, uniques and sets use their names)
    type_to_slot = build_item_slots()
    bases = build_bases(item_str, type_to_slot)
    base_names = {base["code"]: base["name"] for base in bases}

    uniques = build_uniques(item_str, base_names)
    set_items, set_lists = build_sets(item_str, base_names)
    runewords = build_runewords(item_str)
    runes, gems = build_runes_and_gems(item_str)
    stat_templates = build_stat_templates(mod_strings)
    affix_names = build_affix_names(item_str)

    save_json({"uniques": uniques, "sets": set_items, "set_items": set_lists, 
               "runewords": runewords, "bases": bases, "runes": runes, "gems": gems},
               "items.json")
    save_json(stat_templates, "stat_templates.json")
    save_json(affix_names, "affix_names.json")

    return

if __name__ == "__main__":
    main()