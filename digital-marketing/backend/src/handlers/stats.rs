use axum::{extract::State, response::IntoResponse, Json};
use serde_json::json;

use crate::{errors::AppResult, AppState};

#[derive(sqlx::FromRow)]
struct CountRow {
    cnt: i64,
}

async fn count(db: &sqlx::PgPool, sql: &str) -> Result<i64, sqlx::Error> {
    let row: CountRow = sqlx::query_as(sql).fetch_one(db).await?;
    Ok(row.cnt)
}

pub async fn public_stats(State(state): State<AppState>) -> AppResult<impl IntoResponse> {
    let creators =
        count(&state.db, "SELECT COUNT(*) AS cnt FROM users WHERE role='influencer'").await?;
    let brands =
        count(&state.db, "SELECT COUNT(*) AS cnt FROM users WHERE role='brand'").await?;
    let campaigns = count(&state.db, "SELECT COUNT(*) AS cnt FROM products").await?;
    let bids = count(&state.db, "SELECT COUNT(*) AS cnt FROM bids").await?;
    let approved =
        count(&state.db, "SELECT COUNT(*) AS cnt FROM bids WHERE status='approved'").await?;
    let delivered = count(&state.db, "SELECT COUNT(*) AS cnt FROM concepts").await?;

    let delivery = if approved > 0 {
        ((delivered as f64 / approved as f64) * 100.0).round() as i64
    } else {
        100
    };

    Ok(Json(json!({
        "creators": creators,
        "brands": brands,
        "campaigns": campaigns,
        "bids": bids,
        "approved": approved,
        "delivery": delivery,
    })))
}
