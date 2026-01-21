import os
import subprocess
import requests
from datetime import datetime, timezone

# -------------------------
# Configuration
# -------------------------
STATION_NAME = "Astoria–Ditmars Blvd"
DIRECTION = "southbound"

# Subway configuration (UNCHANGED)
SUBWAY_STOP_ID = "R01S"
SUBWAY_ROUTES = ["N", "W"]

# Bus configuration (NEW)
BUS_ROUTE = "Q69"
BUS_STOP_ID = "550714"
BUSTIME_URL = "https://bustime.mta.info/api/siri/stop-monitoring.json"


# -------------------------
# Subway logic (UNCHANGED)
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
# Bus logic (NEW)
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

        # Keep arrivals within next 3 hours
        if 0 <= delta_min <= 180:
            arrivals.append(delta_min)

    return sorted(arrivals)[:4]


# -------------------------
# Lambda handler
# -------------------------
def handler(event, context):
    # Subway key (already working, do not change)
    if not os.environ.get("MTA_API_KEY"):
        raise Exception("MTA_API_KEY not set")

    # Bus key (new)
    bustime_key = os.environ.get("MTA_BUSTIME_API_KEY")
    if not bustime_key:
        raise Exception("MTA_BUSTIME_API_KEY not set")

    now_epoch = int(datetime.now(timezone.utc).timestamp())
    arrivals = {}

    # Subway arrivals (UNCHANGED)
    for route in SUBWAY_ROUTES:
        arrivals[route] = []
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
                    arrivals[route].append(delta_min)

        arrivals[route] = sorted(arrivals[route])[:4]

    # Bus arrivals (NEW)
    arrivals[BUS_ROUTE] = get_q69_arrivals(bustime_key, now_epoch)

    response = {
        "station": STATION_NAME,
        "direction": DIRECTION,
        "arrivals": arrivals,
        "generated_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
    }

    print(response)
    return response
