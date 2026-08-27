from django.contrib import admin
from .models import DoctorProfile, Specialite

@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialite', 'speciality', 'verification_status')
    list_filter = ('verification_status', 'specialite')
    search_fields = ('user__username', 'speciality', 'license_number')
