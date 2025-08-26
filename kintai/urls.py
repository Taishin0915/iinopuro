from django.urls import path
from . import views


urlpatterns = [
    path('',views.kintai_views, name = 'kintai_top')
]