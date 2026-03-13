A premortem assumes the project has failed and works backward to identify the most likely causes.

## Assumptions to Kill

These foundational assumptions represent the project's key uncertainties. If proven false, they could lead to failure. Validate them immediately using the specified methods.

| ID | Assumption | Validation Method | Failure Trigger |
|----|------------|-------------------|-----------------|
| A1 | The Hong Kong Film Censorship Authority will allow subtle political commentary without requiring significant cuts. | Submit a detailed synopsis outlining the most politically sensitive scenes to the Hong Kong Film Development Council and request informal feedback. | The HKFDC expresses strong concerns about specific scenes and suggests major revisions to avoid potential censorship issues. |
| A2 | The lead actor cast will be able to obtain all necessary work permits and visas without delays or complications. | Initiate the work permit application process for a hypothetical non-Hong Kong actor with a similar profile to the intended lead. | The Immigration Department raises concerns or requests additional documentation that would cause significant delays (more than 30 days) in the permit approval process. |
| A3 | The production team can secure all necessary filming locations in Hong Kong within the allocated budget and timeframe. | Contact location managers and property owners for the three most critical filming locations and obtain firm quotes and availability timelines. | Quotes for location rentals exceed the budgeted amount by more than 25%, or availability timelines conflict with the production schedule. |
| A4 | The target audience will be receptive to a remake of 'The Game' set in Hong Kong, despite potential cultural differences and familiarity with the original. | Conduct a survey with a representative sample of the target audience (adults 25-54) to gauge their interest in a Hong Kong-set remake of 'The Game'. | Less than 50% of respondents express interest in seeing the film, or a significant portion express concerns about cultural appropriation or unnecessary remakes. |
| A5 | The film's score and soundtrack, blending Western and Eastern musical elements, will resonate positively with both local and international audiences. | Create a sample soundtrack incorporating both Western and Eastern musical styles and conduct focus group testing with representative audience segments. | Focus group participants rate the sample soundtrack poorly, citing it as either inauthentic, distracting, or not fitting the film's tone. |
| A6 | Post-production facilities and skilled personnel (editors, VFX artists, sound designers) will be readily available in Hong Kong to meet the project's quality and timeline requirements. | Contact several reputable post-production houses in Hong Kong to assess their capacity, availability, and pricing for the project's specific needs (VFX-heavy thriller). | Major post-production houses are fully booked for the project's timeframe, or their quotes exceed the allocated budget by more than 20%. |
| A7 | The film's depiction of law enforcement and criminal organizations in Hong Kong will not offend or alienate significant segments of the local population. | Conduct focus groups with diverse segments of the Hong Kong population (e.g., former police officers, triad members, community leaders) to gauge their reactions to the proposed portrayal of law enforcement and criminal elements. | Focus group participants express strong objections to the film's depiction of law enforcement or criminal organizations, citing it as disrespectful, inaccurate, or glorifying violence. |
| A8 | The film's reliance on modern technology and surveillance themes will resonate with audiences without feeling dated or cliché by the time of release in 2028. | Consult with technology futurists and experts to assess the long-term relevance and potential obsolescence of the film's technological themes. | Technology experts predict that the film's technological themes will feel outdated or cliché by 2028, or that the technology depicted will be easily circumvented or rendered obsolete by future advancements. |
| A9 | The film's marketing campaign will effectively reach and engage the target audience through social media and digital channels, despite increasing competition for attention and evolving algorithms. | Conduct A/B testing of different marketing messages and creative assets on social media platforms to assess their effectiveness in reaching and engaging the target audience. | A/B testing reveals that the marketing campaign fails to generate significant engagement or reach the target audience effectively, or that the cost per engagement is significantly higher than industry benchmarks. |


## Failure Scenarios and Mitigation Plans

Each scenario below links to a root-cause assumption and includes a detailed failure story, early warning signs, measurable tripwires, a response playbook, and a stop rule to guide decision-making.

### Summary of Failure Modes

