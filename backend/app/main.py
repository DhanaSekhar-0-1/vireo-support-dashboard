from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.services.data_service import (
    load_tickets,
    load_agents,
    load_customers,
    load_orders,
    load_products,
)

from app.analytics.metrics import (
    calculate_agent_metrics,
    calculate_training_priority,
    calculate_monthly_trends,
    filter_tickets_by_period,
    validate_tickets,
)

from app.api.routes.ai import router as ai_router


# ==================================================
# APP
# ==================================================

app = FastAPI(
    title="Vireo Audio Support Dashboard",
    version="1.0.0",
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# AI ROUTES
# ==================================================
# ai.py already contains:
# prefix="/api/ai"
#
# Therefore DO NOT add another prefix here.

app.include_router(ai_router)


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():
    return {
        "message": "Vireo Support Dashboard API is running"
    }


# ==================================================
# HEALTH
# ==================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==================================================
# DATA SUMMARY
# ==================================================

@app.get("/api/data/summary")
def data_summary():

    tickets = load_tickets()
    agents = load_agents()
    customers = load_customers()
    orders = load_orders()
    products = load_products()

    return {
        "tickets": len(tickets),
        "agents": len(agents),
        "customers": len(customers),
        "orders": len(orders),
        "products": len(products),
    }


# ==================================================
# DATA QUALITY
# ==================================================

@app.get("/api/data/quality")
def data_quality():

    tickets = load_tickets()
    agents = load_agents()

    return validate_tickets(
        tickets,
        agents,
    )


# ==================================================
# AGENTS
# ==================================================

@app.get("/api/agents")
def get_agents(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):

    tickets = load_tickets()
    agents = load_agents()

    filtered_tickets = filter_tickets_by_period(
        tickets,
        start_date,
        end_date,
    )

    metrics = calculate_agent_metrics(
        filtered_tickets,
        agents,
    )

    return metrics.fillna("").to_dict(
        orient="records"
    )


# ==================================================
# TRAINING PRIORITY
# ==================================================

@app.get("/api/training-priority")
def get_training_priority(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):

    tickets = load_tickets()
    agents = load_agents()

    filtered_tickets = filter_tickets_by_period(
        tickets,
        start_date,
        end_date,
    )

    result = calculate_training_priority(
        filtered_tickets,
        agents,
    )

    return result.fillna("").to_dict(
        orient="records"
    )


# ==================================================
# MONTHLY TRENDS
# ==================================================

@app.get("/api/trends")
def get_trends():

    tickets = load_tickets()

    result = calculate_monthly_trends(
        tickets
    )

    return result.fillna("").to_dict(
        orient="records"
    )