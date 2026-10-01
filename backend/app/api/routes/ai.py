import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai_service import explain_agent_performance


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)


class AgentExplanationRequest(BaseModel):

    agent_id: str
    name: str

    site: str
    team: str
    tier: int

    tickets: int
    csat_responses: int

    csat: float | None = None

    avg_handle_time_minutes: float | None = None

    sla_breaches: int = 0
    sla_breach_rate: float = 0.0

    replacements: int = 0

    transfers: int = 0

    attendance_rate: float = 0.0

    peer_csat: float | None = None
    peer_gap: float | None = None

    confidence: float | None = None
    priority_score: float | None = None
    priority: str | None = None


@router.post("/agent-explanation")
def agent_explanation(
    request: AgentExplanationRequest,
):
    try:

        agent_data = request.model_dump()

        explanation = explain_agent_performance(
            agent_data
        )

        return {
            "agent_id": request.agent_id,
            "provider": "OpenRouter",
            "model": os.getenv(
                "OPENROUTER_MODEL",
                "nvidia/nemotron-3-ultra-550b-a55b:free",
            ),
            "explanation": explanation,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=f"AI explanation failed: {str(exc)}",
        )