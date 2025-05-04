from django.contrib import admin
from django.utils.html import format_html

from .models import (
    QLearningState, 
    QLearningAction, 
    QTableEntry,
    SupplierRanking, 
    SupplierPerformanceCache,
    RankingConfiguration,
    RankingEvent
)


@admin.register(QLearningState)
class QLearningStateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(QLearningAction)
class QLearningActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(QTableEntry)
class QTableEntryAdmin(admin.ModelAdmin):
    list_display = ('state', 'action', 'q_value', 'update_count', 'last_updated')
    list_filter = ('state', 'action')
    search_fields = ('state__name', 'action__name')
    readonly_fields = ('last_updated',)


@admin.register(SupplierRanking)
class SupplierRankingAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'supplier_id', 'date', 'rank', 'overall_score', 
                   'quality_score', 'delivery_score', 'price_score', 'service_score')
    list_filter = ('date', 'rank')
    search_fields = ('supplier_name', 'supplier_id')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('state')
        return queryset


@admin.register(SupplierPerformanceCache)
class SupplierPerformanceCacheAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'supplier_id', 'date', 'quality_score', 
                   'on_time_delivery_rate', 'price_competitiveness', 'last_updated')
    list_filter = ('date', 'data_complete')
    search_fields = ('supplier_name', 'supplier_id')
    date_hierarchy = 'date'
    readonly_fields = ('last_updated',)
    fieldsets = (
        ('Supplier Information', {
            'fields': ('supplier_id', 'supplier_name', 'date')
        }),
        ('Quality Metrics', {
            'fields': ('quality_score', 'defect_rate', 'return_rate')
        }),
        ('Delivery Metrics', {
            'fields': ('on_time_delivery_rate', 'average_delay_days')
        }),
        ('Price Metrics', {
            'fields': ('price_competitiveness',)
        }),
        ('Service Metrics', {
            'fields': ('responsiveness', 'issue_resolution_time')
        }),
        ('Fulfillment Metrics', {
            'fields': ('fill_rate', 'order_accuracy')
        }),
        ('Additional Metrics', {
            'fields': ('compliance_score', 'demand_forecast_accuracy', 'logistics_efficiency')
        }),
        ('Metadata', {
            'fields': ('last_updated', 'data_complete'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RankingConfiguration)
class RankingConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'learning_rate', 'discount_factor', 'exploration_rate', 
                   'quality_weight', 'delivery_weight', 'price_weight', 'service_weight')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('General', {
            'fields': ('name', 'is_active')
        }),
        ('Learning Parameters', {
            'fields': ('learning_rate', 'discount_factor', 'exploration_rate')
        }),
        ('Weight Configuration', {
            'fields': ('quality_weight', 'delivery_weight', 'price_weight', 'service_weight')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RankingEvent)
class RankingEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'timestamp', 'supplier_id', 'state_id', 'action_id')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('description', 'supplier_id')
    readonly_fields = ('timestamp',)
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'description', 'timestamp')
        }),
        ('Related Objects', {
            'fields': ('supplier_id', 'state_id', 'action_id', 'reward')
        }),
        ('Additional Data', {
            'fields': ('metadata',)
        }),
    )