#!/usr/bin/env python

"""
GlomDetect - annotation-centered WSI dataset builder

Goals
-----
- Represent every expert glomerulus.
- Generate positive 1024x1024 patches around expert annotations.
- Prefer patches containing no partially visible/unlabelled glomeruli.
- Label every glomerulus fully contained in a selected patch.
- Sample tissue-rich negative patches only when they have zero
  intersection with any expert glomerulus.

This creates a DEVELOPMENT/TRAINING dataset.
Independent validation must be performed at slide/patient level.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import openslide


def load_boxes(path):

    data = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    feats = (
        data["features"]
        if isinstance(data, dict)
        and data.get("type") == "FeatureCollection"
        else data
    )

    boxes = []

    for i, ft in enumerate(feats, start=1):

        g = ft.get("geometry", {})

        if g.get("type") != "Polygon":
            continue

        pts = g["coordinates"][0]

        xs = [float(p[0]) for p in pts]
        ys = [float(p[1]) for p in pts]

        xmin = min(xs)
        ymin = min(ys)
        xmax = max(xs)
        ymax = max(ys)

        boxes.append({
            "id": i,
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
            "cx": (xmin + xmax) / 2,
            "cy": (ymin + ymax) / 2
        })

    return boxes


def intersection_fraction(box, x0, y0, tile):

    x1 = x0 + tile
    y1 = y0 + tile

    ix0 = max(box["xmin"], x0)
    iy0 = max(box["ymin"], y0)
    ix1 = min(box["xmax"], x1)
    iy1 = min(box["ymax"], y1)

    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0

    full = (
        (box["xmax"] - box["xmin"])
        *
        (box["ymax"] - box["ymin"])
    )

    inter = (
        (ix1 - ix0)
        *
        (iy1 - iy0)
    )

    if full <= 0:
        return 0.0

    return inter / full


def fully_inside(box, x0, y0, tile, eps=1e-6):

    return (
        box["xmin"] >= x0 - eps
        and
        box["ymin"] >= y0 - eps
        and
        box["xmax"] <= x0 + tile + eps
        and
        box["ymax"] <= y0 + tile + eps
    )


def yolo_label(box, x0, y0, tile):

    cx = (
        box["cx"] - x0
    ) / tile

    cy = (
        box["cy"] - y0
    ) / tile

    w = (
        box["xmax"] - box["xmin"]
    ) / tile

    h = (
        box["ymax"] - box["ymin"]
    ) / tile

    return (
        f"0 "
        f"{cx:.6f} "
        f"{cy:.6f} "
        f"{w:.6f} "
        f"{h:.6f}"
    )


def tissue_fraction(rgb):

    a = np.asarray(
        rgb,
        dtype=np.uint8
    )

    mx = a.max(axis=2).astype(np.int16)
    mn = a.min(axis=2).astype(np.int16)

    mask = (
        (mx < 235)
        |
        ((mx - mn) > 18)
    )

    return float(mask.mean())


def clamp(v, lo, hi):

    return max(
        lo,
        min(v, hi)
    )


def candidate_origins(
    target,
    tile,
    W,
    H,
    search_step
):

    """
    Generate candidate patch origins around a target glomerulus.

    Start with exact centering, then systematically shift the patch
    around the target while keeping the target fully contained.
    """

    centered_x = int(
        round(target["cx"] - tile / 2)
    )

    centered_y = int(
        round(target["cy"] - tile / 2)
    )

    centered_x = int(
        clamp(
            centered_x,
            0,
            max(0, W - tile)
        )
    )

    centered_y = int(
        clamp(
            centered_y,
            0,
            max(0, H - tile)
        )
    )

    candidates = {
        (
            centered_x,
            centered_y
        )
    }

    # Legal x-origin range that keeps target fully inside
    min_x = int(
        np.ceil(
            target["xmax"] - tile
        )
    )

    max_x = int(
        np.floor(
            target["xmin"]
        )
    )

    min_y = int(
        np.ceil(
            target["ymax"] - tile
        )
    )

    max_y = int(
        np.floor(
            target["ymin"]
        )
    )

    min_x = max(
        0,
        min_x
    )

    max_x = min(
        W - tile,
        max_x
    )

    min_y = max(
        0,
        min_y
    )

    max_y = min(
        H - tile,
        max_y
    )

    if min_x > max_x or min_y > max_y:
        return list(candidates)

    xs = list(
        range(
            min_x,
            max_x + 1,
            search_step
        )
    )

    ys = list(
        range(
            min_y,
            max_y + 1,
            search_step
        )
    )

    # Ensure boundaries are considered
    if not xs or xs[-1] != max_x:
        xs.append(max_x)

    if not ys or ys[-1] != max_y:
        ys.append(max_y)

    for x in xs:
        for y in ys:
            candidates.add(
                (x, y)
            )

    return list(candidates)


def analyse_patch(
    x,
    y,
    tile,
    boxes
):

    full_ids = []
    partial = []

    for box in boxes:

        frac = intersection_fraction(
            box,
            x,
            y,
            tile
        )

        if frac <= 0:
            continue

        if fully_inside(
            box,
            x,
            y,
            tile
        ):
            full_ids.append(
                box["id"]
            )
        else:
            partial.append(
                (
                    box["id"],
                    frac
                )
            )

    return full_ids, partial


def choose_patch_for_target(
    target,
    boxes,
    tile,
    W,
    H,
    search_step
):

    candidates = candidate_origins(
        target,
        tile,
        W,
        H,
        search_step
    )

    scored = []

    for x, y in candidates:

        if not fully_inside(
            target,
            x,
            y,
            tile
        ):
            continue

        full_ids, partial = analyse_patch(
            x,
            y,
            tile,
            boxes
        )

        n_partial = len(partial)

        total_partial_fraction = sum(
            frac
            for _, frac in partial
        )

        # Prefer:
        # 1) zero partial objects
        # 2) fewer partial objects
        # 3) smaller amount of partial tissue
        # 4) more complete glomeruli in same patch
        # 5) target closer to patch centre

        patch_cx = x + tile / 2
        patch_cy = y + tile / 2

        centre_distance = (
            (target["cx"] - patch_cx) ** 2
            +
            (target["cy"] - patch_cy) ** 2
        )

        score = (
            0 if n_partial == 0 else 1,
            n_partial,
            total_partial_fraction,
            -len(full_ids),
            centre_distance,
            y,
            x
        )

        scored.append(
            (
                score,
                x,
                y,
                full_ids,
                partial
            )
        )

    if not scored:

        raise RuntimeError(
            f"No valid patch for glomerulus "
            f"{target['id']}"
        )

    scored.sort(
        key=lambda z: z[0]
    )

    return scored[0]


def grid_starts(length, tile, stride):

    if length <= tile:
        return [0]

    vals = list(
        range(
            0,
            length - tile + 1,
            stride
        )
    )

    end = length - tile

    if vals[-1] != end:
        vals.append(end)

    return vals


def main():

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--svs",
        required=True
    )

    ap.add_argument(
        "--geojson",
        required=True
    )

    ap.add_argument(
        "--out",
        default="GlomDetect_centered_dataset"
    )

    ap.add_argument(
        "--tile",
        type=int,
        default=1024
    )

    ap.add_argument(
        "--search-step",
        type=int,
        default=64
    )

    ap.add_argument(
        "--negative-stride",
        type=int,
        default=768
    )

    ap.add_argument(
        "--tissue-threshold",
        type=float,
        default=0.20
    )

    ap.add_argument(
        "--negative-ratio",
        type=float,
        default=1.0
    )

    ap.add_argument(
        "--jpeg-quality",
        type=int,
        default=90
    )

    args = ap.parse_args()

    svs = Path(args.svs)
    geo = Path(args.geojson)
    root = Path(args.out)

    images_dir = root / "images"
    labels_dir = root / "labels"

    images_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    labels_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    boxes = load_boxes(
        geo
    )

    box_by_id = {
        b["id"]: b
        for b in boxes
    }

    slide = openslide.OpenSlide(
        str(svs)
    )

    W, H = slide.dimensions

    print()
    print("Expert glomeruli:")
    print(len(boxes))

    print()
    print("Slide dimensions:")
    print(W, "x", H)

    # -------------------------------------------------
    # STEP 1
    # Find preferred centered/shifted patch for each
    # expert glomerulus.
    # -------------------------------------------------

    print()
    print("Searching clean positive patches...")

    target_choices = {}

    for n, target in enumerate(
        boxes,
        start=1
    ):

        (
            score,
            x,
            y,
            full_ids,
            partial
        ) = choose_patch_for_target(
            target,
            boxes,
            args.tile,
            W,
            H,
            args.search_step
        )

        target_choices[
            target["id"]
        ] = {
            "x": x,
            "y": y,
            "full_ids": full_ids,
            "partial": partial
        }

        if n % 50 == 0:
            print(
                "Patch search:",
                n,
                "/",
                len(boxes)
            )

    # -------------------------------------------------
    # STEP 2
    # Greedy deduplication / coverage.
    #
    # If one selected patch fully contains several
    # glomeruli, all are labelled and considered covered.
    # -------------------------------------------------

    uncovered = {
        b["id"]
        for b in boxes
    }

    selected_positive = []

    used_origins = set()

    while uncovered:

        best_target = None
        best_gain = -1
        best_clean = False

        for target_id in uncovered:

            choice = target_choices[
                target_id
            ]

            gain_ids = (
                set(choice["full_ids"])
                &
                uncovered
            )

            gain = len(
                gain_ids
            )

            clean = (
                len(choice["partial"])
                == 0
            )

            if (
                gain > best_gain
                or
                (
                    gain == best_gain
                    and clean
                    and not best_clean
                )
            ):
                best_target = target_id
                best_gain = gain
                best_clean = clean

        choice = target_choices[
            best_target
        ]

        origin = (
            choice["x"],
            choice["y"]
        )

        if origin not in used_origins:

            selected_positive.append(
                {
                    "x": choice["x"],
                    "y": choice["y"],
                    "full_ids": choice["full_ids"],
                    "partial": choice["partial"],
                    "source_target": best_target
                }
            )

            used_origins.add(
                origin
            )

        covered_now = set(
            choice["full_ids"]
        )

        uncovered -= (
            covered_now
        )

    # -------------------------------------------------
    # STEP 3
    # Generate positive images and labels.
    # -------------------------------------------------

    print()
    print("Generating positive patches...")

    represented = set()

    manifest_rows = []

    partial_rows = []

    positive_with_partial = 0
    total_partial_appearances = 0

    clean_positive_count = 0

    for i, item in enumerate(
        selected_positive,
        start=1
    ):

        x = item["x"]
        y = item["y"]

        full_ids, partial = analyse_patch(
            x,
            y,
            args.tile,
            boxes
        )

        if partial:
            positive_with_partial += 1
            total_partial_appearances += len(
                partial
            )
        else:
            clean_positive_count += 1

        region = slide.read_region(
            (x, y),
            0,
            (
                args.tile,
                args.tile
            )
        ).convert("RGB")

        stem = (
            f"{svs.stem}"
            f"_centered_{i:04d}"
            f"_x{x:06d}"
            f"_y{y:06d}"
        )

        labels = []

        for obj_id in full_ids:

            box = box_by_id[
                obj_id
            ]

            labels.append(
                yolo_label(
                    box,
                    x,
                    y,
                    args.tile
                )
            )

            represented.add(
                obj_id
            )

        region.save(
            images_dir
            /
            f"{stem}.jpg",
            quality=args.jpeg_quality
        )

        (
            labels_dir
            /
            f"{stem}.txt"
        ).write_text(
            "\n".join(labels),
            encoding="utf-8"
        )

        manifest_rows.append([
            stem,
            x,
            y,
            "positive",
            len(full_ids),
            ";".join(
                str(v)
                for v in full_ids
            ),
            len(partial),
            ";".join(
                str(obj_id)
                for obj_id, _
                in partial
            ),
            ";".join(
                f"{obj_id}:{frac:.4f}"
                for obj_id, frac
                in partial
            ),
            item["source_target"]
        ])

        for obj_id, frac in partial:

            partial_rows.append([
                stem,
                x,
                y,
                obj_id,
                frac
            ])

    # -------------------------------------------------
    # STEP 4
    # Clean negatives from a regular grid.
    # -------------------------------------------------

    print()
    print("Finding clean negative patches...")

    xs = grid_starts(
        W,
        args.tile,
        args.negative_stride
    )

    ys = grid_starts(
        H,
        args.tile,
        args.negative_stride
    )

    negative_candidates = []

    for y in ys:

        for x in xs:

            has_glomerulus = False

            for box in boxes:

                if (
                    intersection_fraction(
                        box,
                        x,
                        y,
                        args.tile
                    )
                    > 0
                ):
                    has_glomerulus = True
                    break

            if has_glomerulus:
                continue

            region = slide.read_region(
                (x, y),
                0,
                (
                    args.tile,
                    args.tile
                )
            ).convert("RGB")

            tf = tissue_fraction(
                region
            )

            if (
                tf
                >=
                args.tissue_threshold
            ):
                negative_candidates.append(
                    (
                        x,
                        y,
                        tf,
                        region
                    )
                )

    max_negatives = int(
        round(
            len(selected_positive)
            *
            args.negative_ratio
        )
    )

    negative_candidates.sort(
        key=lambda z: z[2],
        reverse=True
    )

    selected_negatives = (
        negative_candidates[
            :max_negatives
        ]
    )

    for i, (
        x,
        y,
        tf,
        region
    ) in enumerate(
        selected_negatives,
        start=1
    ):

        stem = (
            f"{svs.stem}"
            f"_negative_{i:04d}"
            f"_x{x:06d}"
            f"_y{y:06d}"
        )

        region.save(
            images_dir
            /
            f"{stem}.jpg",
            quality=args.jpeg_quality
        )

        (
            labels_dir
            /
            f"{stem}.txt"
        ).write_text(
            "",
            encoding="utf-8"
        )

        manifest_rows.append([
            stem,
            x,
            y,
            "negative",
            0,
            "",
            0,
            "",
            "",
            ""
        ])

    # -------------------------------------------------
    # AUDIT
    # -------------------------------------------------

    all_ids = {
        b["id"]
        for b in boxes
    }

    missing = sorted(
        all_ids
        -
        represented
    )

    with open(
        root / "manifest.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "tile",
            "x",
            "y",
            "type",
            "n_glomeruli",
            "glomerulus_ids",
            "n_partial_unlabelled",
            "partial_ids",
            "partial_visibility",
            "source_target"
        ])

        writer.writerows(
            manifest_rows
        )

    with open(
        root / "partial_audit.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "tile",
            "x",
            "y",
            "glomerulus_id",
            "visibility"
        ])

        writer.writerows(
            partial_rows
        )

    (
        root / "dataset.yaml"
    ).write_text(
        "path: .\n"
        "train: images\n"
        "val: images\n"
        "names:\n"
        "  0: glomerulus\n",
        encoding="utf-8"
    )

    mppx = slide.properties.get(
        openslide.PROPERTY_NAME_MPP_X,
        ""
    )

    mppy = slide.properties.get(
        openslide.PROPERTY_NAME_MPP_Y,
        ""
    )

    slide.close()

    summary = f"""
