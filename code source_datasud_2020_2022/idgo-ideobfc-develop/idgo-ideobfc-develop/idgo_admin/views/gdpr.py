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


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import render

from mama_cas.utils import redirect as mama_redirect

from idgo_admin.models import Gdpr
from idgo_admin.models import GdprUser

from idgo_admin import LOGIN_URL


decorators = [csrf_exempt, login_required(login_url=LOGIN_URL)]
@method_decorator(decorators, name='dispatch')
class GdprView(View):

    def get(self, request):
        context = {'terms': Gdpr.objects.latest('issue_date')}
        return render(
            request, 'idgo_admin/gdpr.html', context=context)

    def post(self, request):
        GdprUser.objects.create(user=request.user, gdpr=Gdpr.objects.latest('issue_date'))
        return mama_redirect('idgo_admin:list_my_datasets')
