use std::path::PathBuf;

use axum::{
    extract::{Multipart, State},
    http::HeaderMap,
    response::IntoResponse,
    Json,
};
use serde_json::json;

use crate::{
    auth::extract_user,
    errors::{AppError, AppResult},
    AppState,
};

const MAX_BYTES: usize = 5 * 1024 * 1024; // 5 MB limit
const ALLOWED_EXT: &[&str] = &["jpg", "jpeg", "png", "gif", "webp"];

pub async fn upload_picture(
    State(state): State<AppState>,
    headers: HeaderMap,
    mut multipart: Multipart,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| AppError::bad_request(e.to_string()))?
    {
        if field.name() != Some("file") {
            continue;
        }

        // Determine file extension from the original filename
        let original = field.file_name().unwrap_or("upload.jpg").to_string();
        let ext = original
            .rsplit('.')
            .next()
            .unwrap_or("jpg")
            .to_lowercase();

        if !ALLOWED_EXT.contains(&ext.as_str()) {
            return Err(AppError::bad_request("only jpg, png, gif, webp allowed"));
        }

        let data = field
            .bytes()
            .await
            .map_err(|e| AppError::bad_request(e.to_string()))?;

        if data.len() > MAX_BYTES {
            return Err(AppError::bad_request("file must be under 5 MB"));
        }

        // Build save path relative to frontend_dir (../  → digital-marketing/)
        let (sub_dir, prefix) = if user.role == "influencer" {
            ("img/influencers", "inf")
        } else if user.role == "brand" {
            ("img/brands", "brand")
        } else {
            return Err(AppError::forbidden("only influencers and brands can upload a picture"));
        };

        let frontend = PathBuf::from(&state.config.frontend_dir);
        let img_dir = frontend.join(sub_dir);
        tokio::fs::create_dir_all(&img_dir)
            .await
            .map_err(|e| AppError::internal(e.to_string()))?;

        let filename = format!("{}-{}.{}", prefix, user.id, ext);
        let filepath = img_dir.join(&filename);
        tokio::fs::write(&filepath, &data)
            .await
            .map_err(|e| AppError::internal(e.to_string()))?;

        // URL served by the frontend static file server
        let url = format!("{}/{}", sub_dir, filename);

        // Update DB
        if user.role == "influencer" {
            sqlx::query(
                "UPDATE influencer_profiles SET avatar = $1 WHERE user_id = $2",
            )
            .bind(&url)
            .bind(user.id)
            .execute(&state.db)
            .await?;
        } else {
            sqlx::query(
                "UPDATE brand_profiles SET logo = $1 WHERE user_id = $2",
            )
            .bind(&url)
            .bind(user.id)
            .execute(&state.db)
            .await?;
        }

        return Ok(Json(json!({ "url": url })));
    }

    Err(AppError::bad_request("no file field found in request"))
}
