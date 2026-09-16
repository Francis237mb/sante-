from django.contrib import admin
from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = [
        'reference_short', 'patient', 'medecin', 'montant_paye',
        'payment_type', 'status', 'phone_number', 'campay_operator',
        'created_at'
    ]
    list_filter = ['status', 'payment_type', 'campay_operator', 'created_at']
    search_fields = [
        'patient__username', 'patient__email',
        'medecin__username',
        'phone_number', 'campay_reference'
    ]
    readonly_fields = [
        'reference', 'campay_reference', 'campay_raw_response',
        'created_at', 'updated_at', 'paid_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = [
        ('Identification', {
            'fields': ['reference', 'campay_reference', 'campay_operator']
        }),
        ('Acteurs', {
            'fields': ['patient', 'medecin', 'rdv']
        }),
        ('Montants', {
            'fields': ['montant_total_consultation', 'montant_paye', 'pourcentage_acompte']
        }),
        ('Statut & Type', {
            'fields': ['payment_type', 'status', 'phone_number']
        }),
        ('Horodatage', {
            'fields': ['created_at', 'updated_at', 'paid_at'],
            'classes': ['collapse']
        }),
        ('Données brutes CamPay', {
            'fields': ['campay_raw_response'],
            'classes': ['collapse']
        }),
    ]

    def reference_short(self, obj):
        return str(obj.reference).upper()[:12] + '...'
    reference_short.short_description = 'Référence'
