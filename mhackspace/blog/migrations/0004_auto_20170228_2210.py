# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-28 22:10
from __future__ import unicode_literals

from django.db import migrations
import draceditor.models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_auto_20170215_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='description',
            field=draceditor.models.DraceditorField(),
        ),
    ]