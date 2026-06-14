from constance import config


def shared_variables(request):
    return {"app_title": config.APP_TITLE}
