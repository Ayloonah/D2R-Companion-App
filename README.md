# DIABLO II: RESURRECTED COMPANION – ITEM TOOLTIP RECOGNITION
Diablo II: Resurrected players constantly compare equipment tooltips against their desired builds to decide whether to keep or discard items. This project aims to develop a computer vision application that automatically detects in-game tooltips, extracts their information, and identifies affixes (attributes) matching user-defined preferences.

## DATASET
A custom dataset of in-game screenshots will be collected, containing equipment tooltips from different item categories, rarities, and affixes, along with associated JSON files storing manually annotated ground truth for performance evaluation.

## PROPOSED SOLUTION
The application will use OpenCV for tooltip detection and image preprocessing, including edge detection and thresholding. An OCR engine will extract item names and affixes, which will then be compared against user preferences. Desired affixes receiving color-coded indicators based on their values, while exact item matches will be marked with a star. For example, if a user wants a specific ring with 10% Faster Cast Rate (FCR), finding that ring would trigger a star beside its name. A different ring with FCR would instead receive a green indicator if its FCR is at least 10%, or orange otherwise.

## MY CONTRIBUTION
I will collect and annotate the dataset, implement and evaluate the tooltip detection and preprocessing pipeline, develop the attribute extraction and matching logic, and create a UI for configuring preferences and displaying results. I will compare recognition performance before and after preprocessing, and document any external libraries and reused code, if applicable.
