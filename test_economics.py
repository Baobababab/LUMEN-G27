from math import isfinite
from numbers import Real

from acceptance import AcceptanceDataError
import economics


def _assert_positive_finite(value: float) -> None:
    assert isinstance(value, Real)
    assert isfinite(value)
    assert value > 0


def test_real_data_economics_contract_and_scenario_relationships():
    """Exercise every public economics function with the real project data."""
    channel = "DTC Online"
    price = 2.19
    july = 7

    unit = economics.unit_contribution(price, channel)
    monthly = economics.monthly_contribution(price, channel, july)
    lifetime = economics.customer_lifetime_months()
    lifetime_value = economics.ltv(price, channel)
    payback = economics.payback_months(price, channel, july)
    ratio = economics.ltv_cac_ratio(price, channel)

    for value in (unit, monthly, lifetime, lifetime_value, payback, ratio):
        _assert_positive_finite(value)

    february_monthly = economics.monthly_contribution(price, channel, 2)
    july_monthly = economics.monthly_contribution(price, channel, july)
    february_payback = economics.payback_months(price, channel, 2)
    july_payback = economics.payback_months(price, channel, july)
    assert july_monthly > february_monthly
    assert july_payback < february_payback

    lower_price = 1.79
    higher_price = 2.19
    assert economics.unit_contribution(higher_price, channel) > economics.unit_contribution(lower_price, channel)
    assert economics.payback_months(higher_price, channel, july) < economics.payback_months(
        lower_price, channel, july
    )


def test_economics_rejects_invalid_inputs_and_unsupported_prices():
    try:
        economics.unit_contribution(0, "DTC Online")
        assert False, "invalid price must raise ValueError"
    except ValueError:
        pass

    try:
        economics.unit_contribution(2.19, "Unsupported channel")
        assert False, "invalid channel must raise ValueError"
    except ValueError:
        pass

    try:
        economics.monthly_contribution(2.19, "DTC Online", 13)
        assert False, "invalid month must raise ValueError"
    except ValueError:
        pass

    for unsupported_price in (0.61, 3.10):
        try:
            economics.monthly_contribution(unsupported_price, "DTC Online", 7)
            assert False, "prices outside observed support must raise AcceptanceDataError"
        except AcceptanceDataError:
            pass


if __name__ == "__main__":
    test_real_data_economics_contract_and_scenario_relationships()
    test_economics_rejects_invalid_inputs_and_unsupported_prices()
    print("test_economics.py: all tests passed")
