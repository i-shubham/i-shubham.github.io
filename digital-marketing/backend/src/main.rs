use std::{net::SocketAddr, path::PathBuf};

use axum::{
    routing::{get, patch, post},
    Router,
};
use tower_http::{cors::{Any, CorsLayer}, services::ServeDir};

use plugg::{
    config::Config,
    handlers::{admin, auth, bids, influencers, payments, products, profile, stats, users},
    AppState,
};

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();
    tracing_subscriber::fmt::init();

    let config = Config::from_env();
    let db = sqlx::PgPool::connect(&config.database_url)
        .await
        .expect("Failed to connect to PostgreSQL");

    let state = AppState { db, config: config.clone() };

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Axum 0.8 uses {param} syntax (not :param)
    let api = Router::new()
        // ── public ──────────────────────────────────────────────────────────
        .route("/auth/register",         post(auth::register))
        .route("/auth/login",            post(auth::login))
        .route("/stats",                 get(stats::public_stats))
        .route("/products",              get(products::list_products).post(products::create_product))
        .route("/products/{id}",         get(products::get_product))
        .route("/influencers",           get(influencers::list_influencers))
        // ── protected ───────────────────────────────────────────────────────
        .route("/me",                    get(users::me))
        .route("/products/{id}/bids",    get(bids::list_bids).post(bids::place_bid))
        .route("/bids/{id}",             patch(bids::update_bid_status))
        .route("/bids/{id}/concept",     get(bids::get_concept).post(bids::share_concept))
        .route("/influencers/connect",   post(influencers::connect_social))
        .route("/influencers/sync",      post(influencers::sync_stats))
        .route("/payments",              post(payments::record_payment))
        .route("/subscriptions",         post(payments::subscribe))
        .route("/admin/revenue",         get(admin::revenue))
        .route("/profile/picture",       post(profile::upload_picture));

    // Resolve the frontend directory relative to the backend/ folder
    let frontend_dir = PathBuf::from(&config.frontend_dir)
        .canonicalize()
        .unwrap_or_else(|_| PathBuf::from(&config.frontend_dir));

    let serve_dir = ServeDir::new(&frontend_dir).append_index_html_on_directories(true);

    let app = Router::new()
        .nest("/api", api)
        .fallback_service(serve_dir)
        .layer(cors)
        .with_state(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], config.port));
    println!("Plugg (Rust/Axum) running on http://{}", addr);
    println!("   Frontend: {}", frontend_dir.display());

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
