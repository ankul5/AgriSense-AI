"""Survey paper (IEEE Access format) -> paper/out/AgriSense_Survey_Paper.docx
Quantities quoted from the literature are those reported by the cited
sources; the coverage marks in Table 1 are the authors' assessment of each
survey's primary scope.
"""
import os

from ieee import Paper, PAPER

OUT = os.path.join(PAPER, "out")
os.makedirs(OUT, exist_ok=True)
PNG = os.path.join(PAPER, "png")
F, H, N = "●", "◐", "○"

p = Paper("T. Jhariya et al.: IoT, Edge AI and LLMs for Smart Agriculture — A Survey")

p.front(
    title="IoT, Edge AI, and Large Language Models for Smart Agriculture: A Survey of Closed-Loop "
          "Irrigation, Crop Disease Diagnosis, and Their Deployment Gaps",
    authors="**TISHA JHARIYA**^{1}, **AKIKO GAJBHIYE**^{1}, **ANSH MESHRAM**^{1}, **AGYA CHOURASIA**^{1}, AND **[GUIDE NAME]**^{1}",
    affils=["^{1}Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, Maharashtra 441501, India"],
    corresponding="[Guide Name] ([email address])",
    received="Received [date], accepted [date], date of publication [date], date of current version [date].  "
             "Digital Object Identifier 10.1109/ACCESS.2026.DOI",
    abstract=(
        "Smart-agriculture research has converged on a recognisable stack: low-cost sensor nodes and "
        "cameras, wireless connectivity, automated irrigation, deep-learning disease diagnosis, and, most "
        "recently, large language models (LLMs) that answer agronomic questions. Existing surveys usually "
        "treat these layers separately, and most predate both the TinyML and LLM waves. This survey "
        "reviews the full stack in one frame and focuses on the question that matters for deployment: "
        "which reported results survive contact with real fields. We organise the literature into a "
        "five-branch taxonomy covering sensing and connectivity, irrigation control, disease diagnosis, "
        "edge AI, and LLM-based advisory with security. For each branch we compare representative methods "
        "and quantify recurring gaps. Three findings stand out. First, reported irrigation savings span "
        "roughly 9–50 %, yet few studies meter both a treatment and a control arm or specify behaviour under "
        "sensor failure. Second, plant-disease classifiers commonly report over 99 % accuracy on laboratory "
        "imagery but fall to about 31–68 % on field images, a gap compounded by near-duplicate leakage in "
        "random splits. Third, published feasibility results for disease models on ESP32-class "
        "microcontrollers contradict one another because class count, input resolution, quantization and "
        "chip variant are rarely reported together. We illustrate these issues with an open reference "
        "implementation, AgriSense AI, and close with a research agenda centred on field-validated "
        "evaluation, fail-safe control, memory-aware edge models, and grounded, auditable agricultural LLMs."),
    keywords="Smart agriculture, Internet of Things, precision irrigation, plant disease detection, deep "
             "learning, domain shift, TinyML, edge computing, large language models, survey.",
)

# ------------------------------------------------------------------ I
p.h1("Introduction")
p.para("Feeding a growing population with less water and fewer chemical inputs is a defining challenge of "
       "this century. Agriculture already accounts for around 70 % of global freshwater withdrawals "
       "[@fao2024aquastat], and an expert survey across 67 countries estimates yield losses to pathogens and "
       "pests of 10–28 % for wheat, 25–41 % for rice, 20–41 % for maize, 8–21 % for potato and 11–32 % for "
       "soybean [@savary2019burden]. Plant disease has long been recognised as a threat to food security "
       "[@strange2005plant]. Both problems are worst for smallholders, who lack sensors, agronomists and "
       "reliable connectivity.")
p.para("Digital agriculture promises to close this gap by measuring the field continuously and acting on "
       "it automatically [@wolfert2017bigdata,tzounis2017iot]. Over the past decade three technology waves "
       "have arrived in quick succession: Internet of Things (IoT) sensing and actuation "
       "[@elijah2018overview,ayaz2019iot,farooq2019survey], deep learning for image-based diagnosis "
       "[@kamilaris2018deep,mohanty2016deep], and, since 2023, large language models (LLMs) and foundation "
       "models [@tzachor2023llm,li2024foundation]. In parallel, TinyML has made it plausible to run neural "
       "networks on microcontrollers costing a few dollars [@warden2019tinyml,lin2020mcunet].")
