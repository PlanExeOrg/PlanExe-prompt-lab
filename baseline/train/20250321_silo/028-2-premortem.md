A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | Strict social controls will effectively prevent unrest and maintain order within the silo. | Conduct a simulation with a diverse group of participants, exposing them to the planned social controls and monitoring their reactions and stress levels. | The simulation reveals significant dissent, anxiety, or attempts to subvert the control mechanisms among a substantial portion of the participants (>=25%). |
| A2 | The closed-loop life support systems will reliably provide all necessary resources (air, water, food) without significant external inputs for at least 50 years. | Run a long-term simulation of the life support systems, factoring in potential equipment failures, resource depletion rates, and unforeseen environmental changes. | The simulation projects a critical resource shortage (e.g., water, oxygen, arable land) or system failure within the 50-year timeframe. |
| A3 | The silo's location will remain geologically stable and secure from unforeseen natural disasters (e.g., earthquakes, floods) for the duration of the project. | Conduct a comprehensive geological risk assessment, including seismic activity analysis, groundwater level monitoring, and flood risk modeling, for the selected site. | The risk assessment identifies a significant probability (>=10%) of a major natural disaster impacting the silo's structural integrity or operational capacity within the project's lifespan. |
| A4 | The initial population selected for the silo will be adaptable and resilient to the unique challenges of confined living, maintaining social cohesion and productivity. | Administer psychological and sociological assessments to a representative sample of potential candidates, simulating stressful scenarios and evaluating their coping mechanisms and group dynamics. | Assessments reveal a significant proportion (>=30%) of candidates exhibit traits indicative of poor adaptability, high conflict potential, or susceptibility to psychological distress under confinement. |
| A5 | The silo's internal economy will function effectively, providing equitable access to goods and services and incentivizing productivity without creating significant social stratification. | Develop a detailed economic model of the silo, simulating resource allocation, production, and consumption under various scenarios, including potential economic shocks and inequalities. | The economic model projects significant disparities in wealth and access to resources, leading to a Gini coefficient >= 0.4 or a substantial portion of the population (>=20%) falling below a defined poverty line. |
| A6 | External threats (cyberattacks, sabotage) can be effectively mitigated through planned security measures, preventing significant disruption to silo operations or compromise of critical systems. | Conduct a comprehensive penetration test and red team exercise, simulating realistic cyber and physical attacks on the silo's security infrastructure. | The penetration test or red team exercise successfully breaches critical systems (e.g., life support, power grid, security controls), demonstrating a significant vulnerability to external threats. |
| A7 | The silo's internal culture will foster innovation and creativity, leading to continuous improvement and adaptation to unforeseen challenges. | Establish a baseline measurement of innovation output (e.g., patents filed, new processes implemented) and regularly survey inhabitants on their perceived opportunities for creative expression and problem-solving. | Innovation output remains stagnant or declines over a sustained period (>=1 year), and surveys reveal widespread dissatisfaction with the silo's creative environment. |
| A8 | The silo's physical infrastructure will be resilient to long-term wear and tear, requiring only routine maintenance and preventing catastrophic failures. | Develop a detailed predictive maintenance model for all critical infrastructure components, factoring in material degradation rates, environmental conditions, and potential failure modes. | The predictive maintenance model projects a significant probability (>=20%) of a catastrophic infrastructure failure (e.g., structural collapse, life support system breakdown) within the silo's projected lifespan. |
| A9 | The silo's inhabitants will maintain a strong sense of community and shared purpose, preventing social fragmentation and ensuring collective action in times of crisis. | Regularly assess social cohesion through surveys, focus groups, and analysis of community participation rates, monitoring for signs of social fragmentation and declining collective efficacy. | Social cohesion scores decline below a critical threshold (e.g., 70 out of 100), and participation rates in community initiatives decrease significantly (>=30%). |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Resource Rationing Riot | Process/Financial | A2 | Resource Management Director | CRITICAL (20/25) |
| FM2 | The Subterranean Shift | Technical/Logistical | A3 | Head of Engineering | CRITICAL (15/25) |
| FM3 | The Echo Chamber Rebellion | Market/Human | A1 | Social Control Administrator | CRITICAL (20/25) |
| FM4 | The Factional Feud | Process/Financial | A4 | Social Systems and Governance Planner | CRITICAL (20/25) |
| FM5 | The Automation Autocracy | Technical/Logistical | A5 | Resource Management Director | CRITICAL (15/25) |
| FM6 | The Ghost in the Machine | Market/Human | A6 | Security Systems Engineer | CRITICAL (15/25) |
| FM7 | The Innovation Ice Age | Process/Financial | A7 | Social Systems and Governance Planner | CRITICAL (16/25) |
| FM8 | The Concrete Cancer | Technical/Logistical | A8 | Head of Engineering | CRITICAL (15/25) |
| FM9 | The Silent Spring | Market/Human | A9 | Social Systems and Governance Planner | CRITICAL (20/25) |


