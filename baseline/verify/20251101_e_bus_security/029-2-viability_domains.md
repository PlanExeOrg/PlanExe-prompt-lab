<div class="domains-grid">
  <!-- Green Domain Card -->
  <div class="domain-card domain-card--green domain-card--count-zero" role="status" aria-labelledby="domains-green-title">
    <div class="domain-card__header">
      <div class="domain-card__left">
        <span class="domain-card__icon" aria-hidden="true">✔</span>
        <span id="domains-green-title" class="domain-card__status-name">GREEN</span>
      </div>
      <span class="domain-card__count">0 domains</span>
    </div>
    <div class="domain-card__body">
      <p>Good to go. You have solid evidence and no open critical unknowns. Proceed. Any remaining tasks are minor polish.</p>
    </div>
  </div>

  <!-- Yellow Domain Card -->
  <div class="domain-card domain-card--yellow " role="status" aria-labelledby="domains-yellow-title">
    <div class="domain-card__header">
      <div class="domain-card__left">
        <span class="domain-card__icon" aria-hidden="true">!</span>
        <span id="domains-yellow-title" class="domain-card__status-name">YELLOW</span>
      </div>
      <span class="domain-card__count">5 domains</span>
    </div>
    <div class="domain-card__body">
      <p>Conditionally ready; key risks/unknowns remain. There is promise, but is missing proof on key points or has non-fatal risks. Proceed with caution and a focused checklist.</p>
    </div>
  </div>

  <!-- Red Domain Card -->
  <div class="domain-card domain-card--red domain-card--count-zero" role="status" aria-labelledby="domains-red-title">
    <div class="domain-card__header">
      <div class="domain-card__left">
        <span class="domain-card__icon" aria-hidden="true">✖</span>
        <span id="domains-red-title" class="domain-card__status-name">RED</span>
      </div>
      <span class="domain-card__count">0 domains</span>
    </div>
    <div class="domain-card__body">
      <p>Not ready; fix blockers before proceeding. A concrete blocker or negative evidence exists (legal, technical, economic) that stops execution until fixed. Pause or pivot.</p>
    </div>
  </div>

  <!-- Gray Domain Card -->
  <div class="domain-card domain-card--gray " role="status" aria-labelledby="domains-gray-title">
    <div class="domain-card__header">
      <div class="domain-card__left">
        <span class="domain-card__icon" aria-hidden="true">?</span>
        <span id="domains-gray-title" class="domain-card__status-name">GRAY</span>
      </div>
      <span class="domain-card__count">1 domain</span>
    </div>
    <div class="domain-card__body">
      <p>Unknown / unassessed. Insufficient information to judge. Do not guess—initiate a “first measurement” task to resolve uncertainty.</p>
    </div>
  </div>
</div>




### Legend: How to Read the Scores

Each domain’s health is scored on a 1–5 scale across three key metrics. Higher scores are better.

| Metric | Strong Negative (1) | Weak Negative (2) | Neutral (3) | Weak Positive (4) | Strong Positive (5) |
|--------|--------------------|-------------------|-------------|-------------------|---------------------|
| **Evidence** | No/contradictory evidence; claims only | Anecdotes/unstable drafts | Inconclusive; limited data | Internal tests/pilot support | Independent, reproducible validation; monitored |
| **Risk** | Severe exposure; blockers/unknowns | Major exposure; mitigations not in place | Moderate; mitigations planned/in progress | Low residual risk; mitigations in place | Minimal residual risk; contingencies tested |
| **Fit** | Conflicts with constraints/strategy | Low alignment; major trade-offs | Mixed/unclear alignment | Good alignment; minor trade-offs | Strong alignment; directly reinforces strategy |

### Domain: Human Stability

**Status**: <code>YELLOW</code>

**Metrics**: evidence=2, risk=3, fit=4

**Issues:**

- <code>TRAINING_GAPS</code>: Training needs assessment + skill gap analysis report
- <code>TALENT_UNKNOWN</code>: Talent market scan report (availability, salary ranges, channels)

**Evidence Needed:**

- Stakeholder map + skills gap snapshot — acceptance criteria: top 20 stakeholders include influence/interest scores, critical role gaps quantified, and HR lead sign-off captured.
- Change plan v1 (communications, training, adoption KPIs) — acceptance criteria: communications calendar, training modules, and baseline adoption KPIs documented with exec sponsor approval.


### Domain: Economic Resilience

**Status**: <code>YELLOW</code>

**Metrics**: evidence=2, risk=3, fit=4

**Issues:**

- <code>CONTINGENCY_LOW</code>: Budget v2 with ≥10% contingency + Monte Carlo risk workbook
- <code>UNIT_ECON_UNKNOWN</code>: Unit economics model v1 + sensitivity table (key drivers)

**Evidence Needed:**

- Assumption ledger v1 + sensitivity table — acceptance criteria: ledger lists top 10 assumptions with owners and rationale, sensitivity table shows +/-20% scenario impact, and file stored in shared workspace.
- Cost model v2 (on-prem vs cloud TCO) — acceptance criteria: three-year capex/opex comparison completed with currency assumptions, variance notes, and CFO review recorded.


### Domain: Ecological Integrity

**Status**: <code>GRAY</code>

**Metrics**: evidence=—, risk=—, fit=—

**Evidence Needed:**

- Environmental baseline note (scope, metrics) — acceptance criteria: scope, metrics, measurement methods, and data sources detailed with sustainability lead sign-off.
- Cloud carbon estimate v1 (regions/services) — acceptance criteria: regional/service mix applied, monthly kgCO2e calculated with methodology notes, and results published to shared dashboard.


### Domain: Rights & Legality

**Status**: <code>YELLOW</code>

**Metrics**: evidence=2, risk=3, fit=3

**Issues:**

- <code>DPIA_GAPS</code>: Bundle the license files for the top data sources and the corresponding DPIAs.

**Evidence Needed:**

- Top-N data sources: licenses + DPIAs bundle — acceptance criteria: each top data source includes license file, DPIA (v2+ for high-risk), retention policy link, and DPO sign-off recorded.
- Regulatory mapping v1 + open questions list — acceptance criteria: applicable regulations by jurisdiction linked to control owners, open questions assigned with due dates, and compliance counsel acknowledged.


### Domain: Technical Feasibility

**Status**: <code>YELLOW</code>

**Metrics**: evidence=2, risk=3, fit=4

**Issues:**

- <code>GEO_RISK_UNASSESSED</code>: Independent geological survey + risk memo

**Evidence Needed:**

- Independent geological survey + risk memo — acceptance criteria: fieldwork scope and sampling appropriate to the site, laboratory results summarized, hazards rated with mitigations, and licensed geoscience/engineering signature recorded.
- Utility/grid interconnection feasibility letter — acceptance criteria: artifact is published to the workspace with an owner, acceptance evidence, and review date recorded.


### Domain: Program Delivery

**Status**: <code>YELLOW</code>

**Metrics**: evidence=2, risk=3, fit=4

**Issues:**

- <code>CRITICAL_PATH_UNKNOWN</code>: Integrated master schedule (CPM) with logic ties and baseline

**Evidence Needed:**

- PMO charter + roles/RACI — acceptance criteria: artifact is published to the workspace with an owner, acceptance evidence, and review date recorded.
- Integrated master schedule (CPM) with critical path — acceptance criteria: artifact is published to the workspace with an owner, acceptance evidence, and review date recorded.

