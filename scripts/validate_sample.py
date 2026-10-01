from pathlib import Path
import sys

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

# Allow imports from backend/
sys.path.insert(
    0,
    str(BASE_DIR / "backend"),
)


# =========================================================
# APPLICATION LOGIC
# =========================================================

from app.analytics.metrics import prepare_tickets


# =========================================================
# CONFIGURATION
# =========================================================

SAMPLE_SIZE = 100
RANDOM_STATE = 42

IST = "Asia/Kolkata"

SLA_TARGETS = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def find_existing_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    """
    Return the first candidate column that exists.
    """
    for column in candidates:
        if column in df.columns:
            return column

    return None


def compare_series(
    expected: pd.Series,
    actual: pd.Series,
    tolerance: float = 0.001,
) -> int:
    """
    Compare two Series while treating matching NaN values
    as equal.

    For numeric values, a small tolerance is allowed.
    """
    expected_numeric = pd.to_numeric(
        expected,
        errors="coerce",
    )

    actual_numeric = pd.to_numeric(
        actual,
        errors="coerce",
    )

    both_missing = (
        expected_numeric.isna()
        & actual_numeric.isna()
    )

    numeric_difference = (
        expected_numeric
        - actual_numeric
    ).abs()

    mismatch = (
        ~both_missing
        & (
            numeric_difference
            > tolerance
        )
    )

    return int(mismatch.sum())


def compare_boolean_series(
    expected: pd.Series,
    actual: pd.Series,
) -> int:
    """
    Compare boolean classifications.
    """
    expected_bool = (
        expected
        .fillna(False)
        .astype(bool)
    )

    actual_bool = (
        actual
        .fillna(False)
        .astype(bool)
    )

    return int(
        (
            expected_bool
            != actual_bool
        ).sum()
    )


# =========================================================
# LOAD SOURCE DATA
# =========================================================

tickets = pd.read_csv(
    DATA_DIR / "tickets.csv"
)


# =========================================================
# DETERMINISTIC SAMPLE
# =========================================================

sample = tickets.sample(
    n=SAMPLE_SIZE,
    random_state=RANDOM_STATE,
).copy()

sample = sample.reset_index(drop=True)


# =========================================================
# RUN APPLICATION PREPARATION LOGIC
# =========================================================

application_sample = prepare_tickets(
    sample.copy()
)

application_sample = (
    application_sample.reset_index(drop=True)
)


# =========================================================
# INDEPENDENT TIMESTAMP CALCULATIONS
# =========================================================

created_at = pd.to_datetime(
    sample["created_at"],
    errors="coerce",
)

first_response_at = pd.to_datetime(
    sample["first_response_at"],
    errors="coerce",
)

resolved_raw = pd.to_datetime(
    sample["resolved_at"],
    errors="coerce",
)


# ---------------------------------------------------------
# Normalize created_at / first_response_at to IST
# ---------------------------------------------------------

if created_at.dt.tz is None:
    created_at = created_at.dt.tz_localize(
        IST
    )
else:
    created_at = created_at.dt.tz_convert(
        IST
    )


if first_response_at.dt.tz is None:
    first_response_at = (
        first_response_at
        .dt.tz_localize(IST)
    )
else:
    first_response_at = (
        first_response_at
        .dt.tz_convert(IST)
    )


# ---------------------------------------------------------
# Source-aware resolution timestamp
# ---------------------------------------------------------

resolved_at = pd.Series(
    pd.NaT,
    index=sample.index,
    dtype=f"datetime64[ns, {IST}]",
)


legacy_mask = sample[
    "source_system"
].eq("legacy_fd")


helpdesk_mask = sample[
    "source_system"
].eq("helpdesk")


legacy_resolved = resolved_raw[
    legacy_mask
].copy()


helpdesk_resolved = resolved_raw[
    helpdesk_mask
].copy()


if not legacy_resolved.empty:

    if legacy_resolved.dt.tz is None:
        legacy_resolved = (
            legacy_resolved
            .dt.tz_localize("UTC")
            .dt.tz_convert(IST)
        )
    else:
        legacy_resolved = (
            legacy_resolved
            .dt.tz_convert(IST)
        )

    resolved_at.loc[
        legacy_mask
    ] = legacy_resolved


if not helpdesk_resolved.empty:

    if helpdesk_resolved.dt.tz is None:
        helpdesk_resolved = (
            helpdesk_resolved
            .dt.tz_localize(IST)
        )
    else:
        helpdesk_resolved = (
            helpdesk_resolved
            .dt.tz_convert(IST)
        )

    resolved_at.loc[
        helpdesk_mask
    ] = helpdesk_resolved


# =========================================================
# INDEPENDENT FIRST RESPONSE
# =========================================================

first_response_minutes = (
    first_response_at
    - created_at
).dt.total_seconds() / 60


