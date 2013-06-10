from cronrunner import models
from django.contrib import admin

admin.site.register(models.ScheduledTask)
admin.site.register(models.ScheduledImport)