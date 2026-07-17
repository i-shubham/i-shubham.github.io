use axum::{extract::State, http::HeaderMap, response::IntoResponse, Json};
use serde_json::json;

use crate::{
    auth::extract_user,
    errors::AppResult,
    models::{BrandProfile, InfluencerProfile},
    AppState,
};

pub async fn me(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;

    let mut resp = json!({
        "user": {
            "id": user.id,
            "role": user.role,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
        }
    });

    if user.role == "influencer" {
        let p: Option<InfluencerProfile> = sqlx::query_as::<_, InfluencerProfile>(
            "SELECT user_id, handle, niche, bio, location, avatar, insta_url, yt_url, \
             last_synced, insta_followers, insta_top_reel, yt_subscribers, yt_top_views, \
             CAST(engagement AS FLOAT8) AS engagement, trial_start, plan, plan_type, \
             subscribed_until FROM influencer_profiles WHERE user_id = $1",
        )
        .bind(user.id)
        .fetch_optional(&state.db)
        .await?;

        if let Some(p) = p {
            resp["profile"] = json!(p);
        }
    } else if user.role == "brand" {
        let p: Option<BrandProfile> = sqlx::query_as::<_, BrandProfile>(
            "SELECT user_id, company, industry, website, about, logo \
             FROM brand_profiles WHERE user_id = $1",
        )
        .bind(user.id)
        .fetch_optional(&state.db)
        .await?;

        if let Some(p) = p {
            resp["profile"] = json!(p);
        }
    }

    Ok(Json(resp))
}
