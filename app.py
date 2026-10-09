"""Options pricing dashboard (Streamlit). Run with: streamlit run app.py

UI only: every number comes from grids.py, which calls pricing_core. There is no
pricing formula in this repo.
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st

import grids

RATE_HELP = "Continuously compounded, as a decimal: 0.05 = 5%."
VOL_HELP = "Annualised, as a decimal: 0.20 = 20%."


def _heatmap(grid, spots, vols, title, *, cmap="viridis", fmt=".2f", center=None):
    """Annotated (vol x spot) heatmap: rows = vol, columns = spot."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        grid,
        xticklabels=np.round(spots, 2),
        yticklabels=np.round(vols, 2),
        cmap=cmap,
        center=center,
        annot=True,
        fmt=fmt,
        annot_kws={"size": 7},
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Spot price")
    ax.set_ylabel("Volatility")
    ax.tick_params(axis="both", labelsize=8, labelrotation=0)
    return fig


def _show_pair(left, right):
    """Two figures side by side; figures are closed after rendering."""
    col_left, col_right = st.columns(2)
    for col, fig in ((col_left, left), (col_right, right)):
        with col:
            st.pyplot(fig)
        plt.close(fig)


def calculator_page():
    st.title("Options Pricing Calculator")
    col1, col2, col3 = st.columns(3)
    with col1:
        S = st.number_input("Spot price", value=140.0, min_value=0.0)
        K = st.number_input("Strike price", value=150.0, min_value=0.0)
    with col2:
        T = st.number_input("Time to expiry (years)", value=0.5, min_value=0.0)
        sigma = st.number_input("Volatility", value=0.30, min_value=0.0, help=VOL_HELP)
    with col3:
        r = st.number_input("Risk-free rate", value=0.05, format="%.4f", help=RATE_HELP)
        q = st.number_input(
            "Dividend yield",
            value=0.0,
            format="%.4f",
            help="Continuous yield, " + RATE_HELP,
        )

    table = grids.calculator_table(S, K, T, r, q, sigma)
    call_price, put_price = table["Price"]["Call"], table["Price"]["Put"]
    if math.isnan(call_price):
        st.error("Invalid inputs: spot and strike must be positive.")
        return

    col_call, col_put = st.columns(2)
    col_call.metric("Call price", f"{call_price:.4f}")
    col_put.metric("Put price", f"{put_price:.4f}")

    st.subheader("Greeks")
    greeks = {row: values for row, values in table.items() if row != "Price"}
    st.table(
        {
            "Greek": list(greeks),
            "Call": [f"{v['Call']:.4f}" for v in greeks.values()],
            "Put": [f"{v['Put']:.4f}" for v in greeks.values()],
        }
    )
    st.caption(
        "Delta per 1.00 of spot; gamma per 1.00 of spot squared. NaN means the "
        "Greek is undefined there (e.g. gamma at the strike on expiry day)."
    )


def heatmaps_page():
    st.title("Heatmaps")
    with st.form("heatmap_inputs"):
        col1, col2, col3 = st.columns(3)
        with col1:
            spot_min = st.number_input("Minimum spot price", value=100.0, min_value=0.0)
            spot_max = st.number_input("Maximum spot price", value=200.0, min_value=0.0)
            K = st.number_input("Strike price", value=150.0, min_value=0.0)
        with col2:
            vol_min, vol_max = st.slider(
                "Volatility range", 0.01, 1.00, (0.01, 1.00), help=VOL_HELP
            )
            T = st.number_input("Time to expiry (years)", value=1.0, min_value=0.0)
            r = st.number_input(
                "Risk-free rate", value=0.02, format="%.4f", help=RATE_HELP
            )
        with col3:
            q = st.number_input(
                "Dividend yield",
                value=0.0,
                format="%.4f",
                help="Continuous yield, " + RATE_HELP,
            )
            s_t_call = st.number_input(
                "Spot at expiry, call P&L", value=135.0, min_value=0.0
            )
            s_t_put = st.number_input(
                "Spot at expiry, put P&L", value=65.0, min_value=0.0
            )
        submitted = st.form_submit_button("Generate heatmaps")
    if not submitted:
        return

    try:
        spots, vols = grids.axes(spot_min, spot_max, vol_min, vol_max)
    except ValueError as err:
        st.error(str(err))
        return
    args = (spots, vols, K, T, r, q)

    st.header("Prices")
    _show_pair(
        _heatmap(grids.price_grid(*args, is_call=True), spots, vols, "Call price"),
        _heatmap(grids.price_grid(*args, is_call=False), spots, vols, "Put price"),
    )

    st.header("Greeks")
    _show_pair(
        _heatmap(
            grids.delta_grid(*args, is_call=True),
            spots,
            vols,
            "Call delta",
            cmap="Blues",
        ),
        _heatmap(
            grids.delta_grid(*args, is_call=False),
            spots,
            vols,
            "Put delta",
            cmap="Reds_r",
        ),
    )
    _show_pair(
        _heatmap(
            grids.gamma_grid(*args), spots, vols, "Gamma", cmap="magma", fmt=".4f"
        ),
        _heatmap(
            grids.vega_grid(*args), spots, vols, "Vega (per vol point)", cmap="magma"
        ),
    )
    st.caption("Gamma and vega are the same for calls and puts.")

    st.header("P&L at expiry")
    st.caption(
        "Buy today at the model price for each (spot, vol), hold to expiry, where "
        "the spot is the value entered above: P&L = payoff - premium."
    )
    _show_pair(
        _heatmap(
            grids.pnl_at_expiry_grid(*args, spot_at_expiry=s_t_call, is_call=True),
            spots,
            vols,
            f"Call P&L, spot at expiry {s_t_call:g}",
            cmap="RdYlGn",
            center=0.0,
        ),
        _heatmap(
            grids.pnl_at_expiry_grid(*args, spot_at_expiry=s_t_put, is_call=False),
            spots,
            vols,
            f"Put P&L, spot at expiry {s_t_put:g}",
            cmap="RdYlGn",
            center=0.0,
        ),
    )


st.set_page_config(page_title="Options Pricing Dashboard", layout="wide")
st.navigation(
    [
        st.Page(calculator_page, title="Calculator", default=True),  # served at /
        st.Page(heatmaps_page, title="Heatmaps", url_path="heatmaps"),
    ]
).run()
