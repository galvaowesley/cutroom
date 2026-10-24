// Deck layout check. Runs only with ?check=1 and writes the result to <script id="deck-check">, which the
// `deck check` command reads with Chrome's --dump-dom. Rules: references/composition.md of the cutroom-deck skill.
(function () {
  if (!/[?&]check=1/.test(location.search)) return;
  var TOL = 1.5;
  // Boxes sized by the layout: their content must fit inside them.
  var CONTAINERS = '.bd, .box, .card, .kpi, .verdict, .step, .use, .proposal, .highlights li, .recs li, .cols > div, .multiples > div, td';

  function visible(el) {
    var r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
  }
  function desc(el) {
    var t = (el.textContent || '').replace(/\s+/g, ' ').trim();
    var name = el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '');
    return name + (t ? ' "' + t.slice(0, 60) + (t.length > 60 ? '…' : '') + '"' : '');
  }
  function isLabel(el) {  // uppercase labels, table headers and the footer may be 12 px
    return !!el.closest('.k, .kpi-l, .m-l, th, .ft, .eyebrow');
  }
  function fontRenders(family, weight) {
    var c = document.createElement('canvas').getContext('2d');
    var sample = 'Ranking 0123456789 ÁÉÍÓÚ ção';
    c.font = weight + ' 40px "' + family + '", monospace';
    var a = c.measureText(sample).width;
    c.font = '40px monospace';
    return Math.abs(a - c.measureText(sample).width) > 1;
  }

  document.fonts.ready.then(function () {
    var res = { slides: [], fonts: [], font_errors: [] };
    document.fonts.forEach(function (f) { res.fonts.push({ family: f.family.replace(/"/g, ''), weight: f.weight, status: f.status }); });
    var used = {};
    document.querySelectorAll('h1, h2, h3, h4, p, li, td, span, b').forEach(function (el) {
      var fam = getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim();
      if (fam) used[fam] = true;
    });
    Object.keys(used).forEach(function (fam) {
      if (['sans-serif', 'serif', 'monospace', 'system-ui'].indexOf(fam) >= 0) return;
      var faces = res.fonts.filter(function (f) { return f.family === fam; });
      var ok = faces.filter(function (f) { return f.status === 'loaded'; });
      if (!ok.length || !fontRenders(fam, String(ok[0].weight).split(' ')[0]))
        res.font_errors.push('font "' + fam + '" did not load');
    });

    document.querySelectorAll('section.slide').forEach(function (s) {
      if (getComputedStyle(s).display === 'none') return;
      var n = s.getAttribute('data-n'), sr = s.getBoundingClientRect(), problems = [];
      var ft = s.querySelector('.ft'), ftTop = ft ? ft.getBoundingClientRect().top : sr.bottom;
      var h2 = s.querySelector('.hd h2');
      if (h2) {
        var lh = parseFloat(getComputedStyle(h2).lineHeight), nl = Math.round(h2.getBoundingClientRect().height / lh);
        if (nl > 2) problems.push({ type: 'title', msg: 'title with ' + nl + ' lines (max. 2)' });
      }
      s.querySelectorAll('*').forEach(function (el) {
        if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') return;
        if (!visible(el)) return;
        var r = el.getBoundingClientRect();
        if (r.right > sr.right + TOL || r.bottom > sr.bottom + TOL || r.left < sr.left - TOL || r.top < sr.top - TOL)
          problems.push({ type: 'overflow_slide', msg: 'leaves the slide: ' + desc(el) });
        if (el instanceof HTMLElement && el.clientWidth > 0 && !el.closest('.ft') && el.scrollWidth > el.clientWidth + 2)
          problems.push({ type: 'overflow_container', msg: 'content wider than its container: ' + desc(el) });
        if (el.matches(CONTAINERS)) {
          var kids = Array.prototype.slice.call(el.children).filter(visible);
          kids.forEach(function (f) {
            var fr = f.getBoundingClientRect();
            if (fr.bottom > r.bottom + TOL || fr.right > r.right + TOL)
              problems.push({ type: 'overflow_container', msg: 'leaves the box ' + desc(el).split(' ')[0] + ': ' + desc(f) });
          });
        }
        if (ft && !el.closest('.ft') && el.closest('.bd') && r.bottom > ftTop + TOL)
          problems.push({ type: 'footer', msg: 'runs into the footer: ' + desc(el) });
      });
      // Text size: body HTML >= 13 px; SVG text >= 12 px.
      var walker = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        var tn = walker.currentNode, el = tn.parentElement;
        if (!tn.textContent.trim() || !el || el.closest('svg') || !visible(el) || isLabel(el)) continue;
        var px = parseFloat(getComputedStyle(el).fontSize);
        if (px < 13) problems.push({ type: 'small_text', msg: px + ' px (min. 13): ' + desc(el) });
      }
      s.querySelectorAll('svg, img').forEach(function (g) {
        var gr = g.getBoundingClientRect(), pw = g.tagName === 'IMG' ? 0 : parseFloat(g.getAttribute('width')), ph = g.tagName === 'IMG' ? 0 : parseFloat(g.getAttribute('height'));
        if (pw && ph && (gr.width < pw - TOL || gr.height < ph - TOL) && !g.closest('.ui-icon'))
          problems.push({ type: 'shrunk_chart', msg: 'chart drawn smaller than its size (' + Math.round(gr.width) + '×' + Math.round(gr.height) + ' of ' + pw + '×' + ph + '): not enough room on the slide' });
      });
      s.querySelectorAll('svg').forEach(function (g) {
        var vb = g.viewBox && g.viewBox.baseVal, W = vb && vb.width ? vb.width : g.clientWidth, H = vb && vb.height ? vb.height : g.clientHeight;
        g.querySelectorAll('text').forEach(function (t) {
          var px = parseFloat(t.getAttribute('font-size') || getComputedStyle(t).fontSize);
          if (px < 12) problems.push({ type: 'small_text', msg: 'SVG ' + px + ' px (min. 12): "' + t.textContent.slice(0, 40) + '"' });
          var b = t.getBBox();
          if (b.width && (b.x < -TOL || b.y < -TOL || b.x + b.width > W + TOL || b.y + b.height > H + TOL))
            problems.push({ type: 'cut_label', msg: 'label outside the chart: "' + t.textContent.slice(0, 40) + '"' });
        });
      });
      var seen = {};
      problems = problems.filter(function (p) { var k = p.type + p.msg; if (seen[k]) return false; seen[k] = 1; return true; });
      res.slides.push({ n: Number(n), problems: problems });
    });
    var out = document.createElement('script');
    out.type = 'application/json';
    out.id = 'deck-check';
    out.textContent = JSON.stringify(res);
    document.body.appendChild(out);
  });
})();
