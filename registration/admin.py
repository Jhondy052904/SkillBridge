from django.contrib import admin
from .models import Event, Job, Training, Official, UserAccount

# Register your models here
admin.site.register(Event)
admin.site.register(Job)
admin.site.register(Training)
admin.site.register(Official)
admin.site.register(UserAccount)
