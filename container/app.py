import os
import subprocess
from datetime import datetime

STOP_ID = "R36N"
ROUTE = "N"

def handler(event, context):
    if not os.environ.get("MTA_API_KEY"):
        raise Exception("MTA_API_KEY not set")

    # Ask underground for epoch timestamps (seconds since Unix epoch)
    cmd = [
        "underground",
        "stops",
        ROUTE,
        "--format",
        "epoch"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=20
    )

    if result.returncode != 0:
        print("STDERR:", result.stderr)
        raise Exception("underground command failed")

    now_epoch = int(datetime.utcnow().timestamp())
    arrivals_min = []

    for line in result.stdout.splitlines():
        if not line.startswith(STOP_ID):
            continue

        times = line.split()[1:]

        for t in times:
            try:
                arrival_epoch = int(t)
            except ValueError:
                continue

            delta_min = int((arrival_epoch - now_epoch) / 60)

            # Keep arrivals from now up to 3 hours out
            if 0 <= delta_min <= 180:
                arrivals_min.append(delta_min)

    arrivals_min = sorted(arrivals_min)[:4]

    response = {
        "station": "Astoria–Ditmars Blvd",
        "route": ROUTE,
        "stop_id": STOP_ID,
        "arrivals_min": arrivals_min,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    print(response)
    return response
