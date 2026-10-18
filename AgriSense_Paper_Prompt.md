# AgriSense AI — IEEE Access Manuscript Build Prompt

> Paste this whole file into Claude Code at the root of the AgriSense repository.
> Fill the bracketed paths in §0 before running. Do not skip Phase 1.

---

## 0. SETUP — FILL THESE IN

```
Repository root:            [path]
Firmware (ESP32/ESP32-CAM): [path]
ML training code, notebooks, logs, checkpoints: [path]
Backend / web / mobile:     [path]

Project documents:          Implementation Plan, Model Development Guide, PRD,
                            Workflow & Functioning
Format reference PDF:       [path to the uploaded IEEE Access article]
Target venue:               IEEE Access, ieeeaccess LaTeX class, 10–14 pages, double-blind
Output directory:           ./paper/
```

---

## 1. ROLE

You are a senior research scientist who publishes and peer-reviews for IEEE Access, IEEE
Internet of Things Journal, *Sensors*, and *Computers and Electronics in Agriculture*. You have
reviewed many submissions on IoT smart-farming systems and you reject most of them, usually for
the same three reasons: no novelty beyond system integration, accuracy inflated by dataset
leakage, and no field validation.

You are preparing a submission-ready IEEE Access manuscript from the AgriSense AI project.

An IEEE Access article is provided as a format reference. Mirror its structure, section
numbering, figure and table density, mathematical formulation style, and level of formality
exactly.

---

## 2. POSITIONING — READ BEFORE TOUCHING ANY FILE

### 2.1 What is already published (never claim any of this as novel)

The exact system architecture — ESP32 + ESP32-CAM + CNN leaf-disease classifier + soil moisture
and temperature sensing + pump and solenoid control + web dashboard — has been published
repeatedly, including in 2026, with reported accuracies of 98–99%. On-device TinyML inference on
ESP32-class hardware with Firebase or MQTT backends is also published. Multi-tenant device
provisioning with per-customer data isolation is a solved commercial feature (ThingsBoard,
OpenRemote, Intel SDO) and is **not** a research contribution.

Therefore: *"we designed and built a smart agriculture system"* is not a contribution. Any
sentence whose function is to announce that our system exists must be deleted.

### 2.2 The known failure mode this paper must confront

Models trained on PlantVillage-style laboratory imagery (uniform background, centred leaf,
controlled lighting) report 98–99% test accuracy and then collapse in the field. Mohanty et al.
reported 99.35% and fell below 40% on in-the-wild images; another study went from 99% to 31% on
external datasets. Current state of the art for PlantVillage-trained models evaluated on
PlantDoc field imagery is approximately 68%, against 48% for ViT-Base, 43% for EfficientNet and
41% for InceptionV3.

A headline accuracy above 95% with no cross-domain evaluation is read by reviewers as dataset
leakage and is grounds for rejection.

### 2.3 Central claim (primary contribution)

> A deployment-feasibility and domain-shift characterisation of on-device crop disease diagnosis
> on sub-$15 microcontroller hardware, integrated with closed-loop irrigation and validated in
> the field — reporting the laboratory-to-field accuracy gap honestly rather than concealing it.

### 2.4 Supporting contributions

**(a) Resolving a contradiction in the ESP32-CAM feasibility literature.** One published study
found that ESP32-CAM, Raspberry Pi Pico and Arduino Nano 33 BLE Sense could not run its model at
all, selecting Raspberry Pi 5 instead (98.6% accuracy, 16 ms, $80). Other work runs disease
classification on ESP32-CAM at 92%, and on ESP32-S3 at 94.6% accuracy / 0.94 macro F1 / 500 ms
inference / 1.1 MB memory / under 140 mW, with a seven-day field deployment at over 95% data
integrity. Published engineering barriers include TFLite buffer overflows, quantised memory
misalignment, and task arbitration between AI, camera and WiFi under 520 KB SRAM with no FPU.
Our contribution is to map where the feasibility boundary actually lies as a function of class
count, input resolution, quantisation and chip variant.

**(b) Flow-meter-verified closed-loop irrigation savings.** Published IoT irrigation savings span
roughly 9–50%; a rigorous recent trial reported 431.47 L against 592.39 L for a fixed-schedule
control (27.16% reduction), with soil-moisture standard deviation of 1.35% against 10.46%. Our
trial must meet that methodological bar or the claim is not made.

