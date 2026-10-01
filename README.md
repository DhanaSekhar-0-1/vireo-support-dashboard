# Vireo Audio — Support Operations Dashboard

AI-assisted support-operations dashboard built for the **Vireo Audio — Support Tickets (Set B)** assessment.

The application turns support-ticket data into deterministic operational metrics, training-priority signals, business-impact estimates, validation evidence, and an optional AI explanation layer.

---

## 1. Quick Navigation

### Main documentation

- [Memo to Priya](docs/memo-to-priya.md) — non-technical management summary and business recommendation context.
- [Validation Evidence](docs/validation.md) — independent 100-ticket validation and calculation checks.
- [Submission Form](submission-form.md) — assessment decisions, scope, AI disclosure, limitations, and final outcome.

### Main application areas

- `frontend/` — React + TypeScript + Vite dashboard.
- `backend/` — FastAPI + Python analytics/API service.
- `data/` — source CSV datasets used by the application.
- `scripts/` — validation and supporting scripts.
- `docs/` — assessment documentation.

---

## 2. What the Tool Does

The dashboard provides:

- Agent-level CSAT
- Average handle time
- SLA breach rate
- Replacement rate
- Training-priority review
- Period filters
- Team/site/tier filters
- Monthly operational trends
- Business-impact calculation
- Data-quality checks
- Agent detail drawer
- CSV, Excel and PDF exports
- AI-generated manager-facing explanations

The numerical calculations are deterministic. The AI is an explanation layer and does not calculate or override dashboard metrics.

---

## 3. Business Objective

The measurable business objective selected from the data is:

> **Reduce the Q2 2026 replacement rate from 17.46% toward 15%.**

Q2 2026 contains:

- 2,067 tickets
- 361 replacements
- 17.46% replacement rate

At the same ticket volume, a 15% replacement rate corresponds to approximately 51 fewer replacements.

Using the support-policy replacement-cost definition, this represents approximately:

> **₹91,263 potential quarterly cost avoided**

This is an opportunity estimate, not a guaranteed saving attributable to training alone.

See [Memo to Priya](docs/memo-to-priya.md) for the management-facing explanation.

---

## 4. Technology Stack

### Frontend

- React
- TypeScript
- Vite
- Recharts
- Axios
- XLSX
- jsPDF / AutoTable

### Backend

- Python
- FastAPI
- Pandas
- NumPy
- Uvicorn

### AI

- OpenRouter API
- NVIDIA Nemotron 3 Ultra
- Model: `nvidia/nemotron-3-ultra-550b-a55b:free`
- Free model tier

The AI is intentionally used after deterministic calculations:

```text
CSV data
   ↓
Pandas / deterministic calculations
   ↓
FastAPI
   ↓
Dashboard
   ↓
Calculated agent signals
   ↓
Nemotron explanation
```

The model is not used for per-ticket analysis or to determine the numerical metrics.

---

## 5. Project Structure

```text
vireo-support-dashboard/
│
├── backend/
│   ├── app/
│   │   ├── analytics/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── main.py
│   ├── .env
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── agents/
│   │   │   ├── ai/
│   │   │   ├── charts/
│   │   │   └── dashboard/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   └── package.json
│
├── data/
│   ├── agents.csv
│   ├── customers.csv
│   ├── orders.csv
│   ├── products.csv
│   └── tickets.csv
│
├── docs/
│   ├── memo-to-priya.md
│   └── validation.md
│
├── scripts/
│   └── validate_sample.py
│
└── submission-form.md
```

---

## 6. Setup

### Requirements

- Python 3.12
- Node.js
- npm

### Backend

Open PowerShell:

```powershell
cd D:\vireo-support-dashboard\backend
```

Create/activate the virtual environment:

```powershell
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create `backend/.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

### Frontend

Open another terminal:

