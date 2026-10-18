"""Implementation paper (IEEE Access format) -> paper/out/AgriSense_Implementation_Paper.docx
Every number is traceable: firmware constants (AgriSense_ESP32.ino), backend
constants (backend/main.py), ML artifacts (ml/artifacts/results_and_accuracy/),
ONNX benchmark (bench.py run on 2026-10-15) and sim_results.json.
"""
import json
import os

from ieee import Paper, PAPER, ROOT

OUT = os.path.join(PAPER, "out")
os.makedirs(OUT, exist_ok=True)
PNG = os.path.join(PAPER, "png")
ART = os.path.join(ROOT, "ml", "artifacts", "results_and_accuracy")
SIM = json.load(open(os.path.join(os.path.dirname(__file__), "sim_results.json")))
S1, S2 = SIM["Single threshold (30 %)"], SIM["AgriSense hysteresis (30/70 %)"]

p = Paper("T. Jhariya et al.: AgriSense AI — Edge-Authoritative IoT Irrigation and Crop Disease Diagnosis")

p.front(
    title="AgriSense AI: Design and Implementation of an Edge-Authoritative IoT Platform "
          "for Fail-Safe Closed-Loop Irrigation and Leakage-Aware Crop Disease Diagnosis",
    authors="**TISHA JHARIYA**^{1}, **AKIKO GAJBHIYE**^{1}, **ANSH MESHRAM**^{1}, **AGYA CHOURASIA**^{1}, AND **[GUIDE NAME]**^{1}",
    affils=["^{1}Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, Maharashtra 441501, India"],
    corresponding="[Guide Name] ([email address])",
    received="Received [date], accepted [date], date of publication [date], date of current version [date].  "
             "Digital Object Identifier 10.1109/ACCESS.2026.DOI",
    abstract=(
        "Smart-agriculture systems that combine microcontroller sensing, automated irrigation and "
        "image-based disease diagnosis are widely reported, yet three engineering weaknesses recur: "
        "the irrigation decision usually lives in the cloud and stops when connectivity fails, a "
        "disconnected soil probe is often indistinguishable from saturated or bone-dry soil, and "
        "headline disease-classification accuracies are measured on laboratory imagery with splits "
        "that permit near-duplicate leakage. This paper presents the design, implementation and "
        "verification of AgriSense AI, an open three-tier platform that addresses each weakness "
        "explicitly. An ESP32 sensor node evaluates an ordered, seven-rule irrigation policy on the "
        "device itself, so that safety interlocks (failed probe, rain, saturated soil) dominate any "
        "operator or cloud command, with a 30/70 % hysteresis band, a 15 min run cap, a 30 min "
        "cooldown and an 11-case boot-time self-test. Telemetry and commands flow directly between "
        "the device and a managed PostgreSQL store with row-level security, so monitoring and "
        "manual control survive a backend outage. A demand-driven ESP32-CAM relay streams the field "
        "without port forwarding. Diagnosis is served by a two-stage ONNX pipeline built on a "
        "leakage-aware data path (SHA-256 and perceptual-hash de-duplication, duplicate-group-aware "
        "stratified splits, a field dataset held out for evaluation only), with a schema-constrained "
        "vision-language fallback and a telemetry-grounded advisory assistant. A YOLO11n-cls "
        "baseline with 1.57 M parameters reaches 99.32 % top-1 and 100 % top-5 accuracy on 10,861 "
        "PlantVillage validation images across 38 classes and runs in 6.07 ms per image on one CPU "
        "thread. We report that figure as a laboratory upper bound, not a field estimate, show "
        "analytically why the exported model cannot run on the base ESP32 as-is, and list the field "
        "measurements that remain open."),
    keywords="Internet of Things, precision agriculture, smart irrigation, fail-safe control, ESP32, "
             "plant disease classification, YOLO11, ONNX, data leakage, edge computing, large language models.",
)

# ------------------------------------------------------------------ I
p.h1("Introduction")
p.para("Agriculture is under simultaneous pressure from water scarcity and crop disease. Irrigated "
       "agriculture accounts for roughly 70 % of global freshwater withdrawals [@fao2024aquastat], while "
       "pathogens and pests are estimated to cost 10–28 % of wheat, 25–41 % of rice and 20–41 % of maize "
       "yield worldwide, with the heaviest losses in food-deficit regions [@savary2019burden,strange2005plant]. "
       "For smallholders both problems share a cause: decisions are made by eye and by habit, on fixed "
       "schedules and late visual inspection, because sensing and expert diagnosis are expensive.")
