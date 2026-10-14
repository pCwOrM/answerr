/* answerr.me/pro — Mandelbrot keyframe worker for the live horizon.
   Returns a smooth escape value per pixel (-1 = inside the set). Plain doubles, so the
   zoom stays honest down to ~1e-12 around the werr seed coordinate. */
self.onmessage = function (e) {
  const { id, w, h, cx, cy, scale, ax, ay, maxIter } = e.data;
  const out = new Float32Array(w * h);
  const px = (2 * scale) / w;            // complex units per pixel (scale = half-width)
  const left = cx - ax * w * px;          // anchor (ax, ay) = where the seed sits in the frame
  const top = cy + ay * h * px;
  const LOG2 = Math.log(2);
  for (let j = 0; j < h; j++) {
    const ci = top - j * px;
    for (let i = 0; i < w; i++) {
      const cr = left + i * px;
      // main cardioid and period-2 bulb are inside: skip the full iteration
      const q = (cr - 0.25) * (cr - 0.25) + ci * ci;
      if (q * (q + (cr - 0.25)) <= 0.25 * ci * ci || (cr + 1) * (cr + 1) + ci * ci <= 0.0625) { out[j * w + i] = -1; continue; }
      let zr = 0, zi = 0, zr2 = 0, zi2 = 0, n = 0;
      while (n < maxIter && zr2 + zi2 <= 256) {
        zi = 2 * zr * zi + ci;
        zr = zr2 - zi2 + cr;
        zr2 = zr * zr; zi2 = zi * zi;
        n++;
      }
      if (n >= maxIter) { out[j * w + i] = -1; continue; }
      // smooth (continuous) escape count; |Z| > 2 is the werr divergence threshold
      const nu = Math.log(Math.log(zr2 + zi2) / 2 / LOG2) / LOG2;
      out[j * w + i] = n + 1 - nu;
    }
  }
  self.postMessage({ id, w, h, scale, data: out }, [out.buffer]);
};
