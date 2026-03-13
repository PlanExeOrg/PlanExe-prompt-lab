A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | The supply chain for enhanced-reliability components will remain stable and predictable throughout the project lifecycle. | Contact key suppliers of enhanced-reliability components and request updated lead times and pricing quotes for all critical components. | Any supplier indicates lead times exceeding 6 months or price increases exceeding 15%. |
| A2 | The thermal and vibration testing environment will accurately simulate the conditions experienced in space, allowing for reliable performance predictions. | Compare the planned thermal and vibration test profiles with published data on the actual space environment, focusing on key parameters like temperature ranges, vibration frequencies, and radiation levels. | The planned test profiles deviate by more than 10% from the published data for any critical parameter. |
| A3 | Stakeholders will remain aligned on project goals and priorities throughout the project lifecycle, minimizing the risk of scope creep and conflicting requirements. | Conduct a formal stakeholder alignment workshop to review project goals, priorities, and success metrics, and to identify any potential areas of disagreement or conflicting expectations. | Significant disagreements or conflicting expectations are identified among key stakeholders regarding project goals, priorities, or success metrics. |
| A4 | The selected location (NIST, CU Boulder, Sandia, AFRL, JPL) will have sufficient and consistent access to the required facilities (vacuum chamber, optical tables, etc.) throughout the project duration. | Obtain written confirmation from the selected location guaranteeing access to all required facilities for the duration of the project, including specific time slots and contingency plans for potential conflicts. | The selected location cannot guarantee consistent access to all required facilities, or imposes significant restrictions on their use. |
| A5 | The project team possesses sufficient expertise in all relevant areas (optics, thermal, vibration, control systems, etc.) to successfully execute the project without requiring significant external consulting or training. | Conduct a skills gap analysis of the project team, comparing their expertise to the project's technical requirements and identifying any areas where external support may be needed. | The skills gap analysis reveals significant gaps in the team's expertise that cannot be addressed through internal training or mentoring. |
| A6 | The project's reliance on specific software tools (Zemax, ANSYS, MATLAB, etc.) will not be hindered by licensing restrictions, compatibility issues, or unexpected software updates that disrupt workflows. | Verify that the project has valid licenses for all required software tools and that these tools are compatible with the project's hardware and operating systems. Also, assess the potential impact of future software updates on project workflows. | The project lacks valid licenses for any required software tool, or significant compatibility issues or disruptive software updates are identified. |
| A7 | The project's reliance on a Class 4 laser system will not encounter unforeseen regulatory hurdles or stricter safety requirements that necessitate costly design modifications or operational restrictions. | Consult with regulatory agencies and laser safety experts to confirm that the project's laser safety plan meets all current and anticipated regulatory requirements. | Regulatory agencies or laser safety experts identify significant gaps in the project's laser safety plan or anticipate stricter safety requirements that would necessitate costly design modifications or operational restrictions. |
| A8 | The project's data management plan will effectively ensure the integrity, security, and accessibility of all project data throughout the project lifecycle and beyond. | Conduct a comprehensive review of the project's data management plan, focusing on data backup and recovery procedures, access controls, and long-term data storage and archiving. | The data management plan lacks adequate procedures for data backup and recovery, access controls, or long-term data storage and archiving, potentially jeopardizing the integrity, security, or accessibility of project data. |
| A9 | The project's reliance on specific collaboration tools and communication channels will effectively facilitate seamless communication and knowledge sharing among team members, regardless of their location or expertise. | Assess the effectiveness of the project's collaboration tools and communication channels by surveying team members and analyzing communication patterns. | Team members report significant difficulties in communicating or collaborating effectively due to limitations in the project's collaboration tools or communication channels. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Component Crunch Catastrophe | Process/Financial | A1 | Procurement Manager | CRITICAL (20/25) |
| FM2 | The Vacuum Validation Void | Technical/Logistical | A2 | Head of Engineering | CRITICAL (15/25) |
| FM3 | The Shifting Sands of Stakeholder Support | Market/Human | A3 | Project Manager | CRITICAL (15/25) |
| FM4 | The Facility Fiasco | Process/Financial | A4 | Project Manager | CRITICAL (20/25) |
| FM5 | The Expertise Erosion | Technical/Logistical | A5 | Head of Engineering | CRITICAL (15/25) |
| FM6 | The Software Shutdown | Market/Human | A6 | IT Manager | CRITICAL (15/25) |
| FM7 | The Regulatory Red Tape Trap | Process/Financial | A7 | Regulatory Compliance Specialist | CRITICAL (15/25) |
| FM8 | The Data Deluge Disaster | Technical/Logistical | A8 | Data Manager | HIGH (10/25) |
| FM9 | The Communication Breakdown Catastrophe | Market/Human | A9 | Project Manager | CRITICAL (15/25) |