| ID | Title | Archetype | Root Cause | Owner | Risk Level |
|----|-------|-----------|------------|-------|------------|
| FM1 | The Censor's Scissors: A Financial Fiasco | Process/Financial | A1 | Producer | CRITICAL (20/25) |
| FM2 | The Permit Impasse: A Logistical Nightmare | Technical/Logistical | A2 | Permitting Lead | HIGH (12/25) |
| FM3 | The Location Lockout: A Human Disaster | Market/Human | A3 | Location Manager | HIGH (12/25) |
| FM4 | The Remake Rejection: A Box Office Bomb | Process/Financial | A4 | Marketing & Distribution Strategist | CRITICAL (20/25) |
| FM5 | The Sonic Clash: An Aural Assault | Technical/Logistical | A5 | Post-Production Supervisor | HIGH (12/25) |
| FM6 | The Post-Production Bottleneck: A Quality Catastrophe | Market/Human | A6 | Post-Production Supervisor | HIGH (12/25) |
| FM7 | The Offended Outcry: A Public Relations Disaster | Process/Financial | A7 | Public Relations Manager | CRITICAL (20/25) |
| FM8 | The Techno-Fossil: A Dated Disaster | Technical/Logistical | A8 | Technology Consultant | HIGH (12/25) |
| FM9 | The Marketing Misfire: A Lost Audience | Market/Human | A9 | Marketing & Distribution Strategist | HIGH (12/25) |


### Failure Modes

#### FM1 - The Censor's Scissors: A Financial Fiasco

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A1
- **Owner**: Producer
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumed that subtle political commentary would be acceptable to the Hong Kong Film Censorship Authority. However, the Authority, under increasing pressure from Beijing, takes a hard line. The initial submission is rejected, requiring extensive rewrites and reshoots to remove or alter politically sensitive scenes. This leads to significant budget overruns due to additional production days, VFX work to digitally alter scenes, and legal fees to navigate the censorship process. The film's release is delayed, missing key film festival deadlines and impacting distribution deals. Ultimately, the film is released in a heavily censored form, alienating local audiences and failing to resonate with international viewers. The reduced box office revenue and diminished streaming deals result in a significant financial loss, jeopardizing future franchise opportunities.

##### Early Warning Signs
- Initial screenplay draft flagged for multiple potential censorship issues by legal counsel.
- Delays in receiving feedback from the Hong Kong Film Development Council on the synopsis.
- Increased scrutiny of film projects with political themes in Hong Kong media.

##### Tripwires
- HK Film Censorship Authority requests more than 3 major script revisions.
- Reshoot costs exceed 10% of the original production budget.
- Distribution deals in key Asian markets are withdrawn due to censorship concerns.

##### Response Playbook
- Contain: Immediately halt all production activities related to the flagged scenes.
- Assess: Conduct a thorough review of the script with censorship experts to identify all potential issues and develop alternative solutions.
- Respond: Negotiate with the HK Film Censorship Authority to find a compromise that satisfies their concerns while preserving the core narrative, or pivot to a less politically sensitive storyline.


**STOP RULE:** The HK Film Censorship Authority demands changes that fundamentally alter the film's narrative or message, rendering it artistically meaningless.

---

#### FM2 - The Permit Impasse: A Logistical Nightmare

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A2
- **Owner**: Permitting Lead
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumed that securing work permits for the lead actor would be a straightforward process. However, due to unforeseen changes in immigration policy or increased scrutiny of foreign talent, the lead actor's work permit is delayed indefinitely. This creates a cascade of logistical problems. The production schedule is thrown into disarray, forcing the postponement of key filming dates. The availability of other cast members and crew is affected, leading to scheduling conflicts and increased costs. The delay also impacts location agreements, potentially losing access to critical filming locations. The production team scrambles to find a replacement actor, but the casting process takes time and the new actor may not be as well-suited for the role. Ultimately, the production is significantly delayed, exceeding the allocated budget and jeopardizing the film's quality.

##### Early Warning Signs
- Increased processing times for work permits in Hong Kong.
- Stricter requirements for documentation and background checks for foreign talent.
- Public debate about the employment of foreign workers in the Hong Kong film industry.

##### Tripwires
- Work permit application is pending for more than 60 days.
- Immigration Department requests additional documentation not initially required.
- Key filming locations become unavailable due to permit delays.

