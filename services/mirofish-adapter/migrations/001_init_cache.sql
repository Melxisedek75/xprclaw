-- Initialize MiroFish simulation cache table in Cloudflare D1
-- Migration: 001_init_cache.sql

CREATE TABLE IF NOT EXISTS mirofish_simulations (
    -- Primary key: cache key (SHA256 hash of scenario + market_state)
    cache_key TEXT PRIMARY KEY,

    -- Serialized SimulationResult (JSON)
    result_json TEXT NOT NULL,

    -- Metadata for cache management
    scenario TEXT NOT NULL,  -- Index for lookups
    request_id TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,

    -- Cache TTL: timestamp when entry expires (seconds since epoch)
    expires_at INTEGER NOT NULL,

    -- Timestamps
    created_at INTEGER NOT NULL,  -- unix timestamp
    updated_at INTEGER NOT NULL,  -- unix timestamp

    -- Indexes
    CONSTRAINT created_at_expires_check CHECK (created_at <= expires_at)
);

-- Index for cache expiry cleanup queries
CREATE INDEX IF NOT EXISTS idx_expires_at ON mirofish_simulations(expires_at);

-- Index for scenario filtering
CREATE INDEX IF NOT EXISTS idx_scenario ON mirofish_simulations(scenario);

-- Index for cache hit lookups (cache_key)
-- Primary key already indexed

-- Metadata table for migrations tracking
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    executed_at INTEGER NOT NULL,
    checksum TEXT NOT NULL
);

-- Record this migration
INSERT OR IGNORE INTO migrations (name, executed_at, checksum)
VALUES ('001_init_cache', CAST(UNIXEPOCH() AS INTEGER), 'v1');
