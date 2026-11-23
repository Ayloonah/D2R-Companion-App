# Notes

## Data gathering
The original plan was to work with a dataset of 150 images. Out of these, 105 were going to be for the training set and 45 were going to be for the test set. Fifteen from the 150 images were not going to contain an item tooltip so that they may be used to measure false positives. From those 15 images, ten were going to be part of the training set and five were going to be included in the test set.

In actuality, we ended up with a total of 160 images, 10 of which reflect items created using an offline game save editor to help save time. The latter still reflect accurate data even though they were not organically found during gameplay. Our final count for the training set was of 108 while it was of 52 for the testing set, with them containing 11 and 5 negative images respectively.

It is good to keep in mind that the scope of this companion app is to keep track of the equipment and items needed for a specific character build. As such, we are building a pipeline that will look at the following tooltips:
- Any equippable equipment, such as helmets, chest pieces, gloves, boots, amulets, rings, belts, weapons, and ammunition
- Charms, which are usually kept in a player's inventory
- Jewels, which have random stat values
We will also make sure to track gems, runes, and other miscellaneous items, though for those, as their stats are predefined or irrelevant, only the item name will be considered.

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

It is good to note that item comparison is available while holding Shift. It is used in some screenshots, and those images have two to three entries in tooltips. This will be mentioned in the notes for that entry.

Here is each piece of information explained, with the potential values it will hold:
- image: The image file name in the format "0001_rarity_slot_background.png", with the mention of "ethereal" being added in when applicable
- resolution: Game resolution, which is 2560x1440 for all of these images
- split: Whether the image is part of the train or test set
- background: Information on where the tooltip is shown
  - Potential values: inventory, equipped, stash, shop, cube, mercenary
  - For the 16 negatives, gives a free-text description of what is displayed on screen
- bbox: Coordinates of the bounds of the tooltip in the format [xmin, ymin, xmax, ymax]
- rarity: Item rarity
  - Potential values: normal, magic, rare, set, unique, crafted, runeword, null
  - Null only applies for runes, gems and miscellaneous items
- name: Item name
- base: Item base
  - Value examples: Bramble Mitts, Grand Matron Bow, Mage Plate, Grand Crown, Ring, null
  - Null always applies for normal, magic, and unidentified items as the item's name includes it 
- base_lines: Item's built-in information
  - Value examples: Cost: 112, Required Strength: 101, Required Level: 45, Durability: 53 of 60, Defense: 191
- slot:
   - Potential values: weapon, offhand, helm, gloves, boots, belt, ring, amulet, chest, charm, gem, rune, jewel, misc
- affixes: Item's affixes/attributes
  - Value examples: +2 to Combat Skills (Barbarian Only), +124% Enhanced Defense, +34% Faster Cast Rate, +11 to All Attributes, All Resistances +18, 21% Better Chance of Getting Magic Items
- set: If the item is part of a set, the set's name, bonuses, and items, null otherwise
  - Example of a set item: Death's Touch
    - set_name: Death's Disguise
    - set_bonuses: +8% Life Steal (2 Items), +8% Life Steal, 40% Bonus to Attack Rating, All Resistances +25, +10 to Minimum Damage
    - set_items: Death's Touch, Death's Guard, Death's Hand
- runes: The name of the runes used to make this item's runeword
  - Value examples: JahIthBer, RalTirTalSol, TirTalAmn, IthElEth
- ethereal: Whether or not the item is ethereal, stored as a boolean 
- sockets: Number of sockets an item has, represented by an integer
- notes: Used to describe anything unusual about the screen's contents

To get the values for the bounding boxes, we have made use of LabelImg. We manually drew the bounding boxes around where the tooltips were inside of the screenshots, and the tool saved the data in PascalVOC XML format.

In this step, Claude AI was used in the following ways:
- It generated a screenshot tracking tool so that we could accurately keep track of the various types of screenshots that were taken versus those that were still needed.
- It extracted the data from the tracker to get us started with the dataset annotation.
- It extracted the bounding box values from the generated XML files to add them to the JSON annotations.
- It verified the manual annotations to ensure that no mistakes had slipped in. This was manually verified afterwards as well.
- It identified gaps in the dataset which led to further data collection.
- It assisted with information gathering to better understand the tools and languages used.