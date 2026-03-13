A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | Contractors will consistently meet performance standards and adhere to ethical guidelines. | Review contractor selection criteria and training materials to ensure they adequately address performance and ethics. | Selection criteria lack specific performance metrics or ethical guidelines, or training materials are inadequate. |
| A2 | Vulnerable populations are aware of the cooling centers and perceive them as safe and accessible. | Conduct a survey in high-risk neighborhoods to assess awareness and perceptions of cooling centers. | Survey results indicate low awareness or negative perceptions of cooling centers among vulnerable populations. |
| A3 | Thessaloniki is the optimal location for the pilot program. | Conduct a comparative analysis of Thessaloniki with at least two other potential pilot cities, considering factors like climate data, vulnerable population density, and municipal support. | The comparative analysis reveals that another city is significantly better suited for the pilot program based on key criteria. |
| A4 | Existing municipal ordinances provide sufficient legal basis for all planned program activities. | Conduct a thorough legal review of all relevant municipal ordinances. | The legal review identifies gaps or conflicts in existing ordinances that would impede program implementation. |
| A5 | Local healthcare providers are willing and able to effectively integrate the program into their existing workflows. | Conduct interviews with key healthcare providers to assess their willingness and capacity to participate. | Healthcare providers express significant concerns about workload, data sharing, or integration challenges. |
| A6 | The cost estimates for all program activities are accurate and sufficient. | Obtain updated quotes from suppliers and contractors for all major cost items. | The updated quotes reveal that the total cost of program activities exceeds the allocated budget by more than 10%. |
| A7 | The selected communication channels will effectively reach all segments of the vulnerable population, including those with limited digital literacy or language barriers. | Conduct a pilot test of the communication channels with representatives from different vulnerable groups. | The pilot test reveals that certain segments of the vulnerable population are not effectively reached by the selected communication channels. |
| A8 | The local community will support the establishment and operation of cooling centers in their neighborhoods. | Conduct community meetings in potential cooling center locations to gauge local support. | Significant community opposition arises to the establishment of cooling centers in certain neighborhoods. |
| A9 | The program's interventions will not have unintended negative consequences on the environment or public health. | Conduct an environmental and public health impact assessment of the program's interventions. | The impact assessment identifies potential negative consequences, such as increased energy consumption or air pollution. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Contractor Catastrophe | Process/Financial | A1 | Program Manager | CRITICAL (16/25) |
| FM2 | The Empty Cooling Center Echo | Market/Human | A2 | Community Outreach Coordinator | CRITICAL (15/25) |
| FM3 | The Thessaloniki Trap | Technical/Logistical | A3 | Program Manager | HIGH (10/25) |
| FM4 | The Regulatory Roadblock | Process/Financial | A4 | Program Manager | HIGH (12/25) |
| FM5 | The Healthcare Hesitation | Market/Human | A5 | Healthcare Liaison | CRITICAL (15/25) |
| FM6 | The Budget Black Hole | Technical/Logistical | A6 | Program Manager | CRITICAL (20/25) |
| FM7 | The Lost in Translation Tragedy | Market/Human | A7 | Communications Specialist | CRITICAL (20/25) |
| FM8 | The NIMBY Nightmare | Market/Human | A8 | Community Outreach Coordinator | CRITICAL (15/25) |
| FM9 | The Greenwashing Gambit | Technical/Logistical | A9 | Logistics Coordinator | MEDIUM (8/25) |


### Failure Modes

#### FM1 - The Contractor Catastrophe

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A1
- **Owner**: Program Manager
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The project relies heavily on contractors for outreach and home interventions. If contractors fail to meet performance standards (e.g., due to inadequate training, poor management, or lack of motivation), the project will experience significant delays and cost overruns. This could lead to a reduction in the number of homes reached, a decrease in the quality of interventions, and a failure to meet key performance indicators. The financial impact would include increased contractor fees, rework costs, and potential legal liabilities. The process impact would include delays in project timelines, increased administrative burden, and a loss of stakeholder confidence.

##### Early Warning Signs
- Contractor performance consistently below agreed-upon metrics for 2 consecutive weeks.
- Complaints from residents regarding contractor behavior or quality of work >= 5 per week.
- Invoice discrepancies or unexplained cost increases exceeding 5% of the contracted amount.

##### Tripwires
- Contractor performance scores <= 70% for 2 consecutive months.
- Rework requests due to contractor errors >= 10% of completed interventions.
- Contractor invoices exceed budget by >= 15%.

##### Response Playbook
- Contain: Immediately suspend all new work assignments for the underperforming contractor.
- Assess: Conduct a thorough audit of the contractor's performance, identifying the root causes of the issues.
- Respond: Implement a corrective action plan, which may include retraining, closer supervision, or termination of the contract.


