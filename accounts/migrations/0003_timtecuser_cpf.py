# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20160224_0053'),
    ]

    operations = [
        migrations.AddField(
            model_name='timtecuser',
            name='cpf',
            field=models.CharField(max_length=11, unique=True, null=True, blank=True),
        ),
    ]
