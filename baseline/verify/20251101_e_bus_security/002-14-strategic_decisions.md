## Primary Decisions
The vital few decisions that have the most impact.


The 'Critical' and 'High' impact levers address the fundamental project tensions of 'Security vs. Maintainability' (Isolation Depth), 'Short-Term Cost vs. Long-Term Security' (Procurement Reform), and 'Speed vs. Thoroughness' (Deployment Speed). Vendor Relationship is key to enabling the others. A missing strategic dimension might be active threat intelligence gathering to inform isolation and rollback strategies.

### Decision 1: Vendor Relationship Strategy
**Lever ID:** `5a89331f-135d-4fa2-abbc-b0fc6451cfca`

**The Core Decision:** The Vendor Relationship Strategy defines the approach taken with the e-bus vendors, ranging from collaborative to adversarial. It controls the level of cooperation and information sharing expected from vendors. The objective is to gain necessary access and compliance for security measures. Key success metrics include vendor responsiveness, access to critical system information, and adherence to security requirements.

**Why It Matters:** Choosing a confrontational approach risks vendor non-cooperation. Immediate: Delayed access to system information. → Systemic: 30% slower vulnerability patching due to vendor resistance. → Strategic: Increased long-term costs and potential legal battles.

**Strategic Choices:**

1. Maintain cordial relations, seeking voluntary vendor cooperation and information sharing.
2. Adopt a firm but fair approach, demanding full access and compliance under existing contracts, with threat of legal action.
3. Implement aggressive legal and regulatory pressure, including potential blacklisting and retroactive liability claims, to force vendor compliance and set a precedent.

**Trade-Off / Risk:** Controls Cooperation vs. Conflict. Weakness: The options don't consider the potential for international trade disputes.

**Strategic Connections:**

**Synergy:** This lever strongly synergizes with Procurement Reform Strategy. A firm vendor relationship can enforce stricter security standards in future procurements. It also enhances Vendor Dependency Management by clarifying the terms of engagement and potential exit strategies.

**Conflict:** An aggressive Vendor Relationship Strategy can conflict with Deployment Speed & Scope. Pushing too hard might delay implementation if vendors resist or become uncooperative. It may also strain Operator Training & Response if vendors withhold information.

**Justification:** *High*, High importance due to its strong influence on cooperation, information access, and future procurement. The conflict text highlights its impact on deployment speed, making it a key trade-off controller.

### Decision 2: Isolation Depth Strategy
**Lever ID:** `6516a0b8-e774-4aa1-9be5-e694029411b1`

**The Core Decision:** The Isolation Depth Strategy determines the extent to which critical e-bus systems are isolated from remote access. It controls the level of connectivity retained for vendor diagnostics and updates. The objective is to minimize the attack surface and prevent unauthorized remote control. Key success metrics include the complete removal of kill-switch capabilities and the reduction of remote vulnerabilities.

**Why It Matters:** Deeper isolation increases security but can cripple essential maintenance. Immediate: Reduced remote diagnostics capabilities. → Systemic: 40% increase in on-site maintenance costs due to limited remote access. → Strategic: Potential for service disruptions and higher operational expenses.

**Strategic Choices:**

1. Implement minimal isolation, focusing on severing only the most critical remote access pathways while retaining some vendor diagnostic capabilities.
2. Implement moderate isolation, creating a secure operator-controlled gateway for essential remote diagnostics and updates, with strict access controls.
3. Implement complete air-gapping of drive/brake/steer systems, eliminating all remote access and relying solely on on-site maintenance and diagnostics.

**Trade-Off / Risk:** Controls Security vs. Maintainability. Weakness: The options fail to account for the evolving threat landscape and the need for adaptable security measures.

**Strategic Connections:**

**Synergy:** Isolation Depth Strategy works well with Rollback and Recovery Strategy. Deeper isolation reduces the likelihood of needing a rollback, while a robust rollback plan mitigates the risk of complete isolation. It also supports Operator Training & Response by simplifying the threat landscape.

**Conflict:** Complete air-gapping, a high Isolation Depth Strategy, can conflict with Vendor Relationship Strategy if vendors are unwilling to provide on-site support. It also creates tension with Deployment Speed & Scope, as thorough isolation can be time-consuming.

**Justification:** *Critical*, Critical because it directly addresses the core problem of remote access vulnerabilities. Its synergy and conflict texts show it's a central hub influencing vendor relations, rollback, and deployment speed. It controls the project's core security/maintainability trade-off.

### Decision 3: Rollback and Recovery Strategy
**Lever ID:** `ebcb1f34-0fa8-4572-b7f3-1e60c428ff73`

**The Core Decision:** The Rollback and Recovery Strategy defines the procedures and capabilities for restoring e-bus systems to a secure state after a cyber incident. It controls the speed and completeness of system recovery. The objective is to minimize downtime and data loss in the event of a successful attack. Key success metrics include recovery time objective (RTO) and recovery point objective (RPO).

