# AgriSense AI — Phase 1 Audit and Gap Report

Repository root: `C:\Users\ankul\OneDrive\Desktop\MAJRO\AgriSense` (branch `main`).
This audit reads only what already exists in the repo — code, configs, logs, notebooks,
artifacts, docs. No experiments were run, no numbers were estimated or invented. Every
number below is quoted verbatim from a cited file. Where a number the paper will need does
not exist anywhere in the repo, it is listed only in the gap table, never in sections 1–6.

---

## 1. Every model trained

**Only one model has actually been trained to completion in this repo.** The "full" two-stage
pipeline (`ml/src/agrisense_pd/train/stage1.py`, `stage2.py`) is fully implemented but has
**not** been run — there is no corresponding `.onnx`, checkpoint, or metrics artifact for it
anywhere in the repo, and `serving/models/` is gitignored and empty. This is stated explicitly
in `documents/DATASETS.md` lines 139–151 and `ml/artifacts/results_and_accuracy/README.md`
lines 41–56.

### The one trained model: Stage-1-only species classifier

Produced by `ml/notebooks/AgriSense_Minimal_Train_Colab.ipynb`, artifacts committed at
`ml/artifacts/results_and_accuracy/`.

- **Architecture/backbone**: `yolo11n-cls` (Ultralytics YOLO11, "nano" classification
  variant). Source: `ml/artifacts/results_and_accuracy/metrics.json:2` (`"model": "yolo11n-cls"`)
  and `args.yaml:3` (`model: yolo11n-cls.pt`).
- **Transfer-learned or from scratch**: transfer-learned. `args.yaml:18` sets `pretrained: true`
  (Ultralytics' COCO/ImageNet-pretrained `yolo11n-cls.pt` checkpoint fine-tuned on PlantVillage).
- **Total / trainable parameter counts**: **not recorded anywhere in the repo.** No
  `model.info()` output, no parameter count in `metrics.json`, `args.yaml`, or the notebook
  cells. `torch`/`ultralytics` are not installed in this audit environment so it cannot be
  computed locally either. → gap table (not fabricated here).
- **Input resolution**: 224×224. `metrics.json:5` (`"imgsz": 224`), `args.yaml:9`.
- **Full class list (38 classes)**, verbatim from `metrics.json:11-50`:
  `Apple___Apple_scab`, `Apple___Black_rot`, `Apple___Cedar_apple_rust`, `Apple___healthy`,
  `Blueberry___healthy`, `Cherry_(including_sour)___Powdery_mildew`,
  `Cherry_(including_sour)___healthy`, `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot`,
  `Corn_(maize)___Common_rust_`, `Corn_(maize)___Northern_Leaf_Blight`, `Corn_(maize)___healthy`,
  `Grape___Black_rot`, `Grape___Esca_(Black_Measles)`, `Grape___Leaf_blight_(Isariopsis_Leaf_Spot)`,
  `Grape___healthy`, `Orange___Haunglongbing_(Citrus_greening)`, `Peach___Bacterial_spot`,
  `Peach___healthy`, `Pepper,_bell___Bacterial_spot`, `Pepper,_bell___healthy`,
  `Potato___Early_blight`, `Potato___Late_blight`, `Potato___healthy`, `Raspberry___healthy`,
  `Soybean___healthy`, `Squash___Powdery_mildew`, `Strawberry___Leaf_scorch`,
  `Strawberry___healthy`, `Tomato___Bacterial_spot`, `Tomato___Early_blight`,
  `Tomato___Late_blight`, `Tomato___Leaf_Mold`, `Tomato___Septoria_leaf_spot`,
  `Tomato___Spider_mites Two-spotted_spider_mite`, `Tomato___Target_Spot`,
  `Tomato___Tomato_Yellow_Leaf_Curl_Virus`, `Tomato___Tomato_mosaic_virus`, `Tomato___healthy`.
- **Every metric present in the logs**:
  - `metrics.json` (final): `"val_top1": 0.9931866526603699`, `"val_top5": 1.0`.
  - `results.csv` (per-epoch training log, all 9 columns, exact values):
    | epoch | time (s) | train/loss | top1 | top5 | val/loss | lr/pg0 | lr/pg1 | lr/pg2 |
    |---|---|---|---|---|---|---|---|---|
    | 1 | 265.928 | 1.68919 | 0.94752 | 0.99816 | 0.21023 | 7.92165e-05 | 7.92165e-05 | 7.92165e-05 |
    | 2 | 524.739 | 0.19834 | 0.97873 | 0.99972 | 0.07124 | 0.000143561 | 0.000143561 | 0.000143561 |
    | 3 | 780.502 | 0.10881 | 0.98914 | 1 | 0.03825 | 0.000156518 | 0.000156518 | 0.000156518 |
    | 4 | 1040.41 | 0.07452 | 0.99208 | 1 | 0.02821 | 8.37847e-05 | 8.37847e-05 | 8.37847e-05 |
    | 5 | 1299.99 | 0.05237 | 0.99319 | 1 | 0.02396 | 2.48797e-05 | 2.48797e-05 | 2.48797e-05 |
  - No precision/recall/F1 or per-class breakdown numbers are present anywhere (only
    `confusion_matrix.png` / `confusion_matrix_normalized.png` images exist — these are
    images, not machine-readable numbers, and were not decoded for this audit).
- **Epochs**: 5 (`args.yaml:5`, `metrics.json:3`). **Batch**: 64. **Seed**: 42.
  **Optimizer**: `auto` (Ultralytics default), `cos_lr: true`. Full hyperparameter dump is
  `ml/artifacts/results_and_accuracy/args.yaml` (117 keys, e.g. `lr0: 0.01`, `momentum: 0.937`,
  `weight_decay: 0.0005`, augmentation params `hsv_h: 0.015`, `degrees: 0.0`, `fliplr: 0.5`,
  `mosaic: 1.0`).
- **Dataset used for this run**: PlantVillage only (`mohitsingh1804/plantvillage` on Kaggle).
  **Train / val images: 43,444 / 10,861** (`metrics.json:8-9`, matches
  `ml/artifacts/results_and_accuracy/README.md:27`).
- **Exported artifact**: `ml/artifacts/results_and_accuracy/weights/species.onnx`, opset 12,
  dynamic, simplified (`ml/notebooks/AgriSense_Minimal_Train_Colab.ipynb`, cell 19: `model.export(format='onnx', opset=12, dynamic=True, simplify=True, imgsz=IMGSZ)`).
- **On-disk model sizes** (measured directly from the committed files, this audit):
  `weights/best.pt` = 3,279,554 bytes (3.28 MB); `weights/last.pt` = 3,279,554 bytes;
  `weights/species.onnx` = 6,396,724 bytes (6.40 MB).
- **What this model is not**, per `ml/artifacts/results_and_accuracy/README.md:41-56` (the
  repo's own words, quoted because they matter for the paper's honesty framing): "Not the
  production two-stage pipeline"; "Not what the app currently runs" (the deployed Plant Scan
  uses Gemini vision, not this file — see §6); "Not a real-world accuracy number" — "PlantVillage
  is lab imagery — single detached leaves on plain backgrounds. Accuracy here runs high and does
  not transfer to field photos."

### The unrealized full pipeline (designed, not trained)

Configured in `ml/configs/train_stage1.yaml` and `ml/configs/train_stage2.yaml`, implemented in
`ml/src/agrisense_pd/train/stage1.py` / `stage2.py`, but never executed to produce an artifact:

- **Stage 1 (species)**: `yolo11s-cls` ("small", one size up from nano), 224px, **30 epochs**,
  batch 128 (drop to 64 on OOM), `patience: 10`, across all four training datasets combined.
