db = db.getSiblingDB('test_automation');
db.createCollection('api_audit_events');
db.api_audit_events.createIndex({ event_id: 1 }, { unique: true });
db.api_audit_events.createIndex({ entity_id: 1, event_type: 1 });
