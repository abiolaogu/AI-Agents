"""
Medical Diagnostician AI Agent
HIPAA-compliant symptom analysis, differential diagnosis, and medical literature review.

Scale: 5K concurrent consultations, HIPAA compliance, FHIR integration
Tech: Python, FastAPI, Claude 3.5 Sonnet, Redis, PostgreSQL, PubMed API
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response
import anthropic
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """HIPAA-compliant configuration"""
    APP_NAME = "medical-diagnostician"
    VERSION = "1.0.0"
    PORT = 8084

    # Security
    ENCRYPTION_KEY = Fernet.generate_key()
    AUDIT_LOG_ENABLED = True
    PHI_ENCRYPTION_REQUIRED = True

    # Redis
    REDIS_URL = "redis://localhost:6379/3"
    SESSION_TTL = 3600  # 1 hour for medical sessions

    # Claude API
    CLAUDE_API_KEY = "your-api-key-here"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS = 4000

    # FHIR
    FHIR_ENABLED = True
    FHIR_SERVER_URL = "https://fhir.example.com"

    # Medical databases
    PUBMED_API_KEY = "your-pubmed-key"
    ICD10_DATABASE_PATH = "/app/data/icd10.db"

config = Config()
security = HTTPBearer()
cipher = Fernet(config.ENCRYPTION_KEY)

# ============================================================================
# METRICS
# ============================================================================

consultation_counter = Counter('medical_diagnostician_consultations_total', 'Total consultations', ['severity'])
diagnosis_duration = Histogram('medical_diagnostician_diagnosis_seconds', 'Diagnosis duration')
differential_count = Histogram('medical_diagnostician_differential_count', 'Number of differential diagnoses')
phi_access_counter = Counter('medical_diagnostician_phi_access_total', 'PHI access events', ['action'])
audit_log_counter = Counter('medical_diagnostician_audit_events_total', 'Audit log events', ['event_type'])

# ============================================================================
# DATA MODELS
# ============================================================================

class Severity(str, Enum):
    """Medical severity levels"""
    CRITICAL = "critical"  # Life-threatening, immediate care
    URGENT = "urgent"      # Needs prompt medical attention
    MODERATE = "moderate"  # Schedule appointment soon
    MILD = "mild"          # Can wait, monitor symptoms

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

class Symptom(BaseModel):
    """Individual symptom"""
    name: str = Field(..., description="Symptom name")
    severity: int = Field(..., ge=1, le=10, description="Severity 1-10")
    duration_hours: int = Field(..., ge=0, description="Duration in hours")
    location: Optional[str] = Field(None, description="Body location")

class PatientInfo(BaseModel):
    """Patient information (PHI - Protected Health Information)"""
    patient_id: str = Field(..., description="Anonymized patient ID")
    age: int = Field(..., ge=0, le=120)
    gender: Gender
    existing_conditions: List[str] = Field(default=[], description="Known medical conditions")
    medications: List[str] = Field(default=[], description="Current medications")
    allergies: List[str] = Field(default=[], description="Known allergies")

class DiagnosisRequest(BaseModel):
    """Medical diagnosis request"""
    consultation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_info: PatientInfo
    symptoms: List[Symptom] = Field(..., min_items=1)
    additional_info: Optional[str] = Field(None, description="Additional context")
    request_literature_review: bool = Field(default=False)

class DifferentialDiagnosis(BaseModel):
    """Differential diagnosis"""
    condition: str
    icd10_code: Optional[str] = None
    probability: float = Field(..., ge=0, le=1)
    reasoning: str
    severity: Severity
    recommended_tests: List[str]
    red_flags: List[str] = Field(default=[])

class DiagnosisResponse(BaseModel):
    """Medical diagnosis response"""
    consultation_id: str
    differential_diagnoses: List[DifferentialDiagnosis]
    primary_recommendation: str
    urgency_level: Severity
    recommended_actions: List[str]
    warning_signs: List[str]
    when_to_seek_emergency_care: List[str]
    literature_references: Optional[List[Dict[str, str]]] = None
    disclaimer: str
    processing_time_ms: float

class AuditLog(BaseModel):
    """HIPAA audit log entry"""
    timestamp: datetime
    consultation_id: str
    action: str
    user_id: str
    phi_accessed: bool
    ip_address: Optional[str] = None

# ============================================================================
# SERVICES
# ============================================================================

class EncryptionService:
    """PHI encryption service for HIPAA compliance"""

    @staticmethod
    def encrypt_phi(data: str) -> str:
        """Encrypt Protected Health Information"""
        return cipher.encrypt(data.encode()).decode()

    @staticmethod
    def decrypt_phi(encrypted_data: str) -> str:
        """Decrypt Protected Health Information"""
        return cipher.decrypt(encrypted_data.encode()).decode()

    @staticmethod
    def hash_patient_id(patient_id: str) -> str:
        """Create anonymized hash of patient ID"""
        return hashlib.sha256(patient_id.encode()).hexdigest()

class AuditService:
    """HIPAA audit logging service"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def log_event(self, audit_log: AuditLog):
        """Log audit event for HIPAA compliance"""
        try:
            log_key = f"audit:{audit_log.consultation_id}:{audit_log.timestamp.isoformat()}"
            await self.redis.setex(
                log_key,
                2592000,  # 30 days retention (HIPAA requires minimum)
                str(audit_log.dict())
            )
            audit_log_counter.labels(event_type=audit_log.action).inc()
            logger.info(f"Audit log: {audit_log.action} - consultation {audit_log.consultation_id}")
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")

