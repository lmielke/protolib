"""
script_path: src/protolib/test/core/apis/test_announce.py
description: >-
  Runs integration tests for the registry host endpoint defined in app/apis/announce.py. Validates
  service registration logic and the dormant state when the host is disabled. Uses temporary
  directories to isolate state file mutations during test execution.
tags:
- infra
- settings
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import json, os, shutil, tempfile, unittest
import protolib.core.settings as core_sts
from protolib.core.apis.announce import _handle_registration, _get_state, main
import protolib.app.settings as sts


class TestHandleRegistration(unittest.TestCase):
    """_handle_registration: process POST body and register service."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig = core_sts.registry_state_file
        core_sts.registry_state_file = os.path.join(self.tmpdir, "state.json")

    def tearDown(self):
        core_sts.registry_state_file = self._orig
        shutil.rmtree(self.tmpdir)

    def test_registers_service(self, *args, **kwargs):
        body = {"id": "test_svc", "data": {"port": 8080}}
        state = _handle_registration(body)
        assert "test_svc" in state.get("services", {})

    def test_unknown_id_default(self, *args, **kwargs):
        body = {"data": {"port": 1234}}
        state = _handle_registration(body)
        assert "unknown" in state.get("services", {})


class TestMain(unittest.TestCase):
    """main: returns dormant message or state."""

    def test_dormant_when_disabled(self, *args, **kwargs):
        orig = getattr(sts, 'registry_host_enabled', False)
        sts.registry_host_enabled = False
        try:
            result = main()
            assert "not enabled" in result
        finally:
            sts.registry_host_enabled = orig


if __name__ == '__main__':
    unittest.main()
