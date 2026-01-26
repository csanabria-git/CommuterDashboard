import os
import subprocess
import requests
from datetime import datetime, timezone

# -------------------------
# Configuration
# -------------------------
STATION_NAME = "Astoria–Ditmars Blvd"
DIRECTION = "southbound"

# Subway configuration
SUBWAY_STOP_ID = "R01S"
SUBWAY_ROUTES = ["N", "W"]

# Bus configuration
BUS_ROUTE = "Q69"
BUS_STOP_ID = "550714"
BUSTIME_URL = "https://bustime.mta.info/api/siri/stop-monitoring.json"

# -------------------------
# Subway logic
# -------------------------
def run_underground(route):
    """
    Runs underground CLI.
    Auth is provided implicitly via MTA_API_KEY env var.
    """
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
        raise Exception(f"underground failed for route {route}")

    return result.stdout.splitlines()

# -------------------------
# Bus logic
# -------------------------
def get_q69_arrivals(bustime_key, now_epoch):
    params = {
        "key": bustime_key,
        "MonitoringRef": BUS_STOP_ID,
        "LineRef": BUS_ROUTE
    }

    resp = requests.get(BUSTIME_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    arrivals = []

    visits = (
        data.get("Siri", {})
            .get("ServiceDelivery", {})
            .get("StopMonitoringDelivery", [{}])[0]
            .get("MonitoredStopVisit", [])
    )

    for visit in visits:
        call = (
            visit.get("MonitoredVehicleJourney", {})
                 .get("MonitoredCall", {})
        )

        expected = call.get("ExpectedArrivalTime")
        if not expected:
            continue

        arrival_time = datetime.fromisoformat(
            expected.replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        delta_min = int((arrival_time.timestamp() - now_epoch) / 60)

        if 0 <= delta_min <= 180:
            arrivals.append(delta_min)

    return sorted(arrivals)[:4]

# -------------------------
# Lambda handler
# -------------------------
def handler(event, context):
    # Validate environment
    if not os.environ.get("MTA_API_KEY"):
        raise Exception("MTA_API_KEY not set")

    bustime_key = os.environ.get("MTA_BUSTIME_API_KEY")
    if not bustime_key:
        raise Exception("MTA_BUSTIME_API_KEY not set")

    now_epoch = int(datetime.now(timezone.utc).timestamp())

    # -------------------------
    # Collect subway arrivals (merged + sortable)
    # -------------------------
    subway_arrivals = []

    for route in SUBWAY_ROUTES:
        lines = run_underground(route)

        for line in lines:
            if not line.startswith(SUBWAY_STOP_ID):
                continue

            for t in line.split()[1:]:
                try:
                    arrival_epoch = int(t)
                except ValueError:
                    continue

                delta_min = int((arrival_epoch - now_epoch) / 60)

                if 0 <= delta_min <= 180:
                    subway_arrivals.append({
                        "route": route,
                        "minutes": delta_min
                    })

    # Global sort: what comes next, regardless of route
    subway_arrivals.sort(key=lambda x: x["minutes"])

    # Keep only the next N arrivals total (across N + W)
    subway_arrivals = subway_arrivals[:6]

    # -------------------------
    # Bus arrivals
    # -------------------------
    bus_arrivals = get_q69_arrivals(bustime_key, now_epoch)

    # -------------------------
    # Response
    # -------------------------
    response = {
        "station": STATION_NAME,
        "direction": DIRECTION,
        "arrivals": {
            "subway": subway_arrivals,
            "bus": {
                BUS_ROUTE: bus_arrivals
            }
        },
        "generated_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
    }

    print(response)
    return response
