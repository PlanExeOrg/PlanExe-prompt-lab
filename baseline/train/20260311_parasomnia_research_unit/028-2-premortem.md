A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | The local community will be receptive to the establishment and operation of the residential research unit. | Conduct a survey of residents within a 500-meter radius of the proposed facility location to gauge their attitudes towards the project. | More than 25% of surveyed residents express strong opposition to the project due to concerns about noise, traffic, or privacy. |
| A2 | The planned data acquisition methods (PSG, video-EEG, sensors) will consistently capture sufficient parasomnia events to meet the study's objectives. | Conduct a pilot study with 5 participants using the planned data acquisition methods to assess the frequency and quality of captured parasomnia events. | The pilot study captures fewer than 2 adjudicated parasomnia events per participant-night on average. |
| A3 | The project's budget is sufficient to cover all anticipated costs, including facility renovation, equipment procurement, staffing, and participant compensation. | Obtain firm quotes from at least three qualified contractors for the facility renovation work and compare them to the budgeted amount. | The average of the firm quotes exceeds the budgeted amount for facility renovation by more than 15%. |
| A4 | The research team will have access to all necessary equipment and technology without significant delays. | Confirm the availability and delivery timelines of all critical equipment from suppliers. | Any critical equipment is delayed by more than 4 weeks from the expected delivery date. |
| A5 | The project will maintain a high level of participant engagement throughout the study duration. | Conduct a preliminary survey with potential participants to assess their willingness to engage in a residential study. | Less than 60% of surveyed potential participants express a strong interest in participating in the study. |
| A6 | The data analysis methods chosen will be sufficient to extract meaningful insights from the collected data. | Run a pilot analysis on a small subset of collected data to evaluate the effectiveness of the chosen analysis methods. | The pilot analysis fails to yield any significant findings or insights that align with the study's objectives. |
| A7 | The chosen location will remain accessible and suitable for research activities throughout the project's duration. | Investigate potential planned infrastructure projects (road work, construction) near the chosen location that could disrupt access. | Planned infrastructure projects are identified that will significantly restrict access to the facility for more than 2 weeks during the study period. |
| A8 | Participants will accurately and truthfully report their medical history and medication usage. | Compare self-reported medical history with available medical records (with participant consent) for a subset of recruited participants. | Significant discrepancies (e.g., unreported diagnoses, medications) are found in more than 20% of the compared records. |
| A9 | The planned data storage and backup systems will reliably protect against data loss or corruption. | Conduct a simulated data loss event and test the effectiveness of the data recovery procedures. | More than 1% of the total dataset is unrecoverable after the simulated data loss event. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Empty Suites: A Financial Black Hole | Process/Financial | A3 | Principal Investigator | CRITICAL (20/25) |
| FM2 | The Ghost in the Machine: A Data Desert | Technical/Logistical | A2 | Head of Engineering | HIGH (12/25) |
| FM3 | The Silent Treatment: A Community Rejection | Market/Human | A1 | Permitting Lead | MEDIUM (8/25) |
| FM4 | The Empty Suites: A Financial Black Hole | Process/Financial | A3 | Principal Investigator | CRITICAL (20/25) |
| FM5 | The Ghost in the Machine: A Data Desert | Technical/Logistical | A2 | Head of Engineering | HIGH (12/25) |
| FM6 | The Silent Treatment: A Community Rejection | Market/Human | A1 | Permitting Lead | MEDIUM (8/25) |
| FM7 | The Vanishing Data: A Digital Apocalypse | Technical/Logistical | A9 | Data Engineer | HIGH (10/25) |
| FM8 | The Hidden History: A Medical Minefield | Market/Human | A8 | Clinical Psychologist | HIGH (12/25) |
| FM9 | The Impassable Road: A Logistical Nightmare | Process/Financial | A7 | Facility and Safety Manager | HIGH (12/25) |


### Failure Modes

