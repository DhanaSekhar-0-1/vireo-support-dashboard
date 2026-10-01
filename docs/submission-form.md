# Vireo Audio — Support Tickets (Set B)
## Submission Form

### 1. Working tool

**Project:** Vireo Audio Support Dashboard

**Stack:**
- React + TypeScript + Vite
- FastAPI + Python
- Pandas / NumPy
- Recharts
- Gemini API
- CSV source data

The application provides:
- Agent performance metrics
- CSAT analysis
- Handle-time analysis
- SLA breach analysis
- Replacement-rate analysis
- Training-priority review
- Period, team, site and tier filters
- Business-impact calculation
- Data-quality validation
- CSV / Excel / PDF exports
- Agent-level detail view

The core operational metrics are calculated deterministically. AI is intended as an explanation layer rather than the source of numerical calculations.

---

### 2. Business goal

The measurable business goal is:

> Reduce the Q2 2026 replacement rate from **17.46% toward 15%**.

Q2 2026 contains:
- 2,067 tickets
- 361 replacements
- 17.46% replacement rate

At the same ticket volume, a 15% replacement rate corresponds to approximately 310 replacements, or approximately **51 fewer replacements**.

Using the policy-defined replacement cost, this represents approximately **₹91,263 potential quarterly cost avoided**.

This is an opportunity estimate, not a guaranteed saving attributable to training alone.

---

### 3. Training prioritization

The original business request asked for the bottom ten.

Instead of presenting a simple bottom-ten ranking, the dashboard provides a **Training Priority** view.

The priority calculation considers:
- CSAT
- Comparable peer CSAT
- Peer gap
- CSAT response confidence
- SLA breach rate

The dashboard currently identifies:
- **4 Priority Review**
- **3 Watch**

Tier 2 agents are not compared with Tier 1 agents on volume metrics because Tier 2 work is multi-touch and measured in days.

The priority view is intended for coaching review, not automatic disciplinary or bonus decisions.

---

### 4. Data validation

A deterministic sample of **100 tickets** was independently recalculated.

Five calculation categories were compared:

1. First-response time
2. SLA classification
3. Handle time
4. CSAT handling
5. Replacement classification

Results:

| Check | Mismatches |
|---|---:|
| First response | 0 |
| SLA classification | 0 |
| Handle time | 0 |
| CSAT handling | 0 |
| Replacement classification | 0 |
| **Total** | **0 / 500** |

**Comparison error rate: 0.00%.**

The sample contained:
- 76 helpdesk tickets
- 24 legacy tickets
- 48 CSAT responses
- 17 replacement tickets
- 5 tickets without resolution timestamps

The missing resolution timestamps were associated with open/pending tickets in the validation sample.

---

### 5. Data-quality checks

The dashboard validates:
- Duplicate ticket IDs
- Missing agent IDs
- Unknown agent IDs
- Missing first-response timestamps
- Negative first-response times
- Resolved tickets without resolution timestamps
- Invalid handle times
- Invalid channels
- Invalid CSAT values
- Missing SLA targets
- Source-system coverage

Current dataset validation found no invalid agent IDs, CSAT values, channels, SLA targets, first-response times or negative handle times.

---

### 6. Important data decisions

**Agent identity:**  
Agent joins use `agent_id`, not display name, because display names are not unique.

**CSAT:**  
Blank CSAT responses are excluded rather than treated as zero.

**Timestamps:**  
Legacy and helpdesk timestamps require source-aware handling because their timestamp conventions differ.

**Handle time:**  
Handle time is measured from first response to resolution.

**Tier 2:**  
Tier 2 is kept separate from Tier 1 volume comparisons because the work is multi-touch and measured in days.

**Replacement attribution:**  
A replacement is not assumed to be solely controlled by the resolving agent because queue, product and case characteristics can influence replacement activity.

---

### 7. Scope decisions

Given the five-hour assessment constraint, the implementation prioritizes the requested operational dashboard and measurable business opportunity.

Included:
- Dashboard-first operational metrics
- Agent performance
- Training-priority review
- Business-impact calculation
- Data validation
- Period and operational filters
- Export functionality
- Agent detail view

Not fully automated:

**Diwali bonus recommendation:**  
No automatic top-five bonus ranking was implemented. The available data and policy context do not provide sufficient basis to make a fair cross-tier, cross-queue bonus decision.

**Root-cause analysis:**  
Detailed causal analysis was intentionally left for a later phase because Priya's stated priority was dashboard-first visibility.

**Per-ticket AI analysis:**  
Not used for all tickets because the source context explicitly cautions against expensive per-ticket model calls at approximately 12,000 tickets.

---

### 8. AI usage

AI assistance was used during development for:
- Code generation and refinement
- Debugging
- UI implementation
- Analytical reasoning support
- Documentation drafting

The dashboard's numerical calculations remain deterministic.

The deployed AI explanation layer uses:
- Provider: OpenRouter
- Model: NVIDIA Nemotron 3 Ultra
- Model ID: `nvidia/nemotron-3-ultra-550b-a55b:free`
- Cost: Free model tier

AI is used only to explain already-calculated agent performance signals. It does not calculate or override dashboard metrics.

AI should not be treated as the source of truth for:
- CSAT
- SLA classification
- Handle time
- Replacement counts
- Cost calculations

---

### 9. Known limitations

- CSAT represents only tickets with survey responses.
- Agent-level CSAT can be noisy with low response counts.
- Queue mix can affect apparent agent performance.
- Replacement activity is not necessarily fully agent-controlled.
- Handle time depends on workflow and case complexity.
- The validation result applies to the tested 100-ticket sample and five calculation categories; it is not proof that every possible edge case is error-free.
- The replacement-cost opportunity should be treated as an estimate rather than guaranteed savings.

---

### 10. Final outcome

The deliverable provides a working support-operations dashboard that connects the requested agent metrics to a measurable business objective:

> **17.46% Q2 2026 replacement rate → 15% target → approximately 51 fewer replacements and ₹91K potential quarterly cost avoidance at the same volume.**

The dashboard also provides a controlled training-priority view rather than treating a raw bottom-ten list as definitive individual performance evidence.