/* ============================================================
   Plugg — Brand dashboard logic
   ============================================================ */
(async function () {
  const user = await App.requireRole("brand");
  if (!user) return;
  await App.renderShell({ active: "" });

  let brand = await API.getBrand(user.id);
  document.getElementById("sbName").textContent = brand.company || user.name;
  if (brand && brand.logo) {
    const sba = document.querySelector(".sb-avatar");
    sba.textContent = ""; sba.style.cssText = `background-image:url('${brand.logo}');background-size:cover;background-position:center;background-color:#fff`;
  }
  document.getElementById("sbFoot").innerHTML = `<div class="card" style="padding:16px;background:var(--grad-soft);border-color:transparent">
    <strong style="font-size:.9rem">Ready to launch?</strong>
    <p class="muted" style="font-size:.78rem;margin:4px 0 10px">Post a campaign and start receiving bids.</p>
    <button class="btn btn-primary btn-sm btn-block" id="sbPost">➕ New campaign</button></div>`;
  document.getElementById("sbPost").addEventListener("click", () => go("post"));
  const titles = {
    overview: ["Overview", "Your campaigns at a glance"],
    campaigns: ["My campaigns", "Review bidders & manage collaborations"],
    post: ["Post a campaign", "Tell creators what you need"],
    discover: ["Discover creators", "Browse talent by niche & audience"],
    billing: ["Payments", "Commissions paid to the platform"],
    profile: ["Brand profile", "How creators see your brand"],
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

  async function render(panel) {
    if (panel === "overview") return renderOverview();
    if (panel === "campaigns") return renderCampaigns();
    if (panel === "post") return renderPost();
    if (panel === "discover") return renderDiscover();
    if (panel === "billing") return renderBilling();
    if (panel === "profile") return renderProfile();
  }

  async function renderOverview() {
    const products = await API.listProducts({ brandUserId: user.id });
    let totalBids = 0, approved = 0, spend = 0;
    for (const p of products) {
      const bids = await API.bidsForProduct(p.id);
      totalBids += bids.length;
      const a = bids.find(b => b.status === "approved");
      if (a) { approved++; spend += a.amount; }
    }
    const open = products.filter(p => p.status === "open").length;
    document.getElementById("panel-overview").innerHTML = `
      <div class="dash-hero">
        <div class="dh-text">
          <h2>Welcome, ${App.esc(brand.company || user.name)} 🏷️</h2>
          <p>Compare creators by real audience data and approve the perfect match.</p>
        </div>
        <div class="hero-acts">
          <button class="btn btn-white btn-sm" data-goto="post">➕ Post a campaign</button>
          <button class="btn btn-glass btn-sm" data-goto="discover">🔎 Discover</button>
        </div>
      </div>
      <div class="grid grid-4 mb">
        ${stat("📣", products.length, "Campaigns")}
        ${stat("🟢", open, "Open")}
        ${stat("📨", totalBids, "Total bids")}
        ${stat("💰", App.money(spend), "Committed spend")}
      </div>
      <div class="grid grid-2">
        <div class="card">
          <h3>Get started</h3>
          <p class="muted" style="font-size:.92rem">Post a campaign, then review creator bids side-by-side and approve the best fit.</p>
          <div class="flex gap wrap mt">
            <button class="btn btn-primary btn-sm" data-goto="post">➕ Post campaign</button>
            <button class="btn btn-ghost btn-sm" data-goto="campaigns">Review bids</button>
            <button class="btn btn-ghost btn-sm" data-goto="discover">Find creators</button>
          </div>
        </div>
        <div class="card">
          <h3>How fees work</h3>
          <p class="muted" style="font-size:.92rem">Posting and browsing is free. You pay a <strong>${API.CONFIG.brandCommissionPct}% platform commission</strong> only when you approve a bid — and it's handled automatically at approval.</p>
        </div>
      </div>`;
    wireGoto();
  }

  async function renderCampaigns() {
    const products = await API.listProducts({ brandUserId: user.id });
    const host = document.getElementById("panel-campaigns");
    if (!products.length) { host.innerHTML = `<div class="empty"><div class="e-emoji">📣</div>No campaigns yet. <button class="btn btn-primary btn-sm" data-goto="post">Post your first</button></div>`; wireGoto(); return; }
    const blocks = [];
    for (const p of products) {
      const bids = await API.bidsForProduct(p.id);
      blocks.push(`<div class="card mb">
        <div class="flex between items-center wrap gap">
          <div><h3 style="margin:0">${App.esc(p.title)}</h3>
            <div class="muted" style="font-size:.85rem">${App.esc(p.category)} · Budget ${App.money(p.budget)} ${p.deadline?`· Due ${App.dateFmt(p.deadline)}`:""}</div></div>
          <div class="flex gap items-center">${App.statusBadge(p.status)}<span class="chip">${bids.length} bid${bids.length===1?"":"s"}</span></div>
        </div>
        <p class="muted" style="font-size:.9rem;margin-top:10px">${App.esc(p.description)}</p>
        <div class="divider"></div>
        ${bids.length ? `<div class="grid grid-2">${bids.map(b => bidCard(p, b)).join("")}</div>`
          : `<p class="muted" style="margin:0">No bids yet — share your campaign to attract creators.</p>`}
      </div>`);
    }
    host.innerHTML = blocks.join("");
    host.querySelectorAll("[data-approve]").forEach(b => b.addEventListener("click", () => approveBid(+b.dataset.approve, +b.dataset.product)));
    host.querySelectorAll("[data-reject]").forEach(b => b.addEventListener("click", () => rejectBid(+b.dataset.reject)));
    host.querySelectorAll("[data-concept]").forEach(b => b.addEventListener("click", () => conceptModal(+b.dataset.concept, +b.dataset.product)));
    host.querySelectorAll("[data-view]").forEach(b => b.addEventListener("click", () => viewCreator(+b.dataset.view)));
    wireGoto();
  }

  function bidCard(p, b) {
    const i = b.influencer || {};
    const pro = i.sub && i.sub.status === "pro" ? '<span class="badge badge-violet">Pro ✓</span>' : "";
    const actions = b.status === "pending"
      ? `<button class="btn btn-primary btn-sm" data-approve="${b.id}" data-product="${p.id}">Approve</button>
         <button class="btn btn-ghost btn-sm" data-reject="${b.id}">Decline</button>`
      : b.status === "approved"
      ? `<button class="btn btn-primary btn-sm" data-concept="${b.id}" data-product="${p.id}">Share / edit brief</button>`
      : `<span class="badge badge-red">Declined</span>`;
    return `<div class="card" style="box-shadow:none;border-color:var(--line)">
      <div class="flex gap items-center">
        ${App.avatar(i.name || b.influencerName, i.avatar)}
        <div style="flex:1">
          <div class="flex between items-center"><strong>${App.esc(i.name||b.influencerName)}</strong>${pro}</div>
          <div class="muted" style="font-size:.8rem">@${App.esc(i.handle||"creator")} · ${App.esc(i.niche||"—")}</div>
        </div>
        <div style="text-align:right"><div style="font-weight:800">${App.money(b.amount)}</div>${App.statusBadge(b.status)}</div>
      </div>
      <div class="metrics mt">
        <div class="metric"><div class="mv">${App.compact(i.instaFollowers||0)}</div><div class="ml">IG</div></div>
        <div class="metric"><div class="mv">${App.compact(i.ytSubscribers||0)}</div><div class="ml">YT</div></div>
        <div class="metric"><div class="mv">${(i.engagement||0)}%</div><div class="ml">Eng.</div></div>
      </div>
      <p class="muted" style="font-size:.86rem;margin:10px 0">“${App.esc(b.message||"")}”</p>
      <div class="flex gap wrap">${actions}<button class="btn btn-ghost btn-sm" data-view="${b.influencerUserId}">Profile</button></div>
    </div>`;
  }

  async function approveBid(bidId, productId) {
    const bids = await API.bidsForProduct(productId);
    const b = bids.find(x => x.id === bidId);
    const commission = Math.round(b.amount * API.CONFIG.brandCommissionPct / 100);
    App.modal({
      title: "Approve this bid?",
      body: `
        <p>You're approving <strong>${App.esc(b.influencerName)}</strong> at <strong>${App.money(b.amount)}</strong>.</p>
        <div class="alert alert-info" style="font-size:.88rem">A <strong>${API.CONFIG.brandCommissionPct}% platform commission (${App.money(commission)})</strong> applies to the accepted bid. All other bids on this campaign will be declined.</div>
        <p class="muted" style="font-size:.88rem">After approving, you'll share the private video concept with the creator.</p>`,
      footer: `<button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button><button class="btn btn-primary" id="confirmApprove">Approve & continue</button>`,
    });
    document.getElementById("confirmApprove").onclick = async () => {
      await API.updateBidStatus(bidId, "approved");
      App.closeModal();
      App.toast("Bid approved! Now share your concept.", "ok");
      conceptModal(bidId, productId);
    };
  }

  async function rejectBid(bidId) {
    await API.updateBidStatus(bidId, "rejected");
    App.toast("Bid declined.");
    render("campaigns");
  }

  async function conceptModal(bidId, productId) {
    const existing = await API.getConceptForBid(bidId);
    const p = await API.getProduct(productId);
    App.modal({
      title: "Share your video concept",
      maxWidth: 560,
      body: `
        <div class="alert alert-ok" style="font-size:.85rem">🔒 Only the approved creator can see this brief.</div>
        <form id="conceptForm">
          <div class="field"><label>Creative concept *</label><textarea class="input" name="concept" required placeholder="The big idea, tone, hook, must-mention points…">${App.esc(existing?existing.concept:"")}</textarea></div>
          <div class="field"><label>Script / shot direction</label><textarea class="input" name="script" placeholder="Optional structure, talking points, do's & don'ts…">${App.esc(existing?existing.script:"")}</textarea></div>
          <div class="field"><label>Deliverables</label><input class="input" name="deliverables" value="${App.esc(existing?existing.deliverables:p.deliverables||"")}" /></div>
          <div class="field"><label>Delivery deadline</label><input class="input" type="date" name="deadline" value="${existing?existing.deadline||"":p.deadline||""}" /></div>
        </form>`,
      footer: `<button class="btn btn-ghost" onclick="App.closeModal()">Later</button><button class="btn btn-primary" id="saveConcept">${existing?"Update brief":"Send brief"}</button>`,
    });
    document.getElementById("saveConcept").onclick = async () => {
      const f = document.getElementById("conceptForm");
      if (!f.reportValidity()) return;
      await API.shareConcept(bidId, user.id, App.serializeForm(f));
      App.closeModal();
      App.toast("Concept shared with the creator!", "ok");
      render("campaigns");
    };
  }

  function renderPost() {
    document.getElementById("panel-post").innerHTML = `<div class="card" style="max-width:720px">
      <form id="postForm">
        <div class="field"><label>Campaign title *</label><input class="input" name="title" required placeholder="e.g. Summer Glow Serum — GRWM Reel" /></div>
        <div class="field"><label>Description *</label><textarea class="input" name="description" required placeholder="What's the product? What are you looking for from creators?"></textarea></div>
        <div class="field-row">
          <div class="field"><label>Category</label><select class="input" name="category">${["Tech","Fashion","Beauty","Fitness","Food","Travel","Gaming","Lifestyle","Finance","General"].map(c=>`<option>${c}</option>`).join("")}</select></div>
          <div class="field"><label>Budget (${API.CONFIG.currencySymbol}) *</label><input class="input" type="number" name="budget" required min="1" placeholder="e.g. 45000" /></div>
        </div>
        <div class="field-row">
          <div class="field"><label>Deliverables</label><input class="input" name="deliverables" placeholder="e.g. 1 Reel + 3 stories" /></div>
          <div class="field"><label>Deadline</label><input class="input" type="date" name="deadline" /></div>
        </div>
        <div class="alert alert-info" style="font-size:.85rem">💡 Keep your secret creative concept out of this public post — you'll share it privately after approving a creator.</div>
        <button class="btn btn-primary" type="submit">Publish campaign</button>
      </form>
    </div>`;
    document.getElementById("postForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const d = App.serializeForm(e.target);
      await API.createProduct(user.id, d);
      App.toast("Campaign published! 🎉", "ok");
      go("campaigns");
    });
  }

  async function renderDiscover() {
    const list = await API.listInfluencers();
    document.getElementById("panel-discover").innerHTML = `<div class="grid grid-3">${list.map(i => `
      <div class="card hover">
        <div class="flex gap items-center">
          ${App.avatar(i.name, i.avatar, "lg")}
          <div style="flex:1"><div class="flex between items-center"><h3 style="margin:0">${App.esc(i.name)}</h3>${i.sub.status==="pro"?'<span class="badge badge-violet">Pro ✓</span>':""}</div>
          <div class="muted" style="font-size:.82rem">@${App.esc(i.handle)} · ${App.esc(i.niche)}</div></div>
        </div>
        <div class="metrics mt">
          <div class="metric"><div class="mv">${App.compact(i.instaFollowers)}</div><div class="ml">IG</div></div>
          <div class="metric"><div class="mv">${App.compact(i.ytSubscribers)}</div><div class="ml">YT</div></div>
          <div class="metric"><div class="mv">${i.engagement}%</div><div class="ml">Eng.</div></div>
        </div>
        <button class="btn btn-ghost btn-sm mt" data-view="${i.userId}">View profile</button>
      </div>`).join("")}</div>`;
    document.querySelectorAll("#panel-discover [data-view]").forEach(b => b.addEventListener("click", () => viewCreator(+b.dataset.view)));
  }

  async function viewCreator(userId) {
    const i = await API.getInfluencer(userId);
    if (!i) return;
    const s = API.subscriptionStatus(i);
    App.modal({
      title: i.name,
      body: `
        <div class="flex gap items-center mb">
          ${App.avatar(i.name, i.avatar, "lg")}
          <div><div class="flex gap items-center"><strong>@${App.esc(i.handle)}</strong>${s.status==="pro"?'<span class="badge badge-violet">Pro ✓</span>':""}</div>
          <div class="muted" style="font-size:.85rem">${App.esc(i.niche)} · ${App.esc(i.location||"—")}</div></div>
        </div>
        <p class="muted">${App.esc(i.bio||"")}</p>
        <div class="metrics mt">
          <div class="metric"><div class="mv">${App.compact(i.instaFollowers)}</div><div class="ml">IG followers</div></div>
          <div class="metric"><div class="mv">${App.compact(i.instaTopReel)}</div><div class="ml">Top reel</div></div>
          <div class="metric"><div class="mv">${i.engagement}%</div><div class="ml">Engagement</div></div>
        </div>
        <div class="metrics mt" style="grid-template-columns:1fr 1fr">
          <div class="metric"><div class="mv">${App.compact(i.ytSubscribers)}</div><div class="ml">YT subscribers</div></div>
          <div class="metric"><div class="mv">${App.compact(i.ytTopViews)}</div><div class="ml">Top video</div></div>
        </div>`,
      footer: `<button class="btn btn-primary" onclick="App.closeModal()">Close</button>`,
    });
  }

  async function renderBilling() {
    const payments = await API.paymentsFor(user.id);
    const total = payments.reduce((s, p) => s + p.amount, 0);
    document.getElementById("panel-billing").innerHTML = `
      <div class="grid grid-3 mb">
        ${stat("💸", App.money(total), "Total commission paid")}
        ${stat("🤝", payments.length, "Accepted deals")}
        ${stat("📈", API.CONFIG.brandCommissionPct + "%", "Commission rate")}
      </div>
      <div class="alert alert-info" style="font-size:.88rem">Commission is charged automatically on the winning bid when you approve a creator. Posting and reviewing bids is always free.</div>
      <h3>Commission history</h3>
      ${payments.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Description</th><th>Bid value</th><th>Commission</th><th>Status</th></tr></thead>
        <tbody>${payments.map(p=>`<tr><td>${App.dateFmt(p.createdAt)}</td><td>${App.esc(p.note||p.type)}</td><td>${p.gross?App.money(p.gross):"—"}</td><td>${App.money(p.amount)}</td><td>${App.statusBadge(p.status)}</td></tr>`).join("")}</tbody></table></div>`
        : `<div class="empty"><div class="e-emoji">🧾</div>No commissions yet — they appear when you approve a bid.</div>`}`;
  }

  async function renderProfile() {
    document.getElementById("panel-profile").innerHTML = `<div class="card" style="max-width:640px">
      <form id="brandForm">
        <div class="field"><label>Company name</label><input class="input" name="company" value="${App.esc(brand.company)}" required /></div>
        <div class="field-row">
          <div class="field"><label>Industry</label><select class="input" name="industry">${["Electronics","Fashion","Beauty","Health","Food & Beverage","Travel","Gaming","Finance","General"].map(c=>`<option ${c===brand.industry?"selected":""}>${c}</option>`).join("")}</select></div>
          <div class="field"><label>Website</label><input class="input" name="website" value="${App.esc(brand.website||"")}" /></div>
        </div>
        <div class="field"><label>About</label><textarea class="input" name="about">${App.esc(brand.about||"")}</textarea></div>
        <button class="btn btn-primary" type="submit">Save profile</button>
      </form>
    </div>`;
    document.getElementById("brandForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      await API.updateBrand(user.id, App.serializeForm(e.target));
      brand = await API.getBrand(user.id);
      App.toast("Brand profile updated.", "ok");
    });
  }

  function stat(icon, value, label) {
    return `<div class="card stat"><div class="si">${icon}</div><div><div class="sv">${value}</div><div class="sl">${label}</div></div></div>`;
  }
  function wireGoto() {
    document.querySelectorAll("[data-goto]").forEach(el => el.addEventListener("click", (e) => { e.preventDefault(); go(el.dataset.goto); }));
  }

  // global new-campaign button in page head
  wireGoto();
  const start = (location.hash || "#overview").slice(1);
  go(titles[start] ? start : "overview");
})();
