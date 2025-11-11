from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_patient_doctorprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
