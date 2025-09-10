# kintai/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

class Timestamp(models.Model):
    # 記録の種類を定義（出勤、退勤、休憩開始、休憩終了）
    STATUS_CHOICES = [
        ('CLOCK_IN', '出勤'),
        ('CLOCK_OUT', '退勤'),
        ('BREAK_START', '休憩開始'),
        ('BREAK_END', '休憩終了'),
    ]

    # どのユーザーの記録か（Userモデルと関連付け）
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # 記録の種類（出勤、退勤など）
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # 打刻された日時（デフォルトで現在時刻を記録）
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        # 管理画面などで分かりやすく表示するための設定
        return f"{self.user.username} - {self.get_status_display()} at {self.timestamp}"