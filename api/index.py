"""Vercel API for the LUMEN Germany launch-scenario tool."""

from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from acceptance import AcceptanceDataError
from constants import DEFAULT_PAYBACK_HORIZON_MONTHS
from data_loader import cleaning_report
from economics import ltv, monthly_contribution, unit_contribution
from verdict import verdict


class ScenarioRequest(BaseModel):
    """Inputs accepted from the public scenario form."""

    model_config = ConfigDict(extra="forbid")

    price: float = Field(gt=0)
    channel: Literal["DTC Online", "Retail/Grocery", "Gym & Office"]
    month: int = Field(ge=1, le=12)
    payback_horizon_months: float = Field(default=DEFAULT_PAYBACK_HORIZON_MONTHS, gt=0)


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.exception_handler(RequestValidationError)
def invalid_scenario_request(_: Request, __: RequestValidationError) -> JSONResponse:
    """Reject invalid public input without returning submitted values."""
    return JSONResponse(status_code=422, content={"detail": "Invalid scenario input."})


@app.post("/api/scenario")
def evaluate_scenario(request: ScenarioRequest) -> dict:
    """Return only aggregated scenario results; never return raw survey data."""
    try:
        decision = verdict(
            request.price,
            request.channel,
            request.month,
            request.payback_horizon_months,
        )
        decision_metrics = decision["metrics"]
        return {
            "verdict": decision["verdict"],
            "decided_by": decision["decided_by"],
            "reasons": decision["reasons"],
            "trade_off": decision["trade_off"],
            "metrics": {
                "price_acceptability_index": decision_metrics["acceptance_rate"],
                "unit_contribution_eur": unit_contribution(request.price, request.channel),
                "monthly_contribution_eur": monthly_contribution(
                    request.price, request.channel, request.month
                ),
                "lifetime_value_eur": ltv(request.price, request.channel),
                "ltv_cac_ratio": decision_metrics["ltv_cac_ratio"],
                "payback_months": decision_metrics["payback_months"],
                "target_ltv_cac": decision_metrics["target_ltv_cac"],
                "payback_horizon_months": decision_metrics["payback_horizon_months"],
                "acceptance_floor": decision_metrics["acceptance_floor"],
            },
            "data_quality": cleaning_report(),
        }
    except AcceptanceDataError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Acceptance evidence is unavailable for this scenario.",
                "reason": str(error),
            },
        ) from error
    except (ValueError, RuntimeError, KeyError) as error:
        raise HTTPException(
            status_code=500,
            detail={"message": "The scenario could not be evaluated with available business data."},
        ) from error
