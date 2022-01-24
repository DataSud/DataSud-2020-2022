# coding: utf8


from ckan.common import c
from ckan.common import config


def restricted_get_user_id():
    return (str(c.user))


def restricted_alternate_login_url():
    return config.get('ckanext.restricted.alternate_login_url', None)
