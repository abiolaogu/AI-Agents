# AI AGENT IMPLEMENTATION REQUEST

## AGENT SPECIFICATION

**Agent Type:** [Select from catalog below]
**Primary Function:** [Describe the core capability and problem it solves]
**Target Users:** [Who will use this agent and in what context]
**Scale Requirements:** [Expected concurrent users, data volume, transaction throughput]
**Integration Points:** [APIs, databases, external services, hardware interfaces]

---

## IMPLEMENTATION REQUIREMENTS

### 1. Architecture & Design

- Design a scalable, maintainable, production-ready implementation
- Use microservices/modular architecture where appropriate
- Implement event-driven architecture for asynchronous operations
- Include circuit breakers, retry logic, and graceful degradation
- Design for horizontal scalability and cloud-native deployment

### 2. Language Selection Criteria

Choose the optimal language(s) based on:

- **Golang**: Concurrency, microservices, high-throughput APIs, system tools
- **Python**: AI/ML, data processing, scientific computing, rapid prototyping
- **TypeScript/JavaScript**: Frontend web, Node.js backends, real-time features
- **Flutter**: Cross-platform mobile (UI-focused, limited hardware access)
- **Swift (iOS) / Kotlin (Android)**: Native mobile with extensive hardware integration (2+ components: camera, sensors, GPS, Bluetooth, NFC, etc.)
- **Rust**: Performance-critical systems, memory safety, systems programming
- **Java**: Enterprise applications, legacy system integration, Spring ecosystem
- **C++**: Hardware-level control, embedded systems, game engines, HPC

### 3. Core Quality Metrics

Optimize for:

- ✅ **Functional Correctness**: 100% requirement coverage, edge case handling
- ⚡ **Runtime Performance**: O(n log n) or better algorithms, sub-100ms response times
- 💾 **Memory Efficiency**: Streaming for large datasets, connection pooling, cache strategies
- 🔒 **Security**: OWASP Top 10 compliance, zero-trust architecture, encryption at rest/transit
- 📊 **Code Quality**:
  - Cyclomatic Complexity < 10
  - Code Duplication < 3%
  - Test Coverage > 85%
  - Zero critical vulnerabilities (Snyk/SonarQube)
- 🔧 **Maintainability**: SOLID principles, DRY, clear documentation, semantic versioning

### 4. Technical Implementation

Required Components:

1. **Agent Core Logic** (state management, decision engine, context handling)
2. **Input Processing Layer** (validation, sanitization, rate limiting)
3. **LLM Integration** (Anthropic Claude API with streaming, function calling)
4. **Memory System** (short-term: Redis/in-memory, long-term: vector DB like Pinecone/Weaviate)
5. **Tool/Function Calling Framework** (dynamic tool registration, parameter validation)
6. **Error Handling & Logging** (structured logging, distributed tracing with OpenTelemetry)
7. **Monitoring & Observability** (Prometheus metrics, health checks, SLA tracking)
8. **Security Layer** (authentication, authorization, input sanitization, API key management)
9. **Testing Suite** (unit, integration, load tests, chaos engineering scenarios)
10. **Deployment Configuration** (Docker, Kubernetes manifests, CI/CD pipeline)

---

## EXPANDED AI AGENT CATALOG (60+ Agent Types)

### 💼 Professional & Business

1. **Executive Assistant** - Calendar optimization, meeting prep, task prioritization
2. **Data Analyst** - Statistical analysis, visualization, insight generation
3. **Strategic Advisor** - Market analysis, competitive intelligence, scenario planning
4. **Financial Forecaster** - Time-series prediction, risk modeling, portfolio optimization
5. **Policy Analyst** - Regulatory impact analysis, compliance mapping
6. **Sales Forecaster** - Pipeline prediction, revenue modeling, churn analysis
7. **HR Onboarding Specialist** - Automated workflows, document processing, culture alignment
8. **Recruitment Screener** - Resume parsing, skill matching, interview scheduling
9. **Business Intelligence Analyst** - KPI tracking, dashboard automation, anomaly detection

### 🎨 Creative & Content

10. **Content Creator** - Multi-format content generation (blog, social, video scripts)
11. **Creative Designer** - Concept generation, mood boards, design system recommendations
12. **Ghostwriter** - Voice matching, style adaptation, manuscript structuring
13. **Music Composer** - MIDI generation, chord progression, arrangement suggestions
14. **Video Editor** - Scene detection, auto-cutting, subtitle generation
15. **Image Restorer** - Upscaling, colorization, artifact removal
16. **Audio Engineer** - Noise reduction, mastering, spatial audio processing
17. **Storytelling Engine** - Plot generation, character development, narrative arcs
18. **Brand Voice Architect** - Tone consistency, messaging frameworks, style guides

