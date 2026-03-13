A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | The fixed quarterly clay shipment schedule from Denmark will remain reliable despite Arctic winter weather disruptions. | Commission an Arctic shipping risk assessment using historical data from the Danish Maritime Authority (2018–2025) and validate with a live simulation of a 6-week delay scenario. | Historical data shows a 40% probability of >4-week delays during January–March, and the simulation confirms that a 6-week delay would deplete the 50 kg buffer stock, leading to session cancellations. |
| A2 | Passive solar design and thermal mass walls alone can maintain stable indoor conditions under 90% winter occupancy with active kilns. | Conduct a full-scale thermal stress test in December 2025 using IoT sensors and EnergyPlus simulation to measure temperature variance across drying zones. | The test reveals a 7°C variance in drying zones during peak operation, exceeding the ±5°C safety threshold and indicating system failure without additional heating. |
| A3 | Retired artists can serve as reliable backup instructors without formal training, liability coverage, or integration into the core operational framework. | Redesign the volunteer program as a 'Community Teaching Fellowship' with mandatory 12-hour safety certification, liability waivers, and $500,000 insurance coverage, then verify compliance with the National Labour Inspectorate. | The National Labour Inspectorate denies approval due to lack of formal training protocols and unverified liability coverage, rendering the volunteer model non-compliant and legally risky. |
| A4 | The 'Inuit Clay Legacy Project' will attract sufficient community and tourist interest to serve as a flagship event without requiring significant marketing investment. | Conduct a pre-launch survey with 50 local residents and 30 tourists to gauge awareness, perceived cultural relevance, and willingness to participate or attend. | Survey results show that only 25% of locals and 15% of tourists are aware of the project, and less than 40% express interest in attending, indicating insufficient organic traction. |
| A5 | The 'pay-what-you-can' model during winter months will be self-sustaining through summer surpluses and sponsorships without requiring additional subsidies. | Run a pilot program with 10 participants in January 2026, track contributions, and compare actual revenue against projected costs for materials and staffing. | The pilot reveals a 60% participation rate but average contributions are only 30% of the cost per session, resulting in a 180,000 DKK deficit that cannot be covered by summer surpluses alone. |
| A6 | The digital onboarding kit for volunteers and instructors will be effective in ensuring consistent training and compliance across all team members. | Deploy the bilingual (Danish/Greenlandic) onboarding kit to 10 new team members, then conduct a post-training quiz and audit their completion of safety checklists and consent forms. | Post-training quiz scores average 65%, and 40% of participants fail to complete required safety checklists, indicating poor comprehension and inconsistent adherence. |
| A7 | The 'Climate & Craft' public dashboard will enhance visitor engagement and perceived cultural relevance without requiring significant content curation or maintenance. | Deploy the live IoT dashboard at the workshop entrance and track daily visitor interactions, dwell time, and feedback via digital surveys over a 30-day period. | Surveys show that only 12% of visitors engage with the dashboard, average dwell time is under 30 seconds, and 68% report it as 'confusing' or 'irrelevant' to their experience. |
| A8 | The rotating emergency response protocol will be effective in reducing crisis response time by 50% without requiring formal drills or role-specific training. | Conduct a full-scale emergency drill with all staff, measuring response time from alarm activation to evacuation completion and comparing it to pre-drill benchmarks. | The drill reveals an average response time of 9 minutes, exceeding the target of 4.5 minutes, and 45% of staff fail to follow assigned roles due to lack of clarity. |
| A9 | The AI-assisted design tools will be adopted by participants without requiring extensive technical support or cultural context guidance. | Run a pilot with 15 participants using the AI tools for 2 hours, then assess tool usage, error rates, and participant feedback on usability and cultural alignment. | Only 3 participants successfully complete a design, 75% report confusion, and 80% express concern about cultural misrepresentation, indicating poor adoption and ethical risk. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Quarterly Quagmire: When Winter Cuts Off the Clay Pipeline | Process/Financial | A1 | Supply Chain Coordinator | CRITICAL (20/25) |
| FM2 | The Frozen Kiln Crisis: When Passive Design Fails Under Pressure | Technical/Logistical | A2 | Facility Manager | CRITICAL (15/25) |
| FM3 | The Volunteer Void: When Good Intentions Become Legal Landmines | Market/Human | A3 | Safety Officer | CRITICAL (20/25) |
| FM4 | The Silent Launch: When a Flagship Event Fails to Resonate | Process/Financial | A4 | Marketing and Community Engagement Specialist | HIGH (12/25) |
| FM5 | The Winter Shortfall: When Subsidies Can't Cover the Gap | Technical/Logistical | A5 | Financial Analyst | CRITICAL (16/25) |
| FM6 | The Onboarding Mirage: When Training Fails to Stick | Market/Human | A6 | Safety Officer | CRITICAL (16/25) |
| FM7 | The Silent Screen: When Data Fails to Connect | Process/Financial | A7 | Digital Coordinator | HIGH (9/25) |
| FM8 | The Chaotic Evacuation: When Protocols Collapse Under Pressure | Technical/Logistical | A8 | Safety Officer | CRITICAL (20/25) |
| FM9 | The AI Divide: When Technology Alienates Instead of Empowering | Market/Human | A9 | Cultural Liaison | CRITICAL (16/25) |


