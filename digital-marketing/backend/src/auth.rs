use axum::http::HeaderMap;
use chrono::{Duration, Utc};
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;

use crate::errors::{AppError, AppResult};
use crate::models::User;

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,
    pub role: String,
    pub name: String,
    pub exp: usize,
}

pub fn create_token(
    user_id: i64,
    role: &str,
    name: &str,
    secret: &str,
    expire_hours: i64,
) -> AppResult<String> {
    let exp = (Utc::now() + Duration::hours(expire_hours)).timestamp() as usize;
    let claims = Claims {
        sub: user_id.to_string(),
        role: role.to_string(),
        name: name.to_string(),
        exp,
    };
    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .map_err(|e| AppError::internal(e.to_string()))
}

pub fn decode_token(token: &str, secret: &str) -> AppResult<Claims> {
    let mut v = Validation::new(Algorithm::HS256);
    v.validate_exp = true;
    decode::<Claims>(token, &DecodingKey::from_secret(secret.as_bytes()), &v)
        .map(|d| d.claims)
        .map_err(|e| AppError::unauthorized(e.to_string()))
}

/// Extract and validate the Bearer token; return the `User` row.
pub async fn extract_user(headers: &HeaderMap, secret: &str, db: &PgPool) -> AppResult<User> {
    let auth = headers
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .ok_or_else(|| AppError::unauthorized("missing Authorization header"))?;

    let token = auth
        .strip_prefix("Bearer ")
        .ok_or_else(|| AppError::unauthorized("invalid Authorization format"))?;

    let claims = decode_token(token, secret)?;
    let user_id: i64 = claims
        .sub
        .parse()
        .map_err(|_| AppError::unauthorized("invalid token subject"))?;

    sqlx::query_as::<_, User>(
        "SELECT id, role, name, email, password_hash, created_at FROM users WHERE id = $1",
    )
    .bind(user_id)
    .fetch_optional(db)
    .await?
    .ok_or_else(|| AppError::unauthorized("user not found"))
}

/// Async bcrypt hash — runs in a blocking thread to avoid stalling the executor.
pub async fn hash_pw(password: String) -> AppResult<String> {
    tokio::task::spawn_blocking(move || bcrypt::hash(&password, bcrypt::DEFAULT_COST))
        .await
        .map_err(|e| AppError::internal(e.to_string()))?
        .map_err(Into::into)
}

/// Async bcrypt verify.
pub async fn verify_pw(password: String, hash: String) -> AppResult<bool> {
    tokio::task::spawn_blocking(move || bcrypt::verify(&password, &hash))
        .await
        .map_err(|e| AppError::internal(e.to_string()))?
        .map_err(Into::into)
}