#### FM1 - The Empty Suites: A Financial Black Hole

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A3
- **Owner**: Principal Investigator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project's initial budget underestimated the true cost of renovating the residential facility to meet research standards. Several unforeseen issues arose during the renovation, including the discovery of asbestos, unexpected structural repairs, and the need for specialized soundproofing to minimize noise pollution for the local community. These issues led to significant cost overruns, depleting the contingency fund and forcing the project to make drastic cuts in other areas.  The data engineer position was reduced to half-time, delaying the development of the automated event-triage tools.  Participant compensation was reduced, leading to lower enrollment and higher dropout rates.  Ultimately, the facility was completed, but with only 4 of the planned 8 suites operational. The reduced capacity significantly hampered the project's ability to collect sufficient data, jeopardizing its primary research aims. The lack of automated triage tools meant that the existing data was taking far longer to process, further compounding the problem. The project limped along, burning through its remaining funds without achieving meaningful results.

##### Early Warning Signs
- Renovation costs exceed initial estimates by 10% within the first month.
- The contingency fund is depleted by 50% within the first three months.
- Participant enrollment falls below 50% of the target rate after six months.

##### Tripwires
- Total renovation costs exceed the initial budget by 20%.
- Participant enrollment remains below 60% of the target for two consecutive months.
- The data engineer position remains at half-time for more than 3 months.

##### Response Playbook
- Contain: Immediately freeze all non-essential spending and renegotiate contracts with vendors.
- Assess: Conduct a thorough financial audit to identify areas for cost reduction and explore alternative funding sources.
- Respond: Reduce the scope of the project by focusing on a smaller subset of research questions and scaling back data collection efforts.


**STOP RULE:** The project runs out of funding before collecting sufficient data to address its primary research aims.

---

#### FM2 - The Ghost in the Machine: A Data Desert

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A2
- **Owner**: Head of Engineering
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project's data acquisition methods, while sophisticated, proved inadequate for capturing the elusive nature of NREM parasomnias. The dry-electrode EEG headbands, intended to provide continuous monitoring with minimal participant burden, suffered from poor signal quality due to movement artifacts and inconsistent electrode contact. The contact-free mattress sensors, designed to detect movement patterns, lacked the sensitivity to distinguish between normal sleep movements and subtle parasomnia events. The scheduled enhanced-night PSG sessions, intended to provide high-quality data, often failed to coincide with actual parasomnia episodes. As a result, the project collected vast amounts of noisy and uninformative data, but captured very few genuine parasomnia events. The research team struggled to identify meaningful patterns or triggers, and the development of the automated event-triage tools was hampered by the lack of reliable training data. The project became a data desert, filled with technical complexities but devoid of scientific insights.

##### Early Warning Signs
- The signal-to-noise ratio of the EEG data consistently falls below acceptable levels.
- Fewer than 1 adjudicated parasomnia event is captured per participant-night on average.
- The automated event-triage tools exhibit poor performance in identifying known parasomnia events.

##### Tripwires
- The average signal-to-noise ratio of the EEG data is below 3:1 after three months of data collection.
- The average number of adjudicated parasomnia events captured per participant-night is less than 0.5 after six months.
- The sensitivity of the automated event-triage tools is below 60% on a validated test dataset.

##### Response Playbook
- Contain: Immediately suspend data collection and re-evaluate the data acquisition methods.
- Assess: Conduct a thorough analysis of the collected data to identify the sources of noise and signal degradation.
- Respond: Revise the data acquisition protocols, potentially incorporating more traditional PSG monitoring techniques and increasing the frequency of enhanced-night sessions.


**STOP RULE:** The project fails to capture sufficient parasomnia events to address its primary research aims after one year of data collection.

---

#### FM3 - The Silent Treatment: A Community Rejection

- **Archetype**: Market/Human
- **Root Cause**: Assumption A1
- **Owner**: Permitting Lead
- **Risk Level:** MEDIUM 8/25 (Likelihood 2/5 × Impact 4/5)