### Failure Modes

#### FM1 - The Component Crunch Catastrophe

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A1
- **Owner**: Procurement Manager
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project's reliance on enhanced-reliability components makes it vulnerable to supply chain disruptions. If the supply chain becomes unstable, component lead times could extend significantly, leading to project delays and increased costs. This could result in a cascade of negative consequences, including missed deadlines, budget overruns, and ultimately, project cancellation.

Specifically, the team assumed a stable supply chain for these specialized parts. However, a confluence of factors – a geopolitical event impacting a key supplier, a surge in demand from other aerospace projects, and a previously unknown manufacturing defect discovered in a batch of components – created a perfect storm. Lead times for critical components stretched from the expected 3 months to over 18 months. Prices skyrocketed, exceeding the allocated budget by 40%. The project was forced to halt fabrication, burning through contingency funds while scrambling for alternative suppliers and redesigning the system to accommodate more readily available (but less reliable) components. The resulting system, cobbled together from inferior parts, failed to meet the required performance targets, leading to project termination.

##### Early Warning Signs
- Key component suppliers report production delays or material shortages.
- Lead times for critical components increase by more than 25%.
- Prices for critical components increase by more than 10%.

##### Tripwires
- Lead time for critical enhanced-reliability component X >= 9 months
- Price of critical enhanced-reliability component Y increases by >= 25%
- Number of critical components on backorder >= 3

##### Response Playbook
- Contain: Immediately freeze all non-essential spending and initiate a project-wide cost reduction exercise.
- Assess: Conduct a thorough assessment of the supply chain situation, identifying alternative suppliers and potential component substitutions.
- Respond: Negotiate with existing suppliers to expedite deliveries, explore alternative component designs, and re-evaluate the project schedule and budget.


**STOP RULE:** The project cannot secure a reliable supply of critical enhanced-reliability components within 12 months and within 150% of the original budget.

---

#### FM2 - The Vacuum Validation Void

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A2
- **Owner**: Head of Engineering
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project hinges on accurately simulating the space environment in a lab setting. If the thermal and vibration testing environment fails to replicate key aspects of space, the validation results will be unreliable, leading to unforeseen performance issues and potential mission failure.

The team meticulously designed thermal and vibration tests, confident they were mirroring space conditions. However, they overlooked a subtle but critical factor: the unique radiation environment of space. The high-energy particles in space caused gradual degradation of the optical coatings, a phenomenon not replicated in the lab's testing chamber. As a result, the system performed flawlessly during ground testing but experienced a significant drop in Strehl ratio within weeks of deployment in space. The mission was compromised, and the project was deemed a failure due to inadequate environmental simulation.

##### Early Warning Signs
- Discrepancies are identified between the planned test profiles and published data on the space environment.
- The testing chamber fails to maintain the required vacuum level or temperature stability.
- Unexpected performance degradation is observed during initial testing.

##### Tripwires
- Deviation between planned thermal test profile and actual space environment >= 15%
- Vacuum level in testing chamber exceeds target by >= 10%
- Unexplained Strehl ratio degradation during initial testing >= 5%

