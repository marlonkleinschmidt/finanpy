from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'description',
        'transaction_type',
        'amount',
        'account',
        'category',
    )
    list_filter = ('transaction_type', 'account', 'category')
    date_hierarchy = 'date'
