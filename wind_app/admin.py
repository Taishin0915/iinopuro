# wind_app/admin.py
from django.contrib import admin
from .models import Carrier, Report, ReportImage 

admin.site.register(Carrier)
admin.site.register(Report)
admin.site.register(ReportImage)