# LUMEN Data Plan

The LUMEN decision is: which price, positioning, launch channel, city, and timing should the brand choose for Germany?

There is no German sales history in the data room. Historical sales come from the Netherlands, Denmark, and Sweden, so the Germany estimate must combine comparable-market performance with German survey, market, and competitor evidence.

## Internal data to use

| Decision | Files | Fields or measures |
| --- | --- | --- |
| Price | [`price_test_results.csv`](data/price_test_results.csv), [`price_sensitivity_survey.csv`](data/price_sensitivity_survey.csv) | candidate price, estimated acceptance, price thresholds |
| Unit economics | [`channel_economics.csv`](data/channel_economics.csv), [`cost_breakdown.csv`](data/cost_breakdown.csv) | net price to LUMEN, retailer and distributor cuts, fulfillment, COGS, contribution per unit |
| Segment targeting | [`customer_survey.csv`](data/customer_survey.csv), [`customer_quotes.csv`](data/customer_quotes.csv) | segment, city, spend, price sensitivity, preferred channel, awareness, purchase intent, motivations and objections |
| Channel mix | [`marketing_funnel_monthly.csv`](data/marketing_funnel_monthly.csv), [`historical_sales_weekly.csv`](data/historical_sales_weekly.csv) | CAC, LTV, conversions, spend, units, revenue, channel performance, promotions |
| Positioning | [`competitor_prices_by_channel.csv`](data/competitor_prices_by_channel.csv), [`competitor_price_history.csv`](data/competitor_price_history.csv), [`customer_quotes.csv`](data/customer_quotes.csv) | competitor price, positioning, promotion intensity, reasons to buy or reject |
| City prioritisation | [`market_context.csv`](data/market_context.csv), [`customer_survey.csv`](data/customer_survey.csv) | market size, city share, city growth assumption, city, segment, purchase intent |
| Launch timing | [`seasonality_and_weather.csv`](data/seasonality_and_weather.csv), [`competitor_price_history.csv`](data/competitor_price_history.csv) | monthly demand index, temperature, competitor promotions |

## Minimum model

Compare EUR 1.79, EUR 2.19, and EUR 2.59 by channel. Do not blend the prices before modelling because the channel mix is part of the decision.

Use this flow:

`price x segment x channel -> acceptance -> units -> revenue -> contribution -> CAC/payback`

The recommended first version should use the six highest-value inputs:

1. `price_test_results.csv`
2. `channel_economics.csv`
3. `price_sensitivity_survey.csv`
4. `customer_survey.csv`
5. `marketing_funnel_monthly.csv`
6. `historical_sales_weekly.csv`

Use the remaining internal files as supporting evidence and validation.

## External data to add

Add external data only where it improves a decision or validates an assumption.

### 1. City and regional demographics

Use official population, household, age, and purchasing-power data for Berlin, Munich, Hamburg, Cologne, and Frankfurt. The city shares and growth rates in `market_context.csv` are illustrative assumptions, so external demographics should validate or replace them in a city prioritiser.

- [Destatis population data](https://www.destatis.de/EN/Themes/Society-Environment/Population/Current-Population/Tables/population-by-laender-basis-2022.html)
- [Munich official statistics](https://stadt.muenchen.de/infos/statistik-bevoelkerung.html?lang=en)
- [Berlin-Brandenburg official statistics](https://www.statistik-berlin-brandenburg.de/presse/2026/73-bevoelkerungsfortschreibung-2025/)

### 2. German weather

Use DWD historical observations to validate the simplified monthly weather series. Useful fields are average temperature, precipitation, sunshine hours, and hot-day counts by city or nearest station. Use the data to test seasonality, not to claim causality from twelve monthly observations.

- [DWD Climate Data Center historical daily data](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/)

### 3. Food and beverage inflation

Use the German CPI for food and non-alcoholic beverages to create low, base, and high price scenarios and keep the internal EUR price points current.

- [Destatis consumer price index](https://www.destatis.de/EN/Themes/Economy/Prices/Consumer-Price-Index/Tables/Consumer-prices-12-divisions.html)

### 4. Packaging and regulatory constraints

Add these as model assumptions rather than demand variables:

- EUR 0.25 deposit for eligible one-way cans
- caffeine content in mg per 100 ml
- required high-caffeine warning above 150 mg/l
- permitted conditions for nutrition and health claims

- [EU Food Information Regulation 1169/2011](https://eur-lex.europa.eu/legal-content/en/TXT/PDF/?uri=CELEX%3A32011R1169)
- [European Commission nutrition claims](https://food.ec.europa.eu/food-safety/labelling-and-nutrition/nutrition-and-health-claims/nutrition-claims_en)
- [German DPG deposit overview](https://dpg-pfandsystem.de/images/pdf/220105-DPG-Overview-beverages-3cols-S.pdf)

## Optional validation data

Only add these if time permits:

- timestamped German retailer prices from REWE, EDEKA, dm, and online beverage stores;
- Google Trends by city for functional-drink, energy-drink, low-sugar, and adaptogen searches;
- public location counts for gyms, universities, offices, and train stations.

These sources should validate the internal model, not replace the case data.

## Privacy rule

Do not use `first_name`, `last_name`, `email`, or respondent-level identifiers from `customer_survey.csv`. Publish only synthetic or aggregated outputs. See [`DATA_CONFIDENTIALITY.md`](DATA_CONFIDENTIALITY.md) before adding or deploying data.