- **Stage 2 (per-species disease)**: `yolo11n-cls` per species (smaller base — "per-species
  datasets are small"), 224px, 30 epochs, batch 64, `patience: 8`, with an optional
  `overrides:` block per species for a Phase-F aggressive-augmentation retrain (currently empty
  — `overrides: {}` in `train_stage2.yaml:29`).
- Both stages share `seed: 42`.
- No trained weights, no `metrics.json`, no `results.csv` exist for either stage of this
  configuration anywhere in the repo.

### Non-classification models present in code but not trained/artifacted

- `ml/src/agrisense_pd/detect/train_detector.py` — a YOLO leaf-detector training script for
  the conditional Phase E2 (only run "if Phase E1's report says to", per `ml/README.md:23`).
  No weights or metrics exist for it. `registry.py:79-84` reads
  `artifacts/phase_e2_detector_metrics.json` and a `detector/leaf_detector.onnx` if present —
  neither exists in the repo.

---

## 2. Exact dataset manifest

Source of truth per `documents/DATASETS.md:3-6`: `ml/configs/sources.yaml` (acquisition) +
`ml/configs/paths.yaml` (what's actually wired into training vs. eval). **No manifest file
with real per-class counts (`manifests/master.csv`, `fingerprints.csv`) exists in this repo** —
those are written to Google Drive during a Colab run (`ml/README.md:55-56`,
`ml/configs/paths.yaml:7`) and are not committed. The counts below are the *documented/expected*
counts from `sources.yaml` and `DATASETS.md`, not counts read from an actual manifest — treat
accordingly; per-class counts below are only what's explicitly stated, nothing is extrapolated.

### Training datasets (`ml/configs/paths.yaml:33-36`: `training_datasets`)

| Source | Kind | Approx size | Image count (as documented) | Classes | Licence |
|---|---|---|---|---|---|
| PlantVillage | Kaggle `mohitsingh1804/plantvillage` | ~800 MB | Used in the one completed run: 43,444 train + 10,861 val = **54,305** (post-split, that run's split only — see §3). No total pre-split count is recorded in `sources.yaml`. | 38 (`Species___Condition`) | Not stated in `sources.yaml` or `DATASETS.md` |
| PlantWild | HuggingFace `uqtwei2/PlantWild` | ~4.4 GB | **30,030** (v1: 18,542 images / 89 classes + v2: 11,488 images / 115 classes = 30,030 / 146 classes total) — `sources.yaml:29-31`, `DATASETS.md:32` | 146 total (v1 89 + v2 115) | **CC BY-NC-ND 4.0** (non-commercial, no derivatives) — `sources.yaml:32`, `DATASETS.md:34` |
| Cassava Leaf Disease | Kaggle `nirmalsankalana/cassava-leaf-disease-classification` | ~5.8 GB | **21,367** — `sources.yaml:60`, `DATASETS.md:50` | 5 (Bacterial Blight, Brown Streak Disease, Green Mottle, Mosaic Disease, healthy) | Not stated |
| Rice Leaf Disease | Kaggle `nirmalsankalana/rice-leaf-disease-image` | ~500 MB | **5,932** total: Bacterial Blight 1,584 / Blast 1,440 / Brown Spot 1,600 / Tungro 1,308 — `sources.yaml:74-77`, `DATASETS.md:66` | 4 (no `healthy` class — `sources.yaml:78-79`) | Not stated |

`DATASETS.md:73`: **"Training total: roughly 57,000+ images before cleaning and deduplication"**
— note this is an approximate figure stated by the repo's own docs, not an exact manifest count,
and it is **before** the dedup/reject pipeline in `clean.py` runs (which removes unreadable,
too-small, exact-duplicate, unmapped-label, and PlantDoc-overlap images — the post-clean count is
not recorded anywhere since `clean.py` has not been run to completion / its output is not
committed).

**Note on the "100,000+ images" claim**: `AgriSense_Paper_Prompt.md:273` states "trained by us on
100,000+ images." This is **not supported** by any file in this repo — the documented training
total across all four configured sources is ~57,000 images (pre-cleaning), and the only run that
actually happened used 54,305 images from one source (PlantVillage) alone. This claim must not
appear in the manuscript as written; use the actual manifest figures once §2's gaps are filled,
or the pre-cleaning ~57,000 figure with the "not yet fully acquired/trained" caveat.

### Evaluation-only dataset (`ml/configs/paths.yaml:41-42`: `eval_datasets`, never merged into training)

| Source | Kind | Approx size | Format | Notes |
|---|---|---|---|---|
| PlantDoc | GitHub `pratikkayal/PlantDoc-Object-Detection-Dataset` | ~1.7 GB | Images + Pascal VOC XML boxes (object-detection variant, not classification-folder variant — `sources.yaml:104-112`) | Held out entirely from training; this is the field-realism eval set the paper's E1 depends on |

### Excluded source

- **Digipathos** (Embrapa): `kind: unavailable` in `sources.yaml:82-101`. Confirmed dead host
  (`ECONNREFUSED 200.0.70.2:443`), reproduced locally and from Colab. Not deleted, kept for the
  record in case the service returns. Contributes 0 images.

### Public-dataset vs. field-collected-by-us split

**All four training sources and the one eval source are public datasets acquired from
Kaggle/HuggingFace/GitHub.** There is no field-collected-by-us imagery anywhere in the ML
pipeline as of this audit — no directory, config entry, or manifest row represents images
captured by the project's own ESP32-CAM. (`AgriSense_Paper_Prompt.md`'s E1 requires exactly this:
"300+ images captured by our own ESP32-CAM in real field conditions... Hand-labelled" — this does
not exist yet; see gap table E1.)

### Licence note for the paper

Only PlantWild's licence is explicitly recorded in the repo (`CC BY-NC-ND 4.0` — non-commercial,
no derivatives). No licence is recorded in `sources.yaml` or `DATASETS.md` for PlantVillage,
Cassava, Rice, or PlantDoc. These must be looked up from each dataset's own Kaggle/GitHub page
before the manuscript's Data Availability / licensing statement is written — do not assume a
licence not stated in this repo.

---

## 3. Split strategy

**Two different split mechanisms exist in this repo, and they are not the same code path. This
matters directly for leakage risk.**

### 3a. The full pipeline's split (`ml/src/agrisense_pd/data/split.py`) — NOT what produced the trained model

This is a stratified, **dup_group-aware** split, seeded (`SEED=42`), target ratios
`{"train": 0.8, "val": 0.1, "test": 0.1}` (`split.py:30`). Its own module docstring
(`split.py:1-16`) states the exact rationale:

> "Why dup_group-aware: an exact-hash dedup does not catch near-duplicate frames of the same
> leaf. If those straddle train/test, validation accuracy overstates real generalization. Every
> dup_group is therefore assigned to exactly one split as a whole."

`dup_group` assignment happens upstream in `ml/src/agrisense_pd/data/clean.py`
(`_cluster_duplicates`, lines 156-213): exact duplicates are collapsed by SHA-256 first
(PlantVillage wins ties on a tie-break sort), then remaining images are perceptual-hash (phash)
bucketed and clustered by Hamming distance (`PHASH_HAMMING_THRESHOLD`, from `imaging.py`) so that
near-duplicate crops/rotations of the same source photo land in the same `dup_group`. `split.py`
then assigns each whole `dup_group` to exactly one of train/val/test
(`assign_splits`, lines 45-96) — a greedy per-stratum deficit-fill assignment keyed on
`(species, condition)`, with a small-stratum guarantee that val/test each get at least one group
if the stratum has ≥10 images (`MIN_IMAGES_FOR_GUARANTEE = 10`, lines 79-94).

`clean.py` additionally cross-checks every PlantWild training image's phash against every
PlantDoc (eval-only) image's phash and rejects any near-duplicate with `reason: plantdoc_overlap`
(`clean.py:274-293`) — specifically because PlantWild and PlantDoc are both crowdsourced from the
same search engines (Google/Ecosia/Baidu), so a genuine cross-dataset near-duplicate is possible
without this check.

Unit tests exist and pass for this split logic: `ml/tests/test_split.py` — 4 tests, verifying
(a) no `dup_group` spans two splits, (b) ratios land within `RATIO_TOLERANCE = 0.02` of target,
(c) determinism across repeated runs with the same seed, (d) small-but-sufficient strata still
get at least one val and one test image. **This logic has never actually been run against real
data** — `master.csv` does not exist in the repo (would be on Google Drive per
`ml/configs/paths.yaml`), so this split code path did not produce the one model that was
actually trained.

### 3b. The split that actually produced the trained model — plain random 80/20, no dedup awareness

`ml/notebooks/AgriSense_Minimal_Train_Colab.ipynb`, cell 11, builds its own split independently
of `agrisense_pd/data/split.py`:

```python
random.seed(42)
MAX_PER_CLASS = 400
VAL_FRACTION  = 0.2
...
for c in classes:
    imgs = sorted(list(c.glob('*.jp*g')) + list(c.glob('*.png')) + list(c.glob('*.JPG')))
    random.shuffle(imgs)
    if MAX_PER_CLASS:
        imgs = imgs[:MAX_PER_CLASS]
    n_val = max(1, int(len(imgs) * VAL_FRACTION))
    for split, chunk in (('val', imgs[:n_val]), ('train', imgs[n_val:])):
        ...
```

This is a per-class `random.shuffle` + slice into an 80/20 train/val split, with **no
perceptual-hash clustering, no exact-duplicate collapse, no dup_group, and no cross-check
against near-duplicate frames**. PlantVillage is documented and widely known to contain
augmented/near-duplicate images (small rotations, brightness/contrast variants, and repeated
crops of the same source leaf) within a class folder. Nothing in this notebook's split code
detects or prevents such a near-duplicate pair from landing one copy in `train/` and the other
in `val/`.

**Plain statement for the paper**: the split that produced the reported 99.32% top-1 /
100% top-5 numbers in `ml/artifacts/results_and_accuracy/` is a naive random split with no
duplicate- or near-duplicate-awareness. **Leakage across train/val is plausible and has not been
ruled out.** This is exactly the situation the paper's E2 (leakage audit and regrouped split) is
designed to test — a positive leakage finding (accuracy drops after a dedup-aware regrouped
split) is the likely outcome given what the split code actually did, not a hypothetical. The
dup_group-aware `split.py` exists and is unit-tested, but was never applied to this run — running
`clean.py` + `split.py` on the PlantVillage-only data and retraining under that split is exactly
what E2 requires and is not yet done.

---

## 4. Firmware

**Working-tree caveat (read this before the rest of §4):** `git status` at the start of this
audit shows both `esp32_firmware/AgriSense_ESP32/AgriSense_ESP32.ino` and
`esp32_firmware/WIRING_GUIDE.md` as modified-but-uncommitted. The current working-tree content
of `AgriSense_ESP32.ino` is **not sensor/pump firmware at all** — it is an unrelated Arduino
UNO + L298N + HC-SR04 "4 Motor Obstacle Avoiding Car" sketch (motor pins `ENA/IN1/IN2`,
`ENB/IN3/IN4`, ultrasonic `TRIG/ECHO`, `Serial.begin(9600)`), with no Wi-Fi, no sensors matching
this project, and no relay/pump logic. This appears to be an accidental file overwrite (e.g. a
paste from an unrelated Arduino tutorial project) rather than an intentional firmware change —
it does not build against this project's wiring, backend endpoints, or Supabase schema. The
working-tree diff for `WIRING_GUIDE.md` is similarly a partial content loss: it drops the
"Powering the relay" JD-VCC troubleshooting section and the "Use NO, never NC" warning that are
present at `HEAD`, and introduces a stray `r` character into the pin-mapping section heading.
**Everything described below for `AgriSense_ESP32.ino` is read from the last commit (`git show
HEAD:...`), not the current working tree**, because the working-tree version is not this
project's firmware. This discrepancy should be resolved (revert the working-tree changes, or
confirm intent) before the paper cites firmware behaviour, and is flagged again in "assumptions"
below.

