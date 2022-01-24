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


from django import forms
from django.utils import timezone

from idgo_admin.models import Profile
from idgo_cadastre_order.models import Order


class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'idgo_admin/widgets/file_drop_zone.html'


class OrderForm(forms.ModelForm):

    class Meta(object):
        model = Order
        fields = [
            'dpo_cnil',
            'acte_engagement']

    dpo_cnil = forms.FileField(
        label="Déclaration CNIL désignant le DPO de l'organisation*",
        required=True,
        widget=CustomClearableFileInput(attrs={'value': None}),
        )

    acte_engagement = forms.FileField(
        label="Acte d'engagement DGFIP*",
        required=True,
        widget=CustomClearableFileInput(attrs={'value': None}),
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        year = timezone.now().date().year
        match = Order.objects.filter(
            date__year=year,
            status=1,
            applicant__in=[
                profile.user for profile
                in Profile.objects.filter(organisation=self.user.profile.organisation)],
            )

        if match.exists():
            er_mess = (
                "Une demande a déjà été approuvée pour cette organisation "
                "dans l'année civile en cours."
                )
            raise forms.ValidationError(er_mess)

        return cleaned_data
