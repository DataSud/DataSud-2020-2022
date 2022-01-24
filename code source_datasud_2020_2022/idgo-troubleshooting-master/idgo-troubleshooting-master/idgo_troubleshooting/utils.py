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


from datetime import datetime
from datetime import timedelta
from dateutil import parser
from functools import reduce
import logging
from urllib.parse import urljoin
from uuid import UUID

from django.apps import apps
from django.conf import settings
from django.db import transaction
import requests

from idgo_admin import CKAN_URL
from idgo_admin.ckan_module import CkanHandler
from idgo_admin.models import Dataset
from idgo_admin.models import Resource
from idgo_troubleshooting.models import DeadLinkResource
from idgo_troubleshooting.models import OrphanCkanObject
from idgo_troubleshooting.models import OutdatedResource
from idgo_troubleshooting.models import UndocumentedPackage


BETA = False
if apps.is_installed('idgo_resource'):
    from idgo_resource.models import Resource as ResourceBeta
    BETA = True


logger = logging.getLogger(__name__)


CKAN_PACKAGE_URL = "{}/dataset/".format(settings.CKAN_URL)
CKAN_PACKAGES_LIST_PATH = "{}/api/3/action/package_list/".format(
    settings.CKAN_URL)
CKAN_PACKAGE_PATH = "{}/api/3/action/package_show".format(settings.CKAN_URL)


def log_ckan_package(organization_name, package_name, package_json):
    logger.info('organisation : %s', organization_name),
    logger.info('dataset : %s', package_name),
    logger.info('voir le catalogue : %s', package_json),
    logger.info('dernier contrôle : %s', datetime.now())


def parse_package(package):

    package_json = package_json = requests.get(
        CKAN_PACKAGE_PATH,
        params={'id': package}
    )
    resources = package_json.json()
    results = resources['result']
    return package_json, resources, results


def report_outdated_resource(
    resource,
    creation_date,
    frequency,
    curr_date,
    package_json,
    resource_name,
    resource_ckanurl,
    package_name,
    organization_name
):
    last_update = parser.parse(
        resource['last_modified'])

    if (creation_date != 'none') and (last_update != 'none'):
        (planned_update, declared_frequency) = which_planned_update(
            last_update, frequency)

        if planned_update and (last_update != 'none') and (
                planned_update < curr_date):
            delay = curr_date - planned_update
            delay = delay.days

            jour = ' jour' if delay == 1 else ' jours'

            if delay and (planned_update < curr_date):

                log_ckan_package(organization_name, package_name, package_json)

                logger.info('ressource : %s', resource_name),
                logger.info('dernière mise à jour : %s', last_update),
                logger.info('c\'était prévu pour le : %s', planned_update),
                logger.info('fréquence déclarée : %s', declared_frequency),
                logger.info('retard : %s%s', delay, jour),

                o = OutdatedResource.objects.create(
                    resource_name=resource_name,
                    resource_ckanurl=resource_ckanurl,
                    package_name=package_name,
                    organization=organization_name,
                    lastupdate=last_update,
                    resource_frequency=declared_frequency,
                    delay=delay,
                    last_log=datetime.now(),
                )
                o.save()


def report_deadlink_resource(
    resource,
    results,
    organization_name,
    package_json,
    package_name,
    resource_name,
    resource_url,
    resource_ckanurl
):
    external_url = resource['url']
    organization_name = results['organization']['title']
    package_name = results['title']
    resource_name = resource['name']

    r = requests.get(external_url)
    if r.status_code == 200:
        log_ckan_package(organization_name, package_name, package_json),
        logger.info('ressource : %s', resource_name),
        logger.info('lien référencé dans la ressource : %s', external_url),
        logger.info('url OK')
    else:
        logger.debug('organisation : %s', organization_name),
        logger.debug('dataset : %s', package_name),
        logger.debug('ressource : %s', resource_name),
        logger.debug('voir le catalogue : %s', resource_url),
        logger.debug('lien référencé dans la ressource : %s', external_url),
        logger.debug('dernier contrôle : %s', datetime.now()),
        logger.debug('url NOT OK')

        d = DeadLinkResource.objects.create(
            resource_name=resource_name,
            package_name=package_name,
            resource_ckanurl=resource_ckanurl,
            external_link=external_url,
            organization=organization_name,
            last_log=datetime.now(),
        )
        d.save()


def analyze_and_report_resource(results, package, package_json, case):

    curr_date = datetime.now()

    for resource in results['resources']:

        organization_name = results['organization']['title']
        package_name = results['title']
        resource_name = resource['name']
        resource_id = resource['id']
        resource_url = requests.get(
            CKAN_PACKAGE_PATH,
            params={'resource_id': resource_id}
        )
        resource_ckanurl = "{}{}/resource/{}".format(
            CKAN_PACKAGE_URL,
            package,
            resource_id
        )
        frequency = results['frequency']
        creation_date = resource['created']

        if case == 'outdated_resource' and resource['last_modified']:

            report_outdated_resource(
                resource,
                creation_date,
                frequency,
                curr_date,
                package_json,
                resource_name,
                resource_ckanurl,
                package_name,
                organization_name
            )

        if case == 'deadlink_resource' and resource['url']:

            report_deadlink_resource(
                resource,
                results,
                organization_name,
                package_json,
                package_name,
                resource_name,
                resource_url,
                resource_ckanurl
            )


