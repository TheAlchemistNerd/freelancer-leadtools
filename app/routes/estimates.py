"""Deterministic project estimate; no generated prices or automatic sending."""
from fastapi import APIRouter
from pydantic import Field
from app.schemas import BaseModel

router = APIRouter()


class EstimateRequest(BaseModel):
    hours: float = Field(gt=0, le=100000)
    hourly_rate: float = Field(gt=0, le=1000000)
    expenses: float = Field(ge=0, le=100000000, default=0)
    contingency_percent: float = Field(ge=0, le=100, default=15)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@router.post("/project-estimate")
def project_estimate(request: EstimateRequest):
    labor = request.hours * request.hourly_rate
    subtotal = labor + request.expenses
    contingency = subtotal * request.contingency_percent / 100
    return {
        "labor": round(labor, 2), "expenses": request.expenses,
        "contingency": round(contingency, 2),
        "estimate": round(subtotal + contingency, 2), "currency": request.currency,
        "assumptions": ["Contingency applies to labor plus expenses.",
                        "Excludes taxes, platform fees and profit markup. Not a sent quote."],
        "formula_version": "project-estimate-v1",
    }