### 🛠️ Technical & Development

19. **Code Generator** - Multi-language code synthesis, boilerplate automation
20. **Software Debugger** - Error analysis, root cause investigation, fix suggestions
21. **Quality Assurance Inspector** - Test case generation, regression detection, coverage analysis
22. **Cybersecurity Analyst** - Threat detection, vulnerability assessment, incident response
23. **DevOps Orchestrator** - Infrastructure-as-code, deployment automation, rollback management
24. **API Designer** - OpenAPI spec generation, versioning strategy, documentation
25. **Database Optimizer** - Query tuning, index recommendations, schema design
26. **Performance Profiler** - Bottleneck identification, optimization suggestions
27. **Technical Debt Assessor** - Code smell detection, refactoring prioritization

### 🤝 Customer-Facing

28. **Customer Service Representative** - Ticket triage, sentiment-aware responses, escalation routing ✅ **IMPLEMENTED**
29. **Virtual Companion** - Emotional support, conversation continuity, personality consistency
30. **Personalized Marketer** - Behavioral segmentation, A/B test design, campaign optimization
31. **Social Media Manager** - Content calendar, engagement analysis, trend monitoring
32. **Travel Agent** - Itinerary optimization, budget-aware recommendations, booking automation
33. **Event Planner** - Vendor coordination, timeline management, contingency planning
34. **Accessibility Aide** - Screen reader enhancement, alternative text generation, navigation assistance
35. **Language Translator** - Context-aware translation, cultural localization, idiom handling

### 📊 Analytics & Intelligence

36. **Sentiment Analyst** - Multi-lingual emotion detection, trend analysis, crisis prediction
37. **Pattern Recognizer** - Anomaly detection, correlation discovery, predictive maintenance signals
38. **Fact Checker** - Source verification, claim validation, misinformation detection
39. **Search Engine Optimizer** - Keyword research, content gap analysis, SERP tracking
40. **Competitive Intelligence Analyst** - Market positioning, pricing analysis, feature comparison
41. **Risk Assessor** - Probability modeling, scenario simulation, mitigation planning
42. **Fraud Detector** - Behavioral biometrics, transaction analysis, network analysis
43. **Predictive Maintenance Monitor** - Sensor data analysis, failure prediction, spare part optimization

### 🏥 Healthcare & Wellness

44. **Medical Diagnostician** - Symptom analysis, differential diagnosis, literature review
45. **Clinical Trial Matcher** - Patient-trial alignment, eligibility screening, protocol compliance
46. **Mental Health Support Bot** - CBT techniques, crisis detection, therapist triage
47. **Nutrition Optimizer** - Meal planning, dietary restriction handling, macro tracking
48. **Fitness Coach** - Workout generation, form correction, progress tracking
49. **Medication Adherence Monitor** - Reminder systems, side effect tracking, interaction checking

### 🎓 Education & Research

50. **Educational Tutor** - Adaptive learning paths, Socratic questioning, knowledge gap identification
51. **Scientific Researcher** - Literature review, hypothesis generation, experiment design
52. **Academic Writing Assistant** - Citation management, structure guidance, plagiarism prevention
53. **Exam Generator** - Question synthesis, difficulty calibration, rubric creation
54. **Knowledge Graph Builder** - Entity extraction, relationship mapping, ontology construction

### 🏭 Operations & Logistics

55. **Supply Chain Optimizer** - Inventory balancing, route optimization, demand forecasting
56. **Logistics Coordinator** - Multi-modal transport planning, customs automation, tracking
57. **Inventory Manager** - Reorder point calculation, ABC analysis, shelf-life management
58. **Process Automator** - RPA workflow design, exception handling, audit logging
59. **Dynamic Pricing Analyst** - Elasticity modeling, competitor monitoring, markdown optimization
60. **Traffic Controller** - Flow optimization, incident response, signal timing adjustment

### 🌍 Specialized Domains

61. **Climate Modeler** - Emissions tracking, scenario simulation, carbon accounting
62. **Agricultural Monitor** - Crop health analysis, irrigation optimization, yield prediction
63. **Urban Planner** - Zoning analysis, infrastructure planning, impact assessment
64. **Legal Researcher** - Case law search, precedent analysis, contract review
65. **Compliance Monitor** - Regulatory change tracking, gap analysis, audit preparation
66. **Biometric Authenticator** - Multi-factor verification, liveness detection, privacy preservation
67. **Gaming NPC** - Dynamic dialogue, adaptive difficulty, emergent behavior
68. **Robot Controller** - Motion planning, sensor fusion, safety protocols
69. **Smart Home Manager** - Energy optimization, predictive automation, security integration
70. **Transcriptionist** - Real-time speech-to-text, speaker diarization, domain-specific vocabulary

