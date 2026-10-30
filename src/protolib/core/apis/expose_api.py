"""
script_path: src/protolib/core/apis/expose_api.py
description: >-
  Exposes the package's full API signatures as formatted JSON, including parameter names,
  types, and docstrings. Uses ApiIntrospector to gather service metadata and serializes the
  result for direct output. Serves as the self-documenting endpoint consumed by the registry
  and client packages during discovery via CLI or HTTP.
tags:
- cli
- infra
- parsing
"""
import json
from protolib.core.registry import ApiIntrospector


class ExposeAPI:
    """
    description: Serializes and prints this package's full API signatures as JSON.
    """

    def __init__(self, *args, **kwargs):
        """description: 'Initialize the expose API facade.'"""
        super().__init__(*args, **kwargs)

    def main(self, *args, **kwargs) -> str:
        """description: Return this package's API signatures as JSON."""
        introspector = ApiIntrospector(*args, **kwargs)
        info = introspector.get_service_info(*args, **kwargs)
        output = json.dumps(info, indent=2)
        print(output)
        return output

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "ExposeAPI(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short label.'"""
        return "ExposeAPI"

def main(*args, **kwargs) -> str:
    """description: 'Module-level shim — delegates to ExposeAPI.main().'"""
    return ExposeAPI().main(*args, **kwargs)


if __name__ == '__main__':
    main()
