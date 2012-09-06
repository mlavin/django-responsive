from __future__ import unicode_literals

from django.conf import settings

# Name, Max Width (inclusive)
DEFAULT_BREAKPOINTS = {
    'phone': 480,
    'tablet': 767,
    'desktop': None,
}

BREAKPOINTS = getattr(settings, 'RESPONSIVE_BREAKPOINTS', DEFAULT_BREAKPOINTS)
