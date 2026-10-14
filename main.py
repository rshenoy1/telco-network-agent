import os
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
import chromadb
from chromadb.utils import embedding_functions
import gradio as gr

# 1. Initialize core FastAPI Application Instance
app = FastAPI(title="Telecom Network Support Core", version="1.0.0")

# 2. Infrastructure Authentication Handlers
API_KEY_NAME = "X-Network-Token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_token(api_key: str = Security(api_key_header)):
    """Validates structural authorization headers for secure microservice routing."""
    if api_key != "noc-secure-vault-token-abc":
        raise HTTPException(status_code=403, detail="Unauthorized Infrastructure Access Token.")
    return api_key

# 3. Setup Local In-Memory Vector Storage Layers
chroma_client = chromadb.Client()
emb_fn = embedding_functions.DefaultEmbeddingFunction()
vector_db = chroma_client.create_collection(name="network_playbooks", embedding_function=emb_fn)
memory_db = chroma_client.create_collection(name="incident_topology_logs", embedding_function=emb_fn)

# 4. Seed Local Knowledge Base (Engineering Runbooks)
vector_db.add(
    documents=[
        "Error Code NET-ERR-502 implies an Optical Line Terminal (OLT) laser mismatch. Check receive power levels.",
        "Standard SLA protocol for Tier-1 cell tower outages requires dispatching local field engineering within 4 hours.",
        "BGP Routing Loop Mitigation requires verifying ASN parameters and clearing peer routing caching layers.",
        "Fiber ONT terminal resetting requires checking upstream attenuation thresholds. Acceptable limit is -15dBm to -27dBm."
    ],
    ids=["runbook_0", "runbook_1", "runbook_2", "runbook_3"],
    metadatas=[{"subsystem": "optical"}, {"subsystem": "sla"}, {"subsystem": "routing"}, {"subsystem": "ont"}]
)

# 5. Input Data Validation Models
class SupportRequest(BaseModel):
    node_id: str = Field(..., example="node_manhattan_04")
    circuit_id: str = Field(..., example="CKT-55412")
    diagnostic_query: str = Field(..., example="Failing with NET-ERR-502")

# Mock Production Infrastructure Topology DB
MOCK_TOPOLOGY_REGISTRY = {
    "CKT-55412": {"node": "Manhattan_OLT_04", "status": "Degraded", "attenuation_dbm": -32.4, "firmware": "v4.12.2"}
}

# 6. Automated Network Hardware Interaction Scripts
class NetworkDiagnosticTools:
    @staticmethod
    async def trigger_line_diagnostic_loop(circuit_id: str) -> Dict[str, Any]:
        """Tool: Run dynamic OTDR line test sweep over the circuit."""
        if circuit_id not in MOCK_TOPOLOGY_REGISTRY:
            return {"status": "Error", "message": "Circuit Identifier Not Found in Network Registry."}
        MOCK_TOPOLOGY_REGISTRY[circuit_id]["attenuation_dbm"] = -22.1
        MOCK_TOPOLOGY_REGISTRY[circuit_id]["status"] = "Active"
        return {"status": "Success", "message": "Line diagnostic loop cleared downstream loop blocks."}

    @staticmethod
    async def cycle_ont_port(circuit_id: str) -> Dict[str, Any]:
        """Tool: Hard cycle upstream network interface hardware port."""
        if circuit_id not in MOCK_TOPOLOGY_REGISTRY:
            return {"status": "Error", "message": "Circuit Trace Missing."}
        MOCK_TOPOLOGY_REGISTRY[circuit_id]["status"] = "Provisioning"
        return {"status": "Success", "message": "Signal cycle frame issued to upstream hardware frame link."}