**STOP RULE:** If contractor performance does not improve to acceptable levels within 30 days of implementing the corrective action plan, terminate the contract and find a replacement, even if it means delaying the project.

---

#### FM2 - The Empty Cooling Center Echo

- **Archetype**: Market/Human
- **Root Cause**: Assumption A2
- **Owner**: Community Outreach Coordinator
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
Despite significant investment in establishing cooling centers, vulnerable populations may not utilize them if they are unaware of their existence or perceive them as unsafe, inaccessible, or undesirable. This could be due to inadequate outreach efforts, concerns about safety or hygiene, lack of transportation, or cultural barriers. The market impact would be a failure to reach the target population and reduce heat-related harm. The human impact would be continued suffering and mortality among vulnerable residents, leading to negative publicity and a loss of public trust.

##### Early Warning Signs
- Cooling center utilization rates significantly below projections for the first 2 weeks of operation.
- Negative feedback from community members regarding cooling center location, services, or atmosphere >= 3 per week.
- Low enrollment rates in the program among residents living near cooling centers.

##### Tripwires
- Average daily cooling center attendance <= 20% of projected capacity for 14 consecutive days.
- Negative sentiment expressed in social media or community forums regarding cooling centers >= 10 mentions per week.
- Enrollment rates among residents within 500m of cooling centers <= 5%.

##### Response Playbook
- Contain: Immediately increase outreach efforts in areas surrounding underutilized cooling centers.
- Assess: Conduct focus groups with community members to identify barriers to cooling center utilization.
- Respond: Implement changes to cooling center location, services, or atmosphere based on community feedback, and adjust outreach strategies accordingly.


**STOP RULE:** If cooling center utilization rates do not improve to at least 50% of projected capacity within 60 days of implementing the corrective actions, pivot to a mobile cooling unit strategy or reallocate resources to home interventions.

---

#### FM3 - The Thessaloniki Trap

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A3
- **Owner**: Program Manager
- **Risk Level:** HIGH 10/25 (Likelihood 2/5 × Impact 5/5)

##### Failure Story
Thessaloniki may not be the optimal location for the pilot program due to unforeseen challenges related to climate, infrastructure, or local government support. For example, the city's climate may be less predictable than anticipated, making it difficult to accurately forecast heatwaves and allocate resources effectively. The existing infrastructure may be inadequate to support the program's needs, such as a lack of suitable cooling center locations or unreliable transportation services. The local government may be unwilling or unable to provide the necessary support, such as permits, funding, or personnel. This could lead to delays, cost overruns, and a failure to achieve the program's goals. Logistically, the supply chain for home interventions could be more complex and costly than anticipated due to local regulations or limited availability of materials.

##### Early Warning Signs
- Significant delays in obtaining necessary permits or approvals from local government >= 30 days.
- Unexpected challenges related to climate or infrastructure emerge during the first month of implementation.
- Cost of procuring cooling center equipment or home intervention supplies exceeds budget by >= 10%.

##### Tripwires
- Permit delays exceed 60 days.
- Unforeseen infrastructure limitations require additional investment >= 20% of allocated budget.
- Supply chain disruptions cause delays in delivery of essential equipment >= 45 days.

##### Response Playbook
- Contain: Immediately halt further investment in Thessaloniki and explore alternative pilot locations.
- Assess: Conduct a rapid assessment of the feasibility of continuing the program in Thessaloniki, identifying the specific challenges and potential solutions.
- Respond: If the challenges are insurmountable, pivot to an alternative pilot location or significantly revise the program's scope and objectives.


**STOP RULE:** If the rapid assessment concludes that the program cannot be successfully implemented in Thessaloniki within the allocated budget and timeline, cancel the project and re-evaluate the overall strategy.

---

#### FM4 - The Regulatory Roadblock

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A4
- **Owner**: Program Manager
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumes that existing municipal ordinances provide a sufficient legal basis for all planned activities, including operating cooling centers, conducting outreach, and implementing home interventions. However, if this assumption is false, the project could face significant delays and legal challenges. For example, existing ordinances may not adequately address issues related to liability, permitting, or data privacy. This could lead to increased costs, reduced program scope, and a failure to achieve key performance indicators. The financial impact would include legal fees, fines, and potential rework costs. The process impact would include delays in project timelines, increased administrative burden, and a loss of stakeholder confidence.

##### Early Warning Signs
- Significant delays in obtaining necessary permits or approvals from local government >= 30 days.
- Legal challenges or complaints filed by residents or community groups regarding program activities >= 2 per month.
- Increased scrutiny from regulatory agencies regarding program compliance.

