# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-27 19:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0013_auto_20180327_1237'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='node',
            name='admins',
        ),
        migrations.AlterField(
            model_name='node',
            name='catalog_url',
            field=models.URLField(),
        ),
    ]
