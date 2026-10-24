// The figure's truth: cutroom's opt-in components, each download size, and the scale that turns size into drawer
// depth. The build and the page both read from here, so what a drawer shows, what the ruler marks and what the
// readout says never disagree.

// Logarithmic scale: every decade (10x the download) adds DECADE units of drawer.
// On a linear scale the 30 MB drawers would be 1/150 of the 4.5 GB one and vanish.
export const DECADE = 28;
export const ORIGIN_MB = 10; // 10 MB = a drawer of zero depth, the ruler's zero
export const depthOf = (mb) => DECADE * Math.log10(mb / ORIGIN_MB);

// Bottom to top: the deepest drawers sit at the bottom, like a workshop cabinet. Sizes from `cutroom catalog`.
export const DRAWERS = [
  { id: "voice-clone", tool: "Chatterbox", mb: 4500, size: "~4.5 GB", note: "optional" },
  { id: "extract", tool: "Docling", mb: 2300, size: "~2.3 GB" },
  { id: "voice", tool: "Kokoro", mb: 740, size: "~740 MB" },
  { id: "math", tool: "ManimGX", mb: 400, size: "~400 MB" },
  { id: "motion", tool: "HyperFrames", mb: 150, size: "~150 MB" },
  { id: "diagram", tool: "Archify", mb: 40, size: "~40 MB" },
  { id: "iso3d", tool: "Anatomy + Hairline", mb: 30, size: "~30 MB" },
];

// 1 GB = 1000 MB: sizes are approximate (~), and so is their sum.
export const sizeText = (mb) => (mb < 1000 ? `${Math.round(mb)} MB` : `${(mb / 1000).toFixed(1)} GB`);
