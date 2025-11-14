# Agent Access Control Policy
# Defines who can execute which agents and under what conditions

package agents.access

import future.keywords.if
import future.keywords.in
import data.roles
import data.agent_categories

# Default deny
default allow = false
default deny = []

# ============================================================================
# RBAC (Role-Based Access Control)
# ============================================================================

# Admins can execute any agent
allow if {
    "admin" in input.user.roles
}

# Agent operators can execute agents in their permitted categories
allow if {
    "agent_operator" in input.user.roles
    input.agent.category in input.user.permissions.allowed_categories
}

# Developers can execute agents in development mode
allow if {
    "developer" in input.user.roles
    input.environment == "development"
}

# Users can execute specific agents based on permissions
allow if {
    "user" in input.user.roles
    input.agent.agent_id in input.user.permissions.allowed_agents
}

# ============================================================================
# Rate Limiting
# ============================================================================

# Check if user has exceeded rate limit
rate_limit_exceeded if {
    count(user_requests_last_hour(input.user.id)) > user_rate_limit(input.user.id)
}

deny contains msg if {
    rate_limit_exceeded
    msg := sprintf("Rate limit exceeded for user %v. Limit: %v requests/hour",
        [input.user.id, user_rate_limit(input.user.id)])
}

# Helper: Get user's rate limit
user_rate_limit(user_id) := limit if {
    user := data.users[user_id]
    limit := user.rate_limit
} else := 100  # Default rate limit

# Helper: Mock function for recent requests (would connect to real data)
user_requests_last_hour(user_id) := [] if {
    # TODO: Connect to Redis/Database for real request history
    true
}

# ============================================================================
# Data Access Control
# ============================================================================

# Deny access to PII data without permission
deny contains msg if {
    "pii_access" in input.agent.capabilities
    not input.user.permissions.pii_access
    msg := "User lacks permission to access PII data"
}

# Deny access to financial data without permission
deny contains msg if {
    input.agent.category == "finance_legal"
    not input.user.permissions.financial_data_access
    msg := "User lacks permission to access financial data"
}

# Deny access to HR data without permission
deny contains msg if {
    input.agent.category == "hr_people"
    not input.user.permissions.hr_data_access
    msg := "User lacks permission to access HR data"
}

# ============================================================================
# Agent-Specific Policies
# ============================================================================

# High-risk agents require additional approval
deny contains msg if {
    input.agent.agent_id in data.high_risk_agents
    not input.approval_token
    msg := sprintf("Agent %v requires approval token", [input.agent.agent_id])
}

# Production agents cannot be used in development environment
deny contains msg if {
    "production_only" in input.agent.tags
    input.environment == "development"
    msg := "Production-only agent cannot be used in development"
}

# ============================================================================
# Quota Management
# ============================================================================

# Check if user has exceeded monthly quota
monthly_quota_exceeded if {
    user_monthly_usage(input.user.id) > user_monthly_quota(input.user.id)
}

deny contains msg if {
    monthly_quota_exceeded
    msg := sprintf("Monthly quota exceeded for user %v", [input.user.id])
}

user_monthly_quota(user_id) := quota if {
    user := data.users[user_id]
    quota := user.monthly_quota
} else := 1000  # Default monthly quota

user_monthly_usage(user_id) := 0 if {
    # TODO: Connect to usage tracking system
    true
}

# ============================================================================
# Time-Based Restrictions
# ============================================================================

# Restrict access to certain agents during business hours only
deny contains msg if {
    "business_hours_only" in input.agent.tags
    not is_business_hours
    msg := "This agent can only be used during business hours (9 AM - 5 PM EST)"
}

is_business_hours if {
    # TODO: Implement actual time checking
    true
}

# ============================================================================
# Team Collaboration Policies
# ============================================================================

# Allow team execution if all team members are permitted
allow_team if {
    input.action == "execute_team"
    all_members_allowed
}

all_members_allowed if {
    count(denied_members) == 0
}

denied_members contains member_id if {
    member := input.team.members[_]
    member_id := member.agent_id
    not agent_allowed_for_user(member_id, input.user)
}

agent_allowed_for_user(agent_id, user) if {
    # Simplified check - would use full policy evaluation
    agent := data.agents[agent_id]
    agent.category in user.permissions.allowed_categories
}

# ============================================================================
# Audit Requirements
# ============================================================================

# Always audit these sensitive agent executions
audit_required if {
    input.agent.category in ["finance_legal", "hr_people", "healthcare_wellness"]
}

audit_required if {
    "pii_access" in input.agent.capabilities
}

audit_required if {
    input.agent.agent_id in data.high_risk_agents
}

# ============================================================================
# Compliance Rules
# ============================================================================

# GDPR compliance: Check user consent for EU users
deny contains msg if {
    input.user.region == "EU"
    "pii_access" in input.agent.capabilities
    not input.user.gdpr_consent
    msg := "GDPR consent required for PII access in EU region"
}

# HIPAA compliance: Healthcare agents require certified users
deny contains msg if {
    input.agent.category == "healthcare_wellness"
    not input.user.certifications.hipaa
    msg := "HIPAA certification required for healthcare agents"
}

# SOC2 compliance: Audit logging must be enabled
deny contains msg if {
    audit_required
    not input.audit_enabled
    msg := "Audit logging must be enabled for this agent"
}
