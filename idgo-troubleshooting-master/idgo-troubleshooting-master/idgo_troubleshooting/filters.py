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


from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Q

from idgo_troubleshooting.models import DeadLinkResource
from idgo_troubleshooting.models import OutdatedResource
from idgo_troubleshooting.models import UndocumentedPackage


TEMPLATE = 'admin/idgo_troubleshooting/dropdown_filter.html'


class OutdatedResourceFilter(SimpleListFilter):
    """
    Turns classic Django administrator interface filter into a drop-down list
    """
    template = TEMPLATE

    def lookups(self, request, model_admin):
        return OutdatedResource.objects.all().values_list('pk', 'title')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(_from__outdated__pk=self.value()) | Q(
                    _to__outdated__pk=self.value())
            )

        return queryset


class UndocumentedPackageFilter(SimpleListFilter):
    """
    Turns classic Django administrator interface filter into a drop-down list
    """
    template = TEMPLATE

    def lookups(self, request, model_admin):
        return UndocumentedPackage.objects.all().values_list('pk', 'title')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(_from__undocumented__pk=self.value()) | Q(
                    _to__undocumented__pk=self.value())
            )

        return queryset


class DeadlinkResourceFilter(SimpleListFilter):
    """
    Turns classic Django administrator interface filter into a drop-down list
    """
    template = TEMPLATE

    def lookups(self, request, model_admin):
        return DeadLinkResource.objects.all().values_list('pk', 'title')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(_from__resource__pk=self.value()) | Q(
                    _to__resource__pk=self.value())
            )

        return queryset
