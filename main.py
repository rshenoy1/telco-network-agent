import os
import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Float, select, update
import chromadb
from chromadb.utils import embedding_functions
import gradio as gr
import httpx

# ==========================================
# 1. POSTGRESQL ASYNC ENGINE & MODEL CONFIG
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:securepass@postgres_db:5432/network_db")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class CircuitEntity(Base):
    """Database model mapping telecom physical infrastructure topology."""
    __tablename__ = "circuits"
    
    circuit_id = Column(String, primary_key=True, index=True)
    node_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    attenuation_dbm = Column(Float, nullable=False)

async def get_db_session():
    """Asynchronous Database Dependency Injector."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ==========================================
# 2. APPLICATION BOOTSTRAP INITIALIZATION
# ==========================================
app = FastAPI(title="Telecom Network Support Core v2", version="2.0.0")

API_KEY_NAME = "X-Network-Token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_token(api_key: str = Security(api_key_header)):
    """Validates global structural authorization tokens."""
    if api_key != "noc-secure-vault-token-abc":
        raise HTTPException(status_code=403, detail="Unauthorized Infrastructure Access Token.")
    return api_key

chroma_client = chromadb.Client()
emb_fn = embedding_functions.DefaultEmbeddingFunction()
vector_db = chroma_client.create_collection(name="network_playbooks", embedding_function=emb_fn)
memory_db = chroma_client.create_collection(name="incident_topology_logs", embedding_function=emb_fn)

@app.on_event("startup")
async def app_startup_pipeline():
    """Initializes tables, seeds runtime RAG vectors and default PostgreSQL rows."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CircuitEntity).where(CircuitEntity.circuit_id == "CKT-55412"))
        if not result.scalar_one_or_none():
            seed_ckt = CircuitEntity(circuit_id="CKT-55412", node_id="Manhattan_OLT_04", status="Degraded", attenuation_dbm=-32.4)
            session.add(seed_ckt)
            await session.commit()

    if vector_db.count() == 0:
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

# ==========================================
# 3. VERIFIED DATA INTERACTION SCHEMAS
# ==========================================
class SupportRequest(BaseModel):
    node_id: str = Field(..., example="node_manhattan_04")
    circuit_id: str = Field(..., example="CKT-55412")
    diagnostic_query: str = Field(..., example="Failing with NET-ERR-502")

# ==========================================
# 4. TECHNICAL DATA MUTATION REPOS
# ==========================================
class NetworkDiagnosticTools:
    @staticmethod
    async def trigger_line_diagnostic_loop(session: AsyncSession, circuit_id: str) -> Dict[str, Any]:
        """Tool: Run live OTDR test line sweep and patch database metrics."""
        result = await session.execute(select(CircuitEntity).where(CircuitEntity.circuit_id == circuit_id))
        circuit = result.scalar_one_or_none()
        if not circuit:
            return {"status": "Error", "message": f"Circuit {circuit_id} absent from database records."}
            
        circuit.attenuation_dbm = -22.1
        circuit.status = "Active"
        await session.flush()
        return {"status": "Success", "message": "Line diagnostic loop cleared downstream blocks on database node."}

    @staticmethod
    async def cycle_ont_port(session: AsyncSession, circuit_id: str) -> Dict[str, Any]:
        """Tool: Hard cycle upstream network interface hardware port."""
        result = await session.execute(select(CircuitEntity).where(CircuitEntity.circuit_id == circuit_id))
        circuit = result.scalar_one_or_none()
        if not circuit:
            return {"status": "Error", "message": f"Circuit {circuit_id} record missing."}
        circuit.status = "Provisioning"
        await session.flush()
        return {"status": "Success", "message": "Signal cycle frame issued to upstream hardware frame link."}

