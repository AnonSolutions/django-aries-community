# Generated by Django 2.2.12 on 2020-08-07 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aries_community', '0006_agentmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentmessage',
            name='guid',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name='agentmessage',
            name='message_id',
            field=models.CharField(max_length=35, primary_key=True, serialize=False),
        ),
    ]
