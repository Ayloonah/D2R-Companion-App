import cv2
import json
import numpy as np

def main():
        
    # Load in the annotations from JSON
    with open("Dataset\\annotations.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    IoU_sum = 0
    false_positives = []
    false_negatives = []

    # For every screenshot
    for screenshot in data:

        # If it's in the test split, skip it
        if screenshot["split"] == "train":
            continue

        # Print the file name and load it
        print(f"Looking at {screenshot["image"]}")
        file = "Dataset/" + screenshot["image"]
        img = cv2.imread(file)

        # Resize screenshots to 1920 by 1080 for detection (standardize across various potential resolutions)
        width = 1920
        height = 1080
        resized_img = cv2.resize(img, (width, height))

        # Store ratio for later
        resize_ratio = img.shape[1] / width

        # Grayscale to be able to keep track of darkness levels
        gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

        # Keep only the brightest pixel value in RGB channels to convert to 1 channel
        v_channel = np.max(resized_img, axis=2)

        # Apply a mask with threshold of 95 on the processed image
        threshold = 95
        _, mask = cv2.threshold(v_channel, threshold, 255, cv2.THRESH_BINARY)

        # Dilate letters to merge a line into a blob
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        dilated = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find the contours of all the blobs
        contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Store blobs corresponding to potential lines of text in a list and sort them by y 
        potential_text = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > 10 and h < 25:
                if w / h > 4:
                    potential_text.append((x, y, w, h))
        potential_text.sort(key=lambda y: y[1])

        # From the potential lines of text, form groups when lines are close enough to each other
        maybe_tooltips = []
        for line in potential_text:
            line_center = line[0] + line[2] / 2
            for tooltip in maybe_tooltips:
                last = tooltip[-1]
                last_center = last[0] + last[2] / 2
                if line[1] - last[1] < 80 and abs(last_center - line_center) < 15:
                    tooltip.append(line)
                    break
            else:
                maybe_tooltips.append([line])

        # Discard any group of less than 2 blobs
        maybe_tooltips = [tooltip for tooltip in maybe_tooltips if len(tooltip) >= 2]

        # If two potential tooltips share a horizontal center,
        # if they are one above the other, and if the gap is dark enough, merge them
        while True:
            merged_something = False
            for i in range(len(maybe_tooltips)):
                for j in range(i + 1, len(maybe_tooltips)):

                    # Grab the two tooltips
                    first_tooltip = maybe_tooltips[i]
                    second_tooltip = maybe_tooltips[j]

                    # Grab first_tooltip's center + top, bottom, right, left
                    first_center = np.median([box[0] + box[2] / 2 for box in first_tooltip])
                    first_left = min(box[0] for box in first_tooltip)
                    first_right = max(box[0] + box[2] for box in first_tooltip)
                    first_top = min(box[1] for box in first_tooltip)
                    first_bottom = max(box[1] + box[3] for box in first_tooltip)

                    # Grab second_tooltip's center + top, bottom, right, left
                    second_center = np.median([box[0] + box[2] / 2 for box in second_tooltip])
                    second_left = min(box[0] for box in second_tooltip)
                    second_right = max(box[0] + box[2] for box in second_tooltip)
                    second_top = min(box[1] for box in second_tooltip)
                    second_bottom = max(box[1] + box[3] for box in second_tooltip)

                    # Grab the max left and min right values
                    max_left = max(first_left, second_left)
                    min_right = min(first_right, second_right)

                    # Figure out which tooltip is above the other, and calculate the gap between them
                    if first_top < second_top:
                        upper_tooltip = first_tooltip
                        lower_tooltip = second_tooltip
                        upper_bottom = first_bottom
                        lower_top = second_top
                        gap = second_top - first_bottom
                    else:
                        upper_tooltip = second_tooltip
                        lower_tooltip = first_tooltip
                        upper_bottom = second_bottom
                        lower_top = first_top
                        gap = first_top - second_bottom

                    # Crop the gap region between the two tooltips
                    if max_left < min_right:
                        if gap > 0:
                            cropped_gap = gray[upper_bottom:lower_top, max_left:min_right]
                            gap_median = np.median(cropped_gap)
                        else:
                            gap_median = 0
                    else:
                        gap_median = 255
                    
                    # Check if the split meets the conditions
                    if abs(first_center - second_center) <= 15:
                        if gap <= 200:
                            if gap_median <= 30:
                                upper_tooltip.extend(lower_tooltip)
                                upper_tooltip.sort(key=lambda y: y[1])
                                maybe_tooltips.remove(lower_tooltip)
                                merged_something = True
                                break

                if merged_something:
                    break

            if not merged_something:
                break

        # Check if the tooltip is valid and the proper size, contour it,
        # and scale the values back to true image size
        contoured = resized_img.copy()
        scaled_coords = []
        for tooltip in maybe_tooltips:

            # Figure out the contour of the group of blobs add padding
            left = min(box[0] for box in tooltip) - 10
            right = max(box[0] + box[2] for box in tooltip) + 10
            top = min(box[1] for box in tooltip) - 10
            bottom = max(box[1] + box[3] for box in tooltip) + 10

            left = max(0, left)
            right = min(width, right)
            top = max(0, top)
            bottom = min(height, bottom)

            # Look at the box's darkness value
            cropped = gray[top:bottom, left:right]
            median = np.median(cropped)

            # If darkness value is higher than 13, discard
            if median > 13:
                continue

            # Horizontal region growth
            horizontal_growth = 0
            while True:

                # If we're at the edge, exit loop
                if left <= 0 or right >= width:
                    break
                
                # Look at the pixels on each side of the detected tooltip
                left_side = gray[top:bottom, max(0, left - 5):left]
                right_side = gray[top:bottom, right:min(width, right + 5)]
                left_side_median = np.median(left_side)
                right_side_median = np.median(right_side)

                # If the darkness pixel value is too high, discard
                if left_side_median > 17 or right_side_median > 17:
                    break
                # Otherwise, grow the region
                else:
                    left -= 5
                    right += 5

                # Make sure the values are not out of bounds
                left = max(0, left)
                right = min(width, right)

                # If we reached the screen edges, stop growth
                if left == 0 or right == width:
                    break

                # If growth limit is reached, stop growth
                horizontal_growth += 5
                if horizontal_growth > 115:
                    break

            # Vertical region growth
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

                    # Look at the pixels on top of the detected tooltip
                    top_side = gray[max(0, top - 5):top, left:right]
                    top_side_median = np.median(top_side)

                    # If the darkness pixel value is too high, discard and mark as done
                    # Otherwise, grow the region
                    if top_side_median <= 13: 
                        top -= 5
                        top_growth += 5
                    else:
                        top_is_done = True

                if not bottom_is_done:

                    # Look at the pixels on top of the detected tooltip
                    bottom_side = gray[bottom:min(height, bottom + 5), left:right]
                    bottom_side_median = np.median(bottom_side)

                    # If the darkness pixel value is too high, discard and mark as done
                    # Otherwise, grow the region
                    if bottom_side_median <= 13: 
                        bottom += 5
                        bottom_growth += 5
                    else:
                        bottom_is_done = True    

                # Make sure the values are not out of bounds
                top = max(0, top)
                bottom = min(height, bottom)

                # If we reached the screen edges or if growth limit reached, mark as done
                if (top == 0 or top_growth > 15) and not top_is_done:
                    top_is_done = True
                if (bottom == height or bottom_growth > 35) and not bottom_is_done:
                    bottom_is_done = True

                # If both top and bottom are done, stop growth
                if (top_is_done and bottom_is_done):
                    break

            cv2.rectangle(contoured, (left, top), (right, bottom), (0, 255, 0), 4)

            # Scale values back to original size and store them
            xmin = left * resize_ratio
            xmax = right * resize_ratio
            ymin = top * resize_ratio
            ymax = bottom * resize_ratio
            scaled_coords.append((xmin, ymin, xmax, ymax))
        
        # If there are no tooltips found and no tooltips to find, true negative
        if not screenshot["tooltips"] and len(scaled_coords) == 0:
            true_negative += 1

        # Check for false negatives and compute IoU to see if true or false positive
        for tooltip in screenshot["tooltips"]:

            # If no tooltips found but there was a tooltip to find, false negative and skip loop
            if len(scaled_coords) == 0:
                false_negative += 1
                continue

            # Find the tooltip with the best IoU and count as hit if >= 0.5
            best_IoU = -1
            best_coords = ()
            for coords in scaled_coords:
                overlap_rect = (max(tooltip["bbox"][0], coords[0]), max(tooltip["bbox"][1], coords[1]),
                                min(tooltip["bbox"][2], coords[2]), min(tooltip["bbox"][3], coords[3]))
                overlap_area = max(0, (overlap_rect[2] - overlap_rect[0])) * max(0, (overlap_rect[3] -
                               overlap_rect[1]))
                area_coords = (coords[2] - coords[0]) * (coords[3] - coords[1])
                area_tooltip = (tooltip["bbox"][2] - tooltip["bbox"][0]) * (tooltip["bbox"][3] - 
                               tooltip["bbox"][1])
                union_area = area_coords + area_tooltip - overlap_area
                IoU = overlap_area / union_area

                if IoU >= 0.5:
                    if IoU > best_IoU:
                        best_IoU = IoU
                        best_coords = coords

            # If we found a tooltip with a proper IoU, true positive
            if best_IoU > -1:
                true_positive += 1
                IoU_sum += best_IoU

                # Remove tooltip from list
                scaled_coords.remove(best_coords)

            # Otherwise, tooltip was missed, false_negative
            else:
                false_negative += 1
                false_negatives.append(screenshot["image"][:4])

        # Every tooltip still in the list is a false positive
        for coords in scaled_coords:
            false_positive += 1

        if len(scaled_coords) > 0:
            false_positives.append(screenshot["image"][:4])

        # Save the result
        cv2.imwrite(f"Dataset/predictions/contoured_{screenshot["image"][:4]}.png", contoured)

    # Stats
    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    f1 = 2 * precision * recall / (precision + recall)
    IoU_mean = IoU_sum / true_positive

    # All the printing
    print(f"\nTrue Positives: {true_positive}")
    print(f"False Positives: {false_positive}")
    print(f"False Negatives: {false_negative}")
    print(f"Negative images with nothing detected: {true_negative}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F1: {f1}")
    print(f"IoU Mean: {IoU_mean}")

    print(f"These screenshots had false positives: {false_positives}")
    print(f"These screenshots had false negatives: {false_negatives}")

if __name__ == "__main__":
    main()