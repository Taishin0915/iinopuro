# kintai/views.py

from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
# 🔽 Report, ReportImage, Carrier モデルをインポート
from core.models import Report, ReportImage, Carrier
# 🔽 作成したフォームをインポート
from .forms import ReportImageForm

def get_user_attendance_status(user):
    """
    ユーザーの現在の出勤状態を取得する
    Returns:
        'CLOCKED_IN': 出勤中
        'CLOCKED_OUT': 退勤中
        'NO_RECORD': 記録なし
    """
    # 今日の日付
    today = date.today()
    
    # 今日のレポートを取得
    today_reports = Report.objects.filter(
        user=user,
        work_date=today
    ).order_by('-created_at')
    
    if not today_reports.exists():
        return 'NO_RECORD'
    
    # 最新のレポートを取得
    latest_report = today_reports.first()
    
    # レポートが作成された時刻を出勤時刻として扱う
    return 'CLOCKED_IN'
# 外部サービス呼び出しのライブラリは起動時のimportを避けるため関数内で遅延importする





@login_required
def kintai_view(request):
    """
    勤怠管理のトップページを表示するビュー
    """
    # ログインしているユーザーの最新のレポートを1件取得
    latest_report = Report.objects.filter(user=request.user).order_by('-work_date').first()
    
    # ユーザーの現在の出勤状態を取得
    attendance_status = get_user_attendance_status(request.user)
    
    # 最新の出勤記録を取得（表示用）
    last_clock_in = Timestamp.objects.filter(
        user=request.user,
        status='CLOCK_IN'
    ).order_by('-timestamp').first()
    
    # 最新の退勤記録を取得（表示用）
    last_clock_out = Timestamp.objects.filter(
        user=request.user,
        status='CLOCK_OUT'
    ).order_by('-timestamp').first()

    # 既存のcontextに、新しいデータを追加
    context = {
        'title': '勤怠管理システム',
        'message': '勤怠管理システムへようこそ',
        'user': request.user,      # ◀ ログインユーザー情報を追加
        'report': latest_report,   # ◀ 最新のレポート情報を追加
        'attendance_status': attendance_status,
        'last_clock_in': last_clock_in,
        'last_clock_out': last_clock_out,
    }
    
    return render(request, 'kintai/mypage_top.html', context)


# kintai/views.py の checkin_view を修正

# kintai/views.py


@login_required
def checkin_view(request):
    # 既に出勤中の場合は出勤できない
    attendance_status = get_user_attendance_status(request.user)
    if attendance_status == 'CLOCKED_IN':
        return render(request, 'kintai/checkin_page.html', {
            'user': request.user,
            'form': None,
            'error_message': '既に出勤済みです。退勤してから再度出勤してください。'
        })
    
    if request.method == 'POST':
        form = ReportImageForm(request.POST, request.FILES)
        if form.is_valid():
            # (既存のレポート作成処理はそのまま)
            carrier, _ = Carrier.objects.get_or_create(carrier_name="テスト運送")
            new_report = Report.objects.create(
                user=request.user,
                carrier=carrier,
                report_type='DISPATCH',
                work_date=timezone.now().date(),
                close_number=0,
                swing_number=0,
            )
            report_image = form.save(commit=False)
            report_image.report = new_report
            report_image.save()
            
            # --- ▼ ここから追記 ▼ ---
            # 同時に出勤(CLOCK_IN)のTimestampも作成する
            Timestamp.objects.create(
                user=request.user,
                status='CLOCK_IN',
                timestamp=timezone.now()
            )
            # --- ▲ ここまで追記 ▲ ---
            
            return redirect('kintai_complete') 

    else:
        form = ReportImageForm()

    context = {'user': request.user, 'form': form}
    return render(request, 'kintai/checkin_page.html', context)


@login_required
def checkin_complete_view(request):
    # ログインユーザーが作成した最新の画像レポートを取得
    latest_image = ReportImage.objects.filter(report__user=request.user).order_by('-created_at').first()

    context = {
        'user': request.user,
        'report_image': latest_image,
    }
    return render(request, 'kintai/checkin_complete.html', context)


