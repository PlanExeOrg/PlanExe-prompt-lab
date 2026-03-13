## Primary Decisions
The vital few decisions that have the most impact.


The 'Critical' and 'High' impact levers address the core project tensions: participant safety vs. operational complexity (`Risk Mitigation Protocol`, `Staffing Coverage Model`), data richness vs. participant burden (`Data Acquisition Intensity Strategy`), sample size vs. event yield (`Recruitment Stringency Strategy`), and data validity vs. annotation cost (`Data Annotation Workflow`). These levers collectively govern the project's feasibility, ethical conduct, and scientific rigor. A missing dimension might be a lever explicitly addressing community engagement and neighborhood relations.

### Decision 1: Recruitment Channel Strategy
**Lever ID:** `aab98b8b-a06e-434d-a8c9-ac353c08e684`

**The Core Decision:** The Recruitment Channel Strategy defines how participants are sourced for the study. It controls the pool of potential participants and influences the screening burden and demographic diversity. Objectives include maximizing enrollment of eligible participants while minimizing screening costs and self-selection bias. Key success metrics are the number of enrolled participants, the proportion of eligible participants from each channel, and the cost per enrolled participant.

**Why It Matters:** Altering recruitment affects enrollment rate and participant profile. Immediate: Change in application volume → Systemic: Skews participant demographics, impacting generalizability → Strategic: Alters statistical power and relevance to target population.

**Strategic Choices:**

1. Prioritize referrals from University Hospital Bonn sleep clinic to ensure a steady stream of pre-screened participants, accepting a potentially narrower demographic.
2. Expand recruitment to regional neurologist networks and the Deutsche Gesellschaft für Schlafforschung und Schlafmedizin, accepting increased screening burden and variable diagnostic rigor.
3. Implement targeted online advertising campaigns and partnerships with patient advocacy groups, accepting higher initial screening costs and potential for self-selection bias.

**Trade-Off / Risk:** Controls Enrollment Rate vs. Participant Representativeness. Weakness: The options don't address the potential impact of recruitment strategies on participant retention rates.

**Strategic Connections:**

**Synergy:** This lever strongly synergizes with `Recruitment Stringency Strategy`. The chosen channel influences the effectiveness of stringent screening. A broader channel may necessitate stricter screening. A narrow channel like the sleep clinic may allow for less stringent criteria. 

**Conflict:** This lever conflicts with `Data Acquisition Intensity Strategy`. If recruitment yields participants less tolerant of intensive monitoring, a lower-intensity data acquisition strategy may be necessary to maintain enrollment and adherence, potentially sacrificing data richness.

**Justification:** *High*, High because it directly impacts enrollment rate, participant demographics, and screening burden. Its synergy with `Recruitment Stringency Strategy` and conflict with `Data Acquisition Intensity Strategy` highlight its central role in balancing project feasibility and data quality.

### Decision 2: Recruitment Stringency Strategy
**Lever ID:** `a140c2be-490c-499a-a964-3d0b8b11f4ea`

**The Core Decision:** The Recruitment Stringency Strategy dictates the criteria used to select participants for the study. It controls the homogeneity of the sample and influences the event capture rate. Objectives include maximizing the yield of parasomnia events while maintaining a reasonable sample size. Key success metrics are the proportion of participants exhibiting captured events and the overall number of captured events.

**Why It Matters:** Stricter criteria reduce unproductive admissions but limit sample size. Immediate: Fewer participants admitted → Systemic: Slower enrollment and reduced statistical power → Strategic: Impacts the generalizability and robustness of findings, potentially requiring longer study duration.

**Strategic Choices:**

1. Prioritize broad inclusion using minimal screening criteria, accepting a higher rate of unproductive admissions to maximize sample size.
2. Employ moderate screening, balancing inclusion and exclusion criteria to optimize event capture rate while maintaining a reasonable sample size.
3. Implement stringent pre-admission screening, including home video-EEG, to minimize unproductive admissions and maximize event capture efficiency, accepting a smaller, highly-selected sample.

**Trade-Off / Risk:** Controls Sample Size vs. Event Yield. Weakness: The options do not explicitly address the ethical considerations of home video-EEG screening.

**Strategic Connections:**

**Synergy:** This lever synergizes with `Recruitment Channel Strategy`. A stringent recruitment strategy may require focusing on specific recruitment channels known to yield eligible participants, such as referrals from specialized sleep clinics. 

**Conflict:** This lever conflicts with `Facility Expansion Strategy`. A highly stringent recruitment strategy may result in slower enrollment, potentially underutilizing the capacity of a larger facility. A more moderate approach might be necessary to fill available sleep suites.

