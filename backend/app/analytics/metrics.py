import pandas as pd
import numpy as np


IST = "Asia/Kolkata"

SLA_TARGETS_MINUTES = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}

MIN_CSAT_RESPONSES = 10
FULL_CONFIDENCE_RESPONSES = 20

def filter_tickets_by_period(
    tickets,
    start_date=None,
    end_date=None,
):
    """
    Filter tickets using created_at.

    Dates are interpreted as the timestamps displayed
    by the helpdesk (IST).
    """

    if not start_date and not end_date:
        return tickets.copy()

    df = tickets.copy()

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce",
    )

    if start_date:
        start = pd.Timestamp(start_date)
        df = df[df["created_at"] >= start]

    if end_date:
        # Inclusive end date.
        end = (
            pd.Timestamp(end_date)
            + pd.Timedelta(days=1)
        )

        df = df[df["created_at"] < end]

    return df.copy()
    
def prepare_tickets(tickets: pd.DataFrame) -> pd.DataFrame:

    df = tickets.copy()

    # ---------------------------------------------------------
    # CREATED / FIRST RESPONSE
    # These are helpdesk display timestamps = IST
    # ---------------------------------------------------------

    for column in [
        "created_at",
        "first_response_at",
    ]:

        parsed = pd.to_datetime(
            df[column],
            errors="coerce",
        )

        df[column] = (
            parsed.dt.tz_localize(
                IST,
                ambiguous="NaT",
                nonexistent="NaT",
            )
        )

    # ---------------------------------------------------------
    # RESOLVED AT
    #
    # helpdesk   -> IST
    # legacy_fd  -> UTC -> IST
    # ---------------------------------------------------------

    resolved = pd.to_datetime(
        df["resolved_at"],
        errors="coerce",
    )

    legacy_mask = (
        df["source_system"] == "legacy_fd"
    )

    helpdesk_mask = (
        df["source_system"] == "helpdesk"
    )

    legacy_resolved = (
        resolved.loc[legacy_mask]
        .dt.tz_localize(
            "UTC",
            ambiguous="NaT",
            nonexistent="NaT",
        )
        .dt.tz_convert(IST)
    )

    helpdesk_resolved = (
        resolved.loc[helpdesk_mask]
        .dt.tz_localize(
            IST,
            ambiguous="NaT",
            nonexistent="NaT",
        )
    )

    # Start with a timezone-aware series.
    normalized_resolved = pd.Series(
        pd.NaT,
        index=df.index,
        dtype="datetime64[ns, Asia/Kolkata]",
    )

    normalized_resolved.loc[
        legacy_mask
    ] = legacy_resolved

    normalized_resolved.loc[
        helpdesk_mask
    ] = helpdesk_resolved

    df["resolved_at_normalized"] = (
        normalized_resolved
    )

    # ---------------------------------------------------------
    # NUMERIC FIELDS
    # ---------------------------------------------------------

    df["csat_score"] = pd.to_numeric(
        df["csat_score"],
        errors="coerce",
    )

    df["transfers"] = pd.to_numeric(
        df["transfers"],
        errors="coerce",
    ).fillna(0)

    # ---------------------------------------------------------
    # FIRST RESPONSE TIME
    # ---------------------------------------------------------

    df["first_response_minutes"] = (
        df["first_response_at"]
        - df["created_at"]
    ).dt.total_seconds() / 60

    # ---------------------------------------------------------
    # HANDLE TIME
    #
    # Policy:
    # first response -> resolution
    # ---------------------------------------------------------

    df["handle_time_minutes"] = (
        df["resolved_at_normalized"]
        - df["first_response_at"]
    ).dt.total_seconds() / 60

    # ---------------------------------------------------------
    # SLA
    # ---------------------------------------------------------

    df["sla_target_minutes"] = (
        df["channel"].map(
            SLA_TARGETS_MINUTES
        )
    )

    df["sla_eligible"] = (
        df["first_response_at"].notna()
        & df["sla_target_minutes"].notna()
        & (
            df["first_response_minutes"]
            >= 0
        )
    )

    df["sla_breach"] = (
        df["sla_eligible"]
        & (
            df["first_response_minutes"]
            > df["sla_target_minutes"]
        )
    )

    # ---------------------------------------------------------
    # VALID HANDLE TIME
    # ---------------------------------------------------------

    df["valid_handle_time"] = (
        df["first_response_at"].notna()
        & df["resolved_at_normalized"].notna()
        & (
            df["handle_time_minutes"]
            >= 0
        )
    )

    # Remove impossible handle times
    df.loc[
        ~df["valid_handle_time"],
        "handle_time_minutes",
    ] = np.nan

    # ---------------------------------------------------------
    # REPLACEMENT
    # ---------------------------------------------------------

    df["replacement_flag"] = (
        df["replacement_issued"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("Y")
    )

    # ---------------------------------------------------------
    # ATTENDANCE
    # ---------------------------------------------------------

    df["attendance"] = (
        df["status"].isin(
            ["resolved", "closed"]
        )
    )

    return df


def validate_tickets(
    tickets: pd.DataFrame,
    agents: pd.DataFrame,
) -> dict:

    df = prepare_tickets(tickets)

    roster_ids = set(
        agents["agent_id"]
        .dropna()
        .astype(str)
    )

    ticket_agent_ids = set(
        df["agent_id"]
        .dropna()
        .astype(str)
    )

    unknown_agents = (
        ticket_agent_ids - roster_ids
    )

    csat_numeric = pd.to_numeric(
        df["csat_score"],
        errors="coerce",
    )

    invalid_csat = (
        csat_numeric.notna()
        & ~csat_numeric.between(1, 5)
    )

    invalid_channels = (
        ~df["channel"].isin(
            SLA_TARGETS_MINUTES.keys()
        )
    )

    resolved_status = df["status"].isin(
        ["resolved", "closed"]
    )

    negative_first_response = (
        df["first_response_minutes"].notna()
        & (
            df["first_response_minutes"]
            < 0
        )
    )

    negative_handle = (
        df["first_response_at"].notna()
        & df["resolved_at_normalized"].notna()
        & df["handle_time_minutes"].notna()
        & (
            df["handle_time_minutes"]
            < 0
        )
    )

    return {
        "total_tickets": int(
            len(df)
        ),

        "duplicate_ticket_ids": int(
            df["ticket_id"]
            .duplicated()
            .sum()
        ),

        "missing_agent_id": int(
            df["agent_id"]
            .isna()
            .sum()
        ),

        "unknown_agent_ids": int(
            len(unknown_agents)
        ),

        "missing_first_response": int(
            df["first_response_at"]
            .isna()
            .sum()
        ),

        "negative_first_response": int(
            negative_first_response.sum()
        ),

        "resolved_without_resolution": int(
            (
                resolved_status
                & df[
                    "resolved_at_normalized"
                ].isna()
            ).sum()
        ),

        "negative_handle_time": int(
            negative_handle.sum()
        ),

        "invalid_handle_time": int(
            negative_handle.sum()
        ),

        "invalid_channels": int(
            invalid_channels.sum()
        ),

        "invalid_csat": int(
            invalid_csat.sum()
        ),

        "missing_sla_target": int(
            df[
                "sla_target_minutes"
            ].isna().sum()
        ),

        "legacy_tickets": int(
            (
                df["source_system"]
                == "legacy_fd"
            ).sum()
        ),

        "helpdesk_tickets": int(
            (
                df["source_system"]
                == "helpdesk"
            ).sum()
        ),

        "missing_resolution_total": int(
            df[
                "resolved_at_normalized"
            ].isna().sum()
        ),
    }


def merge_agent_roster(
    df: pd.DataFrame,
    agents: pd.DataFrame,
) -> pd.DataFrame:

    agent_info = agents[
        [
            "agent_id",
            "name",
            "site",
            "team",
            "shift",
            "tier",
        ]
    ].copy()

    return df.merge(
        agent_info,
        on="agent_id",
        how="left",
    )


def calculate_agent_metrics(
    tickets: pd.DataFrame,
    agents: pd.DataFrame,
) -> pd.DataFrame:

    df = prepare_tickets(
        tickets
    )

    df = merge_agent_roster(
        df,
        agents,
    )

    # Tier 2 excluded.
    df = df[
        df["tier"] == 1
    ].copy()

    result = (
        df.groupby(
            [
                "agent_id",
                "name",
                "site",
                "team",
                "shift",
                "tier",
            ],
            dropna=False,
        )
        .agg(
            tickets=(
                "ticket_id",
                "count",
            ),

            csat_responses=(
                "csat_score",
                "count",
            ),

            csat=(
                "csat_score",
                "mean",
            ),

            avg_handle_time_minutes=(
                "handle_time_minutes",
                "mean",
            ),

            sla_breaches=(
                "sla_breach",
                "sum",
            ),

            sla_eligible=(
                "sla_eligible",
                "sum",
            ),

            resolved_or_closed=(
                "attendance",
                "sum",
            ),

            replacements=(
                "replacement_flag",
                "sum",
            ),

            transfers=(
                "transfers",
                "sum",
            ),
        )
        .reset_index()
    )

    result["sla_breach_rate"] = np.where(
        result["sla_eligible"] > 0,
        (
            result["sla_breaches"]
            / result["sla_eligible"]
        ),
        np.nan,
    )

    result["replacement_rate"] = (
        result["replacements"]
        / result["tickets"]
    )

    result["attendance_rate"] = (
        result["resolved_or_closed"]
        / result["tickets"]
    )

    return result


def calculate_training_priority(
    tickets: pd.DataFrame,
    agents: pd.DataFrame,
) -> pd.DataFrame:

    df = prepare_tickets(
        tickets
    )

    df = merge_agent_roster(
        df,
        agents,
    )

    # Tier 2 excluded.
    df = df[
        df["tier"] == 1
    ].copy()

    # ---------------------------------------------------------
    # Agent + channel
    # ---------------------------------------------------------

    channel_metrics = (
        df.groupby(
            [
                "agent_id",
                "name",
                "site",
                "team",
                "shift",
                "tier",
                "channel",
            ],
            dropna=False,
        )
        .agg(
            tickets=(
                "ticket_id",
                "count",
            ),

            csat_responses=(
                "csat_score",
                "count",
            ),

            csat_sum=(
                "csat_score",
                "sum",
            ),

            csat=(
                "csat_score",
                "mean",
            ),

            avg_handle_time_minutes=(
                "handle_time_minutes",
                "mean",
            ),

            sla_breaches=(
                "sla_breach",
                "sum",
            ),

            sla_eligible=(
                "sla_eligible",
                "sum",
            ),

            replacements=(
                "replacement_flag",
                "sum",
            ),

            transfers=(
                "transfers",
                "sum",
            ),
        )
        .reset_index()
    )

    channel_metrics[
        "sla_breach_rate"
    ] = np.where(
        channel_metrics[
            "sla_eligible"
        ] > 0,

        channel_metrics[
            "sla_breaches"
        ]
        / channel_metrics[
            "sla_eligible"
        ],

        np.nan,
    )

    channel_metrics[
        "replacement_rate"
    ] = (
        channel_metrics[
            "replacements"
        ]
        / channel_metrics[
            "tickets"
        ]
    )

    # ---------------------------------------------------------
    # Peer benchmark
    # Same team + same channel
    # ---------------------------------------------------------

    peer = (
        channel_metrics.groupby(
            [
                "team",
                "channel",
            ],
            dropna=False,
        )
        .agg(
            peer_csat_sum=(
                "csat_sum",
                "sum",
            ),

            peer_csat_responses=(
                "csat_responses",
                "sum",
            ),
        )
        .reset_index()
    )

    channel_metrics = channel_metrics.merge(
        peer,
        on=[
            "team",
            "channel",
        ],
        how="left",
    )

    # Remove current agent's own CSAT.
    channel_metrics[
        "other_csat_responses"
    ] = (
        channel_metrics[
            "peer_csat_responses"
        ]
        - channel_metrics[
            "csat_responses"
        ]
    )

    channel_metrics[
        "other_csat_sum"
    ] = (
        channel_metrics[
            "peer_csat_sum"
        ]
        - channel_metrics[
            "csat_sum"
        ]
    )

    channel_metrics[
        "peer_csat"
    ] = np.where(
        channel_metrics[
            "other_csat_responses"
        ] > 0,

        channel_metrics[
            "other_csat_sum"
        ]
        / channel_metrics[
            "other_csat_responses"
        ],

        np.nan,
    )

    channel_metrics[
        "peer_gap"
    ] = (
        channel_metrics["csat"]
        - channel_metrics["peer_csat"]
    )

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    channel_metrics[
        "confidence"
    ] = (
        channel_metrics[
            "csat_responses"
        ]
        / FULL_CONFIDENCE_RESPONSES
    ).clip(upper=1.0)

    # ---------------------------------------------------------
    # Priority score
    # ---------------------------------------------------------

    channel_metrics[
        "training_priority_score"
    ] = (
        -channel_metrics[
            "peer_gap"
        ]
        * channel_metrics[
            "confidence"
        ]
        + (
            0.20
            * channel_metrics[
                "sla_breach_rate"
            ].fillna(0)
        )
    )

    # ---------------------------------------------------------
    # Aggregate to ONE row per agent
    # ---------------------------------------------------------

    rows = []

    for agent_id, group in channel_metrics.groupby(
        "agent_id"
    ):

        first = group.iloc[0]

        tickets_total = int(
            group["tickets"].sum()
        )

        csat_responses = int(
            group[
                "csat_responses"
            ].sum()
        )

        csat_sum = group[
            "csat_sum"
        ].sum()

        sla_eligible = int(
            group[
                "sla_eligible"
            ].sum()
        )

        # Weighted by CSAT response count.
        valid_peer = (
            group["peer_gap"].notna()
            & group[
                "csat_responses"
            ].gt(0)
        )

        if valid_peer.any():

            peer_gap = np.average(
                group.loc[
                    valid_peer,
                    "peer_gap",
                ],

                weights=group.loc[
                    valid_peer,
                    "csat_responses",
                ],
            )

            priority_score = np.average(
                group.loc[
                    valid_peer,
                    "training_priority_score",
                ],

                weights=group.loc[
                    valid_peer,
                    "csat_responses",
                ],
            )

        else:
            peer_gap = np.nan
            priority_score = np.nan

        rows.append(
            {
                "agent_id": agent_id,
                "name": first["name"],
                "site": first["site"],
                "team": first["team"],
                "shift": first["shift"],
                "tier": first["tier"],

                "tickets": tickets_total,

                "csat_responses": csat_responses,

                "csat": (
                    csat_sum
                    / csat_responses
                    if csat_responses > 0
                    else np.nan
                ),

                "avg_handle_time_minutes": (
                    group[
                        "avg_handle_time_minutes"
                    ]
                    .mean()
                ),

                "sla_breach_rate": (
                    group[
                        "sla_breaches"
                    ].sum()
                    / sla_eligible
                    if sla_eligible > 0
                    else np.nan
                ),

                "replacement_rate": (
                    group[
                        "replacements"
                    ].sum()
                    / tickets_total
                    if tickets_total > 0
                    else np.nan
                ),

                "transfers": int(
                    group[
                        "transfers"
                    ].sum()
                ),

                "peer_gap": peer_gap,

                "training_priority_score": (
                    priority_score
                ),
            }
        )

    result = pd.DataFrame(
        rows
    )

    result[
        "confidence"
    ] = (
        result[
            "csat_responses"
        ]
        / FULL_CONFIDENCE_RESPONSES
    ).clip(upper=1.0)

    result[
        "priority"
    ] = "Normal"

    insufficient = (
        result[
            "csat_responses"
        ]
        < MIN_CSAT_RESPONSES
    )

    watch = (
        (
            result[
                "csat_responses"
            ]
            >= MIN_CSAT_RESPONSES
        )
        & result[
            "peer_gap"
        ].notna()
        & (
            result[
                "peer_gap"
            ]
            <= -0.10
        )
    )

    priority_review = (
        (
            result[
                "csat_responses"
            ]
            >= MIN_CSAT_RESPONSES
        )
        & result[
            "peer_gap"
        ].notna()
        & (
            result[
                "peer_gap"
            ]
            <= -0.25
        )
    )

    result.loc[
        insufficient,
        "priority",
    ] = "Insufficient data"

    result.loc[
        watch,
        "priority",
    ] = "Watch"

    result.loc[
        priority_review,
        "priority",
    ] = "Priority review"

    return result.sort_values(
        "training_priority_score",
        ascending=False,
        na_position="last",
    )
    
def calculate_monthly_trends(tickets):
    """
    Calculate monthly operational trends from deterministic ticket data.

    Metrics:
    - ticket volume
    - CSAT
    - SLA breach rate
    - replacement rate
    - average handle time
    """

    df = prepare_tickets(tickets).copy()

    # Use created_at for monthly ticket reporting.
    df["created_month"] = (
        df["created_at"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        df.groupby("created_month")
        .agg(
            tickets=("ticket_id", "count"),
            csat_responses=("csat_score", "count"),
            csat=("csat_score", "mean"),
            sla_breaches=("sla_breach", "sum"),
            sla_eligible=("sla_eligible", "sum"),
            replacements=("replacement_flag", "sum"),
            avg_handle_time_minutes=(
                "handle_time_minutes",
                "mean",
            ),
        )
        .reset_index()
    )

    monthly["sla_breach_rate"] = (
        monthly["sla_breaches"]
        / monthly["sla_eligible"].replace(0, pd.NA)
    ).fillna(0)

    monthly["replacement_rate"] = (
        monthly["replacements"]
        / monthly["tickets"].replace(0, pd.NA)
    ).fillna(0)

    monthly["csat"] = monthly["csat"].fillna(0)
    monthly["avg_handle_time_minutes"] = (
        monthly["avg_handle_time_minutes"]
        .fillna(0)
    )

    return monthly