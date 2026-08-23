"""
script_path: src/protolib/core/apis/discover.py
description: >-
  Resolves a service identifier into its full metadata and endpoint URL by querying the central
  registry client. Returns a structured JSON payload containing the service definition, its
  URL, and a status message. Handles missing identifiers and lookup failures by emitting a
  standardized error object. Serves as the CLI entry point for the proto discover command.
tags:
- cli
- infra
- settings
governance_exceptions:
- c8: no class definition — verify OOP intent
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryClient

_NO_SVC_ID = {"ok": False, "service_id": None, "url": None,
              "service": None, "message": "service_id is required"}

def _json_print(*args, data: dict, **kwargs) -> str:
    output = json.dumps(data, indent=2)
    print(output)
    return output

def _discover_service(*args, service_id: str = None, **kwargs) -> dict:
    if not service_id: return _NO_SVC_ID
    client = RegistryClient(*args, **kwargs)
    svc = client.discover(service_id, *args, fresh=True, **kwargs)
    url = client.discover_url(service_id, *args, **kwargs)
    msg = f"Found {service_id}" if svc else f"{service_id} not found in registry"
    return {"ok": bool(svc), "service_id": service_id,
            "url": url, "service": svc, "message": msg}

def main(*args, **kwargs) -> str:
    return _json_print(*args, data=_discover_service(*args, **kwargs), **kwargs)

if __name__ == '__main__':
    main()