p.para("The Internet of Things (IoT) and deep learning have each been proposed as the remedy. Wireless "
       "soil-moisture sensing with automated actuation was demonstrated more than a decade ago "
       "[@gutierrez2014automated] and has since been extended with machine-learning scheduling and "
       "platform-scale water management [@goap2018iot,kamienski2019swamp,garcia2020iot]. Convolutional "
       "networks trained on leaf images report accuracies above 99 % [@mohanty2016deep,ferentinos2018deep,"
       "too2019comparative]. Systems that combine the two on low-cost microcontrollers are now common "
       "[@samanta2024leafsense,nyakuri2025aiiot,aqasizade2026tinymlops].")
p.para("Building one more such system is not, by itself, a contribution. What we found missing when "
       "reviewing these systems was attention to how they *fail*. Three failure modes motivated this work:")
p.bullets([
    "**Cloud-dependent control.** When the pump decision runs on a server, a Wi-Fi drop or backend crash "
    "leaves the field either unwatered or, worse, with a pump latched on.",
    "**Fail-unsafe sensing.** A disconnected analogue soil probe floats to an ADC value near zero. Depending "
    "on calibration direction this reads as saturated or as completely dry soil; in the latter case a naïve "
    "threshold rule runs the pump indefinitely.",
    "**Unaudited accuracy.** Laboratory leaf datasets contain near-duplicate photographs of the same leaf; "
    "random splits place them on both sides of the partition, and the resulting accuracy does not transfer "
    "to field photographs, where published models fall to roughly 31–68 % [@mohanty2016deep,salman2025plantdisease,kapoor2023leakage].",
], numbered=True)
p.para("This paper describes AgriSense AI, a complete, open implementation designed around these three "
       "failure modes, and reports what has and has not yet been measured. Its contributions are:")
p.bullets([
    "An **edge-authoritative irrigation controller** whose ordered rule set places sensor interlocks above "
    "operator and cloud commands, with hysteresis, hard run-time limits and a boot-time self-test "
    "(Section V); and a simulation showing its effect on actuator cycling under sensor noise (Section X-D).",
    "A **cloud-decoupled data path** in which the device writes telemetry and reads commands directly from "
    "a row-level-secured database, so that the application backend is required only for value-added "
    "services and every optional service degrades independently (Sections III and VI).",
    "A **leakage-aware diagnosis pipeline**: exact and perceptual-hash de-duplication, duplicate-group-aware "
    "stratified splitting, a field dataset quarantined for evaluation, and a two-stage species-then-condition "
    "classifier exported to ONNX with confidence gating (Section VII).",
    "A **measured baseline and a static edge-feasibility bound**: training curves, model complexity, CPU "
    "latency, and a closed-form memory analysis of the exported model against ESP32 SRAM (Section X).",
    "An **explicit limitations statement** separating implemented, measured and pending items (Section XI).",
], numbered=True)
p.para("Section II reviews related work. Sections III–IX describe the architecture, hardware, firmware, "
       "backend, diagnosis pipeline, advisory layer and client applications. Section X reports results, "
       "Section XI discusses limitations, and Section XII concludes.")

# ------------------------------------------------------------------ II
p.h1("Related Work")
p.h2("IoT-Based Irrigation")
p.para("Gutiérrez et al. [@gutierrez2014automated] combined a wireless sensor network with a GPRS gateway "
       "and threshold-based actuation. Goap et al. [@goap2018iot] added weather forecasts and machine-learning "
       "prediction of soil moisture to schedule irrigation, and the SWAMP project [@kamienski2019swamp] "
       "generalised this to a platform for precision irrigation. Reviews [@garcia2020iot,vallejo2023smart] "
       "report water savings spanning roughly 9–50 %, a range wide enough that unmetered claims are "
       "uninformative; a recent metered trial reports a 27.16 % reduction (431.47 L vs. 592.39 L) against a "
       "fixed schedule [@usman2026aiirrigation]. Few of these works specify behaviour under sensor failure or "
       "connectivity loss, which is the focus of our controller design.")
p.h2("Deep Learning for Plant Disease Diagnosis")
p.para("Following Mohanty et al. [@mohanty2016deep], transfer learning from ImageNet-pretrained backbones "
       "[@deng2009imagenet,he2016resnet] became the standard recipe on the PlantVillage corpus "
       "[@hughes2015plantvillage], with accuracies above 99 % [@ferentinos2018deep,too2019comparative,brahimi2017deep]. "
       "The same authors observed a fall to about 31 % on images from outside the corpus, and PlantDoc "
       "[@singh2020plantdoc] was assembled to provide a field-condition benchmark; the current cross-domain "
       "reference point for PlantVillage-trained models on such data is about 68 % [@salman2025plantdisease]. "
       "Barbedo attributes the gap to background clutter, capture variability and lesion co-occurrence absent "
       "from laboratory images [@barbedo2018factors]. We adopt the YOLO11 classification family "
       "[@ultralytics2024yolo11] for its maintained export path to ONNX.")
