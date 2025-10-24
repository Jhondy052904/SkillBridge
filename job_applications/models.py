from django.db import models

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    application_id = models.UUIDField(primary_key=True, default=None)
    resident_id = models.CharField(max_length=100)
    job_id = models.CharField(max_length=100)
    date_applied = models.DateTimeField(auto_now_add=True)
    application_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        app_label = 'job_applications'

    def __str__(self):
        return f"Application {self.application_id}"