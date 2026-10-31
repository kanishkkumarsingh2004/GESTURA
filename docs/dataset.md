# Dataset Documentation

## Organization

Raw images are stored under `data/raw/<GESTURE>/` and are treated as immutable
— preprocessing never overwrites the originals. Processed images go to
`data/processed/`. Dataset split manifests live in `data/splits/`.

```
data/
├── raw/
│   ├── HELLO/
│   ├── YES/
│   ├── NO/
│   ├── THANK_YOU/
│   ├── PLEASE/
│   ├── STOP/
│   ├── HELP/
│   ├── GOOD/
│   ├── BAD/
│   ├── LOVE/
│   └── NONE/
├── processed/
└── splits/
    ├── train.csv
    ├── validation.csv
    └── test.csv
```

### Project gesture classes

HELLO, YES, NO, THANK_YOU, PLEASE, STOP, HELP, GOOD, BAD, LOVE, plus NONE for
unsupported/unknown input.

The class mapping is the single source of truth and lives in `config.yaml`
(`class_mapping`). `num_classes` is derived from it, never hardcoded.

## Downloading the HAGRID dataset

The HAGRID dataset provides many static hand-gesture classes. Use
`scripts/download_dataset.py` to download archives from the official SberCloud
source:

```bash
# Download all gesture archives into ./hagrid/dataset/
uv run --active python scripts/download_dataset.py --dataset

# Download specific gestures only
uv run --active python scripts/download_dataset.py --dataset \
    --targets stop like peace rock no_gesture

# Download + extract archives in place
uv run --active python scripts/download_dataset.py --dataset --extract

# Download annotations (hand landmarks)
uv run --active python scripts/download_dataset.py --annotations --extract
```

Downloaded archives are written to `--save_path` (default `./hagrid/dataset/`).

## Preparing data for training

Organize the extracted HAGRID class folders into the project `data/raw/`
layout and generate stratified split manifests:

```bash
uv run --active python scripts/prepare_dataset.py \
    --source ./hagrid/dataset/ \
    --dest data/raw/ \
    --seed 42
```

This:
- Copies images from each source class folder into `data/raw/<CLASS>/`
- Never overwrites existing raw files
- Writes `data/splits/train.csv`, `validation.csv`, `test.csv` (70/15/15)

The trainer (`python -m train.train`) derives `num_classes` and the class
mapping automatically from `data/raw/` subdirectories, so the dataset can be
used to train on HAGRID classes directly. Update `config.yaml`
`class_mapping` to match the classes you prepared.

## Dataset splitting rules

- Splits prevent leakage: near-identical frames from one recording session must
  not appear in both training and test sets. For production, split at the
  session/participant level rather than purely random per-image splits.
- Recommended starting split: 70% train, 15% validation, 15% test.
- Never mix training and testing datasets.

## Dataset quality

Collect images covering different lighting, backgrounds, hand orientations,
users, camera distances, skin tones, and hand sizes, plus negative samples for
the `NONE` class. Never fabricate dataset statistics.
