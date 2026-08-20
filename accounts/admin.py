from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'city', 'island', 'created_at')
    list_filter = ('island', 'created_at')
    search_fields = ('user__username', 'user__email', 'company')
    readonly_fields = ('created_at', 'updated_at')
admin.site.site_header = "Ahlikicorp Admin"
admin.site.site_title = "Ahlikicorp Admin Portal"
admin.site.index_title = "Welcome to Ahlikicorp Admin Portal"