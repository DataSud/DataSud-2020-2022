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
from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from idgo_admin.models.mail import sender as mail_sender

from idgo_cadastre_order.forms import OrderForm

from idgo_admin import IDGO_USER_PARTNER_LABEL_PLURAL

from idgo_cadastre_order import IDGO_CADASTRE_ORDER_CONTACT_EMAIL
from idgo_cadastre_order import IDGO_CADASTRE_ORDER_CC_EMAIL
from idgo_cadastre_order import IDGO_CADASTRE_ORDER_REDUCED_TO_PARTNER


def upload_file(request):
    user = request.user
    if not request.user.is_authenticated:
        message = ("La commande de fichiers fonciers est réservée "
                   "aux {partner_lbl_plu}. Veuillez vous connecter pour "
                   "accéder au formulaire. "
                   ).format(partner_lbl_plu=IDGO_USER_PARTNER_LABEL_PLURAL)
        messages.info(request, message)
        return redirect('{path}?next={next}'.format(
            path=reverse(settings.LOGIN_URL), next=request.path))

    profile = request.user.profile
    if IDGO_CADASTRE_ORDER_REDUCED_TO_PARTNER and not profile.crige_membership:
        return render(request, 'idgo_cadastre_order/forbidden.html')

    if request.method == 'POST':
        # crée une instance formulaire et la peuple avec des données provenant de la requête
        form = OrderForm(request.POST, request.FILES, user=user)

        if form.is_valid():
            order = form.save(commit=False)
            # peuplement de l'instance applicant du modèle form (= user_id)
            order.applicant = user
            order.organisation = profile.organisation
            order.save()

            attach_files = [
                order.dpo_cnil.file.name,
                order.acte_engagement.file.name]

            mail_kwargs = {
                'attach_files': attach_files,
                'full_name': user.get_full_name(),
                'last_name': user.last_name,
                'first_name': user.first_name,
                'date': timezone.now().date().strftime('%d/%m/%Y'),
                'email': user.email}

            mail_sender(
                'cadastre_order',
                to=[user.email],
                cc=IDGO_CADASTRE_ORDER_CC_EMAIL,
                **mail_kwargs,
                )

            mail_sender(
                'confirm_cadastre_order',
                to=[IDGO_CADASTRE_ORDER_CONTACT_EMAIL],
                cc=IDGO_CADASTRE_ORDER_CC_EMAIL,
                url=request.build_absolute_uri(
                    reverse('admin:idgo_cadastre_order_order_change', args=(order.id,))),
                **mail_kwargs,
                )

            message = (
                "Votre commande de fichiers fonciers a bien été envoyée. "
                "Vous recevrez un e-mail récapitulatif d'ici quelques minutes."
                )
            return render(
                request, 'idgo_admin/message.html', {'message': message})

    # si on reçoit un GET (ou autre méthode) un formulaire vide est renvoyé
    else:
        form = OrderForm(user=user)
    return render(request, 'idgo_cadastre_order/order.html', {'form': form})