p.para("The literature on each wave is large, but it is fragmented, and much of it reports results under "
       "conditions that do not hold in deployment: irrigation savings without metered controls, disease "
       "accuracies measured on laboratory photographs, and edge feasibility judged on a single operating "
       "point. This survey therefore asks not only *what has been built* but *what has been shown to work in "
       "the field, and under what evaluation*.")
p.h2("Comparison With Existing Surveys")
p.para("Table 1 positions this survey against prior reviews. IoT surveys [@tzounis2017iot,elijah2018overview,"
       "ayaz2019iot,farooq2019survey,friha2021iot,talavera2017review] cover sensing and networking in depth but "
       "treat disease diagnosis briefly; disease-detection reviews [@li2021plantreview,liu2021plantmethods,"
       "thakur2022trends] cover models and datasets but not actuation or deployment hardware; and the "
       "foundation-model review of Li et al. [@li2024foundation] predates most agricultural LLM deployments. "
       "None jointly examines closed-loop control, diagnosis, edge feasibility and LLM advisory, nor treats "
       "evaluation validity as a cross-cutting theme.")
p.table(["Survey", "Year", "IoT", "Irrig.", "Disease DL", "Edge/TinyML", "LLM", "Domain shift"],
        [["Tzounis et al. [@tzounis2017iot]", "2017", F, H, N, N, N, N],
         ["Kamilaris & Prenafeta-Boldú [@kamilaris2018deep]", "2018", N, H, F, N, N, H],
         ["Liakos et al. [@liakos2018machine]", "2018", N, F, H, N, N, N],
         ["Elijah et al. [@elijah2018overview]", "2018", F, H, N, H, N, N],
         ["Ayaz et al. [@ayaz2019iot]", "2019", F, F, H, N, N, N],
         ["Farooq et al. [@farooq2019survey]", "2019", F, F, N, N, N, N],
         ["García et al. [@garcia2020iot]", "2020", F, F, N, N, N, N],
         ["Gupta et al. [@gupta2020security]", "2020", F, N, N, N, N, N],
         ["Friha et al. [@friha2021iot]", "2021", F, H, H, F, N, N],
         ["Li, Zhang & Wang [@li2021plantreview]", "2021", N, N, F, N, N, H],
         ["Thakur et al. [@thakur2022trends]", "2022", N, N, F, N, N, H],
         ["Li et al. [@li2024foundation]", "2024", N, N, H, N, F, H],
         ["**This survey**", "2026", F, F, F, F, F, F]],
        "Scope of related surveys (● major focus, ◐ partial, ○ not covered; authors' assessment).",
        widths=[2.3, 0.45, 0.45, 0.5, 0.75, 0.85, 0.45, 0.85], wide=True, size=7.5)
p.h2("Contributions")
p.bullets([
    "A unified **five-branch taxonomy** of AI-enabled smart agriculture spanning sensing, control, "
    "diagnosis, edge inference and LLM advisory (Section III, Fig. 1).",
    "A critical comparison of **irrigation control strategies** with attention to metered evaluation and "
    "fail-safe behaviour (Section V).",
    "A synthesis of **disease-diagnosis datasets and models** together with the evidence on the "
    "laboratory-to-field gap and data leakage, and concrete evaluation recommendations (Sections VI–VII).",
    "An analysis of the **ESP32-class feasibility contradiction** in edge disease diagnosis, reduced to a "
    "closed-form memory bound (Section VIII).",
    "A review of **LLMs for agricultural advisory** and of **security and multi-tenancy** (Sections IX–X), "
    "a reference-implementation case study (Section XI) and a **research agenda** (Section XII).",
], numbered=True)

# ------------------------------------------------------------------ II
p.h1("Survey Methodology")
p.para("We conducted a structured narrative review following the reporting principles of systematic "
       "reviews. Sources were IEEE Xplore, ScienceDirect, MDPI, SpringerLink/Nature, ACM Digital Library, "
       "Frontiers, Google Scholar and arXiv. Query strings combined a domain term (*smart agriculture, "
       "precision irrigation, plant disease, crop disease*) with a technology term (*IoT, wireless sensor "
       "network, deep learning, CNN, vision transformer, TinyML, edge computing, ESP32, large language "
       "model, retrieval-augmented generation*).")
