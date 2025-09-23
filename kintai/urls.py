from django.urls import path
from . import views


urlpatterns = [
    path('', views.kintai_view, name='kintai_top'), # ◀ 最後のsを削除
    path('checkin/', views.checkin_view, name='kintai_checkin'),
    path('complete/', views.checkin_complete_view, name='kintai_complete'),
    path('clockout/', views.kintai_clockout_view, name='kintai_checkout'),
    path('clockout/complete/', views.checkout_complete_view, name='kintai_checkout_complete'),
    path('performance/', views.performance_view, name='kintai_performance'),
    path('team-performance/', views.team_performance_view, name='team_performance'),
    
    # 管理者画面のURL
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/users/<int:user_id>/performance/', views.admin_user_performance_view, name='admin_user_performance'),
    path('admin/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin/carriers/', views.admin_carriers_view, name='admin_carriers'),
    path('admin/carriers/<int:carrier_id>/', views.admin_carrier_detail_view, name='admin_carrier_detail'),
    path('admin/analytics/', views.admin_analytics_view, name='admin_analytics'),
    path('admin/attendance/', views.admin_attendance_management_view, name='admin_attendance_management'),
]