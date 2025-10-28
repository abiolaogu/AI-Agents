import os
from services.crm_data_entry_agent.app import app

if __name__ == "__main__":
    port = int(os.environ.get("AGENT_PORT", 5001))
    app.run(host='0.0.0.0', port=port)