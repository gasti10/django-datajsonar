# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-29 13:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_field_description'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Query',
        ),
    ]
