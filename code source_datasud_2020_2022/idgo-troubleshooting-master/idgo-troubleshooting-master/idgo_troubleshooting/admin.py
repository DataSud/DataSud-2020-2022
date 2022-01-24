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


from functools import update_wrapper
import logging

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import DropdownFilter

from idgo_troubleshooting.models import DeadLinkResource
from idgo_troubleshooting.models import OrphanCkanObject
from idgo_troubleshooting.models import OutdatedResource
from idgo_troubleshooting.models import UndocumentedPackage


logger = logging.getLogger(__name__)


URL_REF = "<a href='{url}'>{url}</a>"
LINK_TITLE = "Lien CKAN"


class OutdatedResourceAdmin(admin.ModelAdmin):

    list_display = (
        'resource_name',
        'show_resource_ckanurl',
        'package_name',
        'organization',
        'lastupdate',
        'resource_frequency',
        'delay',
        'last_log',
    )

    def show_resource_ckanurl(self, obj):
        return format_html(URL_REF, url=obj.resource_ckanurl)

    show_resource_ckanurl.short_description = LINK_TITLE

    list_filter = (
        ('resource_name', DropdownFilter),
        ('organization', DropdownFilter),
        ('package_name', DropdownFilter),
        ('lastupdate', DropdownFilter),
        ('resource_frequency', DropdownFilter),
        ('delay', DropdownFilter),
        ('last_log', DropdownFilter)
    )

    ordering = (
        'resource_name',
        'package_name',
        'organization',
        'lastupdate',
        'delay',
        'last_log',
    )


class UndocumentedPackageAdmin(admin.ModelAdmin):

    list_display = (
        'package_name',
        'show_package_ckanurl',
        'organization',
        'last_log',
    )

    def show_package_ckanurl(self, obj):
        return format_html(URL_REF, url=obj.package_ckanurl)

    show_package_ckanurl.short_description = LINK_TITLE

    list_filter = (
        ('package_name', DropdownFilter),
        ('package_ckanurl', DropdownFilter),
        ('organization', DropdownFilter),
        ('last_log', DropdownFilter)
    )

    ordering = (
        'package_name',
        'package_ckanurl',
        'organization',
        'last_log',
    )


class DeadLinkResourceAdmin(admin.ModelAdmin):

    list_display = (
        'resource_name',
        'show_resource_ckanurl',
        'show_external_link',
        'package_name',
        'organization',
        'last_log',
    )

    def show_external_link(self, obj):
        return format_html(URL_REF, url=obj.external_link)

    show_external_link.short_description = "Lien en erreur"

    def show_resource_ckanurl(self, obj):
        return format_html(URL_REF, url=obj.resource_ckanurl)

    show_resource_ckanurl.short_description = LINK_TITLE

    list_filter = (
        ('resource_name', DropdownFilter),
        ('resource_ckanurl', DropdownFilter),
        ('external_link', DropdownFilter),
        ('package_name', DropdownFilter),
        ('organization', DropdownFilter),
        ('last_log', DropdownFilter)
    )

    ordering = (
        'resource_name',
        'package_name',
        'organization',
        'last_log',
    )


class OrphanCkanObjectForm(forms.ModelForm):
    class Meta(object):
        model = OrphanCkanObject
        fields = (
            'object_location',
            'object_name',
            'object_id',
        )


class OrphanCkanObjectAdmin(admin.ModelAdmin):
    form = OrphanCkanObjectForm
    list_display = (
        'object_location',
        'object_name',
    )
    list_filter = (
        'object_name',
    )
    readonly_fields = (
        'object_location',
        'object_name',
        'object_id',
    )

    def _call_command(self, command_name, request, qs=None):
        try:
            call_command(command_name, queryset=qs)
        except Exception as err:
            logger.exception(err)
            messages.error(request, "Command failed")
        else:
            msg = "Command passed successfully"
            messages.success(request, msg)

        opts = self.model._meta
        info = opts.app_label, opts.model_name
        redirect_url = reverse(
            'admin:%s_%s_changelist' % info, current_app=self.admin_site.name)

        preserved_filters = self.get_preserved_filters(request)
        context = {
            'preserved_filters': preserved_filters,
            'opts': opts,
        }
        redirect_url = add_preserved_filters(context, redirect_url)
        return HttpResponseRedirect(redirect_url)

    def auto_add(self, request):
        return self._call_command('search_orphan_ckan_objects', request)

    def clear_all(self, request):
        return self._call_command('clear_orphan_ckan_objects', request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_auto_add_permission(self, request):
        return True

    def has_clear_all_permission(self, request):
        return True

    def changelist_view(self, request):
        return super().changelist_view(
            request, extra_context={
                'has_auto_add_permission': self.has_auto_add_permission(request),
                'has_clear_all_permission': self.has_clear_all_permission(request),
            }
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_urls(self):
        from django.conf.urls import url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url(r'^$', wrap(self.changelist_view), name='%s_%s_changelist' % info),
            url(r'^auto_add/$', wrap(self.auto_add), name='%s_%s_auto_add' % info),
            url(r'^clear_all/$', wrap(self.clear_all), name='%s_%s_clear_all' % info),
            url(r'^(.+)/history/$', wrap(self.history_view), name='%s_%s_history' % info),
            url(r'^(.+)/delete/$', wrap(self.delete_view), name='%s_%s_delete' % info),
            url(r'^(.+)/change/$', wrap(self.change_view), name='%s_%s_change' % info),
        ]
        return urlpatterns


admin.site.register(OutdatedResource, OutdatedResourceAdmin)
admin.site.register(UndocumentedPackage, UndocumentedPackageAdmin)
admin.site.register(DeadLinkResource, DeadLinkResourceAdmin)
admin.site.register(OrphanCkanObject, OrphanCkanObjectAdmin)