**Justification:** *High*, High because it controls the trade-off between sample size and event yield, directly impacting statistical power and the ability to achieve Aim 2. Its synergy with `Recruitment Channel Strategy` and conflict with `Facility Expansion Strategy` are key.

### Decision 3: Data Acquisition Intensity Strategy
**Lever ID:** `0e866b59-5181-443c-9bb3-f73fc15f3e91`

**The Core Decision:** The Data Acquisition Intensity Strategy determines the level of physiological monitoring employed during participant stays. It controls the richness of the collected data and influences participant comfort and adherence. Objectives include maximizing data quality while minimizing participant burden. Key success metrics are the signal-to-noise ratio of the data, the participant dropout rate, and the completeness of the data records.

**Why It Matters:** More intensive data acquisition improves signal fidelity but increases participant burden. Immediate: Increased participant discomfort → Systemic: Higher dropout rates and reduced adherence to protocol → Strategic: Affects data completeness and introduces bias, potentially compromising the study's validity.

**Strategic Choices:**

1. Rely primarily on low-burden sensors (dry-electrode EEG, mattress sensors) with minimal scheduled PSG, prioritizing participant comfort and long-term adherence.
2. Balance low-burden sensors with scheduled enhanced-night PSG on a subset of nights, aiming for a compromise between data richness and participant burden.
3. Maximize data richness through continuous full PSG monitoring for all participants, accepting potential participant discomfort and increased dropout rates.

**Trade-Off / Risk:** Controls Data Richness vs. Participant Burden. Weakness: The options don't consider adaptive PSG scheduling based on initial low-burden sensor data.

**Strategic Connections:**

**Synergy:** This lever synergizes with `Data Annotation Workflow`. Higher data acquisition intensity provides more detailed information for annotation, potentially improving the accuracy and reliability of event scoring. A comprehensive annotation workflow is essential for extracting meaningful insights from rich datasets.

**Conflict:** This lever conflicts with `Recruitment Stringency Strategy`. A less stringent recruitment strategy, aimed at broader inclusion, may necessitate a lower-intensity data acquisition approach to accommodate participants less tolerant of intensive monitoring, potentially sacrificing data richness.

**Justification:** *Critical*, Critical because it governs the fundamental trade-off between data richness and participant burden. Its impact on data completeness and validity makes it a central hub, influencing both recruitment and annotation workflows. Directly impacts Aim 2 and Aim 3.

### Decision 4: Staffing Coverage Model
**Lever ID:** `4c598798-03d1-4e91-965e-21a4c43ea8bc`

**The Core Decision:** The Staffing Coverage Model lever determines the number and roles of personnel present during overnight data collection. It controls the level of real-time monitoring, event response speed, and annotation throughput. Objectives include ensuring participant safety, capturing parasomnia events effectively, and maintaining data quality. Key success metrics are the ratio of captured events to participant-nights, the speed of response to potential safety incidents, and the completeness of initial data annotation. This lever directly impacts personnel costs and operational efficiency.

**Why It Matters:** Higher staffing levels improve safety and annotation quality but increase operational costs. Immediate: Increased personnel expenses → Systemic: Reduced budget for other research activities → Strategic: Impacts the scope and depth of the scientific program, potentially limiting the number of research questions addressed.

**Strategic Choices:**

1. Minimize staffing costs by relying on a single night technician with remote backup, accepting potential delays in event response and annotation.
2. Maintain a standard staffing model with one on-site technician and a rotating backup, balancing cost-effectiveness with adequate event response and annotation capacity.
3. Maximize safety and annotation quality by employing two on-site technicians per shift, ensuring immediate event response and comprehensive annotation, despite higher personnel costs.

**Trade-Off / Risk:** Controls Safety/Annotation Quality vs. Operational Costs. Weakness: The options fail to consider task automation to reduce technician workload.

**Strategic Connections:**

**Synergy:** A robust Staffing Coverage Model, particularly with two on-site technicians, directly enhances the effectiveness of the Risk Mitigation Protocol by enabling faster response times to alarms and potential safety incidents. It also improves the Data Annotation Workflow by providing more immediate and detailed initial annotations.

**Conflict:** Increasing staffing levels directly conflicts with budget constraints. A higher Staffing Coverage Model may necessitate compromises in other areas, such as delaying Facility Expansion Strategy or limiting the Data Acquisition Intensity Strategy to reduce costs associated with data storage and processing.

