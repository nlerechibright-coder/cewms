from django.contrib import admin
from .models import Complaint, ComplaintAttachment, WorkAssignment, StatusHistory

class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ('status_value', 'changed_by', 'changed_at', 'remarks')
    can_delete = False
    can_add = False

    def has_add_permission(self, request, obj=None):
        return False

class WorkAssignmentInline(admin.TabularInline):
    model = WorkAssignment
    extra = 1
    readonly_fields = ('assigned_at',)

    # This is the fix: Tell the form 'assigned_by' is not required
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if 'assigned_by' in formset.form.base_fields:
            formset.form.base_fields['assigned_by'].required = False
        return formset

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'complaint_title', 'category', 'location', 'status', 'created_at')
    list_filter = ('status', 'category', 'operational_priority')
    search_fields = ('reference_number', 'complaint_title', 'complaint_details', 'full_name')
    readonly_fields = ('reference_number', 'tracking_token_hash', 'created_at', 'updated_at')
    
    inlines = [StatusHistoryInline, WorkAssignmentInline]

    actions = ['mark_as_accepted', 'mark_as_rejected']

    def mark_as_accepted(self, request, queryset):
        updated_count = 0
        for complaint in queryset:
            if complaint.status != 'ACCEPTED':
                old_status = complaint.status
                complaint.status = 'ACCEPTED'
                complaint.save()
                StatusHistory.objects.create(
                    complaint=complaint,
                    status_value='ACCEPTED',
                    changed_by=request.user,
                    remarks=f"Bulk updated from {old_status} via admin action."
                )
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} complaints to ACCEPTED.")
    mark_as_accepted.short_description = "Mark selected complaints as Accepted"

    def mark_as_rejected(self, request, queryset):
        updated_count = 0
        for complaint in queryset:
            if complaint.status != 'REJECTED':
                old_status = complaint.status
                complaint.status = 'REJECTED'
                complaint.save()
                StatusHistory.objects.create(
                    complaint=complaint,
                    status_value='REJECTED',
                    changed_by=request.user,
                    remarks=f"Bulk updated from {old_status} via admin action."
                )
                updated_count += 1
        self.message_user(request, f"Successfully updated {updated_count} complaints to REJECTED.")
    mark_as_rejected.short_description = "Mark selected complaints as Rejected"

    def save_model(self, request, obj, form, change):
        is_status_change = False
        old_status = None
        
        if change:
            old_obj = Complaint.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                is_status_change = True
                old_status = old_obj.status

        super().save_model(request, obj, form, change)

        if is_status_change:
            StatusHistory.objects.create(
                complaint=obj,
                status_value=obj.status,
                changed_by=request.user,
                remarks=f"Changed from {old_status} in admin panel."
            )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, WorkAssignment) and not obj.assigned_by_id:
                obj.assigned_by = request.user
            obj.save()
        formset.save_m2m()


@admin.register(ComplaintAttachment)
class ComplaintAttachmentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'complaint', 'officer', 'assigned_by', 'status', 'assigned_at')
    list_filter = ('status', 'assigned_at')
    search_fields = ('complaint__reference_number', 'officer__username', 'notes')
    readonly_fields = ('assigned_at', 'assigned_by')

    def save_model(self, request, obj, form, change):
        if not obj.assigned_by_id:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'status_value', 'changed_by', 'changed_at')
    list_filter = ('status_value', 'changed_at')
    search_fields = ('complaint__reference_number', 'remarks')
    readonly_fields = ('changed_at',)