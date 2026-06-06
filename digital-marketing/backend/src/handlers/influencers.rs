use axum::{extract::State, http::HeaderMap, response::IntoResponse, Json};
use serde::Deserialize;
use serde_json::json;

use crate::{
    auth::extract_user,
    errors::{AppError, AppResult},
    models::{InfluencerProfile, User},
    AppState,
};

// ── FNV-1a 32-bit hash (mirrors the Python _str_hash) ────────────────────────

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

fn derive_engagement(insta_url: &str, yt_url: &str) -> f64 {
    let combined = format!("{}{}", insta_url, yt_url);
    let h = str_hash(&combined);
    let raw = 3.0 + (h % 50) as f64 / 10.0;
    (raw * 10.0).round() / 10.0
}

const INF_COLS: &str =
    "user_id, handle, niche, bio, location, avatar, insta_url, yt_url, last_synced, \
     insta_followers, insta_top_reel, yt_subscribers, yt_top_views, \
     CAST(engagement AS FLOAT8) AS engagement, trial_start, plan, plan_type, subscribed_until";

// ── Handlers ──────────────────────────────────────────────────────────────────

pub async fn list_influencers(State(state): State<AppState>) -> AppResult<impl IntoResponse> {
    let profiles = sqlx::query_as::<_, InfluencerProfile>(&format!(
        "SELECT {} FROM influencer_profiles ORDER BY insta_followers DESC",
        INF_COLS
    ))
    .fetch_all(&state.db)
    .await?;

    let mut result = Vec::with_capacity(profiles.len());
    for p in &profiles {
        let user: Option<User> = sqlx::query_as::<_, User>(
            "SELECT id, role, name, email, password_hash, created_at \
             FROM users WHERE id = $1",
        )
        .bind(p.user_id)
        .fetch_optional(&state.db)
        .await?;

        result.push(json!({
            "userId":         p.user_id,
            "handle":         p.handle,
            "niche":          p.niche,
            "bio":            p.bio,
            "location":       p.location,
            "avatar":         p.avatar,
            "instaUrl":       p.insta_url,
            "ytUrl":          p.yt_url,
            "lastSynced":     p.last_synced,
            "instaFollowers": p.insta_followers.unwrap_or(0),
            "instaTopReel":   p.insta_top_reel.unwrap_or(0),
            "ytSubscribers":  p.yt_subscribers.unwrap_or(0),
            "ytTopViews":     p.yt_top_views.unwrap_or(0),
            "engagement":     p.engagement.unwrap_or(0.0),
            "trialStart":     p.trial_start,
            "plan":           p.plan,
            "planType":       p.plan_type,
            "subscribedUntil":p.subscribed_until,
            "name":           user.as_ref().map(|u| u.name.as_str()).unwrap_or(""),
        }));
    }
    Ok(Json(result))
}

#[derive(Deserialize)]
pub struct ConnectSocialRequest {
    pub insta_url: Option<String>,
    pub yt_url: Option<String>,
}

pub async fn connect_social(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(req): Json<ConnectSocialRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "influencer" {
        return Err(AppError::forbidden("influencers only"));
    }

    // Fetch current URLs so we can preserve whichever isn't being updated
    let current: InfluencerProfile = sqlx::query_as::<_, InfluencerProfile>(&format!(
        "SELECT {} FROM influencer_profiles WHERE user_id = $1",
        INF_COLS
    ))
    .bind(user.id)
    .fetch_optional(&state.db)
    .await?
    .ok_or_else(|| AppError::not_found("influencer profile not found"))?;

    let insta_url = req
        .insta_url
        .as_deref()
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
        .unwrap_or_else(|| current.insta_url.clone().unwrap_or_default());

    let yt_url = req
        .yt_url
        .as_deref()
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
        .unwrap_or_else(|| current.yt_url.clone().unwrap_or_default());

    let (insta_followers, insta_top_reel) = derive_insta(&insta_url);
    let (yt_subscribers, yt_top_views) = derive_yt(&yt_url);
    let engagement = derive_engagement(&insta_url, &yt_url);

    sqlx::query(
        "UPDATE influencer_profiles \
         SET insta_url = $1, yt_url = $2, insta_followers = $3, insta_top_reel = $4, \
             yt_subscribers = $5, yt_top_views = $6, engagement = $7, last_synced = NOW() \
         WHERE user_id = $8",
    )
    .bind(&insta_url)
    .bind(&yt_url)
    .bind(insta_followers)
    .bind(insta_top_reel)
    .bind(yt_subscribers)
    .bind(yt_top_views)
    .bind(engagement)
    .bind(user.id)
    .execute(&state.db)
    .await?;

    Ok(Json(json!({
        "status": "connected",
        "instaFollowers": insta_followers,
        "ytSubscribers": yt_subscribers,
        "engagement": engagement,
    })))
}

pub async fn sync_stats(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "influencer" {
        return Err(AppError::forbidden("influencers only"));
    }

    let current: InfluencerProfile = sqlx::query_as::<_, InfluencerProfile>(&format!(
        "SELECT {} FROM influencer_profiles WHERE user_id = $1",
        INF_COLS
    ))
    .bind(user.id)
    .fetch_optional(&state.db)
    .await?
    .ok_or_else(|| AppError::not_found("influencer profile not found"))?;

    let insta_url = current.insta_url.as_deref().unwrap_or("");
    let yt_url = current.yt_url.as_deref().unwrap_or("");

    let (insta_followers, insta_top_reel) = derive_insta(insta_url);
    let (yt_subscribers, yt_top_views) = derive_yt(yt_url);
    let engagement = derive_engagement(insta_url, yt_url);

    sqlx::query(
        "UPDATE influencer_profiles \
         SET insta_followers = $1, insta_top_reel = $2, yt_subscribers = $3, \
             yt_top_views = $4, engagement = $5, last_synced = NOW() \
         WHERE user_id = $6",
    )
    .bind(insta_followers)
    .bind(insta_top_reel)
    .bind(yt_subscribers)
    .bind(yt_top_views)
    .bind(engagement)
    .bind(user.id)
    .execute(&state.db)
    .await?;

    Ok(Json(json!({
        "instaFollowers": insta_followers,
        "ytSubscribers": yt_subscribers,
        "engagement": engagement,
    })))
}
