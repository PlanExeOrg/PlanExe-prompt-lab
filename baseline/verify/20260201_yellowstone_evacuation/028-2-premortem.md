A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | The public will overwhelmingly comply with evacuation orders, minimizing resistance and maximizing evacuation speed. | Conduct a survey in Yellowstone gateway communities assessing willingness to evacuate under different eruption scenarios and perceived risks. | Survey results indicate that less than 75% of residents express willingness to evacuate promptly, citing concerns about property security or distrust of official information. |
| A2 | The initial budget of $50 million will be sufficient to cover all essential evacuation and immediate response costs. | Develop a detailed cost breakdown for all phases of the evacuation plan, including personnel, equipment, transportation, and sheltering, and compare it to the allocated budget. | The detailed cost breakdown exceeds $65 million, indicating a significant budget shortfall that could compromise essential operations. |
| A3 | Existing inter-agency agreements will ensure seamless coordination and authority transfer between federal, state, and local entities. | Conduct a tabletop exercise involving representatives from all key agencies to simulate authority transfer scenarios and identify potential conflicts or gaps in coordination. | The tabletop exercise reveals significant disagreements or ambiguities regarding roles, responsibilities, or decision-making authority, hindering effective coordination. |
| A4 | Designated evacuation shelters will have sufficient capacity and resources to accommodate all evacuees requiring shelter. | Conduct a detailed assessment of the capacity and resource availability (beds, food, water, medical supplies) at each designated evacuation shelter, comparing it to projected evacuee numbers. | The assessment reveals that total shelter capacity is less than 80% of projected evacuee numbers, or that critical resources are insufficient to meet basic needs for more than 48 hours. |
| A5 | The power grid will remain functional long enough to support critical infrastructure (hospitals, communication centers) during the initial evacuation phase. | Analyze historical data on power grid performance during seismic events and ashfall, and assess the vulnerability of key substations and transmission lines to these hazards. | The analysis indicates a high probability (>= 60%) of widespread power outages within the first 24 hours of the eruption, or that critical substations lack adequate backup power systems. |
| A6 | Sufficient numbers of first responders (medical personnel, law enforcement, firefighters) will be available to support the evacuation and initial response efforts. | Survey local and regional first responder agencies to assess their available personnel and equipment, and compare it to projected needs during the evacuation and initial response. | The survey reveals a significant shortfall (>= 30%) in available first responders, or that critical equipment (ambulances, fire trucks) is insufficient to meet projected needs. |
| A7 | The ashfall will be primarily composed of non-toxic materials, posing minimal long-term health risks beyond respiratory irritation. | Conduct a comprehensive analysis of ash samples from previous Yellowstone eruptions to determine their chemical composition and potential toxicity. | The analysis reveals that the ash contains significant concentrations of heavy metals or other toxic substances that could pose long-term health risks through inhalation, ingestion, or skin contact. |
| A8 | The existing road network will be able to withstand the weight of heavy equipment used for ash removal and emergency response. | Conduct a structural assessment of key bridges and roadways along evacuation routes to determine their load-bearing capacity and vulnerability to damage from heavy equipment. | The assessment reveals that key bridges or roadways are structurally unsound and unable to support the weight of heavy equipment, potentially causing collapses and disrupting evacuation efforts. |
| A9 | The public will trust and utilize official sources of information (FEMA, USGS) over social media and unofficial channels. | Monitor social media and online forums for the spread of misinformation and compare the reach and engagement of official sources versus unofficial sources. | Analysis reveals that unofficial sources of information have significantly higher reach and engagement than official sources, indicating a widespread distrust of official information and a potential for the spread of misinformation. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Austerity Avalanche | Process/Financial | A2 | Finance Lead | CRITICAL (20/25) |
| FM2 | The Jurisdictional Jungle | Technical/Logistical | A3 | Coordination Lead | CRITICAL (15/25) |
| FM3 | The Apathy Apocalypse | Market/Human | A1 | Public Affairs Lead | CRITICAL (20/25) |
| FM4 | The Overflow Ordeal | Process/Financial | A4 | Shelter Coordinator | CRITICAL (20/25) |
| FM5 | The Blackout Blizzard | Technical/Logistical | A5 | Infrastructure Lead | CRITICAL (15/25) |
| FM6 | The Thin Blue Line | Market/Human | A6 | Emergency Services Coordinator | CRITICAL (20/25) |
| FM7 | The Poisoned Legacy | Market/Human | A7 | Public Health Lead | CRITICAL (15/25) |
| FM8 | The Collapsing Corridor | Technical/Logistical | A8 | Transportation Lead | CRITICAL (20/25) |
| FM9 | The Echo Chamber of Error | Process/Financial | A9 | Communication Lead | CRITICAL (20/25) |


### Failure Modes

