from django.db import models

class Job(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    job_id = models.UUIDField(primary_key=True, default=None)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    posted_by = models.CharField(max_length=100)
    date_posted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Open")

    class Meta:
        app_label = 'jobs'

    def __str__(self):
        return self.title