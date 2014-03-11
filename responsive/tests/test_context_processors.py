from __future__ import unicode_literals

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
        default = {'width': None, 'height': None, 'type': None, 'pixelratio': None}
        self.assertEqual(result['device_info'], default)

    def test_device_type(self):
        "Device type should be included based on the current set of breakpoints."
        # FIXME: Currently assumes default settings
        info = {'width': 320, 'height': 480}
        # Simulate DeviceInfoMiddleware
        self.request.device_info = info
        result = device_info(self.request)
        self.assertEqual(result['device_info']['type'], 'phone')
        info = {'width': 700, 'height': 1000}
        # Simulate DeviceInfoMiddleware
        self.request.device_info = info
        result = device_info(self.request)
        self.assertEqual(result['device_info']['type'], 'tablet')

    def test_device_type_max(self):
        "None width in the breakpoints defines no max width."
        # FIXME: Currently assumes default settings
        info = {'width': 1600, 'height': 1000}
        # Simulate DeviceInfoMiddleware
        self.request.device_info = info
        result = device_info(self.request)
        self.assertEqual(result['device_info']['type'], 'desktop')
