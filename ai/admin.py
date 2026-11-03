from django.contrib import admin

from .models import FinancialAnalysis


@admin.register(FinancialAnalysis)
class FinancialAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'period_start',
        'period_end',
        'generated_at',
        'error_code',
        'model_name',
        'total_tokens',
        'created_at',
    )
    list_filter = ('status', 'error_code', 'model_name')
    list_select_related = ('user',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
