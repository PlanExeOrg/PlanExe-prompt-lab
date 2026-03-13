A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | EU and private grants will be readily available to supplement the 10.5 million DKK budget. | Actively apply for relevant EU and private grants and track application success. | Failure to secure any grant funding within the first 6 months of the project. |
| A2 | Digitaliseringsstyrelsen is genuinely open to considering platform-neutral alternatives for AltID. | Schedule a series of meetings with key Digitaliseringsstyrelsen stakeholders to gauge their receptiveness to platform-neutrality proposals. | Consistent pushback or lack of concrete action from Digitaliseringsstyrelsen after multiple meetings, indicating a lack of real interest in platform-neutral alternatives. |
| A3 | The project team possesses sufficient in-house expertise to develop secure and robust technical demonstrators within the allocated budget and timeline. | Conduct a thorough skills gap analysis of the project team and compare it against the demonstrator requirements. | The skills gap analysis reveals critical expertise gaps that cannot be filled within the existing budget and timeline, requiring significant external consulting or scope reduction. |
| A4 | The Danish public will readily adopt and trust platform-neutral digital identity solutions, even if they require slightly more effort or are less integrated with existing platforms. | Conduct user surveys and focus groups to gauge public perception and willingness to adopt platform-neutral solutions. | Survey results indicate widespread reluctance to adopt platform-neutral solutions due to perceived inconvenience, lack of integration, or security concerns. |
| A5 | The legal framework surrounding digital identity in Denmark and the EU will remain stable and supportive of platform-neutrality initiatives throughout the project's duration. | Continuously monitor relevant legal and regulatory developments in Denmark and the EU, seeking expert legal analysis of potential impacts on the project. | Significant legal or regulatory changes occur that explicitly undermine or prohibit platform-neutral approaches to digital identity. |
| A6 | Key project personnel will remain committed and available throughout the entire 24-month project duration. | Implement regular check-in meetings with key personnel to assess their commitment and identify any potential availability issues. | One or more key personnel indicate a high likelihood of leaving the project or significantly reducing their involvement within the next 6 months. |
| A7 | The project's focus on platform neutrality will resonate with and attract support from a diverse range of civil society organizations, including those primarily focused on accessibility and digital inclusion. | Actively engage with accessibility and digital inclusion-focused civil society organizations to gauge their interest in and alignment with the project's goals. | These organizations express limited interest or actively oppose the project, citing concerns about the complexity or potential exclusion of certain user groups. |
| A8 | The technical demonstrators will be readily adaptable and interoperable with a wide range of existing and future digital identity systems and devices, minimizing integration challenges and maximizing their potential impact. | Develop and execute a comprehensive interoperability testing plan, targeting a diverse set of digital identity systems and devices. | The demonstrators prove difficult or impossible to integrate with a significant number of target systems and devices, revealing fundamental interoperability limitations. |
| A9 | The Danish government will maintain a consistent and long-term commitment to promoting digital sovereignty, even in the face of potential pressure from international technology companies or competing policy priorities. | Monitor government statements, policy documents, and legislative actions related to digital sovereignty, seeking clear and consistent support for platform-neutrality initiatives. | The government publicly signals a shift away from prioritizing digital sovereignty or takes actions that directly contradict the project's platform-neutrality goals. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Funding Fiasco | Process/Financial | A1 | Policy and Public-Affairs Coordinator | CRITICAL (20/25) |
| FM2 | The Technical Quagmire | Technical/Logistical | A3 | Head of Engineering | HIGH (12/25) |
| FM3 | The Policy Paralysis | Market/Human | A2 | Permitting Lead | CRITICAL (25/25) |
| FM4 | The Adoption Abyss | Market/Human | A4 | Policy and Public-Affairs Coordinator | CRITICAL (20/25) |
| FM5 | The Regulatory Rollercoaster | Process/Financial | A5 | Regulatory and Compliance Specialist | HIGH (12/25) |
| FM6 | The Talent Drain | Technical/Logistical | A6 | Project Manager | HIGH (10/25) |
| FM7 | The Inclusion Illusion | Market/Human | A7 | Policy and Public-Affairs Coordinator | CRITICAL (15/25) |
| FM8 | The Interoperability Impasse | Technical/Logistical | A8 | Technical Lead | CRITICAL (16/25) |
| FM9 | The Political Pivot | Process/Financial | A9 | Policy and Public-Affairs Coordinator | HIGH (10/25) |


### Failure Modes

