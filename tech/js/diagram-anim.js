/**
 * Staggered reveal + flow pulse for the diagrams on tech problem pages.
 *
 * Progressive enhancement: the `diagram-anim` class on <html> is what gates the
 * animation CSS, so pages without JS (or with reduced-motion set) render the
 * diagrams fully visible and static.
 */
(function () {
  var root = document.documentElement;

  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  var figures = [].slice.call(document.querySelectorAll('figure.diagram'));
  if (!figures.length) return;

  root.classList.add('diagram-anim');

  // Index every child so CSS can stagger with calc(var(--i) * delay).
  // Arrows also get --step, which drives the repeating left-to-right wave.
  figures.forEach(function (figure) {
    var groups = figure.querySelectorAll('.flow-row, .flow-col, .compare, .concern-grid, .stack-flow, .seq');

    [].forEach.call(groups, function (group) {
      var step = 0;

      [].forEach.call(group.children, function (child, i) {
        child.style.setProperty('--i', i);

        if (child.tagName === 'B') {
          child.style.setProperty('--step', step);
          step += 1;
        }
      });
    });
  });

  function reveal(figure) {
    figure.classList.add('is-animated');
  }

  if (!('IntersectionObserver' in window)) {
    figures.forEach(reveal);
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        reveal(entry.target);
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -10% 0px' }
  );

  figures.forEach(function (figure) {
    observer.observe(figure);
  });
})();
