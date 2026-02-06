from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin


class PlayingStyleAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', "title", "position", "archetype_rating"]
    ordering = ("position", "archetype_rating")
    list_filter = ["position"]


admin.site.register(PlayingStyle, PlayingStyleAdmin)


class BadgeLeveAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', "name", "badge", "icon", ]
    list_filter = ['name', "badge"]


class BadgeCheckListAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', "name", "weight", "rating", "auto_assignable"]


class positionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["id", "name", "rating"]
    ordering = ("name",)
    list_filter = ["rating"]


admin.site.register(Position, positionAdmin)
admin.site.register(BadgeLevel, BadgeLeveAdmin)
admin.site.register(BadgesCheckList, BadgeCheckListAdmin)
admin.site.register(Sport)


class BadgeLevelTemplateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_filter = ["badge_level"]
    list_display = ["id", 'title', "badge_level"]


admin.site.register(BadgeLevelTemplate, BadgeLevelTemplateAdmin)


class SquadStructureAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["id", "structure", "rating", "position_1"]


admin.site.register(SquadStructure, SquadStructureAdmin)


admin.site.register(SchoolGrade)