##### Response Playbook
- Contain: Halt all further testing and immediately review the test environment setup.
- Assess: Conduct a detailed analysis of the discrepancies between the test environment and the actual space environment, identifying any missing or inadequately simulated factors.
- Respond: Revise the test environment setup to more accurately simulate space conditions, potentially including the addition of radiation sources or improved vacuum control.


**STOP RULE:** The project cannot create a testing environment that accurately simulates the key environmental factors of space within 6 months and within 125% of the original budget.

---

#### FM3 - The Shifting Sands of Stakeholder Support

- **Archetype**: Market/Human
- **Root Cause**: Assumption A3
- **Owner**: Project Manager
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
Maintaining stakeholder alignment is crucial for project success. If stakeholders' goals and priorities diverge, the project could face scope creep, conflicting requirements, and ultimately, loss of support and cancellation.

Initially, all stakeholders were aligned on the core goal: validating coherent beam combining for space-based communication. However, as the project progressed, a key funding agency shifted its focus to space-based power transmission, demanding significant changes to the project's scope and deliverables. These changes conflicted with the original goals and priorities of other stakeholders, including the engineering team and potential commercial partners. The resulting disagreements led to delays, budget cuts, and ultimately, the project's termination due to a lack of unified support.

##### Early Warning Signs
- Key stakeholders express dissatisfaction with project progress or direction.
- Conflicting requirements or priorities are identified among stakeholders.
- Stakeholder engagement decreases or communication becomes strained.

##### Tripwires
- Stakeholder satisfaction score (measured via survey) <= 3 out of 5
- Number of unresolved stakeholder conflicts >= 2
- Key stakeholder attendance at project meetings drops below 50%

##### Response Playbook
- Contain: Immediately convene a stakeholder alignment meeting to address concerns and clarify project goals.
- Assess: Conduct a thorough assessment of stakeholder needs and priorities, identifying any areas of misalignment or conflicting expectations.
- Respond: Revise the project scope and deliverables to better align with stakeholder needs, potentially through negotiation and compromise.


**STOP RULE:** Key stakeholders withdraw their support for the project, resulting in a loss of funding or resources exceeding 25% of the original budget.

---

#### FM4 - The Facility Fiasco

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A4
- **Owner**: Project Manager
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project's success depends on consistent access to specialized facilities. If access is disrupted, testing schedules could be delayed, leading to cost overruns and ultimately, project failure.

The team selected a location based on its reputation and initial assurances of facility availability. However, they failed to secure a legally binding agreement guaranteeing access. Midway through the project, a higher-priority project commandeered the vacuum chamber for an extended period. The beam-combining validation project was put on hold, incurring significant costs for idle personnel and equipment. Attempts to find alternative facilities proved futile due to the specialized nature of the equipment and the stringent cleanroom requirements. The project was eventually canceled due to insurmountable delays and budget exhaustion.

##### Early Warning Signs
- The selected location reports scheduling conflicts or limitations on facility access.
- Access to critical facilities is delayed or interrupted.
- The project is unable to secure a legally binding agreement guaranteeing facility access.

##### Tripwires
- Scheduled access to vacuum chamber delayed by >= 30 days
- Number of facility access conflicts per month >= 2
- Legal agreement guaranteeing facility access not secured by [Date]

##### Response Playbook
- Contain: Immediately negotiate with the selected location to resolve the facility access conflict.
- Assess: Identify alternative facilities that meet the project's requirements and assess the feasibility of relocating the project.
- Respond: If the facility access conflict cannot be resolved, relocate the project to an alternative facility or re-evaluate the project scope and schedule.


**STOP RULE:** The project cannot secure consistent access to all required facilities within 90 days and within 125% of the original budget.

---