p.h2("Edge and TinyML Deployment")
p.para("Microcontroller inference is bound by on-chip SRAM for activations rather than flash for weights "
       "[@lin2020mcunet,lin2021mcunetv2], and relies on integer quantization [@jacob2018quantization] executed "
       "by embedded runtimes such as TensorFlow Lite Micro [@david2021tflm]. Published ESP32-class results "
       "disagree: Nyakuri et al. found ESP32-CAM unable to host their model and moved to a Raspberry Pi 5 "
       "[@nyakuri2025aiiot], whereas Samanta et al. report 92 % on ESP32-CAM [@samanta2024leafsense] and "
       "Aqasizade et al. 94.6 % on ESP32-S3 with a seven-day field deployment [@aqasizade2026tinymlops].")
p.h2("Language Models in Agriculture")
p.para("Large language models (LLMs) have been evaluated as extension agents [@tzachor2023llm] and on "
       "agronomy examinations [@silva2023gpt4agro]; retrieval augmentation and fine-tuning both improve "
       "domain answers [@balaguer2024rag,lewis2020rag]. A consistent caution is that ungrounded answers can "
       "be confidently wrong, which motivates grounding the model in measured farm state, as done here.")

p.table(["System", "Control locus", "Fail-safe probe", "Disease model", "Field-validated", "LLM advisor"],
        [["Gutiérrez [@gutierrez2014automated]", "Gateway", "n/s", "No", "Yes (irrigation)", "No"],
         ["Goap [@goap2018iot]", "Cloud/ML", "n/s", "No", "Yes (irrigation)", "No"],
         ["Samanta [@samanta2024leafsense]", "—", "—", "ESP32-CAM, 92 %", "No", "No"],
         ["Nyakuri [@nyakuri2025aiiot]", "—", "—", "RPi 5, 98.6 %", "n/s", "No"],
         ["Aqasizade [@aqasizade2026tinymlops]", "—", "—", "ESP32-S3, 94.6 %", "Yes (7 days)", "No"],
         ["**AgriSense (this work)**", "**On-node**", "**Yes**", "Server ONNX, 99.32 % lab", "**Pending**", "**Yes**"]],
        "Positioning against representative systems. n/s = not stated in the cited source; "
        "— = not applicable. AgriSense is behind on field validation.",
        widths=[1.5, 0.9, 0.8, 1.3, 1.0, 0.8], wide=True)

# ------------------------------------------------------------------ III
p.h1("System Architecture")
p.para("AgriSense is organised in three tiers (Fig. 1). The **field tier** contains two physically "
       "separate boards: an ESP32 DevKit V1 sensor/actuator node and an AI-Thinker ESP32-CAM imaging node. "
       "The **cloud tier** consists of a managed PostgreSQL database with authentication, Realtime "
       "subscriptions and row-level security (Supabase [@supabase2026]), and a Python 3.11 FastAPI backend "
       "packaged with Docker. The **client tier** comprises a web dashboard and a cross-platform mobile "
       "application.")
p.figure(os.path.join(PNG, "fig_architecture.png"),
         "Three-tier architecture of AgriSense AI. Periods and rate limits are the deployed firmware "
         "constants. The irrigation decision executes on the sensor node and remains authoritative when the "
         "cloud tier is unreachable.", wide=True)
p.para("Four design principles shaped the implementation:")
p.bullets([
    "**P1 – Edge authority.** The device makes the final pump decision; cloud components may only *request* "
    "actuation.",
    "**P2 – Fail-safe defaults.** Any missing, stale or implausible input resolves to *pump off*.",
    "**P3 – Least privilege.** Clients never hold third-party API keys or the database service key; every "
    "table is scoped to its owner by row-level security.",
    "**P4 – Graceful degradation.** Each optional service (diagnosis, advisor, camera) returns HTTP 503 when "
    "its credential is absent, without affecting the others.",
])
p.para("The decisive architectural choice is that the sensor node talks **directly** to the database over "
       "HTTPS rather than through the backend. The backend is required only for scheduled automation, "
       "diagnosis, the advisor and the camera relay; telemetry, manual pump control and device pairing keep "
       "working with it stopped. Table 2 lists the data model.")
p.table(["Table", "Purpose"],
        [["devices", "Device ownership; trigger enforces ≤ 4 devices per account"],
         ["device_registry", "Factory serial and pairing secret"],
         ["device_status", "Heartbeat (last_seen_at), per-sensor health flags"],
         ["device_config", "Automation mode, thresholds, pump state"],
         ["telemetry_data", "Time series: temperature, humidity, soil, rain"],
         ["device_commands", "Command queue (PUMP_ON / PUMP_OFF), executed flag"],
         ["timers", "Irrigation windows: start, duration, active days"]],
        "Database schema. All tables are protected by row-level security policies.",
        widths=[1.1, 2.35], first_bold=True)