**Why It Matters:** A slow rollback process can lead to prolonged service disruptions. Immediate: Extended downtime during incidents. → Systemic: 50% longer recovery times due to inefficient rollback procedures. → Strategic: Damage to public trust and potential economic losses from service interruptions.

**Strategic Choices:**

1. Develop a basic rollback playbook focused on manual system restoration procedures.
2. Create a comprehensive rollback playbook with automated scripts for rapid system restoration and data recovery.
3. Implement a fully automated, resilient rollback system with redundant backups and failover capabilities, leveraging containerization and infrastructure-as-code principles for near-instantaneous recovery.

**Trade-Off / Risk:** Controls Speed vs. Complexity. Weakness: The options don't consider the human element in incident response and the need for well-trained personnel.

**Strategic Connections:**

**Synergy:** This lever has strong synergy with Operator Training & Response. Well-trained operators are crucial for executing rollback procedures effectively. It also complements Isolation Depth Strategy, providing a safety net in case isolation fails.

**Conflict:** A fully automated Rollback and Recovery Strategy can conflict with Vendor Dependency Management if it relies on vendor-specific tools or technologies. It may also compete with Deployment Speed & Scope if extensive testing is required.

**Justification:** *High*, High importance because it's the primary mitigation strategy if isolation fails. Its synergy with operator training and conflict with vendor dependency make it a key lever for resilience and risk management.

### Decision 4: Procurement Reform Strategy
**Lever ID:** `f372f21a-3905-474e-aed0-3f2ca7d0e8bb`

**The Core Decision:** The Procurement Reform Strategy aims to enhance cybersecurity considerations in the acquisition of e-buses and related systems. It controls the security standards and vendor selection criteria. The objective is to ensure that future procurements prioritize security and minimize vulnerabilities. Key success metrics include the adoption rate of secure-by-design principles and the reduction of security flaws in new buses.

**Why It Matters:** Weak procurement standards perpetuate vulnerabilities in future acquisitions. Immediate: Continued risk exposure. → Systemic: Recurring security incidents due to insecure systems. → Strategic: Long-term financial losses and reputational damage from repeated breaches.

**Strategic Choices:**

1. Incorporate basic cybersecurity requirements into existing procurement processes.
2. Establish a dedicated cybersecurity review board to evaluate vendor proposals and enforce security standards.
3. Implement a 'security-by-design' procurement framework, requiring vendors to demonstrate verifiable security throughout the entire product lifecycle, including threat modeling, secure coding practices, and continuous vulnerability monitoring, with penalties for non-compliance.

**Trade-Off / Risk:** Controls Short-Term Cost vs. Long-Term Security. Weakness: The options fail to address the challenge of maintaining up-to-date security standards in a rapidly evolving threat landscape.

**Strategic Connections:**

**Synergy:** Procurement Reform Strategy synergizes strongly with Vendor Relationship Strategy. A firm approach can enforce stricter security standards in future procurements. It also supports Vendor Dependency Management by diversifying the vendor pool.

**Conflict:** A stringent Procurement Reform Strategy can conflict with Deployment Speed & Scope, as it may take longer to evaluate and select vendors. It also creates tension with existing Vendor Relationship Strategy if current vendors cannot meet the new standards.

**Justification:** *Critical*, Critical because it prevents future vulnerabilities and shapes long-term security posture. Its synergy with vendor relationships and conflict with deployment speed make it a central lever for sustainable security.

### Decision 5: Deployment Speed & Scope
**Lever ID:** `d2f49a86-971c-45e8-9ddf-dc2b0d5d91e7`

**The Core Decision:** The Deployment Speed & Scope lever determines the pace and extent to which security measures are implemented across the e-bus fleet. It controls the rollout strategy, from phased to parallel. The objective is to balance rapid risk reduction with minimal disruption to operations. Key success metrics include the percentage of buses secured within the project timeline and the overall impact on service availability.

**Why It Matters:** Rapid deployment can address immediate threats but risks overlooking unforeseen issues. Immediate: Quick risk reduction. → Systemic: Increased chance of implementation errors and system vulnerabilities. → Strategic: Potential for widespread system failures and reputational damage.

**Strategic Choices:**

1. Phased Rollout: Implement security measures incrementally across the fleet, starting with a small subset of buses.
2. Parallel Implementation: Simultaneously deploy security measures across the entire fleet, prioritizing speed of execution.
3. Staged & Adaptive: Deploy in Copenhagen, then adapt nationally based on real-time threat intelligence and iterative security testing, delaying full rollout until confidence is high.

**Trade-Off / Risk:** Controls Speed vs. Thoroughness. Weakness: The options don't account for the logistical challenges of retrofitting the entire bus fleet within the given timeframe.

**Strategic Connections:**

