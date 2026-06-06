/* ============================================================
   Plugg — Creator (Influencer) dashboard logic
   ============================================================ */
(async function () {
  const user = await App.requireRole("influencer");
  if (!user) return;
  await App.renderShell({ active: "" });

  let inf = await API.getInfluencer(user.id);
  document.getElementById("sbName").textContent = user.name;
  if (inf && inf.avatar) {
    const sba = document.querySelector(".sb-avatar");
    sba.textContent = ""; sba.style.cssText = `background-image:url('${inf.avatar}');background-size:cover;background-position:center`;
  }
  const titles = {
    overview: ["Overview", "Your collaboration snapshot"],
    campaigns: ["Browse campaigns", "Find and bid on paid collaborations"],
    bids: ["My bids", "Track every bid you've placed"],
    concepts: ["Briefs unlocked", "Creative concepts shared after approval"],
    profile: ["My stats profile", "Keep your audience numbers up to date"],
    billing: ["Subscription", "Manage your trial, plan & payments"],
  };

  // ---- Navigation ----
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

  // ---- Trial / subscription pill + sidebar footer ----
  function refreshPill() {
    const s = API.subscriptionStatus(inf);
    const cls = s.status === "pro" ? "badge-green" : s.status === "trial" ? "badge-amber" : "badge-red";
    document.getElementById("trialPill").innerHTML = `<span class="badge ${cls}">${s.label}</span>`;
    const foot = document.getElementById("sbFoot");
    if (s.status === "pro") {
      foot.innerHTML = `<div class="card" style="padding:14px;text-align:center"><span class="badge badge-green">Pro active ✓</span></div>`;
    } else {
      foot.innerHTML = `<div class="card" style="padding:16px;background:var(--grad-soft);border-color:transparent">
        <strong style="font-size:.9rem">${s.status === "trial" ? "On free trial" : "Trial ended"}</strong>
        <p class="muted" style="font-size:.78rem;margin:4px 0 10px">${s.status === "trial" ? s.daysLeft + " days left" : "Subscribe to keep bidding"}</p>
        <button class="btn btn-primary btn-sm btn-block" data-goto="billing">Upgrade to Pro</button></div>`;
      foot.querySelector("[data-goto]").addEventListener("click", () => go("billing"));
    }
  }

  async function refreshInf() { inf = await API.getInfluencer(user.id); refreshPill(); }

  // ---- Panel renderers ----
  async function render(panel) {
    if (panel === "overview") return renderOverview();
    if (panel === "campaigns") return renderCampaigns();
    if (panel === "bids") return renderBids();
    if (panel === "concepts") return renderConcepts();
    if (panel === "profile") return renderProfile();
    if (panel === "billing") return renderBilling();
  }

  function gate() {
    const s = API.subscriptionStatus(inf);
    if (s.status === "expired") {
      App.toast("Your trial has ended — subscribe to keep bidding.", "err");
      go("billing");
      return false;
    }
    return true;
  }

  async function renderOverview() {
    const bids = await API.myBids(user.id);
    const approved = bids.filter(b => b.status === "approved");
    const pending = bids.filter(b => b.status === "pending");
    const earned = approved.reduce((s, b) => s + b.amount, 0);
    const s = API.subscriptionStatus(inf);
    const trialBar = s.status === "trial"
      ? `<div class="card mb"><div class="flex between items-center mb"><strong>Free trial</strong><span class="muted">${s.daysLeft} of ${API.CONFIG.trialDays} days left</span></div>
         <div class="progress"><span style="width:${Math.max(4, (s.daysLeft/API.CONFIG.trialDays)*100)}%"></span></div>
         <p class="muted mt" style="font-size:.85rem;margin-bottom:0">Enjoy full access. <a href="#billing" data-goto="billing" style="color:var(--violet);font-weight:600">Upgrade to Pro</a> before it ends to avoid interruption.</p></div>`
      : s.status === "expired"
      ? `<div class="alert alert-warn">Your trial has ended. <a href="#billing" data-goto="billing" style="font-weight:700">Subscribe to Pro</a> to bid again.</div>`
      : `<div class="alert alert-ok">You're on <strong>Creator Pro</strong> — unlimited bidding is active. 🎉</div>`;

    document.getElementById("panel-overview").innerHTML = `
      <div class="dash-hero">
        <div class="dh-text">
          <h2>Hey ${App.esc(user.name.split(" ")[0])} 👋</h2>
          <p>Your audience is your pitch — browse fresh campaigns and bid before they close.</p>
        </div>
        <div class="hero-acts">
          <button class="btn btn-white btn-sm" data-goto="campaigns">🔎 Browse campaigns</button>
          <button class="btn btn-glass btn-sm" data-goto="profile">Sync stats</button>
        </div>
      </div>
      <div class="grid grid-4 mb">
        ${stat("📨", bids.length, "Total bids")}
        ${stat("⏳", pending.length, "Pending")}
        ${stat("✅", approved.length, "Approved")}
        ${stat("💰", App.money(earned), "Won value")}
      </div>
      ${trialBar}
      <div class="grid grid-2">
        <div class="card">
          <div class="flex between items-center mb"><h3 style="margin:0">Your audience</h3><span class="chip">${App.esc(inf.niche)}</span></div>
          <div class="metrics">
            <div class="metric synced"><div class="mv">${App.compact(inf.instaFollowers)}</div><div class="ml">IG followers</div></div>
            <div class="metric synced"><div class="mv">${App.compact(inf.ytSubscribers)}</div><div class="ml">YT subs</div></div>
            <div class="metric synced"><div class="mv">${inf.engagement}%</div><div class="ml">Engagement</div></div>
          </div>
          <div class="muted" style="font-size:.78rem;margin-top:8px">${inf.lastSynced ? "🔄 Auto-synced " + App.dateFmt(inf.lastSynced) : "⚠️ Connect your channels to fetch stats"}</div>
          <button class="btn btn-ghost btn-sm mt" data-goto="profile">Manage channels</button>
        </div>
        <div class="card">
          <h3>Quick actions</h3>
          <p class="muted" style="font-size:.9rem">Jump back into the marketplace.</p>
          <div class="flex gap wrap mt">
            <button class="btn btn-primary btn-sm" data-goto="campaigns">Browse campaigns</button>
            <button class="btn btn-ghost btn-sm" data-goto="bids">View my bids</button>
            <button class="btn btn-ghost btn-sm" data-goto="concepts">Unlocked briefs</button>
          </div>
        </div>
      </div>`;
    wireGoto();
  }

  async function renderCampaigns() {
    const host = document.getElementById("panel-campaigns");
    const allowed = API.subscriptionStatus(inf).status !== "expired";
    const products = await API.listProducts({ status: "open" });
    const myBids = await API.myBids(user.id);
    const bidProductIds = new Set(myBids.map(b => b.productId));
    if (!allowed) host.innerHTML = `<div class="alert alert-warn">Your trial has ended. <a href="#billing" data-goto="billing" style="font-weight:700">Subscribe</a> to place new bids. You can still browse below.</div>`;
    else host.innerHTML = "";
    if (!products.length) { host.innerHTML += `<div class="empty"><div class="e-emoji">📭</div>No open campaigns right now. Check back soon.</div>`; return; }
    host.innerHTML += `<div class="grid grid-3">${products.map(p => {
      const already = bidProductIds.has(p.id);
      return `<div class="card hover listing">
        <div class="thumb"${p.brandLogo?` style="background:#fff;background-image:url('${p.brandLogo}');background-size:contain;background-repeat:no-repeat;background-position:center"`:""}><span class="price">${App.money(p.budget)}</span></div>
        <div class="flex between items-center"><span class="chip">${App.esc(p.category)}</span><span class="chip">👥 ${p.bidCount}</span></div>
        <h3 style="margin-top:10px">${App.esc(p.title)}</h3>
        <p class="muted" style="font-size:.88rem">${App.esc(p.description).slice(0,120)}${p.description.length>120?"…":""}</p>
        <div class="meta"><span class="chip">🏷️ ${App.esc(p.brandName)}</span>${p.deadline?`<span class="chip">⏰ ${App.dateFmt(p.deadline)}</span>`:""}</div>
        <div class="foot">
          <span class="muted" style="font-size:.8rem">${App.esc(p.deliverables||"")}</span>
          ${already ? `<span class="badge badge-blue">Bid placed</span>`
            : `<button class="btn btn-primary btn-sm" data-bid="${p.id}" ${allowed?"":"disabled"}>Bid</button>`}
        </div>
      </div>`;
    }).join("")}</div>`;
    host.querySelectorAll("[data-bid]").forEach(b => b.addEventListener("click", () => openBid(+b.dataset.bid)));
    wireGoto();
  }

  async function openBid(productId) {
    if (!gate()) return;
    const p = await API.getProduct(productId);
    App.modal({
      title: "Bid on " + p.title,
      body: `
        <div class="alert alert-info" style="font-size:.85rem">Budget: <strong>${App.money(p.budget)}</strong> · Deliverables: ${App.esc(p.deliverables||"—")}</div>
        <form id="bidForm">
          <div class="field"><label>Your bid amount (${API.CONFIG.currencySymbol})</label><input class="input" type="number" name="amount" required min="1" value="${p.budget}" /></div>
          <div class="field"><label>Pitch — why you?</label><textarea class="input" name="message" placeholder="Mention your audience fit, past results, turnaround time…" required></textarea></div>
        </form>`,
      footer: `<button class="btn btn-ghost" id="cancelBid">Cancel</button><button class="btn btn-primary" id="submitBid">Submit bid</button>`,
    });
    document.getElementById("cancelBid").onclick = App.closeModal;
    document.getElementById("submitBid").onclick = async () => {
      const form = document.getElementById("bidForm");
      if (!form.reportValidity()) return;
      const d = App.serializeForm(form);
      try { await API.placeBid(productId, user.id, d); App.closeModal(); App.toast("Bid submitted!", "ok"); render("campaigns"); }
      catch (e) { App.toast(e.message, "err"); }
    };
  }

  async function renderBids() {
    const bids = await API.myBids(user.id);
    const host = document.getElementById("panel-bids");
    if (!bids.length) { host.innerHTML = `<div class="empty"><div class="e-emoji">📨</div>No bids yet. <button class="btn btn-primary btn-sm" data-goto="campaigns">Browse campaigns</button></div>`; wireGoto(); return; }
    host.innerHTML = `<div class="table-wrap"><table>
      <thead><tr><th>Campaign</th><th>Brand</th><th>My bid</th><th>Status</th><th>Brief</th></tr></thead>
      <tbody>${bids.map(b => `<tr>
        <td><strong>${App.esc(b.product?b.product.title:"—")}</strong></td>
        <td>${App.esc(b.product?b.product.brandName:"—")}</td>
        <td>${App.money(b.amount)}</td>
        <td>${App.statusBadge(b.status)}</td>
        <td>${b.concept ? `<button class="btn btn-primary btn-sm" data-concept="${b.id}">View brief</button>` : b.status==="approved" ? `<span class="muted">Awaiting brief</span>` : `<span class="muted">—</span>`}</td>
      </tr>`).join("")}</tbody></table></div>`;
    host.querySelectorAll("[data-concept]").forEach(btn => btn.addEventListener("click", () => showConcept(+btn.dataset.concept)));
  }

  async function renderConcepts() {
    const bids = await API.myBids(user.id);
    const withConcept = bids.filter(b => b.concept);
    const host = document.getElementById("panel-concepts");
    if (!withConcept.length) {
      host.innerHTML = `<div class="empty"><div class="e-emoji">🎬</div>No briefs yet. Once a brand approves your bid and shares the concept, it appears here.</div>`;
      return;
    }
    host.innerHTML = `<div class="grid grid-2">${withConcept.map(b => {
      const c = b.concept;
      return `<div class="card">
        <div class="flex between items-center mb"><h3 style="margin:0">${App.esc(b.product?b.product.title:"Campaign")}</h3><span class="badge badge-green">Approved</span></div>
        <div class="muted" style="font-size:.85rem;margin-bottom:12px">${App.esc(b.product?b.product.brandName:"")} · Your bid ${App.money(b.amount)}</div>
        <p style="font-weight:700;margin-bottom:4px">🎯 Concept</p><p class="muted" style="font-size:.92rem">${App.esc(c.concept||"—")}</p>
        ${c.script?`<p style="font-weight:700;margin:10px 0 4px">📝 Script direction</p><p class="muted" style="font-size:.92rem">${App.esc(c.script)}</p>`:""}
        ${c.deliverables?`<p style="font-weight:700;margin:10px 0 4px">📦 Deliverables</p><p class="muted" style="font-size:.92rem">${App.esc(c.deliverables)}</p>`:""}
        ${c.deadline?`<span class="chip">⏰ Due ${App.dateFmt(c.deadline)}</span>`:""}
      </div>`;
    }).join("")}</div>`;
  }

  async function showConcept(bidId) {
    const c = await API.getConceptForBid(bidId);
    if (!c) { App.toast("Brief not available yet.", "err"); return; }
    App.modal({
      title: "Creative brief",
      body: `
        <p style="font-weight:700;margin-bottom:4px">🎯 Concept</p><p class="muted">${App.esc(c.concept||"—")}</p>
        ${c.script?`<p style="font-weight:700;margin:10px 0 4px">📝 Script direction</p><p class="muted">${App.esc(c.script)}</p>`:""}
        ${c.deliverables?`<p style="font-weight:700;margin:10px 0 4px">📦 Deliverables</p><p class="muted">${App.esc(c.deliverables)}</p>`:""}
        ${c.deadline?`<span class="chip">⏰ Due ${App.dateFmt(c.deadline)}</span>`:""}`,
      footer: `<button class="btn btn-primary" onclick="App.closeModal()">Got it</button>`,
    });
  }

  async function renderProfile() {
    const host = document.getElementById("panel-profile");
    const igOn = !!inf.instaUrl, ytOn = !!inf.ytUrl;
    const connectRow = (platform, icon, iconCls, label, url, on) => `
      <div class="connect-row">
        <div class="connect-ic ${iconCls}">${icon}</div>
        <div class="grow">
          <div class="conn-title">${label} <span class="status-dot ${on ? "dot-on" : "dot-off"}"></span>
            ${on ? `<span class="synced-tag">Connected</span>` : `<span class="muted" style="font-size:.78rem">Not connected</span>`}</div>
          <input class="input" data-url="${platform}" value="${App.esc(url || "")}" placeholder="${platform === "instagram" ? "https://instagram.com/yourhandle" : "https://youtube.com/@yourchannel"}" style="margin-top:8px" />
        </div>
        <div class="flex gap-sm" style="flex-direction:column">
          <button class="btn btn-primary btn-sm" data-connect="${platform}">${on ? "Update" : "Connect"}</button>
          ${on ? `<button class="btn btn-ghost btn-sm" data-disconnect="${platform}">Remove</button>` : ""}
        </div>
      </div>`;

    host.innerHTML = `
      <div class="card mb flex gap items-center wrap">
        ${App.avatar(inf.name, inf.avatar, "lg")}
        <div style="flex:1;min-width:0">
          <h3 style="margin:0">${App.esc(inf.name)}</h3>
          <div class="muted" style="font-size:.88rem">@${App.esc(inf.handle)} · ${App.esc(inf.niche)} · ${App.esc(inf.location || "—")}</div>
        </div>
        <span class="badge ${API.subscriptionStatus(inf).status === "pro" ? "badge-green" : "badge-amber"}">${API.subscriptionStatus(inf).label}</span>
      </div>
      <div class="grid grid-2">
        <div class="card">
          <h3>Connected channels</h3>
          <p class="muted" style="font-size:.88rem">Your stats are fetched automatically from these links — you never type numbers by hand.</p>
          ${connectRow("instagram", "📸", "ic-ig", "Instagram", inf.instaUrl, igOn)}
          ${connectRow("youtube", "▶️", "ic-yt", "YouTube", inf.ytUrl, ytOn)}
          <div class="flex between items-center mt">
            <span class="muted" style="font-size:.8rem">${inf.lastSynced ? "Last synced " + App.dateFmt(inf.lastSynced) : "Not synced yet"}</span>
            <button class="btn btn-dark btn-sm" id="syncBtn" ${igOn || ytOn ? "" : "disabled"}>🔄 Sync now</button>
          </div>
        </div>

        <div class="card">
          <h3>Fetched stats</h3>
          <p class="muted" style="font-size:.88rem">Read-only — pulled from your connected accounts.</p>
          <div class="metrics">
            <div class="metric synced"><div class="mv">${App.compact(inf.instaFollowers)}</div><div class="ml">IG followers</div><div class="src">Instagram</div></div>
            <div class="metric synced"><div class="mv">${App.compact(inf.instaTopReel)}</div><div class="ml">Top reel</div><div class="src">Instagram</div></div>
            <div class="metric synced"><div class="mv">${inf.engagement}%</div><div class="ml">Engagement</div><div class="src">Instagram</div></div>
          </div>
          <div class="metrics mt" style="grid-template-columns:1fr 1fr">
            <div class="metric synced"><div class="mv">${App.compact(inf.ytSubscribers)}</div><div class="ml">YT subscribers</div><div class="src">YouTube</div></div>
            <div class="metric synced"><div class="mv">${App.compact(inf.ytTopViews)}</div><div class="ml">Top video</div><div class="src">YouTube</div></div>
          </div>
        </div>
      </div>

      <div class="card mt-lg" style="max-width:720px">
        <h3>Profile details</h3>
        <form id="profForm">
          <div class="field-row">
            <div class="field"><label>Display name</label><input class="input" name="name" value="${App.esc(inf.name)}" required /></div>
            <div class="field"><label>Handle</label><input class="input" name="handle" value="${App.esc(inf.handle)}" /></div>
          </div>
          <div class="field-row">
            <div class="field"><label>Niche</label><select class="input" name="niche">${["Tech","Fashion","Beauty","Fitness","Food","Travel","Gaming","Lifestyle","Finance","Comedy"].map(n=>`<option ${n===inf.niche?"selected":""}>${n}</option>`).join("")}</select></div>
            <div class="field"><label>City</label><input class="input" name="location" value="${App.esc(inf.location||"")}" /></div>
          </div>
          <div class="field"><label>Bio</label><textarea class="input" name="bio">${App.esc(inf.bio||"")}</textarea></div>
          <button class="btn btn-primary" type="submit">Save details</button>
        </form>
      </div>`;

    host.querySelectorAll("[data-connect]").forEach(btn => btn.addEventListener("click", async () => {
      const platform = btn.dataset.connect;
      const url = host.querySelector(`[data-url="${platform}"]`).value.trim();
      if (!url) { App.toast("Paste your " + platform + " link first.", "err"); return; }
      btn.disabled = true; btn.textContent = "Fetching…";
      try { await API.connectSocial(user.id, platform, url); await refreshInf(); App.toast("Connected & stats fetched!", "ok"); renderProfile(); }
      catch (e) { App.toast(e.message, "err"); btn.disabled = false; }
    }));
    host.querySelectorAll("[data-disconnect]").forEach(btn => btn.addEventListener("click", async () => {
      await API.disconnectSocial(user.id, btn.dataset.disconnect); await refreshInf(); App.toast("Disconnected."); renderProfile();
    }));
    const syncBtn = document.getElementById("syncBtn");
    if (syncBtn) syncBtn.addEventListener("click", async () => {
      syncBtn.disabled = true; syncBtn.textContent = "Syncing…";
      try { await API.syncStats(user.id); await refreshInf(); App.toast("Stats refreshed.", "ok"); renderProfile(); }
      catch (e) { App.toast(e.message, "err"); syncBtn.disabled = false; syncBtn.textContent = "🔄 Sync now"; }
    });
    document.getElementById("profForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      await API.updateInfluencer(user.id, App.serializeForm(e.target));
      await refreshInf();
      App.toast("Profile updated.", "ok");
    });
  }

  async function renderBilling() {
    const s = API.subscriptionStatus(inf);
    const payments = await API.paymentsFor(user.id);
    const host = document.getElementById("panel-billing");
    const planCard = s.status === "pro"
      ? `<div class="card"><div class="flex between items-center"><div><h3 style="margin:0">Creator Pro</h3><p class="muted" style="margin:0">Active until ${App.dateFmt(inf.subscribedUntil)}</p></div><span class="badge badge-green">Active</span></div></div>`
      : `<div class="card price-card featured" style="max-width:380px">
          <span class="ribbon">${s.status==="trial"?`Trial · ${s.daysLeft} days left`:"Trial ended"}</span>
          <h3>Upgrade to Creator Pro</h3>
          <div class="amount">${App.money(API.CONFIG.subscriptionMonthly)}<span style="font-size:1rem;font-weight:600;color:var(--muted)">/mo</span></div>
          <ul><li>✓ Unlimited bids</li><li>✓ Verified stats badge</li><li>✓ Priority to brands</li><li>✓ Lower payout fees</li></ul>
          <button class="btn btn-primary btn-block" id="subBtn">Subscribe now</button>
        </div>`;
    host.innerHTML = `
      <div class="grid grid-2 mb">
        ${planCard}
        <div class="card">
          <h3>How billing works</h3>
          <ul class="muted" style="padding-left:18px;font-size:.92rem">
            <li>Every creator gets a <strong>${API.CONFIG.trialDays}-day free trial</strong>.</li>
            <li>After the trial, subscribe to <strong>Pro</strong> (${App.money(API.CONFIG.subscriptionMonthly)}/mo) to keep bidding.</li>
            <li>Prefer no monthly fee? Switch to <strong>pay-per-deal</strong> — ${API.CONFIG.influencerCommissionPct}% commission on accepted bids.</li>
            <li>Payments are processed securely through our gateway.</li>
          </ul>
        </div>
      </div>
      <h3>Payment history</h3>
      ${payments.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Description</th><th>Amount</th><th>Status</th></tr></thead>
        <tbody>${payments.map(p=>`<tr><td>${App.dateFmt(p.createdAt)}</td><td>${App.esc(p.note||p.type)}</td><td>${App.money(p.amount)}</td><td>${App.statusBadge(p.status)}</td></tr>`).join("")}</tbody></table></div>`
        : `<div class="empty"><div class="e-emoji">🧾</div>No payments yet.</div>`}`;
    const subBtn = document.getElementById("subBtn");
    if (subBtn) subBtn.addEventListener("click", () => payFlow());
  }

  function payFlow() {
    App.modal({
      title: "Secure checkout",
      body: `
        <div class="alert alert-info" style="font-size:.85rem">🔒 Demo payment gateway — no real charge. Plug in Razorpay/Stripe at the Go backend layer later.</div>
        <div class="flex between items-center mb"><strong>Creator Pro — Monthly</strong><strong>${App.money(API.CONFIG.subscriptionMonthly)}</strong></div>
        <form id="payForm">
          <div class="field"><label>Card number</label><input class="input" inputmode="numeric" placeholder="4242 4242 4242 4242" required /></div>
          <div class="field-row">
            <div class="field"><label>Expiry</label><input class="input" placeholder="MM/YY" required /></div>
            <div class="field"><label>CVV</label><input class="input" placeholder="123" required /></div>
          </div>
          <div class="field"><label>Name on card</label><input class="input" value="${App.esc(user.name)}" required /></div>
        </form>`,
      footer: `<button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button><button class="btn btn-primary" id="payNow">Pay ${App.money(API.CONFIG.subscriptionMonthly)}</button>`,
    });
    document.getElementById("payNow").onclick = async () => {
      const f = document.getElementById("payForm");
      if (!f.reportValidity()) return;
      await API.subscribe(user.id);
      await refreshInf();
      App.closeModal();
      App.toast("You're now on Creator Pro! 🎉", "ok");
      render("billing");
    };
  }

  // ---- helpers ----
  function stat(icon, value, label) {
    return `<div class="card stat"><div class="si">${icon}</div><div><div class="sv">${value}</div><div class="sl">${label}</div></div></div>`;
  }
  function wireGoto() {
    document.querySelectorAll("[data-goto]").forEach(el => el.addEventListener("click", (e) => { e.preventDefault(); go(el.dataset.goto); }));
  }

  // ---- boot ----
  refreshPill();
  const start = (location.hash || "#overview").slice(1);
  go(titles[start] ? start : "overview");
})();