# ------------------------------------------------------------------ IV
p.h1("Hardware Implementation")
p.para("Fig. 2 and Table 3 give the sensing and actuation topology. Air temperature and relative humidity "
       "are read from a DHT11; soil moisture from a capacitive probe on a 12-bit ADC1 channel; rain from an "
       "active-low digital module; and a single relay with a normally-open contact switches the pump.")
p.figure(os.path.join(PNG, "fig_hardware.png"),
         "Sensor node wiring and pin assignment. Root-zone temperature is derived, not measured.")
p.table(["Component", "GPIO", "Notes"],
        [["DHT11 (air T, RH)", "4", "10 kΩ pull-up; 3 reads, 2.2 s apart"],
         ["Capacitive soil probe", "34", "ADC1, input-only; dry 4095, wet 30"],
         ["Rain module (DO)", "33", "Active-LOW; cannot be health-checked"],
         ["Relay (pump)", "16", "Active-LOW, NO contact"],
         ["ESP32-CAM (OV2640)", "—", "Separate board; VGA/QVGA JPEG"]],
        "Sensor node bill of materials and pin map (firmware v3.1.0).", widths=[1.25, 0.45, 1.75])
p.h2("Why Two Boards")
p.para("On the AI-Thinker ESP32-CAM the OV2640 interface and PSRAM occupy GPIO 34 (the soil ADC), GPIO 4 "
       "(flash LED) and GPIO 16 (PSRAM chip-select), leaving no ADC1 pin free for the soil probe. Imaging is "
       "therefore placed on a second board that shares only the Wi-Fi network. This also isolates the "
       "safety-critical control loop from camera memory pressure.")
p.h2("Sensor Conditioning")
p.para("The averaged raw ADC value *r* is mapped to a moisture percentage by a two-point calibration "
       "measured on the deployed probe, with dry-air reading *D* = 4095 and saturated-soil reading *W* = 30:")
p.eq(r"m(r)=\frac{D-r}{D-W}\times 100,\qquad r\geq r_{\mathrm{disc}}=10")
p.para("Readings below *r*_{disc} = 10 are rejected as a disconnected probe instead of being converted, "
       "because an unplugged input floats to approximately zero, which (1) would otherwise map to above "
       "100 % and be indistinguishable from flooded soil. The DHT11 is retried up to three times per tick, "
       "2.2 s apart (beyond the library's 2 s cache window); on failure the node reports the last good "
       "reading rather than zeros. Soil temperature is a derived quantity (air temperature – 2.5 °C) and is "
       "labelled as such. The rain module cannot be health-checked: a floating input reads as “no rain”, "
       "which is fail-safe for watering only because rain merely *inhibits* the pump.")

# ------------------------------------------------------------------ V
p.h1("Firmware and On-Node Control")
p.h2("Task Schedule")
p.para("The firmware (Arduino C++, version 3.1.0) runs a cooperative loop with four periodic tasks: "
       "telemetry upload every 10 s, heartbeat upsert to *device_status* every 10 s, command polling every "
       "5 s, and a pairing check every 30 s. The heartbeat carries per-sensor health flags so the backend "
       "can gate automation per sensor.")
p.h2("Ordered Irrigation Policy")
p.para("Let *m* be calibrated moisture, *s* ∈ {0,1} probe health, *ρ* ∈ {0,1} rain, *u* ∈ {–1,0,+1} the "
       "pending manual command and *p* the current pump state. Algorithm 1 is evaluated every 10 s; the "
       "first matching rule wins, so the three sensor interlocks always dominate operator intent: a manual "
       "*run* cannot water through rain, wet soil or a failed probe.")
p.algorithm("Algorithm 1: pumpShouldRun(m, s, ρ, p, u)", [
    "if s = 0     then return OFF  // failed probe",
    "if ρ = 1     then return OFF  // raining",
    "if m ≥ θ_wet then return OFF  // wet (70 %)",
    "if u = −1    then return OFF  // force stop",
    "if u = +1    then return ON   // manual run",
    "if m < θ_dry then return ON   // dry (30 %)",
    "return p                      // band: hold",
])
p.para("The last rule implements the hysteresis band of Fig. 3, which prevents relay chatter when moisture "
       "hovers near a single threshold. Two hard limits bound delivery regardless of sensor state,")
p.eq(r"\tau_{\mathrm{run}}\leq 15\ \mathrm{min},\qquad \tau_{\mathrm{cool}}\geq 30\ \mathrm{min},")
p.para("so a mis-calibrated probe cannot cycle the pump indefinitely. A manual command expires after 10 min "
       "and control returns to the automatic rules.")
p.figure(os.path.join(PNG, "fig_hysteresis.png"),
         "Hysteresis characteristic: between θ_dry = 30 % and θ_wet = 70 % the pump keeps its previous state.")
