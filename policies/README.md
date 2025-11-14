# Policy as Code - AI Agents Platform

This directory contains all policy definitions for the AI Agents Platform using Open Policy Agent (OPA).

## Structure

```
policies/
├── agents/          # Agent execution policies
│   ├── access_control.rego
│   └── rate_limiting.rego
├── data/            # Policy data
│   ├── roles.json
│   └── users.json
├── workflows/       # Workflow policies
│   └── workflow_policies.rego
├── security/        # Security policies
│   └── security_policies.rego
└── README.md
```

## Policies

### 1. Agent Access Control (`agents/access_control.rego`)

Controls who can execute which agents based on:
- **RBAC (Role-Based Access Control)**: Users assigned roles with specific permissions
- **Rate Limiting**: Prevents abuse with per-user request limits
- **Data Access Control**: Restricts access to sensitive data (PII, financial, HR)
- **Agent-Specific Policies**: High-risk agents require additional approval
- **Quota Management**: Monthly usage quotas per user
- **Time-Based Restrictions**: Some agents only available during business hours
- **Team Collaboration**: Validates all team members have required permissions
- **Compliance Rules**: GDPR, HIPAA, SOC2 compliance checks

### 2. Roles and Permissions (`data/roles.json`)

Predefined roles:
- **admin**: Full system access
- **agent_operator**: Category-based access
- **developer**: Development environment access
- **user**: Standard user access
- **finance_team**: Finance department access
- **hr_team**: HR department access
- **sales_team**: Sales and marketing access
- **support_team**: Customer support access

## Usage

### Testing Policies Locally

```bash
# Install OPA
brew install opa  # macOS
# or
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x opa

# Run OPA server
opa run --server --addr :8181 policies/

# Test a policy
curl -X POST http://localhost:8181/v1/data/agents/access/allow \
  -H 'Content-Type: application/json' \
  -d '{
    "input": {
      "user": {
        "id": "user_123",
        "roles": ["user"],
        "permissions": {
          "allowed_categories": ["business_ops"]
        }
      },
      "agent": {
        "agent_id": "executive_summary_agent_001",
        "category": "business_ops",
        "capabilities": ["text_summarization"]
      },
      "environment": "production",
      "audit_enabled": true
    }
  }'
```

### Running OPA in Docker

```bash
# Run OPA with policies
docker run -p 8181:8181 -v $(pwd)/policies:/policies \
  openpolicyagent/opa:latest \
  run --server --addr :8181 /policies
```

### Deploying to RunPod

OPA is automatically deployed as a sidecar container with the main application.

## Policy Evaluation Flow

```
1. User requests agent execution
2. Request intercepted by Policy Enforcer
3. OPA evaluates policies with request context
4. Policy decision:
   - allow = true  → Execute agent
   - allow = false → Return policy denial with reasons
5. If allowed, execution proceeds
6. Audit log created for sensitive operations
```

## Adding New Policies

To add a new policy:

1. Create a `.rego` file in the appropriate directory
2. Define the policy using Rego language
3. Test the policy locally
4. Add policy data to `data/` if needed
5. Update this README
6. Deploy via CI/CD

Example policy:

```rego
package custom.policy

import future.keywords.if

# Allow only on weekdays
allow if {
    is_weekday(input.timestamp)
}

is_weekday(timestamp) if {
    day := time.weekday(timestamp)
    day >= 1  # Monday
    day <= 5  # Friday
}
```

## Policy Best Practices

1. **Default Deny**: Always start with `default allow = false`
2. **Explicit Permits**: Explicitly define what is allowed
3. **Least Privilege**: Grant minimum necessary permissions
4. **Audit Everything**: Log all policy decisions
5. **Test Thoroughly**: Write tests for all policy paths
6. **Version Control**: Track all policy changes in git
7. **Documentation**: Document why each policy exists

## Compliance

Policies ensure compliance with:
- **GDPR**: Data protection and privacy
- **HIPAA**: Healthcare data security
- **SOC2**: Security and availability
- **ISO 27001**: Information security
- **PCI DSS**: Payment card data (if applicable)

## Monitoring and Alerts

Policy violations trigger alerts:
- Rate limit exceeded
- Unauthorized access attempts
- Compliance violations
- High-risk agent executions without approval

## Emergency Override

In emergencies, admins can override policies:

```bash
# Temporary policy bypass (logged and audited)
curl -X POST /v1/agents/execute \
  -H 'X-Admin-Override: true' \
  -H 'X-Override-Reason: Production incident #123' \
  -d '...'
```

All overrides are:
- Logged in audit trail
- Require reason
- Time-limited (1 hour)
- Reviewed in security reports

## Resources

- [OPA Documentation](https://www.openpolicyagent.org/docs/)
- [Rego Language Guide](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [Policy Testing](https://www.openpolicyagent.org/docs/latest/policy-testing/)
- [Integration Guide](https://www.openpolicyagent.org/docs/latest/integration/)
