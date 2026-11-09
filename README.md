# GlomQuant

## ⬇ [WINDOWS UYGULAMASINI İNDİR](https://github.com/anatomyrte-hash/GlomQuant/releases/download/v0.1.0-rc1/GlomQuant-0.1.0-rc1-Windows.zip)

**Programlama bilgisi gerekmez.**

1. ZIP dosyasını indirin ve tamamını bir klasöre çıkarın.
2. İlk kurulum için **1_KUR.cmd** dosyasını açın. İnternet gerekir.
3. Programı açmak için **3_BASLAT.cmd** dosyasını çalıştırın.


GlomQuant detects and counts two-dimensional glomerular profile candidates in rat kidney whole-slide images and exports editable, numbered GeoJSON boxes for QuPath. This is a Windows x64 **0.1.0-rc1 release candidate**, prepared for installation testing on another computer. It has not yet passed that external installation test.

## Getting started

This repository contains the source, weights and examples. For double-click Windows installation, use the Windows ZIP asset from the repository Releases section once it has been uploaded: https://github.com/anatomyrte-hash/GlomQuant/releases . The source-only download does not include the bundled Python runtime.

Extract the entire ZIP to a writable local folder. Double-click `1_KUR.cmd` to install the pinned dependencies into a private virtual environment. Bundled CPython 3.11.9 is supplied; no separate Python or programming is required. Internet is needed for the initial installation. Run `2_ORNEK_KONTROL.cmd` to repeat the five-tile compatibility check, then `3_BASLAT.cmd` to open the interface. The interface is currently Turkish: **Slayt seç** means select slide; **Analizi başlat** means start analysis; **Sonuç dosyalarını aç** opens outputs. Use the unchanged `.svs` slide in QuPath and import `MODEL_REVIEW.geojson` via File → Object data → Import objects.

Results and logs are stored under `%LOCALAPPDATA%/GlomQuant`. No input image is uploaded by the application. Installation obtains dependencies from PyPI. Moving the extracted folder after installation requires running setup again. Do not distribute an installed `.venv`; distribute the clean release ZIP.

## Frozen algorithm

YOLO11n weights, SHA-256 `98e9ce2434a3839e4dad168a114f48227b704fdc135adebcaa4ad00a4a7853aa`. Local training: slide 59477, 484 tiles, 20 epochs. Train and validation sets overlapped. Filter tuning: 59479. These are development slides, not independent tests. No retraining is performed by this application. The original training dataset builder and annotation reference are provided in `training/` for provenance, not invoked during inference.

CPU inference, 1024-pixel tiles, 768-pixel stride, 640 model input, confidence 0.10, model intersection-over-union 0.70, slide-level intersection-over-union 0.50. An additional confidence-ordered filter removes a box when intersection divided by the smaller box area is strictly greater than 0.50. All settings and model checksums are recorded. No tissue skipping or medulla exclusion is performed. Predictive logic was preserved from the study engine; the portable wrapper replaces machine-specific paths with packaged assets.

## Examples and validation

Five lossless reference patches from development slide 59479 are included. The compatibility gate compares 14 historical detections with coordinate tolerance 0.1 pixel and confidence tolerance 0.0001. Passing this gate does not establish full-slide accuracy. `examples/full_slide_reference.json` describes the original 59614 SVS (not included due to size) and its historical **automatic count of 768**, not an expert ground-truth count. Obtain source slides through the original archive; dataset attribution and license are in `licenses/DATA_NOTICE.md`.

The model was developed on limited rat kidney data. Generalization to other stains, organs, species, scanners or human material has not been established. Expert review is needed for study reference construction. Inference time is machine-dependent; no validated time-saving percentage or novice-user accuracy is claimed. Installation and whole-slide equivalence on another computer remain release acceptance steps. See `SECOND_COMPUTER_CHECK_TR.md` and the external release verification report.

## Citation and availability

Repository: https://github.com/anatomyrte-hash/GlomQuant . A Zenodo DOI has not yet been assigned. Do not cite a fictitious DOI or claim public availability yet. Before public release, complete contributor names, affiliations and software citation metadata; run the second-computer acceptance check; upload corresponding source and model as a versioned GitHub release; archive that same release in Zenodo and use its DOI in the paper. `PUBLICATION_RELEASE_TR.md` lists the remaining steps.

Software and packaged weights: AGPL-3.0-or-later (see `LICENSE` and Ultralytics' licensing information). Bundled Python and installed dependencies retain their own licenses. Data examples and training reference annotations are distributed separately under the original dataset attribution/share-alike conditions. This package contains no research participants' personal data in the application configuration. The unchanged model checkpoint can retain historical training-path metadata; it is not rewritten because that would change its identity.

## Running from source

Developers with Python 3.11 on Windows x64 may create a private environment, install `requirements.lock.txt`, run `python self_check.py`, and then `python app.py`. The numbered CMD launchers are for the Windows release ZIP that includes `runtime/`; they are not source-only launchers. Keep weights and examples in their supplied relative folders.
](https://github.com/anatomyrte-hash/GlomQuant/edit/main/README.md)