```powershell
cd D:\vireo-support-dashboard\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally:

```text
http://localhost:5173
```

---

## 7. Main API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Backend health check |
| `GET /api/data/summary` | Dataset summary |
| `GET /api/data/quality` | Data-quality validation |
| `GET /api/agents` | Agent performance metrics |
| `GET /api/training-priority` | Training-priority signals |
| `GET /api/trends` | Monthly operational trends |
| `POST /api/ai/agent-explanation` | AI explanation for an agent |

---

# 8. Important Problems Faced and How They Were Solved

## Problem 1 — Incorrect handle-time values

### What happened

Initial handle-time calculations produced negative or extremely large values.

### Why

The dataset contains multiple timestamp conventions:

- Helpdesk timestamps are displayed in IST.
- Legacy resolution timestamps were reconstructed from UTC.

Subtracting timestamps without source-aware normalization produced incorrect durations.

### Decision

Normalize timestamps according to `source_system` before calculating handle time.

Conceptually:

```text
Helpdesk → interpret as IST
Legacy → interpret as UTC → convert to IST
```

Then:

```text
Handle time = resolution time - first response time
```

### Result

Negative handle times disappeared from the validated dataset.

The final validation sample also reported zero negative handle times.

---

## Problem 2 — Agent display names are not unique

### What happened

Two roster agents can share the same display name.

### Decision

Never join or identify agents using `name`.

Use:

```text
agent_id
```

as the stable identifier.

### Example

Instead of:

```python
merge(on="name")
```

use:

```python
merge(on="agent_id")
```

This prevents two agents with the same display name from being combined.

---

## Problem 3 — Raw bottom-ten ranking could be misleading

### What happened

The original business request asked for the bottom ten agents.

The supporting context also explains that:

- Queue mix affects customer interactions.
- Hardware triage and warranty queues receive difficult cases by design.
- Tier 2 work is multi-touch and measured in days.

### Decision

Do not present a raw bottom-ten ranking as definitive individual performance evidence.

Instead, create a **Training Priority** view using:

- CSAT
- Comparable peer CSAT
- Peer gap
- CSAT response confidence
- SLA breach rate

The dashboard currently identifies:

```text
Priority Review: 4
Watch: 3
```

The view is intended for coaching review rather than automatic disciplinary or bonus decisions.

---

## Problem 4 — Tier 2 should not be compared directly with Tier 1

### Why

Tier 2 work is multi-touch and measured in days.

Comparing Tier 2 and Tier 1 on volume metrics would mix fundamentally different workflows.

### Decision

Keep Tier 2 separate from Tier 1 volume comparisons.

A related consequence was removing the idea of treating overall AHT as a simple cross-tier performance ranking.

AHT remains useful at agent/detail level but must be interpreted with workflow context.

---

## Problem 5 — CSAT blanks

### What happened

Many tickets have no CSAT response.

### Incorrect approach avoided

Treating blank CSAT as zero would artificially reduce performance.

### Decision

Only actual survey responses contribute to CSAT.

Example:

```text
CSAT responses = 45
Blank responses = excluded
```

Therefore:

```text
CSAT = average of the 45 submitted scores
```

not an average where missing surveys are treated as zero.

---

## Problem 6 — Replacement cost assumptions conflicted

### What happened

The email context mentioned an approximate ₹2,500 replacement estimate.

The support policy specifies:

```text
Replacement cost = product unit cost + ₹340 logistics
```

### Decision

Use the formal support-policy definition for the business-impact calculation.

This produces a policy-consistent estimate instead of using the informal estimate.

---

## Problem 7 — Per-ticket AI would be expensive and unnecessary

### What happened

The dataset contains roughly 12,000 tickets, and the source context explicitly cautioned against expensive per-ticket model calls.

### Decision

Do not call the model for every ticket.

Instead:

```text
11,750 tickets
      ↓
Deterministic aggregation
      ↓
Agent-level signals
      ↓
AI explanation only when a manager opens an agent
```

This keeps the AI usage focused on the manager workflow.

---

## Problem 8 — AI initially exposed reasoning instead of the requested answer

### What happened

Nemotron sometimes returned planning/reasoning such as:

```text
The user wants...
Given data...
Let's craft...
```

instead of only returning:

```text
Summary
Signals
Coaching focus
Caveat
```

### Decision

Do not make the dashboard dependent on perfect model formatting.

The backend:

1. Requests a constrained manager-facing response.
2. Attempts to extract the four required sections.
3. Detects malformed/reasoning-heavy output.
4. Uses a deterministic fallback explanation when necessary.

This prevents model formatting issues from breaking the dashboard.

### Design principle

```text
AI failure
   ↓
Do not corrupt dashboard
   ↓
Use deterministic fallback
```

The calculated metrics remain the source of truth.

---

## Problem 9 — Frontend JSX integration error

### What happened

The AI component was initially inserted beside the drawer in `Dashboard.tsx`, which caused a JSX parsing error.

Vite reported:

```text
Unexpected token
```

### Decision

Integrate the AI explanation component inside the existing `AgentDetailDrawer`.

The final flow is:

```text
Agent Performance
       ↓
Select agent
       ↓
Agent Detail Drawer
       ↓
AI Performance Explanation
       ↓
