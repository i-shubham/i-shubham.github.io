pub mod auth;
pub mod config;
pub mod errors;
pub mod handlers;
pub mod models;

use config::Config;
use sqlx::PgPool;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub config: Config,
}
