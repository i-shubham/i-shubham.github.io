//! Seed demo data into PostgreSQL.
//! Usage:  cargo run --bin seed
use std::env;

use chrono::Utc;
use sqlx::PgPool;

// ── FNV-1a 32-bit (same as influencers handler) ──────────────────────────────

fn str_hash(s: &str) -> u32 {
    let mut h: u32 = 2_166_136_261;
    for b in s.bytes() {
        h ^= b as u32;
        h = h.wrapping_mul(16_777_619);
    }
    h
}

fn derive_insta(url: &str) -> (i32, i32) {
    if url.is_empty() {
        return (0, 0);
    }
    let h = str_hash(url);
    (50_000 + (h % 950_000) as i32, 100_000 + (h % 5_000_000) as i32)
}

fn derive_yt(url: &str) -> (i32, i32) {
    if url.is_empty() {
        return (0, 0);
    }
    let h = str_hash(url);
    (10_000 + (h % 490_000) as i32, 50_000 + (h % 3_000_000) as i32)
}

fn derive_engagement(insta: &str, yt: &str) -> f64 {
    let combined = format!("{}{}", insta, yt);
    let h = str_hash(&combined);
    let raw = 3.0 + (h % 50) as f64 / 10.0;
    (raw * 10.0).round() / 10.0
}

