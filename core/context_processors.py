from .models import SiteSetting


def site_settings(request):
    settings_obj, _ = SiteSetting.objects.get_or_create(id=1)
    return {'site_settings': settings_obj}
