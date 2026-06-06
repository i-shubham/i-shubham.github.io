/* ============================================================
   Plugg — Demo seed data
   Populates a realistic marketplace on first visit so the static
   demo feels alive. Safe to remove once the Go backend is live.
   ============================================================ */
(function seed() {
  if (API.state.useBackend) return;
  if (API.isSeeded()) return;
  const db = API.rawDB();
  const now = Date.now();
  const iso = (daysAgo) => new Date(now - daysAgo * 86400000).toISOString();
  const id = () => API.nextId(db);

  function addUser(role, name, email, password) {
    const uid = id();
    db.users.push({ id: uid, role, name, email, password, createdAt: iso(40) });
    return uid;
  }

  // --- Admin ---
  addUser("admin", "Platform Admin", "admin@plugg.io", "admin123");

  // --- Influencers ---
  const influencers = [
    { name: "Aarav Mehta", handle: "aaravcreates", niche: "Tech", bio: "Gadget reviews & unboxings. Honest takes, crisp edits.", instaFollowers: 285000, instaTopReel: 1900000, ytSubscribers: 540000, ytTopViews: 3200000, engagement: 6.4, location: "Bengaluru", trialDaysAgo: 5, plan: "trial" },
    { name: "Diya Kapoor", handle: "diyaeats", niche: "Food", bio: "Street food + home recipes. Reels that make you hungry.", instaFollowers: 520000, instaTopReel: 4200000, ytSubscribers: 210000, ytTopViews: 1500000, engagement: 8.1, location: "Mumbai", trialDaysAgo: 45, plan: "pro" },
    { name: "Kabir Singh", handle: "kabirfit", niche: "Fitness", bio: "Home workouts, no-equipment routines, nutrition tips.", instaFollowers: 340000, instaTopReel: 2700000, ytSubscribers: 380000, ytTopViews: 2100000, engagement: 7.2, location: "Delhi", trialDaysAgo: 12, plan: "trial" },
    { name: "Sara Khan", handle: "sarastyle", niche: "Fashion", bio: "Affordable styling, GRWM, thrift hauls.", instaFollowers: 760000, instaTopReel: 5600000, ytSubscribers: 120000, ytTopViews: 980000, engagement: 9.0, location: "Pune", trialDaysAgo: 60, plan: "pro" },
    { name: "Rohan Das", handle: "rohantravels", niche: "Travel", bio: "Budget travel across India. Cinematic vlogs.", instaFollowers: 198000, instaTopReel: 1400000, ytSubscribers: 460000, ytTopViews: 2800000, engagement: 5.8, location: "Goa", trialDaysAgo: 2, plan: "trial" },
    { name: "Ishita Rao", handle: "ishitabeauty", niche: "Beauty", bio: "Skincare science + makeup tutorials.", instaFollowers: 430000, instaTopReel: 3100000, ytSubscribers: 290000, ytTopViews: 1700000, engagement: 7.7, location: "Hyderabad", trialDaysAgo: 20, plan: "trial" },
  ];
  const avatarByHandle = {
    aaravcreates: "img/influencers/inf-aarav.png", diyaeats: "img/influencers/inf-diya.png", kabirfit: "img/influencers/inf-kabir.png",
    sarastyle: "img/influencers/inf-sara.png", rohantravels: "img/influencers/inf-rohan.png", ishitabeauty: "img/influencers/inf-ishita.png",
  };
  const infIds = {};
  influencers.forEach(f => {
    const uid = addUser("influencer", f.name, f.handle + "@demo.io", "demo123");
    infIds[f.handle] = uid;
    db.influencers.push({
      userId: uid, name: f.name, handle: f.handle, niche: f.niche, bio: f.bio,
      avatar: avatarByHandle[f.handle] || "",
      instaUrl: "https://instagram.com/" + f.handle, ytUrl: "https://youtube.com/@" + f.handle,
      instaFollowers: f.instaFollowers, instaTopReel: f.instaTopReel,
      ytSubscribers: f.ytSubscribers, ytTopViews: f.ytTopViews, engagement: f.engagement,
      lastSynced: iso(1), location: f.location, trialStart: iso(f.trialDaysAgo), plan: f.plan,
      subscribedUntil: f.plan === "pro" ? iso(-25) : null, planType: "subscription",
    });
  });

  // --- Brands ---
  const brands = [
    { name: "Nimbus Audio", company: "Nimbus Audio", industry: "Electronics", website: "nimbusaudio.com", about: "Premium wireless audio for creators.", logo: "img/brands/brand-nimbus.png" },
    { name: "GreenLeaf Nutrition", company: "GreenLeaf Nutrition", industry: "Health", website: "greenleaf.in", about: "Plant-based supplements & superfoods.", logo: "img/brands/brand-greenleaf.png" },
    { name: "Lumio Cosmetics", company: "Lumio Cosmetics", industry: "Beauty", website: "lumio.co", about: "Clean, cruelty-free beauty.", logo: "img/brands/brand-lumio.png" },
  ];
  const brandIds = {};
  brands.forEach(b => {
    const uid = addUser("brand", b.name, b.company.replace(/\s+/g, "").toLowerCase() + "@demo.io", "demo123");
    brandIds[b.company] = uid;
    db.brands.push({ userId: uid, company: b.company, industry: b.industry, website: b.website, about: b.about, logo: b.logo || "" });
  });

  // --- Products / campaigns ---
  function addProduct(brandCompany, p) {
    const pid = id();
    db.products.push({
      id: pid, brandUserId: brandIds[brandCompany], brandName: brandCompany,
      title: p.title, description: p.description, category: p.category, budget: p.budget,
      deadline: p.deadline, deliverables: p.deliverables, status: p.status || "open", createdAt: iso(p.ago || 3),
    });
    return pid;
  }
  const p1 = addProduct("Nimbus Audio", { title: "Nimbus Pods Pro — Launch Reel", category: "Tech", budget: 45000, deadline: "2026-07-15", deliverables: "1 Instagram Reel (30s) + 3 stories", description: "Showcase our new ANC earbuds. Highlight battery life, sound quality and the matte finish. Looking for authentic, energetic reviewers.", ago: 4 });
  const p2 = addProduct("GreenLeaf Nutrition", { title: "Plant Protein 30-Day Challenge", category: "Fitness", budget: 60000, deadline: "2026-08-01", deliverables: "1 YouTube integration (60s) + 1 Reel", description: "Document a 30-day journey using our plant protein. Honest results, recipes, and a discount code for your audience.", ago: 2 });
  const p3 = addProduct("Lumio Cosmetics", { title: "Glow Serum — GRWM Feature", category: "Beauty", budget: 35000, deadline: "2026-07-20", deliverables: "1 Reel (GRWM) + 2 stories", description: "Feature our vitamin-C glow serum in a get-ready-with-me. Soft, aesthetic, morning-routine vibe.", ago: 6 });
  addProduct("Nimbus Audio", { title: "Studio Mic — Creator Setup Tour", category: "Tech", budget: 28000, deadline: "2026-08-10", deliverables: "1 YouTube short + 1 Reel", description: "Include our USB studio mic in your desk/setup tour. Emphasise plug-and-play simplicity.", ago: 1 });

  // --- Bids ---
  function addBid(pid, handle, amount, message, status) {
    const bid = { id: id(), productId: pid, influencerUserId: infIds[handle], influencerName: influencers.find(i => i.handle === handle).name, amount, message, status: status || "pending", createdAt: iso(1) };
    db.bids.push(bid); return bid;
  }
  addBid(p1, "aaravcreates", 42000, "Tech is my core niche — my last earbud review hit 1.9M views. Can deliver in 7 days.", "pending");
  addBid(p1, "kabirfit", 38000, "Active lifestyle audience, great for ANC + workout angle.", "pending");
  addBid(p2, "kabirfit", 58000, "Perfect fit — I run fitness challenges regularly. High completion + engagement.", "pending");
  addBid(p2, "diyaeats", 55000, "I can blend protein into recipes for a unique food x fitness crossover.", "pending");
  addBid(p3, "sarastyle", 33000, "GRWM is my signature format. Aesthetic guaranteed.", "pending");
  addBid(p3, "ishitabeauty", 34000, "Skincare-first beauty creator, ideal for a serum feature.", "pending");

  API.writeDB(db);
})();
