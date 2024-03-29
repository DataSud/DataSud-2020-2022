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


import operator
import warnings

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from idgo_admin.exceptions import CriticalError
from idgo_admin.exceptions import GenericException
from idgo_admin.forms.organisation import OrganisationForm as Form
from idgo_admin.models import AccountActions
from idgo_admin.models import BaseMaps
from idgo_admin.models import Category
from idgo_admin.models import Dataset
from idgo_admin.models import LiaisonsContributeurs
from idgo_admin.models import LiaisonsReferents
from idgo_admin.models import License
from idgo_admin.models.mail import send_contributor_confirmation_mail
from idgo_admin.models.mail import send_mail_asking_for_idgo_partnership
from idgo_admin.models.mail import send_membership_confirmation_mail
from idgo_admin.models.mail import send_organisation_creation_confirmation_mail
from idgo_admin.models.mail import send_referent_confirmation_mail
from idgo_admin.models import Organisation
from idgo_admin.models import SupportedCrs
from idgo_admin.mra_client import MRAHandler

from idgo_admin import IDGO_ORGANISATION_PARTNER_LABEL
from idgo_admin import LOGIN_URL


decorators = [csrf_exempt, login_required(login_url=LOGIN_URL)]


def creation_process(request, profile, organisation, mail=True):
    action = AccountActions.objects.create(
        action='confirm_new_organisation',
        organisation=organisation,
        profile=profile)
    if mail:
        url = request.build_absolute_uri(
            reverse('idgo_admin:confirm_new_orga', kwargs={'key': action.key}))
        send_organisation_creation_confirmation_mail(profile.user, organisation, url)
    return action


def member_subscribe_process(request, profile, organisation, mail=True):
    action = AccountActions.objects.create(
        action='confirm_rattachement',
        organisation=organisation,
        profile=profile)

    if mail:
        url = request.build_absolute_uri(
            reverse('idgo_admin:confirm_rattachement', kwargs={'key': action.key}))
        send_membership_confirmation_mail(profile.user, organisation, url)
    return action


def member_unsubscribe_process(request, profile, organisation):
    if profile.organisation != organisation:
        raise GenericException()
    if profile.organisation.is_crige_partner:
        profile.crige_membership = False
    profile.organisation = None
    profile.membership = False
    profile.save()


def contributor_subscribe_process(request, profile, organisation, mail=True):
    LiaisonsContributeurs.objects.get_or_create(
        profile=profile,
        organisation=organisation)
    action = AccountActions.objects.create(
        action='confirm_contribution',
        organisation=organisation,
        profile=profile)
    if mail:
        url = request.build_absolute_uri(
            reverse('idgo_admin:confirm_contribution', kwargs={'key': action.key}))
        send_contributor_confirmation_mail(profile.user, organisation, url)
    return action


def contributor_unsubscribe_process(request, profile, organisation):
    LiaisonsContributeurs.objects.get(
        organisation=organisation, profile=profile).delete()


def referent_subscribe_process(request, profile, organisation, mail=True):
    if not LiaisonsContributeurs.objects.filter(
            organisation=organisation, profile=profile).exists():
        contributor_subscribe_process(request, profile, organisation, mail=False)

    LiaisonsReferents.objects.get_or_create(
        organisation=organisation, profile=profile, validated_on=None)
    action = AccountActions.objects.create(
        action='confirm_referent',
        organisation=organisation, profile=profile)

    if mail:
        url = request.build_absolute_uri(
            reverse('idgo_admin:confirm_referent', kwargs={'key': action.key}))
        send_referent_confirmation_mail(profile.user, organisation, url)
    return action


def referent_unsubscribe_process(request, profile, organisation):
    LiaisonsReferents.objects.get(
        organisation=organisation, profile=profile).delete()


@login_required(login_url=LOGIN_URL)
@csrf_exempt
def idgo_partnership(request):
    id = request.GET.get('id')
    if not id:
        raise Http404()
    user = request.user
    organisation = get_object_or_404(Organisation, id=id, is_active=True)
    send_mail_asking_for_idgo_partnership(user, organisation)


