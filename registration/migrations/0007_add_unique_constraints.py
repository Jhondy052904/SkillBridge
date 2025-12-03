# Generated migration to add unique constraints for duplicate prevention
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0006_alter_resident_verification_status_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='resident',
            constraint=models.UniqueConstraint(fields=['email'], name='unique_resident_email'),
        ),
    ]