# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-10-21 08:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0005_auto_20201021_0934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='sftp_password',
            field=models.CharField(blank=True, default='CHANGEME', max_length=10, null=True, verbose_name='Mot de passe sFTP'),
        ),
    ]