##### Tripwires
- Permit applications rejected by municipal authorities >= 2.
- Legal challenges filed against the program >= 1.
- Regulatory audits identify significant compliance violations >= 3.

##### Response Playbook
- Contain: Immediately halt all activities that are potentially in violation of existing ordinances.
- Assess: Conduct a thorough legal review of all program activities to identify potential compliance issues.
- Respond: Develop a corrective action plan, which may include seeking waivers, amending existing ordinances, or revising program activities to ensure compliance.


**STOP RULE:** If the legal review concludes that the program cannot be implemented in compliance with existing ordinances without significant revisions or waivers, cancel the project and re-evaluate the overall strategy.

---

#### FM5 - The Healthcare Hesitation

- **Archetype**: Market/Human
- **Root Cause**: Assumption A5
- **Owner**: Healthcare Liaison
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project relies on the willingness and ability of local healthcare providers to effectively integrate the program into their existing workflows. However, if this assumption is false, the project could face significant challenges in achieving its health-related goals. For example, healthcare providers may be unwilling to participate due to workload constraints, concerns about data sharing, or lack of training. This could lead to reduced referrals to cooling centers and home interventions, a failure to improve early detection of heat-related illness, and a limited impact on hospital admissions. The market impact would be a failure to reach the target population and improve health outcomes. The human impact would be continued suffering and mortality among vulnerable residents, leading to negative publicity and a loss of public trust.

##### Early Warning Signs
- Low participation rates among healthcare providers in program training sessions <= 20%.
- Reluctance from healthcare providers to share data or integrate program protocols into their workflows >= 3 providers.
- Negative feedback from patients regarding healthcare provider knowledge or support for the program >= 5 per week.

##### Tripwires
- Referrals from healthcare providers to cooling centers or home interventions <= 10% of projected referrals.
- Healthcare providers decline to participate in data sharing agreements >= 5.
- Patient complaints regarding healthcare provider support for the program >= 10.

##### Response Playbook
- Contain: Immediately increase outreach efforts to healthcare providers, addressing their concerns and providing additional support.
- Assess: Conduct focus groups with healthcare providers to identify barriers to program integration.
- Respond: Implement changes to program protocols or training materials based on healthcare provider feedback, and offer incentives for participation.


**STOP RULE:** If healthcare provider participation rates do not improve to at least 50% of projected levels within 60 days of implementing the corrective actions, pivot to alternative strategies for health system coordination or reallocate resources to other program components.

---

#### FM6 - The Budget Black Hole

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A6
- **Owner**: Program Manager
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumes that the cost estimates for all program activities are accurate and sufficient. However, if this assumption is false, the project could face significant financial challenges. For example, the cost of procuring cooling center equipment or home intervention supplies may be higher than anticipated due to inflation, supply chain disruptions, or unforeseen expenses. This could lead to budget overruns, reduced program scope, and a failure to achieve key performance indicators. Logistically, the project may be forced to reduce the number of homes reached, scale back outreach efforts, or delay the implementation of certain activities.

##### Early Warning Signs
- Cost of procuring cooling center equipment or home intervention supplies exceeds budget by >= 10%.
- Unexpected expenses or cost increases emerge during the first month of implementation >= 5% of budget.
- Contractor invoices exceed budget by >= 5%.

##### Tripwires
- Total project expenses exceed budget by >= 15%.
- Cost of key program activities exceeds budget by >= 20%.
- Funding requests for unforeseen expenses are denied by municipal authorities >= 2.

##### Response Playbook
- Contain: Immediately halt all non-essential spending and explore cost-saving measures.
- Assess: Conduct a thorough review of the project budget to identify areas where costs can be reduced.
- Respond: Develop a revised budget that prioritizes essential program activities and reduces or eliminates non-essential activities, and seek additional funding from alternative sources.


**STOP RULE:** If the revised budget cannot be balanced without significantly compromising the program's core objectives, cancel the project and re-evaluate the overall strategy.

---

#### FM7 - The Lost in Translation Tragedy

- **Archetype**: Market/Human
- **Root Cause**: Assumption A7
- **Owner**: Communications Specialist
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumes that the selected communication channels will effectively reach all segments of the vulnerable population, including those with limited digital literacy or language barriers. However, if this assumption is false, the project could fail to reach a significant portion of the target population, leading to underutilization of services and a failure to reduce heat-related harm. For example, relying solely on digital communication channels would exclude elderly residents with limited digital literacy, while failing to translate materials into multiple languages would exclude recent migrants. This could lead to increased mortality and morbidity among these vulnerable groups, as well as negative publicity and a loss of public trust.