# 7. Intelligent Routing & Security Middleware
class NetworkOrchestrationEngine:
    @staticmethod
    def filter_malicious_commands(query: str) -> bool:
        """Blocks raw shell injection patterns trying to compromise underlying hardware interfaces."""
        blocked_commands = ["sudo rm", "drop table", "shutdown interface permanent", "format nvram"]
        return not any(cmd in query.lower() for cmd in blocked_commands)

    @staticmethod
    def evaluate_network_intent(query: str) -> str:
        """Routes query into RAG playbooks or active physical hardware intervention endpoints."""
        action_keywords = ["reset line", "cycle port", "fix attenuation", "clear loopback", "diagnostic loop"]
        if any(keyword in query.lower() for keyword in action_keywords):
            return "HARDWARE_ENGINE_ACTION"
        return "PLAYBOOK_RAG_TRIAGE"

    @staticmethod
    async def process_playbook_rag(query: str) -> str:
        """Retrieves targeted operations instructions based on vector context matches."""
        results = vector_db.query(query_texts=[query], n_results=1)
        
        # Extract the plain text from the nested list structure safely
        if results['documents'] and results['documents'][0]:
            retrieved_runbook = results['documents'][0][0]
        else:
            retrieved_runbook = "No runbook configuration located."
            
        return f"Verified Runbook Directive: {retrieved_runbook}"

    @staticmethod
    async def process_hardware_agent(query: str, circuit_id: str) -> str:
        """Maps intents directly to structural framework hardware macros."""
        circuit_data = MOCK_TOPOLOGY_REGISTRY.get(circuit_id, {})
        if "diagnostic" in query.lower() or "reset" in query.lower() or "attenuation" in query.lower():
            execution = await NetworkDiagnosticTools.trigger_line_diagnostic_loop(circuit_id)
            return f"NOC Status: {execution['message']} Circuit [{circuit_id}] telemetry restored to: {circuit_data.get('attenuation_dbm')} dBm. Topology Status: {circuit_data.get('status')}."
        if "cycle" in query.lower() or "port" in query.lower():
            execution = await NetworkDiagnosticTools.cycle_ont_port(circuit_id)
            return f"NOC Status: {execution['message']} Interface state changed to: {circuit_data.get('status')}."
        return "Network agent could not deduce physical hardware instruction parameters."

# 8. Production API Endpoint
@app.post("/api/v1/network-triage", response_model=Dict[str, Any])
async def process_network_incident(payload: SupportRequest, token: str = Depends(verify_api_token)):
    if not NetworkOrchestrationEngine.filter_malicious_commands(payload.diagnostic_query):
        return {"status": "Blocked", "response": "Critical Guardrail Breach: Destructive Commands Intercepted.", "citations": []}
    
    memory_db.add(documents=[payload.diagnostic_query], ids=[f"inc_{asyncio.get_event_loop().time()}"], metadatas=[{"circuit": payload.circuit_id}])
    route = NetworkOrchestrationEngine.evaluate_network_intent(payload.diagnostic_query)
    
    if route == "HARDWARE_ENGINE_ACTION":
        output_response = await NetworkOrchestrationEngine.process_hardware_agent(payload.diagnostic_query, payload.circuit_id)
    else:
        output_response = await NetworkOrchestrationEngine.process_playbook_rag(payload.diagnostic_query)
        
    return {
        "status": "Processed",
        "route_executed": route,
        "response_summary": output_response,
        "circuit_id": payload.circuit_id
    }

# 9. NOC Administrative Graphical Interface Module
def run_noc_interface_bridge(engineer_message, history):
    """Bridge interface ensuring a valid async event loop is always accessible."""
    try:
        # Try to latch onto the main running FastAPI event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            # Fallback: Check for an existing inactive thread loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Safe Strategy: Force spawn a new loop for the background worker thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
    result = loop.run_until_complete(
        process_network_incident(
            SupportRequest(node_id="node_manhattan_04", circuit_id="CKT-55412", diagnostic_query=engineer_message),
            token="noc-secure-vault-token-abc"
        )
    )
    return result["response_summary"]

demo = gr.ChatInterface(
    fn=run_noc_interface_bridge,
    title="NOC Automated Incident Triage Dashboard",
    description="Telecom Network Operations Center runtime orchestration terminal. Triages fiber/cellular anomalies using vector playbooks or automated script loops.",
    examples=["What does error code NET-ERR-502 mean?", "Trigger line diagnostic loop to fix attenuation drops.", "Cycle port link to provision the circuit frame."]
)

app = gr.mount_gradio_app(app, demo, path="/")