p.h2("Boot-Time Self-Test")
p.para("Inverted comparisons or swapped thresholds would produce a pump that never stops, a fault that is "
       "costly to find in the field. The firmware therefore asserts Algorithm 1 against 11 hand-written cases "
       "at every boot with no hardware attached (Table 4). We additionally ported the function line-by-line to "
       "Python and verified the same 11 cases before using it in the simulation of Section X-D.")
p.table(["#", "m (%)", "s", "ρ", "p", "u", "Expected", "Scenario"],
        [["1", "10", "1", "0", "0", "0", "ON", "dry + idle → start"],
         ["2", "10", "1", "1", "0", "0", "OFF", "dry but raining"],
         ["3", "10", "0", "0", "1", "0", "OFF", "probe unplugged"],
         ["4", "45", "1", "0", "1", "0", "ON", "in band, running → hold"],
         ["5", "45", "1", "0", "0", "0", "OFF", "in band, idle → hold"],
         ["6", "80", "1", "0", "1", "0", "OFF", "watered → stop"],
         ["7", "10", "1", "0", "0", "+1", "ON", "manual ON, dry"],
         ["8", "10", "1", "1", "1", "+1", "OFF", "rain beats manual ON"],
         ["9", "90", "1", "0", "1", "+1", "OFF", "wet beats manual ON"],
         ["10", "10", "1", "0", "1", "−1", "OFF", "manual OFF on dry soil"],
         ["11", "10", "0", "0", "1", "+1", "OFF", "unplugged beats manual ON"]],
        "Firmware boot self-test cases for Algorithm 1 (all 11 pass).",
        widths=[0.25, 0.4, 0.25, 0.25, 0.25, 0.3, 0.55, 1.6], size=7)

# ------------------------------------------------------------------ VI
p.h1("Cloud Backend")
p.h2("Supervisory Automation Engine")
p.para("The backend runs an asynchronous loop every 10 s over all devices whose automation mode is not "
       "NONE. The engine is stateless: mode, thresholds and pump state are re-read from *device_config* on "
       "each tick, so a restart loses nothing. Before evaluating a mode, a safety gate blocks automation and "
       "queues PUMP_OFF if the device is offline or (in moisture mode) the data are stale or the soil probe "
       "reports a fault, with")
p.eq(r"\mathrm{offline}\Leftrightarrow t-t_{\mathrm{seen}}>30\,\mathrm{s},\qquad \mathrm{stale}\Leftrightarrow t-t_{\mathrm{telemetry}}>60\,\mathrm{s}.")
p.para("The gate is per mode: timer mode reads no sensor, so a failed DHT11 must not disable it. Two modes "
       "are offered. **Moisture mode** starts the pump when soil is below a user start threshold and it is "
       "not raining, stops it at a stop threshold, and enforces a configurable maximum runtime (default "
       "20 min). **Timer mode** runs the pump within user-defined windows (start time, duration, weekdays), "
       "pausing during rain; it is also the fixed-schedule control arm for a future metered trial. Commands "
       "are only *queued* in *device_commands*; the firmware treats them as manual requests subject to "
       "Algorithm 1, so the cloud can never override the on-node interlocks.")
p.h2("API Surface and Security")
p.table(["Endpoint", "Function", "Auth"],
        [["POST /api/command", "Manual pump ON/OFF, force stop", "JWT"],
         ["POST /api/automation/mode", "NONE / MOISTURE / TIMER", "JWT"],
         ["/api/timers (CRUD)", "Irrigation schedules", "JWT"],
         ["POST /api/plant/predict", "Leaf diagnosis", "JWT"],
         ["POST /api/advisor/ask", "Grounded advisory chat", "JWT"],
         ["POST /api/camera/{id}/frame", "Upload JPEG frame", "X-Cam-Key"],
         ["GET /api/camera/{id}/wanted", "Is a viewer attached?", "X-Cam-Key"],
         ["POST /api/camera/{id}/token", "Short-lived viewer token", "JWT"],
         ["GET /api/camera/stream", "MJPEG stream", "Token"]],
        "Backend REST endpoints.", widths=[1.45, 1.4, 0.6], size=7)
p.para("User tokens are validated on every request, and a malformed token yields HTTP 401 rather than a "
       "server error. Row-level security restricts every table to its owner, and a database trigger limits "
       "each account to four devices. A device is paired with its factory serial and secret and only while it "
       "is online (fresh heartbeat), which prevents claiming a device from a leaked label alone. API keys for "
       "the vision model, the LLM and the model server exist only in the backend environment.")
