# options-pricing-dashboard: design notes

Why each design decision was made: what was chosen, what else was considered, and the
reference behind it. Entries tagged `DRAFT` have not yet been rewritten in my own words.

## Entry format

```
## <Decision>: DRAFT
Chose: ...
Alternatives considered: ...
Why: ...
Interview answer (2 sentences): ...
Reference: <paper / book / section>
```

---

## Pure computations in grids.py, UI in app.py: DRAFT
Chose: `grids.py` holds every computation as pure functions (no Streamlit, no
pricing formulas: everything comes from pricing_core); `app.py` only collects inputs
and draws. Tests (`tests/test_grids.py`) cover grids.py and check wiring, not maths:
grid orientation (rows = vol, columns = spot, on a deliberately non-square 2 x 3
grid so a transpose cannot pass), reporting units (vega per vol point, theta per
day, rho per 1%), each cell against a scalar pricing_core call, and the P&L
definition against the old app's formula.
Alternatives considered: a single app.py (as originally planned; untestable without
driving Streamlit); re-testing the pricing maths here (duplicates pricing-core's
tests).
Why: the bugs a dashboard can add on top of a correct library are wiring bugs: a
transposed grid, a unit left per year or per 1.00 of vol, a premium with the wrong
sign. Planted versions of all four were each caught. Streamlit's headless AppTest
also smoke-tested the calculator, and the full app was checked in a browser.
Interview answer (2 sentences): I kept the dashboard's computations in pure
functions separate from the Streamlit layer, so they can be unit-tested without a
UI. Because the pricing maths is already tested in the library, the dashboard tests
target wiring errors such as transposed grids and wrong units, which are the bugs
this layer can actually introduce.
Reference: Streamlit documentation, "App testing" (streamlit.testing.v1.AppTest).

## One broadcast call per heatmap: DRAFT
Chose: each heatmap is a single pricing_core call with spots as a row vector
(1, n_spot) and vols as a column vector (n_vol, 1), which NumPy broadcasts to
(n_vol, n_spot).
Alternatives considered: the old app's Python double loop, constructing one
BlackScholes object per cell.
Why: the loop pays Python interpreter and object-creation cost per cell; the
broadcast runs the same arithmetic once in compiled NumPy code. Measured against
the old code (identical values to 1e-12): 11 x 11 grid 3.16 ms -> 0.027 ms (117x);
101 x 101 grid 265 ms -> 0.38 ms (701x). The gain grows with grid size because the
loop's overhead is per cell. The dashboard never felt slow; the point is that the
same pricing_core calls scale to the risk engine's scenario revaluations.
Interview answer (2 sentences): I replaced a Python double loop over option objects
with one broadcast call, spot as a row and vol as a column, which gave the same
numbers 117 times faster on the dashboard grid and 700 times faster on a 101 x 101
grid. The same vectorised design is what lets the library revalue a book across
thousands of risk scenarios.
Reference: NumPy documentation, "Broadcasting".

## Units and invalid inputs in the UI: DRAFT
Chose: every Greek is labelled with its unit (vega per vol point, theta per calendar
day, rho per 1% rate move; delta and gamma per 1.00 of spot, stated in a caption);
rates, yields and vol are entered as decimals with help text saying so. Input boxes
refuse negative spot, strike, time and vol; anything still invalid (e.g. spot = 0)
shows a message, and an undefined Greek shows NaN, explained in a caption.
Alternatives considered: unlabelled numbers in internal units (vega per 1.00 of vol
reads as 39.29 instead of 0.39 per point); percentages as inputs (one more
conversion to get wrong).
Why: a Greek without its unit is the easiest number on a risk screen to misread by
a factor of 100 or 365. pricing_core returns NaN rather than raising, so the app
never crashes on bad input, and NaN for an undefined Greek (gamma at the strike on
expiry day) is more honest than a large finite number.
Interview answer (2 sentences): Every Greek on the dashboard carries its unit,
vega per vol point, theta per day and rho per percentage point, because unit
confusion is the commonest way Greeks get misread. Invalid inputs are blocked at
the input or shown as a message, and undefined Greeks appear as NaN, never as a
crash or a fake number.
Reference: Hull, "The Greek letters" chapter (units in the worked examples).

## P&L at expiry heatmap: DRAFT
Chose: P&L = payoff at a chosen spot at expiry minus the premium paid today at the
model price for each (spot, vol): max(S_T - K, 0) - C for calls, max(K - S_T, 0) - P
for puts. Diverging colour map (red-yellow-green) centred at 0.
Alternatives considered: P&L marked to model before expiry (needs a second time and
vol; beyond this task); the old uncentred coolwarm map.
Why: kept the old app's feature and confirmed it was right: a test checks the new
grid against the old formula max(S_T - K - C, -C), which is the same quantity. The
old label ("purchase price") was misleading and is now "spot at expiry". Centring
the colour map at 0 makes losses red and profits green regardless of the data
range; uncentred, the colour at zero moved with the inputs.
Interview answer (2 sentences): The P&L heatmap shows what a buyer at today's model
price would make if the stock finished at a chosen level, payoff minus premium,
across today's spot and vol. I verified it matched the old app's formula exactly
and centred the colour map at zero so profit and loss read correctly at a glance.
Reference: Hull, "Trading strategies involving options" chapter (profit diagrams).
