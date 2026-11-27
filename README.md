# options-pricing-dashboard

Streamlit dashboard for Black-Scholes-Merton option prices, Greeks and heatmaps.
All pricing comes from [pricing-core](https://github.com/divvijchandna/pricing-core);
this repo contains no pricing formulas of its own.

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

## Origin

Rebuilt from my earlier
[Black-Scholes-v1.0](https://github.com/divvijchandna/Black-Scholes-v1.0) on
pricing-core: each heatmap is now one vectorised call over the spot x vol grid
(117x faster at 11 x 11, 701x at 101 x 101, identical values), with dividend yield
and Greeks added.