##### Early Warning Signs
- Low enrollment rates in the program among residents with limited digital literacy or language barriers <= 10%.
- Feedback from community members indicating that communication materials are difficult to understand or access >= 5 per week.
- Cooling center utilization rates significantly below projections in neighborhoods with high concentrations of residents with limited digital literacy or language barriers <= 20%.

##### Tripwires
- Enrollment rates among digitally illiterate residents <= 5% after 2 months.
- Website traffic from target demographics <= 10% of projected traffic.
- Call center inquiries from non-Greek speakers exceed capacity by >= 20%.

##### Response Playbook
- Contain: Immediately expand communication efforts to include non-digital channels, such as flyers, posters, and community events.
- Assess: Conduct focus groups with residents with limited digital literacy or language barriers to identify the most effective communication channels.
- Respond: Revise communication strategy based on focus group feedback, and allocate additional resources to non-digital channels.


**STOP RULE:** If the revised communication strategy does not significantly improve reach among digitally illiterate or non-Greek speaking residents within 60 days, pivot to a more community-based outreach approach or reallocate resources to other program components.

---

#### FM8 - The NIMBY Nightmare

- **Archetype**: Market/Human
- **Root Cause**: Assumption A8
- **Owner**: Community Outreach Coordinator
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project assumes that the local community will support the establishment and operation of cooling centers in their neighborhoods. However, if this assumption is false, the project could face significant opposition from residents, leading to delays, increased costs, and a failure to establish cooling centers in key locations. For example, residents may be concerned about noise, traffic, or safety issues associated with cooling centers. This could lead to protests, legal challenges, and a loss of community support. The market impact would be a failure to provide accessible cooling centers for vulnerable populations. The human impact would be increased suffering and mortality among vulnerable residents, as well as negative publicity and a loss of public trust.

##### Early Warning Signs
- Significant community opposition arises to the establishment of cooling centers in certain neighborhoods >= 3 neighborhoods.
- Negative media coverage or social media sentiment regarding cooling center locations >= 10 mentions per week.
- Delays in obtaining necessary permits or approvals from local government due to community opposition >= 30 days.

##### Tripwires
- Community petitions against cooling center locations gather >= 100 signatures per location.
- Local government officials express concerns about community opposition >= 2 officials.
- Construction or renovation of cooling center locations is delayed due to protests or legal challenges >= 30 days.

##### Response Playbook
- Contain: Immediately halt further development of cooling centers in neighborhoods facing significant opposition.
- Assess: Conduct community meetings to address residents' concerns and explore potential solutions.
- Respond: Revise cooling center locations or operating procedures based on community feedback, and offer incentives to mitigate negative impacts.


**STOP RULE:** If community opposition remains significant despite mitigation efforts, pivot to alternative cooling strategies, such as mobile cooling units or partnerships with existing community centers.

---

#### FM9 - The Greenwashing Gambit

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A9
- **Owner**: Logistics Coordinator
- **Risk Level:** MEDIUM 8/25 (Likelihood 2/5 × Impact 4/5)

##### Failure Story
The project assumes that the program's interventions will not have unintended negative consequences on the environment or public health. However, if this assumption is false, the project could inadvertently harm the environment or public health, undermining its overall goals. For example, increased energy consumption from cooling centers or home interventions could contribute to air pollution and climate change. The use of certain materials in home interventions could release harmful chemicals into the environment. This could lead to negative publicity, legal challenges, and a loss of public trust. Logistically, the project may face challenges in procuring sustainable materials or managing waste disposal.

##### Early Warning Signs
- Increased energy consumption in cooling centers or homes with interventions exceeds projections by >= 10%.
- Complaints from residents regarding indoor air quality or chemical odors >= 3 per week.
- Negative media coverage or social media sentiment regarding the environmental impact of the program >= 10 mentions per week.

##### Tripwires
- Energy consumption exceeds projected levels by >= 15% for 2 consecutive months.
- Air quality tests in homes with interventions reveal elevated levels of harmful chemicals.
- Waste disposal costs exceed budget by >= 20%.

##### Response Playbook
- Contain: Immediately halt the use of interventions that are suspected of causing negative environmental or public health impacts.
- Assess: Conduct a thorough environmental and public health impact assessment of all program interventions.
- Respond: Revise intervention strategies to minimize negative impacts, and implement mitigation measures, such as using energy-efficient appliances or sustainable materials.


**STOP RULE:** If the environmental and public health impact assessment concludes that the program's interventions are causing significant harm, cancel the project and re-evaluate the overall strategy.