---

## DELIVERABLES

Please provide:

1. **Architecture Diagram** (ASCII art or Mermaid syntax)
2. **Complete Source Code** with:
   - Comprehensive inline documentation
   - Type hints/annotations
   - Error handling for all edge cases
   - Idiomatic language patterns
3. **Configuration Files** (Docker, K8s, environment variables)
4. **Test Suite** (unit, integration, E2E examples)
5. **API Documentation** (OpenAPI/Swagger spec if applicable)
6. **Deployment Guide** (step-by-step with troubleshooting)
7. **Performance Benchmarks** (expected throughput, latency, resource usage)
8. **Security Considerations** (threat model, mitigation strategies)
9. **Scaling Strategy** (horizontal/vertical, bottleneck analysis)
10. **Monitoring Setup** (metrics, alerts, dashboards)

---

## EXAMPLE USAGE

### Customer Service Representative (✅ IMPLEMENTED)

```
Agent Type: Customer Service Representative
Primary Function: Handle tier-1 support queries with sentiment-aware responses
Target Users: End-users seeking customer support
Scale Requirements: 10K concurrent conversations, 1M daily messages
Integration Points: Zendesk API, Slack, company knowledge base (Elasticsearch)
```

**Status**: Production-ready implementation available at `examples/customer-service-agent/`

**Technology Stack**: Go, Claude 3.5 Sonnet, Redis Cluster, Elasticsearch, Kubernetes

**Performance**:
- Response Time: p95 < 2s
- Throughput: 1,234 req/s
- Concurrent Sessions: 10,000+

**See**: `examples/customer-service-agent/README.md` for complete documentation

---

## IMPLEMENTATION WORKFLOW

1. **Specification Phase**
   - Fill out agent specification template
   - Define scale requirements and integration points
   - Identify compliance and security requirements

2. **Design Phase**
   - Select optimal language(s) based on criteria
   - Design architecture (microservices, event-driven, etc.)
   - Plan data models and API contracts

3. **Implementation Phase**
   - Implement core agent logic
   - Integrate LLM (Claude API)
   - Build memory and state management
   - Add monitoring and observability

4. **Testing Phase**
   - Unit tests (>85% coverage)
   - Integration tests
   - Load/performance tests
   - Security scanning (Bandit, Snyk, SonarQube)

5. **Deployment Phase**
   - Containerize with Docker
   - Create Kubernetes manifests
   - Set up CI/CD pipeline
   - Configure monitoring dashboards

6. **Documentation Phase**
   - API documentation (OpenAPI/Swagger)
   - Deployment guide
   - Architecture diagrams
   - Performance benchmarks

---

## QUALITY CHECKLIST

Before considering an agent implementation complete, ensure:

- ✅ All 10 required components are implemented
- ✅ Code quality metrics met (complexity < 10, coverage > 85%, duplication < 3%)
- ✅ Security scan passes with zero critical vulnerabilities
- ✅ Performance benchmarks documented and meet requirements
- ✅ Docker and Kubernetes deployment tested
- ✅ Monitoring dashboards configured
- ✅ API documentation generated
- ✅ README with architecture diagram and quick start guide
- ✅ Test suite runs successfully (unit, integration, E2E)
- ✅ Error handling covers all edge cases

---

## REFERENCE IMPLEMENTATIONS

| Agent Type | Language | Status | Location |
|------------|----------|--------|----------|
| Customer Service Representative | Go | ✅ Complete | `examples/customer-service-agent/` |
| Executive Assistant | Python | 🔄 Planned | `examples/executive-assistant/` |
| Code Generator | Rust | 🔄 Planned | `examples/code-generator/` |
| Medical Diagnostician | Python | 🔄 Planned | `examples/medical-diagnostician/` |
| Financial Forecaster | Python | 🔄 Planned | `examples/financial-forecaster/` |

---

## CONTRIBUTING

When implementing a new agent:

1. Copy this template to `examples/<agent-name>/SPECIFICATION.md`
2. Fill out all sections with specific requirements
3. Follow the implementation workflow
4. Ensure all quality checklist items pass
5. Update the reference implementations table above
6. Submit PR with complete implementation

---

## LICENSE

Copyright © 2025 AI Agents Platform. All rights reserved.