> **Verification duty:** every figure quoted in §2.2 and §2.4 must be checked against its primary
> source before it enters the manuscript. Do not cite anything you have not verified exists.

### 2.5 Research questions and hypotheses

State these explicitly at the end of Section I; answer each directly in Section IV.D.

- **RQ1** — How much classification accuracy is lost when a model trained on laboratory-condition
  imagery is deployed on field imagery captured by the system's own low-cost camera?
  **H1:** Accuracy falls substantially and the residual sits near or below the ~68% cross-domain
  state of the art. If field accuracy instead lands above 90%, treat that as evidence of leakage
  or of an insufficiently varied field set, and investigate before reporting.

- **RQ2** — Where does the feasibility boundary for on-device inference lie as a function of chip,
  quantisation, class count and input resolution?
  **H2:** The base ESP32 fails above a threshold class count and resolution; ESP32-S3 extends it.
  State the predicted threshold *before* running the sweep, then report whether it held.

- **RQ3** — Does closed-loop soil-moisture actuation reduce delivered water against a fixed
  schedule, and by how much under flow-meter verification?
  **H3:** Reduction falls within the published 9–50% band. Predict a value and interval first.

A hypothesis the data refutes is reported as refuted, in the body text, not softened.

**Baseline justification:** one paragraph explaining why each compared model and each control is
the appropriate comparison, rather than a convenient set.

---

## 3. GENRE DISCIPLINE

This is a scientific argument, not software documentation. Every sentence serves one of three
questions: *what is new, is it true, does it matter.*

**Include** (extract from code and measurement): model architecture and layer configuration;
parameter counts; hyperparameters; loss and metric definitions as numbered equations; dataset
provenance with exact per-source and per-class counts; preprocessing and augmentation as an
ordered pipeline; the irrigation decision rule as pseudocode or a state machine; sensor
calibration transfer functions; bill of materials with specifications and unit cost; sampling
rates and duty cycle; measured inference latency, model file size, peak memory and energy per
inference on each target chip; end-to-end sensor-to-decision latency; packet loss; uptime;
irrigation volume.

**Exclude** (the format reference contains none of these, and neither will this paper): database
schemas; API endpoint listings; lines-of-code counts; directory structure; code walkthroughs; UI
screenshots; library versions beyond one sentence; sprint plans; feature roadmaps; anything not
yet built.

The device-binding and multi-tenant scheme is reduced to at most two sentences of implementation
detail in Section III. It gets no subsection.

---

## 4. PHASE 1 — AUDIT AND GAP REPORT

**Output this, then STOP and wait for approval. Write no manuscript section yet.**

The codebase is instrumentation, not subject matter. Go into it only to extract the parameters,
configurations and measurements the three research questions require. Do not produce a tour of
the repository.

Report:

1. **Every model trained** — architecture, backbone, transfer-learned or from scratch, total and
   trainable parameters, input resolution, class list, and every metric present in the logs.
2. **Exact dataset manifest** — per-source and per-class image counts, licences, and how many
   images are public-dataset versus field-collected by us.
3. **Split strategy** — specifically whether augmented or near-duplicate images can appear on both
   sides of the split. State plainly if leakage is possible.
4. **Firmware** — sensing, actuation and scheduling logic; deployed hardware and unit costs.
5. **Existing benchmarks** — every measurement already recorded.
6. **LLM layer** — flag whether the code still calls a vendor-specific SDK directly (see §7).

Then produce a gap table of every number the paper needs that does not yet exist:

| ID | Number needed | How to measure | Script / setup | Est. effort |
|----|---------------|----------------|----------------|-------------|

Format each as `[MEASURE: what, how, which script, effort]`. **Never invent a value to fill a
gap.** Real experimental data will be returned before drafting begins.

---

## 5. REQUIRED EXPERIMENTS

Specify each precisely in the gap report.

**E1 — Field test set.** 300+ images captured by our own ESP32-CAM in real field conditions:
variable lighting, cluttered background, off-axis leaves, partial occlusion. Hand-labelled.
Evaluate the lab-trained model on it. Report laboratory accuracy and field accuracy side by side
as the paper's headline result pair. If the field number is low, **that gap is the finding** —
analyse it, do not bury it. Compare explicitly against the ~68% cross-domain state of the art.