@login_required
def checkout_view(request):
    last_clock_in = Timestamp.objects.filter(
        user=request.user,
        status='CLOCK_IN'
    ).order_by('-timestamp').first()

    if request.method == 'POST':
        # 退勤記録をデータベースに作成
        Timestamp.objects.create(
            user=request.user,
            status='CLOCK_OUT',
            timestamp=timezone.now()
        )
        # 完了したらマイページに戻る
        return redirect('kintai_top')

    # 通常通りページを表示する場合 (GETリクエスト)
    context = {
        'user': request.user,
        'last_clock_in': last_clock_in,
    }
    return render(request, 'kintai/checkout_page.html', context)



@login_required
def performance_view(request):
    """
    個人実績ページを表示するビュー
    """
    # スライダーの期間を取得（デフォルトは6ヶ月）
    months_back = int(request.GET.get('months', 6))
    
    # ログインユーザーのレポートを取得（指定期間分）
    from datetime import date, timedelta
    from dateutil.relativedelta import relativedelta
    
    end_date = date.today()
    start_date = end_date - relativedelta(months=months_back)
    
    reports = Report.objects.filter(
        user=request.user,
        work_date__gte=start_date,
        work_date__lte=end_date
    ).order_by('-work_date')
    
    # 統計情報を計算
    total_reports = reports.count()
    total_close_number = sum(report.close_number or 0 for report in reports)
    total_mnp_close_number = sum(report.mnp_close_number or 0 for report in reports)
    
    # 月別統計
    monthly_stats = {}
    for report in reports:
        month_key = report.work_date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'close_number': 0,
                'swing_number': 0,
                'new_close_number': 0,
                'upg_close_number': 0,
                'mnp_close_number': 0,
                'count': 0
            }
        monthly_stats[month_key]['close_number'] += report.close_number or 0
        monthly_stats[month_key]['swing_number'] += report.swing_number or 0
        monthly_stats[month_key]['new_close_number'] += report.new_close_number or 0
        monthly_stats[month_key]['upg_close_number'] += report.upg_close_number or 0
        monthly_stats[month_key]['mnp_close_number'] += report.mnp_close_number or 0
        monthly_stats[month_key]['count'] += 1

    # グラフ用データ（ラベルは年月順にソート）
    monthly_labels = sorted(monthly_stats.keys())
    monthly_close_totals = [monthly_stats[m]['close_number'] for m in monthly_labels]
    monthly_new_close_totals = [monthly_stats[m]['new_close_number'] for m in monthly_labels]
    monthly_upg_close_totals = [monthly_stats[m]['upg_close_number'] for m in monthly_labels]
    monthly_mnp_close_totals = [monthly_stats[m]['mnp_close_number'] for m in monthly_labels]
    
    # 生産性（平均値）: 月ごとの平均クローズ数と各種クローズ数
    monthly_close_avg = [
        (monthly_stats[m]['close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    monthly_new_close_avg = [
        (monthly_stats[m]['new_close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    monthly_upg_close_avg = [
        (monthly_stats[m]['upg_close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    monthly_mnp_close_avg = [
        (monthly_stats[m]['mnp_close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]

    context = {
        'title': '個人実績',
        'user': request.user,
        'reports': reports[:10],  # 最新10件
        'total_reports': total_reports,
        'total_close_number': total_close_number,
        'total_mnp_close_number': total_mnp_close_number,
        'monthly_stats': monthly_stats,
        # グラフ用
        'monthly_labels': monthly_labels,
        'monthly_close_totals': monthly_close_totals,
        'monthly_new_close_totals': monthly_new_close_totals,
        'monthly_upg_close_totals': monthly_upg_close_totals,
        'monthly_mnp_close_totals': monthly_mnp_close_totals,
        'monthly_close_avg': monthly_close_avg,
        'monthly_new_close_avg': monthly_new_close_avg,
        'monthly_upg_close_avg': monthly_upg_close_avg,
        'monthly_mnp_close_avg': monthly_mnp_close_avg,
        # スライダー用
        'months_back': months_back,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'kintai/performance.html', context)


@login_required
def team_performance_view(request):
    """
    チーム全体の実績一覧ページを表示するビュー
    """
    from datetime import date, timedelta
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # 日付選択（デフォルトは複数ユーザーがレポートを出している日付）
    # 複数ユーザーがいる日付を探す
    from django.db.models import Count
    dates_with_multiple_users = Report.objects.values('work_date').annotate(
        user_count=Count('user', distinct=True)
    ).filter(user_count__gt=1).order_by('-work_date')
    
    if dates_with_multiple_users.exists():
        default_date_str = dates_with_multiple_users.first()['work_date'].strftime('%Y-%m-%d')
    else:
        # 複数ユーザーがいない場合は最新の日付
        default_date = Report.objects.order_by('-work_date').first()
        if default_date:
            default_date_str = default_date.work_date.strftime('%Y-%m-%d')
        else:
            default_date_str = date.today().strftime('%Y-%m-%d')
    
    selected_date = request.GET.get('date', default_date_str)
    
    try:
        selected_date_obj = date.fromisoformat(selected_date)
    except ValueError:
        selected_date_obj = date.today()
    
    # 選択された日の全社員のレポートを取得
    reports = Report.objects.filter(work_date=selected_date_obj).order_by('user__username')
    
    # 社員別の統計を計算
    user_stats = {}
    for report in reports:
        user = report.user
        if user not in user_stats:
            user_stats[user] = {
                'reports': [],
                'total_close': 0,
                'total_swing': 0,
                'total_new': 0,
                'total_upg': 0,
                'total_mnp': 0,
            }
        
        user_stats[user]['reports'].append(report)
        user_stats[user]['total_close'] += report.close_number or 0
        user_stats[user]['total_swing'] += report.swing_number or 0
        user_stats[user]['total_new'] += report.new_close_number or 0
        user_stats[user]['total_upg'] += report.upg_close_number or 0
        user_stats[user]['total_mnp'] += report.mnp_close_number or 0
    
    # 全体統計
    total_reports_count = reports.count()
    total_close_all = sum(report.close_number or 0 for report in reports)
    total_swing_all = sum(report.swing_number or 0 for report in reports)
    total_new_all = sum(report.new_close_number or 0 for report in reports)
    total_upg_all = sum(report.upg_close_number or 0 for report in reports)
    total_mnp_all = sum(report.mnp_close_number or 0 for report in reports)
    
    context = {
        'title': '実績一覧',
        'selected_date': selected_date_obj,
        'selected_date_str': selected_date,
        'reports': reports,
        'user_stats': user_stats,
        'total_reports_count': total_reports_count,
        'total_close_all': total_close_all,
        'total_swing_all': total_swing_all,
        'total_new_all': total_new_all,
        'total_upg_all': total_upg_all,
        'total_mnp_all': total_mnp_all,
    }
    
    return render(request, 'kintai/team_performance.html', context)




@login_required
def checkout_complete_view(request):
    """
    退勤完了ページを表示するビュー
    """
    # 最新の出勤記録を取得
    last_clock_in = Timestamp.objects.filter(
        user=request.user,
        status='CLOCK_IN'
    ).order_by('-timestamp').first()
    
    # 「退勤を確定する」ボタンが押された場合
    if request.method == 'POST':
        # 退勤記録をデータベースに作成
        Timestamp.objects.create(
            user=request.user,
            status='CLOCK_OUT',
            timestamp=timezone.now()
        )
        # マイページに戻る
        return redirect('kintai_top')
    
    context = {
        'user': request.user,
        'last_clock_in': last_clock_in,
    }
    return render(request, 'kintai/checkout_complete.html', context)


@login_required
def kintai_clockout_view(request):
    # 出勤していない場合は退勤できない
    attendance_status = get_user_attendance_status(request.user)
    if attendance_status != 'CLOCKED_IN':
        return render(request, 'kintai/checkout_page.html', {
            'user': request.user,
            'form': None,
            'last_clock_in': None,
            'error_message': '出勤していません。先に出勤してください。'
        })
    
    last_clock_in = Timestamp.objects.filter(
        user=request.user,
        status='CLOCK_IN'
    ).order_by('-timestamp').first()

    # 「退勤を確定」ボタンが押された場合 (POSTリクエスト)
    if request.method == 'POST':
        form = ClockOutReportForm(request.POST)
        if form.is_valid():
            # 1. フォームのデータを元にReportオブジェクトを作成
            report = form.save(commit=False) # DBにはまだ保存しない
            report.user = request.user
            report.work_date = timezone.now().date()
            report.report_type = 'WIND' # レポートタイプを固定（必要に応じて変更）
            report.save() # ReportをDBに保存

            # 2. 退勤記録(Timestamp)をDBに作成
            Timestamp.objects.create(
                user=request.user,
                status='CLOCK_OUT',
                timestamp=timezone.now()
            )
            return redirect('kintai_checkout_complete')

    # 通常通りページを表示する場合 (GETリクエスト)
    else:
        form = ClockOutReportForm()

    context = {
        'user': request.user,
        'last_clock_in': last_clock_in,
        'form': form, # ◀ フォームをテンプレートに渡す
    }
    return render(request, 'kintai/checkout_page.html', context)


# 管理者画面のビュー
@staff_member_required
def admin_dashboard_view(request):
    """管理者ダッシュボード"""
    User = get_user_model()
    
    # 統計データの取得
    total_users = User.objects.count()
    total_reports = Report.objects.count()
    today_reports = Report.objects.filter(work_date=date.today()).count()
    
    # 最近7日間でレポートを提出したユーザー数を計算
    week_ago = date.today() - relativedelta(days=7)
    active_users = User.objects.filter(
        report__work_date__gte=week_ago
    ).distinct().count()
    
    context = {
        'title': '管理者ダッシュボード',
        'total_users': total_users,
        'total_reports': total_reports,
        'today_reports': today_reports,
        'active_users': active_users,
    }
    
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def admin_users_view(request):
    """ユーザー管理画面"""
    User = get_user_model()
    users = User.objects.all().order_by('-date_joined')
    
    # 各ユーザーの統計情報を計算
    user_stats = {}
    for user in users:
        user_reports = Report.objects.filter(user=user)
        total_reports = user_reports.count()
        total_close = sum(report.close_number or 0 for report in user_reports)
        total_mnp = sum(report.mnp_close_number or 0 for report in user_reports)
        
        # 最新のレポート日
        latest_report = user_reports.order_by('-work_date').first()
        last_report_date = latest_report.work_date if latest_report else None
        
        user_stats[user] = {
            'total_reports': total_reports,
            'total_close': total_close,
            'total_mnp': total_mnp,
            'last_report_date': last_report_date,
        }
    
    context = {
        'title': 'ユーザー管理',
        'users': users,
        'user_stats': user_stats,
    }
    
    return render(request, 'admin/users.html', context)


@staff_member_required
def admin_reports_view(request):
    """レポート管理画面"""
    reports = Report.objects.all().order_by('-work_date', '-created_at')
    
    context = {
        'title': 'レポート管理',
        'reports': reports,
    }
    
    return render(request, 'admin/reports.html', context)


@staff_member_required
def admin_carriers_view(request):
    """キャリア管理画面"""
    from datetime import date
    from dateutil.relativedelta import relativedelta
    from django.db.models import Count, Sum
    
    # 期間選択（デフォルトは6ヶ月）
    months_back = int(request.GET.get('months', 6))
    end_date = date.today()
    start_date = end_date - relativedelta(months=months_back)
    
    # 全キャリアを取得
    carriers = Carrier.objects.all().order_by('carrier_name')
    
    # 各キャリアの統計情報を計算
    carrier_stats = {}
    for carrier in carriers:
        # 指定期間内のレポートを取得
        reports = Report.objects.filter(
            carrier=carrier,
            work_date__gte=start_date,
            work_date__lte=end_date
        )
        
        # 月別統計
        monthly_stats = {}
        for report in reports:
            month_key = report.work_date.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'work_days': 0,
                    'total_close': 0,
                    'new_close': 0,
                    'upg_close': 0,
                    'mnp_close': 0,
                    'reports': []
                }
            
            monthly_stats[month_key]['work_days'] += 1
            monthly_stats[month_key]['total_close'] += report.close_number or 0
            monthly_stats[month_key]['new_close'] += report.new_close_number or 0
            monthly_stats[month_key]['upg_close'] += report.upg_close_number or 0
            monthly_stats[month_key]['mnp_close'] += report.mnp_close_number or 0
            monthly_stats[month_key]['reports'].append(report)
        
        # 全体統計
        total_work_days = reports.count()
        total_close = sum(report.close_number or 0 for report in reports)
        total_new = sum(report.new_close_number or 0 for report in reports)
        total_upg = sum(report.upg_close_number or 0 for report in reports)
        total_mnp = sum(report.mnp_close_number or 0 for report in reports)
        
        carrier_stats[carrier] = {
            'monthly_stats': monthly_stats,
            'total_work_days': total_work_days,
            'total_close': total_close,
            'total_new': total_new,
            'total_upg': total_upg,
            'total_mnp': total_mnp,
        }
    
    context = {
        'title': 'キャリア管理',
        'carriers': carriers,
        'carrier_stats': carrier_stats,
        'months_back': months_back,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'admin/carriers.html', context)


@staff_member_required
def admin_analytics_view(request):
    """分析画面"""
    # 月別レポート数の集計
    monthly_stats = {}
    reports = Report.objects.all().order_by('work_date')
    
    for report in reports:
        month_key = report.work_date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = 0
        monthly_stats[month_key] += 1
    
    context = {
        'title': '分析',
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'admin/analytics.html', context)


@staff_member_required
def admin_user_performance_view(request, user_id):
    """管理者用個人実績画面"""
    User = get_user_model()
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('admin_users')
    
    # 期間選択パラメータを取得（デフォルトは6ヶ月）
    months_back = int(request.GET.get('months', 6))
    pie_months_back = int(request.GET.get('pie_months', 6))
    end_date = date.today()
    start_date = end_date - relativedelta(months=months_back)
    
    # 円グラフ用の期間
    pie_end_date = date.today()
    pie_start_date = pie_end_date - relativedelta(months=pie_months_back)
    
    reports = Report.objects.filter(
        user=target_user,
        work_date__gte=start_date,
        work_date__lte=end_date
    ).order_by('-work_date')
    
    # 円グラフ用のレポート
    pie_reports = Report.objects.filter(
        user=target_user,
        work_date__gte=pie_start_date,
        work_date__lte=pie_end_date
    ).order_by('-work_date')
    
    # 統計情報を計算
    total_reports = reports.count()
    total_close_number = sum(report.close_number or 0 for report in reports)
    total_mnp_close_number = sum(report.mnp_close_number or 0 for report in reports)
    
    # 月別統計
    monthly_stats = {}
    for report in reports:
        month_key = report.work_date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'close_number': 0,
                'swing_number': 0,
                'new_close_number': 0,
                'upg_close_number': 0,
                'mnp_close_number': 0,
                'count': 0
            }
        monthly_stats[month_key]['close_number'] += report.close_number or 0
        monthly_stats[month_key]['swing_number'] += report.swing_number or 0
        monthly_stats[month_key]['new_close_number'] += report.new_close_number or 0
        monthly_stats[month_key]['upg_close_number'] += report.upg_close_number or 0
        monthly_stats[month_key]['mnp_close_number'] += report.mnp_close_number or 0
        monthly_stats[month_key]['count'] += 1

    # グラフ用データ
    monthly_labels = sorted(monthly_stats.keys())
    monthly_close_totals = [monthly_stats[m]['close_number'] for m in monthly_labels]
    monthly_new_close_totals = [monthly_stats[m]['new_close_number'] for m in monthly_labels]
    monthly_upg_close_totals = [monthly_stats[m]['upg_close_number'] for m in monthly_labels]
    monthly_mnp_close_totals = [monthly_stats[m]['mnp_close_number'] for m in monthly_labels]
    
    # 生産性（平均値）
    monthly_close_avg = [
        (monthly_stats[m]['close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    monthly_new_close_avg = [
        (monthly_stats[m]['new_close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    monthly_upg_close_avg = [
        (monthly_stats[m]['upg_close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    monthly_mnp_close_avg = [
        (monthly_stats[m]['mnp_close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]
    
    # 円グラフ用データ（クローズ件数を100とした時の割合）
    pie_total_new = sum(report.new_close_number or 0 for report in pie_reports)
    pie_total_upg = sum(report.upg_close_number or 0 for report in pie_reports)
    pie_total_mnp = sum(report.mnp_close_number or 0 for report in pie_reports)
    pie_total_close = sum(report.close_number or 0 for report in pie_reports)
    
    if pie_total_close > 0:
        new_ratio = (pie_total_new / pie_total_close) * 100
        upg_ratio = (pie_total_upg / pie_total_close) * 100
        mnp_ratio = (pie_total_mnp / pie_total_close) * 100
        other_ratio = 100 - new_ratio - upg_ratio - mnp_ratio
    else:
        new_ratio = upg_ratio = mnp_ratio = other_ratio = 0
    
    pie_chart_data = [new_ratio, upg_ratio, mnp_ratio, other_ratio]

    context = {
        'title': '個人実績',
        'target_user': target_user,
        'total_reports': total_reports,
        'total_close_number': total_close_number,
        'total_mnp_close_number': total_mnp_close_number,
        'monthly_stats': monthly_stats,
        'monthly_labels': monthly_labels,
        'monthly_close_totals': monthly_close_totals,
        'monthly_new_close_totals': monthly_new_close_totals,
        'monthly_upg_close_totals': monthly_upg_close_totals,
        'monthly_mnp_close_totals': monthly_mnp_close_totals,
        'monthly_close_avg': monthly_close_avg,
        'monthly_new_close_avg': monthly_new_close_avg,
        'monthly_upg_close_avg': monthly_upg_close_avg,
        'monthly_mnp_close_avg': monthly_mnp_close_avg,
        'pie_chart_data': pie_chart_data,
        'months_back': months_back,
        'pie_months_back': pie_months_back,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'admin/user_performance.html', context)


@staff_member_required
def admin_attendance_management_view(request):
    """
    稼働管理画面 - 出勤中のユーザーと打刻時刻を表示
    """
    User = get_user_model()
    
    # 日付パラメータを取得（デフォルトは今日）
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # 全ユーザーを取得
    all_users = User.objects.all().order_by('username')
    
    # 選択された日付のレポートを取得
    attendance_data = []
    for user in all_users:
        # 選択された日付のレポートを取得
        date_reports = Report.objects.filter(
            user=user,
            work_date=selected_date
        ).order_by('-created_at')
        
        if date_reports.exists():
            latest_report = date_reports.first()
            attendance_data.append({
                'user': user,
                'status': 'CLOCKED_IN',
                'clock_in_time': latest_report.created_at,
                'carrier': latest_report.carrier,
                'close_number': latest_report.close_number,
                'swing_number': latest_report.swing_number,
            })
        else:
            attendance_data.append({
                'user': user,
                'status': 'NO_RECORD',
                'clock_in_time': None,
                'carrier': None,
                'close_number': 0,
                'swing_number': 0,
            })
    
    # 出勤中のユーザーのみをフィルタ
    working_users = [data for data in attendance_data if data['status'] == 'CLOCKED_IN']
    
    context = {
        'all_users': attendance_data,
        'working_users': working_users,
        'working_count': len(working_users),
        'total_count': len(all_users),
        'selected_date': selected_date,
        'today': date.today(),
    }
    
    return render(request, 'admin/attendance_management.html', context)





def get_calendar_from_sheet():
    # 遅延importにより起動時のネットワーク依存エラーを回避
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("カレンダー").sheet1  # スプシ名
    data = sheet.get_all_records()
    return data


