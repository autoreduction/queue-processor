# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def insert_status(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Status = apps.get_model("reduction_viewer", "Status")
    db_alias = schema_editor.connection.alias
    Status.objects.using(db_alias).bulk_create([
        Status(pk=1, value="Queued"),
        Status(pk=2, value="Processing"),
        Status(pk=3, value="Completed"),
        Status(pk=4, value="Error"),
        Status(pk=5, value="AwaitingData"),
    ])

class Migration(migrations.Migration):

    dependencies = [
        ('reduction_viewer', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            insert_status,
        ),
    ]
