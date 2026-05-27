import unittest

from app.main import health_check


class HealthCheckTests(unittest.TestCase):
    def test_health_check_returns_success(self):
        response = health_check()

        self.assertEqual(response.status, 'success')
        self.assertEqual(response.data['status'], 'healthy')
        self.assertIn('GuardianIQ backend running', response.message)


if __name__ == '__main__':
    unittest.main()
