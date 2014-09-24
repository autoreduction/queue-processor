# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('reduction_variables', '0002_runvariable'),
    ]

    operations = [
        migrations.AddField(
            model_name='scriptfile',
            name='created',
            field=models.DateTimeField(datetime.date(2014, 9, 16), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='runvariable',
            name='reduction_run',
            field=models.ForeignKey(related_name=b'run_variables', to='reduction_viewer.ReductionRun'),
        ),
    ]
