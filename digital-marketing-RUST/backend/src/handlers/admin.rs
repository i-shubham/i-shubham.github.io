use axum::{extract::State, http::HeaderMap, response::IntoResponse, Json};
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

#[derive(sqlx::FromRow)]
struct SumRow {
    val: f64,
}

async fn sum_type(db: &sqlx::PgPool, payment_type: &str) -> Result<f64, sqlx::Error> {
    let row: SumRow = sqlx::query_as(
        "SELECT COALESCE(SUM(CAST(amount AS FLOAT8)), 0.0) AS val \
         FROM payments WHERE type = $1 AND status = 'completed'",
    )
    .bind(payment_type)
    .fetch_one(db)
    .await?;
    Ok(row.val)
}

pub async fn revenue(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "admin" {
        return Err(AppError::forbidden("admins only"));
    }

    let brand_commissions = sum_type(&state.db, "brand_commission")
        .await
        .map_err(AppError::from)?;
    let influencer_subscriptions = sum_type(&state.db, "influencer_subscription")
        .await
        .map_err(AppError::from)?;
    let influencer_commissions = sum_type(&state.db, "influencer_commission")
        .await
        .map_err(AppError::from)?;

    let total = brand_commissions + influencer_subscriptions + influencer_commissions;

    let recent: Vec<Payment> = sqlx::query_as::<_, Payment>(&format!(
        "SELECT {} FROM payments ORDER BY created_at DESC LIMIT 20",
        PAY_COLS
    ))
    .fetch_all(&state.db)
    .await?;

    Ok(Json(json!({
        "brand_commissions": brand_commissions,
        "influencer_subscriptions": influencer_subscriptions,
        "influencer_commissions": influencer_commissions,
        "total_revenue": total,
        "recent_payments": recent,
    })))
}
