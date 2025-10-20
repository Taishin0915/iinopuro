# models.py の改善案

from django.db import models
from django.conf import settings # Userモデルを扱うための推奨設定
from django import forms


class Carrier(models.Model):
    carrier_name = models.CharField(max_length=100)

    def __str__(self):
        return self.carrier_name

# CloseNumberDispatch と ReportWind を一つの Report モデルに統合
class Report(models.Model):
    # レポートの種類を区別するためのフィールド
    REPORT_TYPE_CHOICES = [
        ('DISPATCH', 'Dispatch Report'),
        ('WIND', 'Wind Report'),
    ]
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, default='WIND')
    
    # ユーザーは文字列ではなく、Userモデルに関連付ける
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    work_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    clock_out_time = models.DateTimeField(null=True, blank=True)
    
    # 両方のレポートで共通のフィールド
    close_number = models.IntegerField()
    swing_number = models.IntegerField()
    
    # ReportWind にしか存在しないフィールド（null=Trueで空でもOKにする）
    new_close_number = models.IntegerField(null=True, blank=True)
    upg_close_number = models.IntegerField(null=True, blank=True)
    mnp_close_number = models.IntegerField(null=True, blank=True)
    tv_close_number = models.IntegerField(null=True, blank=True)
    net_close_number = models.IntegerField(null=True, blank=True)
    tel_close_number = models.IntegerField(null=True, blank=True)
    tos_close_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.work_date} - {self.get_report_type_display()} by {self.user.username}"


# ReportImgDispatch と ReportImgWind を一つの ReportImage モデルに統合
class ReportImage(models.Model):
    # どのレポートに属する画像かを ForeignKey で紐付ける
    report = models.ForeignKey(Report, related_name='images', on_delete=models.CASCADE)
    upload_img = models.ImageField(upload_to='report_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Report ID: {self.report.id}"


# 出発記録モデル
class DepartureRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departure_date = models.DateField()
    departure_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'departure_date']  # 1日に1回のみ
    
    def __str__(self):
        return f"{self.user.username} - {self.departure_date}"


# ... (既存のReportImageFormはそのまま) ...
