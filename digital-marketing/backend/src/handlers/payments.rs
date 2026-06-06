use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use chrono::{Duration, Utc};
use serde::Deserialize;
use serde_json::json;

use crate::{
    auth::extract_user,
    errors::{AppError, AppResult},
    models::Payment,
    AppState,
};

const PAY_COLS: &str =
    "id, type AS payment_type, user_id, ref_id, \
     CAST(gross AS FLOAT8) AS gross, CAST(amount AS FLOAT8) AS amount, \
     status, note, created_at";

#[derive(Deserialize)]
pub struct RecordPaymentRequest {
    pub r#type: String,
    pub ref_id: Option<i64>,
    pub gross: f64,
    pub amount: f64,
    pub note: Option<String>,
}

pub async fn record_payment(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(req): Json<RecordPaymentRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role == "admin" || user.role == "brand" || user.role == "influencer" {
        // allowed
    } else {
        return Err(AppError::forbidden("authenticated users only"));
    }

    let payment: Payment = sqlx::query_as::<_, Payment>(&format!(
        "INSERT INTO payments (type, user_id, ref_id, gross, amount, note) \
         VALUES ($1,$2,$3,$4,$5,$6) RETURNING {}",
        PAY_COLS
    ))
    .bind(&req.r#type)
    .bind(user.id)
    .bind(req.ref_id.unwrap_or(0))
    .bind(req.gross)
    .bind(req.amount)
    .bind(req.note.as_deref().unwrap_or(""))
    .fetch_one(&state.db)
    .await?;

    Ok((StatusCode::CREATED, Json(json!(payment))))
}

#[derive(Deserialize)]
pub struct SubscribeRequest {
    pub plan_type: Option<String>,
}

pub async fn subscribe(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(req): Json<SubscribeRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "influencer" {
        return Err(AppError::forbidden("influencers only"));
    }

    let subscribed_until = Utc::now() + Duration::days(30);
    sqlx::query(
        "UPDATE influencer_profiles \
         SET plan = 'pro', plan_type = $1, subscribed_until = $2 WHERE user_id = $3",
    )
    .bind(req.plan_type.as_deref().unwrap_or("subscription"))
    .bind(subscribed_until)
    .bind(user.id)
    .execute(&state.db)
    .await?;

    sqlx::query(
        "INSERT INTO payments (type, user_id, gross, amount, note) \
         VALUES ('influencer_subscription', $1, 1499, 1499, 'Creator Pro monthly subscription')",
    )
    .bind(user.id)
    .execute(&state.db)
    .await?;

    Ok(Json(json!({ "status": "subscribed", "plan": "pro" })))
}