p.h2("Demand-Driven Camera Relay")
p.para("The ESP32-CAM polls */wanted* every 3 s while idle. When a client requests a viewer token, the "
       "camera begins posting JPEG frames, capped at 4 frames/s, at VGA with quality 12 when PSRAM is present "
       "or QVGA with quality 15 otherwise; the backend re-emits them to viewers as an MJPEG stream. Because "
       "both camera and viewer make outbound requests to the backend, the feed works across NAT from any "
       "network without port forwarding, and the camera consumes upstream bandwidth only while watched.")

# ------------------------------------------------------------------ VII
p.h1("Plant Disease Diagnosis Pipeline")
p.para("The diagnosis subsystem (Fig. 4) is a Python package with seven unit-tested stages: acquisition, "
       "structural inspection, cleaning, taxonomy unification, manifest building, splitting and training, "
       "followed by ONNX export, verification and a serving runtime.")
p.figure(os.path.join(PNG, "fig_model.png"),
         "Transfer-learning and export pipeline. Values are those of the completed baseline run.", wide=True)
p.h2("Datasets")
p.table(["Dataset", "Images", "Classes", "Imagery", "Role"],
        [["PlantVillage [@hughes2015plantvillage]", "54,305", "38", "Lab", "Train (baseline)"],
         ["PlantWild [@plantwild2024]", "30,030", "—", "Web/field", "Train (planned)"],
         ["Cassava [@mwebaze2019icassava]", "21,367", "5", "Field", "Train (planned)"],
         ["Rice leaf [@riceleaf2023]", "5,932", "4", "Field", "Train (planned)"],
         ["PlantDoc [@singh2020plantdoc]", "2,598", "27", "Field", "**Evaluation only**"]],
        "Datasets configured in the pipeline (image counts are those of the configured mirrors). PlantDoc is never merged into training.",
        widths=[1.35, 0.55, 0.5, 0.55, 0.85], size=7)
p.h2("Cleaning and De-Duplication")
p.para("Each image is decoded, size-checked and fingerprinted with SHA-256 and a 64-bit perceptual hash "
       "(pHash) [@zauner2010phash]. Exact duplicates are removed by SHA-256. Near-duplicates are grouped when "
       "the Hamming distance between their hashes satisfies")
p.eq(r"d_H(h_i,h_j)=\sum_{k=1}^{64}\left[h_i^{(k)}\neq h_j^{(k)}\right]\leq\tau,\qquad \tau=5,")
p.para("with candidates bucketed by a 4-hex-digit hash prefix to keep comparisons tractable at ~10^{5} "
       "images. Any training image within τ of a PlantDoc image is rejected, so the held-out field set "
       "cannot leak into training through re-encoded copies.")
p.h2("Splitting")
p.para("Splits are stratified per class with target ratios 80/10/10 (tolerance ±2 %) and are "
       "**duplicate-group aware**: all members of a near-duplicate group are assigned to the same partition, "
       "which removes the leakage path described in [@kapoor2023leakage].")
p.h2("Two-Stage Model")
p.para("Stage 1 classifies species (YOLO11s-cls); Stage 2 uses one smaller YOLO11n-cls per species to "
       "classify the condition. The model is trained by minimising categorical cross-entropy")
p.eq(r"\mathcal{L}=-\frac{1}{N}\sum_{n=1}^{N}\sum_{i=1}^{C}y_{n,i}\log\hat{y}_{n,i}")
p.para("with a cosine learning-rate schedule [@loshchilov2017sgdr], mixed precision and early stopping "
       "(patience 10 for Stage 1, 8 for Stage 2). Augmentation uses HSV jitter (h 0.015, s 0.4, v 0.4), "
       "rotation up to 10°, horizontal flip with probability 0.5 and random erasing 0.2 "
       "[@zhong2020randomerasing]; vertical flips are disabled because leaves have a natural orientation. At "
       "inference the joint confidence and a low-confidence flag are")
p.eq(r"c=c_s\,c_c,\qquad \mathrm{low}\Leftrightarrow c_s<0.5\ \vee\ c_c<0.5,")
p.para("where *c*_{s} and *c*_{c} are the species and condition soft-max confidences; thresholds are read "
       "from a versioned *registry.json*, never hard-coded in the server.")
p.h2("Export and Serving")
p.para("Models are exported to ONNX (opset 12), verified numerically against PyTorch, and served by a "
       "separate FastAPI service with ONNX Runtime [@onnxruntime2026] behind an API key. The backend selects "
       "the inference source at request time: the trained model service when it is configured, otherwise a "
       "hosted vision-language model (Gemini) constrained by a JSON response schema (fields: is_plant, species, "
       "condition, both confidences, healthy, severity ∈ {none, mild, moderate, severe}, affected area %, "
       "symptoms, cause, treatment, prevention) at temperature 0.2. Swapping in the trained model is an "
       "environment change, not a code change.")

