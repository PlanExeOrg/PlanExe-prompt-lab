Reality check: fix before go.

### Summary

| Level | Count | Explanation |
|---|---|---|
| 🛑 High | 14 | Existential blocker without credible mitigation. |
| ⚠️ Medium | 5 | Material risk with plausible path. |
| ✅ Low | 1 | Minor/controlled risk. |


## Checklist

## 1. Violates Known Physics

*Does the project require a major, unpredictable discovery in fundamental science to succeed?*

**Level**: ✅ Low

**Justification**: Rated LOW because the plan does not describe any technology that violates established physics or contains unclear mechanisms. The goal is to improve cybersecurity, which is within the realm of established science and engineering.

**Mitigation**: None


## 2. No Real-World Proof

*Does success depend on a technology or system that has not been proven in real projects at this scale or in this domain?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan addresses a novel and potentially high-risk vulnerability. The scenario states, "While cybersecurity measures are common, the specific focus on foreign-made e-buses and the potential for remote access kill-switches introduces a unique risk profile."

**Mitigation**: Project Lead: Initiate parallel validation tracks: (T1) threat model/PoC; (T2) legal/compliance review; (T3) market validation; (T4) ethics/abuse analysis. Define go/no-go gates. Declare NO-GO if any track blocks. Due: 90 days.


## 3. Buzzwords

*Does the plan use excessive buzzwords without evidence of knowledge?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan mentions several strategic concepts without defining their business-level mechanism-of-action, owner, or measurable outcomes. For example, "A missing strategic dimension might be active threat intelligence gathering to inform isolation and rollback strategies."

**Mitigation**: Project Manager: Assign owners to define one-pagers for 'active threat intelligence gathering' and other undefined strategic concepts, including value hypotheses, success metrics, and decision hooks. Due: 60 days.


## 4. Underestimating Risks

*Does this plan grossly underestimate risks?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan identifies several risks (supply chain, technical, vendor relationship, etc.) and proposes mitigation plans. However, it lacks explicit analysis of risk cascades or second-order effects. For example, "Risk 1 - Supply Chain...Action: Contingency plans for alternative suppliers..."

**Mitigation**: Risk Manager: Conduct a Failure Mode and Effects Analysis (FMEA) to map risk cascades and second-order effects, adding controls and a dated review cadence. Due: 60 days.


## 5. Timeline Issues

*Does the plan rely on unrealistic or internally inconsistent schedules?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks a permit/approval matrix. The plan mentions regulatory compliance, but does not include a matrix of required permits and approvals, their lead times, and dependencies. "Comply with EU NIS Directive and Danish cybersecurity regulations."

**Mitigation**: Legal Team: Create a permit/approval matrix with lead times and dependencies, identifying any potential delays. Due: 60 days.


## 6. Money Issues

*Are there flaws in the financial model, funding plan, or cost realism?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan states, "Constraints include a 12-month timeline and a budget of DKK 120M." The plan does not include a financing plan listing funding sources/status, draw schedule, covenants, or runway length. Without this, funding integrity is unknown.

**Mitigation**: CFO: Develop a dated financing plan listing funding sources/status, draw schedule, covenants, and a NO‑GO on missed financing gates. Due: 30 days.


## 7. Budget Too Low

*Is there a significant mismatch between the project's stated goals and the financial resources allocated, suggesting an unrealistic or inadequate budget?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan states, "Constraints include a 12-month timeline and a budget of DKK 120M." The plan does not include vendor quotes or benchmarks normalized by area. The budget's adequacy is unknown.

**Mitigation**: CFO: Obtain ≥3 vendor quotes, normalize costs per m²/ft² for the stated footprint, and adjust the budget or de-scope by 30 days.


## 8. Overly Optimistic Projections

*Does this plan grossly overestimate the likelihood of success, while neglecting potential setbacks, buffers, or contingency plans?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan presents key projections (e.g., budget allocation, timeline milestones) as single numbers without providing a range or discussing alternative scenarios. For example, "National rollout: DKK 84M. Copenhagen pilot: DKK 36M."

**Mitigation**: Project Manager: Conduct a sensitivity analysis or a best/worst/base-case scenario analysis for the budget and timeline projections. Due: 60 days.


## 9. Lacks Technical Depth

*Does the plan omit critical technical details or engineering steps required to overcome foreseeable challenges, especially for complex components of the project?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks engineering artifacts such as specs, interface contracts, acceptance tests, integration plans, and non-functional requirements. The absence of these critical controls creates a likely failure mode.

**Mitigation**: Engineering Team: Produce technical specs, interface definitions, test plans, and an integration map with owners and dates within 60 days.


## 10. Assertions Without Evidence

*Does each critical claim (excluding timeline and budget) include at least one verifiable piece of evidence?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan states, "The Core Decision: The Vendor Relationship Strategy defines the approach taken with the e-bus vendors..." but lacks verifiable artifacts (contracts, agreements, or documented commitments) to support claims about vendor cooperation or compliance.

**Mitigation**: Procurement Lead: Obtain signed agreements or documented commitments from key vendors outlining their cooperation and compliance with security requirements. Due: 90 days.


## 11. Unclear Deliverables

