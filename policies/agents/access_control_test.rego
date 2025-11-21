package agents.access

import future.keywords.if

# Test admin access
test_admin_allow if {
    allow with input as {
        "user": {"roles": ["admin"]},
        "agent": {"agent_id": "test_agent"},
    }
}

# Test agent operator access with allowed category
test_agent_operator_allow if {
    allow with input as {
        "user": {
            "roles": ["agent_operator"],
            "permissions": {"allowed_categories": ["business_ops"]},
        },
        "agent": {"category": "business_ops"},
    }
}

# Test developer access in development environment
test_developer_allow if {
    allow with input as {
        "user": {"roles": ["developer"]},
        "agent": {"agent_id": "test_agent"},
        "environment": "development",
    }
}

# Test user access with specific permission
test_user_allow if {
    allow with input as {
        "user": {
            "roles": ["user"],
            "permissions": {"allowed_agents": ["test_agent"]},
        },
        "agent": {"agent_id": "test_agent"},
    }
}

# Test default deny
test_default_deny if {
    not allow with input as {
        "user": {"roles": []},
        "agent": {"agent_id": "test_agent"},
    }
}

# Test PII access denial
test_pii_access_deny if {
    count(deny) > 0 with input as {
        "user": {
            "roles": ["user"],
            "permissions": {"pii_access": false},
        },
        "agent": {
            "agent_id": "test_agent",
            "capabilities": ["pii_access"],
        },
    }
}

# Test financial data access denial
test_financial_data_deny if {
    count(deny) > 0 with input as {
        "user": {
            "roles": ["user"],
            "permissions": {"financial_data_access": false},
        },
        "agent": {"category": "finance_legal"},
    }
}

# Test HR data access denial
test_hr_data_deny if {
    count(deny) > 0 with input as {
        "user": {
            "roles": ["user"],
            "permissions": {"hr_data_access": false},
        },
        "agent": {"category": "hr_people"},
    }
}

# Test GDPR compliance
test_gdpr_compliance if {
    count(deny) > 0 with input as {
        "user": {
            "roles": ["user"],
            "region": "EU",
            "gdpr_consent": false,
        },
        "agent": {
            "agent_id": "test_agent",
            "capabilities": ["pii_access"],
        },
    }
}

# Test audit required for sensitive agents
test_audit_required_finance if {
    audit_required with input as {
        "agent": {"category": "finance_legal"},
    }
}

test_audit_required_hr if {
    audit_required with input as {
        "agent": {"category": "hr_people"},
    }
}

test_audit_required_healthcare if {
    audit_required with input as {
        "agent": {"category": "healthcare_wellness"},
    }
}

test_audit_required_pii if {
    audit_required with input as {
        "agent": {"capabilities": ["pii_access"]},
    }
}

# Test SOC2 compliance - audit logging must be enabled
test_soc2_audit_logging if {
    count(deny) > 0 with input as {
        "agent": {"category": "finance_legal"},
        "audit_enabled": false,
    }
}
