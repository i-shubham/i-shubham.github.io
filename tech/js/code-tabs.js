/**
 * Editor-style code blocks: language tabs (Python / Rust / Java / C++),
 * highlight.js colouring, a line-number gutter and a copy button.
 *
 * highlight.js is optional — if the CDN script is missing the code still shows,
 * just without colours.
 */
(function () {
  function highlight() {
    if (!window.hljs) return;
    hljs.configure({ ignoreUnescapedHTML: true });
    document.querySelectorAll('pre code[class*="language-"]').forEach(function (el) {
      try {
        hljs.highlightElement(el);
      } catch (err) {
        /* leave the block as plain text */
      }
    });
  }

  /**
   * The gutter is positioned against the panel rather than the <pre> so it stays
   * put while the code scrolls horizontally underneath it.
   */
  function addGutter(panel) {
    var pre = panel.querySelector('pre');
    var code = pre && pre.querySelector('code');
    if (!code || panel.querySelector('.code-gutter')) return;

    var lines = code.textContent.replace(/\n+$/, '').split('\n').length;
    var numbers = [];
    for (var i = 1; i <= lines; i++) numbers.push(i);

    var gutter = document.createElement('span');
    gutter.className = 'code-gutter';
    gutter.setAttribute('aria-hidden', 'true');
    gutter.textContent = numbers.join('\n');

    panel.insertBefore(gutter, pre);
    panel.classList.add('has-gutter');
  }

  function activate(root, tabId) {
    root.querySelectorAll('.code-tab').forEach(function (tab) {
      var on = tab.getAttribute('data-tab') === tabId;
      tab.classList.toggle('is-active', on);
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    root.querySelectorAll('.code-panel').forEach(function (panel) {
      var on = panel.getAttribute('data-panel') === tabId;
      panel.classList.toggle('is-active', on);
      if (on) panel.removeAttribute('hidden');
      else panel.setAttribute('hidden', '');
    });
  }

  function copyActive(root, btn) {
    var panel = root.querySelector('.code-panel.is-active');
    var code = panel && panel.querySelector('code');
    if (!code || !navigator.clipboard) return;

    navigator.clipboard.writeText(code.textContent).then(function () {
      btn.textContent = 'Copied';
      btn.classList.add('is-copied');
      window.setTimeout(function () {
        btn.textContent = 'Copy';
        btn.classList.remove('is-copied');
      }, 1600);
    });
  }

  highlight();

  document.querySelectorAll('.code-panel').forEach(addGutter);

  document.querySelectorAll('[data-code-tabs]').forEach(function (root) {
    root.addEventListener('click', function (e) {
      var copy = e.target.closest('[data-code-copy]');
      if (copy) {
        copyActive(root, copy);
        return;
      }
      var btn = e.target.closest('.code-tab');
      if (btn) activate(root, btn.getAttribute('data-tab'));
    });

    root.addEventListener('keydown', function (e) {
      var tabs = [].slice.call(root.querySelectorAll('.code-tab'));
      var idx = tabs.indexOf(document.activeElement);
      if (idx < 0) return;

      var next = -1;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (idx + 1) % tabs.length;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (idx - 1 + tabs.length) % tabs.length;
      if (e.key === 'Home') next = 0;
      if (e.key === 'End') next = tabs.length - 1;
      if (next < 0) return;

      e.preventDefault();
      tabs[next].focus();
      activate(root, tabs[next].getAttribute('data-tab'));
    });
  });
})();
