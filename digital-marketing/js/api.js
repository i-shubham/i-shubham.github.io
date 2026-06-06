/* ============================================================
   Plugg — Data / API layer
   ------------------------------------------------------------
   This module is the SINGLE source of truth for all data access.
   Today it is backed by the browser's localStorage so the site
   works as a fully static demo with zero server.

   LATER (Go / Chi + MySQL):
   Flip `API.useBackend = true` and set `API.baseURL`. Every method
   already returns a Promise and mirrors REST endpoints, so the UI
   code never changes — only the transport inside this file does.

   Suggested REST mapping (Axum handlers):
     POST   /auth/register                 -> register()
     POST   /auth/login                    -> login()
     GET    /me                            -> currentUser()
     GET    /products                      -> listProducts()
     POST   /products                      -> createProduct()
     GET    /products/{id}/bids            -> bidsForProduct()
     POST   /products/{id}/bids            -> placeBid()
     PATCH  /bids/{id}                     -> updateBidStatus()
     POST   /bids/{id}/concept             -> shareConcept()
     GET    /influencers                   -> listInfluencers()
     POST   /payments                      -> recordPayment()
     POST   /subscriptions                 -> subscribe()
     GET    /admin/revenue                 -> adminRevenue()
   ============================================================ */

const API = (() => {
  const KEY = "plugg_db_v1";

  // Safe localStorage wrapper (Chrome blocks access on file:// URLs)
  const storage = {
    get(k)    { try { return localStorage.getItem(k); }            catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); }               catch {} },
    del(k)    { try { localStorage.removeItem(k); }                catch {} },
  };

  // --- Revenue config (Admin levers) -----------------------------
  const CONFIG = {
    trialDays: 30,
    brandCommissionPct: 10,      // % taken from brand on accepted bid
    influencerCommissionPct: 8,  // % taken from influencer payout (commission plan)
    subscriptionMonthly: 1499,   // INR / month (influencer Pro plan)
    currency: "INR",
    currencySymbol: "\u20B9",
  };

  // --- Backend toggle (Rust/Axum integration) --------
  const state = { useBackend: true, baseURL: "/api" };

  // --- localStorage helpers -------------------------------------
  function blankDB() {
    return { users: [], influencers: [], brands: [], products: [], bids: [], concepts: [], payments: [], seq: 1 };
  }
  function load() {
    try {
      const raw = storage.get(KEY);
      return raw ? JSON.parse(raw) : blankDB();
    } catch (e) { return blankDB(); }
  }
  function save(db) { storage.set(KEY, JSON.stringify(db)); }
  function nextId(db) { return db.seq++; }
  const delay = (ms = 120) => new Promise(r => setTimeout(r, ms));
  const ok = async (data) => { await delay(); return data; };
  const fail = async (msg) => { await delay(); throw new Error(msg); };

  // --- Future fetch wrapper (used when useBackend = true) -------
  async function http(method, path, body) {
    const headers = { ...authHeader() };
    if (body) headers["Content-Type"] = "application/json";
    const res = await fetch(state.baseURL + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || e.detail || res.statusText); }
    return res.status === 204 ? null : res.json();
  }
  function authHeader() {
    const t = storage.get("plugg_token");
    return t ? { Authorization: "Bearer " + t } : {};
  }

  // --- Session --------------------------------------------------
  const SESSION_KEY = "plugg_session";
  function setSession(userId) { storage.set(SESSION_KEY, String(userId)); }
  function clearSession() { storage.del(SESSION_KEY); }
  function sessionId() { const v = storage.get(SESSION_KEY); return v ? Number(v) : null; }

  // --- Social stat sync (demo) ----------------------------------
  // In the static demo we cannot call the real Instagram/YouTube APIs,
  // so we deterministically derive realistic numbers from the connected
  // URL/handle. When the Rust/Axum backend is live, replace `applySync`
  // with a server call to the Graph API / YouTube Data API.
  function strHash(s) {
    s = String(s || ""); let h = 2166136261;
    for (let k = 0; k < s.length; k++) { h ^= s.charCodeAt(k); h = Math.imul(h, 16777619); }
    return Math.abs(h);
  }
  function fetchInstagram(url) {
    const h = strHash("ig:" + url);
    const followers = 25000 + (h % 1175000);
    return { followers, topReel: Math.round(followers * (2 + (h % 900) / 100)), engagement: +(2 + (h % 80) / 10).toFixed(1) };
  }
  function fetchYouTube(url) {
    const h = strHash("yt:" + url);
    const subs = 10000 + (h % 990000);
    return { subs, topViews: Math.round(subs * (3 + (h % 1200) / 100)) };
  }
  // Mutates an influencer record in place using its connected accounts.
  function applySync(inf) {
    if (inf.instaUrl) { const r = fetchInstagram(inf.instaUrl); inf.instaFollowers = r.followers; inf.instaTopReel = r.topReel; inf.engagement = r.engagement; }
    if (inf.ytUrl) { const r = fetchYouTube(inf.ytUrl); inf.ytSubscribers = r.subs; inf.ytTopViews = r.topViews; }
    if (inf.instaUrl || inf.ytUrl) inf.lastSynced = new Date().toISOString();
    return inf;
  }

  // --- Derived helpers -----------------------------------------
  function trialInfo(inf) {
    const start = new Date(inf.trialStart);
    const end = new Date(start.getTime() + CONFIG.trialDays * 86400000);
    const daysLeft = Math.ceil((end - Date.now()) / 86400000);
    return { end, daysLeft, active: daysLeft > 0 };
  }
  function subscriptionStatus(inf) {
    if (inf.plan === "pro" && inf.subscribedUntil && new Date(inf.subscribedUntil) > new Date())
      return { status: "pro", label: "Pro subscriber" };
    const t = trialInfo(inf);
    if (t.active) return { status: "trial", label: `Trial · ${t.daysLeft} day${t.daysLeft === 1 ? "" : "s"} left`, daysLeft: t.daysLeft };
    return { status: "expired", label: "Trial expired" };
  }

  // ============================================================
  //  AUTH
  // ============================================================
  async function register({ role, name, email, password, profile }) {
    if (state.useBackend) {
      const body = { role, name, email, password, ...profile };
      const r = await http("POST", "/auth/register", body);
      if (r.token) storage.set("plugg_token", r.token);
      setSession(r.user.id);
      return r.user;
    }
    const db = load();
    if (db.users.find(u => u.email.toLowerCase() === email.toLowerCase()))
      return fail("An account with this email already exists.");
    const id = nextId(db);
    const user = { id, role, name, email, password, createdAt: new Date().toISOString() };
    db.users.push(user);
    if (role === "influencer") {
      const inf = {
        userId: id, name, handle: (profile.handle || name).replace(/\s+/g, "").toLowerCase(),
        niche: profile.niche || "Lifestyle", bio: profile.bio || "",
        instaUrl: profile.instaUrl || "", ytUrl: profile.ytUrl || "",
        instaFollowers: 0, instaTopReel: 0, ytSubscribers: 0, ytTopViews: 0, engagement: 0,
        lastSynced: null, location: profile.location || "",
        trialStart: new Date().toISOString(), plan: "trial", subscribedUntil: null, planType: profile.planType || "subscription",
      };
      applySync(inf); // auto-fetch stats from any connected accounts
      db.influencers.push(inf);
    } else if (role === "brand") {
      db.brands.push({
        userId: id, company: profile.company || name, industry: profile.industry || "General",
        website: profile.website || "", about: profile.about || "", logo: "",
      });
    }
    save(db);
    setSession(id);
    return ok(sanitize(user));
  }

  async function login({ email, password }) {
    if (state.useBackend) {
      const r = await http("POST", "/auth/login", { email, password });
      if (r.token) storage.set("plugg_token", r.token);
      setSession(r.user.id);
      return r.user;
    }
    const db = load();
    const user = db.users.find(u => u.email.toLowerCase() === email.toLowerCase());
    if (!user || user.password !== password) return fail("Invalid email or password.");
    setSession(user.id);
    return ok(sanitize(user));
  }

  function logout() { clearSession(); storage.del("plugg_token"); }

  async function currentUser() {
    if (state.useBackend) {
      if (!storage.get("plugg_token")) return null;
      try {
        const r = await http("GET", "/me");
        return r ? r.user : null;
      } catch (e) { return null; }
    }
    const id = sessionId();
    if (!id) return null;
    const db = load();
    const u = db.users.find(x => x.id === id);
    return u ? sanitize(u) : null;
  }

  function sanitize(u) { const { password, ...rest } = u; return rest; }

  // ============================================================
  //  PROFILES
  // ============================================================
  async function getInfluencer(userId) {
    const db = load();
    return ok(db.influencers.find(i => i.userId === userId) || null);
  }
  async function getBrand(userId) {
    const db = load();
    return ok(db.brands.find(b => b.userId === userId) || null);
  }
  async function updateInfluencer(userId, patch) {
    const db = load();
    const i = db.influencers.find(x => x.userId === userId);
    if (!i) return fail("Profile not found");
    // Guard: stat numbers can never be set by hand — they are fetched.
    ["instaFollowers", "instaTopReel", "ytSubscribers", "ytTopViews", "engagement"].forEach(k => delete patch[k]);
    Object.assign(i, patch); save(db); return ok(i);
  }
  // Connect (or update) a social account, then immediately fetch its stats.
  async function connectSocial(userId, platform, url) {
    if (state.useBackend) {
      const field = platform === "instagram" ? "instaUrl" : "ytUrl";
      return http("POST", "/influencers/connect", { instaUrl: platform === "instagram" ? url : "", ytUrl: platform === "youtube" ? url : "" });
    }
    const db = load();
    const i = db.influencers.find(x => x.userId === userId);
    if (!i) return fail("Profile not found");
    if (platform === "instagram") i.instaUrl = url.trim();
    else if (platform === "youtube") i.ytUrl = url.trim();
    else return fail("Unknown platform");
    applySync(i); save(db); return ok(i);
  }
  async function disconnectSocial(userId, platform) {
    const db = load();
    const i = db.influencers.find(x => x.userId === userId);
    if (!i) return fail("Profile not found");
    if (platform === "instagram") { i.instaUrl = ""; i.instaFollowers = 0; i.instaTopReel = 0; i.engagement = 0; }
    else if (platform === "youtube") { i.ytUrl = ""; i.ytSubscribers = 0; i.ytTopViews = 0; }
    save(db); return ok(i);
  }
  // Re-fetch latest numbers from all connected accounts.
  async function uploadPicture(file) {
    const form = new FormData();
    form.append("file", file);
    if (state.useBackend) {
      const token = storage.get("plugg_token");
      const r = await fetch(state.baseURL + "/profile/picture", {
        method: "POST",
        headers: token ? { Authorization: "Bearer " + token } : {},
        body: form,
      });
      if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || "Upload failed"); }
      return r.json();
    }
    // localStorage fallback — store as data URL
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => resolve({ url: e.target.result });
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }
  async function syncStats(userId) {
    if (state.useBackend) return http("POST", "/influencers/sync");
    const db = load();
    const i = db.influencers.find(x => x.userId === userId);
    if (!i) return fail("Profile not found");
    if (!i.instaUrl && !i.ytUrl) return fail("Connect Instagram or YouTube first.");
    applySync(i); save(db); return ok(i);
  }
  async function updateBrand(userId, patch) {
    const db = load();
    const b = db.brands.find(x => x.userId === userId);
    if (!b) return fail("Profile not found");
    Object.assign(b, patch); save(db); return ok(b);
  }
  async function listInfluencers({ niche } = {}) {
    if (state.useBackend) {
      let list = await http("GET", "/influencers");
      if (niche && niche !== "all") list = list.filter(i => i.niche === niche);
      return list.map(i => ({ ...i, sub: subscriptionStatus(i) }));
    }
    const db = load();
    let list = db.influencers.slice();
    if (niche && niche !== "all") list = list.filter(i => i.niche === niche);
    return ok(list.map(i => ({ ...i, sub: subscriptionStatus(i) })));
  }

  // ============================================================
  //  PRODUCTS (campaigns)
  // ============================================================
  async function createProduct(brandUserId, data) {
    const db = load();
    const id = nextId(db);
    const brand = db.brands.find(b => b.userId === brandUserId);
    db.products.push({
      id, brandUserId, brandName: brand ? brand.company : "Brand",
      title: data.title, description: data.description, category: data.category || "General",
      budget: +data.budget || 0, deadline: data.deadline || "",
      deliverables: data.deliverables || "", status: "open", createdAt: new Date().toISOString(),
    });
    save(db); return ok(id);
  }
  async function listProducts({ category, brandUserId, status } = {}) {
    if (state.useBackend) {
      let list = await http("GET", "/products");
      if (category && category !== "all") list = list.filter(p => p.category === category);
      if (brandUserId) list = list.filter(p => p.brandUserId === brandUserId);
      if (status) list = list.filter(p => p.status === status);
      return list;
    }
    const db = load();
    let list = db.products.slice().sort((a, b) => b.id - a.id);
    if (category && category !== "all") list = list.filter(p => p.category === category);
    if (brandUserId) list = list.filter(p => p.brandUserId === brandUserId);
    if (status) list = list.filter(p => p.status === status);
    return ok(list.map(p => {
      const brand = db.brands.find(b => b.userId === p.brandUserId);
      return { ...p, brandLogo: brand ? brand.logo : "", bidCount: db.bids.filter(b => b.productId === p.id).length };
    }));
  }
  async function getProduct(id) {
    const db = load();
    const p = db.products.find(x => x.id === id);
    if (!p) return ok(null);
    const brand = db.brands.find(b => b.userId === p.brandUserId);
    return ok({ ...p, brandLogo: brand ? brand.logo : "" });
  }
  async function updateProduct(id, patch) {
    const db = load();
    const p = db.products.find(x => x.id === id);
    if (!p) return fail("Campaign not found");
    Object.assign(p, patch); save(db); return ok(p);
  }

  // ============================================================
  //  BIDS
  // ============================================================
  async function placeBid(productId, influencerUserId, { amount, message }) {
    const db = load();
    if (db.bids.find(b => b.productId === productId && b.influencerUserId === influencerUserId))
      return fail("You have already bid on this campaign.");
    const id = nextId(db);
    const inf = db.influencers.find(i => i.userId === influencerUserId);
    db.bids.push({
      id, productId, influencerUserId, influencerName: inf ? inf.name : "Influencer",
      amount: +amount, message: message || "", status: "pending", createdAt: new Date().toISOString(),
    });
    save(db); return ok(id);
  }
  async function bidsForProduct(productId) {
    const db = load();
    const bids = db.bids.filter(b => b.productId === productId).map(b => {
      const inf = db.influencers.find(i => i.userId === b.influencerUserId);
      return { ...b, influencer: inf ? { ...inf, sub: subscriptionStatus(inf) } : null };
    });
    return ok(bids);
  }
  async function myBids(influencerUserId) {
    const db = load();
    const bids = db.bids.filter(b => b.influencerUserId === influencerUserId).map(b => {
      const p = db.products.find(x => x.id === b.productId);
      const concept = db.concepts.find(c => c.bidId === b.id) || null;
      return { ...b, product: p || null, concept };
    });
    return ok(bids.sort((a, b) => b.id - a.id));
  }
  async function updateBidStatus(bidId, status) {
    const db = load();
    const bid = db.bids.find(b => b.id === bidId);
    if (!bid) return fail("Bid not found");
    bid.status = status;
    // When approved, brand pays commission to platform; campaign closes; other bids rejected.
    if (status === "approved") {
      const p = db.products.find(x => x.id === bid.productId);
      if (p) {
        p.status = "in_progress";
        db.bids.filter(b => b.productId === p.id && b.id !== bidId && b.status === "pending")
          .forEach(b => b.status = "rejected");
        const commission = Math.round(bid.amount * CONFIG.brandCommissionPct / 100);
        db.payments.push({
          id: nextId(db), type: "brand_commission", userId: p.brandUserId, refId: bid.id,
          gross: bid.amount, amount: commission, status: "paid", createdAt: new Date().toISOString(),
          note: `${CONFIG.brandCommissionPct}% platform commission on accepted bid`,
        });
      }
    }
    save(db); return ok(bid);
  }

  // ============================================================
  //  CONCEPTS (revealed to influencer only after approval)
  // ============================================================
  async function shareConcept(bidId, brandUserId, data) {
    const db = load();
    const bid = db.bids.find(b => b.id === bidId);
    if (!bid) return fail("Bid not found");
    if (bid.status !== "approved") return fail("Approve the bid before sharing the concept.");
    let c = db.concepts.find(x => x.bidId === bidId);
    if (c) { Object.assign(c, data); }
    else {
      c = { id: nextId(db), bidId, productId: bid.productId, brandUserId,
        influencerUserId: bid.influencerUserId, ...data, sharedAt: new Date().toISOString() };
      db.concepts.push(c);
    }
    save(db); return ok(c);
  }
  async function getConceptForBid(bidId) {
    const db = load();
    return ok(db.concepts.find(c => c.bidId === bidId) || null);
  }

  // ============================================================
  //  PAYMENTS & SUBSCRIPTIONS
  // ============================================================
  async function recordPayment(p) {
    const db = load();
    const id = nextId(db);
    db.payments.push({ id, status: "paid", createdAt: new Date().toISOString(), ...p });
    save(db); return ok(id);
  }
  async function subscribe(influencerUserId) {
    const db = load();
    const inf = db.influencers.find(i => i.userId === influencerUserId);
    if (!inf) return fail("Profile not found");
    const until = new Date(Date.now() + 30 * 86400000).toISOString();
    inf.plan = "pro"; inf.subscribedUntil = until;
    db.payments.push({
      id: nextId(db), type: "influencer_subscription", userId: influencerUserId,
      amount: CONFIG.subscriptionMonthly, status: "paid", createdAt: new Date().toISOString(),
      note: "Influencer Pro — monthly subscription",
    });
    save(db); return ok({ subscribedUntil: until });
  }
  async function paymentsFor(userId) {
    const db = load();
    return ok(db.payments.filter(p => p.userId === userId).sort((a, b) => b.id - a.id));
  }

  // ============================================================
  //  ADMIN
  // ============================================================
  async function adminRevenue() {
    const db = load();
    const sum = (arr) => arr.reduce((s, p) => s + (p.amount || 0), 0);
    const brandCom = db.payments.filter(p => p.type === "brand_commission");
    const subs = db.payments.filter(p => p.type === "influencer_subscription");
    const infCom = db.payments.filter(p => p.type === "influencer_commission");
    return ok({
      total: sum(db.payments),
      brandCommission: sum(brandCom),
      subscriptions: sum(subs),
      influencerCommission: sum(infCom),
      counts: {
        users: db.users.length,
        influencers: db.influencers.length,
        brands: db.brands.length,
        products: db.products.length,
        bids: db.bids.length,
        approved: db.bids.filter(b => b.status === "approved").length,
      },
      recent: db.payments.slice().sort((a, b) => b.id - a.id).slice(0, 12),
    });
  }
  // Public marketplace stats (for the landing page hero, etc.)
  async function platformStats() {
    if (state.useBackend) return http("GET", "/stats");
    const db = load();
    const approved = db.bids.filter(b => b.status === "approved");
    const delivered = approved.filter(a => db.concepts.find(c => c.bidId === a.id));
    return ok({
      creators: db.influencers.length,
      brands: db.brands.length,
      campaigns: db.products.length,
      bids: db.bids.length,
      approved: approved.length,
      // % of approved campaigns that have a brief shared (i.e. moving to delivery); 100% baseline
      delivery: approved.length ? Math.round((delivered.length / approved.length) * 100) : 100,
    });
  }
  async function allUsers() {
    const db = load();
    return ok(db.users.map(u => {
      const extra = u.role === "influencer"
        ? db.influencers.find(i => i.userId === u.id)
        : u.role === "brand" ? db.brands.find(b => b.userId === u.id) : null;
      const sub = u.role === "influencer" && extra ? subscriptionStatus(extra) : null;
      return { ...sanitize(u), extra, sub };
    }));
  }

  // ============================================================
  //  SEED (demo data) & RESET
  // ============================================================
  function rawDB() { return load(); }
  function writeDB(db) { save(db); }
  function reset() { storage.del(KEY); clearSession(); }
  function isSeeded() { return load().users.length > 0; }

  return {
    CONFIG, state,
    // auth
    register, login, logout, currentUser, sessionId,
    // profiles
    getInfluencer, getBrand, updateInfluencer, updateBrand, listInfluencers,
    connectSocial, disconnectSocial, syncStats, uploadPicture,
    // products
    createProduct, listProducts, getProduct, updateProduct,
    // bids
    placeBid, bidsForProduct, myBids, updateBidStatus,
    // concepts
    shareConcept, getConceptForBid,
    // payments
    recordPayment, subscribe, paymentsFor,
    // admin
    adminRevenue, allUsers, platformStats,
    // helpers
    subscriptionStatus, trialInfo,
    // db utils
    rawDB, writeDB, reset, isSeeded, nextId,
  };
})();

window.API = API;
