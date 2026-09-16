"""Vercel API for the LUMEN Germany launch-scenario tool."""

from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from acceptance import AcceptanceDataError
from constants import DEFAULT_PAYBACK_HORIZON_MONTHS
from data_loader import cleaning_report, load_all
from decision_support import model_adjustments, scenario_analysis
from economics import ltv, monthly_contribution, unit_contribution
from verdict import verdict


class ScenarioRequest(BaseModel):
    """Inputs accepted from the public scenario form."""

    model_config = ConfigDict(extra="forbid")

    price: float = Field(gt=0)
    channel: Literal["DTC Online", "Retail/Grocery", "Gym & Office"]
    month: int = Field(ge=1, le=12)
    payback_horizon_months: float = Field(default=DEFAULT_PAYBACK_HORIZON_MONTHS, gt=0)


class ScenarioCompareRequest(BaseModel):
    """One to three scenarios for a backend-calculated comparison."""

    scenarios: Annotated[list[ScenarioRequest], Field(min_length=1, max_length=3)]
    baseline_index: int = Field(default=0, ge=0)
    include_analysis: bool = False

    @model_validator(mode="after")
    def baseline_must_reference_a_scenario(self):
        if self.baseline_index >= len(self.scenarios):
            raise ValueError("Baseline must reference a supplied scenario.")
        return self


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.exception_handler(RequestValidationError)
def invalid_scenario_request(_: Request, __: RequestValidationError) -> JSONResponse:
    """Reject invalid public input without returning submitted values."""
    return JSONResponse(status_code=422, content={"detail": "Invalid scenario input."})


def _metric_state(metric_key: str, decision_metrics: dict, decided_by: str) -> str:
    """Return a presentation state without changing any verdict rule."""
    decision_mapping = {
        "price_acceptability_index": ("acceptance_rate", "acceptance_pass"),
        "ltv_cac_ratio": ("ltv_cac_ratio", "ltv_cac_pass"),
        "payback_months": ("payback_months", "payback_pass"),
    }.get(metric_key)
    if decision_mapping is None:
        return "monitor"
    decision_key, pass_key = decision_mapping
    if not decision_metrics[pass_key]:
        return "critical"
    return "monitor" if decision_key == decided_by else "favorable"


def _metric_details(metrics: dict, decision_metrics: dict, decided_by: str) -> list[dict]:
    """Describe calculated metrics for a non-technical manager."""
    def detail(
        key: str,
        name: str,
        acronym: str | None,
        unit: str,
        explanation: str,
        formula: str,
        source: str,
        assumptions: str,
        limits: str,
        comparison: str = "No approved decision threshold.",
    ) -> dict:
        return {
            "key": key,
            "name": name,
            "acronym": acronym,
            "value": metrics[key],
            "unit": unit,
            "state": _metric_state(key, decision_metrics, decided_by),
            "comparison": comparison,
            "explanation": explanation,
            "formula": formula,
            "source": source,
            "assumptions": assumptions,
            "limits": limits,
        }

    return [
        detail(
            "price_acceptability_index",
            "Price acceptability index",
            None,
            "percentage",
            "Shows how much of the selected channel's surveyed customer mix finds this price acceptable.",
            "Sum of each segment's channel weight multiplied by its acceptable-price share.",
            "customer_survey.csv and price_sensitivity_survey.csv",
            "The selected channel's survey mix represents the launch audience.",
            "This is an acceptability index, not a purchase probability.",
            f"{metrics['price_acceptability_index']:.1%} against {metrics['acceptance_floor']:.1%} floor.",
        ),
        detail(
            "unit_contribution_eur",
            "Unit contribution",
            None,
            "currency",
            "Shows money left from one unit after channel deductions and unit costs.",
            "Retail price less channel deductions, fulfilment cost, and total cost of goods sold.",
            "channel_economics.csv and cost_breakdown.csv",
            "Channel deductions and costs remain as supplied in the case data.",
            "No approved decision threshold exists for this metric alone.",
        ),
        detail(
            "monthly_contribution_eur",
            "Monthly contribution",
            None,
            "currency",
            "Shows expected monthly contribution per customer in the chosen launch month.",
            "Unit contribution multiplied by segment-weighted monthly units and the seasonal index.",
            "customer_survey.csv, price_sensitivity_survey.csv, and seasonality_and_weather.csv",
            "Survey purchase frequency and the monthly seasonal index apply to the German scenario.",
            "No approved decision threshold exists for this metric alone.",
        ),
        detail(
            "lifetime_value_eur",
            "Lifetime value",
            "LTV",
            "currency",
            "Shows contribution expected across a customer's derived lifetime.",
            "Base monthly contribution multiplied by derived customer lifetime months.",
            "marketing_funnel_monthly.csv, historical_sales_weekly.csv, cost_breakdown.csv, and customer_survey.csv",
            "Derived lifetime months stay constant across German price scenarios.",
            "The value uses comparable home-market history and is not a German sales forecast.",
        ),
        detail(
            "ltv_cac_ratio",
            "Lifetime value to customer acquisition cost ratio",
            "LTV:CAC",
            "ratio",
            "Shows lifetime contribution for each euro spent to acquire a customer.",
            "Lifetime value divided by blended customer acquisition cost.",
            "marketing_funnel_monthly.csv and calculated lifetime value",
            "Blended customer acquisition cost remains EUR 44.00 for all scenarios.",
            "The ratio does not model future changes in acquisition cost.",
            f"{metrics['ltv_cac_ratio']:.2f}x against {metrics['target_ltv_cac']:.2f}x target.",
        ),
        detail(
            "payback_months",
            "Customer acquisition cost payback",
            "CAC payback",
            "months",
            "Shows months needed for contribution to recover customer acquisition cost.",
            "Blended customer acquisition cost divided by selected-month contribution.",
            "marketing_funnel_monthly.csv and calculated monthly contribution",
            "The selected payback horizon defines the decision threshold.",
            "The result depends on the selected launch month and its seasonal index.",
            f"{metrics['payback_months']:.2f} months against {metrics['payback_horizon_months']:.2f}-month horizon.",
        ),
    ]


