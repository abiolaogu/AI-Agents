# Administrator Manual
## Multi-Framework Super-Agent Platform

**Version:** 1.0  
**Audience:** System Administrators  
**Last Updated:** November 2025  

---

## Table of Contents

1. [Administrator Dashboard Overview](#dashboard)
2. [User & Role Management](#user-management)
3. [Tenant Configuration](#tenant-config)
4. [API Keys & Security](#api-keys)
5. [Billing & Quota Management](#billing)
6. [Integration Setup](#integrations)
7. [Monitoring & Maintenance](#monitoring)
8. [Compliance & Audit](#compliance)
9. [Disaster Recovery](#disaster-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Administrator Dashboard Overview {#dashboard}

As an administrator, you have access to the complete system management interface. Your dashboard displays:

**System Health Panel**
- Platform uptime percentage (SLA: 99.9%)
- Active users count
- Current API requests/second
- Database replication status
- Backup status

**Quick Actions**
- Add User
- Create Tenant
- View Audit Logs
- Generate Reports
- Manage Integrations

**Key Metrics**
- Total API calls (daily/monthly)
- Storage used / total allocated
- Active workflows
- Cost accrual (actual vs. budget)

**Alerts Section**
- Critical alerts (system issues)
- Warning alerts (quota approaching)
- Informational alerts (maintenance scheduled)

---

## User & Role Management {#user-management}

### Creating Users

**Steps**:

1. Navigate to **Admin** > **Users**
2. Click **"Add User"** button
3. Fill in user information:
   - Email address (primary key)
   - First name & Last name
   - Organization (optional)
   - Department (optional)

4. Select role:
   - **Admin**: Full system access, can manage users and settings
   - **Analyst**: Can view all data, create workflows, limited admin capabilities
   - **Data Scientist**: Can build agents, manage knowledge base, create workflows
   - **Developer**: API access, can create custom tools, manage webhooks
   - **User**: Basic task execution, personal knowledge base only
   - **Service Account**: For API-only access, no UI login

5. Set initial permissions:
   - Framework access (LangGraph/CrewAI/AutoGen)
   - API quota (requests/month)
   - Storage quota (GB/month)
   - Knowledge base access (own/team/enterprise)

6. Choose authentication method:
   - Automatic invite email
   - Manual password assignment
   - SSO integration

7. Click **"Create User"**

**Bulk User Import**:
- Click **"Import Users"**
- Download CSV template
- Fill with users:
  ```
  email,first_name,last_name,role,department
  john@company.com,John,Doe,Data Scientist,Analytics
  jane@company.com,Jane,Smith,Developer,Engineering
  ```
- Upload CSV file
- Review and confirm

### Managing User Permissions

**Individual User Permissions**:

1. Click on user in Users list
2. **Permissions Tab**:
   - Framework access checkboxes (LangGraph/CrewAI/AutoGen)
   - API quota slider
   - Storage quota slider
   - Feature toggles (Knowledge Base, Custom Agents, Webhooks, etc.)
   - Billing visibility toggle

3. **Rate Limits Tab**:
   - Requests per minute
   - Requests per hour
   - Requests per day
   - Concurrent requests

4. **Data Access Tab**:
   - Knowledge base collections (which ones user can access)
   - Workflow visibility (own/team/all)
   - Tenant data access (for multi-tenant admins)

5. Click **"Save Changes"**

**Batch Permission Updates**:

1. Click **"Permissions"** in Admin menu
2. Select users via checkboxes or search
3. Choose action:
   - Increase API quota by X
   - Add framework access
   - Assign to team
   - Grant specific feature access
4. Click **"Apply to Selected"**

### Role-Based Access Control (RBAC)

**Built-in Roles**:

| Role | Dashboard | Tasks | Workflows | Users | Billing | Security |
|------|-----------|-------|-----------|-------|---------|----------|
| Admin | Full | Full | Full | Full | Full | Full |
| Analyst | Full | Full | Full | View | View | View |
| Data Scientist | Full | Full | Full | - | Own only | - |
| Developer | API Only | API | API | - | Own only | - |
| User | Limited | Own only | Own only | - | View | - |
| Service Account | API Only | API | API | - | - | - |

**Custom Roles**:

1. Go to **Admin** > **Roles**
2. Click **"Create Custom Role"**
3. Name: e.g., "Analyst+ (Premium)"
4. Select permissions:
   - Framework access: ☐ LangGraph ☐ CrewAI ☐ AutoGen
   - Quotas: Set defaults
   - Features: Which features available
   - Data access: Which data visible
5. Assign existing users to role
6. Save

---

## Tenant Configuration {#tenant-config}

### Multi-Tenant Setup

The platform supports multiple isolated tenants. Each tenant has:
- Isolated data
- Dedicated API keys
- Tenant-specific features
- Billing per tenant

**Create Tenant**:

1. Go to **Admin** > **Tenants**
2. Click **"Create Tenant"**
3. Configure:
   - Tenant name (e.g., "Acme Corp")
   - Subdomain (e.g., acme.superagent.com)
   - Default tier (Free/Professional/Enterprise)
   - Owner email
   - Data residency (US/EU/APAC)

4. Features to enable:
   - ☐ Knowledge Base (Milvus)
   - ☐ Custom Agents
   - ☐ Webhooks
   - ☐ API Access
   - ☐ Single Sign-On
   - ☐ Advanced Analytics

5. Set quotas:
   - API calls/month: ___
   - Storage GB/month: ___
   - Concurrent jobs: ___
   - Users allowed: ___

6. Click **"Create Tenant"**

### Tenant Settings

**For Each Tenant**:

1. Click tenant in list
2. **General Settings**:
   - Tenant name
   - Description
   - Logo/branding
   - Contact email
   - Support URL

3. **Features Tab**:
   - Toggle features on/off
   - Configure feature parameters

4. **Security Tab**:
   - IP whitelist (optional)
   - Forced 2FA requirement
   - Session timeout
   - Password complexity rules

5. **Integration Tab**:
   - OAuth providers to allow
   - SAML configuration
   - API key format

6. **Billing Tab**:
   - Current tier
   - Pricing model
   - Monthly charge
   - Billing email
   - Payment method

---

## API Keys & Security {#api-keys}

### Managing API Keys

**Generate API Key**:

1. Go to **Admin** > **API Keys**
2. Click **"Generate Key"**
3. Name: Descriptive name (e.g., "Production Server")
4. Permissions: Select what this key can do
   - ☐ Create tasks
   - ☐ View results
   - ☐ Manage knowledge base
   - ☐ Create workflows
5. Rate limit: Requests/second this key can make
6. Expiration: Never / 30 days / 90 days / 1 year
7. Click **"Generate"**
8. Copy key immediately (won't be shown again)
9. Store securely (e.g., HashiCorp Vault)

**Revoke API Key**:
1. Click key in list
2. Click **"Revoke"**
3. Confirm - key immediately stops working

**Rotate API Key**:
1. Click key in list
2. Click **"Rotate"**
3. New key generated
4. Old key works for 24 hours (grace period)
5. Update your applications during grace period

### Security Settings

**Authentication Methods**:

1. Go to **Admin** > **Security**
2. **Password Policy**:
   - Minimum length (default: 12 chars)
   - Require uppercase: Yes/No
   - Require numbers: Yes/No
   - Require special chars: Yes/No
   - Password expiration: Never / 90 days / 180 days

3. **Multi-Factor Authentication (MFA)**:
   - Require for admins: Yes/No
   - Require for all users: Yes/No
   - Allowed methods: TOTP / SMS / Email
   - Grace period for compliance (days)

4. **Session Management**:
   - Session timeout (minutes): ___ (default: 30)
   - Remember device for: ___ days (0 = always ask)
   - Concurrent sessions per user: ___ (default: 5)

5. **IP Whitelist** (Enterprise):
   - Add trusted IPs
   - Block all other IPs
   - Grace period for new IPs

6. **Encryption**:
   - TLS version (1.2/1.3)
   - Force HTTPS: Yes/No
   - Certificate renewal: Auto/Manual

### Audit Logging

All admin actions are logged for compliance:

**View Audit Logs**:

1. Go to **Admin** > **Audit Logs**
2. Filter by:
   - Date range
   - Admin user
   - Action type (Create/Read/Update/Delete)
   - Resource type (User/Tenant/API Key, etc.)
   - Status (Success/Failure)

3. Click log entry for details

**Export Audit Log**:

1. Set filters for desired timeframe
2. Click **"Export"**
3. Choose format: CSV / JSON / PDF
4. Download file

**Audit Log Retention**:
- Default: 90 days
- Can be configured to: 30/90/365 days or indefinite
- Set in **Settings** > **Compliance**

---

## Billing & Quota Management {#billing}

### Understanding Costs

The platform charges for:

- **API Calls**: $0.001-0.01 per call (varies by framework selected)
- **Storage**: $0.10 per GB per month (documents in Milvus)
- **Compute**: Included (RunPod covers)
- **Premium Features**: $99/month (custom agents, advanced analytics)

**Cost Calculation**:
```
Total Monthly = (API Calls × Rate) + (Storage GB × $0.10)
              + (Premium Features if enabled)
```

### Setting Quotas

**Per User**:

1. Go to **Admin** > **Users**
2. Click user
3. **Quota Tab**:
   - API calls/month: ___ (e.g., 10,000)
   - Storage GB/month: ___ (e.g., 5)
   - Concurrent jobs: ___ (e.g., 5)
4. Save

**Per Tenant**:

1. Go to **Admin** > **Tenants**
2. Click tenant
3. **Billing Tab**:
   - Set tenant-wide quotas
   - These are limits that cannot be exceeded

**Organization-Wide**:

1. Go to **Admin** > **Settings** > **Billing**
2. Set organization quotas:
   - Total API calls/month for entire organization
   - Total storage/month
   - Total cost budget/month

### Monitoring Quota Usage

**Daily Dashboard**:

1. Each user sees their usage on dashboard:
   - "API Calls: 2,450 / 10,000 (24.5%)"
   - "Storage: 1.2 GB / 5 GB (24%)"

2. Admin dashboard shows:
   - Organization-wide usage
   - Per-user breakdown
   - Per-tenant breakdown

**Quota Alerts**:

Set alerts in **Settings** > **Alerts**:
- Alert when quota reaches: 50% / 75% / 90%
- Alert recipients: admin email(s)
- Alert frequency: Daily / Weekly / When threshold reached

**Exceeded Quota Handling**:

1. When user reaches 100% quota:
   - Soft limit: Task executes but user sees warning
   - Hard limit: Task rejected with "Quota exceeded" error
   - Configure which in **Settings** > **Quota Rules**

2. Options for user:
   - Purchase additional quota immediately (self-serve)
   - Request quota increase (admin approval)
   - Wait until quota resets (monthly)

### Billing Cycle & Payments

**Billing Cycle**:
- Monthly: Charges on 1st of month for previous month
- Usage tracked: 1st of month to last day
- Invoice generated: Within 24 hours of billing date

**View Billing**:
1. Go to **Admin** > **Billing** > **Invoices**
2. Filter by date range
3. Click invoice to view details
4. Download PDF for accounting

**Payment Methods**:
1. Go to **Admin** > **Billing** > **Payment Method**
2. Add payment method:
   - Credit card (Visa/MC/Amex)
   - Bank transfer (ACH for US)
   - Wire transfer (international)
3. Set as default
4. Add backup payment method

**Cost Forecasting**:
1. Go to **Admin** > **Analytics** > **Cost Forecast**
2. Shows:
   - Current month spending
   - Projected month-end cost
   - Trend vs. previous months
   - Alerts if trending high

---

## Integration Setup {#integrations}

### SSO Configuration

**OAuth 2.0 (Google, GitHub)**:

1. Go to **Admin** > **Integrations** > **OAuth**
2. Select provider (Google / GitHub)
3. Get OAuth credentials from provider:
   - For Google: Google Cloud Console
   - For GitHub: GitHub Settings > Developer Settings
4. In super-agent platform, paste:
   - Client ID
   - Client Secret
5. Set redirect URL: (provided by platform)
6. Enable OAuth: Yes
7. Click **"Save"**

**SAML 2.0 (Enterprise)**:

1. Go to **Admin** > **Integrations** > **SAML**
2. Get metadata from your SAML provider (Okta, AzureAD)
3. Provide platform metadata to provider
4. Configure attribute mapping:
   - Email → email (required)
   - FirstName → first_name
   - LastName → last_name
   - Roles → role (optional)
5. Enable SAML: Yes
6. Save

### Email Integration

1. Go to **Admin** > **Integrations** > **Email**
2. Choose email provider:
   - SendGrid
   - AWS SES
   - Mailgun
3. Enter API credentials:
   - API Key
   - Domain
   - Sender email
4. Test email: Click "Send Test Email"
5. Save when working

### Webhook Configuration

1. Go to **Admin** > **Integrations** > **Webhooks**
2. Click **"Add Webhook"**
3. Configure:
   - Name: descriptive
   - URL: where to send data
   - Events to trigger: task_completed, task_failed, etc.
   - Active: Yes/No
4. Test: Click "Send Test Event"
5. Save

### Monitoring Integrations

1. Go to **Admin** > **Integrations** > **Monitor**
2. See status of each integration:
   - Green: Working
   - Yellow: Warning
   - Red: Error
3. Click to see logs and errors
4. Debug issues as needed

---

## Monitoring & Maintenance {#monitoring}

### System Monitoring

**Metrics Dashboard**:

1. Go to **Admin** > **Monitoring**
2. View real-time metrics:
   - CPU usage (target: <70%)
   - Memory usage (target: <80%)
   - Database connections (target: <80% of pool)
   - Request latency (target: <2 seconds avg)
   - Error rate (target: <0.1%)

3. Historical view (24h/7d/30d)
4. Export metrics for external monitoring tools

**Alerts & Notifications**:

1. Go to **Admin** > **Alerts**
2. Create alert rule:
   - Metric: (CPU, Memory, Latency, Error Rate)
   - Threshold: (e.g., CPU > 80%)
   - Duration: (e.g., sustained for 5 minutes)
   - Action: Send email / SMS / PagerDuty
3. Recipients: (email addresses)
4. Save

### Backup & Recovery

**Automated Backups**:

Scheduled daily at 2 AM UTC:
- Databases (PostgreSQL, ScyllaDB, Milvus)
- User files and documents
- Configuration
- Audit logs

**View Backups**:

1. Go to **Admin** > **Backup**
2. See list of recent backups with:
   - Timestamp
   - Size
   - Status (Success/Failed)
   - Restore option

**Manual Backup**:

1. Go to **Admin** > **Backup**
2. Click **"Create Backup Now"**
3. Backup created (takes 5-10 minutes)
4. Available for 30 days

**Restore from Backup**:

**WARNING**: Restoration is destructive - affects all current data

1. Go to **Admin** > **Backup**
2. Click backup to restore
3. Click **"Restore"**
4. Confirm (type "RESTORE" to proceed)
5. System restores from selected backup
6. Takes 10-20 minutes depending on size
7. All users logged out during restore

### Maintenance Windows

**Planned Maintenance**:

1. Announced 14 days before
2. Typically: Sunday 2-4 AM UTC
3. System unavailable 30-120 minutes
4. Users see maintenance page
5. Scheduled for updates/patches

**Emergency Maintenance**:

1. If critical issue detected
2. Maintenance started immediately
3. Users notified via email
4. Status page updated in real-time

---

## Compliance & Audit {#compliance}

### Compliance Scanning

**OpenSCAP Compliance**:

1. Go to **Admin** > **Compliance** > **OpenSCAP**
2. See compliance status for:
   - CIS Benchmarks (0-100%)
   - DISA STIG (0-100%)
   - PCI-DSS (if applicable)
3. Failed controls listed with:
   - Issue description
   - Remediation steps
   - Severity (Critical/High/Medium/Low)
4. Run scan: Click "Scan Now" (takes 15-30 min)
5. Download report as PDF

**Container Security**:

1. Go to **Admin** > **Compliance** > **Container Security**
2. Trivy vulnerability scan results:
   - Critical vulnerabilities count
   - High severity issues
   - Remediation available: Yes/No
3. Grype additional analysis
4. Run scan: Click "Scan Now"

**Code Security**:

1. Go to **Admin** > **Compliance** > **Code Security**
2. SonarQube results:
   - Code smells
   - Security hotspots
   - Bugs
   - Technical debt
3. Each issue links to code location

### Data Privacy & GDPR

**GDPR Compliance**:

1. Go to **Admin** > **Privacy** > **GDPR**
2. Features enabled:
   - Data export: Users can export their data
   - Right to be forgotten: Users can request deletion
   - Consent management: Track user consents

3. Handle user data requests:
   - Filter by user email
   - Request type (Export / Delete / Other)
   - Status (Pending / In Progress / Complete)
   - Download result when ready

### Audit Reports

**Generate Audit Report**:

1. Go to **Admin** > **Reports** > **Audit**
2. Configure:
   - Report type: (Full / By User / By Tenant / By Feature)
   - Date range
   - Include: Actions / Changes / Access / Errors
3. Generate: PDF / CSV
4. Download when ready

---

## Disaster Recovery {#disaster-recovery}

### Recovery Procedures

**Database Corruption Recovery**:

1. Check **Admin** > **Monitoring** > **Database Health**
2. If issues detected:
   - Stop all user traffic (use Admin > Pause System)
   - Run database check: **Admin** > **Maintenance** > **Check Database**
   - Automatic repair attempted
   - If failed, restore from latest backup

3. Recovery steps:
   - Contact support
   - Prepare business impact statement
   - Authorize backup restore
   - Restore selected backup
   - Verify data integrity
   - Resume traffic

**Service Failure Recovery**:

If main service fails:
1. Status automatically shows "Degraded" or "Offline"
2. Failover to backup server (automatic)
3. Users may experience slowness but retain access
4. Engineering team alerted automatically
5. Incident investigation begins

### Business Continuity

**Disaster Recovery Plan**:

Current configuration:
- Primary: RunPod cluster (US)
- Backup: Multi-region redundancy
- Failover: Automatic (< 1 minute)
- Recovery Point Objective (RPO): < 5 minutes
- Recovery Time Objective (RTO): < 1 minute

---

## Troubleshooting {#troubleshooting}

### Common Admin Issues

**Issue: User can't log in**

Solutions:
1. Check user account status: **Users** > Click user > Status
2. If inactive, click **"Activate"**
3. If password reset needed: Click **"Reset Password"**
4. User receives email with reset link
5. Check if MFA is blocking (if recently enabled)

**Issue: API calls failing with 401 Unauthorized**

Solutions:
1. Check API key hasn't been revoked
2. Check API key hasn't expired
3. Verify API key being used is correct (full key with prefix)
4. Check rate limits: Admin > API Keys > View this key's limits
5. Test with test API key to isolate issue

**Issue: System running slowly**

Solutions:
1. Check system metrics: Admin > Monitoring
   - If CPU >80% or Memory >90%, scale up
   - Contact RunPod support for resource increase
2. Check database performance:
   - Admin > Monitoring > Database
   - Look for slow queries
   - May need indexing
3. Clear caches: Admin > Maintenance > Clear Cache
4. Check for runaway workflows/jobs

**Issue: Knowledge base search returning poor results**

Solutions:
1. Check document ingestion completed: Admin > Knowledge Base > Status
2. Reindex collection: Admin > Knowledge Base > Reindex
3. Check embedding model quality
4. Verify query is specific enough
5. Add more documents to improve coverage

---

## Support & Escalation

**Getting Help**:
- Email: support@superagent.com
- Priority support available for Enterprise tier
- Office hours: Thursdays 2-3 PM UTC
- Slack community: (link in dashboard)

**Reporting Issues**:
1. Go to **Admin** > **Support**
2. Click **"Report Issue"**
3. Include:
   - Problem description
   - Steps to reproduce
   - Screenshots if applicable
   - System metrics (if relevant)
4. Submit - support ticket created
5. Check email for ticket number

---

**Last Updated**: November 2025  
**Next Review**: February 2026