*Are the project's final outputs or key milestones poorly defined, lacking specific criteria for completion, making success difficult to measure objectively?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan mentions "The Vendor Relationship Strategy" without defining SMART acceptance criteria. The plan states, "The Vendor Relationship Strategy defines the approach taken with the e-bus vendors..."

**Mitigation**: Procurement Lead: Define SMART criteria for the Vendor Relationship Strategy, including a KPI for vendor compliance (e.g., 95% adherence to security requirements). Due: 60 days.


## 12. Gold Plating

*Does the plan add unnecessary features, complexity, or cost beyond the core goal?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan includes a 'killer application' as an opportunity, but it does not directly support the core project goals of eliminating remote kill-switch vulnerabilities and establishing secure procurement practices.

**Mitigation**: Project Team: Produce a one-page benefit case justifying the 'killer application's' inclusion, complete with a KPI, owner, and estimated cost, or move the feature to the project backlog. Due: 30 days.


## 13. Staffing Fit & Rationale

*Do the roles, capacity, and skills match the work, or is the plan under- or over-staffed?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks a clear identification of the unicorn role, which is critical for success. The expertise required for cybersecurity in public transportation is both specialized and rare.

**Mitigation**: Project Manager: Conduct a market analysis to validate the availability of cybersecurity experts in transportation within 30 days.


## 14. Legal Minefield

*Does the plan involve activities with high legal, regulatory, or ethical exposure, such as potential lawsuits, corruption, illegal actions, or societal harm?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks a permit/approval matrix. The plan mentions regulatory compliance, but does not include a matrix of required permits and approvals, their lead times, and dependencies. "Comply with EU NIS Directive and Danish cybersecurity regulations."

**Mitigation**: Legal Team: Create a permit/approval matrix with lead times and dependencies, identifying any potential delays. Due: 60 days.


## 15. Lacks Operational Sustainability

*Even if the project is successfully completed, can it be sustained, maintained, and operated effectively over the long term without ongoing issues?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan identifies risks and mitigation strategies, but lacks a comprehensive operational sustainability plan. The plan does not include a funding/resource strategy, maintenance schedule, succession planning, or technology roadmap.

**Mitigation**: Project Manager: Develop an operational sustainability plan including a funding/resource strategy, maintenance schedule, succession plan, and technology roadmap. Due: 90 days.


## 16. Infeasible Constraints

*Does the project depend on overcoming constraints that are practically insurmountable, such as obtaining permits that are almost certain to be denied?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan mentions physical locations (Copenhagen, Aarhus, Odense, National) but lacks evidence of zoning compliance, occupancy limits, structural limits, or noise restrictions. The plan states, "Copenhagen location for pilot, Aarhus University and University of Southern Denmark for expertise..."

**Mitigation**: Project Manager: Conduct a fatal-flaw screen with local authorities to confirm zoning/land-use, occupancy/egress, fire load, structural limits, and noise compliance for each location. Due: 60 days.


## 17. External Dependencies

*Does the project depend on critical external factors, third parties, suppliers, or vendors that may fail, delay, or be unavailable when needed?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan identifies vendors as external dependencies, but lacks evidence of SLAs or tested failovers. The plan states, "The Vendor Relationship Strategy defines the approach taken with the e-bus vendors..."

**Mitigation**: Procurement Lead: Secure SLAs with key vendors, including uptime guarantees and tested failover procedures, by 2026-Q1.


## 18. Stakeholder Misalignment

*Are there conflicting interests, misaligned incentives, or lack of genuine commitment from key stakeholders that could derail the project?*

**Level**: ⚠️ Medium

**Justification**: Rated MEDIUM because the plan highlights potential conflicts between stakeholders but does not explicitly address conflicting incentives. For example, "An aggressive Vendor Relationship Strategy can conflict with Deployment Speed & Scope." The incentives of the deployment team (rapid rollout) and legal (aggressive vendor compliance) are not aligned.

**Mitigation**: Project Manager: Create a shared OKR aligning the deployment team and legal on a common outcome (e.g., 'Secure 80% vendor compliance without delaying deployment by >1 month'). Due: 30 days.


## 19. No Adaptive Framework

*Does the plan lack a clear process for monitoring progress and managing changes, treating the initial plan as final?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan lacks a feedback loop. There are no KPIs, review cadence, owners, or a basic change-control process with thresholds (when to re-plan/stop). Vague ‘we will monitor’ is insufficient.

**Mitigation**: Project Manager: Add a monthly review with KPI dashboard and a lightweight change board with escalation paths. Due: 30 days.


## 20. Uncategorized Red Flags

*Are there any other significant risks or major issues that are not covered by other items in this checklist but still threaten the project's viability?*

**Level**: 🛑 High

**Justification**: Rated HIGH because the plan identifies several high risks (Vendor Relationship, Technical, Financial) but lacks a cross-impact analysis. A cascade could occur if aggressive vendor strategy leads to non-cooperation, causing technical delays and budget overruns. No FTA/bow-tie is present.

**Mitigation**: Risk Manager: Create an interdependency map + bow-tie/FTA + combined heatmap with owner/date and NO-GO/contingency thresholds. Due: 90 days.