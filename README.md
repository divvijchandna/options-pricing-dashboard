# options-pricing-dashboard

Streamlit dashboard for Black-Scholes-Merton option prices, Greeks and heatmaps.
All pricing comes from [pricing-core](https://github.com/divvijchandna/pricing-core);
this repo contains no pricing formulas of its own.

Successor to [Black-Scholes-v1.0](https://github.com/divvijchandna/Black-Scholes-v1.0).

## Pages

- **Calculator**: spot, strike, time to expiry, volatility, risk-free rate and
  dividend yield in; call and put prices and a Greeks table out (delta, gamma,
  vega per vol point, theta per calendar day, rho per 1% rate move).
- **Heatmaps**: an 11 x 11 spot x volatility grid of call and put prices, call and
  put delta, gamma, vega, and P&L at expiry (buy today at the model price, hold to
  a chosen spot at expiry).

Rates, yields and volatility are entered as decimals (0.05 = 5%).

## Run locally

Requires Python 3.11+ and a sibling checkout of `pricing-core`
(`../pricing-core`), which `requirements.txt` installs in editable mode.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pytest              # tests/test_grids.py: grid orientation, units, wiring
ruff check .
ruff format --check .
```

The computations live in `grids.py` (pure functions, no Streamlit) so they can be
tested; `app.py` is UI only.

## What changed from Black-Scholes-v1.0

- **No local formula.** Prices and Greeks come from pricing-core, which is tested
  against put-call parity, no-arbitrage bounds, its limits, finite differences and
  textbook values.
- **Vectorised heatmaps.** Each heatmap is one broadcast call over the spot x vol
  grid instead of a Python double loop: 117x faster at 11 x 11 and 701x at
  101 x 101, with identical values.
- **Dividend yield q** added as an input.
- **Greek heatmaps** (delta, gamma, vega) and a Greeks table added.
- **Edge cases handled.** An audit of the old formula found it returned NaN at
  the forward when time or volatility is zero, and divided by zero at every such
  limit; pricing-core returns the correct limit there, and NaN only for invalid
  inputs.
- Navigation uses Streamlit's built-in `st.navigation`; `requirements.txt` lists
  direct dependencies only, as UTF-8 (the old file was a UTF-16 `pip freeze`).
