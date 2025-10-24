from django.db import models

class Skill(models.Model):
    skill_id = models.UUIDField(primary_key=True, default=None)
    skill_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.skill_name
