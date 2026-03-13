Reality check: fix before go.

### Summary

| Level | Count | Explanation |
|---|---|---|
| 🛑 High | 13 | Existential blocker without credible mitigation. |
| ⚠️ Medium | 6 | Material risk with plausible path. |
| ✅ Low | 1 | Minor/controlled risk. |


## Checklist

## 1. Violates Known Physics

*Does the project require a major, unpredictable discovery in fundamental science to succeed?*

**Level**: ✅ Low

**Justification**: Rated LOW because the plan focuses on digital identity and procurement, not on breaking physical laws. The goal is to influence policy and technical standards, not to achieve physics-defying feats. No physics laws are mentioned.

**Mitigation**: None


## 2. No Real-World Proof

*Does success depend on a technology or system that has not been proven in real projects at this scale or in this domain?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan hinges on a novel combination of product (digital identity) + market (Denmark) + tech/process (platform neutrality) + policy (procurement influence) without independent evidence at comparable scale. There is no mention of precedent.

**Mitigation**: Run parallel validation tracks covering Market/Demand, Legal/IP/Regulatory, Technical/Operational/Safety, Ethics/Societal. Define NO-GO gates: (1) empirical/engineering validity, (2) legal/compliance clearance. Reject domain-mismatched PoCs. / Project Manager / 2026-06-01


## 3. Buzzwords

*Does the plan use excessive buzzwords without evidence of knowledge?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan mentions strategic concepts like 'platform-neutral access' and 'digital sovereignty' without defining a business-level mechanism-of-action (inputs→process→customer value), an owner, and measurable outcomes. The plan lacks one-pagers.

**Mitigation**: Project Manager: Create one-pagers for 'platform-neutral access' and 'digital sovereignty,' including value hypotheses, success metrics, and decision hooks, and assign owners. Due Date: 2026-05-03


## 4. Underestimating Risks

*Does this plan grossly underestimate risks?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan identifies several risks (regulatory, technical, financial, social, security) and includes mitigation plans. However, it lacks explicit analysis of risk cascades or second-order effects. For example, "Delays in obtaining permits/approvals" is listed, but the plan doesn't map the potential cascade: permit delay → missed milestones → funding delays.

**Mitigation**: Project Manager: Expand the risk register to explicitly map potential risk cascades and second-order effects, adding controls and a dated review cadence. Due Date: 2026-05-03


## 5. Timeline Issues

*Does the plan rely on unrealistic or internally inconsistent schedules?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the permit/approval matrix is absent. The plan mentions "Delays in obtaining permits/approvals" as a risk, but lacks a comprehensive list of required permits and their typical lead times.

**Mitigation**: Regulatory and Compliance Specialist: Create a permit/approval matrix with required permits, lead times, and dependencies. Due Date: 2026-05-03


## 6. Money Issues

*Are there flaws in the financial model, funding plan, or cost realism?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan states a budget of "10.5 million DKK over 24 months" but lacks a dated financing plan listing funding sources, draw schedule, covenants, and status (e.g., LOI/term sheet/closed).

**Mitigation**: Project Manager: Create a dated financing plan listing funding sources, status, draw schedule, and covenants, and implement a NO-GO on missed financing gates. Due Date: 2026-05-03


## 7. Budget Too Low

*Is there a significant mismatch between the project's stated goals and the financial resources allocated, suggesting an unrealistic or inadequate budget?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan states a budget of "10.5 million DKK over 24 months" but lacks benchmarks or vendor quotes normalized by area. The plan mentions physical locations but not their area.

**Mitigation**: Project Manager: Benchmark (≥3) fit-out costs per m² for similar R&D facilities in Copenhagen and adjust the budget or de-scope by 2026-06-01.


## 8. Overly Optimistic Projections

*Does this plan grossly overestimate the likelihood of success, while neglecting potential setbacks, buffers, or contingency plans?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan presents key projections (e.g., "15% increased policy traction", "20% greater likelihood of influencing AltID requirements", "25% faster scaling") as single numbers without ranges or alternative scenarios.

**Mitigation**: Project Manager: Conduct a sensitivity analysis or best/worst/base-case scenario analysis for the 'increased policy traction' projection by 2026-06-01.


## 9. Lacks Technical Depth

*Does the plan omit critical technical details or engineering steps required to overcome foreseeable challenges, especially for complex components of the project?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because while the plan mentions demonstrators, it lacks explicit references to technical specifications, interface contracts, acceptance tests, or a detailed integration plan. The plan mentions "Implement FIDO2 authentication flow" but lacks specifics.

**Mitigation**: Technical Lead: Produce technical specs, interface definitions, test plans, and an integration map with owners/dates for build-critical components by 2026-06-01.


## 10. Assertions Without Evidence

*Does each critical claim (excluding timeline and budget) include at least one verifiable piece of evidence?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan states "Secure funding for each phase of the project" but lacks evidence of funding commitments. There is no document showing funding secured or a plan to secure it.

**Mitigation**: Project Manager: Obtain letters of intent or commitment from funding sources, or adjust the project scope to match secured funding by 2026-06-01.


## 11. Unclear Deliverables