### Failure Modes

#### FM1 - The Quarterly Quagmire: When Winter Cuts Off the Clay Pipeline

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A1
- **Owner**: Supply Chain Coordinator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumed a fixed quarterly clay shipment from Denmark would ensure uninterrupted supply. However, Arctic winter storms and ice blockages in the Denmark Strait caused a 7-week delay in the April shipment. The 50 kg buffer stock was exhausted within 3 weeks, forcing the workshop to cancel all courses for two consecutive months. This led to a 40% drop in summer tourism revenue (800,000 DKK lost), breach of the 'zero cancellations' KPI, and a 25% decline in local participation. The financial strain forced the team to divert 100,000 DKK from the contingency fund to activate emergency air freight, leaving no reserve for other risks. The crisis eroded trust with Katuaq Cultural Centre, which withdrew its partnership support, further reducing community engagement.

##### Early Warning Signs
- Clay inventory drops below 20 kg for three consecutive days
- Shipment tracking shows delay >14 days beyond scheduled arrival
- Emergency air freight cost exceeds 150,000 DKK for a single shipment

##### Tripwires
- Clay buffer stock < 20 kg for 3+ days
- Shipment delay > 14 days
- Emergency air freight cost > 150,000 DKK

##### Response Playbook
- Contain: Immediately halt all course scheduling and notify all participants of cancellation.
- Assess: Run real-time tracking dashboard to confirm delay duration and calculate buffer depletion rate.
- Respond: Activate pre-negotiated emergency air freight contract and reallocate funds from contingency budget.


**STOP RULE:** If clay buffer stock falls below 10 kg and a shipment delay exceeds 21 days, immediately pivot to a fully digital-only curriculum with remote instruction and suspend physical operations.

---

#### FM2 - The Frozen Kiln Crisis: When Passive Design Fails Under Pressure

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A2
- **Owner**: Facility Manager
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The workshop relied on passive solar design and thermal mass walls to maintain stable conditions during winter. However, during a peak winter session with 14 people and 70% kiln load, the drying zone experienced a 7°C variance, causing clay to freeze at the edges and mold to develop in high-humidity areas. The facility manager attempted to enforce the 'thermal curfew' protocol, but it was insufficient to prevent system overload. Two kilns failed due to thermal stress, and the Nuuk Municipality issued a shutdown order for violating the Health and Safety at Work Act. The repair costs exceeded 120,000 DKK, and the workshop remained closed for 10 days. This disrupted the Instructor Resilience Network, as backup instructors were unable to lead sessions due to unsafe conditions, resulting in a 35% drop in attendance and reputational damage.

