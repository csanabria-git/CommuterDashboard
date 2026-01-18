import os
import subprocess
from datetime import datetime

STOP_ID = "R36N"
ROUTES = ["N", "W"]

def run_underground(route):
    cmd = [
        "underground",
        "stops",
        route,
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
        print(f"STDERR ({route}):", result.stderr)
        raise Exception(f"underground command failed for route {route}")

    return result.stdout.splitlines()

def handler(event, context):
    if not os.environ.get("MTA_API_KEY"):
        raise Exception("MTA_API_KEY not set")

    now_epoch = int(datetime.utcnow().timestamp())
    arrivals = {}

    for route in ROUTES:
        arrivals[route] = []
        lines = run_underground(route)

        for line in lines:
            if not line.startswith(STOP_ID):
                continue

            times = line.split()[1:]

            for t in times:
                try:
                    arrival_epoch = int(t)
                except ValueError:
                    continue

                delta_min = int((arrival_epoch - now_epoch) / 60)

                # Keep arrivals from now to 3 hours out
                if 0 <= delta_min <= 180:
                    arrivals[route].append(delta_min)

        arrivals[route] = sorted(arrivals[route])[:4]

    response = {
        "station": "Astoria–Ditmars Blvd",
        "direction": "southbound",
        "arrivals": arrivals,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    print(response)
    return response
