# Generated by Django 2.2.15 on 2020-08-03 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aries_community', '0004_auto_20200707_0052'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentconversation',
            name='cred_rev_id',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='agentconversation',
            name='rev_reg_id',
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
