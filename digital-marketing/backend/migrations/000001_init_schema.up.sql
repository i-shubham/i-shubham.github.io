-- Plugg database schema

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    role VARCHAR(20) NOT NULL CHECK (role IN ('influencer', 'brand', 'admin')),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS influencer_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    handle VARCHAR(100),
    niche VARCHAR(100),
    bio TEXT DEFAULT '',
    location VARCHAR(255) DEFAULT '',
    avatar VARCHAR(500) DEFAULT '',
    insta_url VARCHAR(500) DEFAULT '',
    yt_url VARCHAR(500) DEFAULT '',
    last_synced TIMESTAMPTZ,
    insta_followers INT DEFAULT 0,
    insta_top_reel INT DEFAULT 0,
    yt_subscribers INT DEFAULT 0,
    yt_top_views INT DEFAULT 0,
    engagement NUMERIC(5,2) DEFAULT 0,
    trial_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    plan VARCHAR(20) NOT NULL DEFAULT 'trial' CHECK (plan IN ('trial', 'pro')),
    plan_type VARCHAR(20) DEFAULT 'subscription',
    subscribed_until TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS brand_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company VARCHAR(255) NOT NULL,
    industry VARCHAR(100) DEFAULT '',
    website VARCHAR(500) DEFAULT '',
    about TEXT DEFAULT '',
    logo VARCHAR(500) DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    brand_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    category VARCHAR(100) DEFAULT '',
    budget NUMERIC(12,2) NOT NULL DEFAULT 0,
    deadline VARCHAR(50) DEFAULT '',
    deliverables TEXT DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bids (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    influencer_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    message TEXT DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(product_id, influencer_user_id)
);

CREATE TABLE IF NOT EXISTS concepts (
    id BIGSERIAL PRIMARY KEY,
    bid_id BIGINT NOT NULL REFERENCES bids(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    brand_user_id BIGINT NOT NULL REFERENCES users(id),
    influencer_user_id BIGINT NOT NULL REFERENCES users(id),
    concept TEXT DEFAULT '',
    script TEXT DEFAULT '',
    deliverables TEXT DEFAULT '',
    deadline VARCHAR(50) DEFAULT '',
    shared_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('brand_commission', 'influencer_subscription', 'influencer_commission')),
    user_id BIGINT NOT NULL REFERENCES users(id),
    ref_id BIGINT DEFAULT 0,
    gross NUMERIC(12,2) NOT NULL DEFAULT 0,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_products_brand ON products(brand_user_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_bids_product ON bids(product_id);
CREATE INDEX idx_bids_influencer ON bids(influencer_user_id);
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_type ON payments(type);
