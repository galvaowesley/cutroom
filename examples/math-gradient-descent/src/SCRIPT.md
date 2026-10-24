# Gradient descent, from one weight to two

| Field | Value |
|---|---|
| Format | explainer video |
| Audience | technical (machine learning developers and students) |
| Goal | whoever watches sees the gradient as the slope of a curve, why a step against it goes downhill, what the learning rate changes, and that the same rule holds with two weights |
| Key message | The slope of the loss tells which way is up; step against it, scaled by the learning rate, and the same rule works with any number of weights. |
| Target duration | 50 s |
| Voice | narrator (af_heart@0.95) |
| Brand | cutroom |

## Facts

| id | fact | value | source | period |
|---|---|---|---|---|
| F1 | slope of the loss at the start | 2.74 | src/scene.py, df(X0) | start point |
| F2 | learning rate that crawls | 0.04 | src/scene.py, LR_CRAWL | run 1 |
| F3 | learning rate that settles | 0.25 | src/scene.py, LR_GOOD | run 2 |
| F4 | learning rate that overshoots | 1.5 | src/scene.py, LR_BOUNCE | run 3 |
| F5 | steps of the descent on the surface | 12 steps | src/scene.py, run_3d() | learning rate 0.35 |
| F6 | zoom at which the curve reads as a line | 1600 | src/scene.py, lz | scene 2 |

## Scenes

### 1. Landscape · 0:00–0:04.3

- **Goal:** open with the question and cut the loss surface down to one curve.
- **On screen:** How does a model learn? It rolls downhill.
- **Speech:** How does a model learn? It rolls downhill. Start with one weight.
- **Visual:** cutroom-math: the surface fades in while the camera swings; it fades out and the camera goes side-on, leaving its slice as a 2D curve.
- **Facts:** —

### 2. Zoom and slope · 0:04.3–0:12.9

- **Goal:** show that a curve is a line up close, and that the slope is the gradient.
- **On screen:** Zoom into any point, and the curve turns into a line. Its slope is the gradient.
- **Speech:** Zoom into any point, and the curve turns into a line. Its slope is the gradient.
- **Visual:** cutroom-math: a shaded gap between curve and tangent falls from about 600 px to 1 px while the zoom readout climbs; then the point slides and the slope changes sign.
- **Facts:** F1, F6

### 3. Step and the rule · 0:12.9–0:22.2

- **Goal:** turn the slope into an update, and explain each term of it before using it.
- **On screen:** New weight = old weight − learning rate × slope
- **Speech:** Step against the slope. The new weight is the old weight, minus the learning rate times the slope. The flatter the curve, the smaller the step.
- **Visual:** cutroom-math: an arrow points against the slope; the rule is built piece by piece with a label under each term (new weight, old weight, learning rate in yellow, slope in blue); then the point hops down the curve with a trail.
- **Facts:** F1
- **Sync:** each term appears as its words are spoken.

### 4. Learning rate · 0:22.2–0:32.3

- **Goal:** show three learning rates on the same curve.
- **On screen:** lr = 0.04 crawls · lr = 0.25 settles · lr = 1.5 overshoots
- **Speech:** Now, change the learning rate. Too small, and it crawls. Just right, and it settles. Too big, and it overshoots.
- **Visual:** cutroom-math: three runs from the same start; a slow trail, a trail that settles in a few hops, and a trail that bounces across the valley.
- **Facts:** F2, F3, F4

### 5. Two weights · 0:32.3–0:46.2

- **Goal:** extrapolate from the curve to a surface.
- **On screen:** Add a second weight, and the curve becomes a surface. Two slopes, one per weight, make the gradient.
- **Speech:** Add a second weight, and the curve becomes a surface. Now there are two slopes, one per weight. Together, they are the gradient. Step against it: the same rule works in any dimension.
- **Visual:** cutroom-math: the camera turns to an isometric view from above and the surface is drawn as a mesh; the camera then orbits the figure and closes in, so the two tangent lines and the gradient arrow are seen from a side where nothing hides them; the arrow flips while the view keeps turning; the camera follows the point down in 12 steps from another side, with live readouts.
- **Facts:** F5

### 6. Close · 0:46.2–0:49.9

- **Goal:** tie the surface back to the question.
- **On screen:** Billions of weights. One rule.
- **Speech:** Billions of weights. One rule.
- **Visual:** cutroom-math: the camera drifts; the logo closes.
- **Facts:** —

## Pronunciation

| written | spoken |
|---|---|
| cutroom | cut room |