### Failure Modes

#### FM1 - The Resource Rationing Riot

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A2
- **Owner**: Resource Management Director
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The closed-loop life support systems, while initially functional, suffer from unforeseen inefficiencies and equipment failures. This leads to a gradual depletion of critical resources like potable water and arable land. Centralized rationing, intended to equitably distribute dwindling supplies, is perceived as unfair and inadequate by a growing segment of the population. Black markets emerge, further exacerbating inequalities and fueling resentment. The Ethical Oversight Committee, lacking real power, is unable to address the growing discontent. The situation escalates when a major water purification system fails, triggering widespread panic and a violent riot. The silo's security forces are overwhelmed, and the central control center is seized. The carefully planned social order collapses, leading to chaos and further resource depletion.

##### Early Warning Signs
- Potable water reserves drop below 75% of capacity.
- Arable land productivity decreases by more than 10% in a single quarter.
- Black market activity, as measured by internal security reports, increases by 50% in a month.

##### Tripwires
- Potable water reserves <= 50% of capacity.
- Arable land productivity <= 70% of initial levels.
- Reports of food hoarding increase by >= 100% in 1 week.

##### Response Playbook
- Contain: Immediately activate emergency water reserves and implement stricter rationing protocols.
- Assess: Conduct a comprehensive audit of the life support systems to identify the root cause of the resource depletion.
- Respond: Implement emergency repairs to the water purification system and explore alternative water sources (e.g., deep groundwater reserves).


**STOP RULE:** Life support systems are deemed irreparable, and critical resource reserves (water, oxygen, food) are projected to be depleted within 6 months.

---

#### FM2 - The Subterranean Shift

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A3
- **Owner**: Head of Engineering
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
Despite initial geological surveys, an unforeseen fault line shifts beneath the silo. This causes structural damage to the lower levels, compromising the integrity of the power generation and waste management systems. The power grid fails, plunging large sections of the silo into darkness. The waste management system malfunctions, leading to a buildup of toxic gases and biohazards. The internal transportation system is disrupted, hindering access to essential resources and emergency services. The silo's inhabitants are trapped in the damaged sections, facing dwindling air supplies and increasing exposure to hazardous materials. Rescue efforts are hampered by the structural instability and the lack of power. The situation deteriorates rapidly, leading to widespread panic and loss of life.

##### Early Warning Signs
- Seismic activity near the silo increases by 50% compared to historical averages.
- Structural stress sensors in the lower levels register readings exceeding established thresholds.
- Power grid stability, as measured by voltage fluctuations, decreases by 20%.

##### Tripwires
- Seismic activity >= 6.0 on the Richter scale within 50km of the silo.
- Structural stress readings >= 90% of design limits in critical support structures.
- Power grid instability leads to >= 24 hours of rolling blackouts.

##### Response Playbook
- Contain: Immediately activate emergency power systems and seal off the damaged sections of the silo.
- Assess: Conduct a thorough structural assessment to determine the extent of the damage and the stability of the remaining sections.
- Respond: Implement emergency repairs to the power grid and waste management systems, prioritizing the restoration of essential services.


