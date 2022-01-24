# Copyright (c) 2017-2021 Neogeo-Technologies.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import importlib
import sys

from django.conf import settings


default_app_config = 'idgo_troubleshooting.apps.IdgoTroubleshootingConfig'


this = sys.modules[__name__]
module_name = '.celery'
module_celery = importlib.import_module(module_name, package=this.__name__)
celery_app = module_celery.celery_app


__all__ = [
    'celery_app',
]


# Set settings module attributes:
# ===============================

MANDATORY = (
    'CKAN_URL',
)

OPTIONAL = ()

for KEY in MANDATORY:
    try:
        setattr(this, KEY, getattr(settings, KEY))
    except AttributeError as e:
        raise AssertionError("Missing mandatory parameter: %s" % e.__str__())

for KEY, VALUE in OPTIONAL:
    setattr(this, KEY, getattr(settings, KEY, VALUE))
