A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | The Danish EPA will grant food-contact reuse certification for the selected Arla cleaning agents within the 4-month timeline (submission April 15th to certification by July 15th). | Immediately submit the full chemical specification and process flow diagram for cleaning agents to the Danish EPA/DFVA via the Regulatory & Compliance Assessor (Expert 6's primary action). | Written confirmation from the EPA/DFVA stating the review timeline exceeds 12 weeks or requires mandatory migration testing protocols beyond the initial submission. |
| A2 | Municipal waste authorities will accept and process 60% of total crate volume under household waste classification without triggering unforeseen waste taxes, gate fees, or capacity restrictions, based on goodwill and narrative framing. | The Stakeholder Integration Manager must present draft SLAs requiring legally binding staffing coefficients and penalty clauses for capacity shortfall to the top 5 target municipalities, verifying classification status with internal legal counsel. | One of the top 5 target municipalities refuses to sign an SLA guaranteeing specific staffing hours or mandates that Arla pre-pays a commercial waste gate fee (exceeding 1.0 DKK/kg) upon crate delivery. |
| A3 | The static 5 DKK charitable donation incentive, despite its low monetary value relative to consumer inconvenience, is sufficient to drive the necessary volume needed to reach 40% recovery target (108,000 crates) without needing budget contingency activation. | The Behavioral Economics Modeler must finalize the elasticity model, and if the variance threshold (>15% deviation from forecast after 6 weeks of Q3) is reached, the Incentive Specialist must immediately draft the authorization paperwork for the DKK 200,000 budget sweep. | Q3 performance audit shows cumulative return volume is 10% below target by August 31st, suggesting the incentive is already deficient, requiring immediate review of the DKK 200,000 contingency deployment trigger. |
| A4 | Arla Procurement's ERP system can seamlessly ingest the 'Ready-to-Deploy Stock Report' (RTSDR) data to automatically offset 2027 production orders without manual intervention or data rejection. | The Procurement & Asset Lifecycle Liaison must conduct a full end-to-end dry-run integration test between the QA Hub reporting protocol and the ERP forecasting module using dummy data. | The ERP system flags >5% of RTSDR data entries as 'invalid format' or requires manual override approval for inventory offsetting during the September 2026 dry-run. |
| A5 | Supermarket store managers will prioritize the allocated crate storage space over core retail merchandising needs during the high-traffic Q4 holiday season, despite the performance-based subsidy structure. | The Stakeholder Integration Manager must secure written acknowledgment from all major retail groups on the escalation path for non-compliance and space reclamation by May 31st. | During the Q2 Pilot or early Q3 rollout, >10% of participating stores report removing crate collection bins to make space for seasonal promotional displays without prior authorization. |
| A6 | Third-party logistics (3PL) providers can maintain the modeled transport cost per crate (≤13 DKK) despite potential Q3/Q4 fuel price volatility and driver shortages in the Danish transport sector. | The Reverse Logistics Lead must finalize 3PL contracts with defined service levels and volume/distance-based cost caps before Q3 scale-up. | 3PL vendors invoke force majeure or fuel surcharge clauses causing the average transport cost per crate to exceed 15 DKK for two consecutive weeks during Q3. |
| A7 | The centralized QA Hub operational staff (27 FTEs) possess the standardized training and resilience necessary to maintain target processing throughput (98% reintroduction rate) despite high stress and potential high contamination volumes. | The QA Operations Lead must conduct a mandatory 3-day stress test simulation immediately following the Q2 pilot, running the hubs at 120% simulated volume under controlled (but realistic) contamination levels. | The resulting throughput efficiency during the stress test drops by >15% from the baseline projection, or Site Manager feedback indicates >20% staff turnover risk due to burnout/stress within the first month of national operation. |
| A8 | The 'Builder Path' decision to pilot a crate-swap model (Option 3 in Logistics Modality) at supermarkets is logistically manageable without interfering with existing Arla supply chain B2B delivery schedules. | The Reverse Logistics Lead must finalize the 3PL contracts to include a mandatory 4-hour buffer on all delivery/collection windows at the top 10 pilot supermarkets to test for schedule compression. | The required decoupling of the deposit/cleaning cycle causes a 24-hour delay in 30% of Arla B2B supply routes during the Q2 pilot, triggering service level breach notifications from retail partners. |
| A9 | The provocative marketing narrative ('Your Garden Furniture is Costing Denmark CO2') will successfully generate at least 50% of the targeted 20 million organic impressions via earned media shareability, rather than triggering brand alienation or regulatory pushback. | The PR Narrative Architect must conduct a final tone-test survey among the general Danish public and the Executive Committee of the Arla Foundation regarding the core messaging before mass deployment. | The negative sentiment score related to the provocative messaging exceeds 30% of total mentions during the first three weeks of the Q2 pilot, requiring the PR Architect to deploy the prepared fallback narrative. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Municipal Gate Fee Catastrophe | Process/Financial | A2 | Stakeholder Integration & Municipal Relations Manager | CRITICAL (20/25) |
| FM2 | The Greenwashing Fallout: Stalled Reuse Pipeline | Technical/Logistical | A1 | Regulatory & Compliance Assessor | CRITICAL (15/25) |
| FM3 | The Incentive Collapse and Narrative Drift | Market/Human | A3 | Incentive & Consumer Compliance Specialist | CRITICAL (20/25) |
| FM4 | The Fuel Price Squeeze | Process/Financial | A6 | Reverse Logistics & QA Operations Lead | CRITICAL (20/25) |
| FM5 | The Digital Black Hole | Technical/Logistical | A4 | Procurement & Asset Lifecycle Liaison | CRITICAL (15/25) |
| FM6 | The Holiday Shelf Wars | Market/Human | A5 | Stakeholder Integration & Municipal Relations Manager | CRITICAL (20/25) |
| FM7 | The Supply Chain Snarl | Technical/Logistical | A8 | Reverse Logistics & QA Operations Lead | CRITICAL (20/25) |
| FM8 | The Tone Deaf Campaign | Market/Human | A9 | Public Engagement & PR Narrative Architect | CRITICAL (20/25) |
| FM9 | The Burnout Bottleneck | Process/Financial | A7 | Reverse Logistics & QA Operations Lead | CRITICAL (16/25) |


### Failure Modes

#### FM1 - The Municipal Gate Fee Catastrophe

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A2
- **Owner**: Stakeholder Integration & Municipal Relations Manager
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
Assumed goodwill regarding municipal crate acceptance failed. Municipal authorities re-classified bulk Arla returns as commercial waste in mid-Q3 due to capacity strain revealed in the initial 60% load. This triggered unexpected gate fees (averaging 1.80 DKK/kg) not accounted for in the logistics budget forecast (1.8M DKK allocation). The initial estimated cost overrun of 100,000 DKK ballooned to 450,000 DKK in the first month of national rollout. This mandatory fee drain eroded the non-donation operational buffer, forcing a 150,000 DKK withdrawal from the contingency budget earmarked for Physical ID contingency, and consequently starved the marketing function, leading to reduced post-Q3 awareness.

##### Early Warning Signs
- Municipal Logistics Negotiator reports >3 formal pushbacks on crate acceptance status during Q2 Pilot.
- Average accrued gate fee cost per 1,000 crates received exceeds 1,500 DKK during the first 4 weeks of Q3.
- No legally binding SLA guaranteeing staffing coefficients (Task ID b8947dc5) is signed by July 31st.

##### Tripwires
- Municipal Gate Fees > 50,000 DKK accrued in Q3.
- Legal Counsel confirms commercial waste classification for >20% of target municipalities.

##### Response Playbook
- Contain: Immediately route 100% of new municipal deliveries to the centralized QA Hubs using the pre-negotiated Tier B 3PL transport contract, pausing municipal collection entirely to stop fee accrual.
- Assess: Financial Controller must calculate the breach cost vs. the remaining discretionary budget. Logistics Lead must immediately assess QA Hub's processing capacity headroom for immediate 60% volume absorbency.
- Respond: Stakeholder Manager must trigger the 'Commercial Uplift' clause in the SLAs, formalizing Arla's intent to pay the municipal gate fee while simultaneously initiating legal action or public narrative framing that shifts responsibility for perceived waste classification onto local authorities.


**STOP RULE:** Accrued, unbudgeted gate fees/taxes at municipal stations exceed 300,000 DKK before October 1st, 2026.

---

#### FM2 - The Greenwashing Fallout: Stalled Reuse Pipeline

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A1
- **Owner**: Regulatory & Compliance Assessor
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The assumption regarding the 4-month EPA certification timeline failed spectacularly. The Danish EPA required extensive external migration testing on the selected cleaning agents post-submission, delaying the final reuse certification until late November 2026, well after the July 15th dependency. Consequently, the QA Hubs, commissioned in mid-July, had to operate for five months solely in a recycling aggregation mode. This meant recovered crates were downcycled, completely negating the 106-tonne CO2 reduction metric. Furthermore, the QA Hub Logistics Lead could not generate a reliable 'Ready-to-Deploy Stock Report' (RTSDR), leading to Procurement maintaining full 2027 ordering levels, incurring 200,000 DKK in unnecessary inventory holding costs and rendering the entire logistics investment inefficient.

##### Early Warning Signs
- Regulatory & Compliance Assessor reports expected certification date slipping past August 30th.
- QA Hubs process > 70% of incoming load through recycling chutes rather than reuse staging bays for 4 consecutive weeks post-Q3 launch.
- Procurement issues a revised 2027 new-crate forecast that shows <10% reduction from baseline.

##### Tripwires
- EPA certification confirmation date slips beyond October 31st, 2026.
- Contracted 3PL logistics costs for downcycling conveyance exceed 15 DKK per crate.

##### Response Playbook
- Contain: Immediately halt all non-certified cleaning operations at the QA Hubs. Isolate all recovered crates into a separate 'Contingent Inventory' zone, clearly segregating them from uncleaned returns.
- Assess: Reverse Logistics Lead must quantify the total volume (crates) in the Contingent Inventory, and the Financial Controller must calculate the maximum storage cost liability until certification is achieved (or a downcycling contract is finalized).
- Respond: The project pivots the narrative aggressively towards 'Investment in Future Circularity' and acknowledges the CO2 delay. The 200,000 DKK previously budgeted for expedited testing is repurposed to subsidize the storage/transfer of the Stranded Inventory to a waste management site until certification is secured.


**STOP RULE:** Reuse certification is not secured by Q1 2027, making the 1.8M DKK logistics investment for cleaning efficiency obsolete for that fiscal year.

---

#### FM3 - The Incentive Collapse and Narrative Drift

- **Archetype**: Market/Human
- **Root Cause**: Assumption A3
- **Owner**: Incentive & Consumer Compliance Specialist
- **Risk Level:** CRITICAL 20/25 (Likelihood 5/5 × Impact 4/5)

##### Failure Story
The static 5 DKK donation incentive proved insufficient to drive the necessary volume, especially in the high-friction municipal channel, validating the Behavioral Economics Modeler's concern. After 6 weeks of Q3 launch, cumulative crate return volume lagged the 40% target by 18%. This directly triggered the authorized DKK 200,000 budget sweep to fund an emergency incentive increase from 5 DKK to 6.50 DKK for Q4. However, the resulting volume spike overcompensated, exhausting the incentive budget unexpectedly early in Q4. This forced the Marketing team to halt the 'Killer Application' QR-code promotion (which required the bonus incentive to function as an active draw) simultaneously with the withdrawal of the increased monetary incentive, causing consumer confusion and a sharp 30% drop in organic social impressions during the crucial year-end period. The narrative drifted entirely from environmental to purely charitable appeal, failing the dual CSR measurement criteria.

##### Early Warning Signs
- Q3 daily return volume averages 15% below forecast for 6 consecutive days before September 15th.
- QR code verification scan success rate drops below 50% during the first 3 weeks of Q3 pilot.
- Social media sentiment analysis reports an increase in consumer complaints citing 'too much effort for 5 DKK'.

##### Tripwires
- Cumulative return volume misses the end-of-September forecast by > 8,000 crates.
- The DKK 200,000 contingency budget is fully committed to incentive uplift before November 15th.

##### Response Playbook
- Contain: Immediately pause media spending on any channel that promotes the 'bonus DKK' tracker within the QR app, ensuring consumers are only driven to the base 5 DKK donation mechanism to conserve remaining budget.
- Assess: Immediately recalculate the projected Q4 return volume based *only* on the base 5 DKK rate and determine the final year-end deficit against the 108,000 crate target. Calculate the total remaining marketing budget available for year-end amplification.
- Respond: PR Architect pivots communication instantly to focus solely on the successful transfer of the *already secured* funds to the Arla Foundation, framing the year as a 'mission achieved' success despite volume shortfall, rather than promising future incentive increases.


**STOP RULE:** Final confirmed crate recovery volume is below 90,000 units by December 31st, 2026, resulting in a net negative ROI against 4M DKK operational spend.

---

#### FM4 - The Fuel Price Squeeze

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A6
- **Owner**: Reverse Logistics & QA Operations Lead
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The assumption regarding stable 3PL transport costs failed due to unforeseen fuel price spikes and driver shortages in Q3. The contracted cost caps were triggered, but the volume of crates moved from municipal stations to centralized hubs was higher than modeled, leading to excess mileage charges. The average cost per recovered crate climbed from 13 DKK to 18 DKK within the first 6 weeks of national rollout. This 5 DKK variance on 100,000 crates consumed an extra 500,000 DKK from the logistics budget, forcing a freeze on marketing spend and reducing the funds available for the contingency incentive sweep.

##### Early Warning Signs
- 3PL vendor issues formal notice of fuel surcharge adjustment in August 2026.
- Average transport cost per crate exceeds 14.50 DKK for 10 consecutive days.
- QA Hub receiving logs show >15% delay in crate intake due to transport backlog.

##### Tripwires
- Average transport cost per crate >= 15 DKK for 2 consecutive weeks.
- Total logistics spend exceeds 1.5M DKK before October 1st, 2026.

##### Response Playbook
- Contain: Immediately activate the 'Decentralized Staging' contingency, holding crates at municipal stations longer to consolidate full truckloads before transport to hubs.
- Assess: Financial Controller must calculate the remaining budget runway assuming the new 18 DKK/crate transport cost and identify immediate cuts in non-essential operational overhead.
- Respond: Reverse Logistics Lead must negotiate an emergency rate freeze with 3PL providers in exchange for extending the contract term into Q1 2027, or switch to a rail-intermodal transport option for long-haul segments.


**STOP RULE:** Total logistics expenditure exceeds 1.9M DKK (breaching the 1.8M allocation + 100k contingency) by November 1st, 2026.

---

#### FM5 - The Digital Black Hole

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A4
- **Owner**: Procurement & Asset Lifecycle Liaison
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The assumption that Procurement's ERP system would accept RTSDR data without friction proved false. The data schema from the QA Hubs did not match the legacy inventory codes in Arla's 2027 forecasting module. As a result, the 'Ready-to-Deploy Stock Report' was rejected by the automated system in September. Procurement, lacking trusted data on recovered stock volume, proceeded with standard new-crate ordering to ensure supply security. This resulted in 'Stranded Inventory' where 50,000 cleaned crates sat in QA hubs while new crates were manufactured, completely negating the CO2 reduction metric and incurring double inventory holding costs.

##### Early Warning Signs
- Procurement Liaison reports >5% data rejection rate during the September 5th dry-run.
- 2027 Production Forecast is published without a line-item deduction for recovered crates.
- QA Hub inventory levels exceed 80% capacity while new crate orders are confirmed.

##### Tripwires
- RTSDR data integration failure rate > 5% in September 2026.
- New crate production orders for Q1 2027 are not reduced by at least 10% by October 15th.

##### Response Playbook
- Contain: Immediately halt all new crate production orders pending manual reconciliation of recovered stock volume.
- Assess: Procurement Liaison must perform a manual audit of the QA Hub inventory vs. ERP requirements to identify the specific data schema mismatch causing rejection.
- Respond: Implement a manual 'Shadow Inventory' ledger approved by Finance to officially offset new orders until the ERP integration patch is deployed, ensuring the CO2 metric is tracked externally if the system fails.


**STOP RULE:** Recovered crates constitute >20% of total inventory but account for 0% reduction in 2027 new production orders by December 31st, 2026.

---

#### FM6 - The Holiday Shelf Wars

- **Archetype**: Market/Human
- **Root Cause**: Assumption A5
- **Owner**: Stakeholder Integration & Municipal Relations Manager
- **Risk Level:** CRITICAL 20/25 (Likelihood 5/5 × Impact 4/5)

##### Failure Story
The assumption that store managers would prioritize crate storage over holiday merchandising failed during the Q4 peak season. Facing pressure to maximize sales per square meter for Christmas promotions, store managers in 30% of locations removed the Arla crate collection bins to create space for high-margin seasonal goods. This drastically reduced consumer visibility and access to return points in the high-visibility supermarket channel (40% of volume). Return volumes dropped by 25% in November, and consumer complaints regarding 'missing bins' spiked on social media, damaging the campaign's momentum and perceived reliability.

##### Early Warning Signs
- Field audits report >10% of stores missing collection bins during October compliance checks.
- Consumer social media mentions regarding 'missing bins' increase by 20% week-over-week.
- Store manager feedback logs indicate conflict between crate space and seasonal display planning.

##### Tripwires
- >10% of participating stores report space removal in October 2026.
- Supermarket channel return volume drops >15% compared to September baseline.

##### Response Playbook
- Contain: Immediately deploy mobile 'Pop-Up Collection' units to the affected high-traffic store parking lots to bypass internal space constraints.
- Assess: Stakeholder Manager must quantify the volume loss per affected store and prioritize re-engagement efforts on the top 20 highest-volume locations.
- Respond: Activate the 'Compliance Floor' penalty clause, withholding the performance subsidy for non-compliant stores and escalating to Retail HQ for mandatory space reinstatement.


**STOP RULE:** Supermarket collection channel volume remains >20% below target for 4 consecutive weeks during Q4 2026.

---

#### FM7 - The Supply Chain Snarl

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Reverse Logistics & QA Operations Lead
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The decision to pilot a crate-swap model at supermarkets (decoupling deposit from reuse cycle) created severe logistical friction. Subcontracted 3PL drivers, attempting to execute the complex crate swap *while* completing standard B2B milk deliveries, could not meet their tight scheduling tolerances. This resulted in a 24-hour delay sequence across 30% of Arla's critical weekly milk supply routes during the Q2 pilot, causing early failure notifications from retail partners regarding frozen goods stock-out. This logistical failure triggered a severe operational conflict, forcing Arla HQ to halt all crate-swap activities immediately, rendering the primary collection mechanism for the 40% supermarket channel non-functional for Q3.

##### Early Warning Signs
- 3PL conveyance partners log >10% delivery variance exceeding 2 hours during the first month of Q2 Pilot.
- Retail Supply Chain Specialist reports 3 or more service level breach notifications from major supermarket groups regarding delayed B2B milk deliveries.
- Pilot Coordinator confirms the crate-swap process adds an average of >15 minutes to the driver's stop time.

##### Tripwires
- >15% of Q2 pilot collection routes report B2B delivery delays exceeding 4 hours.
- Retail partners formally request suspension of the crate swap trial by June 30th.

##### Response Playbook
- Contain: Immediately revert all supermarket collection points to a simple drop-off/sign-in method, suspending the crate-swap mechanism entirely to restore B2B supply chain integrity.
- Assess: Logistics Lead must remap the entire Q3 collection schedule, prioritizing the original 40% volume reduction via mandatory municipal delivery (stressing the now-underfunded municipal channel) and calculating the resulting cost/volume gap.
- Respond: Stakeholder Integration Manager must immediately negotiate temporary financial compensation with retail partners for the operational friction caused during the pilot, while the Logistics team urgently re-evaluates the necessity of Option 1 (pure B2B route reliance) over the failed Option 3 (swap).


**STOP RULE:** If B2B milk delivery delays linked to the crate trial exceed 48 cumulative hours in a single week during Q2.

---

#### FM8 - The Tone Deaf Campaign

- **Archetype**: Market/Human
- **Root Cause**: Assumption A9
- **Owner**: Public Engagement & PR Narrative Architect
- **Risk Level:** CRITICAL 20/25 (Likelihood 5/5 × Impact 4/5)

##### Failure Story
The provocative marketing assumption failed. The core narrative ('Your Garden Furniture is Costing Denmark CO2') triggered immediate backlash, particularly from family demographics targeted by the Arla Foundation messaging. During the Q2 pilot, negative social media sentiment surged, reaching 35% of total mentions, directly conflicting with the positive charitable framing. This backlash was amplified by one major retail partner (Coop Danmark) who refused to display the collateral, citing negative customer feedback. The viral potential was suppressed, resulting in total earned media impressions reaching only 8 million by the end of Q3, far short of the 20 million goal, rendering the low-paid media strategy ineffective and demonstrating that the provocative tone was not culturally resonant enough to overcome the friction of the 5 DKK incentive.

##### Early Warning Signs
- Negative sentiment tracking score exceeds 25% of total tracked mentions during the first two weeks of Q2 pilot.
- One of the three major retail groups publicly distances themselves from specific campaign collateral in writing.
- Earned media coverage volume is <50% of paid media impressions generated during Q2.

##### Tripwires
- Negative sentiment score related to provocative messaging exceeds 30% running average for two consecutive weeks in Q3.
- Public mentions of Arla Foundation association with messaging result in a reported 5% dip in positive brand association scores.

##### Response Playbook
- Contain: Immediately cease all deployment of assets featuring the 'Garden Furniture' visual element. Issue a pre-approved defensive press release redirecting focus entirely to the positive impact of the DKK 5 donation on child nutrition.
- Assess: PR Architect must finalize the tone-test survey results and formally present the pivot strategy to the Arla Foundation liaison for immediate sign-off, ensuring alignment.
- Respond: The narrative shifts 100% to positive social proof ('Heroic Recovery') and charity focus. Marketing budget reallocation is executed to fund promotion of the QR-code tool (as a *digital* way to give more to charity) rather than relying on narrative virality.


**STOP RULE:** Total earned media impressions by end-Q3 are less than 50% of the 20 million target, signaling narrative failure.

---

#### FM9 - The Burnout Bottleneck

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A7
- **Owner**: Reverse Logistics & QA Operations Lead
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The QA Hub staffing model (27 initially contracted FTEs) proved inadequate under sustained operational load. Stress testing during Q2 revealed that while cleaning agents were viable (assuming EPA approval), the manual sorting/inspection process required 30% more labor time per unit than modeled, primarily due to high contamination variability at municipal stations (Risk 1/A2 failure compounding). By Q4, staff exhaustion led to high attrition (25% turnover in one month). This resulted in critical processing bottlenecks, forcing the QA Hubs to operate 24/7 with reduced effective teams, escalating overtime costs by 60,000 DKK monthly, and causing a backlog of uninspected crates. This labor crisis strained the logistics budget and delayed the crucial RTSDR reporting to Procurement.

##### Early Warning Signs
- QA Hub site managers report overtime hours >40% of contracted FTE hours for two consecutive weeks.
- Staff turnover rate exceeds 15% monthly across the three hubs beginning mid-Q3.
- Contamination triage time increases by >25% compared to pilot baseline.

##### Tripwires
- Total accrued overtime costs for QA Hubs exceed 100,000 DKK in Q3.
- QA Hub Site Managers submit formal requests for immediate augmentation of cleaning/sorting contractor headcount.

##### Response Playbook
- Contain: Immediately freeze all intake from the least reliable channel (municipalities, pending A2 resolution) to reduce QA processing queue volume, prioritizing backlog clearance.
- Assess: HR/Logistics Lead must initiate emergency contractor augmentation, approving a 30% temporary lift (9 additional FTEs) using the remaining Logistics contingency fund.
- Respond: QA Operations Lead must review SOPs to identify 2-3 manual triage steps that can be automated via temporary, low-cost fixtures installed on-site, reducing reliance on high-stress manual sorting labor.


**STOP RULE:** Processing backlog (crates awaiting inspection/cleaning) exceeds 15,000 units for more than 10 days, indicating a failure to scale labor capacity effectively.