@login_required(login_url=LOGIN_URL)
@csrf_exempt
def handle_show_organisation(request, *args, **kwargs):
    profile = request.user.profile

    pk = request.GET.get('id')
    if pk:
        try:
            pk = int(pk)
        except Exception:
            raise Http404()
    else:
        if profile.organisation:
            pk = profile.organisation.pk
        elif profile.is_referent:
            pk = profile.referent_for[0].pk
        elif profile.is_contributor:
            pk = profile.contribute_for[0].pk
    try:
        organisation = Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        if Organisation.objects.count() == 0:
            return redirect('idgo_admin:create_organisation')
        id = Organisation.objects.first().id
    else:
        id = organisation.id
    return redirect('idgo_admin:show_organisation', id=id)


@login_required(login_url=LOGIN_URL)
@csrf_exempt
def show_organisation(request, id, *args, **kwargs):
    profile = request.user.profile

    all_organisations = []
    for instance in Organisation.objects.filter(is_active=True):
        all_organisations.append({
            'pk': instance.pk,
            'legal_name': instance.legal_name,
            'member': (instance == profile.organisation),
            'contributor': (instance in profile.contribute_for),
            'referent': profile.is_admin and True or (instance in profile.referent_for),
            })
    all_organisations.sort(key=operator.itemgetter('contributor'), reverse=True)
    all_organisations.sort(key=operator.itemgetter('referent'), reverse=True)
    all_organisations.sort(key=operator.itemgetter('member'), reverse=True)

    try:
        organisation = Organisation.objects.get(pk=id)
    except Organisation.DoesNotExist:
        organisation = None

    context = {
        'all_organisations': all_organisations,
        'basemaps': BaseMaps.objects.all(),
        'organisation': organisation,
        }

    return render(request, 'idgo_admin/organisation/show.html', context=context)


@method_decorator(decorators, name='dispatch')
class CreateOrganisation(View):

    template = 'idgo_admin/organisation/edit.html'

    def get(self, request):
        context = {'form': Form(include={'user': request.user, 'extended': True})}
        return render(request, self.template, context=context)

    def post(self, request):
        user = request.user
        profile = user.profile

        form = Form(request.POST, request.FILES, include={'user': user})
        if not form.is_valid():
            return render(
                request, self.template, context={'form': form})

        try:
            organisation = Organisation.objects.create(**dict(
                (item, form.cleaned_data[item])
                for item in form.Meta.organisation_fields))
        except ValidationError as e:
            messages.error(request, e.__str__())
            return render(request, self.template, context={'form': form})

        creation_process(request, profile, organisation)

        form.cleaned_data.get('rattachement_process', False) \
            and member_subscribe_process(request, profile, organisation)

        # Dans le cas ou seul le role de contributeur est demandé
        form.cleaned_data.get('contributor_process', False) \
            and not form.cleaned_data.get('referent_process', False) \
            and contributor_subscribe_process(request, profile, organisation)

        # role de référent requis donc role de contributeur requis
        form.cleaned_data.get('referent_process', False) \
            and referent_subscribe_process(request, profile, organisation)

        messages.success(request, "La demande a bien été envoyée.")

        return redirect('idgo_admin:handle_show_organisation')


@method_decorator(decorators, name='dispatch')
class UpdateOrganisation(View):
    template = 'idgo_admin/organisation/edit.html'

    def get(self, request, id=None):
        organisation = get_object_or_404(Organisation, id=id)

        user = request.user
        profile = user.profile

        is_admin = profile.is_admin
        is_referent = LiaisonsReferents.objects.filter(
            profile=profile, organisation__id=id,
            validated_on__isnull=False) and True or False

        if not (is_referent or is_admin):
            raise Http404()

        return render(
            request, self.template, context={
                'id': id,
                'update': True,
                'organisation': organisation,
                'form': Form(instance=organisation,
                             include={'user': user, 'id': id})})

    def post(self, request, id=None):
        organisation = get_object_or_404(Organisation, id=id)

        user = request.user
        profile = user.profile

        is_admin = profile.is_admin
        is_referent = LiaisonsReferents.objects.filter(
            profile=profile, organisation__id=id,
            validated_on__isnull=False) and True or False

        if not (is_referent or is_admin):
            raise Http404()

        form = Form(request.POST, request.FILES,
                    instance=organisation, include={'user': user, 'id': id})

        if not form.is_valid():
            return render(
                request, self.template, context={'id': id, 'form': form})

        for item in form.Meta.fields:
            setattr(organisation, item, form.cleaned_data[item])
        try:
            organisation.save()
        except ValidationError as e:
            messages.error(request, e.__str__())
        except CkanBaseError as e:
            form.add_error('__all__', e.__str__())
            messages.error(request, e.__str__())
        else:
            messages.success(
                request, "L'organisation a été mise à jour avec succès.")

        if 'continue' in request.POST:
            context = {
                'id': id,
                'update': True,
                'organisation': organisation,
                'form': Form(
                    instance=organisation, include={'user': user, 'id': id})}
            return render(
                request, self.template, context=context)

        return HttpResponseRedirect(
            reverse('idgo_admin:show_organisation', kwargs={'id': organisation.id}))


