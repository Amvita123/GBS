from django.contrib import admin
from .models import EventRules, Team
from import_export.admin import ImportExportModelAdmin


class EventRuleAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', "text"]


admin.site.register(EventRules, EventRuleAdmin)
admin.site.register(Team)