# ------------------------------------------------------------------ VIII
p.h1("Telemetry-Grounded Farm Advisor")
p.para("The advisor endpoint fetches the device's most recent telemetry and places it in the LLM system "
       "instruction, marking it *STALE* when older than the freshness window, so answers refer to measured "
       "field conditions rather than generic advice. The plant-scan screen can hand a diagnosis directly into "
       "the chat. In the current implementation both the advisor and the vision fallback call one hosted "
       "provider directly; a provider-neutral adapter and an offline fallback are future work.")

# ------------------------------------------------------------------ IX
p.h1("Client Applications")
p.para("The web dashboard is plain HTML/CSS/JavaScript served by the backend and subscribes to database "
       "changes through Realtime. The mobile application is written in TypeScript with React Native, Expo 54 "
       "and expo-router, with four tabs: Dashboard (live tiles, pump control, automation mode, timers, force "
       "stop), Plant Scan, Advisor and Account (Fig. 5).")
p.figure(os.path.join(PNG, "app_montage.png"),
         "Mobile application: irrigation controls (left), plant scan (centre) and farm advisor (right).")

# ------------------------------------------------------------------ X
p.h1("Experimental Results")
p.h2("Training Setup")
p.para("The baseline is a single-stage YOLO11n-cls classifier over the 38 PlantVillage species–condition "
       "classes (14 crops), initialised from pretrained weights and fine-tuned for 5 epochs at 224×224, "
       "batch 64, seed 42, deterministic mode, on a Google Colab T4 GPU. The split is 43,444 training and "
       "10,861 validation images. Total training time was 1,300 s (21.7 min).")
p.table(["Epoch", "Train loss", "Val loss", "Top-1 (%)", "Top-5 (%)", "Time (s)"],
        [["1", "1.689", "0.210", "94.75", "99.82", "265.9"],
         ["2", "0.198", "0.071", "97.87", "99.97", "524.7"],
         ["3", "0.109", "0.038", "98.91", "100.00", "780.5"],
         ["4", "0.075", "0.028", "99.21", "100.00", "1040.4"],
         ["5", "0.052", "0.024", "**99.32**", "**100.00**", "1300.0"]],
        "Per-epoch training log (results.csv). Time is cumulative.",
        widths=[0.45, 0.6, 0.55, 0.6, 0.6, 0.65])
p.figure(os.path.join(PNG, "fig_training_curves.png"),
         "Training and validation loss and accuracy over five epochs.", wide=True, width=5.6)
p.figure(os.path.join(ART, "confusion_matrix_normalized.png"),
         "Row-normalised confusion matrix over the 38 classes on the validation split.", wide=True, width=5.4)
p.h2("Model Complexity and Server-Side Latency")
p.para("The exported model has 1,574,708 parameters (counted from the ONNX initializers) in 155 graph "
       "nodes; the PyTorch checkpoint is 3.13 MiB and the FP32 ONNX file 6.10 MiB. Latency was measured "
       "with ONNX Runtime 1.31 on an AMD Ryzen 5 5625U laptop CPU, batch 1, 224×224 input, 20 warm-up runs "
       "followed by 200 timed runs (Table 8). A single CPU thread suffices for interactive diagnosis.")
p.table(["Threads", "Mean (ms)", "Std (ms)", "p50 (ms)", "p95 (ms)"],
        [["1", "6.07", "1.18", "5.81", "8.36"],
         ["4", "3.98", "1.77", "3.49", "6.78"]],
        "ONNX Runtime CPU inference latency (n = 200).", widths=[0.6, 0.7, 0.7, 0.7, 0.7])
p.h2("Static Edge-Feasibility Analysis")
p.para("For an input of side *r*, *c* channels and *b* bytes per element the input activation alone needs")
p.eq(r"M_{\mathrm{act}}=r^{2}\,c\,b=224^{2}\times3\times4\ \mathrm{B}=588\ \mathrm{KiB},")
p.para("which already exceeds the 520 KiB SRAM of the base ESP32 [@espressif2026esp32] before any "
       "intermediate feature map, camera frame buffer or Wi-Fi stack is allocated. The FP32 model is 12.0× "
       "that SRAM budget, and even an ideal 4× INT8 compression [@jacob2018quantization] leaves 1.53 MiB "
       "(Fig. 8). On-device inference therefore requires a smaller input, fewer classes, PSRAM-backed tensor "
       "arenas or an ESP32-S3-class part; the deployed design runs inference on the server.")
p.figure(os.path.join(PNG, "fig_memory.png"),
         "Model footprint versus on-chip memory budgets (log scale).")
