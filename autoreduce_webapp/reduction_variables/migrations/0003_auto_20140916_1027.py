# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils import timezone
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('reduction_variables', '0002_runvariable'),
    ]

    operations = [
        migrations.AddField(
            model_name='scriptfile',
            name='created',
            field=models.DateTimeField(default=timezone.make_aware(datetime.date(2014, 9, 16), timezone.get_current_timezone()), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='runvariable',
            name='reduction_run',
            field=models.ForeignKey(related_name=b'run_variables', to='reduction_viewer.ReductionRun'),
        ),
    ]