##### Failure Story
Despite initial efforts to engage with the local community, the project faced increasing resistance from residents concerned about noise, traffic, and privacy. The residential research unit, located in a quiet neighborhood, generated unexpected levels of noise due to participant movements and equipment operation. Increased traffic from staff and visitors disrupted the neighborhood's tranquility. Residents also expressed concerns about the privacy of participants and the potential for unauthorized access to sensitive data. The community's opposition manifested in complaints to local authorities, negative media coverage, and even protests outside the facility. The project's reputation suffered, making it difficult to recruit participants and secure future funding. The research team found themselves spending more time addressing community concerns than conducting research, and the project ultimately became a victim of its own social environment.

##### Early Warning Signs
- The project receives more than three formal complaints from local residents within the first month.
- Local media outlets publish negative stories about the project.
- Attendance at community meetings declines significantly.

##### Tripwires
- A local residents' association files a formal lawsuit against the project.
- Local media coverage becomes overwhelmingly negative for two consecutive months.
- Participant recruitment rates decline by more than 30% due to community opposition.

##### Response Playbook
- Contain: Immediately suspend all activities that generate excessive noise or traffic.
- Assess: Conduct a thorough assessment of the community's concerns and identify potential solutions.
- Respond: Implement noise reduction measures, improve traffic management, and enhance data privacy protocols to address the community's concerns.


**STOP RULE:** The project is unable to secure the necessary permits to operate due to community opposition.

---

#### FM4 - The Empty Suites: A Financial Black Hole

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A3
- **Owner**: Principal Investigator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project's initial budget underestimated the true cost of renovating the residential facility to meet research standards. Several unforeseen issues arose during the renovation, including the discovery of asbestos, unexpected structural repairs, and the need for specialized soundproofing to minimize noise pollution for the local community. These issues led to significant cost overruns, depleting the contingency fund and forcing the project to make drastic cuts in other areas.  The data engineer position was reduced to half-time, delaying the development of the automated event-triage tools.  Participant compensation was reduced, leading to lower enrollment and higher dropout rates.  Ultimately, the facility was completed, but with only 4 of the planned 8 suites operational. The reduced capacity significantly hampered the project's ability to collect sufficient data, jeopardizing its primary research aims. The lack of automated triage tools meant that the existing data was taking far longer to process, further compounding the problem. The project limped along, burning through its remaining funds without achieving meaningful results.

##### Early Warning Signs
- Renovation costs exceed initial estimates by 10% within the first month.
- The contingency fund is depleted by 50% within the first three months.
- Participant enrollment falls below 50% of the target rate after six months.

##### Tripwires
- Total renovation costs exceed the initial budget by 20%.
- Participant enrollment remains below 60% of the target for two consecutive months.
- The data engineer position remains at half-time for more than 3 months.

##### Response Playbook
- Contain: Immediately freeze all non-essential spending and renegotiate contracts with vendors.
- Assess: Conduct a thorough financial audit to identify areas for cost reduction and explore alternative funding sources.
- Respond: Reduce the scope of the project by focusing on a smaller subset of research questions and scaling back data collection efforts.


**STOP RULE:** The project runs out of funding before collecting sufficient data to address its primary research aims.

---

#### FM5 - The Ghost in the Machine: A Data Desert

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A2
- **Owner**: Head of Engineering
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project's data acquisition methods, while sophisticated, proved inadequate for capturing the elusive nature of NREM parasomnias. The dry-electrode EEG headbands, intended to provide continuous monitoring with minimal participant burden, suffered from poor signal quality due to movement artifacts and inconsistent electrode contact. The contact-free mattress sensors, designed to detect movement patterns, lacked the sensitivity to distinguish between normal sleep movements and subtle parasomnia events. The scheduled enhanced-night PSG sessions, intended to provide high-quality data, often failed to coincide with actual parasomnia episodes. As a result, the project collected vast amounts of noisy and uninformative data, but captured very few genuine parasomnia events. The research team struggled to identify meaningful patterns or triggers, and the development of the automated event-triage tools was hampered by the lack of reliable training data. The project became a data desert, filled with technical complexities but devoid of scientific insights.

