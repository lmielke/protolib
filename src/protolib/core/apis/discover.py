"""
script_path: src/protolib/core/apis/discover.py
purpose: >-
  Service discovery: look up a registered service by its unique ID and return its
  full metadata (host, port, capabilities) as JSON.
description: |-
  Queries the central
  registry at the configured registry_url. Returns an error payload if the
  service is not found or the registry is unreachable.
  Usage:
      proto discover --service_id ollama
      proto discover --service_id whisker
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryClient

def _json_print(*args, data: dict, **kwargs) -> str:
    output = json.dumps(data, indent=2)
    print(output)
    return output

def _discover_service(*args, service_id: str, **kwargs) -> dict:
    client = RegistryClient(*args, **kwargs)
    svc = client.discover(service_id, *args, fresh=True, **kwargs)
    url = client.discover_url(service_id, *args, **kwargs)
    msg = f"Found {service_id}" if svc else f"{service_id} not found in registry"
    return {"ok": bool(svc), "service_id": service_id,
            "url": url, "service": svc, "message": msg}

def main(*args, service_id: str = None, **kwargs) -> str:
    if not service_id:
        return _json_print(data={"ok": False, "message": "service_id is required"})
    return _json_print(data=_discover_service(*args, service_id=service_id, **kwargs))

if __name__ == '__main__':
    main()