*Are the project's final outputs or key milestones poorly defined, lacking specific criteria for completion, making success difficult to measure objectively?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan mentions "platform-neutral access" without specific, verifiable qualities. The plan lacks SMART acceptance criteria for platform-neutral access.

**Mitigation**: Technical Lead: Define SMART criteria for 'platform-neutral access,' including a KPI for platform diversity (e.g., support for at least three distinct mobile OSs) by 2026-05-03.


## 12. Gold Plating

*Does the plan add unnecessary features, complexity, or cost beyond the core goal?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan includes exploring "passwordless authentication via blockchain-anchored identity and decentralized identifiers (DIDs)" alongside FIDO2. This feature does not directly support the core project goals of establishing platform-neutral access and a certified fallback authentication path.

**Mitigation**: Project Team: Produce a one-page benefit case justifying the inclusion of blockchain-anchored identity and DIDs, complete with a KPI, owner, and estimated cost, or move the feature to the project backlog. / Project Manager / 2026-05-03


## 13. Staffing Fit & Rationale

*Do the roles, capacity, and skills match the work, or is the plan under- or over-staffed?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan requires a 'Mobile Security & Authentication' Lead Researcher. This role is critical for technical feasibility and requires specialized knowledge of mobile security, authentication protocols, and relevant standards, making it difficult to fill.

**Mitigation**: Project Manager: Validate the talent market for a 'Mobile Security & Authentication' Lead Researcher by contacting relevant recruiters and assessing the availability of qualified candidates. Due Date: 2026-05-03


## 14. Legal Minefield

*Does the plan involve activities with high legal, regulatory, or ethical exposure, such as potential lawsuits, corruption, illegal actions, or societal harm?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks a regulatory matrix mapping required permits, licenses, codes, and jurisdictions. The plan mentions "Delays in obtaining permits/approvals" as a risk, but lacks specifics.

**Mitigation**: Regulatory and Compliance Specialist: Create a regulatory matrix (authority, artifact, lead time, predecessors) and implement a NO-GO on adverse findings. Due Date: 2026-05-03


## 15. Lacks Operational Sustainability

*Even if the project is successfully completed, can it be sustained, maintained, and operated effectively over the long term without ongoing issues?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan mentions "Long-Term Sustainability" as Risk 10 and includes "Long-term advocacy. Build community. Monitor developments." as actions. However, it lacks a concrete plan for funding, maintenance, or technology obsolescence beyond the project's 24-month timeline.

**Mitigation**: Project Manager: Develop an operational sustainability plan including a funding/resource strategy, maintenance schedule, succession planning, technology roadmap, and adaptation mechanisms. Due Date: 2026-06-01


## 16. Infeasible Constraints

*Does the project depend on overcoming constraints that are practically insurmountable, such as obtaining permits that are almost certain to be denied?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan implies physical locations in Copenhagen but lacks zoning/land-use verification. The plan requires "access-controlled workspace" and "security-sensitive digital identity research" but lacks evidence of compliance with occupancy/egress, fire load, structural limits, or noise regulations.

**Mitigation**: Project Manager: Perform a fatal-flaw screen with Copenhagen authorities/experts, seek written confirmation where feasible, and define fallback designs/sites with dated NO-GO thresholds. Due Date: 2026-05-03


## 17. External Dependencies

*Does the project depend on critical external factors, third parties, suppliers, or vendors that may fail, delay, or be unavailable when needed?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan mentions "dependence on vendors" as a supply chain risk, but lacks a vendor dependency map showing single points of failure, SLAs, tested failover plans, or secondary suppliers. The plan mentions "Diversify supply chain. Buffer stock. Contingency plans."

**Mitigation**: Project Manager: Create a vendor dependency map showing single points of failure, SLAs, tested failover plans, and secondary suppliers. Due Date: 2026-06-01


## 18. Stakeholder Misalignment

*Are there conflicting interests, misaligned incentives, or lack of genuine commitment from key stakeholders that could derail the project?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the 'Finance Department' is incentivized by budget adherence, while the 'Technical Lead' is incentivized by demonstrator functionality, creating a conflict over demonstrator scope. The plan does not address this conflict.

**Mitigation**: Project Manager: Create a shared OKR for Finance and the Technical Lead focused on 'Demonstrator Cost-Effectiveness' to align incentives. Due Date: 2026-05-03


## 19. No Adaptive Framework

*Does the plan lack a clear process for monitoring progress and managing changes, treating the initial plan as final?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks a feedback loop. There are no KPIs, review cadence, owners, or a change-control process. Vague ‘we will monitor’ is insufficient.

**Mitigation**: Project Manager: Add a monthly review with KPI dashboard and a lightweight change board. Due Date: 2026-05-03


## 20. Uncategorized Red Flags

*Are there any other significant risks or major issues that are not covered by other items in this checklist but still threaten the project's viability?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan identifies 'social resistance' and 'technical difficulties' as critical risks, but lacks a cross-impact analysis. Failure to secure stakeholder buy-in could cripple policy influence, while technical difficulties could undermine credibility. The plan lacks a cascade map.

**Mitigation**: Project Manager: Create a cross-impact matrix and bow-tie analysis for the top three risks, including owners, dates, and NO-GO thresholds. Due Date: 2026-06-01