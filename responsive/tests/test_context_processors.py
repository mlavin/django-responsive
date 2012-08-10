from django.test.client import RequestFactory
from django.utils import unittest

from responsive.context_processors import device_info


class DeviceInfoContextTestCase(unittest.TestCase):
    "Pull device info off the request."

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    def test_return_device_info(self):
        "Return device info if available."
        info = {'width': 320, 'height': 480}
        # Simulate DeviceInfoMiddleware
        self.request.device_info = info
        result = device_info(self.request)
        self.assertEqual(result['device_info'], info)

    def test_default_device_info(self):
        "Return default info if info is not attached to the request."
        result = device_info(self.request)
        self.assertEqual(result['device_info'], {'width': None, 'height': None})