**STOP RULE:** Structural damage is deemed irreparable, and the silo is at risk of collapse, making evacuation impossible.

---

#### FM3 - The Echo Chamber Rebellion

- **Archetype**: Market/Human
- **Root Cause**: Assumption A1
- **Owner**: Social Control Administrator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The strict social controls and information restrictions, intended to maintain order, create an oppressive atmosphere within the silo. The population becomes increasingly isolated and disillusioned, questioning the official narratives and yearning for contact with the outside world. A charismatic leader emerges, challenging the authority of the central control center and advocating for greater freedom and transparency. An underground network of dissidents forms, using clandestine communication channels to spread their message and organize resistance. The central control center attempts to suppress the rebellion, but its efforts are met with widespread defiance. A social media campaign, using smuggled devices, exposes the silo's oppressive conditions to the outside world, generating negative publicity and undermining stakeholder confidence. The rebellion escalates, leading to violent clashes between the dissidents and the security forces. The silo's social order collapses, and the project is abandoned.

##### Early Warning Signs
- Reports of depression and anxiety among the population increase by 30% compared to baseline levels.
- Participation in officially sanctioned social activities decreases by 40%.
- Detection of unauthorized communication networks increases by 60%.

##### Tripwires
- Public demonstrations involve >= 10% of the silo's population.
- Sabotage of critical infrastructure increases by >= 50% in 1 month.
- Smuggled communications reach >= 10,000 external recipients.

##### Response Playbook
- Contain: Immediately implement stricter security measures and attempt to identify and isolate the rebellion's leaders.
- Assess: Conduct a thorough review of the social control policies and their impact on the population's well-being.
- Respond: Initiate a dialogue with the dissidents, offering concessions and reforms to address their grievances and restore social order.


**STOP RULE:** The central control center loses control of the silo, and social order cannot be restored through negotiation or compromise.

---

#### FM4 - The Factional Feud

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A4
- **Owner**: Social Systems and Governance Planner
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The initial population, carefully selected for their skills and compatibility, unexpectedly fractures along pre-existing ideological and cultural lines. Minor disagreements over resource allocation and social policies escalate into heated disputes, fueled by the confined environment and limited opportunities for external interaction. The Ethical Oversight Committee, struggling to mediate the conflicts, is accused of bias by various factions. Productivity declines as individuals prioritize factional loyalty over their assigned tasks. The internal economy stagnates, and black markets flourish, further exacerbating inequalities and fueling resentment. The silo's leadership, paralyzed by the infighting, is unable to address the growing crisis. The situation culminates in a violent confrontation between rival factions, resulting in significant damage to infrastructure and loss of life.

##### Early Warning Signs
- Internal surveys reveal a sharp decline in trust and cooperation among different groups within the silo.
- Reports of harassment and discrimination based on ideological or cultural affiliation increase by 50% in a month.
- Attendance at community events and social gatherings decreases by 40%.

##### Tripwires
- Violent incidents between rival factions occur >= 3 times in 1 week.
- Productivity in critical sectors (e.g., agriculture, power generation) declines by >= 20% due to factional disputes.
- The Ethical Oversight Committee is unable to resolve >= 75% of reported disputes within 1 month.

##### Response Playbook
- Contain: Immediately implement stricter security measures and separate the warring factions.
- Assess: Conduct a thorough investigation into the root causes of the factionalism and the effectiveness of the existing conflict resolution mechanisms.
- Respond: Implement a comprehensive reconciliation program, including facilitated dialogues, cultural exchange initiatives, and revised social policies to promote inclusivity and cooperation.


**STOP RULE:** The factional conflict escalates to a civil war, threatening the silo's structural integrity and the survival of its inhabitants.

---

