
def device_info(request):
    "Add processed device info into the template context."
    default = {'width': None, 'height': None}
    return {'device_info': getattr(request, 'device_info', default)}
