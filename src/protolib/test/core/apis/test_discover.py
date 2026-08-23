"""
script_path: src/protolib/test/core/apis/test_discover.py
description: >-
  Runs integration tests for the service discovery API by invoking the main entry point with
  various service identifiers. Verifies that missing IDs and unknown IDs return structured
  JSON error responses with expected message fragments. Consumed by the test runner to validate
  the discover module's error handling behavior.
tags:
- infra
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import json, unittest
from protolib.core.apis.discover import main


class TestDiscoverMain(unittest.TestCase):
    """main: discover a service by ID from registry."""

    def test_no_service_id_returns_error(self, *args, **kwargs):
        result = main(service_id=None)
        data = json.loads(result)
        assert data["ok"] is False
        assert "required" in data["message"]

    def test_unknown_service_not_found(self, *args, **kwargs):
        result = main(service_id="nonexistent_xyz_999")
        data = json.loads(result)
        assert data["ok"] is False
        assert "not found" in data["message"]


if __name__ == '__main__':
    unittest.main()
