import csv
from pathlib import Path


def starts(length, tile, stride):
    if length <= tile:
        return [0]

    vals = list(range(0, length - tile + 1, stride))
    end = length - tile

    if vals[-1] != end:
        vals.append(end)

    return vals

def box_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)

    inter = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - inter

    if union <= 0:
        return 0.0

    return inter / union

def global_nms(detections, iou_threshold=0.50):
    if not detections:
        return []

    order = sorted(
        range(len(detections)),
        key=lambda i: detections[i]["confidence"],
        reverse=True
    )

    kept = []

    while order:
        current_index = order.pop(0)
        current = detections[current_index]

        kept.append(current)

        current_box = (
            current["x1"],
            current["y1"],
            current["x2"],
            current["y2"]
        )

        remaining = []

        for idx in order:
            candidate = detections[idx]

            candidate_box = (
                candidate["x1"],
                candidate["y1"],
                candidate["x2"],
                candidate["y2"]
            )

            overlap = box_iou(
                current_box,
                candidate_box
            )

            if overlap < iou_threshold:
                remaining.append(idx)

        order = remaining

    return kept

def save_csv(path, detections):
    fields = [
        "detection_id",
        "confidence",
        "x1",
        "y1",
        "x2",
        "y2",
        "cx",
        "cy",
        "width",
        "height",
        "source_tile_x",
        "source_tile_y"
    ]

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fields
        )

        writer.writeheader()

        for i, detection in enumerate(detections, start=1):
            writer.writerow({
                "detection_id": i,
                "confidence": detection["confidence"],
                "x1": detection["x1"],
                "y1": detection["y1"],
                "x2": detection["x2"],
                "y2": detection["y2"],
                "cx": detection["cx"],
                "cy": detection["cy"],
                "width": detection["width"],
                "height": detection["height"],
                "source_tile_x": detection["source_tile_x"],
                "source_tile_y": detection["source_tile_y"]
            })