#### FM5 - The Automation Autocracy

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A5
- **Owner**: Resource Management Director
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The silo's internal economy, heavily reliant on automation and centralized control, becomes increasingly unequal. A small elite, possessing specialized technical skills and access to advanced resources, accumulates disproportionate wealth and power. The majority of the population, relegated to menial tasks or rendered unemployed by automation, struggles to meet their basic needs. The Ethical Oversight Committee, dominated by the elite, fails to address the growing inequalities. Social unrest simmers beneath the surface, fueled by resentment and a sense of injustice. A group of disgruntled workers, possessing technical expertise, sabotages the automated systems, disrupting resource allocation and causing widespread shortages. The silo's leadership responds with harsh repression, further alienating the population and escalating the conflict. The internal economy collapses, leading to widespread poverty and social breakdown.

##### Early Warning Signs
- The Gini coefficient, measuring income inequality, exceeds 0.4.
- Unemployment rate among non-technical workers exceeds 20%.
- Reports of food insecurity and lack of access to essential services increase by 40%.

##### Tripwires
- The Gini coefficient exceeds 0.5.
- Unemployment rate among non-technical workers exceeds 30%.
- Widespread looting and theft of essential resources occur.

##### Response Playbook
- Contain: Immediately implement emergency resource distribution measures and increase security patrols to prevent further sabotage.
- Assess: Conduct a thorough review of the internal economic policies and the impact of automation on employment and income inequality.
- Respond: Implement a universal basic income program, invest in retraining and education programs for displaced workers, and revise the economic policies to promote greater equity and opportunity.


**STOP RULE:** The internal economy collapses completely, and the silo is unable to provide basic necessities for its inhabitants.

---

#### FM6 - The Ghost in the Machine

- **Archetype**: Market/Human
- **Root Cause**: Assumption A6
- **Owner**: Security Systems Engineer
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
Despite robust cybersecurity measures, a sophisticated external hacking group breaches the silo's security systems. They gain control of critical infrastructure, including the life support systems, power grid, and internal communication network. The hackers demand a ransom, threatening to shut down the silo's essential services if their demands are not met. The silo's leadership, facing a desperate situation, attempts to negotiate with the hackers, but their efforts are unsuccessful. The hackers begin to manipulate the silo's systems, spreading misinformation, disrupting resource allocation, and sowing discord among the population. Panic ensues as the silo's inhabitants realize they are at the mercy of an external force. The hackers ultimately shut down the life support systems, leading to widespread suffocation and death.

##### Early Warning Signs
- Detection of unauthorized access attempts to critical systems increases by 100% in a week.
- Unexplained system malfunctions and data corruption occur with increasing frequency.
- Internal communication channels are disrupted by spam and misinformation.

##### Tripwires
- Critical systems (e.g., life support, power grid) are taken offline by external actors.
- Sensitive data is leaked to the outside world.
- The silo's leadership is unable to communicate with the population due to compromised communication systems.

##### Response Playbook
- Contain: Immediately isolate the compromised systems and activate backup control mechanisms.
- Assess: Conduct a thorough forensic analysis to identify the source of the breach and the extent of the damage.
- Respond: Implement emergency protocols to restore essential services and communicate accurate information to the population.


**STOP RULE:** The silo's critical systems are irreparably compromised, and the safety of its inhabitants cannot be guaranteed.

---

#### FM7 - The Innovation Ice Age

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A7
- **Owner**: Social Systems and Governance Planner
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The silo's internal culture, initially vibrant and innovative, gradually stagnates due to a combination of factors: rigid social controls, limited access to external information, and a lack of incentives for creative risk-taking. The Ethical Oversight Committee, prioritizing stability over experimentation, discourages unconventional ideas. The internal economy, focused on efficiency and resource conservation, fails to reward innovation. The silo's inhabitants, feeling stifled and uninspired, lose their motivation to improve existing systems or develop new solutions. The silo becomes increasingly reliant on outdated technologies and processes, making it vulnerable to unforeseen challenges and external threats. The lack of innovation ultimately undermines the silo's long-term sustainability and adaptability.

