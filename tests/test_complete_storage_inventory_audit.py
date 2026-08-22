# tests/test_complete_storage_inventory_audit.py
"""
Test suite for Complete Ardha Data Storage Inventory Audit.
"""

from pathlib import Path
import pytest


def test_storage_inventory_audit_documents_exist():
    docs = [
        "docs/ARDHA_COMPLETE_STORAGE_INVENTORY.md",
        "docs/ARDHA_PERFORMANCE_STORAGE_INVENTORY.md",
        "docs/ARDHA_STORAGE_DUPLICATION_MAP.md",
        "docs/ARDHA_STORAGE_USAGE_AND_RETENTION.md",
    ]
    for d in docs:
        p = Path(d)
        assert p.exists(), f"Missing storage inventory document: {d}"
        content = p.read_text(encoding="utf-8")
        assert len(content) > 100, f"Document {d} is empty"


def test_master_storage_inventory_has_required_sections():
    p = Path("docs/ARDHA_COMPLETE_STORAGE_INVENTORY.md")
    content = p.read_text(encoding="utf-8")
    assert "Repository Storage Directory Tree" in content
    assert "Master Storage Inventory Table" in content
    assert "Explicit Answers to Standard Audit Questions" in content


def test_performance_storage_inventory_has_schema_and_immutability():
    p = Path("docs/ARDHA_PERFORMANCE_STORAGE_INVENTORY.md")
    content = p.read_text(encoding="utf-8")
    assert "ArdhaEvaluationRecord Schema" in content
    assert "IMMUTABILITY RULE" in content
    assert "STRICTLY IMMUTABLE" in content


def test_storage_duplication_map_contains_classification():
    p = Path("docs/ARDHA_STORAGE_DUPLICATION_MAP.md")
    content = p.read_text(encoding="utf-8")
    assert "DUPLICATION CLASSIFICATION" in content
    assert "UNNECESSARY DUPLICATION" in content


def test_storage_usage_and_retention_has_disk_breakdown():
    p = Path("docs/ARDHA_STORAGE_USAGE_AND_RETENTION.md")
    content = p.read_text(encoding="utf-8")
    assert "Storage Size & File Count Breakdown" in content
    assert "Retention Policy Inventory" in content
