import os
import json
from datetime import datetime

# Import the Lambda handler
from app import handler

# -------------------------------------------------
# Local environment setup (DO NOT COMMIT KEYS)
# -------------------------------------------------
# Option 1: export these in your shell instead
# export MTA_API_KEY=...
# export MTA_BUSTIME_API_KEY=...

# Option 2: uncomment and hardcode TEMPORARILY
# os.environ["MTA_API_KEY"] = "YOUR_MTA_KEY"
# os.environ["MTA_BUSTIME_API_KEY"] = "YOUR_BUSTIME_KEY"

# -------------------------------------------------
# Mock Lambda inputs
# -------------------------------------------------
mock_event = {
    "source": "local-test",
    "timestamp": datetime.utcnow().isoformat()
}

mock_context = None  # Lambda context not used

# -------------------------------------------------
# Invoke handler
# -------------------------------------------------
if __name__ == "__main__":
    response = handler(mock_event, mock_context)

    print("\n=== Lambda Response ===")
    print(json.dumps(response, indent=2))