##### Early Warning Signs
- The number of new patents or process improvements originating from within the silo declines by 50% in a year.
- Surveys reveal that >= 60% of inhabitants feel their creative potential is not being utilized.
- Funding for research and development projects is consistently underutilized.

##### Tripwires
- Innovation output (patents, process improvements) <= 1 per year.
- Employee satisfaction with opportunities for creativity <= 40% on a 100-point scale.
- R&D budget utilization <= 50%.

##### Response Playbook
- Contain: Immediately review and revise the social control policies to promote greater freedom of expression and intellectual exchange.
- Assess: Conduct a thorough audit of the internal economic incentives and their impact on innovation.
- Respond: Establish a dedicated innovation fund, provide access to external knowledge resources, and create a culture that rewards creative risk-taking.


**STOP RULE:** The silo's innovation output reaches zero, and there is no prospect of reversing the decline.

---

#### FM8 - The Concrete Cancer

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Head of Engineering
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
Unforeseen chemical reactions within the concrete used to construct the silo's structural supports lead to a gradual degradation of the material, a phenomenon known as 'concrete cancer'. This weakens the silo's structural integrity, making it vulnerable to seismic activity and other external stresses. The predictive maintenance model, based on incomplete data and flawed assumptions, fails to accurately forecast the rate of degradation. Routine maintenance efforts are insufficient to address the underlying problem. The silo's leadership, unaware of the impending crisis, continues to operate as usual. A major earthquake strikes the region, causing catastrophic damage to the silo's structural supports. The silo collapses, burying its inhabitants and destroying its essential systems.

##### Early Warning Signs
- Structural stress sensors register readings exceeding established thresholds.
- Visual inspections reveal cracks and spalling in the concrete supports.
- The rate of concrete degradation, as measured by core samples, exceeds predicted levels.

##### Tripwires
- Structural stress readings >= 80% of design limits in critical support structures.
- The area of visible concrete damage increases by >= 20% in 1 month.
- The rate of concrete degradation exceeds the predicted rate by >= 50%.

##### Response Playbook
- Contain: Immediately implement emergency shoring measures to reinforce the weakened structural supports.
- Assess: Conduct a thorough structural assessment to determine the extent of the damage and the remaining lifespan of the silo.
- Respond: Implement a comprehensive repair program, replacing the degraded concrete with more durable materials and reinforcing the remaining structure.


**STOP RULE:** The structural damage is deemed irreparable, and the silo is at imminent risk of collapse.

---

#### FM9 - The Silent Spring

- **Archetype**: Market/Human
- **Root Cause**: Assumption A9
- **Owner**: Social Systems and Governance Planner
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
Over time, the silo's inhabitants, isolated from the outside world and subjected to strict social controls, lose their sense of community and shared purpose. Apathy and cynicism spread throughout the population. Participation in community initiatives declines, and social connections weaken. The Ethical Oversight Committee, lacking popular support, becomes increasingly ineffective. The silo's leadership, out of touch with the needs and concerns of the population, implements increasingly authoritarian measures. A sense of hopelessness pervades the silo, leading to widespread depression and social breakdown. When a major crisis strikes (e.g., a life support system failure), the silo's inhabitants are unable to mobilize a collective response. The silo descends into chaos, and its long-term survival is jeopardized.

##### Early Warning Signs
- Social cohesion scores decline below 70 out of 100.
- Participation rates in community initiatives decrease by 30%.
- Reports of apathy and cynicism increase by 50%.

##### Tripwires
- Social cohesion scores <= 60 out of 100.
- Participation rates in community initiatives <= 50%.
- Suicide rates increase by >= 100% compared to baseline levels.

##### Response Playbook
- Contain: Immediately implement community-building initiatives to foster social connections and a sense of shared purpose.
- Assess: Conduct a thorough review of the social policies and their impact on community well-being.
- Respond: Implement a participatory governance system, empowering the silo's inhabitants to shape their own destiny and address their own needs.


**STOP RULE:** The silo's social fabric unravels completely, and there is no prospect of restoring a sense of community and shared purpose.
