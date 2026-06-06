/* ============================================================
   Plugg — Shared UI shell & utilities
   Renders the public navbar/footer, toasts, modals, and exposes
   small helpers (money, numbers, initials, guards) used site-wide.
   ============================================================ */
const App = (() => {
  const sym = API.CONFIG.currencySymbol;

  // ---- Formatting ----
  function money(n) {
    n = Number(n || 0);
    return sym + n.toLocaleString("en-IN");
  }
  function compact(n) {
    n = Number(n || 0);
    if (n >= 1e7) return (n / 1e7).toFixed(n % 1e7 === 0 ? 0 : 1) + "Cr";
    if (n >= 1e5) return (n / 1e5).toFixed(n % 1e5 === 0 ? 0 : 1) + "L";
    if (n >= 1e3) return (n / 1e3).toFixed(n % 1e3 === 0 ? 0 : 1) + "K";
    return String(n);
  }
  function initials(name) {
    return (name || "?").split(/\s+/).map(s => s[0]).slice(0, 2).join("").toUpperCase();
  }
  // Renders a circular avatar: a photo/logo when `src` is set, else initials.
  function avatar(name, src, cls = "") {
    if (src) return `<span class="avatar ${cls}" style="background-image:url('${esc(src)}');background-size:cover;background-position:center" role="img" aria-label="${esc(name)}"></span>`;
    return `<span class="avatar ${cls}">${initials(name)}</span>`;
  }
  function dateFmt(d) {
    if (!d) return "—";
    return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function statusBadge(status) {
    const map = {
      open: ["badge-green", "Open"], in_progress: ["badge-blue", "In progress"], closed: ["badge-red", "Closed"],
      pending: ["badge-amber", "Pending"], approved: ["badge-green", "Approved"], rejected: ["badge-red", "Rejected"],
      paid: ["badge-green", "Paid"],
    };
    const [cls, label] = map[status] || ["badge-violet", status];
    return `<span class="badge ${cls}">${label}</span>`;
  }

  // ---- Toast ----
  function toast(msg, type = "") {
    let wrap = document.querySelector(".toast-wrap");
    if (!wrap) { wrap = document.createElement("div"); wrap.className = "toast-wrap"; document.body.appendChild(wrap); }
    const t = document.createElement("div");
    t.className = "toast " + type;
    t.innerHTML = (type === "ok" ? "✓ " : type === "err" ? "✕ " : "") + esc(msg);
    wrap.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; t.style.transform = "translateX(20px)"; setTimeout(() => t.remove(), 250); }, 2600);
  }

  // ---- Modal ----
  function modal({ title, body, footer = "", maxWidth }) {
    closeModal();
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" style="${maxWidth ? `max-width:${maxWidth}px` : ""}" role="dialog" aria-modal="true">
        <div class="modal-head"><h3>${title}</h3><button class="modal-close" aria-label="Close">✕</button></div>
        <div class="modal-body">${body}</div>
        ${footer ? `<div class="modal-foot">${footer}</div>` : ""}
      </div>`;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("open"));
    overlay.addEventListener("click", e => { if (e.target === overlay) closeModal(); });
    overlay.querySelector(".modal-close").addEventListener("click", closeModal);
    document.addEventListener("keydown", escClose);
    return overlay;
  }
  function escClose(e) { if (e.key === "Escape") closeModal(); }
  function closeModal() {
    const o = document.querySelector(".modal-overlay");
    if (o) o.remove();
    document.removeEventListener("keydown", escClose);
  }

  // ---- Navbar / footer ----
  async function renderShell({ active = "" } = {}) {
    const user = await API.currentUser();
    const navHost = document.getElementById("nav");
    if (navHost) navHost.innerHTML = navHTML(user, active);
    const footHost = document.getElementById("footer");
    if (footHost) footHost.innerHTML = footerHTML();
    wireNav();
    return user;
  }

  function dashFor(user) {
    if (!user) return "login.html";
    return user.role === "influencer" ? "dashboard-influencer.html"
      : user.role === "brand" ? "dashboard-brand.html" : "dashboard-admin.html";
  }

  function navHTML(user, active) {
    const link = (href, label, key) => `<a href="${href}" class="${active === key ? "active" : ""}">${label}</a>`;
    const right = user
      ? `<a href="${dashFor(user)}" class="btn btn-ghost btn-sm">Dashboard</a>
         <button class="btn btn-dark btn-sm" id="logoutBtn">Log out</button>`
      : `<a href="login.html" class="btn btn-ghost btn-sm desktop-only">Log in</a>
         <a href="register.html" class="btn btn-primary btn-sm">Join free</a>`;
    return `
    <nav class="nav" id="navBar">
      <div class="container nav-inner">
        <a href="index.html" class="brand"><img class="logo" src="img/plugg-logo.png?v=3" alt="Plugg" /> Plugg</a>
        <div class="nav-links">
          ${link("marketplace.html", "Campaigns", "marketplace")}
          ${link("influencers.html", "Creators", "influencers")}
          ${link("how-it-works.html", "How it works", "how")}
          ${link("pricing.html", "Pricing", "pricing")}
        </div>
        <div class="nav-cta">
          ${right}
          <button class="nav-toggle" id="navToggle" aria-label="Menu">☰</button>
        </div>
      </div>
    </nav>`;
  }

  function footerHTML() {
    const y = new Date().getFullYear();
    return `
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div>
            <a href="index.html" class="brand" style="color:#fff"><img class="logo" src="img/plugg-logo.png?v=3" alt="Plugg" /> Plugg</a>
            <p style="color:#9ca0bb;margin-top:14px;max-width:320px">The marketplace where brands and creators meet, bid, and build campaigns that convert.</p>
          </div>
          <div>
            <h4>Platform</h4>
            <a class="f-link" href="marketplace.html">Browse campaigns</a>
            <a class="f-link" href="influencers.html">Find creators</a>
            <a class="f-link" href="how-it-works.html">How it works</a>
            <a class="f-link" href="pricing.html">Pricing</a>
          </div>
          <div>
            <h4>For you</h4>
            <a class="f-link" href="register.html?role=influencer">Join as creator</a>
            <a class="f-link" href="register.html?role=brand">Join as brand</a>
            <a class="f-link" href="login.html">Log in</a>
          </div>
          <div>
            <h4>Company</h4>
            <a class="f-link" href="#">About</a>
            <a class="f-link" href="#">Trust & safety</a>
            <a class="f-link" href="#">Contact</a>
          </div>
        </div>
        <div class="footer-bottom">
          <span>© ${y} Plugg. Demo build — static front-end (FastAPI + MySQL ready).</span>
          <span>Made for creators & brands.</span>
        </div>
      </div>
    </footer>`;
  }

  function wireNav() {
    const toggle = document.getElementById("navToggle");
    const bar = document.getElementById("navBar");
    if (toggle && bar) toggle.addEventListener("click", () => bar.classList.toggle("open"));
    const lo = document.getElementById("logoutBtn");
    if (lo) lo.addEventListener("click", () => { API.logout(); location.href = "index.html"; });
  }

  // ---- Route guards ----
  async function requireRole(role) {
    const user = await API.currentUser();
    if (!user) { location.href = `login.html?next=${encodeURIComponent(location.pathname.split("/").pop())}`; return null; }
    if (user.role !== role) { location.href = dashFor(user); return null; }
    return user;
  }

  // ---- Misc ----
  function qs(name) { return new URLSearchParams(location.search).get(name); }
  function serializeForm(form) {
    const o = {}; new FormData(form).forEach((v, k) => o[k] = v); return o;
  }

  return { money, compact, initials, avatar, dateFmt, esc, statusBadge, toast, modal, closeModal, renderShell, dashFor, navHTML, footerHTML, requireRole, qs, serializeForm };
})();

window.App = App;