#### FM1 - The Funding Fiasco

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A1
- **Owner**: Policy and Public-Affairs Coordinator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project's financial model relies on securing supplemental funding through EU and private grants. If these grants fail to materialize, the project faces severe budget constraints. This leads to scope reductions, delays in demonstrator development, and ultimately, a failure to deliver on key objectives. The lack of funding also impacts the ability to engage effectively with stakeholders and influence procurement decisions. The project becomes a shell of its former self, unable to achieve its goals due to financial starvation.

##### Early Warning Signs
- Grant application success rate < 20%
- Projected expenses exceed available funds by >= 10%
- Contingency funds depleted by >= 50% within the first year

##### Tripwires
- Grant applications rejected for 3 consecutive cycles
- Projected runway <= 6 months without additional funding
- Actual expenses exceed budgeted expenses by >= 15% for 2 consecutive quarters

##### Response Playbook
- Contain: Immediately freeze all non-essential spending.
- Assess: Conduct a thorough review of the project budget and identify potential cost-saving measures.
- Respond: Revise the project scope to align with available funding, prioritizing core objectives and delaying or eliminating less critical activities.


**STOP RULE:** Available funding falls below 50% of the original budget, making it impossible to deliver even a reduced scope.

---

#### FM2 - The Technical Quagmire

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A3
- **Owner**: Head of Engineering
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumes sufficient in-house technical expertise to develop the demonstrators. However, the team lacks critical skills in GrapheneOS, FIDO2, or secure web authentication. This leads to poorly implemented demonstrators with security vulnerabilities and performance issues. The demonstrators fail to showcase the feasibility of platform-neutral alternatives, undermining the project's credibility with technical stakeholders. The project becomes bogged down in technical challenges, unable to deliver functional demonstrators within the allocated timeline and budget.

##### Early Warning Signs
- Demonstrator development timeline slips by >= 30%
- Critical security vulnerabilities identified in code reviews >= 5
- Demonstrator performance metrics fall below acceptable thresholds by >= 20%

##### Tripwires
- Demonstrator development is delayed by >= 6 months
- External security audit identifies >= 10 critical vulnerabilities
- Demonstrator fails to meet minimum performance requirements in testing

##### Response Playbook
- Contain: Halt all demonstrator development and conduct a thorough code review.
- Assess: Identify the root causes of the technical challenges and assess the skills gaps within the team.
- Respond: Secure external consulting expertise to address the skills gaps, refactor the demonstrator code, and implement robust security measures.


**STOP RULE:** Demonstrators cannot be made secure and functional within the remaining budget and timeline, rendering them useless for influencing procurement decisions.

---

#### FM3 - The Policy Paralysis

- **Archetype**: Market/Human
- **Root Cause**: Assumption A2
- **Owner**: Permitting Lead
- **Risk Level:** CRITICAL 25/25 (Likelihood 5/5 × Impact 5/5)

##### Failure Story
The project assumes Digitaliseringsstyrelsen is open to platform-neutral alternatives. However, the agency is resistant to change, prioritizing the status quo and established vendor relationships. The project's advocacy efforts fall on deaf ears, failing to influence AltID procurement decisions. The project loses credibility with stakeholders, and the coalition of support crumbles. The project becomes a political dead end, unable to achieve its policy objectives due to institutional inertia and resistance from key decision-makers.

##### Early Warning Signs
- Digitaliseringsstyrelsen consistently rejects project proposals
- Key Digitaliseringsstyrelsen contacts become unresponsive
- Coalition members express concerns about the project's lack of progress

##### Tripwires
- Digitaliseringsstyrelsen formally rejects the project's platform-neutrality proposals
- Key Digitaliseringsstyrelsen contacts cease communication for >= 30 days
- >= 50% of coalition members withdraw their support

##### Response Playbook
- Contain: Immediately reassess the project's advocacy strategy and identify alternative approaches.
- Assess: Conduct a thorough analysis of Digitaliseringsstyrelsen's priorities and identify potential points of alignment.
- Respond: Revise the project's messaging to better resonate with Digitaliseringsstyrelsen's concerns, explore alternative legal pathways for promoting platform neutrality, and engage with other government agencies or policymakers.


**STOP RULE:** Digitaliseringsstyrelsen explicitly states that it will not consider platform-neutral alternatives for AltID, making it impossible to achieve the project's policy objectives.

---

#### FM4 - The Adoption Abyss

- **Archetype**: Market/Human
- **Root Cause**: Assumption A4
- **Owner**: Policy and Public-Affairs Coordinator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumes public willingness to adopt platform-neutral solutions. However, the Danish public, accustomed to the convenience of existing platform-integrated solutions like MitID, rejects the new alternatives. They perceive them as less user-friendly, more cumbersome, and lacking the seamless integration they've come to expect. This leads to low adoption rates, rendering the project's technical achievements irrelevant. The lack of public support undermines the project's political leverage, making it impossible to influence procurement decisions or shape EU standards. The project becomes a well-intentioned but ultimately futile exercise, failing to achieve its goal of promoting digital sovereignty due to a lack of user buy-in.

