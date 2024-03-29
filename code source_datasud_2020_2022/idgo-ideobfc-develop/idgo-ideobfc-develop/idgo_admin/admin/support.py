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


from django.contrib import admin

from idgo_admin.models.support import Support


class SupportAdmin(admin.ModelAdmin):
    change_list_template = 'admin/idgo_admin/support_change_list.html'
    list_display = ['slug', 'name', 'description']
    ordering = ['slug']
    can_add_related = False
    can_delete_related = False
    search_fields = ['name', ]
    actions = None

    # Si on veut ajouter des actions ultérieurs tout en empechant
    # l'action de suppression depuis la liste
    # def get_actions(self, request):
    #     actions = super().get_actions(request)
    #     if 'delete_selected' in actions:
    #         del actions['delete_selected']
    #     return actions


admin.site.register(Support, SupportAdmin)
