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


from api.views.dataset import DatasetList
from api.views.dataset import DatasetShow
from api.views.dataset import DatasetMDShow
from api.views.layer import LayerList
from api.views.layer import LayerShow
from api.views.layer_style import LayerStyleDefaultShow
from api.views.organisation import OrganisationList
from api.views.organisation import OrganisationShow
from api.views.resource import ResourceList
from api.views.resource import ResourceShow
from api.views.user import UserList
from api.views.user import UserShow
from api.views.resource_access import ResourceAccessList
from api.views.resource_access import ResourceAccessShow



__all__ = [
    DatasetList,
    DatasetShow,
    DatasetMDShow,
    LayerList,
    LayerShow,
    LayerStyleDefaultShow,
    OrganisationList,
    OrganisationShow,
    ResourceList,
    ResourceShow,
    UserList,
    UserShow,
    ]
