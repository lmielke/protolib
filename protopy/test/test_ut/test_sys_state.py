import os
import unittest
from datetime import datetime, timedelta
import yaml
from protopy.helpers.sys_state import State
import protopy.settings as sts

class Test_State(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache_dir = sts.cache_state_dir
        cls.cache_file = 'test_state.yaml'
        cls.cache_path = os.path.join(cls.cache_dir, cls.cache_file)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.cache_path):
            os.remove(cls.cache_path)

    def setUp(self):
        # Ensure the cache file is reset before each test
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)
        self.state = State(cache_state_name=self.cache_file, cache_state_dir=self.cache_dir)

    def test___init__(self):
        self.assertTrue(isinstance(self.state, State))
        self.assertEqual(self.state.cache_state_name, self.cache_file)
        self.assertEqual(self.state.cache_state_dir, self.cache_dir)

    def test__load_cache(self):
        self.state.set('test', 'data')
        loaded_data = self.state._load_cache()
        self.assertIn('test', loaded_data)
        self.assertEqual(loaded_data['test']['value'], 'data')

    def test__save_cache(self):
        self.state.set('test', 'data')
        with open(self.cache_path, 'r') as f:
            data = yaml.safe_load(f)
        self.assertIn('test', data)
        self.assertEqual(data['test']['value'], 'data')

    def test_get(self):
        self.state.set('test', 'data')
        self.assertEqual(self.state.get('test'), 'data')
        self.assertIsNone(self.state.get('nonexistent'))

    def test_set(self):
        self.state.set('test', 'data')
        with open(self.cache_path, 'r') as f:
            data = yaml.safe_load(f)
        self.assertIn('test', data)
        self.assertEqual(data['test']['value'], 'data')

    def test_is_valid(self):
        self.state.set('test', 'data')
        self.assertTrue(self.state.is_valid('test', max_cache_hours=1))
        old_time = datetime.now() - timedelta(hours=2)
        self.state.data['test']['last_update'] = old_time.isoformat()
        self.state._save_cache()
        self.assertFalse(self.state.is_valid('test', max_cache_hours=1))

if __name__ == "__main__":
    unittest.main()