#### FM1 - The Austerity Avalanche

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A2
- **Owner**: Finance Lead
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The initial budget of $50 million proves woefully inadequate. Unforeseen costs related to ash removal, emergency medical care, and shelter operations quickly deplete available funds. Cost overruns in securing bottled water and N95 respirators further exacerbate the financial strain. As resources dwindle, critical services are curtailed. Evacuation centers are understaffed, leading to long wait times and inadequate care for evacuees. Fuel shortages hamper transportation efforts, stranding evacuees along highways. The lack of financial resources undermines the entire evacuation effort, leading to increased casualties and widespread public discontent. The long-term economic impact on the region is devastating, as businesses struggle to recover and tourism plummets.

##### Early Warning Signs
- Expenditures exceed budgeted amounts by 15% within the first 48 hours of the evacuation.
- Requests for additional funding are denied or delayed by FEMA.
- Critical resource vendors demand upfront payments due to concerns about the project's financial stability.

##### Tripwires
- Available cash reserves <= $10 million
- Fuel supply contracts fulfilled <= 75%
- Shelter capacity >= 90% with resource shortages

##### Response Playbook
- Contain: Immediately implement a hiring freeze and suspend all non-essential spending.
- Assess: Conduct a thorough audit of all expenditures and identify areas for cost reduction.
- Respond: Seek emergency supplemental funding from Congress and explore private sector partnerships.


**STOP RULE:** Available cash reserves are projected to fall below $5 million within the next 72 hours, with no prospect of additional funding.

---

#### FM2 - The Jurisdictional Jungle

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A3
- **Owner**: Coordination Lead
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The assumption of seamless inter-agency coordination proves disastrously false. The National Park Service, state governments of Wyoming, Montana, and Idaho, and FEMA all operate under different protocols and priorities. Disputes arise over authority, resource allocation, and evacuation routes. The lack of a clear chain of command leads to confusion and delays. Critical decisions are stalled by bureaucratic infighting. Evacuation routes are blocked due to conflicting traffic management plans. Resource convoys are delayed due to jurisdictional disputes over access rights. The lack of coordination undermines the entire evacuation effort, leading to increased casualties and widespread chaos. The absence of clear authority transfer protocols results in a fragmented and ineffective response.

##### Early Warning Signs
- Multiple agencies issue conflicting evacuation orders or safety guidelines.
- Communication breakdowns occur between key agencies, hindering coordination efforts.
- Requests for assistance from one agency are denied or delayed by another agency.

##### Tripwires
- Authority transfer MOUs not signed within 24 hours of alert
- Critical resource requests delayed > 12 hours due to inter-agency disputes
- Conflicting evacuation orders issued by >= 2 agencies

##### Response Playbook
- Contain: Immediately convene an emergency meeting of all agency heads to resolve the disputes.
- Assess: Conduct a rapid assessment of the impact of the coordination failures on the evacuation effort.
- Respond: Invoke federal authority to override conflicting state and local directives and establish a unified command structure.


**STOP RULE:** A formal declaration of a state of emergency is blocked by inter-agency conflict, preventing the deployment of federal resources.

---

#### FM3 - The Apathy Apocalypse

- **Archetype**: Market/Human
- **Root Cause**: Assumption A1
- **Owner**: Public Affairs Lead
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The assumption of widespread public compliance with evacuation orders crumbles as apathy and distrust take hold. Years of sensationalized media coverage and perceived government incompetence have eroded public confidence. Many residents dismiss the warnings as another false alarm. Others refuse to leave their homes, fearing looting or believing they can weather the eruption on their own. Misinformation spreads rapidly through social media, further fueling skepticism and resistance. Evacuation efforts are hampered by gridlock as defiant residents clog roadways. First responders are stretched thin dealing with holdouts and managing the flow of traffic. The lack of public cooperation undermines the entire evacuation effort, leading to increased casualties and widespread chaos. The long-term social impact on the region is devastating, as communities are fractured by distrust and resentment.

##### Early Warning Signs
- Social media sentiment analysis indicates a significant increase in skepticism and distrust towards official warnings.
- Traffic counts on evacuation routes are significantly lower than projected.
- Reports of looting and civil unrest increase in evacuated areas.

##### Tripwires
- Evacuation compliance rate <= 60% after 12 hours
- Social media sentiment score indicates > 50% negative sentiment towards evacuation orders
- Traffic flow rate on key evacuation routes <= 50% of projected capacity

##### Response Playbook
- Contain: Immediately launch a targeted public awareness campaign to address misinformation and emphasize the severity of the threat.
- Assess: Conduct a rapid assessment of the reasons for public resistance and identify key influencers who can help promote compliance.
- Respond: Deploy law enforcement and National Guard personnel to enforce evacuation orders and provide security assurances.


**STOP RULE:** Civil unrest escalates to the point where law enforcement is unable to maintain order and protect evacuees.

