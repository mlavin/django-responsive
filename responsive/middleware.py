"Middleware to inject necessary JS and include device info on the request."

import os
import re

from django.utils.encoding import force_unicode


_HTML_TYPES = ('text/html', 'application/xhtml+xml')


class DeviceInfoMiddleware(object):
    "Reads device info from the cookie and makes it available on the request."

    def process_request(self, request):
        "Read cookie and populate device size info."
        value = request.COOKIES.get('resolution', None)
        width = None
        height = None
        if value is not None:
            try:
                width, height = value.split(':')
                width, height = int(width), int(height)
            except ValueError:
                # TODO: Add logging
                width = None
                height = None
        request.device_info = {'width': width, 'height': height}

    def process_response(self, request, response):
        "Insert necessary javascript to set device info cookie."
        is_gzipped = 'gzip' in response.get('Content-Encoding', '')
        is_html = response.get('Content-Type', '').split(';')[0] in _HTML_TYPES
        if is_html and not is_gzipped:
            pattern = re.compile(u"<head>", re.IGNORECASE)
            path = os.path.join(os.path.dirname(__file__), 'static', 'responsive')
            with open(os.path.join(path, 'js', 'responsive.min.js'), 'r') as f:
                js = f.read()
            script = u'<script type="text/javascript">{0}</script>'.format(js)
            response.content = pattern.sub(u"<head>{0}".format(script), force_unicode(response.content))
            if response.get('Content-Length', None):
                response['Content-Length'] = len(response.content)
        return response
