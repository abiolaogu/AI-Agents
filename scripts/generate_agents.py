import json
import os

CATEGORIES = {
    "HR": ["Recruitment", "Onboarding", "Payroll", "EmployeeRelations", "Benefits", "Compliance", "Training", "PerformanceReview", "ExitInterview", "TalentAcquisition"],
    "Finance": ["Invoicing", "Tax", "Auditing", "Budgeting", "ExpenseTracking", "FinancialReporting", "RiskAssessment", "InvestmentAnalysis", "PayrollProcessing", "AccountsPayable"],
    "Sales": ["LeadGen", "CRM", "Closing", "ColdOutreach", "AccountManagement", "SalesForecasting", "PipelineManagement", "CustomerSuccess", "Upselling", "ContractNegotiation"],
    "Marketing": ["SocialMedia", "SEO", "ContentCreation", "EmailMarketing", "AdCampaigns", "MarketResearch", "BrandManagement", "PR", "EventMarketing", "Analytics"],
    "IT": ["Support", "Security", "DevOps", "NetworkAdmin", "DatabaseAdmin", "SoftwareDevelopment", "QA", "SystemArchitecture", "CloudManagement", "HelpDesk"],
    "Legal": ["Compliance", "Contracts", "IP", "Litigation", "CorporateGovernance", "EmploymentLaw", "MergersAcquisitions", "Privacy", "RealEstate", "Regulatory"],
}

OUTPUT_DIR = "/Users/AbiolaOgunsakin1/AI-Agents/AI-Agents/agents/definitions"

def generate_agents():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    count = 0
    for category, roles in CATEGORIES.items():
        for role in roles:
            agent_id = f"{category.lower()}_{role.lower()}_agent_001"
            agent_name = f"{category} {role} Agent"
            
            # In a real scenario, these would point to actual services or a generic runner
            # For now, we point them to a generic runner or the existing ones if they match
            url = "http://generic-agent:5000"
            if "seo" in agent_id:
                url = "http://seo-agent:5001"
            
            agent_def = {
                "id": agent_id,
                "name": agent_name,
                "description": f"AI Agent specialized in {role} tasks for the {category} department.",
                "category": category,
                "url": url,
                "capabilities": [role.lower(), "text_generation", "data_analysis"],
                "version": "1.0.0"
            }
            
            filename = os.path.join(OUTPUT_DIR, f"{agent_id}.json")
            with open(filename, 'w') as f:
                json.dump(agent_def, f, indent=2)
            
            print(f"Generated {filename}")
            count += 1
            
    print(f"Successfully generated {count} agent definitions.")

if __name__ == "__main__":
    generate_agents()