##### Early Warning Signs
- Drying zone temperature fluctuates >5°C above or below target
- CO₂ levels exceed 1,000 ppm during peak session
- Humidity in drying zone exceeds 75% for more than 2 hours

##### Tripwires
- Drying zone temperature variance >5°C
- CO₂ levels >1,000 ppm for 2+ hours
- Humidity >75% for 2+ hours

##### Response Playbook
- Contain: Immediately shut down all kilns and evacuate drying zones if temperature variance exceeds 5°C.
- Assess: Deploy IoT sensors to map thermal gradients and identify hot/cold spots in real time.
- Respond: Install low-power radiant heaters in critical zones and revise the EnergyPlus model with updated insulation specs.


**STOP RULE:** If the drying zone temperature variance exceeds 8°C for more than 1 hour during any session, permanently halt all kiln operations until a certified Arctic building engineer certifies the thermal system as safe.

---

#### FM3 - The Volunteer Void: When Good Intentions Become Legal Landmines

- **Archetype**: Market/Human
- **Root Cause**: Assumption A3
- **Owner**: Safety Officer
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project relied on a pool of retired artists as backup instructors, assuming their goodwill would ensure continuity. However, one volunteer instructor, lacking formal training, mishandled a kiln during a session, causing a minor fire that damaged equipment and triggered a panic. The incident exposed the organization’s lack of liability coverage and safety protocols. The injured volunteer filed a claim for 800,000 DKK, and the National Labour Inspectorate launched an investigation into non-compliance with occupational safety laws. The workshop faced a 3-week closure for audit and remediation, and the Inuit Cultural Heritage Council withdrew its endorsement of the Cultural Anchoring Framework. This led to a 40% drop in local participation, a boycott by youth apprenticeship partners, and a loss of funding from two major sponsors who cited 'ethical concerns'. The crisis undermined the entire 'third place' vision and damaged long-term community trust.

##### Early Warning Signs
- Volunteer instructor leads a session without completing safety certification
- Incident log shows untrained staff operating high-risk equipment
- Liability waiver not signed by a volunteer within 48 hours of onboarding

##### Tripwires
- Untrained volunteer operates kiln or hazardous equipment
- Incident log contains unapproved activity by volunteer
- Liability waiver missing for any volunteer

##### Response Playbook
- Contain: Immediately suspend all volunteer-led sessions and isolate the involved individual.
- Assess: Review all volunteer records for training completion, waivers, and insurance status.
- Respond: Replace the volunteer pool with a paid 'Community Teaching Fellowship' program and retrain all staff.


**STOP RULE:** If any volunteer instructor operates high-risk equipment without completing mandatory safety certification, immediately terminate the volunteer program and transition to a fully paid instructor model with verified credentials.

---

#### FM4 - The Silent Launch: When a Flagship Event Fails to Resonate

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A4
- **Owner**: Marketing and Community Engagement Specialist
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project launched the 'Inuit Clay Legacy Project' as its first major public exhibition, assuming it would draw crowds organically. However, due to low awareness and lack of targeted outreach, attendance was only 120 people—far below the projected 500. The event generated minimal media coverage, no social media buzz, and zero sponsorship interest. This failure undermined the workshop's visibility and credibility, leading to a 30% drop in new memberships and a 20% decline in tourist package sales. The financial shortfall forced the cancellation of two planned youth apprenticeship cohorts, damaging long-term engagement goals. The crisis revealed a fundamental flaw in relying on passive community interest rather than active promotion.

##### Early Warning Signs
- Event attendance < 30% of projected capacity
- Social media mentions < 50 in 30 days
- No press coverage from regional outlets

##### Tripwires
- Attendance < 30% of projected
- Social media mentions < 50
- No media coverage within 30 days

##### Response Playbook
- Contain: Cancel all future events tied to the project until a new strategy is developed.
- Assess: Analyze survey data and social listening tools to identify gaps in messaging and audience reach.
- Respond: Launch a targeted digital campaign using local influencers and Katuaq Cultural Centre partnerships.


