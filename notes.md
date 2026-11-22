# Notes

## Data gathering
We will be working with a dataset of 150 images. Out of these, 105 will be for the training set and 45 will be for the test set. There will be a total of 15 images from the 150 that do not contain an item tooltip; these will be used to measure false positives. From those 15 images, 10 will be part of the training set and 5 will be included in the test set.

It is good to keep in mind that the scope of this companion app is to keep track of the equipment and items needed for a specific character build. As such, we are building a pipeline that will look at the following tooltips:
- Any equippable equipment, such as helmets, chest pieces, gloves, boots, amulets, rings, belts, weapons, and ammunition
- Charms, which are usually kept in a player's inventory
- Jewels, which have random stat values
We will also make sure to track gems and runes, though for those, as their stats are predefined, only the item name will be considered.

The in-game screenshots were taken with these settings: 
- Resolution: 2560x1440
- Display mode: Fullscreen
- Resolution scale: 100
- NVIDIA DLSS: Quality
- Sharpening: 6
- Anti-aliasing: Off
- Dynamic resolution scaling: Off
- Large font mode: Off
- Show Item Tooltip Button Prompts: On
- Color Blind: Off
- Show Items: Toggle
- Automap: Mini Map Right, custom opacity 80
- Chat font size / background: Large / off
- Show Clock, orb text: On
- Graphic preset: Very High
- Brightness: no value shown, but slider at around 40% and remained unchanged for all screenshots

The JSON file, which will hold the ground truth information, will follow this template:
{
  "image": "",
  "resolution": [2560, 1440],
  "split": "",
  "background": "",
  "tooltips": [
    {
      "bbox": null,
      "rarity": null,
      "name": "",
      "base": null,
      "base_lines": [],
      "slot": "",
      "affixes": [],
      "set": null,
      "runes": null,
      "ethereal": false,
      "sockets": 0
    }
  ],
  "notes": ""
}

It is good to note that item comparison is available while holding Shift. It is used in some screenshots, and those images have two entries in tooltips. This will be mentioned in the notes for that entry.

Here is each piece of information explained, with the potential values it will hold:
- image: The image file name in the format "000_image_info.png"
- resolution: Game resolution, which is 2560x1440 for all of these images
- split: Whether the image is part of the train or test set
- background: Information on where the tooltip is shown
  - Potential values: inventory, equipped, stash, shop, cube, mercenary, trade
  - For the 15 negatives, gives information as to what could cause a false positive, such as chat, skill_tree, map, etc
- bbox: Coordinates of the bounds of the tooltip in the format [xmin, ymin, xmax, ymax]
- rarity: Item rarity
  - Potential values: normal, magic, rare, set, unique, crafted, runeword, socketed, null
- name: Item name
- base: Item base
  - Value examples: Bramble Mitts, Grand Matron Bow, Mage Plate, Grand Crown, Ring, null
- base_lines: Item's built-in information
  - Value examples: Socketed (4), Required Strength: 101, Required Level: 45, Durability: 53 of 60, Defense: 191
- slot:
   - Potential values: main_hand, off_hand, head, hands, feet, belt, ring, amulet, chest, charm, gem, rune, jewel
- affixes: Item's affixes/attributes
  - Value examples: +2 to Combat Skills (Barbarian Only), +124% Enhanced Defense, +34% Faster Cast Rate, +11 to all Attributes, +18 to All Resistances, 21% Better Chance of Getting Magic Items
- set: If the item is part of a set, the set's name, bonuses, and items
  - Example of a set item: Death's Touch
    - set_name: Death's Disguise
    - set_bonuses: +8% Life Steal (2 Items), +8% Life Steal, 40% Bonus to Attack Rating, All Resistances +25, +10 to Minimum Damage
    - set_items: Death's Touch, Death's Guard, Death's Hand
- runes: The name of the runes used to make this item's runeword
  - For example, to make Enigma, you would use Jah, Ith, and Ber
- ethereal: Whether or not an item is ethereal, represented by a boolean
- sockets: Number of sockets an item has, represented by an integer
- notes: Used to describe anything unusual about the screen's contents