---

#### FM4 - The Overflow Ordeal

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A4
- **Owner**: Shelter Coordinator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The assumption of adequate shelter capacity proves tragically wrong. The designated evacuation shelters are quickly overwhelmed by the influx of evacuees. Families are crammed into overcrowded spaces, lacking basic amenities and privacy. Food and water supplies run short, leading to rationing and discontent. Medical facilities are strained, unable to cope with the surge in patients. The lack of adequate shelter creates a humanitarian crisis, with vulnerable populations suffering disproportionately. Disease outbreaks spread rapidly through the overcrowded shelters. The situation deteriorates into chaos, undermining the entire evacuation effort and eroding public trust. The long-term social and psychological impact on the evacuees is devastating.

##### Early Warning Signs
- Shelter occupancy rates exceed 90% within the first 12 hours of opening.
- Reports of overcrowding, resource shortages, and unsanitary conditions emerge from evacuation shelters.
- Requests for additional shelter capacity are denied or delayed due to logistical constraints.

##### Tripwires
- Shelter occupancy >= 95%
- Food/water supplies <= 24 hours at >= 50% of shelters
- Medical staff/patient ratio >= 1:200 at >= 50% of shelters

##### Response Playbook
- Contain: Immediately identify and open alternative shelter locations, including schools, community centers, and churches.
- Assess: Conduct a rapid assessment of the needs of evacuees in overcrowded shelters and prioritize resource allocation.
- Respond: Request additional resources from FEMA and other relief organizations and implement a system for managing shelter overflow.


**STOP RULE:** The number of unsheltered evacuees exceeds 10,000, with no prospect of securing additional shelter capacity within the next 24 hours.

---

#### FM5 - The Blackout Blizzard

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A5
- **Owner**: Infrastructure Lead
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The assumption of a functioning power grid proves fatally flawed. A combination of seismic activity and heavy ashfall cripples the region's power infrastructure. Substations fail, transmission lines collapse, and power plants shut down. Hospitals are plunged into darkness, jeopardizing patient care. Communication centers go offline, disrupting emergency response efforts. Traffic signals fail, causing gridlock and hindering evacuation efforts. Water treatment plants lose power, contaminating water supplies. The lack of electricity undermines the entire evacuation effort, leading to increased casualties and widespread panic. The long-term economic impact on the region is devastating, as businesses are forced to close and infrastructure repairs are delayed.

##### Early Warning Signs
- Power outages begin to occur in critical infrastructure facilities (hospitals, communication centers).
- Voltage fluctuations and equipment failures are reported at key substations.
- Ashfall accumulation on power lines exceeds pre-defined thresholds.

##### Tripwires
- Power outages >= 4 hours at >= 50% of hospitals
- Communication system uptime <= 80%
- Water treatment plant output <= 50% of normal capacity

##### Response Playbook
- Contain: Immediately activate backup power systems at critical infrastructure facilities and prioritize fuel delivery to generators.
- Assess: Conduct a rapid assessment of the extent of the power outages and identify critical infrastructure facilities at risk.
- Respond: Request assistance from utility companies and the National Guard to restore power and protect critical infrastructure.


**STOP RULE:** The regional power grid collapses completely, with no prospect of restoring power to critical infrastructure facilities within the next 48 hours.

---

#### FM6 - The Thin Blue Line

- **Archetype**: Market/Human
- **Root Cause**: Assumption A6
- **Owner**: Emergency Services Coordinator
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The assumption of sufficient first responder availability proves tragically optimistic. A combination of factors, including pre-existing staffing shortages, illness, and injuries, decimates the ranks of medical personnel, law enforcement, and firefighters. Hospitals are overwhelmed, lacking the staff to treat the injured. Looting and civil unrest spread as law enforcement is unable to maintain order. Firefighters are unable to respond to fires, allowing them to spread unchecked. The lack of first responders undermines the entire evacuation effort, leading to increased casualties and widespread chaos. The long-term social impact on the region is devastating, as communities are fractured by fear and violence.

##### Early Warning Signs
- Significant numbers of first responders report sick or injured, reducing available staffing levels.
- Requests for mutual aid from neighboring jurisdictions are denied or delayed.
- Reports of looting and civil unrest increase in evacuated areas.

##### Tripwires
- First responder staffing levels <= 70% of pre-eruption levels
- Mutual aid requests denied by >= 3 neighboring jurisdictions
- Looting incidents >= 50 per 24 hours

##### Response Playbook
- Contain: Immediately implement emergency staffing protocols, including mandatory overtime and the deployment of non-essential personnel.
- Assess: Conduct a rapid assessment of the needs of first responders and prioritize resource allocation.
- Respond: Request assistance from federal agencies and neighboring states and deploy the National Guard to support law enforcement and emergency medical services.