##### Response Playbook
- Contain: Immediately explore alternative visa options for the lead actor.
- Assess: Conduct a thorough review of the work permit application process to identify any potential roadblocks and develop a revised strategy.
- Respond: Engage with immigration lawyers and government officials to expedite the permit approval process, or recast the role with a Hong Kong-based actor.


**STOP RULE:** The lead actor's work permit is denied, and a suitable replacement cannot be found within 90 days.

---

#### FM3 - The Location Lockout: A Human Disaster

- **Archetype**: Market/Human
- **Root Cause**: Assumption A3
- **Owner**: Location Manager
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumed that securing key filming locations in Hong Kong would be feasible within the allocated budget and timeframe. However, due to increased demand from other productions, rising property values, or resistance from local residents, the production team is unable to secure several critical locations. This forces the team to compromise on the film's visual aesthetic, settling for less desirable locations that don't capture the intended atmosphere. The lack of authentic Hong Kong locations diminishes the film's cultural resonance and appeal to local audiences. The production team attempts to recreate the desired locations using CGI, but the visual effects are unconvincing and detract from the film's overall quality. The negative word-of-mouth spreads quickly, impacting ticket sales and streaming viewership. The film is ultimately perceived as a generic thriller, failing to capitalize on its unique Hong Kong setting.

##### Early Warning Signs
- Location rental quotes exceed initial budget estimates by more than 15%.
- Property owners express reluctance to allow filming due to potential disruptions.
- Local residents voice concerns about noise and traffic during filming.

##### Tripwires
- More than 2 key filming locations are unavailable within the budget.
- Local residents file formal complaints about filming activities.
- CGI costs to recreate locations exceed 15% of the VFX budget.

##### Response Playbook
- Contain: Immediately explore alternative locations that meet the film's visual requirements.
- Assess: Conduct a thorough review of the location scouting process to identify any potential issues and develop a revised strategy.
- Respond: Negotiate with property owners to address their concerns and offer incentives to secure the desired locations, or significantly revise the script to reduce reliance on specific locations.


**STOP RULE:** The production is unable to secure at least 75% of the key filming locations, and the cost of recreating them with CGI exceeds 20% of the VFX budget.

---

#### FM4 - The Remake Rejection: A Box Office Bomb

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A4
- **Owner**: Marketing & Distribution Strategist
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumed that the target audience would embrace a Hong Kong-set remake of 'The Game'. However, pre-release marketing reveals a significant lack of interest, particularly among younger demographics who are unfamiliar with the original film and skeptical of remakes in general. Older viewers express concerns about cultural appropriation or the unnecessary updating of a classic. Despite a strong marketing push, the film opens to weak box office numbers, failing to generate positive word-of-mouth. The negative reception impacts streaming deals, with major platforms offering significantly lower licensing fees than anticipated. The film becomes a financial disaster, failing to recoup its production costs and damaging the reputation of the production company.

##### Early Warning Signs
- Pre-release social media sentiment is overwhelmingly negative, with comments focusing on remake fatigue and cultural appropriation.
- Ticket pre-sales are significantly lower than comparable thriller releases.
- Marketing campaigns fail to generate significant buzz or engagement.

##### Tripwires
- Pre-release audience surveys indicate less than 40% interest in seeing the film.
- Opening weekend box office gross is less than 50% of projections.
- Major film critics publish negative reviews focusing on the film's lack of originality.

##### Response Playbook
- Contain: Immediately shift marketing focus to highlight the film's unique Hong Kong setting and visual style, downplaying the remake aspect.
- Assess: Conduct a thorough analysis of audience feedback to identify the specific reasons for the negative reception.
- Respond: Negotiate with distributors to adjust release strategy and minimize losses, or pivot to a direct-to-streaming release.


**STOP RULE:** The film fails to recoup at least 75% of its production budget within the first three months of release.

---

