# Copyright (c) 2017-2020 Neogeo-Technologies.
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


default_app_config = 'idgo_cadastre_order.apps.IdgoCadastreOrderConfig'

import os  # noqa E402
import sys  # noqa E402
this = sys.modules[__name__]

from django.conf import settings  # noqa E402


MANDATORY = (
    'IDGO_CADASTRE_ORDER_CONTACT_EMAIL',
    'IDGO_CADASTRE_ORDER_COMMITMENT_HREF',
    )

OPTIONAL = (
    ('IDGO_CADASTRE_ORDER_CC_EMAIL', []),
    ('IDGO_CADASTRE_ORDER_DOCUMENTATION', None),
    ('IDGO_CADASTRE_ORDER_DPO_HREF', 'https://www.cnil.fr/fr/designation-dpo'),
    ('IDGO_CADASTRE_ORDER_PROCESSING_TIME', '15 jours'),
    ('IDGO_CADASTRE_ORDER_REDUCED_TO_PARTNER', True),
    )

for KEY in MANDATORY:
    try:
        setattr(this, KEY, getattr(settings, KEY))
    except AttributeError as e:
        raise AssertionError("Missing mandatory parameter: %s" % e.__str__())

for KEY, VALUE in OPTIONAL:
    setattr(this, KEY, getattr(settings, KEY, VALUE))