fn hash_pw(pw: &str) -> String {
    bcrypt::hash(pw, bcrypt::DEFAULT_COST).expect("bcrypt failed")
}

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();
    let db_url = env::var("DATABASE_URL").expect("DATABASE_URL not set");
    let pool = PgPool::connect(&db_url).await.expect("DB connect failed");

    // Guard: skip if data already exists
    let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
        .fetch_one(&pool)
        .await
        .expect("count query failed");
    if count.0 > 0 {
        println!("Database already has {} user(s) — skipping seed.", count.0);
        println!("Run  make reset-db  first to re-seed.");
        return;
    }

    // ── Admin ─────────────────────────────────────────────────────────────────
    let admin: (i64,) = sqlx::query_as(
        "INSERT INTO users (role, name, email, password_hash) \
         VALUES ('admin','Plugg Admin','admin@plugg.io',$1) RETURNING id",
    )
    .bind(hash_pw("admin123"))
    .fetch_one(&pool)
    .await
    .expect("admin insert");
    println!("Created admin id={}", admin.0);

    // ── Influencers ───────────────────────────────────────────────────────────
    let influencers = vec![
        ("Aarav Creates",  "aaravcreates@demo.io", "aaravcreates", "Tech",
         "https://instagram.com/aaravcreates", "https://youtube.com/@aaravcreates",
         "img/influencers/inf-aarav.png"),
        ("Diya Fashions",  "diyafashions@demo.io", "diyafashions", "Fashion",
         "https://instagram.com/diyafashions", "https://youtube.com/@diyafashion",
         "img/influencers/inf-diya.png"),
        ("Rohan Fitness",  "rohanfit@demo.io",     "rohanfit",     "Fitness",
         "https://instagram.com/rohanfit",     "",
         "img/influencers/inf-rohan.png"),
        ("Ishita Travels", "ishitatravels@demo.io","ishitatravels","Travel",
         "https://instagram.com/ishitatravels","https://youtube.com/@ishitatravels",
         "img/influencers/inf-ishita.png"),
        ("Kabir Vlogs",    "kabirvlogs@demo.io",   "kabirvlogs",   "Lifestyle",
         "https://instagram.com/kabirvlogs",   "https://youtube.com/@kabirvlogs",
         "img/influencers/inf-kabir.png"),
    ];

    let mut inf_ids: Vec<i64> = Vec::new();
    for (name, email, handle, niche, insta, yt, avatar) in &influencers {
        let (uid,): (i64,) = sqlx::query_as(
            "INSERT INTO users (role, name, email, password_hash) \
             VALUES ('influencer',$1,$2,$3) RETURNING id",
        )
        .bind(name)
        .bind(email)
        .bind(hash_pw("demo123"))
        .fetch_one(&pool)
        .await
        .expect("influencer user insert");

        let (inf_fol, inf_reel) = derive_insta(insta);
        let (yt_sub, yt_view)   = derive_yt(yt);
        let eng                 = derive_engagement(insta, yt);

        sqlx::query(
            "INSERT INTO influencer_profiles \
             (user_id, handle, niche, avatar, insta_url, yt_url, \
              insta_followers, insta_top_reel, yt_subscribers, yt_top_views, \
              engagement, last_synced) \
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
        )
        .bind(uid).bind(handle).bind(niche).bind(avatar)
        .bind(insta).bind(yt)
        .bind(inf_fol).bind(inf_reel).bind(yt_sub).bind(yt_view)
        .bind(eng).bind(Utc::now())
        .execute(&pool)
        .await
        .expect("influencer profile insert");

        println!("Created influencer id={uid} {name} (@{handle})");
        inf_ids.push(uid);
    }

    // ── Brands ────────────────────────────────────────────────────────────────
    let brands = vec![
        ("Nimbus Audio",      "nimbusaudio@demo.io",  "Nimbus Audio",
         "Electronics",     "https://nimbusaudio.com",         "img/brands/brand-nimbus.png"),
        ("GreenLeaf Organics","greenleaf@demo.io",    "GreenLeaf Organics",
         "Health & Beauty",  "https://greenleaforganics.in",    "img/brands/brand-greenleaf.png"),
        ("Lumio Tech",        "lumio@demo.io",        "Lumio Tech",
         "Fashion",          "https://lumio.co",                "img/brands/brand-lumio.png"),
    ];

    let mut brand_ids: Vec<i64> = Vec::new();
    for (name, email, company, industry, website, logo) in &brands {
        let (uid,): (i64,) = sqlx::query_as(
            "INSERT INTO users (role, name, email, password_hash) \
             VALUES ('brand',$1,$2,$3) RETURNING id",
        )
        .bind(name)
        .bind(email)
        .bind(hash_pw("demo123"))
        .fetch_one(&pool)
        .await
        .expect("brand user insert");

        sqlx::query(
            "INSERT INTO brand_profiles (user_id, company, industry, website, logo) \
             VALUES ($1,$2,$3,$4,$5)",
        )
        .bind(uid).bind(company).bind(industry).bind(website).bind(logo)
        .execute(&pool)
        .await
        .expect("brand profile insert");

        println!("Created brand id={uid} {company}");
        brand_ids.push(uid);
    }

    let nimbus_id    = brand_ids[0];
    let greenleaf_id = brand_ids[1];
    let aarav_id     = inf_ids[0];
    let diya_id      = inf_ids[1];

    // ── Products ──────────────────────────────────────────────────────────────
    let (p1,): (i64,) = sqlx::query_as(
        "INSERT INTO products (brand_user_id, title, description, category, budget, deadline, deliverables) \
         VALUES ($1,'Wireless Earbuds Launch','Promote our new ANC earbuds with an unboxing + review reel',\
                 'Tech',25000,'2025-02-28','1 Reel (60s) + 3 Stories') RETURNING id",
    )
    .bind(nimbus_id)
    .fetch_one(&pool).await.expect("product 1");
    println!("Created product id={p1} Wireless Earbuds Launch");

    let (p2,): (i64,) = sqlx::query_as(
        "INSERT INTO products (brand_user_id, title, description, category, budget, deadline, deliverables) \
         VALUES ($1,'Podcast Mic Campaign','Showcase our USB-C podcast microphone for creators',\
                 'Tech',40000,'2025-03-15','1 YouTube video (8-12 min)') RETURNING id",
    )
    .bind(nimbus_id)
    .fetch_one(&pool).await.expect("product 2");
    println!("Created product id={p2} Podcast Mic Campaign");

    let (p3,): (i64,) = sqlx::query_as(
        "INSERT INTO products (brand_user_id, title, description, category, budget, deadline, deliverables) \
         VALUES ($1,'Organic Skincare Range','Feature our new turmeric face serum in a morning routine video',\
                 'Beauty',18000,'2025-02-20','1 Reel + 1 Story with swipe-up link') RETURNING id",
    )
    .bind(greenleaf_id)
    .fetch_one(&pool).await.expect("product 3");
    println!("Created product id={p3} Organic Skincare Range");

    let (p4,): (i64,) = sqlx::query_as(
        "INSERT INTO products (brand_user_id, title, description, category, budget, deadline, deliverables) \
         VALUES ($1,'Protein Bar Launch','Taste-test & review our new vegan protein bars',\
                 'Food',12000,'2025-03-01','1 YouTube Short + 2 Stories') RETURNING id",
    )
    .bind(greenleaf_id)
    .fetch_one(&pool).await.expect("product 4");
    println!("Created product id={p4} Protein Bar Launch");

    // ── Bids ──────────────────────────────────────────────────────────────────
    let bids_data = vec![
        (p1, aarav_id, 20000.0_f64, "My audience is very tech-savvy. Last earbud review hit 1.4M views!"),
        (p1, diya_id,  22000.0_f64, "I can create a lifestyle + unboxing aesthetic reel."),
        (p3, diya_id,  15000.0_f64, "Skincare content is my forte — high engagement on beauty reels!"),
    ];
    for (pid, iid, amount, msg) in &bids_data {
        let (bid_id,): (i64,) = sqlx::query_as(
            "INSERT INTO bids (product_id, influencer_user_id, amount, message) \
             VALUES ($1,$2,$3,$4) RETURNING id",
        )
        .bind(pid).bind(iid).bind(amount).bind(msg)
        .fetch_one(&pool).await.expect("bid insert");
        println!("Created bid id={bid_id} on product {pid}");
    }

    println!("\nSeed complete! Demo credentials:");
    println!("  influencer  aaravcreates@demo.io / demo123");
    println!("  brand       nimbusaudio@demo.io  / demo123");
    println!("  admin       admin@plugg.io        / admin123");
}
