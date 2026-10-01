# Vireo Audio — Validation Evidence

## Validation approach

A deterministic sample of 100 tickets was selected from `tickets.csv` using random state 42.

The sample was independently recalculated rather than relying only on the application's existing metric functions.

The following calculations were independently checked against the application output:

- First-response time
- SLA classification
- Handle time
- CSAT handling
- Replacement classification

## Validation result

| Metric | Mismatches |
|---|---:|
| First response | 0 |
| SLA classification | 0 |
| Handle time | 0 |
| CSAT handling | 0 |
| Replacement classification | 0 |
| **Total** | **0 / 500** |

**Comparison error rate: 0.00%**

There were 500 metric-level comparisons across the 100-ticket sample.

## Sample observations

| Check | Result |
|---|---:|
| Tickets sampled | 100 |
| Records with first response | 100 |
| Negative first response | 0 |
| SLA-eligible tickets | 100 |
| SLA breaches | 8 |
| SLA breach rate | 8.00% |
| Valid handle-time records | 95 |
| Negative handle times | 0 |
| CSAT responses | 48 |
| Invalid CSAT values | 0 |
| Replacement tickets | 17 |
| Replacement rate | 17.00% |

## Source coverage

The sample contained:

- 76 helpdesk tickets
- 24 legacy tickets

This exercises both source systems in the validation sample.

Legacy resolution timestamps require source-aware timestamp handling because legacy timestamps are reconstructed from UTC while helpdesk timestamps are reported in IST.

## Missing resolution timestamps

Five sampled tickets had no resolution timestamp:

- 3 open
- 2 pending

These are treated as expected missing values rather than calculation errors because unresolved/open/pending tickets can legitimately lack a resolution timestamp.

## Known limitations

### Tier 2 comparability

Tier 2 work is multi-touch and measured in days. Tier 2 agents are therefore not compared with Tier 1 agents on volume metrics.

### CSAT coverage

CSAT is based only on tickets with a survey response. Blank CSAT values are excluded rather than treated as zero.

The validation sample contained 48 CSAT responses out of 100 tickets.

### Agent identity

Agent joins use `agent_id`, not display name. This avoids ambiguity where roster agents share a display name.

### Replacement attribution

Replacement issuance is not assumed to be solely controlled by an individual agent. Queue, product and case characteristics can affect replacement activity.

### Handle time

Handle time is defined as first response to resolution. Tickets without the required timestamps cannot contribute a valid handle-time measurement.

### Validation scope

The 0.00% comparison error rate applies to this deterministic 100-ticket validation sample and the five tested calculation categories. It should not be interpreted as proof that every possible record or edge case is error-free.