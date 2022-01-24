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


from django.db import models


LINK_TITLE = "Lien CKAN"
LOG_TITLE = "Date du contrôle"


class OutdatedResource(models.Model):
    """
    Outdated resource
    """
    resource_name = models.CharField("Ressource", max_length=200, unique=False)
    resource_ckanurl = models.URLField(LINK_TITLE, max_length=200, default="")
    package_name = models.CharField("Dataset", max_length=200, unique=False)
    organization = models.CharField(
        "Organisation", max_length=200, unique=False)
    lastupdate = models.DateTimeField("Dernière mise à jour")
    resource_frequency = models.CharField(
        "Fréquence déclarée",
        max_length=100,
        unique=False,
        null=True,
        blank=True
    )
    delay = models.IntegerField("Retard (en jours)")
    last_log = models.DateTimeField(LOG_TITLE)

    class Meta:
        verbose_name = "Ressource dont la date de MAJ est dépassée"
        verbose_name_plural = "Ressources dont la date de MAJ est dépassée"


class UndocumentedPackage(models.Model):
    """
    Package with no resource
    """
    package_name = models.CharField("Dataset", max_length=200, unique=False)
    package_ckanurl = models.URLField(LINK_TITLE, max_length=200, default="")
    organization = models.CharField(
        "Organisation", max_length=200, unique=False)
    last_log = models.DateTimeField(LOG_TITLE)

    class Meta:
        verbose_name = "Sans ressource"
        verbose_name_plural = verbose_name


class DeadLinkResource(models.Model):
    """
    Resource with invalid link
    """
    resource_name = models.CharField("Ressource", max_length=200, unique=False)
    resource_ckanurl = models.URLField(LINK_TITLE, max_length=200, default="")
    external_link = models.CharField("URL erronée", max_length=200, default="")
    package_name = models.CharField("Dataset", max_length=200, unique=False)
    organization = models.CharField(
        "Organisation", max_length=200, unique=False)
    last_log = models.DateTimeField(LOG_TITLE)

    class Meta:
        verbose_name = "Liens non valides"
        verbose_name_plural = verbose_name


# ORPHAN CKAN OBJECT MODEL:


CKAN_OBJECT_PKG_ID = 'dataset'
CKAN_OBJECT_RES_ID = 'resource'
ORPHAN_CKAN_OBJECT_CHOICES = (
    (CKAN_OBJECT_PKG_ID, "Jeu de données"),
    (CKAN_OBJECT_RES_ID, "Ressource"),
)


class OrphanCkanObjectQuerySet(models.QuerySet):

    def packages(self):
        return self.filter(object_name=CKAN_OBJECT_PKG_ID)

    def resources(self):
        return self.filter(object_name=CKAN_OBJECT_RES_ID)


class OrphanCkanObjectManager(models.Manager):
    OBJECT_NAME = None

    def get_queryset(self):
        return OrphanCkanObjectQuerySet(self.model, using=self._db)

    def packages(self):
        return self.get_queryset().registered_users()

    def resources(self):
        return self.get_queryset().editors()

    def create(self, **kwargs):
        if self.OBJECT_NAME:
            kwargs.update({'object_name': self.OBJECT_NAME})
        return super().create(**kwargs)


class OrphanCkanPackageObjectManager(OrphanCkanObjectManager):
    OBJECT_NAME = CKAN_OBJECT_PKG_ID

    def get_queryset(self):
        return OrphanCkanObjectQuerySet(self.model, using=self._db).packages()


class OrphanCkanResourceObjectManager(OrphanCkanObjectManager):
    OBJECT_NAME = CKAN_OBJECT_RES_ID

    def get_queryset(self):
        return OrphanCkanObjectQuerySet(self.model, using=self._db).resources()


class OrphanCkanObject(models.Model):
    """CKAN Object without IDGO object."""

    class Meta(object):
        abstract = False
        db_table = 'idgo_troubleshooting_orphanckanobject'
        verbose_name = "Objet CKAN orphelin"
        verbose_name_plural = "Objets CKAN orphelins"

    objects = OrphanCkanObjectManager()
    packages = OrphanCkanPackageObjectManager()
    resources = OrphanCkanResourceObjectManager()

    object_name = models.CharField(
        verbose_name="Objet",
        db_column='mimetype',
        max_length=200,
        choices=ORPHAN_CKAN_OBJECT_CHOICES,
        null=False,
    )

    object_id = models.UUIDField(
        verbose_name="Identifiant de l'object",
        unique=True,
        null=False,
    )

    object_location = models.URLField(
        verbose_name="URL de l'objet",
        max_length=2000,
        null=False,
    )

    def __str__(self):
        return self.object_location
