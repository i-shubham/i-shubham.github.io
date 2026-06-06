/* ============================================================
   Plugg — Admin dashboard logic
   Revenue (brand commission + creator subscriptions/commission),
   user management, fee levers, and demo data controls.
   ============================================================ */
(async function () {
  const user = await App.requireRole("admin");
  if (!user) return;
  await App.renderShell({ active: "" });

  document.getElementById("sbName").textContent = user.name;
  document.getElementById("sbFoot").innerHTML = `<div class="card" style="padding:14px;text-align:center"><a href="index.html" class="btn btn-ghost btn-sm btn-block">↗ View public site</a></div>`;
  const titles = {
    overview: ["Revenue", "Platform earnings & activity"],
    users: ["Users", "Creators, brands & their status"],
    config: ["Fee settings", "Levers that drive platform revenue"],
    data: ["Demo data", "Reset or inspect the local demo database"],
  };

  const links = document.querySelectorAll(".sb-link");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("backdrop");
  function go(panel) {
    links.forEach(l => l.classList.toggle("active", l.dataset.panel === panel));
    document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === "panel-" + panel));
    document.getElementById("pageTitle").textContent = titles[panel][0];
    document.getElementById("pageSub").textContent = titles[panel][1];
    sidebar.classList.remove("open"); backdrop.classList.remove("open");
    render(panel);
    if (location.hash !== "#" + panel) history.replaceState(null, "", "#" + panel);
  }
  links.forEach(l => l.addEventListener("click", () => go(l.dataset.panel)));
  document.getElementById("menuBtn").addEventListener("click", () => { sidebar.classList.toggle("open"); backdrop.classList.toggle("open"); });
  backdrop.addEventListener("click", () => { sidebar.classList.remove("open"); backdrop.classList.remove("open"); });
  if (window.matchMedia("(max-width: 820px)").matches) document.getElementById("menuBtn").style.display = "inline-flex";

  function render(panel) {
    if (panel === "overview") return renderOverview();
    if (panel === "users") return renderUsers();
    if (panel === "config") return renderConfig();
    if (panel === "data") return renderData();
  }

  async function renderOverview() {
    const r = await API.adminRevenue();
    const bar = (val, max, label, color) => {
      const pct = max ? Math.round((val / max) * 100) : 0;
      return `<div class="mb"><div class="flex between" style="font-size:.85rem"><span>${label}</span><strong>${App.money(val)}</strong></div>
        <div class="progress" style="margin-top:6px"><span style="width:${Math.max(2,pct)}%;background:${color}"></span></div></div>`;
    };
    const maxStream = Math.max(r.brandCommission, r.subscriptions, r.influencerCommission, 1);
    document.getElementById("panel-overview").innerHTML = `
      <div class="dash-hero">
        <div class="dh-text">
          <h2>Platform control center 🛡️</h2>
          <p>Track every revenue stream — commissions, subscriptions and per-deal fees — in real time.</p>
        </div>
      </div>
      <div class="grid grid-4 mb">
        ${stat("💰", App.money(r.total), "Total revenue")}
        ${stat("🤝", App.money(r.brandCommission), "Brand commission")}
        ${stat("⭐", App.money(r.subscriptions), "Subscriptions")}
        ${stat("📈", App.money(r.influencerCommission), "Creator commission")}
      </div>
      <div class="grid grid-2">
        <div class="card">
          <h3>Revenue by stream</h3>
          ${bar(r.brandCommission, maxStream, "Brand commission ("+API.CONFIG.brandCommissionPct+"%)", "linear-gradient(135deg,#6366f1,#8b5cf6)")}
          ${bar(r.subscriptions, maxStream, "Creator subscriptions", "linear-gradient(135deg,#8b5cf6,#ec4899)")}
          ${bar(r.influencerCommission, maxStream, "Creator commission ("+API.CONFIG.influencerCommissionPct+"%)", "linear-gradient(135deg,#ec4899,#f59e0b)")}
        </div>
        <div class="card">
          <h3>Marketplace activity</h3>
          <div class="metrics" style="grid-template-columns:1fr 1fr 1fr">
            <div class="metric"><div class="mv">${r.counts.influencers}</div><div class="ml">Creators</div></div>
            <div class="metric"><div class="mv">${r.counts.brands}</div><div class="ml">Brands</div></div>
            <div class="metric"><div class="mv">${r.counts.products}</div><div class="ml">Campaigns</div></div>
            <div class="metric"><div class="mv">${r.counts.bids}</div><div class="ml">Bids</div></div>
            <div class="metric"><div class="mv">${r.counts.approved}</div><div class="ml">Approved</div></div>
            <div class="metric"><div class="mv">${r.counts.users}</div><div class="ml">Users</div></div>
          </div>
        </div>
      </div>
      <div class="card mt">
        <h3>Recent transactions</h3>
        ${r.recent.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Type</th><th>Note</th><th>Amount</th><th>Status</th></tr></thead>
          <tbody>${r.recent.map(p=>`<tr><td>${App.dateFmt(p.createdAt)}</td><td>${typeLabel(p.type)}</td><td>${App.esc(p.note||"")}</td><td>${App.money(p.amount)}</td><td>${App.statusBadge(p.status)}</td></tr>`).join("")}</tbody></table></div>`
          : `<div class="empty"><div class="e-emoji">🧾</div>No transactions yet.</div>`}
      </div>`;
  }

  function typeLabel(t) {
    return { brand_commission: '<span class="badge badge-violet">Brand commission</span>', influencer_subscription: '<span class="badge badge-blue">Subscription</span>', influencer_commission: '<span class="badge badge-amber">Creator commission</span>' }[t] || t;
  }

  async function renderUsers() {
    const users = await API.allUsers();
    const roleBadge = { influencer: "badge-violet", brand: "badge-blue", admin: "badge-amber" };
    document.getElementById("panel-users").innerHTML = `<div class="table-wrap"><table>
      <thead><tr><th>Name</th><th>Role</th><th>Email</th><th>Detail</th><th>Status</th><th>Joined</th></tr></thead>
      <tbody>${users.map(u => {
        const detail = u.role === "influencer" && u.extra ? `@${App.esc(u.extra.handle)} · ${App.compact(u.extra.instaFollowers)} IG`
          : u.role === "brand" && u.extra ? App.esc(u.extra.industry) : "—";
        let status = "—";
        if (u.sub) {
          const map = { pro: ["badge-green", "Pro"], trial: ["badge-amber", "Trial"], expired: ["badge-red", "Expired"] };
          const [cls, label] = map[u.sub.status] || ["badge-violet", u.sub.status];
          status = `<span class="badge ${cls}">${label}</span>`;
        }
        return `<tr><td><strong>${App.esc(u.name)}</strong></td><td><span class="badge ${roleBadge[u.role]||"badge-violet"}">${u.role}</span></td><td>${App.esc(u.email)}</td><td>${detail}</td><td>${status}</td><td>${App.dateFmt(u.createdAt)}</td></tr>`;
      }).join("")}</tbody></table></div>`;
  }

  function renderConfig() {
    const c = API.CONFIG;
    document.getElementById("panel-config").innerHTML = `
      <div class="alert alert-info" style="font-size:.88rem">These levers control platform revenue. In production they live in the FastAPI/MySQL config and apply to new transactions. Editing here updates the live demo session.</div>
      <div class="card" style="max-width:560px">
        <form id="cfgForm">
          <div class="field"><label>Creator free trial (days)</label><input class="input" type="number" name="trialDays" value="${c.trialDays}" min="0" /></div>
          <div class="field"><label>Brand commission (%) — on accepted bid</label><input class="input" type="number" name="brandCommissionPct" value="${c.brandCommissionPct}" min="0" max="100" /></div>
          <div class="field"><label>Creator commission (%) — pay-per-deal</label><input class="input" type="number" name="influencerCommissionPct" value="${c.influencerCommissionPct}" min="0" max="100" /></div>
          <div class="field"><label>Creator Pro subscription (${c.currencySymbol}/mo)</label><input class="input" type="number" name="subscriptionMonthly" value="${c.subscriptionMonthly}" min="0" /></div>
          <button class="btn btn-primary" type="submit">Save settings</button>
        </form>
      </div>`;
    document.getElementById("cfgForm").addEventListener("submit", (e) => {
      e.preventDefault();
      const d = App.serializeForm(e.target);
      Object.assign(API.CONFIG, { trialDays:+d.trialDays, brandCommissionPct:+d.brandCommissionPct, influencerCommissionPct:+d.influencerCommissionPct, subscriptionMonthly:+d.subscriptionMonthly });
      App.toast("Settings updated for this session.", "ok");
    });
  }

  function renderData() {
    document.getElementById("panel-data").innerHTML = `
      <div class="card" style="max-width:560px">
        <h3>Local demo database</h3>
        <p class="muted" style="font-size:.92rem">All data is stored in your browser via <code>localStorage</code>. This makes the static site fully functional without a server. When the FastAPI + MySQL backend is connected, flip <code>API.state.useBackend = true</code> in <code>js/api.js</code> and this data layer talks to real REST endpoints instead.</p>
        <div class="flex gap wrap mt">
          <button class="btn btn-ghost btn-sm" id="exportBtn">⬇ Export JSON</button>
          <button class="btn btn-dark btn-sm" id="resetBtn">↺ Reset demo data</button>
        </div>
      </div>`;
    document.getElementById("exportBtn").onclick = () => {
      const blob = new Blob([JSON.stringify(API.rawDB(), null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = "plugg-demo-data.json"; a.click();
    };
    document.getElementById("resetBtn").onclick = () => {
      App.modal({
        title: "Reset demo data?",
        body: `<p>This clears all accounts, campaigns and bids in this browser and reloads the seeded demo. You'll be logged out.</p>`,
        footer: `<button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button><button class="btn btn-dark" id="confirmReset">Reset</button>`,
      });
      document.getElementById("confirmReset").onclick = () => { API.reset(); location.href = "index.html"; };
    };
  }

  function stat(icon, value, label) {
    return `<div class="card stat"><div class="si">${icon}</div><div><div class="sv">${value}</div><div class="sl">${label}</div></div></div>`;
  }

  const start = (location.hash || "#overview").slice(1);
  go(titles[start] ? start : "overview");
})();
