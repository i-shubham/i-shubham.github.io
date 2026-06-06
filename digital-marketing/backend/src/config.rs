use std::env;

#[derive(Clone, Debug)]
pub struct Config {
    pub database_url: String,
    pub jwt_secret: String,
    pub access_token_expire_hours: i64,
    pub port: u16,
    pub frontend_dir: String,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            database_url: env::var("DATABASE_URL")
                .expect("DATABASE_URL must be set in .env"),
            jwt_secret: env::var("JWT_SECRET")
                .unwrap_or_else(|_| "plugg-dev-secret-2024".to_string()),
            access_token_expire_hours: env::var("ACCESS_TOKEN_EXPIRE_HOURS")
                .unwrap_or_else(|_| "72".to_string())
                .parse()
                .unwrap_or(72),
            port: env::var("PORT")
                .unwrap_or_else(|_| "8080".to_string())
                .parse()
                .unwrap_or(8080),
            frontend_dir: env::var("FRONTEND_DIR")
                .unwrap_or_else(|_| "../".to_string()),
        }
    }
}
