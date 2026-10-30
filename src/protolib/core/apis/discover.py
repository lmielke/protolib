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
"""
import json
from protolib.core.registry import RegistryClient

_NO_SVC_ID = {"ok": False, "service_id": None, "url": None,
              "service": None, "message": "service_id is required"}


class DiscoverAPI:
    """
    description: Resolves service identifiers to metadata and URLs via the registry client.
    """

    def __init__(self, *args, **kwargs):
        """description: 'Initialize the discover API facade.'"""
        super().__init__(*args, **kwargs)

    def _json_print(self, *args, data: dict, **kwargs) -> str:
        """description: 'Serialize data to indented JSON, print it, and return the string.'"""
        output = json.dumps(data, indent=2)
        print(output)
        return output

    def _discover_service(self, *args, service_id: str = None, **kwargs) -> dict:
        """description: 'Query registry for service_id; return envelope with ok, url, service, message.'"""
        if not service_id:
            return _NO_SVC_ID
        client = RegistryClient(*args, **kwargs)
        svc = client.discover(service_id, *args, fresh=True, **kwargs)
        url = client.discover_url(service_id, *args, **kwargs)
        msg = f"Found {service_id}" if svc else f"{service_id} not found in registry"
        return {"ok": bool(svc), "service_id": service_id,
                "url": url, "service": svc, "message": msg}

    def main(self, *args, **kwargs) -> str:
        """description: 'CLI entry point — discover service and print JSON result.'"""
        return self._json_print(*args, data=self._discover_service(*args, **kwargs), **kwargs)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "DiscoverAPI(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short label.'"""
        return "DiscoverAPI"

def main(*args, **kwargs) -> str:
    """description: 'Module-level shim — delegates to DiscoverAPI.main().'"""
    return DiscoverAPI().main(*args, **kwargs)


if __name__ == '__main__':
    main()