### `esp32_firmware/AgriSense_ESP32/AgriSense_ESP32.ino` (sensor/pump node, ESP32 DevKit V1, from `HEAD`)

- **Sensors actually read**:
  - DHT11 (air temperature + humidity), `DHT_PIN = GPIO 4`, `DHT11` type. Retried up to
    `DHT_READ_ATTEMPTS = 3` times, 2.2 s apart (`DHT_RETRY_DELAY_MS = 2200`), per tick; on total
    failure it falls back to the last known-good reading rather than sending zeros, unless the
    sensor has *never* read successfully since boot.
  - Capacitive soil moisture sensor (analog), `SOIL_MOISTURE_PIN = GPIO 34` (12-bit ADC,
    input-only). Calibrated via two measured constants: `SOIL_DRY_VALUE = 4095` (raw ADC fully
    dry) and `SOIL_WET_VALUE = 30` (raw ADC submerged in saturated soil).
  - Rain sensor (digital output), `RAIN_SENSOR_PIN = GPIO 33`, active-LOW (`readRainDetected()`
    returns `digitalRead(...) == LOW`). Documented as unable to be health-checked (a disconnected
    floating pin reads identically to "no rain").
  - No NPK sensor, no DS18B20, no solar/PAR sensor, and no soil-temperature *probe* — "soil
    temperature" in this firmware is a derived value: air temperature + a fixed offset
    (`SOIL_TEMP_OFFSET = -2.5f`), not a measured value from a second probe.
- **Actuator controlled**: one relay (`RELAY_PUMP_PIN = GPIO 16`), active-LOW
  (`RELAY_ACTIVE_LOW = 1`; `RELAY_ON_LEVEL = LOW`), driving a single water pump via the relay's
  NO (normally-open) contact.