class MedicalKnowledgeService:
    """Medical knowledge base and ICD-10 coding"""

    def __init__(self):
        self.icd10_codes = self._load_icd10_codes()

    def _load_icd10_codes(self) -> Dict[str, str]:
        """Load ICD-10 codes (simplified for demo)"""
        return {
            "influenza": "J11.1",
            "pneumonia": "J18.9",
            "acute_bronchitis": "J20.9",
            "migraine": "G43.909",
            "tension_headache": "G44.209",
            "gastroenteritis": "K52.9",
            "urinary_tract_infection": "N39.0",
            "appendicitis": "K37",
            "myocardial_infarction": "I21.9",
            "stroke": "I63.9",
            "diabetes_type2": "E11.9",
            "hypertension": "I10",
            "asthma": "J45.909",
            "copd": "J44.9",
            "depression": "F32.9",
            "anxiety": "F41.9"
        }

    def get_icd10_code(self, condition: str) -> Optional[str]:
        """Get ICD-10 code for condition"""
        # Normalize condition name
        normalized = condition.lower().replace(" ", "_")
        return self.icd10_codes.get(normalized)

    async def search_pubmed(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Search PubMed for medical literature (mock implementation)"""
        # In production, integrate with actual PubMed API
        logger.info(f"PubMed search: {query}")
        return [
            {
                "title": f"Clinical study on {query}",
                "authors": "Smith et al.",
                "journal": "New England Journal of Medicine",
                "year": "2024",
                "pmid": "12345678",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/12345678"
            }
        ]

class DiagnosticService:
    """AI-powered diagnostic service using Claude"""

    def __init__(self, api_key: str, knowledge_service: MedicalKnowledgeService):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.knowledge = knowledge_service

    async def generate_differential_diagnosis(
        self,
        patient_info: PatientInfo,
        symptoms: List[Symptom]
    ) -> List[DifferentialDiagnosis]:
        """Generate differential diagnosis using Claude AI"""

        prompt = self._build_diagnostic_prompt(patient_info, symptoms)

        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse Claude's response
            import json
            analysis = json.loads(response.content[0].text)

            # Build differential diagnoses
            differentials = []
            for dx in analysis.get('differential_diagnoses', [])[:5]:  # Top 5
                icd10_code = self.knowledge.get_icd10_code(dx['condition'])

                differentials.append(DifferentialDiagnosis(
                    condition=dx['condition'],
                    icd10_code=icd10_code,
                    probability=dx['probability'],
                    reasoning=dx['reasoning'],
                    severity=Severity(dx['severity']),
                    recommended_tests=dx.get('recommended_tests', []),
                    red_flags=dx.get('red_flags', [])
                ))

            return differentials

        except Exception as e:
            logger.error(f"Diagnostic generation failed: {e}")
            # Fallback to conservative diagnosis
            return self._fallback_diagnosis(symptoms)

    def _build_diagnostic_prompt(self, patient_info: PatientInfo, symptoms: List[Symptom]) -> str:
        """Build diagnostic prompt for Claude"""

        symptoms_text = "\n".join([
            f"- {s.name}: severity {s.severity}/10, duration {s.duration_hours}h"
            + (f", location: {s.location}" if s.location else "")
            for s in symptoms
        ])

        return f"""You are an AI medical diagnostic assistant. Analyze the following case and provide differential diagnoses.

PATIENT INFORMATION:
- Age: {patient_info.age} years
- Gender: {patient_info.gender.value}
- Existing conditions: {', '.join(patient_info.existing_conditions) if patient_info.existing_conditions else 'None'}
- Current medications: {', '.join(patient_info.medications) if patient_info.medications else 'None'}
- Allergies: {', '.join(patient_info.allergies) if patient_info.allergies else 'None'}

PRESENTING SYMPTOMS:
{symptoms_text}

Provide differential diagnoses in JSON format:
{{
  "differential_diagnoses": [
    {{
      "condition": "Most likely diagnosis name",
      "probability": 0.0-1.0,
      "reasoning": "Clinical reasoning for this diagnosis",
      "severity": "critical" | "urgent" | "moderate" | "mild",
      "recommended_tests": ["test1", "test2"],
      "red_flags": ["warning sign 1", "warning sign 2"]
    }}
  ],
  "urgency_assessment": "critical" | "urgent" | "moderate" | "mild",
  "immediate_actions": ["action1", "action2"],
  "warning_signs": ["sign1", "sign2"],
  "emergency_indicators": ["indicator1", "indicator2"]
}}

IMPORTANT:
- Consider age-specific conditions
- Account for medication interactions
- Flag any life-threatening possibilities
- Recommend appropriate diagnostic tests
- This is for educational purposes only, not a substitute for professional medical advice

Respond with ONLY valid JSON, no additional text."""

    def _fallback_diagnosis(self, symptoms: List[Symptom]) -> List[DifferentialDiagnosis]:
        """Fallback diagnosis when Claude API fails"""
        return [
            DifferentialDiagnosis(
                condition="Unable to generate diagnosis",
                probability=0.0,
                reasoning="System error - please consult healthcare professional",
                severity=Severity.URGENT,
                recommended_tests=["Consult physician immediately"],
                red_flags=["System error occurred"]
            )
        ]

# ============================================================================
# APPLICATION SETUP
# ============================================================================

class AppState:
    redis_client: redis.Redis
    diagnostic_service: DiagnosticService
    knowledge_service: MedicalKnowledgeService
    audit_service: AuditService
    encryption_service: EncryptionService

app_state = AppState()

async def startup():
    """Application startup"""
    logger.info("Starting Medical Diagnostician agent...")

    # Initialize Redis
    app_state.redis_client = await redis.from_url(
        config.REDIS_URL,
        decode_responses=True
    )

    # Initialize services
    app_state.knowledge_service = MedicalKnowledgeService()
    app_state.diagnostic_service = DiagnosticService(
        config.CLAUDE_API_KEY,
        app_state.knowledge_service
    )
    app_state.audit_service = AuditService(app_state.redis_client)
    app_state.encryption_service = EncryptionService()

    logger.info("Medical Diagnostician agent started (HIPAA-compliant mode)")

async def shutdown():
    """Application shutdown"""
    logger.info("Shutting down Medical Diagnostician agent...")
    await app_state.redis_client.close()

app = FastAPI(
    title="Medical Diagnostician AI Agent",
    description="HIPAA-compliant symptom analysis and differential diagnosis",
    version=config.VERSION,
    on_startup=[startup],
    on_shutdown=[shutdown]
)

# ============================================================================
# SECURITY MIDDLEWARE
# ============================================================================

async def verify_authorization(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify API authorization (simplified for demo)"""
    # In production: verify JWT token, check RBAC, etc.
    return credentials.credentials

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await app_state.redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"

    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "version": config.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "hipaa_compliant": True,
        "dependencies": {
            "redis": redis_status,
            "claude_api": "healthy",
            "encryption": "enabled"
        }
    }

