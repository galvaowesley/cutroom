# Gradient Descent: Descending the Loss Landscape

| Field | Value |
|---|---|
| Format | explainer video |
| Audience | technical (machine learning developers and students) |
| Goal | whoever watches understands how gradient descent updates weights using the negative gradient and learning rate |
| Key message | Gradient descent steers parameters down the loss landscape: each step takes the negative gradient scaled by eta until the slope flattens to zero. |
| Target duration | 28 s |
| Voice | narrator (af_heart@0.95) |
| Brand | cutroom |

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | initial parameter weight | w = 2.10 | examples/math-gradient-descent/src/scene.py | step 0 |
| F2 | learning rate eta | eta = 0.20 | examples/math-gradient-descent/src/scene.py | step 0 |
| F3 | converged minimum weight | w = 0.81 | examples/math-gradient-descent/src/scene.py | convergence |
| F4 | loss function formula | 0.5 * w^2 + 0.3 * cos(2.5 * w) | examples/math-gradient-descent/src/scene.py | v2.0 |
| F5 | vanishing gradient at minimum | 0.000 | examples/math-gradient-descent/src/scene.py | convergence |

## Scenes

### 1. The Loss Landscape · 0:00–0:07

- **Goal:** open with a compelling question in the first 3 seconds and reveal the 3-zone spatial layout with the loss bowl.
- **On screen:** Optimization · gradient step · L(w) loss bowl
- **Speech:** How does AI find the [best weights out of billions]? It slides down a [loss landscape].
- **Visual:** Zone 1 eyebrow and formula appear, Zone 2 draws the curved loss bowl on Night Plum with tactile grid, and Zone 3 captions highlight loss landscape.
- **Facts:** F4

### 2. The Gradient and Step · 0:07–0:14

- **Goal:** show the tangent slope and the negative gradient direction vector.
- **On screen:** Gradient vector · tangent slope ∇L
- **Speech:** At any point, the [tangent slope] gives the gradient. It points steepest uphill, so we [step in reverse].
- **Visual:** Tangent line sweeps to the point at w = 2.10, live telemetry readout updates, and an accent Hot Signal arrow points downhill.
- **Facts:** F1

### 3. Rolling into the Valley · 0:14–0:21

- **Goal:** execute discrete gradient descent steps shrinking in magnitude as the slope flattens.
- **On screen:** ValueTracker telemetry · w updates step by step
- **Speech:** Scaled by the [learning rate eta], each gradient step [descends toward the minimum].
- **Visual:** Stepping dot moves through discrete iterations; telemetry counts step 00 to 04 with live loss L(w) and slope readouts.
- **Facts:** F2

### 4. Convergence Lockup · 0:21–0:28

- **Goal:** highlight the flat tangent at the minimum where the gradient vanishes.
- **On screen:** Convergence · ∇L → 0.000 · optimal w = 0.81
- **Speech:** Where the curve flattens, the [gradient vanishes to zero]. The descent [converges], locking into optimal weights.
- **Visual:** Flat tangent locks at w = 0.81, telemetry shows ∇L = 0.000, and a final accent flash marks convergence.
- **Facts:** F3, F5

## Pronunciation

| written | spoken |
|---|---|
| eta | ay-tuh |