**STOP RULE:** If the event attendance falls below 25% of projected capacity and generates no media coverage within 30 days, abandon the current branding and pivot to a co-created narrative with elders and artists.

---

#### FM5 - The Winter Shortfall: When Subsidies Can't Cover the Gap

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A5
- **Owner**: Financial Analyst
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The 'pay-what-you-can' model was implemented during winter months, assuming summer surpluses would cover the deficit. However, the pilot revealed that average contributions were only 30% of the cost per session, and sponsorships failed to materialize. The workshop faced a 180,000 DKK shortfall, forcing the team to divert funds from the contingency reserve. This created a ripple effect: reduced open-studio hours, delayed equipment maintenance, and a 25% drop in youth participation. The financial strain also led to staff burnout, increasing absenteeism and undermining the Instructor Resilience Network. The crisis exposed the fragility of relying on unproven revenue models in a high-cost environment.

##### Early Warning Signs
- Average contribution per session < 40% of cost
- Sponsorship commitments not secured 30 days before launch
- Contingency fund balance < 50,000 DKK

##### Tripwires
- Average contribution < 40% of cost
- Sponsorship commitments not secured
- Contingency fund < 50,000 DKK

##### Response Playbook
- Contain: Freeze all non-essential spending and reduce open-studio hours to 3 days per week.
- Assess: Run a full financial simulation to determine the break-even point and funding gap.
- Respond: Introduce tiered pricing with a minimum fee and secure three new sponsorships within 60 days.


**STOP RULE:** If the average contribution per session remains below 35% of cost for two consecutive months, permanently discontinue the pay-what-you-can model and implement a fixed-tier pricing system.

---

#### FM6 - The Onboarding Mirage: When Training Fails to Stick

- **Archetype**: Market/Human
- **Root Cause**: Assumption A6
- **Owner**: Safety Officer
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The digital onboarding kit was deployed to ensure consistent training across all team members, but post-pilot audits revealed serious gaps. Only 60% of participants passed the quiz, and 40% failed to complete required safety checklists. This inconsistency led to multiple near-misses involving kiln operation and dust exposure. One instructor accidentally used incorrect glaze ratios, resulting in a failed batch and wasted materials. The Safety Officer had to spend 15 hours retraining staff, delaying other projects. The incident eroded trust in the training system and highlighted a disconnect between digital content and real-world application. The crisis undermined the entire Instructor Resilience Network and raised concerns about long-term operational sustainability.

##### Early Warning Signs
- Post-training quiz score < 70%
- Safety checklist completion rate < 80%
- Incident log shows repeated training-related errors

##### Tripwires
- Quiz score < 70%
- Checklist completion < 80%
- Repeated training-related incidents

##### Response Playbook
- Contain: Suspend all new hires until onboarding process is revised.
- Assess: Conduct focus groups with new team members to identify pain points in the digital kit.
- Respond: Replace digital-only training with hybrid sessions combining live instruction and interactive modules.


**STOP RULE:** If the post-training quiz score remains below 70% or the safety checklist completion rate stays under 80% for two consecutive pilots, immediately halt all onboarding and revert to in-person, instructor-led training.

---

#### FM7 - The Silent Screen: When Data Fails to Connect

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A7
- **Owner**: Digital Coordinator
- **Risk Level:** HIGH 9/25 (Likelihood 3/5 × Impact 3/5)

##### Failure Story
The 'Climate & Craft' public dashboard was launched as a centerpiece of community engagement, displaying real-time environmental data from IoT sensors. However, after 30 days, visitor engagement remained negligible—only 12% interacted with the screen, and average dwell time was under 30 seconds. Surveys revealed that 68% found the display confusing or irrelevant, and no positive impact on perceived cultural relevance was observed. The project spent 80,000 DKK on development and installation, but the return on investment was zero. This failure undermined the workshop's digital strategy and led to a 20% drop in digital marketing effectiveness. The crisis exposed a fundamental flaw in assuming that raw data alone could drive engagement without narrative framing or user-friendly design.