p.para("**Inclusion criteria:** peer-reviewed journal or conference papers, or widely cited preprints, "
       "published 2014–2026; a concrete system, model, dataset or evaluation; and reported quantitative "
       "results. **Exclusion criteria:** papers without an evaluation, duplicates of the same system, and "
       "non-English papers. Seminal earlier works were included where they define a method still in use. "
       "Every quantitative figure quoted below is taken from the cited source; where a source does not state "
       "a quantity we mark it *n/s* rather than estimate it.")

# ------------------------------------------------------------------ III
p.h1("Background and Taxonomy")
p.para("A smart-agriculture system closes a loop from **measurement** to **decision** to **action** "
       "[@wolfert2017bigdata]. Sensors and cameras measure the field; a connectivity layer moves data to "
       "edge or cloud computation; intelligence components decide when to irrigate, what disease is present "
       "and what the farmer should do; and actuators and user interfaces carry out the decision. Fig. 1 "
       "organises the surveyed literature along these lines into five branches, which structure the "
       "remainder of this paper.")
p.figure(os.path.join(PNG, "survey_taxonomy.png"),
         "Taxonomy of AI- and IoT-enabled smart agriculture used in this survey, with the section covering "
         "each branch.", wide=True)
p.para("Two cross-cutting concerns run through all branches. **Evaluation validity** asks whether a "
       "reported number predicts field behaviour; **failure behaviour** asks what the system does when a "
       "sensor, link or model fails. Both are under-reported, and we return to them in every section.")

# ------------------------------------------------------------------ IV
p.h1("IoT Sensing and Connectivity")
p.h2("Field Sensors")
p.para("Soil water is the primary irrigation input. Resistive probes are cheap but corrode; low-cost "
       "capacitive probes avoid galvanic contact and, for a soil with constant solid-to-volume ratio, give "
       "a reliable relation between output voltage and gravimetric water content, but they require "
       "per-soil calibration [@placidi2020capacitive]. Air temperature and humidity (e.g., DHT11/DHT22 "
       "class sensors), rain detectors and light sensors complement soil data and feed evapotranspiration "
       "models [@allen1998fao56]. Surveys of agricultural IoT catalogue many further sensors, including soil "
       "nutrient, pH and leaf-wetness probes [@ayaz2019iot,farooq2019survey,talavera2017review].")
p.para("A recurring, rarely discussed issue is **sensor-failure semantics**. A disconnected analogue input "
       "floats to an arbitrary or near-zero ADC value, which a naïve calibration maps to either saturated or "
       "bone-dry soil; in the latter case a threshold controller irrigates indefinitely. Explicit "
       "disconnect detection and fail-safe defaults are therefore a correctness requirement, not an "
       "optimisation (Section V-D).")
p.h2("Connectivity")
p.para("Table 2 compares common link technologies. Wi-Fi suits farms with on-site infrastructure; "
       "LoRa/LoRaWAN trades data rate for kilometre-scale range and multi-year battery life "
       "[@augustin2016lora]; NB-IoT and cellular links add licensed-spectrum reliability at higher cost. "
       "Camera streaming and image upload generally require Wi-Fi or cellular bandwidth, which pushes "
       "image-heavy nodes towards mains power or larger batteries.")
p.table(["Technology", "Typical range", "Data rate", "Power", "Fit"],
        [["Wi-Fi (802.11n)", "~10–100 m", "Mbps", "High", "Images, farm hubs"],
         ["LoRa/LoRaWAN", "km (rural)", "~0.3–50 kbps", "Very low", "Sparse sensor data"],
         ["NB-IoT", "km (cellular)", "~10s kbps", "Low", "Licensed, managed"],
         ["ZigBee (802.15.4)", "~10–100 m", "250 kbps", "Low", "Mesh greenhouses"],
         ["BLE", "~10–50 m", "~1 Mbps", "Very low", "Handheld, local"],
         ["4G/5G cellular", "km", "Mbps+", "High", "Video, remote sites"]],
        "Qualitative comparison of field connectivity options.",
        widths=[0.85, 0.7, 0.65, 0.5, 0.75], size=7)
