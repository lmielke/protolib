"""
script_path: src/protolib/core/apis/register.py
purpose: >-
  Outbound registration: sends this service's metadata (host, port, capabilities)
  to the central registry and prints the result as JSON.
description: |-
  Respects the configured
  registry_url and ttl. Called at startup or on-demand to (re-)announce the service
  after a restart or configuration change.
  Usage:
      proto register
      proto register --registry_url http://localhost:9000 --ttl 60
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryClient

def _do_register(*args, **kwargs) -> dict:
    """
    purpose: Perform one-shot registration with capabilities and return result dict.
    """
    client = RegistryClient(*args, **kwargs)
    state = client.register_with_capabilities(*args, **kwargs)
    return {"ok": bool(state), "service_id": sts.package_name,
            "registry_url": client.registry_url, "registry_state": state,
            "message": "Registered with registry" if state else "Registry unreachable"}

def main(*args, **kwargs) -> str:
    """
    purpose: Register this service with the registry and show result.
    """
    result = _do_register(*args, **kwargs)
    output = json.dumps(result, indent=2)
    print(output)
    return output

if __name__ == '__main__':
    main()
