"""API Routes for Freelancer LeadTools."""
from fastapi import APIRouter

from app.routes import individuals, agencies, shared, lead_capture

api_router = APIRouter()

# Individual freelancer calculators (→ freelance-growth)
api_router.include_router(
    individuals.router,
    prefix="/calculators",
    tags=["individuals"],
)

# Agency calculators (→ freelancer-dealflow)
api_router.include_router(
    agencies.router,
    prefix="/calculators",
    tags=["agencies"],
)

# Shared calculators (→ either product)
api_router.include_router(
    shared.router,
    prefix="/calculators",
    tags=["shared"],
)

# Lead capture endpoints
api_router.include_router(
    lead_capture.router,
    prefix="/leads",
    tags=["leads"],
)