Explain with AI
```

This keeps the AI explanation contextual to the selected agent.

---

## Problem 10 — AI service import error

### What happened

The frontend AI component imported:

```typescript
../../services/ai
```

but the `src/services/ai.ts` file had not yet been created.

Vite therefore reported:

```text
Failed to resolve import "../../services/ai"
```

### Solution

Created:

```text
frontend/src/services/ai.ts
```

The service sends:

```text
POST /api/ai/agent-explanation
```

to FastAPI and returns the model explanation to the drawer.

---

# 9. Validation

A deterministic sample of 100 tickets was independently recalculated.

Five categories were compared:

1. First-response time
2. SLA classification
3. Handle time
4. CSAT handling
5. Replacement classification

Result:

```text
500 metric comparisons
0 mismatches
0.00% comparison error rate
```

The validation sample included both:

```text
76 helpdesk tickets
24 legacy tickets
```

It also contained five unresolved/open/pending records without resolution timestamps, which were treated as expected missing values.

Full evidence:

→ [Validation Evidence](docs/validation.md)

---

# 10. Data-Quality Checks

The dashboard checks for:

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

Current validation found no invalid agent IDs, CSAT values, channels, SLA targets, first-response times, or negative handle times.

---

# 11. Key Data Decisions

### Agent identity

Use `agent_id`, not display name.

### CSAT

Blank responses are excluded.

### Timestamps

Handle legacy and helpdesk timestamps according to their source conventions.

### Handle time

```text
First response → resolution
```

### Tier 2

Keep separate from Tier 1 volume comparisons.

### Replacement attribution

Do not assume a replacement is solely controlled by the resolving agent.

### Business impact

Use the policy-defined replacement cost.

---

# 12. Deliberately Out of Scope

The assessment had a five-hour effort cap, so the implementation prioritizes dashboard-first visibility.

### Not implemented: automatic Diwali bonus ranking

A top-five bonus recommendation was not automated.

Reason:

- Cross-tier comparison is not directly comparable.
- Queue mix affects observed outcomes.
- The available context does not provide sufficient basis for an automatic fair bonus decision.

### Not implemented: detailed root-cause analysis

The requested priority was dashboard-first visibility.

Detailed causal analysis was therefore left for a later phase.

### Not implemented: per-ticket AI analysis

The model is not called for every ticket because that would add unnecessary cost and latency.

---

# 13. AI Safety / Usage Boundary

The AI explanation layer is not the source of truth.

The following remain deterministic:

```text
CSAT
SLA classification
Handle time
Replacement counts
Replacement cost
Business-impact calculations
Training-priority calculations
```

The model receives already-calculated agent-level signals and produces a manager-facing explanation.

The AI does not:

- Change dashboard metrics
- Calculate the business baseline
- Assign replacement blame
- Make disciplinary decisions
- Make automatic bonus decisions
- Replace the deterministic validation layer

---

# 14. Business Impact Calculation

The dashboard uses Q2 2026 as the current baseline.

```text
Q2 tickets              2,067
Q2 replacements           361
Current replacement rate 17.46%

Target replacement rate  15.00%

Approx. target replacements 310
Approx. replacements avoided 51

Estimated quarterly cost avoided ≈ ₹91,263
```

The estimate assumes the same ticket volume and uses the policy-defined replacement cost.

It should be interpreted as potential cost avoidance, not guaranteed savings.

---

# 15. Recommended Demo Flow

For the assessment recording, demonstrate the application in this order:

### 1. Dashboard

Show:

- Ticket volume
- CSAT
- SLA breach rate
- Replacement rate
- Training priority
- Business impact

### 2. Period/filter interaction

Change the period or team/site/tier filter and show that calculated views update.

### 3. Training Priority

Show:

```text
4 Priority Review
3 Watch
```

Explain that this is a coaching-review view, not a definitive bottom-ten ranking.

### 4. Agent detail

Open an agent.

Show:

- CSAT
- Handle time
- SLA signal
- Replacement activity
- Priority context

### 5. AI explanation

Click:

```text
Explain with AI
```

Show the four sections:

```text
Summary
Signals
Coaching focus
Caveat
```

### 6. Validation

Briefly show:

```text
100-ticket independent sample
500 comparisons
0 mismatches
0.00% error
```

### 7. Close with the business objective

```text
17.46% Q2 replacement rate
→ 15% target
→ ~51 fewer replacements
→ ~₹91K potential quarterly cost avoidance
```

---

# 16. Final Outcome

The application connects deterministic support analytics to a measurable business objective while keeping AI in an explanatory role.

The main measurable target is:

> **17.46% Q2 2026 replacement rate → 15% target → approximately 51 fewer replacements and ₹91K potential quarterly cost avoidance at the same volume.**

The dashboard also provides a controlled training-priority view rather than treating a raw bottom-ten list as definitive individual performance evidence.

---

## Assessment Documents

- [Memo to Priya](docs/memo-to-priya.md)
- [Validation Evidence](docs/validation.md)
- [Submission Form](submission-form.md)
