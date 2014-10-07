# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reduction_viewer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='severity',
            field=models.CharField(default=b'i', max_length=1, choices=[(b'i', b'info'), (b'w', b'warning'), (b'e', b'error')]),
        ),
    ]
