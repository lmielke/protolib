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
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryHost


class AnnounceAPI:
    """
    description: Registry host endpoint — registers services and returns state.
      Dormant unless registry_host_enabled is True.
    """

    def __init__(self, *args, **kwargs):
        """description: 'Initialize the announce API facade.'"""
        super().__init__(*args, **kwargs)

    def _handle_registration(self, body: dict, *args, **kwargs) -> dict:
        """description: Process a registration POST body and return updated state."""
        sid = body.get("id", "unknown")
        data = body.get("data", {})
        return RegistryHost(*args, **kwargs).register_service(sid, data, *args, **kwargs)

    def _get_state(self, *args, **kwargs) -> dict:
        """description: Return current registry state."""
        return RegistryHost(*args, **kwargs).read_state(*args, **kwargs)

    def main(self, *args, **kwargs) -> str:
        """description: Dormant unless registry_host_enabled is True."""
        if not getattr(sts, 'registry_host_enabled', False):
            output = "announce API is not enabled on this instance"
        else:
            output = json.dumps(self._get_state(*args, **kwargs), indent=2)
        print(output)
        return output

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "AnnounceAPI(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short label.'"""
        return "AnnounceAPI"

def _handle_registration(body: dict, *args, **kwargs) -> dict:
    """description: 'Module-level shim — delegates to AnnounceAPI._handle_registration().'"""
    return AnnounceAPI()._handle_registration(body, *args, **kwargs)

def _get_state(*args, **kwargs) -> dict:
    """description: 'Module-level shim — delegates to AnnounceAPI._get_state().'"""
    return AnnounceAPI()._get_state(*args, **kwargs)

def main(*args, **kwargs) -> str:
    """description: 'Module-level shim — delegates to AnnounceAPI.main().'"""
    return AnnounceAPI().main(*args, **kwargs)


if __name__ == '__main__':
    main()