p.h2("Platforms and Data Paths")
p.para("Application protocols are dominated by MQTT and HTTPS/REST. Open-source IoT platforms such as "
       "ThingsBoard [@thingsboard] and OpenRemote [@openremote] provide device management, dashboards and "
       "multi-tenant isolation out of the box, and managed back-end-as-a-service databases with row-level "
       "security and real-time subscriptions [@supabase2026] now allow a microcontroller to write directly to "
       "a secured store. Multi-tenancy is thus a commodity capability and should not be presented as a "
       "research contribution. A more consequential architectural decision is *where the control decision "
       "lives*: edge computing literature argues for placing latency- and availability-critical decisions "
       "close to the data source [@shi2016edge,satyanarayanan2017edge].")

# ------------------------------------------------------------------ V
p.h1("Irrigation Control Strategies")
p.h2("From Timers to Closed Loops")
p.para("Irrigation control ranges from open-loop timers through sensor-based closed loops to model-based "
       "and learning-based scheduling (Table 3). Timer control is simple but waters regardless of rain or "
       "soil state. Threshold control with hysteresis switches on below a dry threshold and off above a wet "
       "threshold, avoiding actuator chatter. Water-balance scheduling uses reference evapotranspiration "
       "and crop coefficients following FAO-56 [@allen1998fao56]. Decision-support systems "
       "[@navarro2016dss] and machine-learning predictors that combine soil sensing with weather forecasts "
       "[@goap2018iot] aim to anticipate demand, and platform-scale systems such as SWAMP "
       "[@kamienski2019swamp] integrate these into water-management services.")
p.table(["Strategy", "Inputs", "Strength", "Weakness", "Examples"],
        [["Open-loop timer", "Clock", "Simple, robust", "Ignores rain/soil", "Commercial timers"],
         ["Threshold + hysteresis", "Soil moisture", "Cheap, reactive", "Needs calibration", "[@gutierrez2014automated]"],
         ["Water balance (ET)", "Weather, crop Kc", "Physically grounded", "Needs weather data", "[@allen1998fao56]"],
         ["DSS / expert rules", "Soil, weather, crop", "Agronomic context", "Site tuning", "[@navarro2016dss]"],
         ["ML prediction", "Sensors + forecasts", "Anticipatory", "Data hungry, opaque", "[@goap2018iot]"],
         ["Platform / multi-farm", "Many sources", "Scale, services", "Complexity", "[@kamienski2019swamp]"]],
        "Irrigation control strategies.", widths=[0.95, 0.85, 0.75, 0.8, 0.85], size=7, wide=True)
p.h2("Reported Water Savings")
p.para("Reviews of IoT irrigation report savings spanning roughly 9–50 % [@garcia2020iot,vallejo2023smart]. "
       "The width of this range reflects differences in crop, climate, baseline practice and, critically, "
       "measurement method. A well-instrumented recent trial reports 431.47 L under closed-loop control "
       "against 592.39 L for a fixed schedule, a 27.16 % reduction, while also reducing the soil-moisture "
       "standard deviation from 10.46 % to 1.35 % [@usman2026aiirrigation]; a multi-season IoT deployment "
       "reports improved water-use efficiency [@mohamed2026iotirrigation]. We define the saving as")
p.eq(r"\Sigma=\frac{V_{\mathrm{fs}}-V_{\mathrm{cl}}}{V_{\mathrm{fs}}}\times100\%,")
p.para("where *V*_{fs} and *V*_{cl} are the metered volumes of the fixed-schedule and closed-loop arms. "
       "Because a controller can trivially \"save\" water by under-irrigating, Σ should always be reported "
       "with both volumes, the soil-moisture mean and spread of each arm, and a crop-health or yield proxy.")
p.h2("Evaluation Gaps")
p.bullets([
    "Many studies estimate savings from pump run-time rather than an inline flow meter.",
    "Treatment and control arms often differ in hardware or plot, confounding the comparison.",
    "Trials are short (days to weeks) relative to a crop season.",
])
p.h2("Fail-Safe Design")
p.para("Few papers specify controller behaviour under faults. We identify four practices that should be "
       "standard: (i) **ordered rules** in which sensor interlocks (failed probe, rain, saturated soil) "
       "dominate manual and cloud commands; (ii) **hysteresis** to bound switching; (iii) **hard run-time "
       "limits and cooldowns** that bound delivery under mis-calibration; and (iv) **edge authority**, so "
       "the node keeps controlling when connectivity is lost. Section XI shows one implementation.")

