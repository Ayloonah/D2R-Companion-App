# Notes

## Data Gathering

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
  - Although this is the correct resolution, nine of the dataset screenshots were a few pixels smaller due to cropping during capture
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

## Tooltip Detection

In order to detect the tooltips, we decided to make use of edge detection and thresholding. The first thing of note when looking at tooltips in Diablo 2: Resurrected is that they are rectangular with a black semi-transparent background. This also applies to other UI elements, so it is not sufficient by itself, but it allows us to pinpoint potential locations to look at easily.

To get us started, we first converted screenshots four to seven to greyscale and looked at the median pixel value inside of the tooltip area. We used this value to choose a threshold which was then applied to the image: anything lower than the threshold was turned white, and everything else was turned black. This allowed us to realize that the semi-transparency of the tooltips caused background items to seep through, and that might be problematic when trying to find the tooltip's location.

We tried morphological closing to fill in the spots left behind by the background elements and then drawing a box around the tooltip, but the tooltips ended up being merged with dark parts of the background, meaning that the boxes were covering more than just the tooltip. This caused us to drop this approach.

Our next attempt at detecting the tooltips consisted of using Canny to find all of the edges inside of our greyscale screenshots. We were mostly able to observe the tooltips in this way, but the results were still very messy, and some tooltip edges were getting mixed up with the surrounding elements. We tried using morphological opening with long 100×1 and 1×100 kernels to isolate the horizontal and vertical lines in an effort to get rid of the clutter, and although this caused a lot of the UI to be captured as well, it seemed promising.

For the edges to be more visible and for us to be able to see unbroken lines in the produced images, we tried dilating the edges previously found before isolating the straight edges. We then filtered out any results that had too small of an area as well as anything too bright and drew a box around the tooltip. However, no matter the values we used, while some tooltips were being properly captured, most were either not fully detected or not detected at all, with random UI elements getting a bounding box as well. This was caused by the tooltips' transparency as well as them having no border, making it hard to isolate them properly. We therefore dropped this approach as well.

By this point, we considered our options and figured it would potentially be easier to instead use the tooltips' text to find the tooltip itself. This is therefore what we set out to do.

Before anything, we first decided to integrate a resizing step so that no matter the user's resolution, we would be looking at images of the same size. We settled on 1920x1080 as our resolution of choice. This also fixed the sizing issues with the nine slightly smaller screenshots.

Then, so that we may more easily find the text in our screenshots, because it is one of the brightest elements, we started by reducing the number of channels from three to one, only keeping the highest of the three RGB values. This allowed us to better detect the blue colored text which might have gotten lost using grayscale. We set a threshold at 95 and also set out to dilate the letters with a kernel of size 25x3 so that lines of text turned into a blob. We found those blobs' contours and stored any that were of a height and width fitting a line of text (height between 10 and 25 pixels with width to height ratio of more than 4) into a list which we sorted by y value.

We grouped these potential lines of text into groups based on their location on the screen. If a line was within 80 pixels of another in y and centered within 15 pixels of the same x of it, we determined it was part of the same tooltip and therefore grouped them together. With that done, we discarded any group with only a single line of text, added a 10 pixel padding all around, and were left with our potential tooltip locations.

To determine if this was a good approach, after our initial test on a sample of four screenshots, we ran the code on the whole training set and ended up with the following results:

- True Positives: 103
- False Positives: 45
- False Negatives: 3
- Negative images with nothing detected: 2
- Precision: 0.6959
- Recall: 0.9717
- F1: 0.8110
- Mean IoU: 0.8799

It is good to note that these statistics were obtained using an IoU threshold of 0.5 with one-to-one matching on our training set of 108 images only.

The results showed that this approach was the most promising, with 103 out of 106 tooltips found, leaving us with a recall of 97%. We however ended up with a higher number of false positives than we would have liked, with 9 of the 11 negatives getting at least one detected tooltip, and sought to find a way to reduce them.

Looking at our contoured screenshots, we found that the following situations caused the most false positives to be triggered:

- Ground item labels and NPC names
- Mercenary and character stat labels
- Various UI elements displayed as lines, such as the stamina bar, dividers, stash page selector, and gold box
- Chat and message of the day

