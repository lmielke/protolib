"""
script_path: src/protolib/core/apis/announce.py
description: >-
  Exposes the registry host endpoint for service registration and state retrieval. Processes
  POST bodies to register services and returns the current registry state as JSON. Remains
  dormant unless the registry_host_enabled setting is true in the configuration. Consumed
  by the server POST handler and the CLI announce command.
tags:
- cli
- infra
- settings
governance_exceptions:
- c8: no class definition — verify OOP intent
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryHost

def _handle_registration(body: dict, *args, **kwargs) -> dict:
    """
    description: Process a registration POST body and return updated state.
    """
    sid = body.get("id", "unknown")
    data = body.get("data", {})
    return RegistryHost(*args, **kwargs).register_service(sid, data, *args, **kwargs)

def _get_state(*args, **kwargs) -> dict:
    """
    description: Return current registry state.
    """
    return RegistryHost(*args, **kwargs).read_state(*args, **kwargs)

def main(*args, **kwargs) -> str:
    """
    purpose: Announce API — registry host endpoint.
    description: Dormant unless registry_host_enabled is True.
    """
    if not getattr(sts, 'registry_host_enabled', False):
        output = "announce API is not enabled on this instance"
    else:
        output = json.dumps(_get_state(*args, **kwargs), indent=2)
    print(output)
    return output

if __name__ == '__main__':
    main()