negative_first_response = (
    first_response_minutes.notna()
    & (
        first_response_minutes < 0
    )
)


# =========================================================
# INDEPENDENT SLA CALCULATION
# =========================================================

sla_target = sample[
    "channel"
].map(
    SLA_TARGETS
)


sla_eligible = (
    first_response_at.notna()
    & sla_target.notna()
    & first_response_minutes.notna()
    & (
        first_response_minutes >= 0
    )
)


sla_breach = (
    sla_eligible
    & (
        first_response_minutes
        > sla_target
    )
)


# =========================================================
# INDEPENDENT HANDLE TIME
# =========================================================

handle_time_minutes = (
    resolved_at
    - first_response_at
).dt.total_seconds() / 60


valid_handle_time = (
    first_response_at.notna()
    & resolved_at.notna()
    & handle_time_minutes.notna()
    & (
        handle_time_minutes >= 0
    )
)


negative_handle_time = (
    handle_time_minutes.notna()
    & (
        handle_time_minutes < 0
    )
)


# =========================================================
# INDEPENDENT CSAT
# =========================================================

csat = pd.to_numeric(
    sample["csat_score"],
    errors="coerce",
)


valid_csat = (
    csat.notna()
    & csat.between(1, 5)
)


invalid_csat = (
    csat.notna()
    & ~csat.between(1, 5)
)


# =========================================================
# INDEPENDENT REPLACEMENT CLASSIFICATION
# =========================================================

replacement_flag = (
    sample[
        "replacement_issued"
    ]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
    .eq("Y")
)


# =========================================================
# FIND APPLICATION COLUMNS
# =========================================================

application_sla_column = find_existing_column(
    application_sample,
    [
        "sla_breached",
        "sla_breach",
        "sla_breach_flag",
        "is_sla_breach",
    ],
)


application_handle_column = (
    find_existing_column(
        application_sample,
        [
            "handle_time_minutes",
        ],
    )
)


application_first_response_column = (
    find_existing_column(
        application_sample,
        [
            "first_response_minutes",
        ],
    )
)


application_csat_column = (
    find_existing_column(
        application_sample,
        [
            "csat_score",
        ],
    )
)


application_replacement_column = (
    find_existing_column(
        application_sample,
        [
            "replacement_issued",
        ],
    )
)


# =========================================================
# APPLICATION VS INDEPENDENT COMPARISON
# =========================================================

comparison = {}


# ---------------------------------------------------------
# First response comparison
# ---------------------------------------------------------

if application_first_response_column:

    first_response_mismatches = compare_series(
        first_response_minutes,
        application_sample[
            application_first_response_column
        ],
    )

    comparison[
        "First response"
    ] = first_response_mismatches

else:

    comparison[
        "First response"
    ] = None


# ---------------------------------------------------------
# SLA comparison
# ---------------------------------------------------------

if application_sla_column:

    application_sla_breach = (
        application_sample[
            application_sla_column
        ]
        .fillna(False)
        .astype(bool)
    )

    sla_mismatches = (
        compare_boolean_series(
            sla_breach,
            application_sla_breach,
        )
    )

    comparison[
        "SLA classification"
    ] = sla_mismatches

else:

    comparison[
        "SLA classification"
    ] = None


# ---------------------------------------------------------
# Handle-time comparison
# ---------------------------------------------------------

if application_handle_column:

    handle_mismatches = compare_series(
        handle_time_minutes,
        application_sample[
            application_handle_column
        ],
    )

    comparison[
        "Handle time"
    ] = handle_mismatches

else:

    comparison[
        "Handle time"
    ] = None


# ---------------------------------------------------------
# CSAT comparison
# ---------------------------------------------------------

if application_csat_column:

    csat_mismatches = compare_series(
        csat,
        application_sample[
            application_csat_column
        ],
    )

    comparison[
        "CSAT handling"
    ] = csat_mismatches

else:

    comparison[
        "CSAT handling"
    ] = None


# ---------------------------------------------------------
# Replacement comparison
# ---------------------------------------------------------

if application_replacement_column:

    application_replacement = (
        application_sample[
            application_replacement_column
        ]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
    )

    replacement_mismatches = (
        compare_boolean_series(
            replacement_flag,
            application_replacement,
        )
    )

    comparison[
        "Replacement classification"
    ] = replacement_mismatches

else:

    comparison[
        "Replacement classification"
    ] = None


# =========================================================
# VALIDATION SAMPLE REPORT
# =========================================================

print()

print("=" * 60)
print("VIREO AUDIO — VALIDATION SAMPLE")
print("=" * 60)

print(
    f"Sample size: {SAMPLE_SIZE}"
)

print(
    f"Random state: {RANDOM_STATE}"
)

print()


