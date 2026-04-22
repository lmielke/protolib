"""
script_path: src/protolib/test/core/test_registry.py
purpose: "Integration tests for core/registry.py — registry client/host/introspector."
update_rules: "Append scenarios. Never remove existing tests."
"""
import json, os, tempfile, shutil, unittest
from protolib.core.registry import (
    RegistryClient, RegistryHost, ApiIntrospector,
)
import protolib.core.settings as sts


class TestRegistryClientInit(unittest.TestCase):
    """RegistryClient: constructor and cached state."""

    def test_default_sid(self):
        client = RegistryClient()
        assert client.sid == sts.package_name

    def test_custom_sid(self):
        client = RegistryClient(sid="myservice")
        assert client.sid == "myservice"

    def test_default_url(self):
        client = RegistryClient()
        assert str(sts.registry_port) in client.registry_url


class TestRegistryClientDiscover(unittest.TestCase):
    """discover / discover_url: lookup from cached state."""

    def test_discover_from_cache(self):
        client = RegistryClient()
        client._cached_state = {
            "services": {"svc1": {"host": "localhost", "port": 8000}}
        }
        result = client.discover("svc1")
        assert result["port"] == 8000

    def test_discover_missing_returns_none(self):
        client = RegistryClient()
        client._cached_state = {"services": {}}
        result = client.discover("nonexistent")
        assert result is None

    def test_discover_url(self):
        client = RegistryClient()
        client._cached_state = {
            "services": {"svc1": {"host": "myhost", "port": 9000}}
        }
        url = client.discover_url("svc1")
        assert url == "http://myhost:9000"

    def test_discover_url_no_port(self):
        client = RegistryClient()
        client._cached_state = {"services": {"svc1": {"host": "h"}}}
        assert client.discover_url("svc1") is None


class TestRegistryHost(unittest.TestCase):
    """RegistryHost: file-based state management."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.tmpdir, "state.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_state_file(self):
        host = RegistryHost(state_file=self.state_file)
        assert os.path.exists(self.state_file)

    def test_get_state_has_services(self):
        host = RegistryHost(state_file=self.state_file)
        state = host.read_state()
        assert "services" in state
        assert "shared" in state

    def test_register_service(self):
        host = RegistryHost(state_file=self.state_file)
        state = host.register_service("test_svc", {"port": 5000, "ttl": 30})
        assert "test_svc" in state["services"]
        assert state["services"]["test_svc"]["port"] == 5000
        assert state["services"]["test_svc"]["status"] == "active"

    def test_register_shared(self):
        host = RegistryHost(state_file=self.state_file)
        state = host.register_service("__shared_config", {"key": "val"})
        assert "config" in state["shared"]
        assert state["shared"]["config"]["key"] == "val"

    def test_state_persists(self):
        host = RegistryHost(state_file=self.state_file)
        host.register_service("svc_a", {"port": 1234})
        host2 = RegistryHost(state_file=self.state_file)
        state = host2.read_state()
        assert "svc_a" in state["services"]


class TestRegistryHostTTL(unittest.TestCase):
    """TTL checking: mark stale services."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.tmpdir, "state.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_stale_detection(self):
        host = RegistryHost(state_file=self.state_file)
        svc = {"last_seen": "2020-01-01T00:00:00+00:00", "ttl": 10, "status": "active"}
        now = "2026-01-01T00:00:00+00:00"
        host._check_ttl(svc, now)
        assert svc["status"] == "stale"

    def test_active_within_ttl(self):
        host = RegistryHost(state_file=self.state_file)
        svc = {"last_seen": "2026-01-01T00:00:00+00:00", "ttl": 9999, "status": "active"}
        now = "2026-01-01T00:00:05+00:00"
        host._check_ttl(svc, now)
        assert svc["status"] == "active"

    def test_inactive_not_changed(self):
        host = RegistryHost(state_file=self.state_file)
        svc = {"last_seen": "2020-01-01T00:00:00+00:00", "ttl": 1, "status": "inactive"}
        now = "2026-01-01T00:00:00+00:00"
        host._check_ttl(svc, now)
        assert svc["status"] == "inactive"


class TestApiIntrospector(unittest.TestCase):
    """ApiIntrospector: function signature reading."""

    def test_read_signature_typed(self):
        def sample(name: str, count: int = 5, *args, **kwargs):
            pass
        intro = ApiIntrospector()
        sig = intro._read_signature(sample)
        assert "name" in sig
        assert sig["name"]["type"] == "string"
        assert sig["count"]["default"] == 5

    def test_read_signature_skips_varargs(self):
        def sample(x: str, *args, **kwargs):
            pass
        intro = ApiIntrospector()
        sig = intro._read_signature(sample)
        assert "x" in sig
        assert "args" not in sig
        assert "kwargs" not in sig

    def test_get_api_signatures(self):
        intro = ApiIntrospector()
        apis = intro.get_api_signatures()
        assert isinstance(apis, dict)

    def test_get_service_info(self):
        intro = ApiIntrospector()
        info = intro.get_service_info()
        assert info["id"] == sts.package_name
        assert "apis" in info


if __name__ == '__main__':
    unittest.main()
