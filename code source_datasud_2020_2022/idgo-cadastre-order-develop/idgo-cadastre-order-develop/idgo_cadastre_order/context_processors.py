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


from django.conf import settings

from idgo_admin import HREF_WWW
from idgo_admin import DEFAULT_PLATFORM_NAME
from idgo_admin import IDGO_USER_PARTNER_LABEL_PLURAL

from idgo_cadastre_order import IDGO_CADASTRE_ORDER_COMMITMENT_HREF
from idgo_cadastre_order import IDGO_CADASTRE_ORDER_DOCUMENTATION
from idgo_cadastre_order import IDGO_CADASTRE_ORDER_DPO_HREF
from idgo_cadastre_order import IDGO_CADASTRE_ORDER_PROCESSING_TIME


def global_vars(request):
    return {
        'HREF_WWW': HREF_WWW,
        'DEFAULT_PLATFORM_NAME': DEFAULT_PLATFORM_NAME,
        'IDGO_CADASTRE_ORDER_COMMITMENT_HREF': IDGO_CADASTRE_ORDER_COMMITMENT_HREF,
        'IDGO_CADASTRE_ORDER_DOCUMENTATION': IDGO_CADASTRE_ORDER_DOCUMENTATION,
        'IDGO_CADASTRE_ORDER_DPO_HREF': IDGO_CADASTRE_ORDER_DPO_HREF,
        'IDGO_CADASTRE_ORDER_PROCESSING_TIME': IDGO_CADASTRE_ORDER_PROCESSING_TIME,
        'IDGO_USER_PARTNER_LABEL_PLURAL': IDGO_USER_PARTNER_LABEL_PLURAL,
        }