# ------------------------------------------------------------------ VI
p.h1("Deep Learning for Crop Disease Diagnosis")
p.h2("Datasets")
p.para("Table 4 summarises public datasets. PlantVillage [@hughes2015plantvillage] dominates the "
       "literature but contains single detached leaves photographed on uniform backgrounds. Field-condition "
       "datasets such as PlantDoc [@singh2020plantdoc], iCassava [@mwebaze2019icassava], Plant Pathology "
       "2020 [@thapa2020plantpathology] and PlantWild [@plantwild2024] are smaller per class but far closer to "
       "deployment conditions.")
p.table(["Dataset", "Images", "Classes", "Conditions", "Typical use"],
        [["PlantVillage [@hughes2015plantvillage]", "54,305", "38", "Lab, plain background", "Training benchmark"],
         ["PlantDoc [@singh2020plantdoc]", "2,598", "27", "Field, web-sourced", "Cross-domain test"],
         ["iCassava / Cassava [@mwebaze2019icassava]", "~21k", "5", "Field, Uganda", "Field training"],
         ["Plant Pathology 2020 [@thapa2020plantpathology]", "3,651", "4", "Field, apple", "Field benchmark"],
         ["PlantWild [@plantwild2024]", "30,030", "n/s", "In-the-wild", "Field training"],
         ["Rice leaf [@riceleaf2023]", "5,932", "4", "Mixed", "Crop-specific"]],
        "Public plant-disease image datasets (counts as released or as in common mirrors).",
        widths=[1.7, 0.6, 0.55, 1.15, 1.0], size=7, wide=True)
p.h2("Model Families")
p.para("**CNN transfer learning.** Mohanty et al. fine-tuned AlexNet and GoogLeNet on PlantVillage to "
       "99.35 % [@mohanty2016deep]; Ferentinos reported 99.53 % with VGG on a 58-class corpus "
       "[@ferentinos2018deep,simonyan2015vgg]; Too et al. compared fine-tuned architectures and reached "
       "99.75 % with DenseNet [@too2019comparative]; Sladojevic et al. [@sladojevic2016deep] and Brahimi et "
       "al. [@brahimi2017deep] reported similar figures on smaller taxonomies. **Efficient backbones** such as "
       "MobileNet [@howard2017mobilenets,sandler2018mobilenetv2] and EfficientNet [@tan2019efficientnet] "
       "trade a little accuracy for mobile deployment, as in the smartphone cassava diagnosis of Ramcharan "
       "et al. [@ramcharan2017cassava,ramcharan2019mobile]. **Detectors** localise lesions in cluttered "
       "scenes: Fuentes et al. compared Faster R-CNN, R-FCN and SSD on tomato [@fuentes2017robust], and "
       "YOLO-family detectors [@redmon2016yolo,liu2020yolov3tomato] target real-time use. **Vision "
       "transformers** [@dosovitskiy2021vit] now underpin the strongest cross-domain results "
       "[@salman2025plantdisease]. **Few-shot learning** addresses the scarcity of labelled field images "
       "[@argueso2020fewshot], and explainability studies show what CNNs attend to when diagnosing "
       "[@toda2019cnn,selvaraju2017gradcam].")
p.table(["Study", "Model", "Data", "Reported result", "Field?"],
        [["Mohanty [@mohanty2016deep]", "GoogLeNet", "PlantVillage", "99.35 %; 31.4 % external", "Ext. test"],
         ["Sladojevic [@sladojevic2016deep]", "CaffeNet", "Web images, 13 cl.", "96.3 %", "No"],
         ["Brahimi [@brahimi2017deep]", "GoogLeNet", "Tomato (PV)", "99.18 %", "No"],
         ["Ferentinos [@ferentinos2018deep]", "VGG", "58 classes", "99.53 %", "Partly"],
         ["Too [@too2019comparative]", "DenseNet-121", "PlantVillage", "99.75 %", "No"],
         ["Ramcharan [@ramcharan2017cassava]", "Inception v3", "Cassava field", "93 %", "Yes"],
         ["Fuentes [@fuentes2017robust]", "R-FCN + ResNet", "Tomato field", "mAP 85.98 %", "Yes"],
         ["Salman [@salman2025plantdisease]", "ViT-based", "PV → PlantDoc", "68 % cross-domain", "Yes"],
         ["Samanta [@samanta2024leafsense]", "Compact CNN", "ESP32-CAM", "92 %", "No"],
         ["Aqasizade [@aqasizade2026tinymlops]", "Quantised CNN", "ESP32-S3", "94.6 %, F1 0.94", "7-day"],
         ["Nyakuri [@nyakuri2025aiiot]", "CNN", "Raspberry Pi 5", "98.6 %, 16 ms", "n/s"]],
        "Representative disease-diagnosis studies (values as reported by each source).",
        widths=[1.3, 0.95, 1.05, 1.35, 0.6], size=7, wide=True)