**Justification:** *Critical*, Critical because it controls safety, annotation quality, and operational costs. Its synergy with `Risk Mitigation Protocol` and conflict with budget constraints make it a foundational element of the project's operational feasibility and ethical conduct. Directly impacts Aim 1.

### Decision 5: Risk Mitigation Protocol
**Lever ID:** `7eb7bda8-66e5-4b3d-8bff-5675f416af90`

**The Core Decision:** The Risk Mitigation Protocol lever defines the safety measures and monitoring procedures in place to protect participants during residential data collection. It controls the level of active monitoring, alarm systems, and response protocols. Objectives include minimizing participant injury risk, managing false alarm rates, and ensuring ethical research practices. Key success metrics are the number of safety incidents, the frequency of false alarms, and participant satisfaction with safety measures. This lever impacts operational complexity and resource allocation.

**Why It Matters:** More stringent safety protocols reduce participant risk but increase operational complexity. Immediate: Increased monitoring overhead → Systemic: Slower response times to genuine events due to false alarms → Strategic: Impacts the feasibility of capturing rare events and the overall efficiency of the research unit.

**Strategic Choices:**

1. Implement basic safety measures (padded edges, door alarms) with minimal active monitoring, accepting a higher level of residual risk.
2. Employ standard safety protocols with active video monitoring and technician response to alarms, balancing risk mitigation with operational efficiency.
3. Adopt comprehensive safety measures including continuous video and physiological monitoring with automated anomaly detection, minimizing risk but increasing operational complexity and false alarm rates.

**Trade-Off / Risk:** Controls Participant Safety vs. Operational Complexity. Weakness: The options do not address the psychological impact of constant surveillance on participants.

**Strategic Connections:**

**Synergy:** A comprehensive Risk Mitigation Protocol synergizes strongly with the Staffing Coverage Model. More robust staffing allows for quicker responses to alarms and incidents. It also complements the Data Acquisition Intensity Strategy, as more detailed data streams can be used for automated anomaly detection.

**Conflict:** A more intensive Risk Mitigation Protocol can conflict with participant comfort and the goal of creating a naturalistic sleep environment. Continuous video monitoring, for example, may negatively impact Recruitment Stringency Strategy if potential participants are deterred by privacy concerns. It may also increase false alarms, burdening the Staffing Coverage Model.

**Justification:** *Critical*, Critical because it directly addresses participant safety, a non-negotiable aspect of the research. Its synergy with `Staffing Coverage Model` and conflict with participant comfort highlight its central role in balancing ethical considerations and practical constraints. Directly impacts Aim 1.

---
## Secondary Decisions
These decisions are less significant, but still worth considering.

### Decision 6: Facility Expansion Strategy
**Lever ID:** `9e8e5b69-6af7-4d8a-9d57-2138d2f822f0`

**The Core Decision:** The Facility Expansion Strategy determines the pace and scope of expanding the residential research unit. It controls the number of available sleep suites and influences the rate of data collection. Objectives include optimizing the use of resources and accelerating data acquisition. Key success metrics are the number of active sleep suites, the participant throughput, and the cost per participant.

**Why It Matters:** Altering the expansion plan impacts long-term scalability and resource allocation. Immediate: Change in suite availability → Systemic: Alters enrollment capacity and data collection rate → Strategic: Affects the ability to meet enrollment targets and secure future funding.

**Strategic Choices:**

1. Defer expansion of the facility beyond the initial 8 suites until the pilot phase demonstrates acceptable data quality, manageable false alarm rates, safe staffing ratios, and usable annotation throughput.
2. Initiate expansion to 12 suites concurrently with the pilot phase, accepting increased upfront investment and operational complexity to accelerate data collection.
3. Explore establishing satellite monitoring locations in participants' homes using portable PSG systems and remote monitoring, accepting increased logistical complexity and potential data quality variability for broader reach.

**Trade-Off / Risk:** Controls Enrollment Capacity vs. Financial Risk. Weakness: The options don't address the potential impact of expansion on the facility's community integration and neighborhood relations.

**Strategic Connections:**

**Synergy:** This lever synergizes with `Staffing Coverage Model`. Expanding the facility necessitates adjusting the staffing model to ensure adequate coverage and safety. More suites require more staff, especially during overnight monitoring. 

**Conflict:** This lever conflicts with `Risk Mitigation Protocol`. Rapid expansion without adequate risk mitigation could compromise participant safety and data quality. A slower, phased approach allows for better identification and management of potential risks, but delays data collection.

