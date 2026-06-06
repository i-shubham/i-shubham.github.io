use axum::{
    extract::{Path, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde::Deserialize;
use serde_json::json;

use crate::{
    auth::extract_user,
    errors::{AppError, AppResult},
    models::{Bid, Concept, InfluencerProfile, User},
    AppState,
};

const BID_COLS: &str =
    "id, product_id, influencer_user_id, CAST(amount AS FLOAT8) AS amount, \
     message, status, created_at";

pub async fn list_bids(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(product_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    extract_user(&headers, &state.config.jwt_secret, &state.db).await?;

    let bids = sqlx::query_as::<_, Bid>(&format!(
        "SELECT {} FROM bids WHERE product_id = $1 ORDER BY created_at DESC",
        BID_COLS
    ))
    .bind(product_id)
    .fetch_all(&state.db)
    .await?;

    let mut result = Vec::with_capacity(bids.len());
    for b in &bids {
        let user: Option<User> = sqlx::query_as::<_, User>(
            "SELECT id, role, name, email, password_hash, created_at \
             FROM users WHERE id = $1",
        )
        .bind(b.influencer_user_id)
        .fetch_optional(&state.db)
        .await?;

        let profile: Option<InfluencerProfile> = sqlx::query_as::<_, InfluencerProfile>(
            "SELECT user_id, handle, niche, bio, location, avatar, insta_url, yt_url, \
             last_synced, insta_followers, insta_top_reel, yt_subscribers, yt_top_views, \
             CAST(engagement AS FLOAT8) AS engagement, trial_start, plan, plan_type, \
             subscribed_until FROM influencer_profiles WHERE user_id = $1",
        )
        .bind(b.influencer_user_id)
        .fetch_optional(&state.db)
        .await?;

        result.push(json!({
            "id": b.id,
            "product_id": b.product_id,
            "influencer_user_id": b.influencer_user_id,
            "amount": b.amount,
            "message": b.message,
            "status": b.status,
            "created_at": b.created_at,
            "influencer_name": user.as_ref().map(|u| u.name.as_str()).unwrap_or(""),
            "influencer_handle": profile.as_ref().and_then(|p| p.handle.as_deref()).unwrap_or(""),
            "influencer_avatar": profile.as_ref().and_then(|p| p.avatar.as_deref()).unwrap_or(""),
        }));
    }
    Ok(Json(result))
}

#[derive(Deserialize)]
pub struct PlaceBidRequest {
    pub amount: f64,
    pub message: Option<String>,
}

pub async fn place_bid(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(product_id): Path<i64>,
    Json(req): Json<PlaceBidRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "influencer" {
        return Err(AppError::forbidden("influencers only"));
    }

    // Duplicate bid check
    let existing: Option<Bid> = sqlx::query_as::<_, Bid>(&format!(
        "SELECT {} FROM bids WHERE product_id = $1 AND influencer_user_id = $2",
        BID_COLS
    ))
    .bind(product_id)
    .bind(user.id)
    .fetch_optional(&state.db)
    .await?;

    if existing.is_some() {
        return Err(AppError::conflict("you already placed a bid on this campaign"));
    }

    let bid = sqlx::query_as::<_, Bid>(&format!(
        "INSERT INTO bids (product_id, influencer_user_id, amount, message) \
         VALUES ($1,$2,$3,$4) RETURNING {}",
        BID_COLS
    ))
    .bind(product_id)
    .bind(user.id)
    .bind(req.amount)
    .bind(req.message.as_deref().unwrap_or(""))
    .fetch_one(&state.db)
    .await?;

    Ok((StatusCode::CREATED, Json(json!(bid))))
}

#[derive(Deserialize)]
pub struct UpdateBidRequest {
    pub status: String,
}

pub async fn update_bid_status(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(bid_id): Path<i64>,
    Json(req): Json<UpdateBidRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "brand" {
        return Err(AppError::forbidden("brands only"));
    }
    if req.status != "approved" && req.status != "rejected" {
        return Err(AppError::bad_request("status must be 'approved' or 'rejected'"));
    }

    let bid: Bid = sqlx::query_as::<_, Bid>(&format!(
        "SELECT {} FROM bids WHERE id = $1",
        BID_COLS
    ))
    .bind(bid_id)
    .fetch_optional(&state.db)
    .await?
    .ok_or_else(|| AppError::not_found("bid not found"))?;

    // Use a transaction for multi-step approval
    let mut tx = state.db.begin().await?;

    sqlx::query("UPDATE bids SET status = $1 WHERE id = $2")
        .bind(&req.status)
        .bind(bid_id)
        .execute(&mut *tx)
        .await?;

    if req.status == "approved" {
        // Reject all other pending bids on the same product
        sqlx::query(
            "UPDATE bids SET status = 'rejected' \
             WHERE product_id = $1 AND id != $2 AND status = 'pending'",
        )
        .bind(bid.product_id)
        .bind(bid_id)
        .execute(&mut *tx)
        .await?;

        // Mark product in_progress
        sqlx::query("UPDATE products SET status = 'in_progress' WHERE id = $1")
            .bind(bid.product_id)
            .execute(&mut *tx)
            .await?;

        // Record 10% brand commission
        let commission = bid.amount * 0.10;
        sqlx::query(
            "INSERT INTO payments (type, user_id, ref_id, gross, amount, note) \
             VALUES ('brand_commission', $1, $2, $3, $4, '10% platform commission on accepted bid')",
        )
        .bind(user.id)
        .bind(bid_id)
        .bind(bid.amount)
        .bind(commission)
        .execute(&mut *tx)
        .await?;
    }

    tx.commit().await?;

    Ok(Json(json!({ "status": req.status })))
}

#[derive(Deserialize)]
pub struct ShareConceptRequest {
    pub concept: Option<String>,
    pub script: Option<String>,
    pub deliverables: Option<String>,
    pub deadline: Option<String>,
}

pub async fn share_concept(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(bid_id): Path<i64>,
    Json(req): Json<ShareConceptRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "brand" {
        return Err(AppError::forbidden("brands only"));
    }

    let bid: Bid = sqlx::query_as::<_, Bid>(&format!(
        "SELECT {} FROM bids WHERE id = $1",
        BID_COLS
    ))
    .bind(bid_id)
    .fetch_optional(&state.db)
    .await?
    .ok_or_else(|| AppError::not_found("bid not found"))?;

    let concept: Concept = sqlx::query_as::<_, Concept>(
        "INSERT INTO concepts \
         (bid_id, product_id, brand_user_id, influencer_user_id, concept, script, deliverables, deadline) \
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8) \
         RETURNING id, bid_id, product_id, brand_user_id, influencer_user_id, \
                   concept, script, deliverables, deadline, shared_at",
    )
    .bind(bid_id)
    .bind(bid.product_id)
    .bind(user.id)
    .bind(bid.influencer_user_id)
    .bind(req.concept.as_deref().unwrap_or(""))
    .bind(req.script.as_deref().unwrap_or(""))
    .bind(req.deliverables.as_deref().unwrap_or(""))
    .bind(req.deadline.as_deref().unwrap_or(""))
    .fetch_one(&state.db)
    .await?;

    Ok((StatusCode::CREATED, Json(json!(concept))))
}

pub async fn get_concept(
    State(state): State<AppState>,
    headers: HeaderMap,
    Path(bid_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    extract_user(&headers, &state.config.jwt_secret, &state.db).await?;

    let concept: Concept = sqlx::query_as::<_, Concept>(
        "SELECT id, bid_id, product_id, brand_user_id, influencer_user_id, \
         concept, script, deliverables, deadline, shared_at \
         FROM concepts WHERE bid_id = $1",
    )
    .bind(bid_id)
    .fetch_optional(&state.db)
    .await?
    .ok_or_else(|| AppError::not_found("concept not found"))?;

    Ok(Json(json!(concept)))
}