##### Early Warning Signs
- User survey results show < 30% willingness to adopt platform-neutral solutions
- Focus group participants express strong preference for existing platform-integrated solutions
- Website traffic and demonstrator usage remain consistently low

##### Tripwires
- Adoption rate of platform-neutral solutions remains below 10% after 12 months
- User satisfaction scores for platform-neutral solutions are >= 2 points lower than for existing solutions (on a 5-point scale)
- Public awareness of platform-neutral solutions remains below 20% after a major marketing campaign

##### Response Playbook
- Contain: Immediately launch a comprehensive user education campaign to highlight the benefits of platform-neutral solutions.
- Assess: Conduct in-depth user research to identify the specific pain points and barriers to adoption.
- Respond: Revise the design and implementation of platform-neutral solutions to address user concerns, prioritizing user-friendliness and seamless integration.


**STOP RULE:** Public adoption of platform-neutral solutions remains below 5% after 18 months, indicating a fundamental lack of user acceptance.

---

#### FM5 - The Regulatory Rollercoaster

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A5
- **Owner**: Regulatory and Compliance Specialist
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumes a stable legal framework. However, unexpected changes in Danish or EU regulations undermine the project's core assumptions. New laws or directives explicitly favor platform-specific solutions or impose burdensome requirements on platform-neutral alternatives. This leads to increased compliance costs, project delays, and potentially the need to completely redesign the technical demonstrators. The regulatory uncertainty also deters potential investors and coalition partners, further jeopardizing the project's financial viability and political support. The project becomes a victim of unforeseen legal obstacles, unable to navigate the shifting regulatory landscape.

##### Early Warning Signs
- New draft regulations are published that contradict the project's platform-neutrality goals
- Key legal experts express concerns about the project's compliance with emerging regulations
- Projected compliance costs increase by >= 20% due to regulatory changes

##### Tripwires
- A new law or directive is enacted that explicitly prohibits platform-neutral approaches to digital identity
- Projected compliance costs exceed the allocated budget by >= 30%
- Legal challenges are filed against the project's platform-neutral solutions

##### Response Playbook
- Contain: Immediately halt all activities that are directly impacted by the regulatory changes.
- Assess: Conduct a thorough legal review to assess the impact of the new regulations on the project.
- Respond: Revise the project's strategy to align with the new regulatory landscape, exploring alternative legal pathways and potentially modifying the technical design of the demonstrators.


**STOP RULE:** New regulations make it legally impossible to implement platform-neutral digital identity solutions in Denmark, rendering the project's core objectives unattainable.

---

#### FM6 - The Talent Drain

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A6
- **Owner**: Project Manager
- **Risk Level:** HIGH 10/25 (Likelihood 2/5 × Impact 5/5)

##### Failure Story
The project assumes key personnel will remain committed. However, the Lead Researcher, Technical Lead, or Policy Coordinator unexpectedly leaves the project due to personal reasons, better job opportunities, or burnout. This leads to a loss of critical expertise, project delays, and a decline in team morale. The project struggles to find suitable replacements, and the remaining team members are overburdened, leading to further delays and a decline in quality. The project becomes a shadow of its former self, unable to deliver on its promises due to a lack of key personnel.

##### Early Warning Signs
- Key personnel express dissatisfaction or burnout
- Key personnel begin interviewing for other positions
- Project deadlines are consistently missed due to personnel shortages

##### Tripwires
- The Lead Researcher, Technical Lead, or Policy Coordinator resigns from the project
- The project is unable to fill a critical personnel vacancy within 3 months
- Team morale scores decline by >= 20% in a team survey

##### Response Playbook
- Contain: Immediately redistribute the responsibilities of the departing personnel to the remaining team members.
- Assess: Conduct a thorough assessment of the skills and experience required to fill the vacancy.
- Respond: Launch an aggressive recruitment campaign to find a suitable replacement, offering competitive compensation and benefits. Consider engaging external consultants to fill the gap temporarily.


**STOP RULE:** The Lead Researcher and Technical Lead both leave the project, and suitable replacements cannot be found within 6 months, making it impossible to deliver the technical demonstrators.

---

#### FM7 - The Inclusion Illusion

