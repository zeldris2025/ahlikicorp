from django.contrib import admin, messages
from django.utils.html import format_html

from .models import CustomerApplication, UserProfile
from .services import approve_application, reject_application

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'city', 'island', 'created_at')
    list_filter = ('island', 'created_at')
    search_fields = ('user__username', 'user__email', 'company')
    readonly_fields = ('created_at', 'updated_at')
@admin.register(CustomerApplication)
class CustomerApplicationAdmin(admin.ModelAdmin):
    """Review trade account applications.

    Approving is an action rather than a status dropdown: it has to create the
    account, generate a password and send the email, none of which happens by
    simply editing a field.
    """

    list_display = ('full_name', 'organisation', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'organisation', 'email', 'phone')
    readonly_fields = ('created_at', 'reviewed_at', 'reviewed_by', 'user', 'document_link')
    actions = ('approve_selected', 'decline_selected')
    fieldsets = (
        ('Applicant', {'fields': ('full_name', 'organisation', 'email', 'phone')}),
        ('Verification', {'fields': ('document', 'document_link')}),
        ('Review', {
            'fields': ('status', 'review_notes', 'reviewed_at', 'reviewed_by', 'user', 'created_at'),
            'description': 'Use the Approve action on the list page — it creates the account and emails the credentials.',
        }),
    )

    @admin.display(description='Attached document')
    def document_link(self, obj):
        if not obj.document:
            return '—'
        return format_html('<a href="{}" target="_blank" rel="noopener">Open document</a>', obj.document.url)

    @admin.action(description='Approve: create the account and email the sign-in details')
    def approve_selected(self, request, queryset):
        created = skipped = 0
        for application in queryset:
            if application.user_id:
                skipped += 1
                continue
            approve_application(application, reviewer=request.user)
            created += 1

        if created:
            self.message_user(request, f'Approved {created} application(s); sign-in details emailed.', messages.SUCCESS)
        if skipped:
            self.message_user(request, f'{skipped} already had an account and were left alone.', messages.WARNING)

    @admin.action(description='Decline and notify the applicant')
    def decline_selected(self, request, queryset):
        declined = 0
        for application in queryset.exclude(status=CustomerApplication.Status.APPROVED):
            reject_application(application, reviewer=request.user)
            declined += 1
        self.message_user(request, f'Declined {declined} application(s).', messages.SUCCESS)


admin.site.site_header = "Ahlikicorp Admin"
admin.site.site_title = "Ahlikicorp Admin Portal"
admin.site.index_title = "Welcome to Ahlikicorp Admin Portal"