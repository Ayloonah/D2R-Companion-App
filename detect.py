"""
Tooltip detection for D2R screenshots.

Finds item tooltips by anchoring on their text: bright text lines are found,
grouped into centered stacks, merged when split, filtered by background
darkness, then grown outward to the tooltip's dark background.

Usage:
    from detect import detect_tooltips
    boxes = detect_tooltips(img)  # list of (xmin, ymin, xmax, ymax) in original image pixels

All tuned values live in the constants below and are in pixels of the
resized (WORK_WIDTH x WORK_HEIGHT) image.
"""

import cv2
import numpy as np

# Working resolution: every screenshot is resized to this before detection
WORK_WIDTH = 1920
WORK_HEIGHT = 1080

# Text mask
TEXT_THRESHOLD = 95             # V channel value above which a pixel counts as text
CLOSE_KERNEL = (25, 3)          # closing kernel that merges letters into line blobs

# Line blob shape filter
LINE_MIN_HEIGHT = 10            # exclusive
LINE_MAX_HEIGHT = 25            # exclusive
LINE_MIN_RATIO = 4              # width / height, exclusive

# Grouping lines into tooltips
GROUP_MAX_GAP = 80              # max vertical distance from the previous line (exclusive)
GROUP_CENTER_TOLERANCE = 15     # max center x difference from the previous line (exclusive)
GROUP_MIN_LINES = 2

# Merging split tooltips
MERGE_CENTER_TOLERANCE = 15     # inclusive
MERGE_MAX_GAP = 200             # inclusive
MERGE_GAP_DARKNESS = 30         # max median gray value of the gap between pieces (inclusive)

# Box padding and darkness filter
PADDING = 10
DARKNESS_MAX = 13               # max median gray value inside the box (inclusive)

# Region growing
GROWTH_STEP = 5
HORIZONTAL_GROWTH_DARKNESS = 17  # stop when either side strip is brighter than this
HORIZONTAL_GROWTH_CAP = 115      # stop once growth exceeds this
VERTICAL_GROWTH_DARKNESS = 13    # each side stops when its strip is brighter than this
TOP_GROWTH_CAP = 15              # stop once top growth exceeds this (effective max 20)
BOTTOM_GROWTH_CAP = 35           # stop once bottom growth exceeds this (effective max 40)


def find_text_lines(resized_img):
    """Return (x, y, w, h) boxes of blobs shaped like a line of text, sorted by y."""

    # Keep only the brightest pixel value in RGB channels to convert to 1 channel
    v_channel = np.max(resized_img, axis=2)

    # Apply a mask so only bright pixels (text) are kept
    _, mask = cv2.threshold(v_channel, TEXT_THRESHOLD, 255, cv2.THRESH_BINARY)

    # Dilate letters to merge a line into a blob
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, CLOSE_KERNEL)
    dilated = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find the contours of all the blobs
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Store blobs corresponding to potential lines of text in a list and sort them by y
    potential_text = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if LINE_MIN_HEIGHT < h < LINE_MAX_HEIGHT and w / h > LINE_MIN_RATIO:
            potential_text.append((x, y, w, h))
    potential_text.sort(key=lambda box: box[1])

    return potential_text


def group_lines(potential_text):
    """Group lines that are stacked close together and share a center x."""

    maybe_tooltips = []
    for line in potential_text:
        line_center = line[0] + line[2] / 2
        for tooltip in maybe_tooltips:
            last = tooltip[-1]
            last_center = last[0] + last[2] / 2
            if line[1] - last[1] < GROUP_MAX_GAP and abs(last_center - line_center) < GROUP_CENTER_TOLERANCE:
                tooltip.append(line)
                break
        else:
            maybe_tooltips.append([line])

    # Discard groups with too few lines
    return [tooltip for tooltip in maybe_tooltips if len(tooltip) >= GROUP_MIN_LINES]


def _group_bounds(tooltip):
    """Return (center, left, right, top, bottom) of a group of lines."""
    center = np.median([box[0] + box[2] / 2 for box in tooltip])
    left = min(box[0] for box in tooltip)
    right = max(box[0] + box[2] for box in tooltip)
    top = min(box[1] for box in tooltip)
    bottom = max(box[1] + box[3] for box in tooltip)
    return center, left, right, top, bottom


def merge_split_groups(maybe_tooltips, gray):
    """
    Merge groups that share a horizontal center, sit one above the other,
    and have a dark enough gap between them. Repeats until nothing merges.
    Modifies and returns the list.
    """

    while True:
        merged_something = False
        for i in range(len(maybe_tooltips)):
            for j in range(i + 1, len(maybe_tooltips)):
                first_tooltip = maybe_tooltips[i]
                second_tooltip = maybe_tooltips[j]

                first_center, first_left, first_right, first_top, first_bottom = _group_bounds(first_tooltip)
                second_center, second_left, second_right, second_top, second_bottom = _group_bounds(second_tooltip)

                # Horizontal overlap of the two groups
                max_left = max(first_left, second_left)
                min_right = min(first_right, second_right)

                # Figure out which group is above the other, and the gap between them
                if first_top < second_top:
                    upper_tooltip, lower_tooltip = first_tooltip, second_tooltip
                    upper_bottom, lower_top = first_bottom, second_top
                else:
                    upper_tooltip, lower_tooltip = second_tooltip, first_tooltip
                    upper_bottom, lower_top = second_bottom, first_top
                gap = lower_top - upper_bottom

                # Darkness of the gap region between the two groups
                if max_left < min_right:
                    if gap > 0:
                        gap_median = np.median(gray[upper_bottom:lower_top, max_left:min_right])
                    else:
                        gap_median = 0
                else:
                    gap_median = 255  # no horizontal overlap, never merge

                if (abs(first_center - second_center) <= MERGE_CENTER_TOLERANCE
                        and gap <= MERGE_MAX_GAP
                        and gap_median <= MERGE_GAP_DARKNESS):
                    upper_tooltip.extend(lower_tooltip)
                    upper_tooltip.sort(key=lambda box: box[1])
                    maybe_tooltips.remove(lower_tooltip)
                    merged_something = True
                    break

            if merged_something:
                break

        if not merged_something:
            return maybe_tooltips


