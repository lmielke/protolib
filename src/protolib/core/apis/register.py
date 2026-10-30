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
"""
import json
import protolib.core.settings as sts
from protolib.core.registry import RegistryClient


class RegisterAPI:
    """
    description: Sends service metadata to the central registry for outbound registration.
    """

    def __init__(self, *args, **kwargs):
        """description: 'Initialize the register API facade.'"""
        super().__init__(*args, **kwargs)

    def _do_register(self, *args, **kwargs) -> dict:
        """description: Perform one-shot registration with capabilities and return result dict."""
        client = RegistryClient(*args, **kwargs)
        state = client.register_with_capabilities(*args, **kwargs)
        return {"ok": bool(state), "service_id": sts.package_name,
                "registry_url": client.registry_url, "registry_state": state,
                "message": "Registered with registry" if state else "Registry unreachable"}

    def main(self, *args, **kwargs) -> str:
        """description: Register this service with the registry and show result."""
        result = self._do_register(*args, **kwargs)
        output = json.dumps(result, indent=2)
        print(output)
        return output

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "RegisterAPI(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short label.'"""
        return "RegisterAPI"

def _do_register(*args, **kwargs) -> dict:
    """description: 'Module-level shim — delegates to RegisterAPI._do_register().'"""
    return RegisterAPI()._do_register(*args, **kwargs)

def main(*args, **kwargs) -> str:
    """description: 'Module-level shim — delegates to RegisterAPI.main().'"""
    return RegisterAPI().main(*args, **kwargs)


if __name__ == '__main__':
    main()