DONE

Slide:
{svs.name}

Dimensions:
{W} x {H} px

MPP X/Y:
{mppx} / {mppy}

Expert glomeruli:
{len(boxes)}

Tile size:
{args.tile}

Centered-patch search step:
{args.search_step}

Positive tiles:
{len(selected_positive)}

Clean positive tiles:
{clean_positive_count}

Positive tiles with unlabeled partial glomeruli:
{positive_with_partial}

Total unlabeled partial glomerulus appearances:
{total_partial_appearances}

Negative candidate tiles:
{len(negative_candidates)}

Negative tiles kept:
{len(selected_negatives)}

Total training tiles:
{len(selected_positive) + len(selected_negatives)}

Unique glomeruli represented:
{len(represented)}

Missing glomeruli:
{len(missing)}

Missing IDs:
{missing}

Output:
{root.resolve()}

IMPORTANT:

Positive patches were positioned relative to expert
annotations rather than being restricted to a fixed grid.

Every fully contained glomerulus in each positive patch
was labelled.

partial_audit.csv records any glomerulus intersecting a
positive patch without being fully contained.

Negative patches have zero intersection with all expert
glomerular bounding boxes.

dataset.yaml is only a placeholder.
Independent validation must be performed at slide/patient
level.
"""

    print(summary)

    (
        root
        /
        "BUILD_SUMMARY.txt"
    ).write_text(
        summary.strip() + "\n",
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()