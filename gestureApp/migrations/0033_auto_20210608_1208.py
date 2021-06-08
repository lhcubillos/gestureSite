# Generated by Django 3.1.3 on 2021-06-08 16:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestureApp', '0032_study_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_groups', to=settings.AUTH_USER_MODEL)),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='gestureApp.study')),
            ],
        ),
        migrations.AddField(
            model_name='experiment',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiments', to='gestureApp.group'),
        ),
    ]