- **Calibration transfer function** — soil moisture percentage, exact code
  (`readSoilMoisturePct()`):
  ```
  pct = ((SOIL_DRY_VALUE - raw) / (SOIL_DRY_VALUE - SOIL_WET_VALUE)) * 100.0
  ```
  with `raw` an averaged ADC reading, and a disconnect guard: if `raw < SOIL_DISCONNECT_ADC`
  (default `10`, "measured on the project's own board, where an unplugged probe floats to ~0 and
  a submerged probe reads ~30" — `WIRING_GUIDE.md:137-139`), the probe is treated as
  disconnected/not-ok rather than producing a fake percentage.
- **Scheduling/decision logic** — this is a **real closed-loop rule with hysteresis and safety
  interlocks, not a fixed timer.** Exact decision function, `pumpShouldRun()`:
  ```cpp
  bool pumpShouldRun(float soilPct, bool soilOk, bool rain, bool pumpOn, int8_t manual) {
    if (!soilOk)                 return false;  // no probe -> never water blind
    if (rain)                    return false;  // raining -> field waters itself
    if (soilPct >= SOIL_WET_PCT) return false;  // already wet -> stop/stay off
    if (manual < 0)               return false;  // force-stop from website/app
    if (manual > 0)               return true;   // manual run from website/app
    if (soilPct <  SOIL_DRY_PCT) return true;
    return pumpOn;                              // inside the band -> hold, do not chatter
  }
  ```
  Two-threshold hysteresis band: `SOIL_DRY_PCT = 30` (below → start), `SOIL_WET_PCT = 70`
  (at/above → stop); inside the 30–70% band the pump holds its current state rather than
  chattering. Sensor safety rules (disconnected probe, rain, already-wet) are checked *before*
  and always override a manual command — a manual PUMP_ON cannot force watering through rain or
  wet soil. Evaluated once per 10 s telemetry tick, called from `autoIrrigate()`.
  Additional safety limits: `PUMP_MAX_RUNTIME_MS = 15 min` hard cutoff regardless of sensor
  state, followed by `PUMP_COOLDOWN_MS = 30 min` before auto-irrigation may restart the pump
  (guards against a mis-calibrated probe cycling the pump forever); a manual override from the
  website/app lasts `MANUAL_OVERRIDE_MS` (constant defined earlier in the file) before
  auto-irrigation resumes control.
  Self-test: `#if RUN_SELFTEST` block runs `selfTestPumpLogic()` at boot with 11 hand-written
  cases (dry+idle→start, dry+raining→stay off, probe unplugged→fail-safe, in-band+running→hold
  on, in-band+idle→hold off, watered→stop, and four manual-override precedence cases), asserting
  the decision function's behaviour with no hardware attached.
- **Telemetry/command transport**: HTTPS REST directly to Supabase (`POST .../telemetry_data`
  every 10 s; RPC-based command polling every 5 s), per the file's own architecture comment
  block — not routed through `backend/main.py` for the sensor/pump data path (`backend/main.py`'s
  own docstring confirms: "It does NOT sit in the telemetry or manual-pump-control path — those
  go directly ESP32 <-> Supabase").
- **Deployed hardware / unit costs**: `esp32_firmware/WIRING_GUIDE.md` documents pin-level wiring
  for ESP32 DevKit V1 + DHT11 + capacitive soil moisture sensor + rain sensor module + one relay
  module, but **no unit costs or a bill of materials appear anywhere in `WIRING_GUIDE.md`,
  `ESP32CAM_UPLOAD_GUIDE.md`, `README.md`, or `documents/`** — a repo-wide search for
  currency/price patterns in `esp32_firmware/` and `documents/` returned no matches. → gap table.

### `esp32_firmware/AgriSense_ESP32CAM/AgriSense_ESP32CAM.ino` (camera node, AI-Thinker ESP32-CAM)

- **Sensor**: OV2640 camera module only (no other sensors on this board — the file's own header
  comment explains it is a *separate* board from the sensor node because the camera interface
  occupies GPIO 34 (soil ADC), GPIO 4 (flash LED / DHT11 pin), and GPIO 16 (PSRAM CS) on the
  same chip family).
- **Actuator**: none.
- **Scheduling/decision logic**: not a sensing/actuation loop — it's a demand-driven relay:
  polls `GET /api/camera/{id}/wanted` every `IDLE_POLL_MS = 3000` ms while idle; once a viewer is
  wanted, captures and POSTs JPEG frames to `/api/camera/{id}/frame`, rate-limited to
  `STREAM_FPS_CAP = 4` fps, until a response says no one is watching, then drops back to idle
  polling. Frame size/quality adapt to PSRAM presence: `FRAMESIZE_VGA` @ `JPEG_QUALITY_PSRAM = 12`
  with PSRAM, `FRAMESIZE_QVGA` @ `JPEG_QUALITY_NO_PSRAM = 15` without.
- **Auth**: `X-Cam-Key` header must match `CAM_UPLOAD_KEY` set in both the firmware and
  `backend/.env`.
- No cost figures for this board are recorded in the repo either.

### Dashboard/firmware sensor mismatch — verified current state

The memory note's flagged mismatch is **confirmed still present** in `web_dashboard/index.html`
(this is separate from the two files with uncommitted working-tree corruption above — this file
has no pending changes). The dashboard's telemetry grid includes cards for sensors the firmware
does not have:
- Line 432: `<div class="stat-subtitle">DS18B20 Sub-Surface Probe</div>` ("5. Root Zone
  Temperature").
- Lines 439-451: "6. Solar Radiation / PAR Intensity" card, unit `W/m²`.
- Lines 453-473: "7. NPK Soil Nutrients" card, `RS485 NPK Sensor Probe` subtitle, N/P/K in mg/kg.

`web_dashboard/app.js` confirms these are wired to real (but always-absent) telemetry fields
rather than being purely cosmetic: `state.telemetry.solarRadiation = data.solar_radiation || 0`
(line 390) and `state.telemetry.npk = { n: 0, p: 0, k: 0 }` (line 44) — since the firmware never
sends a `solar_radiation` field or NPK values, these always resolve to their `0`/`--` fallback.
`mobile_app/lib/types.ts:20` likewise declares `solar_radiation: number | null` in the shared
telemetry type. **Net effect**: the dashboard UI presents cards for DS18B20 root-zone
temperature, solar PAR, and RS485 NPK sensing that are permanently blank/zero placeholders in a
live deployment, because no code path (firmware or backend) ever populates them. This is UI
scaffolding for sensors that were never wired to hardware, not fabricated data — but it is a
UI/hardware claim mismatch that must not be implied as deployed capability in the paper's
hardware description or BOM.

---

## 5. Existing benchmarks

Every quantitative measurement found in the repo, with exact file and value:

| Measurement | Value | File |
|---|---|---|
| Validation top-1 accuracy (Stage-1-only, PlantVillage) | 0.9931866526603699 (99.32%) | `ml/artifacts/results_and_accuracy/metrics.json:51` |
| Validation top-5 accuracy | 1.0 (100%) | `ml/artifacts/results_and_accuracy/metrics.json:52` |
| Per-epoch train loss, val loss, top1, top5 | 5 rows, quoted in full in §1 | `ml/artifacts/results_and_accuracy/results.csv` |
| Per-epoch wall-clock time (cumulative, Colab T4) | 265.9s / 524.7s / 780.5s / 1040.4s / 1300.0s (epochs 1–5) | `results.csv` column `time` |
| `best.pt` file size | 3,279,554 bytes (3.28 MB) | measured this audit from `ml/artifacts/results_and_accuracy/weights/best.pt` |
| `species.onnx` file size | 6,396,724 bytes (6.40 MB) | measured this audit from `.../weights/species.onnx` |
| Train / val image counts (this run) | 43,444 / 10,861 | `metrics.json:8-9` |
| ONNX opset | 12 | `metrics.json`-adjacent export cell, `ml/notebooks/AgriSense_Minimal_Train_Colab.ipynb` cell 19 |
| Unit test suite result | 31 passed (ran this audit: `python -m pytest ml/tests -v` → `31 passed in 2.11s`) | `ml/tests/*.py`, confirms `README.md:242`'s claim |
| `test_plant_predict.py`'s `inference_ms` value | **850 — this is a hardcoded test-fixture input, not a measured latency.** `finalize_plant_diagnosis(..., "gemini-3.6-flash", 850)` passes 850 as an arbitrary argument to test the pass-through field; it is not a timed Gemini call. | `backend/test_plant_predict.py:8-15` |

**No inference latency on real hardware, no model RAM/memory usage, no power/energy
measurement, no uptime, no packet-loss figure, and no water-volume figure exist anywhere in
this repo.** These are all gap-table items (E3, E4, E8).

---

## 6. LLM layer

**Confirmed: `backend/main.py` calls the Gemini REST API directly, hardcoded, with no adapter
interface.** There is no `import openai`, no `google.generativeai`/`genai` SDK import, and no
`anthropic` import anywhere in `backend/` or `serving/` (confirmed by grep across both
directories — zero matches). `backend/requirements.txt` lists no LLM SDK at all (`fastapi`,
`uvicorn`, `supabase`, `python-dotenv`, `httpx` only) — the Gemini calls are raw HTTP via
`httpx`, not even the official Google SDK.

Exact call sites, `backend/main.py`:

- Line 68–69 (module-level config, no abstraction layer):
  ```python
  GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
  GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
  ```
- Line 738–741 (`/api/plant/predict` Gemini-vision fallback):
  ```python
  resp = await client.post(
      f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
      params={"key": GEMINI_API_KEY},
      json=body,
  )
  ```
- Line 845–846 (`/api/advisor/ask` farm-advisor chat — same pattern, second independent call
  site to the identical hardcoded endpoint):
  ```python
  f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
  params={"key": GEMINI_API_KEY},
  ```

Both call sites construct the Gemini-specific request body directly inline (`contents`/`parts`/
`inlineData`/`generationConfig.responseSchema` — Gemini's own JSON schema, not a
provider-neutral shape) and parse the Gemini-specific response shape directly
(`data["candidates"][0]["content"]["parts"][0]["text"]`, lines 748-757). There is no
`LLMProvider` interface, no strategy/adapter class, and no offline/local fallback path — if
`GEMINI_API_KEY` is unset, both endpoints return HTTP 503 (lines 706-710, 794-797) rather than
falling back to any alternate provider. `mobile_app/lib/*.ts` was also checked and contains no
direct vendor LLM calls — the client only calls this backend's own `/api/plant/predict` and
`/api/advisor/ask` endpoints, so the vendor coupling is fully server-side and confined to these
two call sites, but it is real, direct, and hardcoded to one named vendor and model string
(`gemini-3.6-flash`).

**Conclusion for the manuscript**: the paper's planned framing — "a provider-agnostic *LLM
reasoning layer* behind an adapter interface" (`AgriSense_Paper_Prompt.md:266-271`) — is **not
yet accurate to the artifact**. As that same prompt file states, this must be flagged for
refactoring rather than written around: either (a) refactor `backend/main.py` to introduce a
genuine adapter interface (e.g. an `LLMProvider` ABC with a Gemini implementation, keeping the
two call sites behind it) before the manuscript claims provider-agnosticism, or (b) describe the
current implementation honestly as a single hardcoded vendor integration and drop the
provider-agnostic claim. Per `AgriSense_Paper_Prompt.md`'s own instruction ("If the code still
calls a vendor SDK directly, flag it in the gap report as requiring refactoring... do not
quietly write around it"), this is flagged, not silently fixed, as part of Phase 1.

---

## GAP TABLE

Every number the paper needs (E1–E8) that does not currently exist anywhere in this repo.

| ID | Number needed | How to measure | Script / setup | Est. effort |
|----|---------------|----------------|-----------------|-------------|
| E1-a | Field test set: 300+ hand-labelled images from the project's own ESP32-CAM in real field conditions | Capture with the deployed ESP32-CAM firmware in situ (variable lighting, cluttered background, off-axis leaves, partial occlusion); label by hand against the 38-class (or fewer, field-relevant) taxonomy | New capture script/log + manual labelling spreadsheet; no code exists for this yet | High (days: hardware deployment + labelling) |
| E1-b | Lab accuracy vs. field accuracy vs. ~68% cross-domain SOTA, side by side | Run the trained `species.onnx` (or a retrained model) against E1-a's field set; compare to the 99.32% lab val-top1 already in `metrics.json` | `ml/src/agrisense_pd/eval/plantdoc_eval.py` (adapt for the new field set) or `evaluate_holdout.py` | Medium (once E1-a exists) |
| E1-c | Evaluation on held-out PlantDoc (already downloaded/available per `sources.yaml`, never yet run against the trained model) | Run `ml/src/agrisense_pd/eval/plantdoc_eval.py` against `species.onnx` | `ml/src/agrisense_pd/eval/plantdoc_eval.py` (exists, unrun) | Low–Medium |
| E2-a | Leakage audit: accuracy before vs. after a dedup-aware regrouped split | Run `clean.py` (dup_group/phash clustering) then `split.py` (dup_group-aware split) on the PlantVillage data actually used, retrain identically, compare to the existing 99.32%/100% numbers | `ml/src/agrisense_pd/data/clean.py` + `split.py` + `ml/notebooks/AgriSense_Minimal_Train_Colab.ipynb` (retrain step) | Medium (compute + one retrain run) |
| E3-a | Edge feasibility grid: chip (ESP32 vs ESP32-S3) × precision (FP32/INT8) × class count (2/4/8/16) × resolution (96/128/224px) — fits/doesn't-fit, accuracy, model size, latency, peak RAM, energy/inference per cell | Export INT8-quantized ONNX/TFLite variants at each resolution/class-count subset; flash to real ESP32 and ESP32-S3 hardware; measure on-device | No script exists; needs a TFLite-Micro or ESP-DL export pipeline (not present in `ml/src/agrisense_pd/export/`) + physical ESP32-S3 board | High |
| E4-a | Irrigation field trial: two plots, inline flow meter, closed-loop vs. fixed-schedule timer, ≥2 weeks, cumulative litres each, % reduction, soil-moisture mean/std each, yield/health proxy | Physical deployment: one plot on the existing `pumpShouldRun()` closed loop, one plot on a fixed timer (the backend's existing `TIMER` automation mode can serve as the control — see `backend/main.py`'s `/api/automation/mode`), both metered | Requires a flow meter (not in current BOM) + 2-plot field site; backend timer mode already exists, closed-loop firmware already exists | High (hardware + ≥2 weeks wall-clock) |
| E5-a | Ablation: backbone alone vs. +augmentation vs. FP32 vs. INT8 vs. sensor-only vs. vision-only vs. fused, identical settings | Series of controlled retrains from `ml/src/agrisense_pd/train/stage1.py` with augmentation toggled and `train_stage1.yaml`'s aug block zeroed for the "backbone alone" arm; INT8 export via a to-be-built quantization step; fused-decision logic does not yet exist in code (only vision-only inference exists today) | `ml/configs/train_stage1.yaml` (toggle augmentation) + new INT8 export script + new sensor-fusion decision code | High |
| E6-a | Statistical significance: ≥4 seeds, mean±std, paired t-tests, p-values vs. baselines | Re-run training (minimal or full pipeline) at ≥4 seeds (`seed:` in `train_stage1.yaml`/`paths.yaml`, currently fixed at 42 everywhere), record top1/top5 each run, run paired t-tests | `ml/configs/train_stage1.yaml` seed sweep + a new stats script (none exists in `ml/src/agrisense_pd/eval/`) | Medium–High (4× compute + new analysis script) |
| E7-a | Grad-CAM panel on correct/incorrect predictions per class, including ≥1 field failure case | Requires the PyTorch model (`best.pt`) + a Grad-CAM implementation (none present — `ml/src/agrisense_pd` has no explainability module) + at least one E1-a field failure case | New script, e.g. `ml/src/agrisense_pd/eval/gradcam.py` (does not exist) | Medium (needs `torch`/`ultralytics` + a field failure case from E1) |
| E8-a | Sensor-to-decision latency distribution | Instrument `AgriSense_ESP32.ino`'s `autoIrrigate()`/telemetry tick with timestamps (sensor read → Supabase write → command-decision), or measure round-trip from Supabase timestamps already being written | Firmware timestamp logging (small firmware change) or a Supabase query script against existing `telemetry_data`/`device_commands` tables | Medium |
| E8-b | Uptime over the deployment period | Long-running deployment log / Supabase `device_status` table query over the trial window | `documents/supabase_presence_and_pairing.sql` schema already tracks device status; needs a query/analysis script (none exists) | Low–Medium (once deployed for a period) |
| E8-c | Packet loss | Compare expected telemetry ticks (every 10s per firmware) vs. actual rows received in Supabase over the trial window | New analysis script against `telemetry_data` table | Low |
| — | Total/trainable parameter count for `yolo11n-cls` (and `yolo11s-cls` if the full pipeline is later run) | Load `best.pt` with `ultralytics`/`torch` and call `model.info()` / sum `p.numel()` over parameters | Needs `torch`+`ultralytics` installed (not available in this audit's environment) — one-line script once available | Low |
| — | Exact per-class image counts, post-cleaning/dedup, for all four training sources | Run `ml/src/agrisense_pd/data/download.py` → `clean.py` → `build_manifest.py` on the full ~13GB corpus | Full pipeline already implemented in `ml/src/agrisense_pd/data/`; needs Drive + Colab GPU session, not yet run | High (data acquisition + compute) |
| — | Bill of materials with per-component unit costs (ESP32 DevKit V1, ESP32-CAM, DHT11, capacitive soil sensor, rain sensor, relay module, pump, flow meter) | Price each component from the vendor actually used; none recorded anywhere in the repo | New table, sourced outside the repo (component invoices/vendor listings) | Low (research, not engineering) |
| — | Full two-stage pipeline trained end to end (`yolo11s-cls` stage 1 + per-species stage 2), with its own metrics.json/results.csv | Run `ml/notebooks/AgriSense_PlantDisease_Colab.ipynb` phases A–G to completion | Notebook exists and is documented (`ml/README.md`); needs ~13GB data acquisition + sustained GPU budget beyond free Colab tier | High |

**Quick-scan tags:**

- `[MEASURE: field accuracy vs lab accuracy vs ~68% SOTA, run species.onnx on hand-labelled ESP32-CAM field images, ml/src/agrisense_pd/eval/plantdoc_eval.py (adapted), effort=high]`
- `[MEASURE: PlantDoc held-out accuracy, run trained model against already-available PlantDoc set, ml/src/agrisense_pd/eval/plantdoc_eval.py (unrun), effort=low-medium]`
- `[MEASURE: leakage delta, retrain after clean.py+split.py dedup-aware regroup vs current naive split, ml/src/agrisense_pd/data/clean.py + split.py + retrain notebook, effort=medium]`
- `[MEASURE: edge feasibility grid (chip x precision x classes x resolution), export+flash+bench on real ESP32/ESP32-S3, no script exists yet — needs TFLite-Micro/ESP-DL export, effort=high]`
- `[MEASURE: flow-meter irrigation savings, 2-plot >=2wk field trial (closed-loop vs backend TIMER mode), needs physical flow meter + field site, effort=high]`
- `[MEASURE: ablation (backbone/+aug/FP32-INT8/sensor-vision-fused), controlled retrains + new INT8 export + new fusion code, effort=high]`
- `[MEASURE: significance across seeds, seed sweep on train_stage1.yaml + new stats script, effort=medium-high]`
- `[MEASURE: Grad-CAM incl field failure case, new gradcam.py using best.pt + torch, effort=medium]`
- `[MEASURE: sensor-to-decision latency distribution, firmware timestamp instrumentation or Supabase timestamp query, effort=medium]`
- `[MEASURE: uptime over trial, Supabase device_status query script, effort=low-medium]`
- `[MEASURE: packet loss, expected-vs-actual telemetry row count query, effort=low]`
- `[MEASURE: model parameter counts, model.info() via torch/ultralytics once installed, effort=low]`
- `[MEASURE: exact post-clean per-class dataset counts, run download.py->clean.py->build_manifest.py on full corpus, effort=high]`
- `[MEASURE: BOM unit costs, price each component from actual vendor used, effort=low]`
- `[MEASURE: full two-stage pipeline trained end-to-end, run AgriSense_PlantDisease_Colab.ipynb phases A-G, effort=high]`

---

## Assumptions made during this audit

1. **Working-tree vs. HEAD for firmware/wiring files.** `AgriSense_ESP32.ino` and
   `WIRING_GUIDE.md` both have uncommitted working-tree changes. The working-tree version of
   `AgriSense_ESP32.ino` is unrelated Arduino-Uno car-robot code, not this project's firmware, so
   §4 describes the last-committed (`HEAD`) version instead, retrieved via
   `git show HEAD:esp32_firmware/AgriSense_ESP32/AgriSense_ESP32.ino`. **This needs to be
   resolved by the repo owner** (confirm whether these uncommitted changes were accidental and
   should be discarded, or intentional and mid-edit) before the paper cites firmware behaviour as
   current. No files were modified by this audit — the extracted HEAD copy used for reading was
   written to a temp path and deleted afterward.
2. **Dataset counts in §2 are pre-acquisition/documented figures, not counts read from an actual
   manifest file.** `manifests/master.csv` and `fingerprints.csv` (the pipeline's real,
   post-cleaning source of truth) live on Google Drive per `ml/configs/paths.yaml` and are not
   committed to this git repo, so they could not be read. Only the one dataset actually used in
   the completed training run (PlantVillage, 43,444 train + 10,861 val) has a directly-verified
   count, from `metrics.json`.
3. **Parameter counts could not be computed** because `torch`/`ultralytics` are not installed in
   this audit's Python environment and no parameter count is logged in any committed artifact.
4. **Confusion-matrix images were not decoded to numbers.** `confusion_matrix.png` and
   `confusion_matrix_normalized.png` exist and are referenced but were not OCR'd/parsed for
   per-class numeric values in this audit — only what's in `metrics.json`/`results.csv` (scalar
   top1/top5, per-epoch loss) is reported as "logged metrics."
5. **Licence lookups for PlantVillage, Cassava, Rice, and PlantDoc were not performed outside the
   repo.** Only PlantWild's licence is stated in-repo (`sources.yaml`, `DATASETS.md`); the others
   are flagged as needing external lookup rather than assumed.
6. No code was changed, no experiments were run, and no training was executed as part of this
   audit — all content above is read directly from committed (or, where noted, HEAD-retrieved)
   repository state.

---

## Six-Point Audit of Sections I–III (post-draft)

Run against the actual drafted text in `paper/main.tex`, not a hypothetical. Section/equation
numbers below refer to `paper/main.tex` as drafted on 2026-09-19.

### 1. Framing audit

Section I opens with the published architecture (§I, ¶1) then pivots on the sentence: *"What
the published record does not resolve is a narrower and more consequential question: how much
of the accuracy reported for these systems survives contact with the conditions they are meant
to operate in."* This is a literature-gap frame, not a system frame — reinforced by the
preceding sentence, *"Building another instance of this architecture is therefore not, by
itself, a research contribution."* RQ1–RQ3/H1–H3 are present in §I-A (`sec:rqs`) in testable
form: each RQ has a directly falsifiable H with a numeric criterion (H1: field accuracy at/below
~68% or investigate as leakage; H2: a specific threshold pre-registered below; H3: an interval
pre-registered below). Contributions list (§I-B, 5 items) checked item by item against the
"system's own name load-bearing" test: none names AgriSense as the sentence's subject; all five
are phrased as measurements/audits/resolutions the paper delivers. No rewrite needed.

### 2. Related-work table stacked-column check

Column by column: **Hardware, Unit cost, Inference location, Accuracy, Field-validated,
Latency, Power, Closed-loop actuation** are the columns the manuscript brief (§6) specifies
outright — chosen because they're the right axes for a hardware-deployment comparison, not
because this work wins them. **Classes** and **Dataset provenance** were added because a fair
reviewer would expect them and this work does not come out ahead on either (This work: "38
(species only)" vs. Aqasizade et al.'s deliberately-reduced 3 coarse classes chosen specifically
to fit ESP32-S3 memory, which is a *harder* deployment achievement, not an easier one; and "100%
public — 0 field-collected images" on provenance, the same weakness flagged for every other row
in the table). No column exists mainly to flatter this work — the This-work row is the sparsest
row in the table (four cells read "TBD," two more are explicitly caveated as "unaudited"/"No").
At least one row beats this work on a real, already-measured axis, quoted from
Table~\ref{tab:related}: **Aqasizade et al. — Field-validated: Yes (7-day) vs. This work's No
(pending E1); Latency: 500 ms (measured) vs. This work's TBD; Accuracy: 94.6% / 0.94 F1 on a
real field deployment vs. This work's 99.32% lab-only, explicitly flagged unaudited for
leakage.** The table is not dishonest by the checklist's own test.

### 3. Gap statement

Quoted from the end of §II: *"No published work jointly (i) measures the accuracy lost when a
lab-trained classifier is evaluated on field images captured by its own deployed camera rather
than a third-party field dataset, (ii) reports the on-device feasibility boundary as a function
of class count, resolution, and quantization rather than a single operating point, and (iii)
verifies a claimed irrigation saving against a metered fixed-schedule control on identical
hardware. This is the gap this work characterizes; it is a gap in what is known, not a gap in
what a grower could buy — every individual capability compared in Table~\ref{tab:related} is
already commercially or academically available."* This is explicitly a knowledge gap (a
combination of measurements nobody has published together) and explicitly not a product gap —
the closing clause says so directly, naming ThingsBoard/OpenRemote-style provisioning and every
individual hardware capability as already available.

### 4. Methodology check

- **Every equation numbered, defined, used later or explicitly flagged for later use**: Eq. 1
  (cross-entropy training loss) is defined and will be directly evidenced by the real
  per-epoch train/val loss values already in `ml/artifacts/results_and_accuracy/results.csv`
  when §IV is drafted — not decorative, it's the literal function that produced those logged
  numbers. Eqs. 2–4 (P/R/F1/Accuracy) are the metrics every results table in §IV will report.
  Eq. 5 (soil calibration) feeds directly into Eq. 6. Eq. 6 (irrigation decision rule) is the
  system's only real closed-loop control law and is what E4's trial section will describe
  operationally. Eq. 7 (joint confidence) is what §IV's low-confidence/field-failure-case
  discussion (E7) will reference. No equation was deleted because none was decorative — each
  maps to a real formula/constant verified against the actual source file
  (`esp32_firmware/AgriSense_ESP32/AgriSense_ESP32.ino` at HEAD; `backend/main.py:763-775`),
  not invented for the paper.
- **Irrigation rule reproducible without code**: Eq. 6 plus the three named timing constants
  (15-min runtime cap, 30-min cooldown, 10-min manual-override expiry) given in the paragraph
  immediately following it are sufficient to reproduce the rule; no reference to firmware source
  is required.
- **Device-binding/multi-tenant ≤2 sentences, no subsection**: confirmed — one sentence, inside
  §III-A (System Architecture) prose, no subsection header: *"Device pairing and per-account
  data isolation follow a standard bearer-token/row-level-isolation scheme and receive no
  further treatment here, as this is a solved, non-novel implementation detail."*
- **No schema/API-listing/directory-structure/screenshot**: confirmed absent. Endpoints are
  referred to generically ("a diagnosis endpoint," "the farm-advisor endpoint"), never by literal
  route string; no table names, no directory tree, no UI screenshot anywhere in §I–III.
- **Sensor-vision fusion equation**: checked against `serving/pipeline_runtime.py` and
  `backend/main.py`'s advisor endpoint before writing anything — no fusion logic exists in
  either. §III-F states this plainly instead of manufacturing a formula, satisfying the
  checklist's explicit instruction not to invent one.

### 5. Pre-registered predictions (H2, H3)

**Timestamp: 2026-09-19T10:13:04Z. These are fixed before Section IV is drafted. If
experimental data contradicts them, the paper reports the contradiction; the prediction is not
retrofitted to the result.**

**H2 — predicted feasibility threshold**, reasoned from the verified edge-feasibility literature
(`main.tex` §III cites: Nyakuri et al. — ESP32-CAM/RPi Pico/Nano 33 BLE Sense could not run
their model at all; Samanta et al. — a model *did* run on plain ESP32-CAM at 92%; Aqasizade et
al. — ESP32-S3 ran a model at 94.6%/0.94 F1 only after the class count was deliberately reduced
to 3 coarse superclasses and the model was quantized to 1.1 MB) and from the base ESP32's
~520 KB SRAM with no FPU/vector unit versus the S3 variant's larger SRAM and optional PSRAM:

- **Base ESP32 predicted to fail (does not fit) at 16 classes / 224 px** (both FP32 and INT8) —
  activation memory at 224px for a MobileNet/YOLO11n-cls-style backbone at 16-way output is
  predicted to exceed available SRAM once framebuffer and Wi-Fi/HTTPS stack overhead are
  accounted for, mirroring Nyakuri et al.'s outright failure on the same chip family for a
  comparably-sized model.
- **Base ESP32 predicted to fail at 8 classes / 224 px FP32**, but predicted to *fit* at
  8 classes / 224 px INT8 (quantization is the deciding factor at this cell) and at 8 classes /
  96 px and 128 px in both precisions.
- **Base ESP32 predicted to fit at 2 and 4 classes across all three resolutions (96/128/224 px)
  in both precisions** — consistent with Samanta et al.'s working plain-ESP32-CAM deployment.
- **ESP32-S3 predicted to fit at 16 classes / 224 px INT8** (the class count and resolution this
  work actually needs for the 38-class species task would still exceed this and is predicted to
  require either a stage-2 per-species split, as already designed in
  `ml/src/agrisense_pd/train/stage2.yaml`, or further quantization) **but to fail at 16 classes
  / 224 px FP32** — S3's extra SRAM/PSRAM is predicted to move the boundary by roughly one
  resolution/class-count tier, not remove it.
- **Falsifiable statement**: if E3's sweep instead shows base ESP32 fitting at 16 classes/224px,
  or ESP32-S3 failing at 8 classes/128px, H2 as stated above is refuted and Section IV reports
  that refutation directly.

**H3 — predicted water reduction**: **22% ± 10%** (i.e., a plausible range of roughly 12%–32%),
reasoned from Usman & Zubairu's directly comparable two-plot, flow-meter-verified trial
(431.47 L vs. 592.39 L, 27.16% reduction, soil-moisture SD 1.35% vs. 10.46%) as the closest
available reference point, adjusted downward from their 27.16% and widened in uncertainty
because: (a) their controller uses a trained Random Forest regression model for irrigation
timing, a strictly more expressive control law than this work's two-threshold hysteresis rule
(Eq. 6), which is predicted to leave more water on the table at the margins of the dry/wet band;
and (b) this work's trial (E4) is planned as a single-site, single-season, ≥2-week trial —
shorter and less controlled than a full growing-season trial, which is predicted to widen the
confidence interval around the point estimate rather than change its center substantially.
**Falsifiable statement**: if E4 measures a reduction outside [12%, 32%], H3 as stated is
refuted and Section IV reports that refutation directly, including if the closed-loop system
uses *more* water than the fixed-schedule control (a negative reduction), which would falsify
even the qualitative direction of H3.

### 6. Claim inventory for Section IV (forward-looking checklist)

One claim per line, marked per the load-bearing-system-name test. This is a checklist for
drafting Section IV once E1–E4 data exists — every SELF-REPORT-shaped claim below must be
rewritten or cut before it enters the manuscript, not just at first draft.

1. "Lab-condition validation accuracy was 99.32% before the leakage audit and X% after a
   duplicate-aware regrouped split (E2)." — **FINDING** (a measured property of the split
   methodology, not of the system's name).
2. "Field accuracy on N hand-labelled images from this project's own ESP32-CAM was X%, a drop of
   Y points from lab accuracy, versus the ~68% cross-domain state of the art (E1)." —
   **FINDING**.
3. "Field-accuracy failures concentrated in classes {A, B, C}, associated with {lighting /
   occlusion / background} conditions absent from PlantVillage (E1, E7)." — **FINDING**.
4. "AgriSense achieves 99% accuracy." — **SELF-REPORT** (system name load-bearing) — must never
   appear in this form; always paired with the field number and the leakage-audit caveat per
   items 1–2 above.
5. "The base ESP32 fits at {cells} and fails at {cells} across the class-count × resolution ×
   precision grid (E3), matching/contradicting the H2 prediction pre-registered in §5 above." —
   **FINDING**.
6. "ESP32-S3 extends the feasible envelope to {specific cells} (E3)." — **FINDING** (chip
   capability, not system name).
7. "Closed-loop irrigation delivered X L against Y L for the fixed-schedule control over the
   trial period, a Z% reduction (flow-meter verified, E4), matching/contradicting the H3
   prediction pre-registered in §5 above." — **FINDING**.
8. "AgriSense's irrigation system saves water." — **SELF-REPORT** — must never appear
   unqualified; always the metered Z% figure with the control condition stated.
9. "Ablation (E5) shows {backbone alone: A1%; +augmentation: A2%; FP32: A3%; INT8: A4%} —
   quantifying each component's individual contribution." — **FINDING**.
10. "Results were statistically significant across ≥4 seeds (mean±std, paired t-test p<0.05
    against {baseline}) (E6)." — **FINDING**, provided the actual p-values are reported, not
    just "was significant."