def grow_horizontally(gray, left, right, top, bottom):
    """Grow both sides together while both side strips stay dark."""

    width = gray.shape[1]
    horizontal_growth = 0
    while True:
        # If we're at the edge, stop
        if left <= 0 or right >= width:
            break

        left_side_median = np.median(gray[top:bottom, max(0, left - GROWTH_STEP):left])
        right_side_median = np.median(gray[top:bottom, right:min(width, right + GROWTH_STEP)])

        if left_side_median > HORIZONTAL_GROWTH_DARKNESS or right_side_median > HORIZONTAL_GROWTH_DARKNESS:
            break

        left = max(0, left - GROWTH_STEP)
        right = min(width, right + GROWTH_STEP)

        if left == 0 or right == width:
            break

        horizontal_growth += GROWTH_STEP
        if horizontal_growth > HORIZONTAL_GROWTH_CAP:
            break

    return left, right


def grow_vertically(gray, left, right, top, bottom):
    """Grow the top and bottom independently while each strip stays dark."""

    height = gray.shape[0]
    top_growth = 0
    bottom_growth = 0
    top_is_done = False
    bottom_is_done = False
    while True:
        # If top or bottom is at the edge, mark as done
        if top == 0:
            top_is_done = True
        if bottom == height:
            bottom_is_done = True

        if not top_is_done:
            top_side_median = np.median(gray[max(0, top - GROWTH_STEP):top, left:right])
            if top_side_median <= VERTICAL_GROWTH_DARKNESS:
                top -= GROWTH_STEP
                top_growth += GROWTH_STEP
            else:
                top_is_done = True

        if not bottom_is_done:
            bottom_side_median = np.median(gray[bottom:min(height, bottom + GROWTH_STEP), left:right])
            if bottom_side_median <= VERTICAL_GROWTH_DARKNESS:
                bottom += GROWTH_STEP
                bottom_growth += GROWTH_STEP
            else:
                bottom_is_done = True

        top = max(0, top)
        bottom = min(height, bottom)

        if (top == 0 or top_growth > TOP_GROWTH_CAP) and not top_is_done:
            top_is_done = True
        if (bottom == height or bottom_growth > BOTTOM_GROWTH_CAP) and not bottom_is_done:
            bottom_is_done = True

        if top_is_done and bottom_is_done:
            break

    return top, bottom


def detect_tooltips(img, return_debug=False):
    """
    Detect item tooltips in a BGR screenshot.

    Returns a list of (xmin, ymin, xmax, ymax) boxes in the original image's pixels.
    With return_debug=True, returns (boxes, contoured) where contoured is the
    resized image with the detected boxes drawn on it.
    """

    # Resize to a standard size so the pixel parameters work at any resolution
    resized_img = cv2.resize(img, (WORK_WIDTH, WORK_HEIGHT))
    x_ratio = img.shape[1] / WORK_WIDTH
    y_ratio = img.shape[0] / WORK_HEIGHT

    # Grayscale to keep track of darkness levels
    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

    potential_text = find_text_lines(resized_img)
    maybe_tooltips = group_lines(potential_text)
    maybe_tooltips = merge_split_groups(maybe_tooltips, gray)

    contoured = resized_img.copy() if return_debug else None
    boxes = []
    for tooltip in maybe_tooltips:

        # Bounds of the group of lines, padded and clamped to the image
        left = max(0, min(box[0] for box in tooltip) - PADDING)
        right = min(WORK_WIDTH, max(box[0] + box[2] for box in tooltip) + PADDING)
        top = max(0, min(box[1] for box in tooltip) - PADDING)
        bottom = min(WORK_HEIGHT, max(box[1] + box[3] for box in tooltip) + PADDING)

        # Discard anything that isn't on a dark background
        if np.median(gray[top:bottom, left:right]) > DARKNESS_MAX:
            continue

        left, right = grow_horizontally(gray, left, right, top, bottom)
        top, bottom = grow_vertically(gray, left, right, top, bottom)

        if return_debug:
            cv2.rectangle(contoured, (left, top), (right, bottom), (0, 255, 0), 4)

        # Scale back to the original image size
        boxes.append((left * x_ratio, top * y_ratio, right * x_ratio, bottom * y_ratio))

    if return_debug:
        return boxes, contoured
    return boxes
