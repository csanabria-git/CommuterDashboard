import os
import requests
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2

SUBWAY_ALERTS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fall-alerts"
BUS_ALERTS_URL = "https://gtfsrt.prod.obanyc.com/alerts"

SUBWAY_ROUTES = ["N", "W"]
BUS_ROUTES = ["Q69"]


def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def get_translation_text(translation_obj) -> str:
    if not translation_obj:
        return ""

    translations = getattr(translation_obj, "translation", [])
    parts = []

    for item in translations:
        text = getattr(item, "text", "")
        if text:
            parts.append(text.strip())

    return " ".join(parts).strip()


def fetch_subway_alert_feed() -> gtfs_realtime_pb2.FeedMessage:
    resp = requests.get(
        SUBWAY_ALERTS_URL,
        timeout=20
    )
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def fetch_bus_alert_feed() -> gtfs_realtime_pb2.FeedMessage:
    key = os.environ["MTA_BUSTIME_API_KEY"]

    resp = requests.get(
        BUS_ALERTS_URL,
        params={"key": key},
        timeout=20
    )
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def is_alert_active(alert, current_ts: int) -> bool:
    if not alert.active_period:
        return False

    for period in alert.active_period:
        start = period.start if period.HasField("start") else None
        end = period.end if period.HasField("end") else None

        starts_ok = start is None or current_ts >= start
        ends_ok = end is None or current_ts <= end

        if starts_ok and ends_ok:
            return True

    return False


def extract_headline(alert) -> str:
    header = get_translation_text(alert.header_text)
    if header:
        return header

    description = get_translation_text(alert.description_text)
    if description:
        return description

    return ""


def infer_status_from_text(text: str) -> str:
    if not text:
        return "Alert"

    lowered = text.lower()

    if "delay" in lowered or "delays" in lowered:
        return "Delays"
    if "detour" in lowered or "detoured" in lowered:
        return "Detour"
    if "planned work" in lowered:
        return "Planned Work"
    if "suspended" in lowered or "suspension" in lowered:
        return "Suspended"
    if "part suspended" in lowered:
        return "Part Suspended"
    if "service change" in lowered or "service changes" in lowered:
        return "Service Change"
    if "running with delays" in lowered:
        return "Delays"

    return "Alert"


def informed_entity_matches_route(entity_selector, route_id: str) -> bool:
    if not entity_selector.HasField("route_id"):
        return False

    selector_route = entity_selector.route_id.strip()

    if selector_route == route_id:
        return True

    if selector_route.endswith(f"_{route_id}"):
        return True

    if selector_route.endswith(route_id):
        return True

    return False


def summarize_route(feed, route_id: str, current_ts: int) -> dict:
    matching_alerts = []

    for entity in feed.entity:
        if not entity.HasField("alert"):
            continue

        alert = entity.alert

        if not is_alert_active(alert, current_ts):
            continue

        matched = False
        for informed_entity in alert.informed_entity:
            if informed_entity_matches_route(informed_entity, route_id):
                matched = True
                break

        if not matched:
            continue

        headline = extract_headline(alert)

        matching_alerts.append({
            "status": infer_status_from_text(headline),
            "headline": headline
        })

    if not matching_alerts:
        return {
            "status": "No Active Alerts",
            "headline": ""
        }

    return matching_alerts[0]


def handler(event, context):
    current_ts = now_ts()
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    routes = {}

    # Subway routes
    try:
        subway_feed = fetch_subway_alert_feed()

        for route in SUBWAY_ROUTES:
            routes[route] = summarize_route(subway_feed, route, current_ts)

    except Exception as e:
        error_text = str(e)
        for route in SUBWAY_ROUTES:
            routes[route] = {
                "status": "Error",
                "headline": error_text
            }

    # Bus routes
    try:
        bus_feed = fetch_bus_alert_feed()

        for route in BUS_ROUTES:
            routes[route] = summarize_route(bus_feed, route, current_ts)

    except Exception as e:
        error_text = str(e)
        for route in BUS_ROUTES:
            routes[route] = {
                "status": "Error",
                "headline": error_text
            }

    return {
        "generated_at": generated_at,
        "routes": routes
    }
