"""Pure computations for the dashboard: no Streamlit, no pricing formulas.

Every number comes from pricing_core. Heatmaps are (vol x spot) grids, rows = vol
and columns = spot, each computed with ONE broadcast call: spots as a row vector
(1, n_spot) and vols as a column vector (n_vol, 1) broadcast to (n_vol, n_spot).
This replaces the old app's Python double loop over BlackScholes objects.

Units shown in the dashboard: delta per 1.00 of spot, gamma per 1.00 of spot
squared, vega per vol point (0.01), theta per calendar day, rho per 1% rate move.
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pricing_core.analytic.black_scholes import bs_price
from pricing_core.analytic.greeks import delta, gamma, rho, theta, vega
from pricing_core.conventions import per_day, per_vol_point

Grid = NDArray[np.float64]


def axes(
    spot_min: float, spot_max: float, vol_min: float, vol_max: float, n: int = 11
) -> tuple[Grid, Grid]:
    """Evenly spaced spot and vol axes, both ends included."""
    if not spot_max > spot_min:
        raise ValueError("Maximum spot must be greater than minimum spot.")
    if not vol_max > vol_min:
        raise ValueError("Maximum volatility must be greater than minimum volatility.")
    return np.linspace(spot_min, spot_max, n), np.linspace(vol_min, vol_max, n)


def _grid(func, spots: ArrayLike, vols: ArrayLike, K, T, r, q, **kwargs) -> Grid:
    """func evaluated on every (vol, spot) pair in one broadcast call."""
    row_of_spots = np.asarray(spots, dtype=np.float64)[np.newaxis, :]
    column_of_vols = np.asarray(vols, dtype=np.float64)[:, np.newaxis]
    return np.asarray(func(row_of_spots, K, T, r, q, column_of_vols, **kwargs))


def price_grid(spots, vols, K, T, r, q, *, is_call: bool) -> Grid:
    """Option price for each (vol, spot)."""
    return _grid(bs_price, spots, vols, K, T, r, q, is_call=is_call)


def delta_grid(spots, vols, K, T, r, q, *, is_call: bool) -> Grid:
    """Delta for each (vol, spot), per 1.00 of spot."""
    return _grid(delta, spots, vols, K, T, r, q, is_call=is_call)


def gamma_grid(spots, vols, K, T, r, q) -> Grid:
    """Gamma for each (vol, spot), per 1.00 of spot squared; calls and puts."""
    return _grid(gamma, spots, vols, K, T, r, q)


def vega_grid(spots, vols, K, T, r, q) -> Grid:
    """Vega for each (vol, spot), per vol point; calls and puts."""
    return np.asarray(per_vol_point(_grid(vega, spots, vols, K, T, r, q)))


def pnl_at_expiry_grid(
    spots, vols, K, T, r, q, *, spot_at_expiry: float, is_call: bool
) -> Grid:
    """P&L of buying today at the model price and holding to expiry.

    The premium depends on today's (spot, vol); the payoff only on the spot at
    expiry: P&L = max(S_T - K, 0) - C for calls, max(K - S_T, 0) - P for puts.
    """
    if is_call:
        payoff = max(spot_at_expiry - K, 0.0)
    else:
        payoff = max(K - spot_at_expiry, 0.0)
    return payoff - price_grid(spots, vols, K, T, r, q, is_call=is_call)


def calculator_table(S, K, T, r, q, sigma) -> dict[str, dict[str, float]]:
    """Price and Greeks for one call and one put, in dashboard units.

    Returns {row label: {"Call": value, "Put": value}}. Invalid inputs give NaN
    (pricing_core never raises for bad values).
    """
    args = (S, K, T, r, q, sigma)
    table: dict[str, dict[str, float]] = {}
    for column, is_call in (("Call", True), ("Put", False)):
        values = {
            "Price": bs_price(*args, is_call=is_call),
            "Delta": delta(*args, is_call=is_call),
            "Gamma": gamma(*args),
            "Vega (per vol point)": per_vol_point(vega(*args)),
            "Theta (per day)": per_day(theta(*args, is_call=is_call)),
            # No rho helper in pricing_core.conventions; per 1% = /100.
            "Rho (per 1% rate)": rho(*args, is_call=is_call) / 100.0,
        }
        for row, value in values.items():
            table.setdefault(row, {})[column] = float(value)
    return table