#### FM5 - The Sonic Clash: An Aural Assault

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A5
- **Owner**: Post-Production Supervisor
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumed that blending Western and Eastern musical elements would create a compelling and unique film score. However, the resulting soundtrack is perceived as jarring and inconsistent, failing to create a cohesive atmosphere. Western audiences find the Eastern musical elements to be distracting and inauthentic, while Eastern audiences find the Western elements to be generic and uninspired. The score clashes with the film's visuals and narrative, creating a disjointed and unpleasant viewing experience. The sound design is also criticized for being overly loud and aggressive, further detracting from the film's impact. The negative feedback impacts the film's critical reception and audience enjoyment, contributing to lower box office numbers and streaming viewership.

##### Early Warning Signs
- Early cuts of the film with the score receive negative feedback from test audiences.
- The composer struggles to integrate Western and Eastern musical elements effectively.
- The director expresses concerns about the score's tone and its impact on the film's atmosphere.

##### Tripwires
- Test audience scores for the film's music and sound design are below 3 out of 5.
- The director requests significant revisions to the score after initial integration.
- Major film critics single out the score for negative criticism in their reviews.

##### Response Playbook
- Contain: Immediately halt further work on the existing score and consult with experienced film music supervisors.
- Assess: Conduct a thorough review of the score's composition and its integration with the film's visuals and narrative.
- Respond: Commission a new score from a different composer, or significantly revise the existing score to address the identified issues.


**STOP RULE:** The film's score is deemed irreparable, and the cost of commissioning a new score exceeds 10% of the post-production budget.

---

#### FM6 - The Post-Production Bottleneck: A Quality Catastrophe

- **Archetype**: Market/Human
- **Root Cause**: Assumption A6
- **Owner**: Post-Production Supervisor
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumed that Hong Kong's post-production industry could readily handle the film's complex requirements. However, the reality is that the available facilities are overbooked, and skilled personnel are in high demand. The film's post-production schedule is significantly delayed, as editors, VFX artists, and sound designers are stretched thin and unable to meet deadlines. The quality of the work suffers, with rushed VFX shots, sloppy editing, and subpar sound design. The film is released with noticeable technical flaws, damaging its credibility and impacting audience enjoyment. The negative word-of-mouth spreads quickly, contributing to lower box office numbers and streaming viewership. The film is ultimately perceived as a low-quality production, failing to capitalize on its potential.

##### Early Warning Signs
- Post-production houses are unable to commit to the project's timeline.
- Quotes from post-production facilities exceed the allocated budget.
- Key post-production personnel express concerns about workload and deadlines.

##### Tripwires
- Post-production is delayed by more than 30 days.
- The cost of post-production exceeds the allocated budget by more than 15%.
- Major technical flaws are identified in test screenings.

##### Response Playbook
- Contain: Immediately outsource some post-production tasks to facilities outside of Hong Kong.
- Assess: Conduct a thorough review of the post-production workflow to identify any bottlenecks and inefficiencies.
- Respond: Negotiate with post-production facilities to prioritize the project and allocate additional resources, or significantly reduce the scope of VFX and sound design.


**STOP RULE:** The film's post-production quality is deemed irreparable, and the cost of fixing the issues exceeds 15% of the post-production budget.

---

#### FM7 - The Offended Outcry: A Public Relations Disaster

- **Archetype**: Process/Financial
- **Root Cause**: Assumption A7
- **Owner**: Public Relations Manager
- **Risk Level:** CRITICAL 20/25 (Likelihood 4/5 × Impact 5/5)

##### Failure Story
The project assumed that the film's portrayal of law enforcement and criminal organizations would be acceptable to the Hong Kong public. However, upon release, the film sparks widespread controversy. Certain segments of the population, particularly former police officers and their families, feel that the film unfairly demonizes law enforcement and glorifies criminal activity. This leads to public protests, calls for boycotts, and negative media coverage. The controversy damages the film's reputation and impacts its box office performance. Distributors become hesitant to promote the film, fearing further backlash. The film is ultimately perceived as insensitive and disrespectful, resulting in a significant financial loss and tarnishing the production company's image.

##### Early Warning Signs
- Negative feedback from focus groups regarding the film's portrayal of law enforcement or criminal organizations.
- Public debate about the film's themes and potential impact on society.
- Increased scrutiny of the film by media outlets and advocacy groups.

