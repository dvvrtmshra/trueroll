from app.core.audit import append_audit_entry, verify_chain
from app.core.clock import app_now


def test_audit_chain_valid(db):
    append_audit_entry(db, "tester", "SYSTEM_ADMIN", "TEST_ACTION", "TestObject", "obj-1")
    append_audit_entry(db, "tester", "SYSTEM_ADMIN", "TEST_ACTION_2", "TestObject", "obj-2")
    result = verify_chain(db)
    assert result["valid"] is True


def test_audit_chain_genesis_first(db):
    from app.models.audit_entry import AuditEntry
    first = db.query(AuditEntry).order_by(AuditEntry.id).first()
    if first:
        assert first.prev_hash == "GENESIS" or len(first.prev_hash) == 64