def _competitive_positioning(price: float, channel: str) -> dict:
    """Compare the selected single-can price with observed channel competitors."""
    rows = load_all()["competitor_prices_by_channel"]
    rows = rows.loc[(rows["channel"] == channel) & (rows["format"] == "Single can (330ml)")]
    competitors = [
        {
            "name": row.competitor,
            "positioning": row.positioning,
            "price_eur": float(row.price_eur),
        }
        for row in rows.itertuples()
    ]
    if not competitors:
        return {"competitors": [], "label": "No observed comparison", "summary": "No comparable competitor price is available for this channel."}
    closest = min(competitors, key=lambda item: abs(item["price_eur"] - price))
    labels = {
        "Mass market": "Accessible",
        "Heritage / loyal niche": "Accessible",
        "Premium performance": "Premium",
        "Boutique adaptogenic": "Very premium",
    }
    label = labels[closest["positioning"]]
    return {
        "competitors": competitors,
        "label": label,
        "summary": f"Closest observed reference: {closest['name']} at EUR {closest['price_eur']:.2f}, positioned as {closest['positioning']}.",
        "limit": "Labels describe the supplied competitor observations, not the full German market.",
    }


def _perspectives(metrics: dict, positioning: dict) -> dict:
    """Group existing evidence for CMO and CFO without making new verdicts."""
    return {
        "cmo": {
            "title": "CMO perspective",
            "points": [
                f"Price acceptability index: {metrics['price_acceptability_index']:.1%}.",
                f"Observed price position: {positioning['label']}.",
                "Premium coherence is assessed against observed competitor positioning only.",
            ],
        },
        "cfo": {
            "title": "CFO perspective",
            "points": [
                f"Unit contribution: EUR {metrics['unit_contribution_eur']:.2f}.",
                f"Lifetime value to customer acquisition cost: {metrics['ltv_cac_ratio']:.2f}x.",
                f"Payback: {metrics['payback_months']:.2f} months.",
            ],
        },
    }


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
        metrics = {
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
        }
        positioning = _competitive_positioning(request.price, request.channel)
        return {
            "verdict": decision["verdict"],
            "decided_by": decision["decided_by"],
            "reasons": decision["reasons"],
            "trade_off": decision["trade_off"],
            "metrics": metrics,
            "metric_details": _metric_details(metrics, decision_metrics, decision["decided_by"]),
            "competitive_positioning": positioning,
            "perspectives": _perspectives(metrics, positioning),
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


@app.post("/api/compare")
def compare_scenarios(request: ScenarioCompareRequest) -> dict:
    """Return up to three existing scenario results and backend-calculated deltas."""
    scenarios = [evaluate_scenario(item) for item in request.scenarios]
    baseline = scenarios[request.baseline_index]["metrics"]
    response = {
        "scenarios": scenarios,
        "baseline_index": request.baseline_index,
        "differences": [
            {
                "unit_contribution_eur": item["metrics"]["unit_contribution_eur"] - baseline["unit_contribution_eur"],
                "monthly_contribution_eur": item["metrics"]["monthly_contribution_eur"] - baseline["monthly_contribution_eur"],
                "lifetime_value_eur": item["metrics"]["lifetime_value_eur"] - baseline["lifetime_value_eur"],
                "ltv_cac_ratio": item["metrics"]["ltv_cac_ratio"] - baseline["ltv_cac_ratio"],
                "payback_months": item["metrics"]["payback_months"] - baseline["payback_months"],
            }
            for item in scenarios
        ],
    }
    if request.include_analysis:
        selected = request.scenarios[request.baseline_index]
        response["analysis"] = scenario_analysis(
            selected.price,
            selected.channel,
            selected.month,
            selected.payback_horizon_months,
            scenarios[request.baseline_index]["metrics"],
        )
    selected = request.scenarios[request.baseline_index]
    if scenarios[request.baseline_index]["verdict"] != "GO":
        response["model_adjustments"] = model_adjustments(
            selected.price,
            selected.channel,
            selected.month,
            selected.payback_horizon_months,
        )
    return response
