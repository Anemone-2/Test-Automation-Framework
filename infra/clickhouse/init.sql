CREATE TABLE IF NOT EXISTS test_automation.api_events
(
    event_id String,
    event_type LowCardinality(String),
    entity_id String,
    payload String,
    created_at DateTime64(3) DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY (event_type, entity_id, created_at);