- **Archetype**: Market/Human
- **Root Cause**: Assumption A7
- **Owner**: Policy and Public-Affairs Coordinator
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The project assumes broad civil society support. However, accessibility and digital inclusion organizations find the platform-neutral solutions complex and potentially exclusionary for users with disabilities or limited technical skills. They actively oppose the project, arguing it prioritizes abstract principles over practical usability for vulnerable populations. This fractures the coalition, undermines public support, and allows opponents to frame the project as elitist and out-of-touch. The project becomes politically toxic, unable to influence policy or procurement decisions due to a perceived lack of concern for digital inclusion.

##### Early Warning Signs
- Accessibility audits reveal significant usability issues for users with disabilities
- Digital inclusion organizations publicly criticize the project's lack of focus on accessibility
- Coalition members express concerns about the project's potential to exclude certain user groups

##### Tripwires
- Accessibility testing reveals that the demonstrators fail to meet WCAG 2.1 AA standards
- A major digital inclusion organization withdraws its support from the project
- Public opinion polls show a significant decline in support for the project among vulnerable populations

##### Response Playbook
- Contain: Immediately launch a comprehensive accessibility audit and user testing program, involving users with disabilities.
- Assess: Identify the specific accessibility barriers and usability issues that are hindering adoption.
- Respond: Revise the design and implementation of platform-neutral solutions to address accessibility concerns, prioritizing inclusive design principles and providing tailored support for vulnerable users.


**STOP RULE:** The project is unable to address the accessibility concerns raised by digital inclusion organizations, and public support among vulnerable populations remains consistently low, making it impossible to achieve broad adoption.

---

#### FM8 - The Interoperability Impasse

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Technical Lead
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The project assumes easy interoperability. However, the technical demonstrators prove difficult to integrate with existing Danish digital identity systems (MitID, NemID) and a wide range of devices (smartphones, tablets, computers). This is due to incompatible protocols, proprietary interfaces, and a lack of standardization. The demonstrators become isolated prototypes, unable to function seamlessly within the existing digital ecosystem. This limits their practical value, undermines their credibility with stakeholders, and makes it impossible to influence AltID procurement decisions. The project becomes a technological dead end, failing to achieve its goal of promoting platform neutrality due to fundamental interoperability limitations.

##### Early Warning Signs
- Integration testing reveals significant compatibility issues with existing digital identity systems
- Demonstrators fail to function correctly on a wide range of devices
- Developers report significant difficulties in adapting the demonstrators to different platforms

##### Tripwires
- The demonstrators fail to integrate with MitID or NemID after 6 months of effort
- The demonstrators function correctly on less than 50% of target devices
- The project team spends more than 50% of its development time addressing interoperability issues

##### Response Playbook
- Contain: Immediately halt all new feature development and focus exclusively on addressing interoperability issues.
- Assess: Conduct a thorough analysis of the technical barriers to interoperability, identifying incompatible protocols and interfaces.
- Respond: Revise the design of the demonstrators to prioritize interoperability, adopting open standards and developing compatibility layers for existing systems.


**STOP RULE:** The demonstrators cannot be made interoperable with MitID or NemID within the remaining budget and timeline, rendering them useless for influencing AltID procurement.

---

#### FM9 - The Political Pivot

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A9
- **Owner**: Policy and Public-Affairs Coordinator
- **Risk Level:** HIGH 10/25 (Likelihood 2/5 × Impact 5/5)

##### Failure Story
The project assumes consistent government commitment. However, a change in government or a shift in policy priorities leads to a decline in support for digital sovereignty. The government prioritizes other policy goals (economic growth, international relations) over platform neutrality, bowing to pressure from international technology companies. Funding for the project is cut, and Digitaliseringsstyrelsen is instructed to prioritize platform-specific solutions. The project loses its political backing, making it impossible to influence procurement decisions or shape EU standards. The project becomes a casualty of shifting political winds, unable to achieve its goals due to a lack of sustained government support.

##### Early Warning Signs
- Government officials publicly express skepticism about the benefits of platform neutrality
- Funding for digital sovereignty initiatives is reduced in the national budget
- Digitaliseringsstyrelsen announces new policies that favor platform-specific solutions

##### Tripwires
- The government publicly announces a shift away from prioritizing digital sovereignty
- Funding for the project is cut by >= 25%
- Digitaliseringsstyrelsen explicitly endorses platform-specific solutions for AltID

##### Response Playbook
- Contain: Immediately reassess the project's advocacy strategy and identify new political allies.
- Assess: Conduct a thorough analysis of the government's new policy priorities and identify potential points of alignment.
- Respond: Revise the project's messaging to better resonate with the government's current concerns, exploring alternative legal pathways for promoting platform neutrality and engaging with other government agencies or policymakers.


**STOP RULE:** The government explicitly withdraws its support for platform-neutrality initiatives, and funding for the project is eliminated, making it impossible to continue.
