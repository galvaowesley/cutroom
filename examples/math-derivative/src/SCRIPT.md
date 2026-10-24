# The derivative is the slope of the tangent

| Field | Value |
|---|---|
| Format | explainer video |
| Audience | technical (first-year students, developers who forgot calculus) |
| Goal | whoever watches understands the derivative as the slope of the tangent and sees its graph appear |
| Key message | The derivative is the slope of the tangent: for x³/3 − x it is x² − 1, flat at x = ±1. |
| Target duration | 30 to 40 s |
| Voice | narrator (af_heart@0.95) |
| Brand | cutroom |

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | the function shown | f(x) = x³/3 − x | src/scene.py, f() | — |
| F2 | point where the slope is measured | x = 1.5 | src/scene.py, X0 | — |
| F3 | first step between the two points | h = 1.2 | src/scene.py, H0 | — |
| F4 | secant slope with h = 1.2 | 3.53 | computed in src/scene.py, secant_slope(X0, H0) | — |
| F5 | derivative at x = 1.5 | 1.25 | f′(1.5) = 1.5² − 1, asserted in src/scene.py | — |
| F6 | where the tangent is flat | x = ±1 | f′(x) = 0 for x² = 1 | — |
| F7 | the derivative | f′(x) = x² − 1 | calculus: d/dx (x³/3 − x) | — |

## Scenes

### 1. Hook · 0:00–0:04

- **Goal:** pose the question on a real curve.
- **On screen:** How steep is a curve at one point?
- **Speech:** [A curve] rises and falls. [How steep] is it at one single point?
- **Visual:** cutroom-math: axes and f(x) drawn in hot pink; a sunflower dot appears at x = 1.5.
- **Facts:** F1, F2
- **Sync:** [A curve] draws the axes and the curve; [How steep] drops the dot.

### 2. Secant · 0:04–0:10

- **Goal:** build the slope from two points.
- **On screen:** Two points, h = 1.2 apart: slope 3.53
- **Speech:** Take a [second point], a small step h away. The [line through both] has a slope: rise over run.
- **Visual:** cutroom-math: a second dot at x + h, the secant through both, the rise-over-run formula and live readouts.
- **Facts:** F3, F4
- **Sync:** [second point] adds the dot and h; [line through both] draws the secant and the formula.

### 3. Limit · 0:10–0:17

- **Goal:** turn the secant into the tangent.
- **On screen:** h → 0: the secant becomes the tangent, slope 1.25
- **Speech:** Now [shrink h] toward zero. The line becomes the [tangent]. Its slope, one point two five, is the derivative.
- **Visual:** cutroom-math: h shrinks to 0.001, the readouts count down to 1.25, the limit formula appears.
- **Facts:** F5
- **Sync:** [shrink h] animates h; [tangent] switches the label to f′(1.5).

### 4. The derivative graph · 0:17–0:25

- **Goal:** show f′ as a graph of slopes.
- **On screen:** Every slope, plotted: f′(x) = x² − 1
- **Speech:** [Slide the point] along the curve. Where it is [flat], the slope is zero. All the slopes together [draw] f prime: x squared minus one.
- **Visual:** cutroom-math: the tangent rides the curve from x = −2.2 to 2.2; a pink-soft dot traces f′(x) on the same axes; marks at x = ±1.
- **Facts:** F6, F7
- **Sync:** [Slide the point] moves the tangent; [flat] marks x = ±1; [draw] completes f′(x).

### 5. Close · 0:25–0:30

- **Goal:** leave the one-line definition.
- **On screen:** The derivative is the slope of the tangent, at every point.
- **Speech:** The derivative: the slope of the tangent, [at every point].
- **Visual:** cutroom-math: the two formulas in a card; the cutroom logo.
- **Facts:** F7
- **Sync:** [at every point] brings the logo.

## Pronunciation

| written | spoken |
|---|---|