# ------------------------------------------------------------------ VII
p.h1("Domain Shift and Evaluation Pitfalls")
p.h2("The Laboratory-to-Field Gap")
p.para("The most important result in this literature is negative. Mohanty et al. themselves observed "
       "accuracy falling from 99.35 % to 31.4 % when their PlantVillage-trained network was applied to "
       "images from other sources [@mohanty2016deep]. On PlantDoc, the cross-domain state of the art for a "
       "PlantVillage-trained model is about 68 %, against 48 % for ViT-Base, 43 % for EfficientNet and 41 % "
       "for InceptionV3 [@salman2025plantdisease] (Fig. 2). Barbedo attributes the gap to background "
       "clutter, illumination, capture variability and co-occurring symptoms absent from laboratory images "
       "[@barbedo2018factors,barbedo2019plant]; Picon et al. showed that training on images captured in the "
       "wild with mobile devices substantially improves field performance [@picon2019deep]. We define the gap "
       "on the same weights as")
p.eq(r"\Delta_{\mathrm{dom}}=A_{@1}^{\mathrm{lab}}-A_{@1}^{\mathrm{field}},")
p.para("and recommend reporting it with both operands, never as a ratio. The phenomenon is an instance of "
       "general distribution shift [@bendavid2010theory,torralba2011unbiased,recht2019imagenet,koh2021wilds] "
       "and of shortcut learning on backgrounds [@geirhos2020shortcut].")
p.figure(os.path.join(PNG, "fig_gap.png"),
         "Published laboratory versus field/cross-domain accuracy [@mohanty2016deep,salman2025plantdisease]. "
         "The two rightmost bars are the AgriSense case study of Section XI; its field value is not yet measured.")
p.h2("Data Leakage")
p.para("Laboratory corpora contain several photographs of the same leaf. A random split places these "
       "near-duplicates in both training and test partitions, inflating accuracy without improving "
       "generalisation; leakage of this kind is now recognised as a leading cause of irreproducible "
       "machine-learning results [@kapoor2023leakage]. Perceptual hashing [@zauner2010phash] offers a cheap "
       "remedy: images whose 64-bit hashes differ in at most τ bits,")
p.eq(r"d_H(h_i,h_j)\leq\tau,")
p.para("are grouped, and each group is assigned to a single partition.")
p.h2("Recommendations")
p.bullets([
    "Report at least one **cross-domain or field test set** never used for training or model selection.",
    "Use **duplicate-group-aware splits** and state the de-duplication method and threshold.",
    "Report **macro-F1** alongside accuracy, because disease taxonomies are imbalanced.",
    "Report **variation across seeds** and test differences with paired statistics [@demsar2006statistical].",
    "Treat field accuracy above ~90 % from a laboratory-trained model as a **red flag for leakage**.",
])

# ------------------------------------------------------------------ VIII
p.h1("Edge AI and TinyML")
p.h2("Why the Edge")
p.para("Running inference on or near the sensor removes dependence on connectivity, reduces bandwidth and "
       "latency, and keeps images local [@shi2016edge,satyanarayanan2017edge]. TinyML pushes this to "
       "microcontrollers with hundreds of kilobytes of SRAM [@warden2019tinyml,sanchez2020tinyml,ray2022tinyml]. "
       "Key enablers are integer quantization [@jacob2018quantization,krishnamoorthi2018whitepaper], "
       "interpreters such as TensorFlow Lite Micro [@david2021tflm], memory-aware architecture search "
       "(MCUNet [@lin2020mcunet]) and patch-based inference that cuts peak activation memory "
       "[@lin2021mcunetv2]. MLPerf Tiny standardises benchmarking [@banbury2021mlperftiny].")