11. "Grad-CAM on the field failure case in class {X} shows the model attending to {background
    clutter / off-axis leaf edge / lighting artifact} rather than the diagnostic lesion (E7)." —
    **FINDING**.
12. "Sensor-to-decision latency was X ms (median, IQR Y), uptime was Z% over the trial period,
    packet loss was W% (E8)." — **FINDING**.
13. "The system is reliable / production-ready." — **SELF-REPORT** (unqualified, no metric) —
    must never appear in this form; replaced by the specific E8 numbers in item 12.
14. Limitations passage (§V): "single-site, single-season trial; N field images is not
    exhaustive of real deployment lighting/background variation; disease-stage (Stage 2)
    classifier was never trained, so this paper characterizes species-only classification;
    dataset is entirely public with zero field-collected training images as of the completed
    run." — **FINDING** (an honest scope statement, not a claim about the system's merit).

---

## Manuscript Status (Sections IV, V, Abstract)

Timestamp: 2026-09-19T10:22:26Z. Written at the user's explicit request to stop
per-section approval gating and complete the manuscript in one pass. `paper/main.tex`
is now a complete end-to-end document (Abstract through Data Availability, 21
section/subsection headings, ~730 lines) and `paper/refs.bib` is unchanged at 12
verified entries (all 12 are cited in `main.tex`; none dangling, none unused).

