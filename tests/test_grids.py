"""Tests for grids.py: the dashboard's pure computations (no Streamlit).

grids.py contains no pricing formulas: everything comes from pricing_core, which
has its own tests. These tests check the wiring: grid orientation (rows = vol,
columns = spot, as in the old heatmaps), reporting units, and that each cell is
the pricing_core value for that spot and vol.
"""

import numpy as np
import pytest
from pricing_core.analytic.black_scholes import bs_price
from pricing_core.analytic.greeks import delta, gamma, rho, theta, vega

from grids import (
    axes,
    calculator_table,
    delta_grid,
    gamma_grid,
    pnl_at_expiry_grid,
    price_grid,
    vega_grid,
)

K, T, R, Q = 150.0, 0.5, 0.05, 0.01
SPOTS = np.array([120.0, 150.0, 180.0])  # 3 columns
VOLS = np.array([0.15, 0.40])  # 2 rows


def _cellwise(func, **kwargs):
    """Reference: call func once per (vol, spot) cell, scalar inputs."""
    return np.array([[func(s, K, T, R, Q, v, **kwargs) for s in SPOTS] for v in VOLS])


# --- axes ----------------------------------------------------------------------


def test_axes_are_evenly_spaced_and_inclusive():
    spots, vols = axes(100.0, 200.0, 0.1, 0.5, n=11)
    np.testing.assert_allclose(spots, np.linspace(100.0, 200.0, 11))
    np.testing.assert_allclose(vols, np.linspace(0.1, 0.5, 11))


@pytest.mark.parametrize(
    ("spot_min", "spot_max", "vol_min", "vol_max"),
    [(200.0, 100.0, 0.1, 0.5), (100.0, 200.0, 0.5, 0.1), (100.0, 100.0, 0.1, 0.5)],
)
def test_axes_reject_empty_or_reversed_ranges(spot_min, spot_max, vol_min, vol_max):
    with pytest.raises(ValueError):
        axes(spot_min, spot_max, vol_min, vol_max)


# --- price and Greek grids -----------------------------------------------------


@pytest.mark.parametrize("is_call", [True, False])
def test_price_grid_orientation_and_values(is_call):
    grid = price_grid(SPOTS, VOLS, K, T, R, Q, is_call=is_call)
    assert grid.shape == (len(VOLS), len(SPOTS))  # rows = vol, columns = spot
    np.testing.assert_allclose(grid, _cellwise(bs_price, is_call=is_call), rtol=1e-14)


@pytest.mark.parametrize("is_call", [True, False])
def test_delta_grid(is_call):
    grid = delta_grid(SPOTS, VOLS, K, T, R, Q, is_call=is_call)
    assert grid.shape == (len(VOLS), len(SPOTS))
    np.testing.assert_allclose(grid, _cellwise(delta, is_call=is_call), rtol=1e-14)


def test_gamma_grid():
    grid = gamma_grid(SPOTS, VOLS, K, T, R, Q)
    assert grid.shape == (len(VOLS), len(SPOTS))
    np.testing.assert_allclose(grid, _cellwise(gamma), rtol=1e-14)


def test_vega_grid_is_per_vol_point():
    # pricing_core vega is per 1.00 of vol; the dashboard shows per vol point.
    grid = vega_grid(SPOTS, VOLS, K, T, R, Q)
    assert grid.shape == (len(VOLS), len(SPOTS))
    np.testing.assert_allclose(grid, _cellwise(vega) / 100.0, rtol=1e-14)


# --- P&L at expiry -------------------------------------------------------------


@pytest.mark.parametrize("is_call", [True, False])
def test_pnl_at_expiry(is_call):
    # Buy today at the model price for each (spot, vol); hold to expiry, where
    # the spot is spot_at_expiry. P&L = payoff(S_T) - premium.
    s_t = 165.0
    grid = pnl_at_expiry_grid(
        SPOTS, VOLS, K, T, R, Q, spot_at_expiry=s_t, is_call=is_call
    )
    premium = _cellwise(bs_price, is_call=is_call)
    payoff = max(s_t - K, 0.0) if is_call else max(K - s_t, 0.0)
    assert grid.shape == (len(VOLS), len(SPOTS))
    np.testing.assert_allclose(grid, payoff - premium, rtol=1e-14)


def test_pnl_matches_legacy_formula():
    # Old app: call max(S_T - K - C, -C); put max(K - S_T - P, -P).
    s_t = 135.0
    c = price_grid(SPOTS, VOLS, K, T, R, Q, is_call=True)
    p = price_grid(SPOTS, VOLS, K, T, R, Q, is_call=False)
    np.testing.assert_allclose(
        pnl_at_expiry_grid(SPOTS, VOLS, K, T, R, Q, spot_at_expiry=s_t, is_call=True),
        np.maximum(s_t - K - c, -c),
    )
    np.testing.assert_allclose(
        pnl_at_expiry_grid(SPOTS, VOLS, K, T, R, Q, spot_at_expiry=s_t, is_call=False),
        np.maximum(K - s_t - p, -p),
    )


# --- calculator table ----------------------------------------------------------

_ROWS = [
    "Price",
    "Delta",
    "Gamma",
    "Vega (per vol point)",
    "Theta (per day)",
    "Rho (per 1% rate)",
]


def test_calculator_table_rows_columns_and_units():
    S, sigma = 140.0, 0.3
    table = calculator_table(S, K, T, R, Q, sigma)
    assert list(table) == _ROWS
    for col, is_call in (("Call", True), ("Put", False)):
        expected = {
            "Price": bs_price(S, K, T, R, Q, sigma, is_call=is_call),
            "Delta": delta(S, K, T, R, Q, sigma, is_call=is_call),
            "Gamma": gamma(S, K, T, R, Q, sigma),
            "Vega (per vol point)": vega(S, K, T, R, Q, sigma) / 100.0,
            "Theta (per day)": theta(S, K, T, R, Q, sigma, is_call=is_call) / 365.0,
            "Rho (per 1% rate)": rho(S, K, T, R, Q, sigma, is_call=is_call) / 100.0,
        }
        for row in _ROWS:
            assert table[row][col] == pytest.approx(expected[row], rel=1e-14)
            assert type(table[row][col]) is float


def test_calculator_table_invalid_input_is_nan_not_error():
    # e.g. a user typing a negative vol: pricing_core returns NaN, never raises.
    table = calculator_table(140.0, K, T, R, Q, -0.1)
    assert all(np.isnan(table[row][col]) for row in _ROWS for col in ("Call", "Put"))
