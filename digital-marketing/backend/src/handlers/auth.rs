use axum::{extract::State, http::StatusCode, response::IntoResponse, Json};
use serde::Deserialize;
use serde_json::json;

use crate::{
    auth::{create_token, hash_pw, verify_pw},
    errors::{AppError, AppResult},
    models::User,
    AppState,
};

#[derive(Deserialize)]
pub struct RegisterRequest {
    pub role: String,
    pub name: String,
    pub email: String,
    pub password: String,
    // influencer optional fields
    pub handle: Option<String>,
    pub niche: Option<String>,
    pub insta_url: Option<String>,
    pub yt_url: Option<String>,
    pub bio: Option<String>,
    pub location: Option<String>,
    // brand optional fields
    pub company: Option<String>,
    pub industry: Option<String>,
    pub website: Option<String>,
}

#[derive(Deserialize)]
pub struct LoginRequest {
    pub email: String,
    pub password: String,
}

fn user_json(u: &User) -> serde_json::Value {
    json!({
        "id": u.id,
        "role": u.role,
        "name": u.name,
        "email": u.email,
        "created_at": u.created_at,
    })
}

pub async fn register(
    State(state): State<AppState>,
    Json(req): Json<RegisterRequest>,
) -> AppResult<impl IntoResponse> {
    if req.role != "influencer" && req.role != "brand" {
        return Err(AppError::bad_request("role must be 'influencer' or 'brand'"));
    }

    // Unique email check
    let exists: Option<User> = sqlx::query_as::<_, User>(
        "SELECT id, role, name, email, password_hash, created_at \
         FROM users WHERE email = $1",
    )
    .bind(&req.email)
    .fetch_optional(&state.db)
    .await?;

    if exists.is_some() {
        return Err(AppError::conflict("email already registered"));
    }

    let hash = hash_pw(req.password).await?;

    let user: User = sqlx::query_as::<_, User>(
        "INSERT INTO users (role, name, email, password_hash) \
         VALUES ($1, $2, $3, $4) \
         RETURNING id, role, name, email, password_hash, created_at",
    )
    .bind(&req.role)
    .bind(&req.name)
    .bind(&req.email)
    .bind(&hash)
    .fetch_one(&state.db)
    .await?;

    if req.role == "influencer" {
        let handle = req
            .handle
            .as_deref()
            .filter(|s| !s.is_empty())
            .map(|s| s.to_string())
            .unwrap_or_else(|| req.name.to_lowercase().replace(' ', ""));

        sqlx::query(
            "INSERT INTO influencer_profiles \
             (user_id, handle, niche, insta_url, yt_url, bio, location) \
             VALUES ($1,$2,$3,$4,$5,$6,$7)",
        )
        .bind(user.id)
        .bind(&handle)
        .bind(req.niche.as_deref().unwrap_or("Lifestyle"))
        .bind(req.insta_url.as_deref().unwrap_or(""))
        .bind(req.yt_url.as_deref().unwrap_or(""))
        .bind(req.bio.as_deref().unwrap_or(""))
        .bind(req.location.as_deref().unwrap_or(""))
        .execute(&state.db)
        .await?;
    } else {
        sqlx::query(
            "INSERT INTO brand_profiles (user_id, company, industry, website) \
             VALUES ($1,$2,$3,$4)",
        )
        .bind(user.id)
        .bind(req.company.as_deref().unwrap_or(&req.name))
        .bind(req.industry.as_deref().unwrap_or("General"))
        .bind(req.website.as_deref().unwrap_or(""))
        .execute(&state.db)
        .await?;
    }

    let token = create_token(
        user.id,
        &user.role,
        &user.name,
        &state.config.jwt_secret,
        state.config.access_token_expire_hours,
    )?;

    Ok((StatusCode::CREATED, Json(json!({ "token": token, "user": user_json(&user) }))))
}

pub async fn login(
    State(state): State<AppState>,
    Json(req): Json<LoginRequest>,
) -> AppResult<impl IntoResponse> {
    let user: Option<User> = sqlx::query_as::<_, User>(
        "SELECT id, role, name, email, password_hash, created_at \
         FROM users WHERE email = $1",
    )
    .bind(&req.email)
    .fetch_optional(&state.db)
    .await?;

    let user = user.ok_or_else(|| AppError::unauthorized("invalid email or password"))?;

    if !verify_pw(req.password, user.password_hash.clone()).await? {
        return Err(AppError::unauthorized("invalid email or password"));
    }

    let token = create_token(
        user.id,
        &user.role,
        &user.name,
        &state.config.jwt_secret,
        state.config.access_token_expire_hours,
    )?;

    Ok(Json(json!({ "token": token, "user": user_json(&user) })))
}