# =========================================================
# FIRST RESPONSE
# =========================================================

print("FIRST RESPONSE")
print("-" * 60)

print(
    "Records with first response:",
    int(
        first_response_at.notna().sum()
    ),
)

print(
    "Negative first response:",
    int(
        negative_first_response.sum()
    ),
)

print()


# =========================================================
# SLA
# =========================================================

print("SLA")
print("-" * 60)

print(
    "SLA-eligible tickets:",
    int(
        sla_eligible.sum()
    ),
)

print(
    "SLA breaches:",
    int(
        sla_breach.sum()
    ),
)

if sla_eligible.sum() > 0:

    print(
        "SLA breach rate:",
        f"{sla_breach.sum() / sla_eligible.sum():.2%}",
    )

else:

    print(
        "SLA breach rate: N/A"
    )

print()


# =========================================================
# HANDLE TIME
# =========================================================

print("HANDLE TIME")
print("-" * 60)

print(
    "Valid handle-time records:",
    int(
        valid_handle_time.sum()
    ),
)

print(
    "Negative handle times:",
    int(
        negative_handle_time.sum()
    ),
)

if valid_handle_time.sum() > 0:

    print(
        "Average valid handle time:",
        f"{handle_time_minutes[valid_handle_time].mean():.2f} min",
    )

else:

    print(
        "Average valid handle time: N/A"
    )

print()


# =========================================================
# CSAT
# =========================================================

print("CSAT")
print("-" * 60)

print(
    "CSAT responses:",
    int(
        csat.notna().sum()
    ),
)

print(
    "Invalid CSAT values:",
    int(
        invalid_csat.sum()
    ),
)

if valid_csat.sum() > 0:

    print(
        "Average CSAT:",
        f"{csat[valid_csat].mean():.2f}",
    )

else:

    print(
        "Average CSAT: N/A"
    )

print()


# =========================================================
# REPLACEMENTS
# =========================================================

print("REPLACEMENTS")
print("-" * 60)

print(
    "Replacement tickets:",
    int(
        replacement_flag.sum()
    ),
)

print(
    "Replacement rate:",
    f"{replacement_flag.mean():.2%}",
)

print()


# =========================================================
# SOURCE COVERAGE
# =========================================================

print("SOURCE COVERAGE")
print("-" * 60)

print(
    sample[
        "source_system"
    ]
    .value_counts()
    .to_string()
)

print()


# =========================================================
# MISSING RESOLUTION
# =========================================================

print("MISSING RESOLUTION")
print("-" * 60)

missing_resolution = (
    resolved_at.isna()
)

print(
    "Missing resolution timestamps:",
    int(
        missing_resolution.sum()
    ),
)

print(
    "Statuses of missing resolutions:"
)

missing_statuses = sample.loc[
    missing_resolution,
    "status",
].value_counts()


if len(missing_statuses) > 0:

    print(
        missing_statuses.to_string()
    )

else:

    print(
        "None"
    )

print()


# =========================================================
# APPLICATION COMPARISON
# =========================================================

print(
    "APPLICATION VS INDEPENDENT CALCULATION"
)

print("-" * 60)


for metric, mismatches in comparison.items():

    if mismatches is None:

        print(
            f"{metric:<32} NOT AVAILABLE"
        )

    else:

        print(
            f"{metric:<32} "
            f"{mismatches} mismatch(es)"
        )


# =========================================================
# OVERALL COMPARISON ERROR RATE
# =========================================================

available_comparisons = [
    value
    for value in comparison.values()
    if value is not None
]


if available_comparisons:

    total_mismatches = sum(
        available_comparisons
    )

    total_comparison_checks = (
        SAMPLE_SIZE
        * len(available_comparisons)
    )

    comparison_error_rate = (
        total_mismatches
        / total_comparison_checks
    )

else:

    total_mismatches = 0
    total_comparison_checks = 0
    comparison_error_rate = 0


print()

print(
    f"Total mismatches: "
    f"{total_mismatches}"
)

print(
    f"Comparison checks: "
    f"{total_comparison_checks}"
)

print(
    f"Comparison error rate: "
    f"{comparison_error_rate:.2%}"
)


# =========================================================
# APPLICATION COLUMNS USED
# =========================================================

print()

print(
    "APPLICATION COLUMNS USED"
)

print("-" * 60)

print(
    "First response:",
    application_first_response_column
    or "NOT FOUND",
)

print(
    "SLA:",
    application_sla_column
    or "NOT FOUND",
)

print(
    "Handle time:",
    application_handle_column
    or "NOT FOUND",
)

print(
    "CSAT:",
    application_csat_column
    or "NOT FOUND",
)

print(
    "Replacement:",
    application_replacement_column
    or "NOT FOUND",
)


# =========================================================
# COMPLETION
# =========================================================

print()

print("=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)