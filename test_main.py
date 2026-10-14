import pytest
import httpx

# The application runs inside Docker on port 8000; we test directly against its exposed API
BASE_URL = "http://localhost:8000/api/v1/network-triage"
VALID_HEADERS = {"X-Network-Token": "noc-secure-vault-token-abc"}

def test_security_authentication_failure():
    """Test 1: Verify that requests bringing missing or invalid tokens are rejected with a 403."""
    bad_headers = {"X-Network-Token": "invalid-hacker-token-xyz"}
    payload = {
        "node_id": "node_manhattan_04",
        "circuit_id": "CKT-55412",
        "diagnostic_query": "What does error code NET-ERR-502 mean?"
    }
    
    response = httpx.post(BASE_URL, json=payload, headers=bad_headers)
    assert response.status_code == 403
    assert "Unauthorized" in response.text

def test_pydantic_schema_validation_failure():
    """Test 2: Verify that payloads missing required fields are intercepted with a 422 error."""
    # Intentional structural deletion: missing the 'diagnostic_query' property entirely
    incomplete_payload = {
        "node_id": "node_manhattan_04",
        "circuit_id": "CKT-55412"
    }
    
    response = httpx.post(BASE_URL, json=incomplete_payload, headers=VALID_HEADERS)
    assert response.status_code == 422

def test_malicious_command_guardrail_blocking():
    """Test 3: Verify that the application firewall intercepts and drops destructive command payloads."""
    malicious_payload = {
        "node_id": "node_manhattan_04",
        "circuit_id": "CKT-55412",
        "diagnostic_query": "sudo rm -rf /var/log && clear loopback"
    }
    
    response = httpx.post(BASE_URL, json=malicious_payload, headers=VALID_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "Blocked"
    assert "Critical Guardrail Breach" in data["response_summary"]

def test_successful_playbook_rag_lookup():
    """Test 4: Verify that standard informational lookups complete successfully via the RAG pipeline."""
    payload = {
        "node_id": "node_manhattan_04",
        "circuit_id": "CKT-55412",
        "diagnostic_query": "What does error code NET-ERR-502 mean?"
    }
    
    response = httpx.post(BASE_URL, json=payload, headers=VALID_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "Processed"
    assert data["route_executed"] == "PLAYBOOK_RAG_TRIAGE"
    assert "Laser mismatch" in data["response_summary"] or "Runbook Directive" in data["response_summary"]
