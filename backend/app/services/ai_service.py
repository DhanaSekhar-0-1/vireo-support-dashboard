import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ==================================================
# ENVIRONMENT
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ==================================================
# CONFIGURATION
# ==================================================

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

OPENROUTER_BASE_URL = (
    "https://openrouter.ai/api/v1"
)


# ==================================================
# FALLBACK EXPLANATION
# ==================================================

def fallback_explanation(agent: dict) -> str:
    """
    Deterministic fallback used when the model does not
    return a usable manager-facing response.

    This does not calculate new business metrics.
    """

    agent_id = agent.get("agent_id", "")
    site = agent.get("site", "")
    team = agent.get("team", "")
    tier = agent.get("tier", "")

    tickets = agent.get("tickets", 0)
    csat = agent.get("csat")
    csat_responses = agent.get("csat_responses", 0)

    aht = agent.get(
        "avg_handle_time_minutes"
    )

    sla_breaches = agent.get(
        "sla_breaches",
        0,
    )

    sla_rate = agent.get(
        "sla_breach_rate"
    )

    replacements = agent.get(
        "replacements",
        0,
    )

    transfers = agent.get(
        "transfers",
        0,
    )

    peer_csat = agent.get(
        "peer_csat"
    )

    peer_gap = agent.get(
        "peer_gap"
    )

    priority = agent.get(
        "priority"
    )

    # ------------------------------------------------
    # SUMMARY
    # ------------------------------------------------

        # ------------------------------------------------
    # SUMMARY
    # ------------------------------------------------

    summary_1 = (
        f"Agent {agent_id} in {site} {team} Tier {tier} "
        f"handled {tickets} tickets with a CSAT of "
        f"{csat} from {csat_responses} responses."
    )

    summary_2 = (
        f"Peer CSAT is {peer_csat} with a peer gap of "
        f"{peer_gap}, and the supplied priority status is "
        f"{priority}."
    )

    # ------------------------------------------------
    # SIGNALS
    # ------------------------------------------------

    signals = []

    if csat is not None:
        if peer_csat is not None and peer_gap is not None:
            signals.append(
                f"- CSAT: {csat} from "
                f"{csat_responses} responses; "
                f"peer CSAT: {peer_csat}; "
                f"peer gap: {peer_gap}."
            )
        else:
            signals.append(
                f"- CSAT: {csat} from "
                f"{csat_responses} responses."
            )

    if aht is not None:
        signals.append(
            f"- Average handle time: "
            f"{aht} minutes."
        )

        if sla_rate is not None:
           signals.append(
            f"- SLA breach rate: "
            f"{sla_rate:.0%} with "
            f"{sla_breaches} breaches."
          )

    if replacements is not None:
        signals.append(
            f"- Replacements: "
            f"{replacements}."
        )

    if transfers is not None:
        signals.append(
            f"- Transfers: "
            f"{transfers}."
        )

    # Exactly four signals
    signals = signals[:4]

    # ------------------------------------------------
    # COACHING
    # ------------------------------------------------

    coaching = [
        "- Review a sample of cases associated "
        "with the observed CSAT peer gap.",
        "- Review cases associated with the "
        "recorded SLA breach signal.",
    ]

    # ------------------------------------------------
    # CAVEAT
    # ------------------------------------------------

    caveat = (
        "CSAT is based only on survey responses, "
        "and queue or case mix can affect "
        "agent-level comparisons."
    )

    return (
        "Summary\n"
        f"{summary_1} {summary_2}\n\n"
        "Signals\n"
        + "\n".join(signals)
        + "\n\n"
        "Coaching focus\n"
        + "\n".join(coaching)
        + "\n\n"
        "Caveat\n"
        + caveat
    )


# ==================================================
# EXTRACT MANAGER ANSWER
# ==================================================

