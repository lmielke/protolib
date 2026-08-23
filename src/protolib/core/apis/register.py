"""
script_path: src/protolib/core/apis/register.py
description: >-
  Sends service metadata, including host, port, and capabilities, to the central registry
  for outbound registration. Constructs a RegistryClient to execute the announcement and returns
  a status dictionary containing the service ID and registry state. Consumed by the CLI entry
  point to announce the service at startup or after configuration changes.
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

def _do_register(*args, **kwargs) -> dict:
    """
    description: Perform one-shot registration with capabilities and return result dict.
    """
    client = RegistryClient(*args, **kwargs)
    state = client.register_with_capabilities(*args, **kwargs)
    return {"ok": bool(state), "service_id": sts.package_name,
            "registry_url": client.registry_url, "registry_state": state,
            "message": "Registered with registry" if state else "Registry unreachable"}

def main(*args, **kwargs) -> str:
    """
    description: Register this service with the registry and show result.
    """
    result = _do_register(*args, **kwargs)
    output = json.dumps(result, indent=2)
    print(output)
    return output

if __name__ == '__main__':
    main()