**Synergy:** Deployment Speed & Scope works well with Operator Training & Response. A phased rollout allows for more focused training and adaptation. It also complements Rollback and Recovery Strategy by providing opportunities to test and refine recovery procedures.

**Conflict:** A parallel implementation, a high Deployment Speed & Scope strategy, can conflict with Isolation Depth Strategy if thorough isolation is time-consuming. It also creates tension with Procurement Reform Strategy if new security requirements delay vendor selection.

**Justification:** *High*, High importance as it balances immediate risk reduction with thoroughness and potential disruption. Its conflicts with isolation depth and procurement reform highlight its role in managing project execution trade-offs.

---
## Secondary Decisions
These decisions are less significant, but still worth considering.

### Decision 6: Operator Training & Response
**Lever ID:** `eb9bf5f9-1fdf-4f4c-96a9-ded04df342f8`

**The Core Decision:** This lever focuses on enhancing the cybersecurity capabilities of e-bus operators. It controls the level of training and preparedness operators have to respond to security incidents. Objectives include improving threat detection, incident response time, and overall security awareness. Key success metrics are the frequency of successful incident response drills, the number of operators trained, and the reduction in security incidents attributed to operator error. This lever aims to create a human firewall, complementing technical security measures.

**Why It Matters:** Well-trained operators are crucial for incident response. Immediate: Improved incident detection. → Systemic: Reduced downtime and faster recovery from attacks. → Strategic: Enhanced resilience and minimized impact of potential security breaches.

**Strategic Choices:**

1. Basic Awareness: Provide basic cybersecurity awareness training to e-bus operators.
2. Incident Response Drills: Conduct regular incident response drills to prepare operators for potential security breaches.
3. Cybersecurity Integration: Embed cybersecurity experts within the e-bus operator teams, empowering them to proactively identify and mitigate threats, and develop custom rollback procedures.

**Trade-Off / Risk:** Controls Preparedness vs. Cost. Weakness: The options don't address the potential for human error in incident response, even with extensive training.

**Strategic Connections:**

**Synergy:** Operator Training & Response strongly synergizes with Rollback and Recovery Strategy. Well-trained operators can effectively execute rollback procedures, minimizing downtime and impact during a security breach. It also enhances the effectiveness of Isolation Depth Strategy by ensuring operators understand and adhere to isolation protocols.

**Conflict:** Operator Training & Response can conflict with Deployment Speed & Scope. Extensive training programs may slow down the initial deployment or expansion of the e-bus fleet. It also presents a trade-off with Vendor Dependency Management, as operators may become reliant on vendor-provided training materials.

**Justification:** *Medium*, Medium importance. While crucial for incident response, it's more supportive than foundational. Its synergy with rollback is important, but its conflicts are less strategically impactful.

### Decision 7: Vendor Dependency Management
**Lever ID:** `227aae77-1987-4c4d-b9db-1a66e55d6512`

**The Core Decision:** This lever addresses the risks associated with relying on a single vendor for critical e-bus components and systems. It controls the level of vendor diversification and the development of alternative solutions. Objectives include reducing vendor lock-in, increasing supply chain resilience, and mitigating the impact of vendor-related security vulnerabilities. Key success metrics are the number of vendors used for critical components, the percentage of components sourced from open-source alternatives, and the reduction in vendor-related security incidents.

**Why It Matters:** The approach to vendor dependency impacts long-term maintenance costs and security risks. Immediate: Diversification of vendor base → Systemic: 15% increase in initial procurement costs due to smaller order volumes per vendor → Strategic: Reduced reliance on single vendors and increased bargaining power.

**Strategic Choices:**

1. Maintain existing vendor relationships while implementing stricter security requirements and monitoring their compliance.
2. Diversify the vendor base by sourcing components and services from multiple suppliers, reducing reliance on any single vendor.
3. Develop open-source alternatives for critical e-bus components and systems, fostering a community of developers and reducing long-term vendor lock-in.

**Trade-Off / Risk:** Controls Cost vs. Vendor Lock-in. Weakness: The options don't consider the potential for increased complexity in managing a diverse vendor ecosystem.

**Strategic Connections:**

**Synergy:** Vendor Dependency Management has strong synergy with Procurement Reform Strategy. Diversifying the vendor base requires changes to procurement processes and criteria. It also amplifies the impact of Isolation Depth Strategy by reducing the attack surface associated with any single vendor's vulnerabilities.

**Conflict:** Vendor Dependency Management can conflict with Vendor Relationship Strategy, especially if diversification leads to strained relationships with existing vendors. It also creates a trade-off with Deployment Speed & Scope, as sourcing from multiple vendors or developing open-source alternatives may increase development time.

**Justification:** *Medium*, Medium importance. It addresses vendor lock-in, but its impact is less immediate than isolation or procurement. Its conflicts with vendor relationships and deployment speed are manageable trade-offs.