def which_planned_update(last_update, frequency):

    if frequency == 'annual':
        return last_update + timedelta(days=366), 'annuelle'
    elif frequency in ['daily', 'continuously', 'realtime']:
        return last_update + timedelta(days=1), 'journalière'
    elif frequency == 'fortnightly':
        return last_update + timedelta(days=14), 'bimensuelle'
    elif frequency == 'monthly':
        return last_update + timedelta(days=31), 'mensuelle'
    elif frequency == 'quaterly':
        return last_update + timedelta(days=92), 'trimestrielle'
    elif frequency == 'semiannual':
        return last_update + timedelta(days=183), 'semestrielle'
    elif frequency == 'weekly':
        return last_update + timedelta(days=7), 'hebdomadaire'
    else:
        return None, 'none'
    # Cases not covered: 'asneeded', 'intermittently', 'never', 'unknown'


def get_outdated_resource():
    '''
    Outdated resources
    '''

    OutdatedResource.objects.all().delete()

    packages = requests.get(CKAN_PACKAGES_LIST_PATH).json()

    for package in packages['result']:

        (package_json, resources, results) = parse_package(package)
        analyze_and_report_resource(
            results, package, package_json, 'outdated_resource')


def get_undocumented_resource():
    '''
    Packages with no resource
    '''

    UndocumentedPackage.objects.all().delete()

    packages = requests.get(CKAN_PACKAGES_LIST_PATH).json()

    for package in packages['result']:

        (package_json, resources, results) = parse_package(package)
        package_ckanurl = "{}{}".format(CKAN_PACKAGE_URL, package)

        if 'organization' in results and not results['resources']:

            organization_name = results['organization']['title']
            package_name = results['title']

            log_ckan_package(organization_name, package_name, package_json)

            u = UndocumentedPackage.objects.create(
                package_name=package_name,
                package_ckanurl=package_ckanurl,
                organization=organization_name,
                last_log=datetime.now(),
            )
            u.save()


def get_deadlink_resource():
    '''
    Resources with invalid link
    '''

    DeadLinkResource.objects.all().delete()

    packages = requests.get(CKAN_PACKAGES_LIST_PATH).json()

    for package in packages['result']:

        (package_json, resources, results) = parse_package(package)
        analyze_and_report_resource(
            results, package, package_json, 'deadlink_resource')


@transaction.atomic
def get_orphan_ckan_objects():
    """Look for CKAN objects which do not exist in IDGO."""

    OrphanCkanObject.objects.all().delete()  # Clear area

    count_res = 0
    count_pkg = 0
    offset = 0
    limit = 25
    while True:  # Paginate `package_list`

        # Iterate over packages
        package_list = CkanHandler.call_action(
            'package_list', limit=limit, offset=offset)
        for package_name in package_list:
            package = CkanHandler.call_action('package_show', id=package_name)
            if package['type'] == 'showcase':
                continue
            pkg_obj_id = UUID(package['id'])
            pkg_obj_location = reduce(urljoin, [
                CKAN_URL, 'dataset/', package_name + '/'])
            logger.debug("Package: %s - %s" % (pkg_obj_id, pkg_obj_location))

            if not Dataset.objects.filter(ckan_id=pkg_obj_id).exists():
                OrphanCkanObject.packages.create(
                    object_id=pkg_obj_id,
                    object_location=pkg_obj_location,
                )
                count_pkg += 1

            # Iterate over package resources
            resource_list = package.get('resources')
            logger.debug("%d resources" % len(resource_list))
            for resource in resource_list:
                res_obj_id = UUID(resource['id'])
                res_obj_location = reduce(urljoin, [
                    pkg_obj_location, 'resource/', str(res_obj_id) + '/'])
                logger.debug("Resource: %s - %s" % (res_obj_id, res_obj_location))

                if not Resource.objects.filter(ckan_id=res_obj_id).exists():
                    if BETA and ResourceBeta.objects.filter(ckan_id=res_obj_id).exists():
                        continue
                    OrphanCkanObject.resources.create(
                        object_id=res_obj_id,
                        object_location=res_obj_location,
                    )
                    count_res += 1

        if len(package_list) < limit:
            break
        offset += limit

    logger.info("%d OrphanCkanObject type resource was found." % count_res)
    logger.info("%d OrphanCkanObject type package was found." % count_pkg)


def call_ckan_action(action, id, attempt=1, max_retry=2):
    import time
    from ckanapi.errors import CKANAPIError

    try:
        return CkanHandler.call_action(action, id=id, force=True)
    except CKANAPIError as e:
        if attempt > max_retry:
            raise e
        logger.error(e)
        logger.warning("Sleep 10s then retry [%d/%d]" % (attempt, max_retry))
        time.sleep(1)
        attempt += 1
        return call_ckan_action(action, id, attempt=attempt)


def clear_orphan_ckan_resource_objects():
    """Clear all CKAN resource objects which do not exist in IDGO."""
    count = 0
    for instance in OrphanCkanObject.resources.all():
        try:
            call_ckan_action('resource_delete', id=str(instance.object_id))
        except Exception as e:
            logger.exception(e)
            continue
        instance.delete()
        count += 1

    logger.info("%d OrphanCkanObject type resource was deleted." % count)


def clear_orphan_ckan_dataset_objects():
    """Clear all CKAN package objects which do not exist in IDGO."""
    count = 0
    for instance in OrphanCkanObject.packages.all():
        call_ckan_action(action='package_delete', id=str(instance.object_id))
        instance.delete()
        count += 1

    logger.info("%d OrphanCkanObject type package was deleted." % count)
