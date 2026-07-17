use chrono::{DateTime, Utc};
use serde::Serialize;
use sqlx::FromRow;

/// All NUMERIC(x,y) columns are queried with CAST(col AS FLOAT8) AS col.
/// The `type` column in payments is aliased to `payment_type` in every query.

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct User {
    pub id: i64,
    pub role: String,
    pub name: String,
    pub email: String,
    pub password_hash: String,
    pub created_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct InfluencerProfile {
    pub user_id: i64,
    pub handle: Option<String>,
    pub niche: Option<String>,
    pub bio: Option<String>,
    pub location: Option<String>,
    pub avatar: Option<String>,
    pub insta_url: Option<String>,
    pub yt_url: Option<String>,
    pub last_synced: Option<DateTime<Utc>>,
    pub insta_followers: Option<i32>,
    pub insta_top_reel: Option<i32>,
    pub yt_subscribers: Option<i32>,
    pub yt_top_views: Option<i32>,
    pub engagement: Option<f64>,        // CAST(engagement AS FLOAT8)
    pub trial_start: Option<DateTime<Utc>>,
    pub plan: Option<String>,
    pub plan_type: Option<String>,
    pub subscribed_until: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct BrandProfile {
    pub user_id: i64,
    pub company: String,
    pub industry: Option<String>,
    pub website: Option<String>,
    pub about: Option<String>,
    pub logo: Option<String>,
}

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct Product {
    pub id: i64,
    pub brand_user_id: i64,
    pub title: String,
    pub description: Option<String>,
    pub category: Option<String>,
    pub budget: f64,                    // CAST(budget AS FLOAT8)
    pub deadline: Option<String>,
    pub deliverables: Option<String>,
    pub status: String,
    pub created_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct Bid {
    pub id: i64,
    pub product_id: i64,
    pub influencer_user_id: i64,
    pub amount: f64,                    // CAST(amount AS FLOAT8)
    pub message: Option<String>,
    pub status: String,
    pub created_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct Concept {
    pub id: i64,
    pub bid_id: i64,
    pub product_id: i64,
    pub brand_user_id: i64,
    pub influencer_user_id: i64,
    pub concept: Option<String>,
    pub script: Option<String>,
    pub deliverables: Option<String>,
    pub deadline: Option<String>,
    pub shared_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, FromRow)]
pub struct Payment {
    pub id: i64,
    /// Aliased from the `type` column (reserved keyword in Rust).
    pub payment_type: String,
    pub user_id: i64,
    pub ref_id: Option<i64>,
    pub gross: f64,                     // CAST(gross AS FLOAT8)
    pub amount: f64,                    // CAST(amount AS FLOAT8)
    pub status: String,
    pub note: Option<String>,
    pub created_at: Option<DateTime<Utc>>,
}
