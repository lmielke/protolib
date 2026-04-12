# announce.py
"""
Registry host endpoint — receives registrations, serves state.
Dormant unless registry_host_enabled = True in settings.yml.

Usage:
    proto announce              # shows state or dormant message
    POST /announce/ with JSON   # register a service (via server.py do_POST)
"""
import json
from .. import settings as sts
from ..registry import RegistryHost


def _handle_registration(body: dict, *args, **kwargs) -> dict:
    """Process a registration POST body and return updated state."""
    host = RegistryHost(*args, **kwargs)
    sid = body.get("id", "unknown")
    data = body.get("data", {})
    state = host.register_service(sid, data, *args, **kwargs)
    return state


def _get_state(*args, **kwargs) -> dict:
    """Return current registry state."""
    host = RegistryHost(*args, **kwargs)
    return host.get_state(*args, **kwargs)


def main(*args, **kwargs) -> str:
    """Announce API — registry host endpoint. Dormant unless registry_host_enabled is True."""
    if not getattr(sts, 'registry_host_enabled', False):
        output = "announce API is not enabled on this instance"
        print(output)
        return output
    state = _get_state(*args, **kwargs)
    output = json.dumps(state, indent=2)
    print(output)
    return output