##### Early Warning Signs
- The signal-to-noise ratio of the EEG data consistently falls below acceptable levels.
- Fewer than 1 adjudicated parasomnia event is captured per participant-night on average.
- The automated event-triage tools exhibit poor performance in identifying known parasomnia events.

##### Tripwires
- The average signal-to-noise ratio of the EEG data is below 3:1 after three months of data collection.
- The average number of adjudicated parasomnia events captured per participant-night is less than 0.5 after six months.
- The sensitivity of the automated event-triage tools is below 60% on a validated test dataset.

##### Response Playbook
- Contain: Immediately suspend data collection and re-evaluate the data acquisition methods.
- Assess: Conduct a thorough analysis of the collected data to identify the sources of noise and signal degradation.
- Respond: Revise the data acquisition protocols, potentially incorporating more traditional PSG monitoring techniques and increasing the frequency of enhanced-night sessions.


**STOP RULE:** The project fails to capture sufficient parasomnia events to address its primary research aims after one year of data collection.

---

#### FM6 - The Silent Treatment: A Community Rejection

- **Archetype**: Market/Human
- **Root Cause**: Assumption A1
- **Owner**: Permitting Lead
- **Risk Level:** MEDIUM 8/25 (Likelihood 2/5 × Impact 4/5)

##### Failure Story
Despite initial efforts to engage with the local community, the project faced increasing resistance from residents concerned about noise, traffic, and privacy. The residential research unit, located in a quiet neighborhood, generated unexpected levels of noise due to participant movements and equipment operation. Increased traffic from staff and visitors disrupted the neighborhood's tranquility. Residents also expressed concerns about the privacy of participants and the potential for unauthorized access to sensitive data. The community's opposition manifested in complaints to local authorities, negative media coverage, and even protests outside the facility. The project's reputation suffered, making it difficult to recruit participants and secure future funding. The research team found themselves spending more time addressing community concerns than conducting research, and the project ultimately became a victim of its own social environment.

##### Early Warning Signs
- The project receives more than three formal complaints from local residents within the first month.
- Local media outlets publish negative stories about the project.
- Attendance at community meetings declines significantly.

##### Tripwires
- A local residents' association files a formal lawsuit against the project.
- Local media coverage becomes overwhelmingly negative for two consecutive months.
- Participant recruitment rates decline by more than 30% due to community opposition.

##### Response Playbook
- Contain: Immediately suspend all activities that generate excessive noise or traffic.
- Assess: Conduct a thorough assessment of the community's concerns and identify potential solutions.
- Respond: Implement noise reduction measures, improve traffic management, and enhance data privacy protocols to address the community's concerns.


**STOP RULE:** The project is unable to secure the necessary permits to operate due to community opposition.

---

#### FM7 - The Vanishing Data: A Digital Apocalypse

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A9
- **Owner**: Data Engineer
- **Risk Level:** HIGH 10/25 (Likelihood 2/5 × Impact 5/5)

##### Failure Story
The project's reliance on a local NAS for data storage proved to be its Achilles' heel. Despite implementing what were believed to be robust backup procedures, a series of unfortunate events led to catastrophic data loss. A power surge, followed by a simultaneous failure of the primary and backup hard drives, resulted in the irretrievable loss of six months' worth of participant data. The lack of offsite backups and inadequate disaster recovery planning left the project reeling. The lost data included critical EEG recordings, video footage, and sensor data, effectively rendering the affected participant sessions unusable. The development of the event-triage tools was severely hampered, and the project's timeline was thrown into disarray. The research team was forced to scramble to recover what little data remained, but the damage was irreparable. The project became a cautionary tale of the importance of data security and disaster preparedness.

##### Early Warning Signs
- Data backup procedures fail to complete successfully for two consecutive weeks.
- The NAS system experiences frequent errors or performance issues.
- The data recovery procedures have not been tested within the past three months.

##### Tripwires
- More than 5% of the total dataset is flagged as corrupted or unreadable.
- The data backup system fails to operate for more than 24 hours.
- A simulated data recovery test fails to restore the data to a usable state within 48 hours.