##### Tripwires
- Public protests against the film attract more than 1000 participants.
- Major media outlets publish editorials criticizing the film's portrayal of law enforcement.
- Distributors express concerns about the film's potential to offend audiences.

##### Response Playbook
- Contain: Immediately issue a public statement acknowledging the concerns and emphasizing the film's fictional nature.
- Assess: Conduct a thorough review of the film's content and marketing materials to identify any potentially offensive elements.
- Respond: Engage with community leaders and advocacy groups to address their concerns and find common ground, or adjust marketing messaging to emphasize the film's positive aspects.


**STOP RULE:** Major distributors withdraw their support for the film due to the public outcry, and the film is deemed unmarketable.

---

#### FM8 - The Techno-Fossil: A Dated Disaster

- **Archetype**: Technical/Logistical
- **Root Cause**: Assumption A8
- **Owner**: Technology Consultant
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumed that the film's reliance on modern technology and surveillance themes would remain relevant by 2028. However, by the time of release, the technology depicted in the film feels outdated and cliché. Audiences are no longer impressed by the surveillance techniques, which have become commonplace in everyday life. The film's depiction of hacking and cybercrime feels unrealistic and uninspired, failing to capture the cutting edge of technological advancements. The film's reliance on outdated technology detracts from its suspense and believability, making it feel like a relic of the past. The negative reception impacts the film's critical acclaim and audience enjoyment, contributing to lower box office numbers and streaming viewership.

##### Early Warning Signs
- Technology experts express concerns about the long-term relevance of the film's technological themes.
- New technological advancements render the film's surveillance techniques obsolete.
- Test audiences find the film's depiction of technology to be uninspired and unrealistic.

##### Tripwires
- Technology experts predict that the film's technological themes will feel outdated within 2 years of release.
- Test audience scores for the film's depiction of technology are below 3 out of 5.
- Major technology publications criticize the film's lack of technological innovation.

##### Response Playbook
- Contain: Immediately consult with technology experts to identify ways to update the film's technological elements.
- Assess: Conduct a thorough review of the film's script and visuals to identify any outdated or unrealistic technology.
- Respond: Incorporate new technological advancements into the film's narrative and visuals, or significantly revise the script to focus on timeless themes rather than specific technologies.


**STOP RULE:** The cost of updating the film's technological elements to remain relevant exceeds 15% of the VFX budget.

---

#### FM9 - The Marketing Misfire: A Lost Audience

- **Archetype**: Market/Human
- **Root Cause**: Assumption A9
- **Owner**: Marketing & Distribution Strategist
- **Risk Level:** HIGH 12/25 (Likelihood 3/5 × Impact 4/5)

##### Failure Story
The project assumed that the film's marketing campaign would effectively reach and engage the target audience through social media and digital channels. However, the marketing campaign fails to generate significant buzz or reach the intended demographic. The target audience is bombarded with competing content and becomes desensitized to traditional marketing tactics. Social media algorithms change, making it more difficult to reach potential viewers organically. The marketing campaign is perceived as generic and uninspired, failing to capture the film's unique selling points. The lack of effective marketing leads to low audience awareness and poor box office performance. The film is ultimately lost in the noise of competing releases, failing to connect with its target audience.

##### Early Warning Signs
- A/B testing reveals that marketing messages fail to generate significant engagement.
- Social media algorithms change, reducing the reach of organic content.
- The cost per engagement for marketing campaigns exceeds industry benchmarks.

##### Tripwires
- The film's social media following remains below 10,000 followers one month before release.
- The cost per engagement for marketing campaigns exceeds industry benchmarks by more than 20%.
- Website traffic to the film's official website remains below 5000 visits per week.

##### Response Playbook
- Contain: Immediately revise the marketing campaign to incorporate more innovative and engaging tactics.
- Assess: Conduct a thorough analysis of the marketing campaign's performance to identify any weaknesses and areas for improvement.
- Respond: Partner with social media influencers and content creators to reach a wider audience, or significantly increase the marketing budget to boost visibility.


**STOP RULE:** The film's marketing campaign fails to generate significant audience awareness, and the cost of reaching the target audience exceeds 20% of the marketing budget.