Additionally, we could see the missed tooltips were either caused by a tooltip being split in two (screenshot #0027), or the detected tooltip size being smaller than the actual tooltip size (screenshots #0124 and #0127).

To resolve this, we decided to first calculate a detected tooltip's line count and median darkness value to decide on accurate thresholds to use instead of guessing like we did the first time around.

Analyzing the results showed us the following:

- TP median darkness avg value: 6.6311
- TP median darkness min/max values: 2.0/13.0
- TP lines avg value: 10.6893
- TP lines min/max values: 2/22
- FP median darkness avg value: 15.7111
- FP median darkness min/max values: 2.0/65.0
- FP lines avg value: 2.5778
- FP lines min/max values: 2/11

Using this data, we decided to settle on the following as initial values:

- Discard anything with a median darkness value higher than 13
- Keep the 2 lines minimum and do not implement a maximum number of lines

Anything less would risk causing us to lose our true positives.

Then, we went ahead and applied the following fixes:

- To avoid detected tooltip regions being too narrow or small, add region growing based on surrounding pixel values.
- Merge vertically aligned detected tooltips if the median darkness value of the region between them fits our threshold to avoid splitting.

When it comes to region growing, we initially figured only horizontal region growing would be necessary, but we quickly realized that item names were getting cropped out. Therefore, we also applied vertical region growing, and we could confirm that this improved our results.

As we implemented both fixes, we tested along the way, and noticed that some of the values we had chosen were causing false positives and negatives. In the end, the following parameters gave us the best results:

- Threshold of 95
- 25×3 closing kernel
- Only keep blobs of height 10–25 pixels with a width to height ratio > 4
- Group blobs with less than an 80 pixel vertical gap, with a 15 pixel center tolerance, and at least 2 lines
- Merge tooltips with centers within 15 pixels of each other, a gap of no more than 200 pixels, and a gap median darkness value of no more than 30
- Only keep tooltips with a median darkness value of no more than 13
- Horizontal region growing: median darkness value of no more than 17, cap growth at 115 pixels
- Vertical region growing: median darkness value of no more than 13, top cap growth at 20 pixels, bottom cap growth at 40 pixels

The final results on our training and testing sets were the following:

| Metric                            | Training | Testing |
| --------------------------------- | -------: | ------: |
| True positives                    |      104 |      51 |
| False positives                   |       19 |       2 |
| False negatives                   |        2 |       0 |
| Negative images with no detection |        7 |       3 |
| Precision                         |   0.8455 |  0.9623 |
| Recall                            |   0.9811 |  1.0000 |
| F1                                |   0.9083 |  0.9808 |
| Mean IoU                          |   0.9471 |  0.9405 |

We were worried about potential overfitting since certain parameter tweaks only improved the results on one or two images, but the results we obtained on our testing set were reassuring. Since the sample size on the testing set is half that of the training set, the higher test numbers likely came from the small sample size and from fewer of the scene types that cause false positives. This being said, the mean IoU being similar for both was a good sign of generalization. The two false positives also made sense, one of them being text on a dark UI and the other being a tooltip which will be discarded during verification.

Even with these fixes, we could notice the following limitations: 

- When tooltips are over bright elements, it causes the detected box to still be too narrow.
- The gap median darkness value of 30 was chosen based mostly on the results of one image.
- Some text elements will always be detected during this step and can only be discarded during verification.

In this step, Claude AI was used in the following ways:

- It helped us learn the various functions of OpenCV we were not familiar with.
- It suggested approaches and helped us troubleshoot when we hit roadblocks.
- It helped us analyze our results to better know how to improve our algorithm.
- It helped with debugging.
- It moved the code from dataset_detection.py into detect.py and evaluate_detection.py for us.
  - It kept our logic the same, though it split everything into functions and also moved the parameter values into constants defined at the top.

All code in this step is our own.

## Tooltip Verification

Once we have found the tooltips, we will then use OCR to look at their contents and decide whether or not it is a tooltip we care about. Initially, we were considering looking at what a tooltip contains to see if it was relevant to us, specifically looking for mentions of:

- Durability
- Unidentified
- Keep in Inventory to Gain Bonus
- Can be Inserted into Socketed Items
- Keybind information, if the setting is enabled by the user

To note, since keybind information is in all of the screenshots gathered in the scope of this project, we will not be able to test the verification without it, leaving us with a clear blind spot. If there is enough time, we will make sure to collect screenshots without the keybind information so as to test the program with those as well.

The issue with the above method is that the tooltip information varies heavily from an item to another, and therefore, there is a possibility that something is missed. We also considered using the rarity color as a tooltip indicator, but this would not be reliable as other unrelated tooltips also use them. We therefore surmised that the best way to proceed is to use the exact item names and affixes, ideally directly taken from the game itself.

## Game Data Extraction

For the gathering of the needed data, we were able to retrieve it from a local game installation using a tool named CascView. It let us access the information needed, which was stored in JSON and TSV files. Using a script we made in Python, we grabbed the information we needed from the files and reformatted it in three easier to read JSON files.

Because the original game files belong to Blizzard, we have not included them in the repository, but the ones that we generated are included in the data folder.

In this step, Claude AI was used to help us find the best way to extract game data, and it assisted us with the coding of a script used in converting the game data into easier to read JSON files, programming three of its 12 functions. It also helped with debugging and confirmed that the generated data matches the screenshot annotations.

## Stat Template Matching

We then set up a template to regex converter so that OCR'd affix lines can be matched against the game's stat templates and their values extracted.

In this step, Claude AI explained regex so that we could properly understand how matcher.py, which it wrote, worked.
