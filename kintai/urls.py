from django.urls import path
from . import views


urlpatterns = [
    path('', views.kintai_view, name='kintai_top'), # ◀ 最後のsを削除
    path('checkin/', views.checkin_view, name='kintai_checkin'),
    path('complete/', views.checkin_complete_view, name='kintai_complete'),
    path('clockout/', views.kintai_clockout_view, name='kintai_checkout'),
    path('clockout/complete/', views.checkout_complete_view, name='kintai_checkout_complete'),
]