### What's real vs. TBD in Section IV

**Real** (read directly from committed repo artifacts, nothing re-measured or estimated):
- Dataset source list, licences, and documented image counts (§IV.A) — from
  `ml/configs/sources.yaml` / `documents/DATASETS.md`, same figures already in this
  audit's §2, not re-derived.
- The completed run's split counts (43,444 train / 10,861 val, 38 classes) — from
  `metrics.json`.
- Full hyperparameter/augmentation pipeline (§IV.A, §IV.B) — from `args.yaml`, including
  the training hardware (Colab T4, confirmed from the notebook's `gpuType: "T4"` metadata).
- Table~\ref{tab:iv-summary}'s one real row (99.32% / 100.00%, unaudited) — from `metrics.json`.
- Figure "training curves" — newly generated by `paper/figures/plot_training_curves.py`
  from `ml/artifacts/results_and_accuracy/results.csv` (script committed, ran successfully,
  output at `paper/figures/training_curves.pdf`).
- Figure "confusion matrix (lab)" — the existing
  `ml/artifacts/results_and_accuracy/confusion_matrix_normalized.png`, copied to
  `paper/figures/confusion_matrix_lab.png` and cited; not regenerated (no raw predictions
  file exists in the repo to regenerate it from).
- One new flagged detail: the split code's documented 400-image-per-class cap does not
  reconcile with the observed 54,305-image total for 38 classes; stated as an open
  inconsistency in §IV.A rather than silently resolved or ignored.

**TBD** (every cell explicitly marked, no invented numbers), tied to the gap table's E1–E8 IDs:
- Field accuracy, leakage-audited lab accuracy, field confusion matrix — **E1, E2**.
- Full edge-feasibility grid (Table~\ref{tab:edge}, 24 chip×precision×class×resolution
  cells) — **E3**. Six cells are annotated with the pre-registered H2 prediction (not a
  measurement) so the eventual real result can be checked against it directly.
- Irrigation trial table (Table~\ref{tab:irrigation}) — **E4**. The reduction-vs-control
  cell is annotated with the pre-registered H3 prediction (22% ± 10%), not a measurement.
- Ablation, significance testing, Grad-CAM, reliability telemetry — **E5–E8**, named in
  §IV.C prose but not tabulated, since no partial data exists for any of them to structure
  a table around yet.
- §IV.D (Discussion) answers all three RQs as "cannot yet be answered," quotes the
  pre-registered H2/H3 predictions verbatim, and states the falsification criteria for
  each rather than asserting a result.

### Hostile self-review (§9 of the prompt)

1. **Is the central claim supported by an experiment, or only asserted?** Only asserted.
   The central claim is a characterization plan with two pre-registered predictions; none
   of RQ1–RQ3 has a completed experiment behind it yet. The manuscript says this explicitly
   in the Conclusion rather than implying otherwise.
2. **Is any number unsourced or carried over from an assumption?** No — every number in
   Sections I–IV traces to either a verified external citation or a specific repo artifact
   (`metrics.json`, `results.csv`, `args.yaml`, firmware constants). The one place an
   assumption could silently pass as fact — the 400-per-class cap vs. observed 54,305 total
   — is flagged as unreconciled instead.
3. **Could the headline accuracy be inflated by dataset leakage? What evidence rules that
   out?** Nothing rules it out. The manuscript states this directly (Table~\ref{tab:related}
   footnote b, §IV.A, §IV.D, Limitations): the 99.32% figure comes from a naive random split
   with no duplicate-awareness, and E2 (the leakage audit) has not run.
4. **Is there a field evaluation, or only a lab test set?** Only lab. Stated in the
   Related-Work table, §IV.A, and §IV.D without qualification.
5. **Would a reviewer call this "an engineering report, not research"? Which sentences
   invite that?** Checked the full draft for feature-description sentences load-bearing on
   the system's own name; found none surviving from the six-point audit's earlier pass, and
   no new ones introduced while drafting §IV/V (§IV/V describe pending measurements and
   limitations, not system features).
6. **Does the related-work table make the system look novel only because a column was
   omitted?** Re-confirmed after §IV was added: Table~\ref{tab:related} is unchanged from
   the six-point audit's version above and still shows this work behind Aqasizade et al. on
   every measured axis; no column was added or removed while drafting §IV/V.
7. **Is every figure and table cited in the body text?** Was NOT true on first pass —
   Figures "training curves" and "confusion matrix (lab)", and Equations 1–4 (cross-entropy
   loss, precision/recall/F1/accuracy) were labeled but never referenced by `\ref` in prose.
   Fixed inline: added explicit `Figure~\ref{fig:curves}`/`Figure~\ref{fig:cm-lab}` sentences
   and an `Equation~\ref{eq:ce}` reference in §IV.B, and an
   `Equations~\ref{eq:pr}--\ref{eq:acc}` reference in §IV.C. Verified by grep afterward:
   every label in the document now has at least one `\ref` elsewhere except `sec:conclusion`
   (a section label with no reason to be back-referenced).
8. **Are the limitations honest, or defensive?** Honest — the Limitations subsection states
   plainly that the deployed app may not even serve the trained model, that the LLM layer
   isn't yet adapter-based, that E1–E8 are all pending, and that "this paper's central claim
   is a plan and a pre-registration, not yet a finding." No hedging language softens these.
9. **Is each hypothesis answered explicitly, including any refuted?** None can be answered
   yet — §IV.D states this for H1/H2/H3 individually, gives each one's falsification
   criterion, and commits to reporting a refutation directly rather than retrofitting the
   prediction if the eventual data contradicts it. That "cannot yet be answered" is itself
   the honest, explicit answer this checklist asks for.

### Explicit non-submission-readiness statement

**This manuscript is not submission-ready.** It is a complete structural draft:
Sections I–III (Introduction, Related Work, Methodology) contain real, literature-verified,
code-verified content and are close to submission quality as prose. Section IV (Results) is
honestly mostly empty — one real table row, two real figures, and explicit TBD placeholders
everywhere else — because E1 through E8 have not been executed. No number anywhere in this
document was invented to fill that gap. The manuscript cannot advance toward submission
without running E1–E8 (`paper/audit.md` gap table) and rewriting §IV/§V/the Abstract against
real results at that point; this draft's job was to make that rewrite a fill-in-the-table
exercise against an already-fixed structure and two already-fixed predictions, not a
from-scratch rewrite.

### Not compiled

No LaTeX toolchain (`pdflatex`/`latexmk`) is available in this environment, so `main.tex`
has been checked structurally (every citation key resolves in `refs.bib`, every figure file
referenced exists on disk, every label has a `\ref`) but not compiled to PDF. Compile before
submission; `ieeeaccess.cls` should replace the substituted `IEEEtran` class at that point
(noted in a header comment in `main.tex`).