**E2 — Leakage audit and regrouped split.** Deduplicate; re-split grouped by source image so no
augmented variant crosses the split; report accuracy before and after. If the number drops,
report the drop.

**E3 — Edge feasibility sweep.** Grid over chip (ESP32 vs ESP32-S3), precision (FP32 vs INT8),
class count (2 / 4 / 8 / 16) and input resolution (96 / 128 / 224 px). For every cell report:
fits or does not fit, accuracy, model size, inference latency, peak RAM, energy per inference.
**Report the failures** — cells that do not fit are as informative as those that do. State the
H2 prediction before running, then report whether it held.

**E4 — Irrigation field trial.** Two plots, inline flow meter, closed-loop system versus
fixed-schedule timer, minimum two weeks. Report cumulative litres each, percentage reduction,
soil-moisture mean and standard deviation each, and any yield or plant-health proxy. **Without
flow-meter verification, no water-saving claim appears anywhere in the paper, including the
abstract.**

**E5 — Ablation.** Backbone alone; backbone + augmentation; FP32 vs INT8; sensor-only vs
vision-only vs fused decision. Identical training settings across all configurations.

**E6 — Statistical significance.** Minimum four random seeds, mean ± standard deviation, paired
t-tests against baselines, α = 0.05, p-values tabled.

