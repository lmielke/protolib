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
governance_exceptions:
- c8: no class definition — verify OOP intent
"""
import json
from protolib.core.registry import ApiIntrospector

def main(*args, **kwargs) -> str:
    """
    description: Return this package's API signatures as JSON.
    """
    introspector = ApiIntrospector(*args, **kwargs)
    info = introspector.get_service_info(*args, **kwargs)
    output = json.dumps(info, indent=2)
    print(output)
    return output

if __name__ == '__main__':
    main()
