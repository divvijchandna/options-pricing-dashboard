# options-pricing-dashboard

Streamlit dashboard for Black-Scholes pricing and Greek heatmaps. All pricing comes
from [pricing-core](https://github.com/divvijchandna/pricing-core); this repo contains
no pricing formulas of its own.

> Status: pre-release scaffold. Successor to
> [Black-Scholes-v1.0](https://github.com/divvijchandna/Black-Scholes-v1.0).

## Run locally

Requires Python 3.11+ and a sibling checkout of `pricing-core`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