**STOP RULE:** The number of active first responders falls below 50% of pre-eruption levels, with no prospect of securing additional personnel within the next 24 hours.

---

#### FM7 - The Poisoned Legacy

- **Archetype**: Market/Human
- **Root Cause**: Assumption A7
- **Owner**: Public Health Lead
- **Risk Level:** CRITICAL 15/25 (Likelihood 3/5 × Impact 5/5)

##### Failure Story
The assumption of non-toxic ash proves tragically wrong. Analysis reveals high concentrations of heavy metals and other toxins. Public health officials downplay the risks initially, leading to widespread exposure. Long-term health effects emerge years later, including respiratory illnesses, cancers, and neurological disorders. Lawsuits against the government and responsible parties ensue. Public trust is shattered, and the region is stigmatized as a toxic wasteland. The economic impact is devastating, as tourism collapses and property values plummet. The social fabric of the community is torn apart by anger, resentment, and fear. The long-term recovery is hampered by the ongoing health crisis and the lack of public confidence.

##### Early Warning Signs
- Initial ash samples show elevated levels of concerning chemicals.
- Public health officials downplay the risks of ash exposure.
- Reports of unusual health problems begin to emerge in affected communities.

##### Tripwires
- Ash toxicity levels exceed EPA safety standards by >= 20%
- Public trust in health officials <= 40%
- Reports of unusual illnesses increase by >= 30% in affected areas

##### Response Playbook
- Contain: Immediately issue revised health warnings and provide guidance on protective measures.
- Assess: Conduct a comprehensive health assessment of affected communities and identify individuals at risk.
- Respond: Implement long-term health monitoring programs and provide medical care to those affected.


**STOP RULE:** Scientific evidence confirms a direct link between ash exposure and a significant increase in cancer rates, with no effective treatment available.

---

#### FM8 - The Collapsing Corridor

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Transportation Lead
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The assumption of robust roadways proves disastrously false. Heavy equipment used for ash removal and emergency response causes key bridges and roadways to collapse. Evacuation routes are blocked, hindering the movement of people and resources. Emergency vehicles are stranded, unable to reach those in need. The lack of access undermines the entire evacuation effort, leading to increased casualties and widespread chaos. The long-term economic impact on the region is devastating, as transportation networks are crippled and infrastructure repairs are delayed for years. The ability to deliver aid and support to affected communities is severely compromised.

##### Early Warning Signs
- Structural damage is observed on key bridges and roadways.
- Weight restrictions are imposed on certain routes.
- Heavy equipment operators report concerns about road stability.

##### Tripwires
- Bridge collapses >= 2 on primary evacuation routes
- Weight restrictions imposed on >= 50% of evacuation routes
- Heavy equipment accidents increase by >= 20%

##### Response Playbook
- Contain: Immediately reroute traffic to alternative routes and implement emergency repairs to damaged infrastructure.
- Assess: Conduct a rapid assessment of the structural integrity of all key bridges and roadways.
- Respond: Request assistance from the Army Corps of Engineers to construct temporary bridges and repair damaged infrastructure.


**STOP RULE:** A major bridge collapse completely isolates a significant portion of the evacuation zone, preventing the evacuation of thousands of residents.

---

#### FM9 - The Echo Chamber of Error

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A9
- **Owner**: Communication Lead
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The assumption of public reliance on official sources proves tragically naive. Misinformation spreads rapidly through social media and unofficial channels, undermining evacuation efforts and creating chaos. Conspiracy theories about the eruption's cause and severity gain traction, leading many to distrust official warnings. False rumors about resource shortages and government incompetence fuel panic and hoarding. Evacuation routes are clogged by people seeking to escape based on inaccurate information. First responders are overwhelmed by calls for assistance based on false reports. The lack of public trust undermines the entire evacuation effort, leading to increased casualties and widespread confusion. The long-term social impact on the region is devastating, as communities are fractured by distrust and misinformation.

##### Early Warning Signs
- Misinformation about the eruption spreads rapidly on social media.
- Official sources of information are ignored or dismissed by a significant portion of the public.
- Evacuation routes are clogged by people seeking to escape based on inaccurate information.

##### Tripwires
- Reach of unofficial information sources >= 2x reach of official sources
- Public trust in official sources <= 50%
- Emergency hotline calls related to misinformation >= 30% of total calls

##### Response Playbook
- Contain: Immediately launch a counter-misinformation campaign using social media and other channels to debunk false rumors and promote accurate information.
- Assess: Conduct a rapid assessment of the sources and spread of misinformation and identify key influencers who can help promote accurate information.
- Respond: Partner with social media platforms to remove or flag misinformation and amplify official sources of information.


**STOP RULE:** Misinformation leads to widespread panic and civil unrest, preventing effective evacuation and endangering lives.