@method_decorator(decorators, name='dispatch')
class OrganisationOWS(View):

    def post(self, request):
        id = request.GET.get('id')
        if not id:
            raise Http404()
        organisation = get_object_or_404(Organisation, id=id)

        user = request.user
        profile = user.profile

        is_admin = profile.is_admin
        is_referent = LiaisonsReferents.objects.filter(
            profile=profile, organisation__id=id,
            validated_on__isnull=False) and True or False

        if not (is_referent or is_admin):
            raise Http404()

        json = {
            'abstract': request.POST.get('abstract', None),
            'srs': [crs.authority for crs in SupportedCrs.objects.all()],
            'title': request.POST.get('title', None),
            }

        try:
            MRAHandler.update_ows_settings('ows', json, ws_name=organisation.slug)
        except Exception as e:
            messages.error(request, e.__str__())
        else:
            messages.success(request, "Le service OGC a été mis à jour avec succès.")

        return redirect('idgo_admin:show_organisation', id=id)

@method_decorator(decorators, name='dispatch')
class Subscription(View):

    def get(self, request, status=None, subscription=None):
        id = request.GET.get('id')
        if not id:
            raise Http404()
        organisation = get_object_or_404(Organisation, id=id)

        user = request.user
        profile = user.profile

        actions = {
            'member': {
                'subscribe': member_subscribe_process,
                'unsubscribe': member_unsubscribe_process,
                },
            'contributor': {
                'subscribe': contributor_subscribe_process,
                'unsubscribe': contributor_unsubscribe_process,
                },
            'referent': {
                'subscribe': referent_subscribe_process,
                'unsubscribe': referent_unsubscribe_process,
                },
            }

        status_fr_label = {
            'member': "membre",
            'contributor': "contributeur",
            'referent': "référent",
            }

        try:
            actions[status][subscription](request, profile, organisation)
        except Exception as e:
            messages.error(request, str(e))
        else:
            if subscription == 'unsubscribe':
                message = (
                    "Vous n'êtes plus %s de l'organisation "
                    "« <strong>%s</strong> »." % (
                        status_fr_label[status], organisation.legal_name
                    )
                )
            elif subscription == 'subscribe':
                message = (
                    "Votre demande de statut de <strong>%s</strong> de "
                    "l'organisation « <strong>%s</strong> » est en cours de "
                    "traitement. Celle-ci ne sera effective qu'après "
                    "validation par un administrateur." % (
                        status_fr_label[status], organisation.legal_name
                        )
                    )

                if status == 'member':
                    messages.info(request, (
                        "L'organisation est %s." % IDGO_ORGANISATION_PARTNER_LABEL
                        ))
            messages.success(request, message)

        return JsonResponse(data={})
        # TODO Supprimer AJAX et remplacer par `redirect('idgo_admin:show_organisation', id=id)`


