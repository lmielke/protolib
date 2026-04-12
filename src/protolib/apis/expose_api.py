# expose_api.py
"""
Returns this package's API signatures as JSON.
Always active — every package is self-documenting.

Usage:
    proto expose_api
    curl http://localhost:9001/expose_api/
"""
import json
from ..registry import ApiIntrospector


def main(*args, **kwargs) -> str:
    """Return this package's API signatures as JSON."""
    introspector = ApiIntrospector(*args, **kwargs)
    info = introspector.get_service_info(*args, **kwargs)
    output = json.dumps(info, indent=2)
    print(output)
    return output
