"""
Evaluate tooltip detection against the annotated dataset.

Usage (from the project root):
    python evaluate_detection.py            # train split
    python evaluate_detection.py test       # test split
    python evaluate_detection.py all        # every image

Matching: for each annotated tooltip, the detection with the best IoU >= 0.5
counts as a true positive and can't be matched again. Unmatched annotations
are false negatives, unmatched detections are false positives.
Contoured images are saved to Dataset/predictions/.
"""

import json
import os
import sys
import cv2
from detect import detect_tooltips

ANNOTATIONS = os.path.join("Dataset", "annotations.json")
IMAGE_DIR = "Dataset"
OUTPUT_DIR = os.path.join("Dataset", "predictions")
IOU_THRESHOLD = 0.5


def iou(box_a, box_b):
    """IoU of two (xmin, ymin, xmax, ymax) boxes."""
    overlap_w = max(0, min(box_a[2], box_b[2]) - max(box_a[0], box_b[0]))
    overlap_h = max(0, min(box_a[3], box_b[3]) - max(box_a[1], box_b[1]))
    overlap_area = overlap_w * overlap_h
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return overlap_area / (area_a + area_b - overlap_area)


def main(split="train"):
    with open(ANNOTATIONS, "r", encoding="utf-8") as file:
        data = json.load(file)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    iou_sum = 0
    false_positive_images = []
    false_negative_images = []

    for screenshot in data:
        if split != "all" and screenshot["split"] != split:
            continue

        image_id = screenshot["image"][:4]
        print(f"Looking at {screenshot['image']}")
        img = cv2.imread(os.path.join(IMAGE_DIR, screenshot["image"]))

        detections, contoured = detect_tooltips(img, return_debug=True)
        cv2.imwrite(os.path.join(OUTPUT_DIR, f"contoured_{image_id}.png"), contoured)

        # Negative image with nothing detected
        if not screenshot["tooltips"] and not detections:
            true_negative += 1

        # Match each annotated tooltip to its best remaining detection
        for tooltip in screenshot["tooltips"]:
            best_iou = -1
            best_box = None
            for box in detections:
                score = iou(tooltip["bbox"], box)
                if score >= IOU_THRESHOLD and score > best_iou:
                    best_iou = score
                    best_box = box

            if best_box is not None:
                true_positive += 1
                iou_sum += best_iou
                detections.remove(best_box)
            else:
                false_negative += 1
                false_negative_images.append(image_id)

        # Every detection left over is a false positive
        false_positive += len(detections)
        if detections:
            false_positive_images.append(image_id)

    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    mean_iou = iou_sum / true_positive if true_positive else 0

    print(f"\nSplit: {split}")
    print(f"True Positives: {true_positive}")
    print(f"False Positives: {false_positive}")
    print(f"False Negatives: {false_negative}")
    print(f"Negative images with nothing detected: {true_negative}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"Mean IoU: {mean_iou:.4f}")
    print(f"These screenshots had false positives: {false_positive_images}")
    print(f"These screenshots had false negatives: {false_negative_images}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "train")