# discover.py
"""
Service discovery: look up a service by ID from the registry.

Usage:
    proto discover --service_id ollama
    proto discover --service_id whisker
"""
import json
from .. import settings as sts
from ..registry import RegistryClient


def main(*args, service_id: str = None, **kwargs) -> str:
    """Discover a service by ID from the registry."""
    if not service_id:
        output = json.dumps({"ok": False, "message": "service_id is required"}, indent=2)
        print(output)
        return output
    client = RegistryClient(*args, **kwargs)
    svc = client.discover(service_id, *args, fresh=True, **kwargs)
    url = client.discover_url(service_id, *args, **kwargs)
    result = {
        "ok": bool(svc),
        "service_id": service_id,
        "url": url,
        "service": svc,
        "message": f"Found {service_id}" if svc else f"{service_id} not found in registry",
    }
    output = json.dumps(result, indent=2)
    print(output)
    return output