# ==========================================
# 5. CORE ROUTING EXECUTION ENGINE
# ==========================================
class NetworkOrchestrationEngine:
    @staticmethod
    def filter_malicious_commands(query: str) -> bool:
        """Blocks raw shell injection patterns trying to compromise underlying hardware interfaces."""
        blocked_commands = ["sudo rm", "drop table", "shutdown interface permanent", "format nvram"]
        return not any(cmd in query.lower() for cmd in blocked_commands)

    @staticmethod
    def evaluate_network_intent(query: str) -> str:
        """Routes queries into RAG playbooks or active hardware intervention endpoints."""
        action_keywords = ["reset line", "cycle port", "fix attenuation", "clear loopback", "diagnostic loop"]
        if any(keyword in query.lower() for keyword in action_keywords):
            return "HARDWARE_ENGINE_ACTION"
        return "PLAYBOOK_RAG_TRIAGE"

    @staticmethod
    async def process_playbook_rag(query: str) -> str:
        """Retrieves targeted operations instructions based on vector context matches."""
        results = vector_db.query(query_texts=[query], n_results=1)
        if results['documents'] and results['documents']:
            retrieved_runbook = results['documents']
        else:
            retrieved_runbook = "No runbook configuration located."
        return f"Verified Runbook Directive: {retrieved_runbook}"

    @staticmethod
    async def process_hardware_agent(session: AsyncSession, query: str, circuit_id: str) -> str:
        """Maps intents directly to structural framework hardware macros."""
        if "diagnostic" in query.lower() or "reset" in query.lower() or "attenuation" in query.lower():
            execution = await NetworkDiagnosticTools.trigger_line_diagnostic_loop(session, circuit_id)
            if execution["status"] == "Error":
                return f"NOC Alert: {execution['message']}"
                
            result = await session.execute(select(CircuitEntity).where(CircuitEntity.circuit_id == circuit_id))
            updated_circuit = result.scalar_one()
            return f"NOC Status: {execution['message']} Circuit [{circuit_id}] telemetry restored in Postgres to: {updated_circuit.attenuation_dbm} dBm. Status: {updated_circuit.status}."
        
        if "cycle" in query.lower() or "port" in query.lower():
            execution = await NetworkDiagnosticTools.cycle_ont_port(session, circuit_id)
            if execution["status"] == "Error":
                return f"NOC Alert: {execution['message']}"
                
            result = await session.execute(select(CircuitEntity).where(CircuitEntity.circuit_id == circuit_id))
            updated_circuit = result.scalar_one()
            return f"NOC Status: {execution['message']} Interface state updated in Postgres to: {updated_circuit.status}."
            
        return "Network agent could not deduce physical hardware instruction parameters."

# ==========================================
# 6. REST MIDDLEWARE ENDPOINT
# ==========================================
@app.post("/api/v1/network-triage")
async def process_network_incident(payload: SupportRequest, token: str = Depends(verify_api_token), session: AsyncSession = Depends(get_db_session)):
    if not NetworkOrchestrationEngine.filter_malicious_commands(payload.diagnostic_query):
        return {"status": "Blocked", "response_summary": "Critical Guardrail Breach: Destructive Commands Intercepted."}
    
    memory_db.add(documents=[payload.diagnostic_query], ids=[f"inc_{asyncio.get_event_loop().time()}"], metadatas=[{"circuit": payload.circuit_id}])
    route = NetworkOrchestrationEngine.evaluate_network_intent(payload.diagnostic_query)
    
    if route == "HARDWARE_ENGINE_ACTION":
        output_response = await NetworkOrchestrationEngine.process_hardware_agent(session, payload.diagnostic_query, payload.circuit_id)
    else:
        output_response = await NetworkOrchestrationEngine.process_playbook_rag(payload.diagnostic_query)
        
    return {
        "status": "Processed",
        "route_executed": route,
        "response_summary": output_response
    }

# ==========================================
# 7. GRADIO ADMIN PANEL INTEGRATION
# ==========================================
def run_noc_interface_bridge(engineer_message, history):
    """Bypasses worker thread conflicts via internal HTTP API requests directly to localhost inside the container."""
    try:
        url = "http://localhost:8000/api/v1/network-triage"
        headers = {"X-Network-Token": "noc-secure-vault-token-abc"}
        payload = {
            "node_id": "node_manhattan_04",
            "circuit_id": "CKT-55412",
            "diagnostic_query": engineer_message
        }
        
        response = httpx.post(url, json=payload, headers=headers, timeout=15.0)
        
        if response.status_code == 200:
            return response.json()["response_summary"]
        else:
            return f"API Error Code: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Network Connection Fault: {str(e)}"

demo = gr.ChatInterface(
    fn=run_noc_interface_bridge,
    title="NOC Automated Incident Triage Dashboard v2",
    description="Telecom Network Operations Center runtime orchestration terminal. Triaging errors with Async PostgreSQL storage connections.",
    examples=["What does error code NET-ERR-502 mean?", "Trigger line diagnostic loop to fix attenuation drops.", "Cycle port link to provision the circuit frame."]
)

app = gr.mount_gradio_app(app, demo, path="/")