##### Early Warning Signs
- Dashboard interaction rate < 15%
- Average dwell time < 45 seconds
- Survey feedback cites 'confusing' or 'irrelevant'

##### Tripwires
- Interaction rate < 15%
- Dwell time < 45 seconds
- Negative feedback > 60%

##### Response Playbook
- Contain: Temporarily disable the dashboard and redirect resources to higher-impact initiatives.
- Assess: Conduct user testing with local residents to identify pain points in the interface and messaging.
- Respond: Redesign the dashboard with storytelling elements, bilingual labels, and real-time impact metrics (e.g., 'Today’s kiln saved 15 kWh').


**STOP RULE:** If the dashboard interaction rate remains below 10% for two consecutive months, permanently decommission the system and reallocate funds to physical exhibits.

---

#### FM8 - The Chaotic Evacuation: When Protocols Collapse Under Pressure

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Safety Officer
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The rotating emergency response protocol was implemented as a key safety measure, assuming that clear roles would reduce response time by 50%. However, during a full-scale drill, the average response time was 9 minutes—double the target of 4.5 minutes. Forty-five percent of staff failed to follow assigned roles, leading to confusion, duplicated actions, and delayed evacuation. One instructor attempted to shut down the main power while another tried to activate the fire suppression system, causing a temporary blackout. The incident triggered a Nuuk Municipality audit and forced the workshop to suspend operations for 5 days. The crisis exposed a critical gap between theoretical planning and real-world execution, undermining trust in the Safety Officer and the entire Instructor Resilience Network.

##### Early Warning Signs
- Response time > 6 minutes
- Role confusion in 3+ staff members
- Duplicate actions during drill

##### Tripwires
- Response time > 6 minutes
- Role confusion in 3+ staff
- Duplicate actions during drill

##### Response Playbook
- Contain: Immediately suspend all emergency drills and isolate the affected team members.
- Assess: Conduct a root cause analysis of role assignments and communication breakdowns.
- Respond: Implement a RACI matrix, conduct monthly role-specific drills, and assign a dedicated emergency coordinator.


**STOP RULE:** If the response time exceeds 7 minutes in two consecutive drills, immediately halt all operations until a certified emergency management specialist restructures the protocol.

---

#### FM9 - The AI Divide: When Technology Alienates Instead of Empowering

- **Archetype**: Market/Human
- **Root Cause**: Assumption A9
- **Owner**: Cultural Liaison
- **Risk Level:** CRITICAL 16/25 (Likelihood 4/5 × Impact 4/5)

##### Failure Story
The AI-assisted design tools were introduced as a modern innovation to blend tradition with digital creativity. However, the pilot revealed a stark reality: only 3 out of 15 participants successfully completed a design, and 75% reported confusion. Eighty percent expressed concerns about cultural misrepresentation, fearing that algorithmic patterns might distort sacred Inuit motifs. The tool became a source of frustration rather than empowerment, leading to a 25% drop in participant satisfaction scores. The crisis damaged the workshop's reputation as a culturally respectful space and raised questions about the ethics of integrating AI into Indigenous art. The failure highlighted a disconnect between technological ambition and community values, undermining the Cultural Anchoring Framework.

##### Early Warning Signs
- Tool success rate < 25%
- Participant feedback cites 'confusing' or 'culturally inappropriate'
- Error rate > 50% in design attempts

##### Tripwires
- Success rate < 25%
- Feedback cites 'culturally inappropriate'
- Error rate > 50%

##### Response Playbook
- Contain: Immediately pause all AI tool usage and remove access from public sessions.
- Assess: Conduct focus groups with elders and artists to evaluate cultural risks and usability issues.
- Respond: Rebuild the tool with co-created templates, add cultural context prompts, and require elder approval before any public use.


**STOP RULE:** If the tool success rate remains below 20% or 70% of users report cultural concerns, permanently discontinue the AI feature and revert to traditional design methods.
