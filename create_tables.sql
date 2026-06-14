-- Initial tables for Intent-to-Cart system

-- 1. intents table
CREATE TABLE IF NOT EXISTS intents (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    raw_text TEXT NOT NULL,
    intent_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 2. clarifications table
CREATE TABLE IF NOT EXISTS clarifications (
    id UUID PRIMARY KEY,
    intent_id UUID NOT NULL REFERENCES intents(id),
    question TEXT NOT NULL,
    answer TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 3. bundles table
CREATE TABLE IF NOT EXISTS bundles (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    intent_id UUID NOT NULL REFERENCES intents(id),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 4. bundle_items table
CREATE TABLE IF NOT EXISTS bundle_items (
    id UUID PRIMARY KEY,
    bundle_id UUID NOT NULL REFERENCES bundles(id),
    product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL
);

-- 5. carts table
CREATE TABLE IF NOT EXISTS carts (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    bundle_id UUID REFERENCES bundles(id),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT ck_carts_status CHECK (status IN ('active', 'checked_out', 'abandoned'))
);

-- 6. cart_items table
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY,
    cart_id UUID NOT NULL REFERENCES carts(id),
    product_id VARCHAR(255) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL,
    CONSTRAINT ck_cart_items_quantity CHECK (quantity >= 1),
    CONSTRAINT ck_cart_items_price CHECK (price >= 0.01)
);

-- 7. substitutions table
CREATE TABLE IF NOT EXISTS substitutions (
    id UUID PRIMARY KEY,
    original_product_id VARCHAR NOT NULL,
    replacement_product_id VARCHAR NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT ck_substitution_no_self_reference CHECK (original_product_id != replacement_product_id),
    CONSTRAINT uq_substitution_original_replacement UNIQUE (original_product_id, replacement_product_id)
);

-- 8. user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL UNIQUE,
    brand_preferences JSONB NOT NULL DEFAULT '{}',
    category_preferences JSONB NOT NULL DEFAULT '{}',
    reorder_affinity JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create alembic_version table for migration tracking
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Insert the current migration version
INSERT INTO alembic_version (version_num) VALUES ('001') ON CONFLICT DO NOTHING;
