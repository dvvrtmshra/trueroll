"""S17 — Tamper demo: tamper one audit entry, chain verify fails, restore makes it valid."""
import pytest
from sqlalchemy import text
from app.core.audit import append_audit_entry, verify_chain


def test_s17_chain_valid_after_append(db):
    """Freshly appended entries form a valid chain."""
    append_audit_entry(db, "test.s17", "SYSTEM_ADMIN", "s17_action_1", "TestObj", "obj-s17-1")
    result = verify_chain(db)
    assert result["valid"] is True


def test_s17_tamper_breaks_chain(db):
    """Corrupting an entry hash causes verify_chain to report broken."""
    entry = append_audit_entry(db, "test.s17", "SYSTEM_ADMIN", "s17_action_2", "TestObj", "obj-s17-2")
    entry_id = entry.id
    orig_hash = entry.entry_hash

    # Corrupt the hash
    bogus = "00000000" + orig_hash[8:]
    db.execute(text("UPDATE audit_entry SET entry_hash = :h WHERE id = :i"), {"h": bogus, "i": entry_id})
    db.commit()

    result = verify_chain(db)
    assert result["valid"] is False
    assert result.get("broken_at_id") == entry_id

    # Restore to avoid polluting subsequent tests
    db.execute(text("UPDATE audit_entry SET entry_hash = :h WHERE id = :i"), {"h": orig_hash, "i": entry_id})
    db.commit()


def test_s17_restore_fixes_chain(db):
    """After tamper then restore, the chain is valid again."""
    entry = append_audit_entry(db, "test.s17", "SYSTEM_ADMIN", "s17_action_3", "TestObj", "obj-s17-3")
    entry_id = entry.id
    orig_hash = entry.entry_hash

    # Tamper
    bogus = "00000000" + orig_hash[8:]
    db.execute(text("UPDATE audit_entry SET entry_hash = :h WHERE id = :i"), {"h": bogus, "i": entry_id})
    db.commit()
    assert verify_chain(db)["valid"] is False

    # Restore
    db.execute(text("UPDATE audit_entry SET entry_hash = :h WHERE id = :i"), {"h": orig_hash, "i": entry_id})
    db.commit()

    assert verify_chain(db)["valid"] is True
