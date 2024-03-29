# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-08-25 12:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idgo_admin', '0003_auto_20200320_1033'),
    ]

    operations = [
        migrations.AddField(
            model_name='asyncextractortask',
            name='app_label',
            field=models.CharField(blank=True, default='idgo_admin', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='sync_frequency',
            field=models.CharField(blank=True, choices=[('1hour', 'Toutes les heures'), ('3hours', 'Toutes les trois heures'), ('6hours', 'Toutes les six heures'), ('daily', 'Quotidienne (tous les jours à minuit)'), ('weekly', 'Hebdomadaire (tous les lundi)'), ('bimonthly', 'Bimensuelle (1er et 15 de chaque mois)'), ('monthly', 'Mensuelle (1er de chaque mois)'), ('quarterly', 'Trimestrielle (1er des mois de janvier, avril, juillet, octobre)'), ('biannual', 'Semestrielle (1er janvier et 1er juillet)'), ('annual', 'Annuelle (1er janvier)'), ('never', 'Jamais')], default='never', max_length=20, null=True, verbose_name='Fréquence de synchronisation'),
        ),
    ]