##### Response Playbook
- Contain: Immediately shut down the NAS system and prevent any further data writes.
- Assess: Conduct a thorough assessment of the data loss and identify the root causes.
- Respond: Implement a more robust data storage and backup solution, including offsite backups and a comprehensive disaster recovery plan.


**STOP RULE:** More than 25% of the total dataset is permanently lost due to data corruption or system failure.

---

#### FM8 - The Hidden History: A Medical Minefield

- **Archetype**: Market/Human
- **Root Cause**: Assumption A8
- **Owner**: Clinical Psychologist
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project's reliance on self-reported medical history proved to be a critical flaw. Several participants, either intentionally or unintentionally, failed to disclose significant medical conditions or medication usage that could have directly impacted their sleep patterns and parasomnia events. One participant, for example, failed to report a history of nocturnal seizures, leading to misinterpretation of EEG data and potentially endangering the participant's safety. Another participant neglected to mention the use of a sedative medication, confounding the analysis of sleep architecture and event frequency. These hidden medical histories introduced significant bias into the data, making it difficult to draw accurate conclusions about the underlying mechanisms of NREM parasomnias. The research team struggled to disentangle the effects of the undisclosed medical conditions from the genuine parasomnia events, jeopardizing the validity of the study's findings.

##### Early Warning Signs
- Significant discrepancies are found between self-reported medical history and available medical records for a subset of participants.
- Participants exhibit unexpected physiological responses or behaviors during sleep studies.
- The statistical analysis reveals unexplained outliers or anomalies in the data.

##### Tripwires
- More than 30% of participants exhibit significant discrepancies between self-reported medical history and available medical records.
- The number of unexplained outliers in the data exceeds 10% of the total dataset.
- The statistical analysis reveals a significant interaction between undisclosed medical conditions and parasomnia event frequency.

##### Response Playbook
- Contain: Immediately review the medical history of all enrolled participants and compare it with available medical records.
- Assess: Conduct a thorough analysis of the potential impact of undisclosed medical conditions on the collected data.
- Respond: Revise the inclusion/exclusion criteria to exclude participants with certain medical conditions or medication usage, and implement more rigorous screening procedures.


**STOP RULE:** The project is unable to reliably distinguish between genuine parasomnia events and the effects of undisclosed medical conditions, jeopardizing the validity of the study's findings.

---

#### FM9 - The Impassable Road: A Logistical Nightmare

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A7
- **Owner**: Facility and Safety Manager
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project's chosen location, initially deemed ideal due to its proximity to the University Hospital Bonn, became a logistical nightmare due to unforeseen infrastructure projects. A major road construction project, scheduled to last for several months, severely restricted access to the facility, causing significant delays and disruptions. Participants struggled to reach the facility for scheduled monitoring sessions, leading to increased dropout rates and reduced data collection. Staff members faced long commutes and parking difficulties, impacting their morale and productivity. The increased transportation costs strained the project's budget, forcing cuts in other areas. The research team found themselves spending more time navigating traffic and managing logistical challenges than conducting research, and the project's timeline was thrown into disarray. The seemingly ideal location became a major impediment to the project's success.

##### Early Warning Signs
- Construction crews begin mobilizing near the chosen location.
- Traffic congestion near the facility increases significantly.
- Participants report difficulties reaching the facility for scheduled monitoring sessions.

##### Tripwires
- Road construction near the facility restricts access for more than 5 days in a given month.
- Participant attendance rates decline by more than 20% due to transportation difficulties.
- Staff members report a significant increase in commute times and parking difficulties.

##### Response Playbook
- Contain: Immediately explore alternative transportation options for participants and staff, such as shuttle services or ride-sharing programs.
- Assess: Conduct a thorough assessment of the impact of the road construction on the project's timeline and budget.
- Respond: Negotiate with local authorities to minimize the disruption caused by the road construction, and consider relocating the facility to a more accessible location if necessary.


**STOP RULE:** The road construction project renders the chosen location inaccessible for more than 3 months, jeopardizing the project's ability to meet its data collection goals.
