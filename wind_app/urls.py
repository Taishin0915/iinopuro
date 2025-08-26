# myapp/urls.py (新規作成)

# wind_app/urls.py
from django.urls import path
from . import views # ← viewsを正しくインポートしているか

urlpatterns = [
    path('', views.index, name='job_wind'), # ← pathの第一引数は空文字''
]