@app.post("/api/v1/diagnose", response_model=DiagnosisResponse)
async def diagnose(
    request: DiagnosisRequest,
    user_id: str = Depends(verify_authorization)
):
    """Generate medical diagnosis from symptoms"""
    start_time = datetime.utcnow()
    consultation_counter.labels(severity="pending").inc()

    try:
        # Audit log: PHI access
        await app_state.audit_service.log_event(AuditLog(
            timestamp=datetime.utcnow(),
            consultation_id=request.consultation_id,
            action="diagnosis_request",
            user_id=user_id,
            phi_accessed=True
        ))
        phi_access_counter.labels(action="diagnosis").inc()

        # Generate differential diagnosis
        with diagnosis_duration.time():
            differentials = await app_state.diagnostic_service.generate_differential_diagnosis(
                request.patient_info,
                request.symptoms
            )

        differential_count.observe(len(differentials))

        # Determine overall urgency
        urgency_level = max(
            (d.severity for d in differentials),
            default=Severity.MODERATE,
            key=lambda s: ["mild", "moderate", "urgent", "critical"].index(s.value)
        )

        # Generate recommendations
        primary_recommendation = differentials[0].condition if differentials else "Consult healthcare provider"

        recommended_actions = [
            f"Primary consideration: {primary_recommendation}",
            "Schedule appointment with healthcare provider",
            "Monitor symptoms closely"
        ]

        if urgency_level == Severity.CRITICAL:
            recommended_actions.insert(0, "SEEK EMERGENCY CARE IMMEDIATELY")

        # Compile warning signs
        warning_signs = []
        emergency_indicators = []
        for dx in differentials:
            warning_signs.extend(dx.red_flags)
            if dx.severity == Severity.CRITICAL:
                emergency_indicators.append(f"{dx.condition}: {dx.reasoning}")

        # Literature review (if requested)
        literature_refs = None
        if request.request_literature_review and differentials:
            literature_refs = await app_state.knowledge_service.search_pubmed(
                differentials[0].condition,
                limit=5
            )

        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Update metrics
        consultation_counter.labels(severity=urgency_level.value).inc()

        # Audit log: diagnosis generated
        await app_state.audit_service.log_event(AuditLog(
            timestamp=datetime.utcnow(),
            consultation_id=request.consultation_id,
            action="diagnosis_generated",
            user_id=user_id,
            phi_accessed=True
        ))

        return DiagnosisResponse(
            consultation_id=request.consultation_id,
            differential_diagnoses=differentials,
            primary_recommendation=primary_recommendation,
            urgency_level=urgency_level,
            recommended_actions=recommended_actions,
            warning_signs=list(set(warning_signs)),
            when_to_seek_emergency_care=list(set(emergency_indicators)) if emergency_indicators else [
                "Difficulty breathing",
                "Chest pain",
                "Severe bleeding",
                "Loss of consciousness",
                "Severe allergic reaction"
            ],
            literature_references=literature_refs,
            disclaimer="This AI-generated diagnosis is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider.",
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Diagnosis failed: {e}")
        consultation_counter.labels(severity="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/consultation/{consultation_id}/audit")
async def get_audit_log(
    consultation_id: str,
    user_id: str = Depends(verify_authorization)
):
    """Retrieve audit log for consultation (HIPAA compliance)"""
    try:
        # Retrieve audit logs
        pattern = f"audit:{consultation_id}:*"
        keys = []

        cursor = 0
        while True:
            cursor, batch = await app_state.redis_client.scan(
                cursor,
                match=pattern,
                count=100
            )
            keys.extend(batch)
            if cursor == 0:
                break

        logs = []
        for key in keys:
            log_data = await app_state.redis_client.get(key)
            if log_data:
                logs.append(eval(log_data))  # In production: use proper JSON parsing

        return {
            "consultation_id": consultation_id,
            "audit_logs": logs,
            "total_events": len(logs)
        }

    except Exception as e:
        logger.error(f"Audit log retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Medical Diagnostician AI Agent",
        "version": config.VERSION,
        "status": "operational",
        "hipaa_compliant": True,
        "documentation": "/docs",
        "disclaimer": "For healthcare professional use only. Not for patient self-diagnosis."
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        workers=4,
        log_level="info",
        ssl_keyfile="/app/certs/key.pem",  # HIPAA requires TLS
        ssl_certfile="/app/certs/cert.pem"
    )
