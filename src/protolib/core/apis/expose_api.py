"""
script_path: src/protolib/core/apis/expose_api.py
purpose: >-
  Returns this package's full API signatures as JSON, including parameter names, types,
  and docstrings.
description: |-
  Always active — every protolib package is self-documenting
  by design. Consumed by the registry and by client packages discovering available
  operations via proto discover or direct HTTP.
  Usage:
      proto expose_api
      curl http://localhost:9001/expose_api/
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import json
from protolib.core.registry import ApiIntrospector

def main(*args, **kwargs) -> str:
    """
    purpose: Return this package's API signatures as JSON.
    """
    introspector = ApiIntrospector(*args, **kwargs)
    info = introspector.get_service_info(*args, **kwargs)
    output = json.dumps(info, indent=2)
    print(output)
    return output

if __name__ == '__main__':
    main()