p.h2("The ESP32 Feasibility Contradiction")
p.para("Published results disagree on whether disease classification fits ESP32-class parts. Nyakuri et al. "
       "report that ESP32-CAM, Raspberry Pi Pico and Arduino Nano 33 BLE Sense could not run their model and "
       "selected a Raspberry Pi 5 (98.6 %, 16 ms, about US$80) [@nyakuri2025aiiot]; Samanta et al. run a "
       "classifier on ESP32-CAM at 92 % [@samanta2024leafsense]; and Aqasizade et al. deploy a quantised model "
       "on ESP32-S3 at 94.6 % accuracy and 0.94 macro-F1 with a seven-day field deployment "
       "[@aqasizade2026tinymlops]. These are not contradictory once the binding constraint is made explicit. "
       "For an input of side *r*, *c* channels and *b* bytes per element, the input activation alone needs")
p.eq(r"M_{\mathrm{act}}=r^{2}\,c\,b,")
p.para("which at 224×224×3 in FP32 is 588 KiB, already above the 520 KiB SRAM of the base ESP32 "
       "[@espressif2026esp32]. Feasibility is therefore a surface over class count, resolution, precision "
       "and chip (with or without PSRAM), not a yes/no property of a board (Fig. 3). We recommend that edge "
       "papers report all four together with peak RAM, flash, latency and energy per inference.")
p.figure(os.path.join(PNG, "fig_memory.png"),
         "Footprint of a 1.57 M-parameter YOLO11n-cls classifier versus ESP32-family memory (case study of "
         "Section XI).")

# ------------------------------------------------------------------ IX
p.h1("Large Language Models for Agricultural Advisory")
p.para("LLMs can translate agronomic knowledge into conversational, localised advice. Tzachor et al. "
       "tested GPT-based models for cassava extension advice in Nigeria, found useful but sometimes "
       "inaccurate output, and proposed a design process with human experts in the loop "
       "[@tzachor2023llm]. Silva et al. evaluated GPT-4 on agriculture examinations "
       "[@silva2023gpt4agro]. Balaguer et al. compared retrieval-augmented generation (RAG) "
       "[@lewis2020rag] with fine-tuning on agricultural data and found that fine-tuning improved accuracy "
       "by over six percentage points, with RAG adding about five more [@balaguer2024rag]. Li et al. survey "
       "language, vision, multimodal and reinforcement-learning foundation models for agriculture "
       "[@li2024foundation].")
p.para("Three design patterns recur in deployed systems: **grounding** the model in live measurements "
       "(sensor telemetry, location, crop stage) so that advice is specific; **schema-constrained output** "
       "so that diagnoses can be parsed, validated and displayed consistently; and **human oversight** for "
       "high-stakes recommendations such as pesticide use. Open problems include hallucinated treatments, "
       "regional regulatory differences, low-resource languages, offline operation, and evaluation: few "
       "agricultural LLM systems report accuracy against expert-validated answers.")

# ------------------------------------------------------------------ X
p.h1("Security, Privacy and Multi-Tenancy")
p.para("Smart farms expose physical actuators and commercially sensitive data. Gupta et al. review threats "
       "across the smart-farming stack, from device tampering and wireless attacks to data-integrity and "
       "privacy risks [@gupta2020security]; Ferrag et al. survey security for green IoT-based agriculture "
       "including blockchain-based approaches [@ferrag2020security]. Practical baseline controls are: "
       "per-device credentials and pairing that requires physical possession; token-authenticated APIs; "
       "row-level data isolation between tenants; keeping third-party API keys server-side; and, for "
       "actuators, safety interlocks on the device that no remote command can override.")

# ------------------------------------------------------------------ XI
p.h1("Case Study: AgriSense AI Reference Implementation")
p.para("To ground the survey's recommendations we summarise AgriSense AI, an open implementation by the "
       "authors that integrates the five branches (Fig. 4).")
p.figure(os.path.join(PNG, "fig_architecture.png"),
         "AgriSense AI three-tier architecture: ESP32 sensor node and ESP32-CAM, managed PostgreSQL with "
         "row-level security, FastAPI backend, web and mobile clients.", wide=True)
