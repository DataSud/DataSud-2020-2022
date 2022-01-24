# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-03-11 15:53
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaskTracking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(unique=True, verbose_name='UUID')),
                ('task', models.TextField(blank=True, null=True, verbose_name='Tâche')),
                ('detail', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Détail')),
                ('state', models.CharField(choices=[('running', 'Tâche en cours de traitement'), ('succesful', 'Tâche terminée avec succés'), ('failed', 'Échec de la tâche'), ('unknown', 'Tâche perdue')], default='running', max_length=10, verbose_name='État')),
                ('start', models.DateTimeField(auto_now_add=True, verbose_name='Début')),
                ('end', models.DateTimeField(blank=True, null=True, verbose_name='Fin')),
            ],
            options={
                'verbose_name': 'Suivi',
                'verbose_name_plural': 'Suivi des tâches',
            },
        ),
    ]
