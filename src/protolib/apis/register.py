# register.py
"""
Outbound registration: register this service with the registry and show result.

Usage:
    proto register
    proto register --registry_url http://localhost:9000 --ttl 60
"""
import json
from .. import settings as sts
from ..registry import RegistryClient


def _do_register(*args, **kwargs) -> dict:
    """Perform one-shot registration with capabilities and return result dict."""
    client = RegistryClient(*args, **kwargs)
    state = client.register_with_capabilities(*args, **kwargs)
    return {
        "ok": bool(state),
        "service_id": sts.package_name,
        "registry_url": client.registry_url,
        "registry_state": state,
        "message": "Registered with registry" if state else "Registry unreachable",
    }


def main(*args, **kwargs) -> str:
    """Register this service with the registry and show result."""
    result = _do_register(*args, **kwargs)
    output = json.dumps(result, indent=2)
    print(output)
    return output