p.h2("Controller Simulation")
p.para("To illustrate why the hold rule matters, we simulated 48 h with a bucket soil model: moisture falls "
       "2 %/h by evapotranspiration, rises 0.12 % per 10 s tick while pumping, and one hour of rain occurs "
       "at t = 20 h; the sensor adds Gaussian noise (σ = 2 %), and the 15 min cap and 30 min cooldown apply "
       "to both rules. These parameters are assumptions, not field measurements. "
       f"A single 30 % threshold switched the relay **{S1['switches']}** times as noise crossed the "
       f"threshold, whereas Algorithm 1 switched **{S2['switches']}** times for similar pump-on time "
       f"({S1['pump_minutes']:.0f} vs. {S2['pump_minutes']:.0f} min) (Fig. 9). The simulation also exposed a "
       "design interaction: with this wetting rate the 15 min cap ends each cycle near 45 %, well short of "
       "θ_wet, so in practice the cap rather than the upper threshold bounds each irrigation event.")
p.figure(os.path.join(PNG, "sim_hysteresis.png"),
         "Simulated 48 h trace (assumed soil model; not a field result). Hysteresis reduces relay "
         "switching by roughly two orders of magnitude under 2 % sensor noise.")
p.h2("Functional Verification")
p.table(["Suite", "Scope", "Result"],
        [["Firmware self-test", "Algorithm 1, 11 cases", "11/11 pass"],
         ["ML unit tests (pytest)", "Cleaning, manifest, split, taxonomy, config, pipeline", "31/31 pass"],
         ["Backend test_automation", "Per-mode safety gate", "Pass"],
         ["Backend test_plant_predict", "Diagnosis response normalisation", "Pass"],
         ["Python port of Algorithm 1", "Same 11 cases", "11/11 pass"]],
        "Automated verification executed for this paper.", widths=[1.2, 1.55, 0.7], size=7)

# ------------------------------------------------------------------ XI
p.h1("Discussion and Limitations")
p.para("**The 99.32 % is a laboratory upper bound.** The baseline was trained with a naïve per-class 80/20 "
       "random split, not the duplicate-group-aware split of Section VII, so validation accuracy may be "
       "inflated by near-duplicates. PlantVillage photographs are single detached leaves on plain backgrounds; "
       "published models trained on it fall to 31–68 % on field images (Fig. 10). The field gap of this model "
       "has not yet been measured.")
p.figure(os.path.join(PNG, "fig_gap.png"),
         "Published laboratory-to-field accuracy evidence [@mohanty2016deep,salman2025plantdisease]; the "
         "field value for this work is pending.")
p.para("Further limitations, stated so they are not mistaken for capabilities:")
p.bullets([
    "The deployed Plant Scan currently uses the vision-language fallback; the full two-stage pipeline is "
    "implemented but has not been trained end to end (it needs ~13 GB of data and more GPU time than a free "
    "Colab session).",
    "No inline flow meter is installed, so no water-saving percentage is claimed.",
    "The firmware does not report measured pump state, so cloud and node can briefly disagree.",
    "The DHT11 has limited accuracy (±2 °C, ±5 % RH class), and soil temperature is derived.",
    "The LLM layer is bound to one hosted provider and fails closed (HTTP 503) when unreachable.",
    "Per-unit cost, on-device latency, power, uptime and packet loss have not been measured.",
])
p.para("The planned next steps are: evaluation on PlantDoc and on a hand-labelled set captured by the "
       "project's own ESP32-CAM; a retrain on the de-duplicated split to quantify leakage; a two-plot, "
       "flow-metered trial of moisture mode against timer mode; and an INT8 feasibility sweep on ESP32-S3.")

# ------------------------------------------------------------------ XII
p.h1("Conclusion")
p.para("AgriSense AI shows that the familiar sensor-plus-camera-plus-classifier architecture can be built "
       "around its failure modes rather than its happy path. Placing an ordered, self-tested rule set on the "
       "node keeps irrigation safe and available when the cloud is not; routing telemetry directly to a "
       "secured database makes every value-added service optional; and a data pipeline that removes "
       "near-duplicates and quarantines field data makes the reported accuracy auditable. The measured "
       "baseline (99.32 % top-1 on laboratory images, 6.07 ms per image on one CPU thread) proves the "
       "training-to-serving path end to end. We have deliberately not claimed field accuracy or water "
       "savings; the protocol and code to measure both are in place, and the full source is released.")

p.h1("Acknowledgment", numbered=False)
p.para("The authors thank [Guide Name] and the Department of Emerging Technologies, S. B. Jain Institute of Technology, Management and Research, Nagpur, for guidance and the maintainers of PlantVillage, PlantDoc, "
       "Ultralytics, ONNX Runtime and Supabase for openly available datasets and tools.")
p.references()
p.bio("Tisha Jhariya", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("Akiko Gajbhiye", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("Ansh Meshram", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("Agya Chourasia", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("[Guide Name]", "is with the Department of Emerging Technologies, S. B. Jain Institute of Technology, Management and Research, Nagpur, India. [Research interests.]")
p.save(os.path.join(OUT, "AgriSense_Implementation_Paper.docx"))
