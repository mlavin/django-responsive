from django.test.client import RequestFactory
from django.utils import unittest


from responsive.middleware import DeviceInfoMiddleware


class DeviceInfoMiddlewareTestCase(unittest.TestCase):
    "Middleware for processing device info from the cookies."

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.middleware = DeviceInfoMiddleware()

    def test_process_request_no_cookies(self):
        "Process a request which does not have the info cookie set."
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device'))
        device = self.request.device
        self.assertEqual(device['width'], None)
        self.assertEqual(device['height'], None)

    def test_process_request_invalid_cook(self):
        "Process a request which has an invalid value in the cookie."
        self.request.COOKIES['resolution'] = 'XXXXXXXXXXXXXXX'
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device'))
        device = self.request.device
        self.assertEqual(device['width'], None)
        self.assertEqual(device['height'], None)

    def test_process_request_valid_cookie(self):
        "Read data from the cookie and make it available on the request."
        self.request.COOKIES['resolution'] = '320:480'
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device'))
        device = self.request.device
        self.assertEqual(device['width'], 320)
        self.assertEqual(device['height'], 480)
