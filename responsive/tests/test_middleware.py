import re

from django.http import HttpResponse
from django.test.client import RequestFactory
from django.utils import unittest


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

    def test_process_request_invalid_cook(self):
        "Process a request which has an invalid value in the cookie."
        self.request.COOKIES['resolution'] = 'XXXXXXXXXXXXXXX'
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device_info'))
        device = self.request.device_info
        self.assertEqual(device['width'], None)
        self.assertEqual(device['height'], None)

    def test_process_request_valid_cookie(self):
        "Read data from the cookie and make it available on the request."
        self.request.COOKIES['resolution'] = '320:480'
        self.middleware.process_request(request=self.request)
        self.assertTrue(hasattr(self.request, 'device_info'))
        device = self.request.device_info
        self.assertEqual(device['width'], 320)
        self.assertEqual(device['height'], 480)


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
                html = """
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
        self.assertFalse('</script>' in response.content)
        response = self.middleware.process_response(self.request, response)
        self.assertTrue('</script>' in response.content)
        # Do a little more digging to ensure it's inside <head>
        pattern = re.compile(r'<head>(?P<inner>.*)</head>', re.MULTILINE | re.DOTALL)
        # Parsing HTML with regex is not possible in general but we have
        # control over the exact HTML
        head = pattern.search(response.content).groupdict()['inner']
        self.assertTrue('</script>' in head)

    def test_non_html_content_type(self):
        "Don't insert if the content type is not html or xhtml."
        response = self.view(self.request, content='{}', content_type='application/json')
        response = self.middleware.process_response(self.request, response)
        self.assertFalse('</script>' in response.content)

    def test_gzipped_html(self):
        "Don't insert if the content had been gzipped."
        response = self.view(self.request)
        response['Content-Encoding'] = 'gzip'
        response = self.middleware.process_response(self.request, response)
        self.assertFalse('</script>' in response.content)

    def test_unicode_content(self):
        "Ensure insertion will still work with unicode body content."
        html = u"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"  
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">  
        <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">  
            <head>  
                <meta http-equiv="content-type" content="text/html; charset=utf-8"/>  
                <title>title</title>
            </head>
            <body>\x80abc</body>  
        </html>
        """
        response = self.view(self.request, content=html)
        self.assertFalse('</script>' in response.content)
        response = self.middleware.process_response(self.request, response)
        self.assertTrue('</script>' in response.content)