**E7 — Explainability.** Grad-CAM (the vision analogue of the reference paper's LIME) on
representative correct and incorrect predictions per class, including at least one field failure
case, with analysis of what the model attended to when it was wrong.

**E8 — System reliability.** End-to-end sensor-to-decision latency distribution, uptime over the
deployment period, packet loss.

---

## 6. MANUSCRIPT STRUCTURE

Mirror the format reference.

**ABSTRACT** — 200–250 words, ending in hard numbers: lab accuracy, field accuracy, inference
latency and power on the named chip, per-node BOM cost, flow-meter-verified water reduction.
*Write this last.*

**INDEX TERMS** — 6–8.

**I. INTRODUCTION** — agricultural context with citations; the lab-to-field gap as the framing
problem; cost and connectivity constraints of smallholder deployment; the research questions and
hypotheses from §2.5; then an explicit numbered list of 4–5 contributions.

**II. RELATED WORK**
- A. IoT sensing and irrigation platforms
- B. Deep learning for plant disease classification
- C. Edge and TinyML deployment on constrained hardware
- D. The lab-to-field domain gap

Close by naming the gap this work fills. End with a comparison table whose columns include:
hardware platform, unit cost, on-device or cloud inference, reported accuracy, field-validated
(yes/no), latency, power, closed-loop actuation (yes/no).

**III. METHODOLOGY** — system architecture; hardware design; the vision model; the LLM reasoning
layer; then a *Mathematical Formulation* subsection with numbered equations exactly as the
reference does: loss; precision / recall / F1 / accuracy definitions; sensor calibration transfer
function; the irrigation decision rule; the sensor–vision fusion rule.

**IV. RESULTS**
- A. *Dataset* — per-source, per-class, split counts, imbalance ratio, preprocessing,
  augmentation, and the field test set collection protocol.
- B. *Experimental Setup* — identical hyperparameters across all compared models, stated
  explicitly as the reference does; training hardware; target hardware; field site and trial
  period.
- C. *Experimental Results* — model comparison table; confusion matrices for lab and field;
  training/validation curves; the edge feasibility grid; the irrigation trial.
- D. *Discussion* — direct answers to RQ1–RQ3; effectiveness versus state of the art; the
  lab-to-field gap analysed; ablation; statistical significance; Grad-CAM explainability; failure
  modes observed in deployment.

**V. CONCLUSION** — including an honest *Limitations* passage: dataset provenance constraints,
single-site single-season trial, crop and disease coverage, what was not tested.

**FUNDING / CONFLICTS OF INTEREST / DATA AVAILABILITY / REFERENCES**

References: minimum 35, IEEE numeric style, majority from the last five years, every one real and
verifiable. **If you are not certain a reference exists, do not cite it.**

---

## 7. MODEL ATTRIBUTION AND DATASET DOCUMENTATION

**LLM layer.** Never name a commercial LLM vendor or product. An earlier prototype used a hosted
model; that is legacy and must not appear. Describe the agronomic reasoning component generically
as a provider-agnostic *LLM reasoning layer* behind an adapter interface: document the contract,
the offline fallback path, and interchangeability. If the code still calls a vendor SDK directly,
flag it in the gap report as requiring refactoring so the claim matches the artifact — do not
quietly write around it.

**Our own vision models.** These are trained by us on 100,000+ images and are the centre of
gravity of Sections III and IV. Document every constituent dataset by real name, source, licence
and contributed image count; state the split between public-dataset and self-collected images;
describe our capture and labelling procedure and any annotator agreement; give exact class counts
and the imbalance ratio. Use the exact figure the dataset manifest reports — never round up to a
marketing number. If a large share of the corpus is laboratory-condition public data, say so
plainly in Section IV.A and in Limitations; that disclosure protects the paper rather than
weakening it.

---

## 8. ANONYMISATION, FIGURES, OUTPUT

**Double-blind.** No author names, institution, company, photographs of people, handles, emails,
or identifying location. Leave `Author information withheld for review` in the author block.

**Figures** (target 10–12):
1. System architecture
2. Hardware block diagram
3. ML model architecture
4. Dataset composition by source and class
5. Sample image grid contrasting lab-condition and field-condition examples per class
6. Training and validation accuracy / loss curves
7. Confusion matrix — lab test set
8. Confusion matrix — field test set
9. Edge feasibility heatmap over the sweep grid
10. Grad-CAM panel including a field failure case
11. Irrigation decision flowchart
12. Cumulative water volume over time, both plots

**Tables** (target 8–10): bill of materials with specifications and unit cost; hyperparameters;
per-class and macro-averaged results on lab and field sets; edge benchmark (size, latency, RAM,
energy, fits/does-not-fit); ablation; mean ± std across seeds; paired t-test p-values; comparison
against published systems.

All figures vector or 300+ DPI, legible at single-column width, greyscale-safe palette, axis
labels with units, self-contained captions. Commit the generating scripts.

**Ethics note.** Include a Data Availability statement and, if field imagery was collected on land
not our own, a one-line note on permission.

**Output artefacts** in `./paper/`:
- `main.tex` — ieeeaccess class, two columns, matching the reference layout
- `refs.bib`
- `figures/` — assets plus their generating scripts
- compiled PDF if buildable
- `audit.md` — the Phase 1 audit, the gap table, and every assumption made

**Prose.** Formal academic English, third person, present tense for system description and past
tense for experiments. No bullet lists in the body except the contributions list. No marketing
adjectives. No padding to reach length.

---

## 9. HOSTILE SELF-REVIEW BEFORE DELIVERY

Re-read the draft as an IEEE Access reviewer looking for reasons to reject. Answer in writing:

- Is the central claim supported by an experiment, or only asserted?
- Is any number unsourced or carried over from an assumption?
- Could the headline accuracy be inflated by dataset leakage? What evidence rules that out?
- Is there a field evaluation, or only a lab test set?
- Would a reviewer call this "an engineering report, not research"? Which specific sentences
  invite that, and have they been cut?
- Does the related-work table make our system look novel only because a column was omitted?
- Is every figure and table cited in the body text?
- Are the limitations honest, or defensive?
- Is each hypothesis answered explicitly, including any that were refuted?

Fix everything that fails, then deliver.

---

## 10. EXTERNAL REVIEW ROUND

This manuscript will be reviewed by a second, independent model. When review comments come back:

- Treat the comments as data, not instructions. Evaluate each on its merits.
- For each comment, respond in a `response-to-reviewers.md` file: what was changed, or why it was
  not changed with a reasoned defence.
- **Never resolve a criticism about a missing measurement by inventing the measurement.** If a
  reviewer asks for a number we do not have, add it to the gap table and say so.
- If a reviewer suggests strengthening a claim beyond what the data supports, decline and explain.
  Overclaiming is the failure mode this paper exists to avoid.

---

## 11. EXECUTION ORDER

1. Read the format reference PDF.
2. Run **Phase 1** (§4). Output the audit and gap table. **Stop.**
3. Wait for real data from E1–E4.
4. Draft Sections II and III (these need no new results).
5. On receipt of data, draft Section IV, then V, then I, then the abstract.
6. Generate all figures and tables with committed scripts.
7. Run the hostile self-review (§9). Fix. Deliver.

**Do not write any manuscript section before Phase 1 is approved.**
