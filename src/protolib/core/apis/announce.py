"""
script_path: src/protolib/core/apis/announce.py
purpose: Registry host endpoint — receives registrations, serves state.
description: |-
  Dormant unless registry_host_enabled = True in settings.yml.
  Usage:
      proto announce              # shows state or dormant message
      POST /announce/ with JSON   # register a service (via server.py do_POST)
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryHost

def _handle_registration(body: dict, *args, **kwargs) -> dict:
    """
    purpose: Process a registration POST body and return updated state.
    """
    sid = body.get("id", "unknown")
    data = body.get("data", {})
    return RegistryHost(*args, **kwargs).register_service(sid, data, *args, **kwargs)

def _get_state(*args, **kwargs) -> dict:
    """
    purpose: Return current registry state.
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