#### FM5 - The Expertise Erosion

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A5
- **Owner**: Head of Engineering
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project's technical complexity requires a team with deep expertise in multiple disciplines. If the team lacks sufficient expertise, critical tasks could be performed inadequately, leading to technical problems and project failure.

The team, initially confident in their collective expertise, underestimated the challenges of integrating the thermal, structural, and optical systems. A critical control systems engineer left the project unexpectedly, and the remaining team members lacked the specialized knowledge to design and implement the complex control algorithms required for beam steering and phasing. Attempts to hire a replacement proved difficult due to the niche skill set required. As a result, the system suffered from instability and poor disturbance rejection, failing to meet the required Strehl ratio targets. The project was ultimately deemed a failure due to a lack of specialized expertise.

##### Early Warning Signs
- Key team members express concerns about their ability to perform required tasks.
- The project experiences difficulty in solving technical problems or meeting performance targets.
- The project is unable to attract or retain qualified personnel.

##### Tripwires
- Skills gap analysis identifies >= 3 critical areas where the team lacks sufficient expertise
- Project fails to meet a key performance target for >= 2 consecutive months
- Turnover rate among key technical personnel exceeds 10%

##### Response Playbook
- Contain: Immediately assess the skills gap within the project team and identify areas where external support is needed.
- Assess: Develop a training plan to address the skills gap or engage external consultants to provide specialized expertise.
- Respond: Implement the training plan or engage external consultants to provide the necessary expertise, potentially re-evaluating the project schedule and budget.


**STOP RULE:** The project cannot acquire the necessary expertise to address critical technical challenges within 6 months and within 125% of the original budget.

---

#### FM6 - The Software Shutdown

- **Archetype**: Market/Human
- **Root Cause**: Assumption A6
- **Owner**: IT Manager
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project's reliance on specific software tools creates a vulnerability to licensing restrictions, compatibility issues, and disruptive software updates. If these issues arise, project workflows could be disrupted, leading to delays and ultimately, project failure.

The team heavily relied on a specific version of Zemax for optical simulations. Unexpectedly, the software vendor announced that the current version would no longer be supported and that a mandatory upgrade was required. The new version, however, proved incompatible with the project's existing hardware and operating systems, requiring a costly and time-consuming upgrade of the entire computing infrastructure. Furthermore, the new version introduced subtle changes to the simulation algorithms, invalidating much of the previously generated data. The project was significantly delayed, and the team struggled to reproduce the original results, leading to uncertainty and ultimately, project termination.

##### Early Warning Signs
- The project receives notice of upcoming software updates or licensing changes.
- The project experiences compatibility issues between software tools and hardware.
- Software updates disrupt project workflows or invalidate existing data.

##### Tripwires
- Notice of mandatory software upgrade received with < 90 days notice
- Compatibility issues identified between software and hardware
- Software update invalidates >= 20% of existing data

##### Response Playbook
- Contain: Immediately assess the impact of the software update or licensing change on project workflows and data.
- Assess: Develop a plan to mitigate the impact, potentially including upgrading hardware, modifying software configurations, or finding alternative software tools.
- Respond: Implement the mitigation plan, potentially re-evaluating the project schedule and budget.


**STOP RULE:** The project cannot resolve critical software compatibility issues or licensing restrictions within 90 days and within 125% of the original budget.

---

#### FM7 - The Regulatory Red Tape Trap

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A7
- **Owner**: Regulatory Compliance Specialist
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project's use of a Class 4 laser system makes it vulnerable to regulatory changes and stricter safety requirements. If unforeseen hurdles arise, costly design modifications and operational restrictions could derail the project.

The team, initially confident in their laser safety plan, failed to anticipate a sudden tightening of regulations regarding high-power laser systems. The regulatory agency mandated the installation of additional safety interlocks, beam enclosures, and personnel training programs, adding significant costs and delays to the project. The team scrambled to comply, but the required modifications proved more complex and time-consuming than anticipated. The project was eventually canceled due to insurmountable regulatory hurdles and budget exhaustion.

