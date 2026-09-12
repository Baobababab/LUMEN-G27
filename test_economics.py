from math import inf, isfinite

import economics
from constants import SALES_CHANNELS


def _stub_acceptance_rate(price: float, channel: str) -> float:
    return 0.5


def test_economics_contract_functions_work_with_task_b_stubbed():
    economics.acceptance_rate = _stub_acceptance_rate

    price = 2.19
    channel = SALES_CHANNELS[0]
    month = 7

    assert economics.unit_contribution(price, channel) > 0
    assert economics.monthly_contribution(price, channel, month) > 0
    assert economics.customer_lifetime_months() > 0
    assert economics.ltv(price, channel) > 0
    assert isfinite(economics.payback_months(price, channel, month))
    assert economics.ltv_cac_ratio(price, channel) > 0


def test_launch_month_changes_the_result():
    economics.acceptance_rate = _stub_acceptance_rate

    winter = economics.monthly_contribution(2.19, "DTC Online", 2)
    summer = economics.monthly_contribution(2.19, "DTC Online", 7)

    assert winter != summer
    assert summer > winter


def test_higher_contribution_shortens_payback():
    economics.acceptance_rate = _stub_acceptance_rate

    low_contribution_price = 1.79
    high_contribution_price = 2.19

    assert economics.unit_contribution(high_contribution_price, "DTC Online") > economics.unit_contribution(
        low_contribution_price, "DTC Online"
    )
    assert economics.payback_months(high_contribution_price, "DTC Online", 7) < economics.payback_months(
        low_contribution_price, "DTC Online", 7
    )


def test_payback_is_infinite_when_contribution_is_not_positive():
    economics.acceptance_rate = _stub_acceptance_rate

    assert economics.payback_months(0.5, "DTC Online", 7) == inf


if __name__ == "__main__":
    test_economics_contract_functions_work_with_task_b_stubbed()
    test_launch_month_changes_the_result()
    test_higher_contribution_shortens_payback()
    test_payback_is_infinite_when_contribution_is_not_positive()
    print("test_economics.py: all tests passed")
