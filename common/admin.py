from django.contrib import admin
from django.apps import apps
from import_export.admin import ImportExportModelAdmin

models = apps.get_models()
# print("models", models)
remove_fields = ["created_at", "updated_at", "delete_at", "is_deleted", "is_active"]
skip_models = ["<class 'common.models.post_report.ReportReasons'>", "<class 'event.models.event_rule.EventRules'>", "<class 'users.models.verification.IdentityVerification'>"]
for model in models:
    try:
        model_name = f"Custom{model}Admin"
        all_fields = model._meta.fields
        model_field_names = [f.name for f in all_fields]
        if str(model) in skip_models:
            continue
        if str(model) == "<class 'users.models.User'>":
            model_field_names.remove("password")

        for field in remove_fields:
            model_field_names.remove(field)
        try:
            model_field_names.remove("description")
        except:
            pass


        class model_name(ImportExportModelAdmin, admin.ModelAdmin):
            list_display = model_field_names
            try:
                readonly_fields = ['id']
            except:
                pass


        admin.site.register(model, model_name)
    except:
        pass

admin.site.site_header = "Get Buckets"
admin.site.site_title = " GBS"
admin.site.index_title = "GBS Admin"

