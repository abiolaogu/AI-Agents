import os
from services.brand_voice_consistency_agent.app import app

if __name__ == "__main__":
    port = int(os.environ.get("AGENT_PORT", 5001))
    app.run(host='0.0.0.0', port=port)