from idgo_admin import ENABLE_CKAN_HARVESTER  # noqa
if ENABLE_CKAN_HARVESTER:

    from idgo_admin.ckan_module import CkanBaseError
    from idgo_admin.forms.organisation import RemoteCkanForm
    from idgo_admin.models import MappingCategory
    from idgo_admin.models import MappingLicence
    from idgo_admin.models import RemoteCkan

    # =======================
    # MOISSONNAGE DE SITE CKAN
    # =======================

    @method_decorator(decorators, name='dispatch')
    class RemoteCkanEditor(View):

        template = 'idgo_admin/organisation/remoteckan/edit.html'

        def get(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            context = {'organisation': organisation}

            try:
                instance = RemoteCkan.objects.get(organisation=organisation)
            except RemoteCkan.DoesNotExist:
                form = RemoteCkanForm()
            else:
                context['datasets'] = Dataset.harvested_ckan.filter(organisation=organisation)
                context['instance'] = instance
                form = RemoteCkanForm(instance=instance)

            context['form'] = form

            return render(
                request, self.template, context=context)

        def post(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            context = {'organisation': organisation}

            instance = None
            url = request.POST.get('url')
            try:
                with transaction.atomic():
                    instance, created = \
                        RemoteCkan.objects.get_or_create(
                            organisation=organisation, url=url)
            except CkanBaseError as e:
                form = RemoteCkanForm(request.POST)
                form.add_error('url', e.__str__())
            except ValidationError as e:
                form = RemoteCkanForm(request.POST)
                form.add_error(e.code, e.message)
            else:
                context['datasets'] = Dataset.harvested_ckan.filter(organisation=organisation)
                context['instance'] = instance
                form = RemoteCkanForm(request.POST, instance=instance)

            if not form.is_valid():
                messages.error(request, form._errors.__str__())
                return redirect('idgo_admin:edit_remote_ckan_link', id=organisation.id)

            try:
                with transaction.atomic():
                    self.map_categories(instance, request.POST, form)
                    self.map_licences(instance, request.POST, form)
            except ValidationError as e:
                error = True
                messages.error(request, e.__str__())
            except CkanBaseError as e:
                error = True
                form.add_error('__all__', e.__str__())
                messages.error(request, e.__str__())

            else:  # Une fois le mapping effectué, on sauvegarde l'instance
                context['form'] = form
                if not form.is_valid():
                    return render(
                        request, self.template, context=context)

                for k, v in form.cleaned_data.items():
                    setattr(instance, k, v)
                try:
                    # with transaction.atomic():
                    with warnings.catch_warnings(record=True) as caught_warnings:
                        instance.save()
                        for warn in caught_warnings:
                            messages.warning(request, str(warn.message))
                except ValidationError as e:
                    error = True
                    messages.error(request, e.__str__())
                except CkanBaseError as e:
                    error = True
                    form.add_error('__all__', e.__str__())
                    messages.error(request, e.__str__())
                except CriticalError as e:
                    error = True
                    form.add_error('__all__', e.__str__())
                    messages.error(request, e.__str__())
                else:
                    error = False
                    context['datasets'] = \
                        Dataset.harvested_ckan.filter(organisation=organisation)
                    context['form'] = RemoteCkanForm(instance=instance)
                    if created:
                        msg = "Veuillez indiquez les organisations distantes à moissonner."
                    else:
                        msg = "Les informations de moissonnage ont été mises à jour."
                    messages.success(request, msg)

            if 'continue' in request.POST or error:
                namespace = 'idgo_admin:edit_remote_ckan_link'
            else:
                namespace = 'idgo_admin:update_organisation'

            return redirect(namespace, id=organisation.id)

        def map_categories(self, instance, mapper, form):
            MappingCategory.objects.filter(remote_ckan=instance).delete()

            data = list(filter(
                lambda k: k in [el.name for el in form.get_category_fields()],
                mapper.dict().keys()))
            not_empty = {k: mapper.dict()[k] for k in data if mapper.dict()[k]}
            for k, v in not_empty.items():
                MappingCategory.objects.create(
                    remote_ckan=instance, category=Category.objects.get(id=v), slug=k[4:])

        def map_licences(self, instance, mapper, form):
            MappingLicence.objects.filter(remote_ckan=instance).delete()

            data = list(filter(
                lambda k: k in [el.name for el in form.get_licence_fields()],
                mapper.dict().keys()))
            not_empty = {k: mapper.dict()[k] for k in data if mapper.dict()[k]}
            for k, v in not_empty.items():
                MappingLicence.objects.create(
                    remote_ckan=instance, licence=License.objects.get(slug=v), slug=k[4:])

    @method_decorator(decorators, name='dispatch')
    class DeleteRemoteCkanLinked(View):

        def post(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)
            instance = get_object_or_404(RemoteCkan, organisation=organisation)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            try:
                with transaction.atomic():
                    instance.delete()
            except ValidationError as e:
                messages.error(request, e.__str__())
            except CkanBaseError as e:
                messages.error(request, e.__str__())
            else:
                messages.success(request, (
                    'Les informations ainsi que les jeux de données et '
                    'ressources synchronisés avec le catalogue distant '
                    'ont été supprimés avec succès.'))

            return redirect('idgo_admin:update_organisation', id=organisation.id)


from idgo_admin import ENABLE_CSW_HARVESTER  # noqa
if ENABLE_CSW_HARVESTER:

    from idgo_admin.csw_module import CswBaseError
    from idgo_admin.forms.organisation import RemoteCswForm
    from idgo_admin.models import RemoteCsw

    # =======================
    # MOISSONNAGE DE SITE CSW
    # =======================

    @method_decorator(decorators, name='dispatch')
    class RemoteCswEditor(View):

        template = 'idgo_admin/organisation/remotecsw/edit.html'

        def get(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            context = {'organisation': organisation}

            try:
                instance = RemoteCsw.objects.get(organisation=organisation)
            except RemoteCsw.DoesNotExist:
                form = RemoteCswForm()
            else:
                context['datasets'] = Dataset.harvested_csw.filter(organisation=organisation)
                context['instance'] = instance
                form = RemoteCswForm(instance=instance)

            context['form'] = form

            return render(
                request, self.template, context=context)

        def post(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            context = {'organisation': organisation}

            url = request.POST.get('url')
            try:
                with transaction.atomic():
                    instance, created = \
                        RemoteCsw.objects.get_or_create(
                            organisation=organisation, url=url)
            except CswBaseError as e:
                form = RemoteCswForm(request.POST)
                form.add_error('url', e.__str__())
            except ValidationError as e:
                form = RemoteCswForm(request.POST)
                form.add_error(e.code, e.message)
            else:
                context['datasets'] = Dataset.harvested_csw.filter(organisation=organisation)
                context['instance'] = instance
                form = RemoteCswForm(request.POST, instance=instance)

            context['form'] = form

            if not form.is_valid():
                messages.error(request, form._errors.__str__())
                return redirect('idgo_admin:edit_remote_csw_link', id=organisation.id)

            for k, v in form.cleaned_data.items():
                setattr(instance, k, v)
            try:
                # with transaction.atomic():
                with warnings.catch_warnings(record=True) as caught_warnings:
                    instance.save(harvest=not created)
                    for warn in caught_warnings:
                        messages.warning(request, str(warn.message))
            except ValidationError as e:
                error = True
                messages.error(request, e.__str__())
            except CswBaseError as e:
                error = True
                form.add_error('__all__', e.__str__())
                messages.error(request, e.__str__())
            except CriticalError as e:
                error = True
                form.add_error('__all__', e.__str__())
                messages.error(request, e.__str__())
            else:
                error = False
                context['datasets'] = \
                    Dataset.harvested_csw.filter(organisation=organisation)
                context['form'] = RemoteCswForm(instance=instance)
                if created:
                    msg = "Veuillez indiquez une requête <strong>GetRecord</strong> avant moissonnage du service."
                else:
                    msg = "Les informations de moissonnage ont été mises à jour."
                messages.success(request, msg)

            if 'continue' in request.POST or error:
                return render(
                    request, self.template, context=context)

            return redirect('idgo_admin:update_organisation', id=organisation.id)

    @method_decorator(decorators, name='dispatch')
    class DeleteRemoteCswLinked(View):

        def post(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)
            instance = get_object_or_404(RemoteCsw, organisation=organisation)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            try:
                with transaction.atomic():
                    instance.delete()
            except ValidationError as e:
                messages.error(request, e.__str__())
            except CswBaseError as e:
                messages.error(request, e.__str__())
            else:
                messages.success(request, (
                    'Les informations ainsi que les jeux de données et '
                    'ressources synchronisés avec le catalogue distant '
                    'ont été supprimés avec succès.'))

            return redirect('idgo_admin:update_organisation', id=organisation.id)


from idgo_admin import ENABLE_DCAT_HARVESTER  # noqa
if ENABLE_DCAT_HARVESTER:

    from idgo_admin.dcat_module import DcatError
    from idgo_admin.dcat_module import DcatTimeoutError
    from idgo_admin.forms.organisation import RemoteDcatForm
    from idgo_admin.models import RemoteDcat

    # ========================
    # MOISSONNAGE DE SITE DCAT
    # ========================

    @method_decorator(decorators, name='dispatch')
    class RemoteDcatEditor(View):

        template = 'idgo_admin/organisation/remotedcat/edit.html'

        def get(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            context = {'organisation': organisation}

            try:
                instance = RemoteDcat.objects.get(organisation=organisation)
            except RemoteDcat.DoesNotExist:
                form = RemoteDcatForm()
            else:
                context['datasets'] = Dataset.harvested_dcat.filter(organisation=organisation)
                context['instance'] = instance
                form = RemoteDcatForm(instance=instance)

            context['form'] = form

            return render(
                request, self.template, context=context)

        def post(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            context = {'organisation': organisation}

            instance = None
            url = request.POST.get('url')
            try:
                with transaction.atomic():
                    instance, created = \
                        RemoteDcat.objects.get_or_create(
                            organisation=organisation, url=url)
            except (DcatError, DcatTimeoutError) as e:
                form = RemoteDcatForm(request.POST)
                form.add_error('url', e.__str__())
            except ValidationError as e:
                form = RemoteDcatForm(request.POST)
                form.add_error(e.code, e.message)
            else:
                context['datasets'] = Dataset.harvested_dcat.filter(organisation=organisation)
                context['instance'] = instance
                form = RemoteDcatForm(request.POST, instance=instance)

            if not form.is_valid():
                messages.error(request, form._errors.__str__())
                return redirect('idgo_admin:edit_remote_dcat_link', id=organisation.id)

            else:  # Une fois le mapping effectué, on sauvegarde l'instance
                context['form'] = form
                if not form.is_valid():
                    return render(
                        request, self.template, context=context)

                for k, v in form.cleaned_data.items():
                    setattr(instance, k, v)
                try:
                    # with transaction.atomic():
                    with warnings.catch_warnings(record=True) as caught_warnings:
                        instance.save(harvest=not created)
                        for warn in caught_warnings:
                            messages.warning(request, str(warn.message))
                except ValidationError as e:
                    error = True
                    messages.error(request, e.__str__())
                except (DcatError, DcatTimeoutError) as e:
                    error = True
                    form.add_error('__all__', e.__str__())
                    messages.error(request, e.__str__())
                except CriticalError as e:
                    error = True
                    form.add_error('__all__', e.__str__())
                    messages.error(request, e.__str__())
                else:
                    error = False
                    context['datasets'] = \
                        Dataset.harvested_dcat.filter(organisation=organisation)
                    context['form'] = RemoteDcatForm(instance=instance)
                    if created:
                        msg = "Veuillez configurer les informations ci-dessous et poursuivre le moissonnage du catalogue."
                    else:
                        msg = "Les informations de moissonnage ont été mises à jour."
                    messages.success(request, msg)

            if 'continue' in request.POST or error:
                namespace = 'idgo_admin:edit_remote_dcat_link'
            else:
                namespace = 'idgo_admin:update_organisation'

            return redirect(namespace, id=organisation.id)


    @method_decorator(decorators, name='dispatch')
    class DeleteRemoteDcatLinked(View):

        def post(self, request, id, *args, **kwargs):
            organisation = get_object_or_404(Organisation, id=id)
            instance = get_object_or_404(RemoteDcat, organisation=organisation)

            user = request.user
            profile = user.profile

            is_admin = profile.is_admin
            is_referent = LiaisonsReferents.objects.filter(
                profile=profile, organisation__id=id,
                validated_on__isnull=False) and True or False

            if not (is_referent or is_admin):
                raise Http404()

            try:
                with transaction.atomic():
                    instance.delete()
            except ValidationError as e:
                messages.error(request, e.__str__())
            except (DcatError, DcatTimeoutError) as e:
                messages.error(request, e.__str__())
            else:
                messages.success(request, (
                    'Les informations ainsi que les jeux de données et '
                    'ressources synchronisés avec le catalogue distant '
                    'ont été supprimés avec succès.'))

            return redirect('idgo_admin:update_organisation', id=organisation.id)