##### Early Warning Signs
- Regulatory agencies announce upcoming changes to laser safety regulations.
- The project receives negative feedback from regulatory inspections or audits.
- The project experiences difficulty in obtaining necessary permits or approvals.

##### Tripwires
- New laser safety regulations announced with < 6 months implementation timeframe
- Cost of complying with new regulations exceeds 10% of project budget
- Project fails a regulatory inspection or audit

##### Response Playbook
- Contain: Immediately engage with regulatory agencies to understand the new requirements and negotiate a reasonable compliance timeline.
- Assess: Conduct a thorough assessment of the impact of the new regulations on the project's design, schedule, and budget.
- Respond: Revise the project's laser safety plan and implement the necessary design modifications and operational restrictions, potentially re-evaluating the project scope and schedule.


**STOP RULE:** The project cannot comply with new laser safety regulations within 12 months and within 150% of the original budget.

---

#### FM8 - The Data Deluge Disaster

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Data Manager
- **Risk Level:** HIGH 10/25 (Likelihood 2/5 × Impact 5/5)

##### Failure Story
The project generates vast amounts of data, making effective data management crucial. If the data management plan fails, data integrity could be compromised, leading to inaccurate results and project failure.

The team, initially focused on data collection, neglected data security and long-term archiving. A disgruntled employee, with access to sensitive project data, intentionally corrupted critical simulation files. The team discovered the breach, but the backup and recovery procedures proved inadequate, and much of the corrupted data was irretrievable. The project was significantly delayed, and the team struggled to reconstruct the lost data, leading to uncertainty and ultimately, project termination.

##### Early Warning Signs
- Data backup and recovery procedures fail during testing.
- Unauthorized access to project data is detected.
- Data files become corrupted or inaccessible.

##### Tripwires
- Data loss incident occurs affecting >= 10% of project data
- Unauthorized access to project data detected
- Data backup and recovery procedures fail during testing

##### Response Playbook
- Contain: Immediately isolate the affected data and implement emergency data recovery procedures.
- Assess: Conduct a thorough investigation to determine the cause of the data breach and assess the extent of the damage.
- Respond: Revise the data management plan to improve data security and backup procedures, potentially implementing stricter access controls and more frequent data backups.


**STOP RULE:** The project experiences a catastrophic data loss that cannot be recovered within 3 months and within 125% of the original budget.

---

#### FM9 - The Communication Breakdown Catastrophe

- **Archetype**: Market/Human
- **Root Cause**: Assumption A9
- **Owner**: Project Manager
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
Effective communication and collaboration are essential for project success. If the project's collaboration tools and communication channels fail, team members could become isolated, leading to misunderstandings, errors, and project failure.

The team, initially relying on email and occasional video conferences, failed to establish effective communication channels. A critical design flaw, identified by a junior engineer, was never communicated to the lead optical engineer due to a lack of clear communication protocols. The flaw went undetected until late in the project, requiring a costly and time-consuming redesign. The resulting delays and budget overruns led to stakeholder dissatisfaction and ultimately, project termination.

##### Early Warning Signs
- Team members report difficulties in communicating or collaborating effectively.
- Critical information is not shared among team members.
- Decisions are made without adequate input from relevant stakeholders.

##### Tripwires
- Team satisfaction with communication tools (measured via survey) <= 3 out of 5
- Critical design flaw goes undetected for >= 1 month
- Number of communication-related errors or misunderstandings per month >= 3

##### Response Playbook
- Contain: Immediately implement a project-wide communication protocol, including daily stand-up meetings and regular status reports.
- Assess: Conduct a survey to assess team members' satisfaction with the project's collaboration tools and communication channels.
- Respond: Revise the project's communication plan and implement new collaboration tools or communication channels as needed, potentially providing training to team members on their effective use.


**STOP RULE:** The project cannot establish effective communication and collaboration channels within 3 months, resulting in a significant decline in team morale and productivity.
