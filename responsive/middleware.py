"Middleware to inject necessary JS and include device info on the request."
from __future__ import unicode_literals

import os
import re

from .context_processors import _get_device_type

try:
    from django.utils.encoding import smart_bytes
except ImportError:
    # Django < 1.5 so no Python 3 support
    smart_bytes = bytes


_HTML_TYPES = ('text/html', 'application/xhtml+xml')


class DeviceInfoMiddleware(object):
    "Reads device info from the cookie and makes it available on the request."

    def process_request(self, request):
        "Read cookie and populate device size info."
        value = request.COOKIES.get('resolution', None)
        width = None
        height = None
        pixelratio = None
        if value is not None:
            try:
                width, height, pixelratio = value.split(':')
                width, height, pixelratio = int(width), int(height), float(pixelratio)
            except ValueError:
                # TODO: Add logging
                width = None
                height = None
                pixelratio = None
        info = {'width': width, 'height': height, 'pixelratio': pixelratio}
        if width is not None:
            info['type'] = _get_device_type(width)
        else:
            info['type'] = None
        request.device_info = info

    def process_response(self, request, response):
        "Insert necessary javascript to set device info cookie."
        if not getattr(response, 'streaming', False):
            is_gzipped = 'gzip' in response.get('Content-Encoding', '')
            is_html = response.get('Content-Type', '').split(';')[0] in _HTML_TYPES
            if is_html and not is_gzipped:
                pattern = re.compile(b'<head>', re.IGNORECASE)
                path = os.path.join(os.path.dirname(__file__), 'static', 'responsive')
                with open(os.path.join(path, 'js', 'responsive.min.js'), 'r') as f:
                    js = f.read()
                script = b'<script type="text/javascript">' + smart_bytes(js) + b'</script>'
                response.content = pattern.sub(b'<head>' + script, response.content)
                if response.get('Content-Length', None):
                    response['Content-Length'] = len(response.content)
        return response
