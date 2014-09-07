from __future__ import unicode_literals

import re

from django.http import HttpResponse
from django.test.client import RequestFactory
from django.utils import unittest

try:
    from django.http import StreamingHttpResponse
except ImportError:
    StreamingHttpResponse = None


from responsive.middleware import DeviceInfoMiddleware


class ProcessDeviceInfoTestCase(unittest.TestCase):
    "Middleware for processing device info from the cookies."

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.middleware = DeviceInfoMiddleware()

    def test_process_request_no_cookies(self):
        "Process a request which does not have the info cookie set."
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device_info'))
        device = self.request.device_info
        self.assertEqual(device['width'], None)
        self.assertEqual(device['height'], None)
        self.assertEqual(device['type'], None)
        self.assertEqual(device['pixelratio'], None)

    def test_process_request_invalid_cookie(self):
        "Process a request which has an invalid value in the cookie."
        self.request.COOKIES['resolution'] = 'XXXXXXXXXXXXXXX'
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device_info'))
        device = self.request.device_info
        self.assertEqual(device['width'], None)
        self.assertEqual(device['height'], None)
        self.assertEqual(device['type'], None)
        self.assertEqual(device['pixelratio'], None)

    def test_process_request_valid_cookie(self):
        "Read data from the cookie and make it available on the request."
        # FIXME: Currently assumes default settings
        self.request.COOKIES['resolution'] = '320:480:2'
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device_info'))
        device = self.request.device_info
        self.assertEqual(device['width'], 320)
        self.assertEqual(device['height'], 480)
        self.assertEqual(device['type'], 'phone')
        self.assertEqual(device['pixelratio'], 2)

    def test_process_request_float_pixelratio(self):
        """
        `pixelratio` can be a float when the user uses in-browser zoom and
        should give us valid device info.
        """
        self.request.COOKIES['resolution'] = '1920:1200:1.100000023841858'  # 110%
        self.middleware.process_request(request=self.request)
        device = self.request.device_info
        self.assertEqual(device['width'], 1920)
        self.assertEqual(device['height'], 1200)
        self.assertEqual(device['type'], 'desktop')
        self.assertEqual(device['pixelratio'], 1.100000023841858)


class DeviceInfoScriptTestCase(unittest.TestCase):
    "Middleware for including necessary script tags in HTML responses."

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.middleware = DeviceInfoMiddleware()
        # Make a fake view
        def view(request, **kwargs):
            if 'content' not in kwargs:
            # Return a miminally valid HTML doc
                html = b"""
                <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"  
                "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">  
                <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">  
                    <head>  
                        <meta http-equiv="content-type" content="text/html; charset=utf-8"/>  
                        <title>title</title>
                    </head>  
                    <body>  
                    </body>  
                </html>
                """
                kwargs['content'] = html
            return HttpResponse(**kwargs)
        self.view = view

    def test_insert_script_tag(self):
        "Insert script tag for setting cookie in the <head>."
        response = self.view(self.request)
        self.assertFalse(b'</script>' in response.content)
        response = self.middleware.process_response(self.request, response)
        self.assertTrue(b'</script>' in response.content)
        # Do a little more digging to ensure it's inside <head>
        pattern = re.compile(b'<head>(?P<inner>.*)</head>', re.MULTILINE | re.DOTALL)
        # Parsing HTML with regex is not possible in general but we have
        # control over the exact HTML
        head = pattern.search(response.content).groupdict()['inner']
        self.assertIn(b'</script>', head)

    def test_non_html_content_type(self):
        "Don't insert if the content type is not html or xhtml."
        response = self.view(self.request, content='{}', content_type='application/json')
        response = self.middleware.process_response(self.request, response)
        self.assertNotIn(b'</script>', response.content)

    def test_gzipped_html(self):
        "Don't insert if the content had been gzipped."
        response = self.view(self.request)
        response['Content-Encoding'] = 'gzip'
        response = self.middleware.process_response(self.request, response)
        self.assertNotIn(b'</script>', response.content)

    def test_unicode_content(self):
        "Ensure insertion will still work with unicode body content."
        html = b"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"  
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">  
        <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">  
            <head>  
                <meta http-equiv="content-type" content="text/html; charset=utf-8"/>  
                <title>title</title>
            </head>
            <body>\xc2\x80abc</body>  
        </html>
        """
        response = self.view(self.request, content=html)
        self.assertNotIn(b'</script>', response.content)
        response = self.middleware.process_response(self.request, response)
        self.assertIn(b'</script>', response.content)

    def test_streaming_response(self):
        "Tag will not be added to a streaming response."
        if StreamingHttpResponse is None:
            self.skipTest('No StreamingHttpResponse')
        else:
            view = lambda r: StreamingHttpResponse(b'')
            response = view(self.request)
            response = self.middleware.process_response(self.request, response)
            self.assertNotIn(b'</script>', response.streaming_content)