def extract_manager_answer(
    text: str,
) -> str | None:
    """
    Extract the requested four sections if the model
    actually produced them.

    Returns None when the model mostly returned
    reasoning/planning instead.
    """

    if not text:
        return None

    # Remove code fences
    text = text.replace(
        "```markdown",
        "",
    )

    text = text.replace(
        "```text",
        "",
    )

    text = text.replace(
        "```",
        "",
    )

    # ------------------------------------------------
    # Locate sections
    # ------------------------------------------------

    pattern = re.compile(
        r"(?im)^\s*"
        r"(Summary|Signals|Coaching focus|Caveat)"
        r"\s*:?\s*$"
    )

    matches = list(
        pattern.finditer(text)
    )

    # Need all four sections
    names = [
        match.group(1).lower()
        for match in matches
    ]

    required = {
        "summary",
        "signals",
        "coaching focus",
        "caveat",
    }

    if not required.issubset(set(names)):
        return None

    sections = {}

    for index, match in enumerate(matches):

        name = match.group(1).lower()

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        content = text[start:end].strip()

        sections[name] = content

    # ------------------------------------------------
    # Validate content
    # ------------------------------------------------

    if not sections.get("summary"):
        return None

    if not sections.get("signals"):
        return None

    if not sections.get("coaching focus"):
        return None

    if not sections.get("caveat"):
        return None

    # ------------------------------------------------
    # Remove accidental reasoning language
    # ------------------------------------------------

    suspicious_phrases = [
        "the user wants",
        "let me analyze",
        "let's craft",
        "i need to",
        "we need to",
        "given data",
        "rules:",
        "we must",
        "the prompt",
        "the instruction",
    ]

    lower_text = text.lower()

    for phrase in suspicious_phrases:
        if phrase in lower_text:
            return None

    # ------------------------------------------------
    # Return clean response
    # ------------------------------------------------

    return (
        "Summary\n"
        + sections["summary"]
        + "\n\n"
        "Signals\n"
        + sections["signals"]
        + "\n\n"
        "Coaching focus\n"
        + sections["coaching focus"]
        + "\n\n"
        "Caveat\n"
        + sections["caveat"]
    )


# ==================================================
# MAIN AI FUNCTION
# ==================================================

def explain_agent_performance(
    agent: dict,
) -> str:

    # ------------------------------------------------
    # API KEY
    # ------------------------------------------------

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            f"OPENROUTER_API_KEY is not configured "
            f"in {ENV_FILE}"
        )

    # ------------------------------------------------
    # CLIENT
    # ------------------------------------------------

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )

    # ------------------------------------------------
    # DATA SENT TO MODEL
    # ------------------------------------------------

    model_data = {
        "agent_id": agent.get(
            "agent_id"
        ),
        "site": agent.get(
            "site"
        ),
        "team": agent.get(
            "team"
        ),
        "tier": agent.get(
            "tier"
        ),
        "tickets": agent.get(
            "tickets"
        ),
        "csat_responses": agent.get(
            "csat_responses"
        ),
        "csat": agent.get(
            "csat"
        ),
        "avg_handle_time_minutes": agent.get(
            "avg_handle_time_minutes"
        ),
        "sla_breaches": agent.get(
            "sla_breaches"
        ),
        "sla_breach_rate": agent.get(
            "sla_breach_rate"
        ),
        "replacements": agent.get(
            "replacements"
        ),
        "transfers": agent.get(
            "transfers"
        ),
        "attendance_rate": agent.get(
            "attendance_rate"
        ),
        "peer_csat": agent.get(
            "peer_csat"
        ),
        "peer_gap": agent.get(
            "peer_gap"
        ),
        "priority": agent.get(
            "priority"
        ),
    }

    # ------------------------------------------------
    # PROMPT
    # ------------------------------------------------

    prompt = f"""
Return ONLY a manager-facing answer.

Use exactly these headings:

Summary
Signals
Coaching focus
Caveat

No reasoning.
No analysis.
No explanation of instructions.

Summary: 2 sentences.

Signals: 4 bullets.

Coaching focus: 2 neutral review actions.

Caveat: 1 sentence.

Use only the supplied values.
Do not calculate new values.
Do not infer causes.
Do not infer intent or skill.
Do not make disciplinary or bonus recommendations.
Do not blame the agent for replacements.
Do not say one metric causes another.
CSAT uses survey responses only.
Queue and case mix can affect comparisons.

DATA:
{model_data}
"""

    # ------------------------------------------------
    # CALL MODEL
    # ------------------------------------------------

    try:

        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Produce only the final answer. "
                        "Never output analysis, reasoning, "
                        "planning, or discussion of the prompt."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            temperature=0.0,

            max_tokens=500,

            extra_headers={
                "HTTP-Referer": (
                    "http://localhost:5173"
                ),
                "X-Title": (
                    "Vireo Audio Support Dashboard"
                ),
            },
        )

    except Exception as exc:

        raise RuntimeError(
            f"OpenRouter request failed: {exc}"
        ) from exc

    # ------------------------------------------------
    # RESPONSE
    # ------------------------------------------------

    if not response:
        raise RuntimeError(
            "OpenRouter returned no response"
        )

    if not response.choices:
        raise RuntimeError(
            "OpenRouter returned no choices. "
            f"Response: {str(response)[:2000]}"
        )

    message = response.choices[0].message

    if not message:
        raise RuntimeError(
            "OpenRouter returned an empty message"
        )

    result = message.content

    if not result:
        raise RuntimeError(
            "OpenRouter returned no text content"
        )

    # ------------------------------------------------
    # TRY TO EXTRACT CLEAN AI RESPONSE
    # ------------------------------------------------

    cleaned = extract_manager_answer(
        result
    )

    if cleaned:
        return cleaned

    # ------------------------------------------------
    # SAFE FALLBACK
    # ------------------------------------------------

    return fallback_explanation(
        agent
    )