**Justification:** *Medium*, Medium because it impacts enrollment capacity and data collection rate. While important, its connections are less central than other levers. The conflict with `Risk Mitigation Protocol` is notable, but not a primary driver of strategic trade-offs.

### Decision 7: Data Sharing Scope
**Lever ID:** `a7989aed-70db-44e7-ba0c-62068b91574c`

**The Core Decision:** The Data Sharing Scope defines the extent to which collected data is shared with the broader scientific community. It controls the accessibility of the data and influences the potential for collaborations and secondary analyses. Objectives include maximizing scientific impact while minimizing privacy risks. Key success metrics are the number of data requests, the number of publications using the shared data, and the absence of privacy breaches.

**Why It Matters:** Broader data sharing accelerates scientific progress but increases privacy risks. Immediate: Increased data accessibility → Systemic: Enhanced collaboration and reproducibility → Strategic: Greater scientific impact but heightened risk of privacy breaches and reputational damage. Trade-off: Scientific Impact vs. Privacy.

**Strategic Choices:**

1. Restrict data sharing to de-identified physiological data only, minimizing privacy risks but limiting the scope of potential collaborations and secondary analyses.
2. Share de-identified physiological data and limited metadata (e.g., demographics, episode frequency) under strict data use agreements, balancing scientific impact with privacy protection.
3. Publicly release fully de-identified physiological data, metadata, and carefully curated video segments of parasomnia events (with explicit consent and facial blurring), maximizing scientific impact but requiring extensive ethical review and robust privacy safeguards.

**Trade-Off / Risk:** Controls Scientific Impact vs. Privacy. Weakness: The options do not address the potential for re-identification of participants through combined datasets or advanced analytical techniques.

**Strategic Connections:**

**Synergy:** This lever synergizes with `Data Annotation Workflow`. High-quality, well-documented data annotation enhances the value and usability of shared data. A robust annotation workflow is crucial for enabling secondary analyses by other researchers.

**Conflict:** This lever conflicts with `Recruitment Channel Strategy`. Certain recruitment channels (e.g., patient advocacy groups) may impose stricter data privacy requirements, limiting the scope of permissible data sharing, especially regarding video data.

**Justification:** *Medium*, Medium because it affects scientific impact vs. privacy. While important for long-term impact, it's less critical for the initial 3-year project success. The conflict with `Recruitment Channel Strategy` is relevant but not a core tension.

### Decision 8: Data Annotation Workflow
**Lever ID:** `023bbe44-7966-4180-a58c-150b024c69df`

**The Core Decision:** The Data Annotation Workflow lever determines the process for reviewing and scoring polysomnography and sensor data. It controls the number of raters, the level of expert review, and the adjudication process for disagreements. Objectives include achieving high inter-rater reliability, minimizing annotation errors, and maintaining annotation throughput. Key success metrics are inter-rater agreement scores, annotation completion time, and the accuracy of event classification. This lever directly impacts data quality and analysis efficiency.

**Why It Matters:** Faster annotation workflows reduce costs but may compromise inter-rater reliability. Immediate: Reduced annotation time → Systemic: Increased potential for scoring errors and disagreements → Strategic: Impacts the validity and reproducibility of the research findings, potentially undermining the credibility of publications.

**Strategic Choices:**

1. Employ a single rater for initial annotation with spot-checking by a second rater, prioritizing speed and cost-effectiveness over inter-rater reliability.
2. Utilize dual independent raters with adjudication of disagreements, balancing annotation speed with acceptable inter-rater reliability.
3. Implement a multi-rater annotation workflow with expert review of all events, maximizing inter-rater reliability but significantly increasing annotation time and costs.

**Trade-Off / Risk:** Controls Annotation Speed vs. Inter-Rater Reliability. Weakness: The options don't consider incorporating machine learning pre-annotation to improve efficiency.

**Strategic Connections:**

**Synergy:** A dual-rater Data Annotation Workflow enhances the value of the Data Acquisition Intensity Strategy by ensuring that the rich data collected is accurately and reliably interpreted. It also complements the Staffing Coverage Model, as well-trained technicians can provide valuable initial annotations to guide the raters.

**Conflict:** A more rigorous Data Annotation Workflow, such as multi-rater review, increases annotation time and costs, potentially conflicting with budget limitations. This may constrain the Data Sharing Scope if resources for de-identification and data preparation are limited. It may also slow down the publication timeline.

**Justification:** *High*, High because it controls the trade-off between annotation speed and inter-rater reliability, directly impacting the validity and reproducibility of findings (Aim 3). Its synergy with `Data Acquisition Intensity Strategy` and conflict with budget limitations are significant.
