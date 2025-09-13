
from django.contrib import admin
from .models import Carrier, Report, ReportImage 

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['carrier_name']
    search_fields = ['carrier_name']
    ordering = ['carrier_name']

admin.site.register(Report)
admin.site.register(ReportImage)