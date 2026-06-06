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
    models::{BrandProfile, Product},
    AppState,
};

const PRODUCT_COLS: &str =
    "id, brand_user_id, title, description, category, \
     CAST(budget AS FLOAT8) AS budget, deadline, deliverables, status, created_at";

async fn enrich(p: &Product, state: &AppState) -> serde_json::Value {
    let brand = sqlx::query_as::<_, BrandProfile>(
        "SELECT user_id, company, industry, website, about, logo \
         FROM brand_profiles WHERE user_id = $1",
    )
    .bind(p.brand_user_id)
    .fetch_optional(&state.db)
    .await
    .unwrap_or(None);

    json!({
        "id": p.id,
        "brand_user_id": p.brand_user_id,
        "title": p.title,
        "description": p.description,
        "category": p.category,
        "budget": p.budget,
        "deadline": p.deadline,
        "deliverables": p.deliverables,
        "status": p.status,
        "created_at": p.created_at,
        "brand_name": brand.as_ref().map(|b| &b.company).map(|s| s.as_str()).unwrap_or(""),
        "brand_logo": brand.as_ref().and_then(|b| b.logo.as_deref()).unwrap_or(""),
    })
}

pub async fn list_products(State(state): State<AppState>) -> AppResult<impl IntoResponse> {
    let products = sqlx::query_as::<_, Product>(&format!(
        "SELECT {} FROM products ORDER BY created_at DESC",
        PRODUCT_COLS
    ))
    .fetch_all(&state.db)
    .await?;

    let mut result = Vec::with_capacity(products.len());
    for p in &products {
        result.push(enrich(p, &state).await);
    }
    Ok(Json(result))
}

pub async fn get_product(
    State(state): State<AppState>,
    Path(product_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let p = sqlx::query_as::<_, Product>(&format!(
        "SELECT {} FROM products WHERE id = $1",
        PRODUCT_COLS
    ))
    .bind(product_id)
    .fetch_optional(&state.db)
    .await?
    .ok_or_else(|| AppError::not_found("product not found"))?;

    Ok(Json(enrich(&p, &state).await))
}

#[derive(Deserialize)]
pub struct CreateProductRequest {
    pub title: String,
    pub description: Option<String>,
    pub category: Option<String>,
    pub budget: f64,
    pub deadline: Option<String>,
    pub deliverables: Option<String>,
}

pub async fn create_product(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(req): Json<CreateProductRequest>,
) -> AppResult<impl IntoResponse> {
    let user = extract_user(&headers, &state.config.jwt_secret, &state.db).await?;
    if user.role != "brand" {
        return Err(AppError::forbidden("brands only"));
    }
    if req.title.trim().is_empty() || req.budget <= 0.0 {
        return Err(AppError::bad_request("title and budget > 0 required"));
    }

    let p = sqlx::query_as::<_, Product>(&format!(
        "INSERT INTO products \
         (brand_user_id, title, description, category, budget, deadline, deliverables) \
         VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING {}",
        PRODUCT_COLS
    ))
    .bind(user.id)
    .bind(&req.title)
    .bind(req.description.as_deref().unwrap_or(""))
    .bind(req.category.as_deref().unwrap_or(""))
    .bind(req.budget)
    .bind(req.deadline.as_deref().unwrap_or(""))
    .bind(req.deliverables.as_deref().unwrap_or(""))
    .fetch_one(&state.db)
    .await?;

    Ok((StatusCode::CREATED, Json(enrich(&p, &state).await)))
}
