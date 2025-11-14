# Multi-Framework Super-Agent Platform
## Comprehensive Training Manual

**Version:** 1.0  
**Date:** November 2025  
**Audience:** All Users (Admins, Data Scientists, Developers, End Users)  
**Status:** Production Ready

---

## 📚 Table of Contents

1. [Introduction & Platform Overview](#introduction)
2. [Getting Started](#getting-started)
3. [Role-Based Training Paths](#role-based-paths)
4. [Core Concepts](#core-concepts)
5. [Hands-On Tutorials](#hands-on-tutorials)
6. [Troubleshooting & FAQs](#troubleshooting)
7. [Best Practices](#best-practices)
8. [Advanced Configuration](#advanced-configuration)

---

## Introduction & Platform Overview {#introduction}

### What is the Multi-Framework Super-Agent Platform?

The Multi-Framework Super-Agent Platform is an enterprise-grade AI orchestration system that intelligently routes tasks across three specialized frameworks:

**LangGraph** - Control plane for intelligent routing based on task complexity, resource availability, and cost optimization.

**CrewAI** - Multi-agent teamwork engine for complex tasks requiring collaboration, research, and quality output. Ideal for analytics, report generation, and strategic planning.

**AutoGen** - Dialogue-based agent with code execution capabilities for reliability-critical tasks requiring self-correction and iteration.

### Key Features

**Multi-Framework Orchestration**: Automatically selects the best framework for your task (speed, quality, or reliability).

**Knowledge Management**: Global vector memory (Milvus) for semantic search across all your documents, code, and policies.

**Durable State Management**: ScyllaDB ensures reliable event tracking, session management, and audit logs.

**High-Speed Caching**: DragonflyDB provides transient memory for agent execution context and real-time metrics.

**Strong Consistency Control Plane**: PostgreSQL with pgvector ensures billing, authentication, and strong consistency requirements.

**Role-Based Access Control**: Fine-grained permissions at API, endpoint, and data levels.

**Web & Mobile Access**: Native support for React web app and Flutter mobile app with offline capabilities.

**Enterprise Security**: OpenSCAP compliance scanning, encryption, audit logging, and policy enforcement.

### Platform Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│               User Interfaces                            │
├──────────────────────┬──────────────────────┬────────────┤
│  Web (React)         │  Mobile (Flutter)    │  Desktop   │
│  Real-time Updates   │  Offline Support     │  (Electron)│
└──────────────────────┴──────────────────────┴────────────┘
                            │
                    API Gateway & Auth
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    ┌────────────┐   ┌──────────────┐   ┌─────────────┐
    │ LangGraph  │   │  CrewAI      │   │  AutoGen    │
    │ Router     │   │  Orchestrator│   │  Code Agent │
    │ (Speed)    │   │  (Quality)   │   │  (Reliability)
    └────────────┘   └──────────────┘   └─────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Milvus     │  │  ScyllaDB    │  │ DragonflyDB  │
    │   (Vectors)  │  │  (Events)    │  │  (Cache)     │
    └──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  PostgreSQL    │
                    │  (Control)     │
                    └────────────────┘
```

### Platform Benefits

- **50-70% Cost Savings**: Intelligent routing uses cheapest appropriate framework
- **99.9% Uptime SLA**: Enterprise-grade infrastructure on RunPod
- **Sub-2 Second Response Times**: Average response <2 seconds for standard queries
- **100% Audit Trail**: Immutable event logs for compliance
- **Multi-Tenant Ready**: Complete tenant isolation at data level
- **Scalable to 100,000+ TPS**: Can handle massive concurrent load

---

## Getting Started {#getting-started}

### Prerequisites

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Mobile device (iOS 12+ or Android 8+) for Flutter app
- Internet connection
- Credentials provided by your administrator

### First Login

**Web Application**:
1. Navigate to your organization's super-agent URL
2. Click "Sign In" or "Login with SSO"
3. Enter your credentials (email + password or OAuth provider)
4. If prompted, complete MFA (Multi-Factor Authentication)
5. You'll land on your dashboard

**Mobile Application**:
1. Download the app from App Store (iOS) or Google Play (Android)
2. Tap "Create Account" or "Sign In"
3. Enter your email
4. Complete the verification code sent to your email
5. Set biometric authentication (optional but recommended)
6. You're ready to go!

### Dashboard Orientation

The dashboard displays:

**Status Panel** - System health, active agents, queue length

**Recent Activity** - Your last 5 executed tasks with status

**Quick Actions** - Buttons for common operations (New Task, View Reports, etc.)

**Notifications** - Task completions, alerts, system updates

**Resource Usage** - Your API quota, storage usage, team capacity

### Your First Task

1. Click **"New Task"** button
2. Enter your query or request in the input field
3. (Optional) Select specific framework or let AI decide
4. (Optional) Upload files for context (documents, code, data)
5. Click **"Execute"**
6. Watch real-time progress in the Results panel
7. Download or share results when complete

---

## Role-Based Training Paths {#role-based-paths}

### Administrator Path

**Responsibilities**: System configuration, user management, security, compliance

**Topics**:
- User & role management (create users, assign roles, set permissions)
- Tenant configuration & billing setup
- API key management & quota allocation
- Integration setup (OAuth, SAML, email)
- Backup & disaster recovery procedures
- Compliance reporting (audit logs, compliance dashboards)
- System monitoring & alerting
- Cost optimization & budget management

**Time Commitment**: 8-12 hours initial training

**Key Sections**: See "Administrator Guide" in manuals section

### Data Scientist Path

**Responsibilities**: Building agents, optimizing workflows, knowledge management

**Topics**:
- Creating and configuring custom agents
- Building multi-agent crews (CrewAI)
- Designing agent workflows
- Knowledge base management (uploading documents to Milvus)
- Prompt engineering best practices
- Testing & validation workflows
- Monitoring agent performance metrics
- Cost optimization per workflow

**Time Commitment**: 6-10 hours initial training

**Key Sections**: See "Data Scientist Guide" in manuals section

### Developer Path

**Responsibilities**: API integration, custom tools, system architecture

**Topics**:
- API authentication & authorization
- Building custom tools for agents
- Webhook integration
- Database schema & queries
- Deployment & DevOps
- Security best practices
- Performance tuning
- Custom framework integration

**Time Commitment**: 10-16 hours initial training

**Key Sections**: See "Developer Guide" in manuals section

### End User Path

**Responsibilities**: Using the platform for daily tasks

**Topics**:
- Creating new tasks
- Uploading context documents
- Monitoring task progress
- Understanding results
- Cost tracking for personal projects
- Troubleshooting common issues

**Time Commitment**: 2-4 hours initial training

**Key Sections**: See "End User Guide" in manuals section

---

## Core Concepts {#core-concepts}

### Framework Selection Logic

The platform automatically selects the best framework based on:

**Task Complexity** - Measured in context requirements, reasoning depth

- Low complexity → LangGraph (Speed path)
- Medium complexity → CrewAI (Quality path)
- High complexity → AutoGen (Reliability path)

**Resource Requirements**

- Needs real-time code execution? → AutoGen
- Needs multi-step reasoning? → CrewAI
- Simple answer suffices? → LangGraph

**Cost Constraints**

- Budget optimization enabled? Platform chooses cheapest option
- Quality prioritized? Might override cost for better results
- Speed critical? Fast path preferred

**User Role & Permissions**

- Admin can override routing
- Data Scientists can set routing hints
- Regular users use default intelligent routing

### Data Layers Explained

**Milvus (Vector Memory Layer)**

Stores semantic embeddings of:
- Documents & PDFs (policies, guides, specifications)
- Code repositories (implementation examples, API docs)
- User knowledge (FAQs, best practices)

Enables: Semantic search, similarity matching, context retrieval

Example: User asks "How do I integrate OAuth?" → Milvus finds all related documentation

**ScyllaDB (Durable State Backbone)**

Stores:
- Session data (user active tasks, preferences)
- Job execution history (every task, every result)
- Audit logs (immutable record of all actions)
- Tenant configurations (settings, API keys, billing)

Enables: Historical analysis, compliance audit trails, state recovery

Example: Retrieve all tasks executed by a user in last 30 days

**DragonflyDB (Transient Brain)**

Stores (fast, non-persistent):
- Agent execution context (current variables, state)
- Tool results cache (avoid re-executing same tool)
- Short-term memory (conversation history)
- Real-time metrics (current queue length, latency)

Enables: Fast lookups, reduced latency, efficient memory usage

Example: Same question asked twice → DragonflyDB cache prevents re-execution

**PostgreSQL (Control Plane)**

Stores:
- User accounts & credentials
- Role definitions & permissions
- Billing records & payments
- API keys
- Strong consistency requirements

Enables: Authentication, authorization, billing accuracy

Example: Authenticate a user, verify their API quota

### Agent Roles & Responsibilities

**Researcher Agent** (CrewAI)
- Gathers information from knowledge base
- Searches external APIs if needed
- Synthesizes findings
- Used for: Market research, competitive analysis, documentation review

**Writer Agent** (CrewAI)
- Takes research and creates polished output
- Formats according to specifications
- Ensures consistency and quality
- Used for: Report generation, content creation, documentation

**Reviewer Agent** (CrewAI)
- Validates output quality
- Checks completeness
- Provides feedback for iterations
- Used for: QA, fact-checking, compliance verification

**Code Agent** (AutoGen)
- Writes code based on specifications
- Tests in sandbox environment
- Debugs and self-corrects
- Provides explanations
- Used for: Code generation, debugging, automation scripts

**Router Agent** (LangGraph)
- Analyzes incoming tasks
- Routes to appropriate framework
- Monitors resource availability
- Makes intelligent trade-offs
- Used for: Every request internally

### Understanding Results

Each task result includes:

**Main Output** - Answer/artifact/code generated

**Confidence Score** - How confident the agent is (0-100%)

**Execution Trace** - Step-by-step what the agent did

**Tool Usage** - Which tools/APIs were called

**Metadata** - Duration, cost, tokens used, framework selected

**Raw Data** - For technical users who want full details

---

## Hands-On Tutorials {#hands-on-tutorials}

### Tutorial 1: Create Your First Task

**Objective**: Submit a simple task and understand the workflow

**Time**: 10 minutes

**Steps**:

1. Log into the web application
2. Click **"New Task"** on the dashboard
3. Enter a simple query: "Summarize the benefits of machine learning"
4. Leave framework selection as "Auto"
5. Click **"Execute"**
6. Observe the progress bar showing execution stages
7. When complete, click **"View Results"**
8. Expand each section to understand the output
9. Click **"Feedback"** and rate the response quality
10. Click **"Download"** to save as PDF or JSON

**Key Learnings**: Task submission, result interpretation, quality feedback

### Tutorial 2: Upload Documents & Search

**Objective**: Teach the platform about your documents and search them semantically

**Time**: 20 minutes

**Steps**:

1. Click **"Knowledge Base"** in left menu
2. Click **"New Collection"** (e.g., "Company Policies")
3. Drag and drop 3-5 PDF files
4. Or click **"Upload"** and select files
5. Platform processes files (2-5 min depending on size)
6. Once complete, go to **"Search Documents"**
7. Enter a semantic query: "What's our vacation policy?"
8. Review search results (ranked by relevance)
9. Click on results to see where they came from
10. Use these in a task by selecting "Use Knowledge Base"

**Key Learnings**: Document ingestion, semantic search, knowledge base integration

### Tutorial 3: Configure Your Profile & Settings

**Objective**: Personalize your experience and set preferences

**Time**: 10 minutes

**Steps**:

1. Click your **Profile Icon** (top-right)
2. Select **"Settings"**
3. **General Tab**:
   - Update name, organization
   - Set timezone and language
   - Enable/disable notifications
4. **Security Tab**:
   - Review login history
   - Set up MFA if not done
   - Generate API key (if developer)
   - Set password strength requirements
5. **API Tab** (for developers):
   - View your API key
   - Set rate limits
   - Configure webhooks
6. **Preferences Tab**:
   - Default framework selection
   - Cost optimization priority
   - Auto-save history
7. Click **"Save"** at bottom

**Key Learnings**: Configuration options, API setup, security settings

### Tutorial 4: Create a Multi-Step Workflow (CrewAI)

**Objective**: Build a complex task requiring multi-agent collaboration

**Time**: 30 minutes

**Steps**:

1. Click **"Workflows"** in left menu
2. Click **"Create New Workflow"**
3. Name it: "Market Analysis Report"
4. Click **"Add Agent"**
5. Select **"Researcher"** type
6. Assign task: "Research top 5 AI companies, their funding, and market position"
7. Click **"Add Agent"** again
8. Select **"Writer"** type
9. Assign task: "Create professional report from research, include tables and charts"
10. Click **"Add Agent"** again
11. Select **"Reviewer"** type
12. Assign task: "Review report for accuracy and completeness"
13. Set dependencies (Reviewer depends on Writer, Writer depends on Researcher)
14. Click **"Preview"** to see execution flow
15. Click **"Execute"**
16. Watch the agents collaborate in real-time
17. When complete, download the final report

**Key Learnings**: Multi-agent workflows, agent collaboration, execution flow

### Tutorial 5: Monitor Task Performance & Costs

**Objective**: Understand your resource usage and optimize

**Time**: 15 minutes

**Steps**:

1. Click **"Analytics"** in left menu
2. **Dashboard Tab**:
   - View total tasks executed
   - See framework distribution (pie chart)
   - Check average response times
   - View cost trends
3. **Tasks Tab**:
   - Filter by date range, status, framework
   - Sort by duration, cost, complexity
   - Click a task to see detailed breakdown
4. **Cost Analysis Tab**:
   - View cost per framework
   - Cost per agent type
   - Cost trends over time
   - Identify expensive tasks
5. **Performance Tab**:
   - Average latency by endpoint
   - P50, P95, P99 latencies
   - Error rates and types
6. Export any report as CSV or PDF

**Key Learnings**: Analytics, cost tracking, performance monitoring

---

## Troubleshooting & FAQs {#troubleshooting}

### Common Issues & Solutions

**Issue: Task taking too long to execute**

*Possible Causes*:
- System under heavy load
- Task routed to AutoGen (longest but most reliable)
- Large document processing required
- API quota limits being hit

*Solutions*:
1. Check "System Status" dashboard for current load
2. Try same task at off-peak hours
3. Split large documents into smaller chunks
4. Contact admin to increase quota
5. Use "Speed Path" hint if quality can be sacrificed

**Issue: "Authentication Failed" error on login**

*Possible Causes*:
- Incorrect credentials
- MFA code expired (if using 2FA)
- Browser cookies disabled
- Session timeout

*Solutions*:
1. Verify you're using correct email/password
2. If MFA enabled, generate fresh code (don't use old code)
3. Clear browser cache and cookies, try again
4. Log out from other devices/browsers
5. Request password reset if forgotten
6. Contact admin if account locked

**Issue: Document upload fails**

*Possible Causes*:
- File too large (>100MB)
- Unsupported file format
- Connection interrupted
- Storage quota exceeded

*Solutions*:
1. Check file size is <100MB, split if needed
2. Use supported formats: PDF, TXT, DOCX, MD, JSON
3. Try from different network or browser
4. Contact admin to increase storage quota
5. Delete old unused documents first

**Issue: Mobile app crashes on startup**

*Possible Causes*:
- Incompatible OS version
- Corrupted cache
- Insufficient storage space
- Network connectivity issue

*Solutions*:
1. Verify OS version (iOS 12+, Android 8+)
2. Go to Settings > App Storage > Clear Cache
3. Free up at least 100MB of device storage
4. Ensure stable internet connection
5. Uninstall and reinstall app
6. Contact support with crash logs

**Issue: API calls returning 429 (Rate Limited)**

*Possible Causes*:
- Exceeded API rate limit
- Making too many requests in short time
- Quota reset hasn't occurred yet

*Solutions*:
1. Check your rate limits: Settings > API > View Limits
2. Implement exponential backoff in your code
3. Batch requests when possible
4. Request quota increase from admin
5. Wait until quota resets (usually midnight UTC)

**Issue: "Insufficient permissions" error**

*Possible Causes*:
- Your role doesn't allow this action
- Admin hasn't granted necessary permissions
- Feature restricted to certain roles

*Solutions*:
1. Check your current role: Settings > Account > View Role
2. Request specific permission from admin
3. Ask admin to upgrade your role
4. Use Admin account if you're admin
5. Contact support if you believe this is an error

### Frequently Asked Questions

**Q: What's the difference between the three frameworks?**

A: **LangGraph** is fastest and cheapest (direct LLM call). **CrewAI** is best for complex tasks needing multi-agent collaboration (slower but higher quality). **AutoGen** is most reliable with code execution and self-correction (slowest but most comprehensive).

**Q: How is my data secured?**

A: Data encrypted in transit (TLS 1.3) and at rest (AES-256). Role-based access control ensures only authorized users access data. Audit logs track all access. Compliance scanning ensures standards are met.

**Q: Can I use this offline?**

A: Web app requires internet. Mobile app supports offline mode - tasks queue locally and sync when connection returns.

**Q: What's included in the cost?**

A: API calls to LLMs, storage usage (per GB/month), computation time. Knowledge base ingestion, basic features, and standard analytics are free tier. Premium features (advanced analytics, custom agents, priority support) are paid.

**Q: How do I integrate with external systems?**

A: API authentication with JWT tokens, webhook support for event triggers, direct database queries via connection strings, OAuth 2.0 for third-party integrations.

**Q: Can I export my data?**

A: Yes - task results, analytics, audit logs all exportable as CSV/JSON/PDF. Contact admin for bulk exports or data migrations.

**Q: What's the uptime SLA?**

A: 99.9% uptime guaranteed. Redundant infrastructure across multiple regions. Real-time status page available.

**Q: How long are results retained?**

A: Results retained for 90 days default. Admins can configure retention policies (30/90/365 days or indefinite).

**Q: Can multiple users work on same task?**

A: Limited collaboration in current version. Workflows can be assigned to teams. Real-time collaboration coming in v2.

**Q: What happens if my quota is exceeded?**

A: Task execution fails with clear message. You can purchase additional quota immediately or wait for next reset period (usually daily).

---

## Best Practices {#best-practices}

### Query Formulation

**Be Specific**: "Generate Python code to read CSV file and calculate average" is better than "Write code"

**Provide Context**: Upload relevant documents before asking questions about them

**Use Examples**: Show the AI what good output looks like with examples

**Break Down Complex Tasks**: Instead of asking one complex question, ask step-by-step

Example:
```
Bad: "Analyze our business"
Good: "Analyze our Q3 revenue focusing on: 
  1. Total revenue vs Q2
  2. Revenue by product line
  3. Customer acquisition costs
  4. Churn rate trends"
```

### Document Management

**Organize Collections**: Group related documents (e.g., "Engineering Policies", "Customer Data")

**Use Consistent Formats**: Standardized documents easier to process

**Clean Up Old Documents**: Remove outdated or redundant documents

**Version Your Documents**: Include dates or version numbers

Example Structure:
```
Company-Wide Policies/
├─ 2025-Q1-Vacation-Policy-v2.pdf
├─ 2025-Q1-Remote-Work-Policy.pdf
└─ 2025-Q1-Security-Guidelines.pdf

Product-Docs/
├─ API-Reference-v3.md
├─ Quick-Start-Guide-v2.pdf
└─ Troubleshooting-Guide.md
```

### Workflow Design

**Start Simple**: Build basic workflows before complex ones

**Test Each Agent**: Before combining agents, test individually

**Monitor Costs**: Track which workflows are expensive and optimize

**Review Outputs**: Always check agent outputs for accuracy

**Set Clear Definitions**: Agent instructions should be specific and unambiguous

### API Best Practices

**Authentication**: Never hardcode API keys, use environment variables

**Error Handling**: Implement retry logic with exponential backoff

**Rate Limiting**: Design for rate limits, batch requests when possible

**Caching**: Use DragonflyDB results cache to avoid re-executing

**Monitoring**: Log all API calls for debugging and analysis

Example Python:
```python
import os
import time
import logging

API_KEY = os.environ.get("SUPER_AGENT_API_KEY")
MAX_RETRIES = 3
BASE_DELAY = 1  # seconds

def call_api_with_retry(endpoint, payload):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"https://api.superagent.com/{endpoint}",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RateLimited:
            wait_time = BASE_DELAY * (2 ** attempt)
            logging.warning(f"Rate limited, retry in {wait_time}s")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            logging.error(f"API error: {e}")
            raise
    
    raise Exception(f"API call failed after {MAX_RETRIES} attempts")
```

### Cost Optimization

**Use Speed Path for Simple Tasks**: Save quality/reliability for complex tasks

**Batch Similar Requests**: Process multiple documents in one batch

**Schedule During Off-Peak**: Run heavy jobs at nights/weekends (if using auto-scaling)

**Optimize Prompts**: Better prompts need fewer iterations

**Cache Results**: Don't re-execute same query multiple times

**Monitor Spending**: Set budget alerts with admin

---

## Advanced Configuration {#advanced-configuration}

### Setting Up Custom Agents

**For Data Scientists**:

1. Click **"Custom Agents"** in admin panel
2. Click **"Create Agent"**
3. Define agent properties:
   - Name: descriptive name
   - Type: Researcher/Writer/Reviewer/Custom
   - Base Model: Claude/GPT-4/Gemini/Local
   - System Prompt: detailed instructions for the agent
   - Tools: select which tools agent can use
   - Constraints: any limitations or guardrails
4. Define tools agent can use (APIs, functions, etc.)
5. Set up validation rules
6. Test with sample inputs
7. Deploy when ready

### Configuring Knowledge Base Integration

**For Data Scientists/Admins**:

1. Go to **"Knowledge Base"** settings
2. Select embedding model (OpenAI, Sentence Transformers, etc.)
3. Configure collection parameters:
   - Similarity threshold (default 0.7)
   - Max results returned (default 5)
   - Reranking enabled? (yes for better accuracy)
4. Set up ingestion pipeline:
   - Auto-extract text from PDFs? (yes)
   - Index code comments? (yes)
   - Chunk size (1024 tokens default)
   - Overlap between chunks (10% default)
5. Configure update frequency
6. Test with sample queries

### Setting Up Webhooks

**For Developers**:

1. Go to **"Integrations"** > **"Webhooks"**
2. Click **"New Webhook"**
3. Configure trigger events:
   - task_started
   - task_completed
   - task_failed
   - result_available
4. Enter webhook URL (must be publicly accessible)
5. Select which events trigger webhook
6. Add custom headers if needed
7. Test with "Send Test Event"
8. Active webhook is ready

Example webhook handler:
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/super-agent', methods=['POST'])
def handle_webhook():
    data = request.json
    event_type = data['event']
    
    if event_type == 'task_completed':
        task_id = data['task_id']
        result = data['result']
        # Process result, store in database, send notification, etc.
        print(f"Task {task_id} completed!")
        
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(port=5000)
```

### Multi-Tenancy Configuration

**For Admins**:

1. Create tenant in admin console
2. Configure tenant isolation:
   - Data: Separate schemas or row-level security
   - API: Tenant-specific API keys and rate limits
   - Storage: Dedicated or shared volume
3. Set tenant-specific features:
   - Available frameworks (LangGraph, CrewAI, AutoGen)
   - Knowledge base collections
   - Custom agents
   - Integrations
4. Configure billing for tenant
5. Assign tenant admins
6. Monitor tenant resource usage

---

## Getting Help

**In-App Help**: Click **"?"** icon in any screen for context-sensitive help

**Documentation**: Full API docs at https://docs.superagent.com

**Community**: Join Slack workspace for Q&A with other users

**Premium Support**: Email support@superagent.com for priority assistance

**Office Hours**: Weekly office hours Thursdays 2-3 PM UTC

**Issues & Bugs**: Report via GitHub or in-app bug reporter

---

## Next Steps

- Complete the role-specific training for your position
- Work through all hands-on tutorials
- Set up your knowledge base
- Configure your API integration
- Join the community Slack
- Attend next office hours

**Happy learning and building! 🚀**

---

*Last Updated: November 2025*  
*Next Review: February 2026*