p.table(["Survey finding", "AgriSense design response", "Status"],
        [["Cloud-dependent control", "Ordered on-node rules; cloud only queues requests", "Implemented"],
         ["Fail-unsafe probes", "ADC < 10 ⇒ probe failed ⇒ pump off; 11-case boot self-test", "Implemented"],
         ["Actuator chatter", "30/70 % hysteresis, 15 min cap, 30 min cooldown", "Implemented, simulated"],
         ["Unmetered savings", "Timer mode as control arm; flow meter required", "Pending"],
         ["Lab-only accuracy", "PlantDoc quarantined for evaluation only", "Pipeline built; eval pending"],
         ["Near-duplicate leakage", "SHA-256 + pHash (τ = 5) groups; group-aware 80/10/10 split", "Implemented"],
         ["Edge feasibility", "Memory bound: 588 KiB input > 520 KiB SRAM", "Analysed; server inference"],
         ["Ungrounded LLM advice", "Live telemetry in system prompt; JSON schema for diagnosis", "Implemented"],
         ["Tenant isolation", "Row-level security, ≤ 4 devices per account, keys server-side", "Implemented"]],
        "Mapping survey findings to the AgriSense implementation.",
        widths=[1.4, 3.0, 1.3], wide=True, size=7)
p.para("Its baseline YOLO11n-cls classifier reaches 99.32 % top-1 on 10,861 PlantVillage validation images "
       "across 38 classes and runs in about 6 ms per image on one laptop CPU thread, but was trained on a "
       "random split and has not yet been field-tested, so by this survey's own criteria it is a laboratory "
       "upper bound. The case illustrates that the gaps identified above are practical engineering choices "
       "that can be designed for from the start.")

# ------------------------------------------------------------------ XII
p.h1("Open Challenges and Future Directions")
p.bullets([
    "**Field-first evaluation.** Benchmarks built from images captured by deployed low-cost cameras, with "
    "standard cross-domain protocols and leakage-free splits.",
    "**Metered, controlled irrigation trials.** Season-long, flow-metered comparisons on identical hardware, "
    "reporting volumes, moisture statistics and yield.",
    "**Feasibility surfaces for edge models.** Systematic sweeps over chip, precision, resolution and class "
    "count with energy measurements, and hierarchical (species-then-disease) models to reduce per-model "
    "class count.",
    "**Sensor–vision fusion.** Using microclimate data (humidity, leaf wetness, temperature) as priors for "
    "disease risk, with calibrated uncertainty.",
    "**Trustworthy agricultural LLMs.** Retrieval over vetted extension material, expert-validated test "
    "sets, multilingual and offline small models, and provenance for every recommendation.",
    "**Fail-safe autonomy.** Formal or test-based verification of actuator logic, and actuator-state "
    "feedback so that cloud and node never disagree silently.",
    "**Cost and accessibility.** Reporting bill-of-materials cost, power autonomy (e.g., solar) and "
    "maintenance burden, which determine smallholder adoption.",
], numbered=True)

# ------------------------------------------------------------------ XIII
p.h1("Conclusion")
p.para("This survey reviewed IoT sensing, irrigation control, crop-disease diagnosis, edge AI and LLM "
       "advisory as one system rather than separate fields. Across all five branches the dominant gap is not "
       "a missing algorithm but missing evidence under deployment conditions: irrigation savings without "
       "metered controls, disease accuracy without field tests or leakage control, and edge feasibility "
       "without the parameters that determine it. Closing these gaps calls for field-first benchmarks, "
       "fail-safe control designs, memory-aware edge models and grounded, evaluated agricultural LLMs. We "
       "hope the taxonomy, comparisons and recommendations here help future work report results that "
       "transfer from the paper to the farm.")

p.h1("Acknowledgment", numbered=False)
p.para("The authors thank [Guide Name] and the Department of Emerging Technologies, S. B. Jain Institute of Technology, Management and Research, Nagpur, for support and the creators of the open datasets and tools "
       "discussed in this survey.")
p.references()
p.bio("Tisha Jhariya", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("Akiko Gajbhiye", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("Ansh Meshram", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("Agya Chourasia", "is with the Department of Emerging Technologies (Artificial Intelligence & Data Science), S. B. Jain Institute of Technology, Management and Research, Nagpur, India.")
p.bio("[Guide Name]", "is with the Department of Emerging Technologies, S. B. Jain Institute of Technology, Management and Research, Nagpur, India. [Research interests.]")
p.save(os.path.join(OUT, "AgriSense_Survey_Paper.docx"))
