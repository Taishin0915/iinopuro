
import csv
import io
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Carrier, Report, ReportImage, DepartureRecord

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['carrier_name']
    search_fields = ['carrier_name']
    ordering = ['carrier_name']
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv, name='core_carrier_import_csv'),
        ]
        return my_urls + urls
    
    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'ファイル形式はCSVである必要があります。')
                return redirect("..")
            
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # ヘッダー行をスキップ
            
            for column in csv.reader(io_string, delimiter=',', quotechar="|"):
                _, created = Carrier.objects.update_or_create(
                    carrier_name=column[0]
                )
            
            messages.success(request, 'CSVファイルが正常にインポートされました。')
            return redirect("..")
        
        form = """
        <form action="." method="post" enctype="multipart/form-data">
            <input type="hidden" name="csrfmiddlewaretoken" value="{}">
            <input type="file" name="csv_file" accept=".csv">
            <button type="submit">CSVをインポート</button>
        </form>
        """.format(request.META.get('CSRF_COOKIE'))
        
        return HttpResponse(form)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'carrier', 'report_type', 'work_date', 'close_number', 'swing_number']
    list_filter = ['report_type', 'carrier', 'work_date']
    search_fields = ['user__username', 'carrier__carrier_name']
    date_hierarchy = 'work_date'

@admin.register(ReportImage)
class ReportImageAdmin(admin.ModelAdmin):
    list_display = ['report', 'created_at']
    list_filter = ['created_at']

@admin.register(DepartureRecord)
class DepartureRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'departure_date', 'departure_time']
    list_filter = ['departure_date']
    search_fields = ['user__username']