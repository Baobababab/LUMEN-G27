BLENDED_CAC_EUR = 44.0
TARGET_LTV_CAC = 3.0
DEFAULT_PAYBACK_HORIZON_MONTHS = 12.0
ACCEPTANCE_FLOOR = 0.35
SALES_CHANNELS = ("DTC Online", "Retail/Grocery", "Gym & Office")
PUBLISHED_TEST_PRICES = (1.79, 2.19, 2.59)  # prices price_test_results.csv actually tested
OBSERVED_PRICE_SUPPORT = (0.62, 3.09)  # min(cheap_eur), max(expensive_eur) in the data
ACCEPTANCE_MONOTONE_FLOOR_EUR = 2.10  # monotonicity only holds at/above this price
