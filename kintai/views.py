# kintai/views.py

from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.db.models import Count
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
# 🔽 Report, ReportImage, Carrier モデルをインポート
from core.models import Report, ReportImage, Carrier, DepartureRecord
# 🔽 作成したフォームをインポート
from .forms import ReportImageForm, ClockOutReportForm, UserRegistrationForm
from .models import Timestamp


def login_view(request):
    """ログイン・登録画面（統一）"""
    if request.user.is_authenticated:
        return redirect('kintai_top')
    
    login_form = AuthenticationForm()
    registration_form = UserRegistrationForm()
    
    # ログイン処理
    if request.method == 'POST':
        print(f"DEBUG: POST received - {request.POST}")  # デバッグ
        print(f"DEBUG: User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")  # デバッグ
        print(f"DEBUG: Remote IP: {request.META.get('REMOTE_ADDR', 'Unknown')}")  # デバッグ
        
        login_form = AuthenticationForm(request, data=request.POST)
        print(f"DEBUG: Form valid - {login_form.is_valid()}")  # デバッグ
        
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            print(f"DEBUG: Authenticating user: {username}")  # デバッグ
            print(f"DEBUG: Password length: {len(password) if password else 0}")  # デバッグ
            
            # ユーザーが存在するかチェック
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user_exists = User.objects.filter(username=username).exists()
            print(f"DEBUG: User exists in database: {user_exists}")  # デバッグ
            
            user = authenticate(request, username=username, password=password)
            print(f"DEBUG: User authenticated: {user is not None}")  # デバッグ
            
            if user is not None:
                print(f"DEBUG: User details: {user.username}, Active: {user.is_active}")  # デバッグ
                if user.is_active:
                    login(request, user)
                    print("DEBUG: Login successful, redirecting")  # デバッグ
                    messages.success(request, f'ようこそ、{user.username}さん！')
                    return redirect('kintai_top')
                else:
                    print("DEBUG: User account is inactive")  # デバッグ
                    messages.error(request, 'このアカウントは無効化されています。管理者にお問い合わせください。')
            else:
                print("DEBUG: Authentication failed")  # デバッグ
                if user_exists:
                    messages.error(request, 'パスワードが正しくありません。')
                else:
                    messages.error(request, 'ユーザー名が存在しません。')
        else:
            print("DEBUG: Form validation failed")  # デバッグ
            print(f"DEBUG: Form errors - {login_form.errors}")  # デバッグ
            
            # より詳細なエラーメッセージを表示
            if 'username' in login_form.errors:
                messages.error(request, 'ユーザー名を入力してください。')
            elif 'password' in login_form.errors:
                messages.error(request, 'パスワードを入力してください。')
            else:
                for field, errors in login_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    
    context = {
        'login_form': login_form,
    }
    return render(request, 'registration/login.html', context)


def register_view(request):
    """新規登録画面"""
    if request.user.is_authenticated:
        return redirect('kintai_top')
    
    registration_form = UserRegistrationForm()
    
    # 新規登録処理
    if request.method == 'POST':
        registration_form = UserRegistrationForm(request.POST)
        if registration_form.is_valid():
            User = get_user_model()
            user = User.objects.create_user(
                username=registration_form.cleaned_data['username'],
                password=registration_form.cleaned_data['password1'],
                first_name=registration_form.cleaned_data['first_name'],
                last_name=registration_form.cleaned_data['last_name'],
                email=registration_form.cleaned_data['email']
            )
            messages.success(request, 'アカウントが正常に作成されました！ログインしてください。')
            return redirect('login')
    
    context = {
        'registration_form': registration_form,
    }
    return render(request, 'registration/register.html', context)


def logout_view(request):
    """ログアウト"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')


def get_user_attendance_status(user):
    """
    ユーザーの現在の出勤状態を取得する
    Returns:
        'CLOCKED_IN': 出勤中
        'CLOCKED_OUT': 退勤中
        'NO_RECORD': 記録なし
    """
    # 日本時間での今日の日付を取得
    jst_now = timezone.localtime(timezone.now())
    today = jst_now.date()
    
    # 今日のレポートを取得
    today_reports = Report.objects.filter(
        user=user,
        work_date=today
    ).order_by('-created_at')
    
    print(f"DEBUG: User {user.username}, Today: {today}")
    print(f"DEBUG: Found {today_reports.count()} reports for today")
    
    if not today_reports.exists():
        print("DEBUG: No reports found, returning NO_RECORD")
        return 'NO_RECORD'
    
    # 最新のレポートを取得
    latest_report = today_reports.first()
    print(f"DEBUG: Latest report: {latest_report}")
    print(f"DEBUG: clock_out_time: {latest_report.clock_out_time}")
    
    # 退勤時刻が設定されているかチェック
    if latest_report.clock_out_time:
        print("DEBUG: clock_out_time exists, returning CLOCKED_OUT")
        return 'CLOCKED_OUT'
    else:
        print("DEBUG: clock_out_time is None, returning CLOCKED_IN")
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
    print(f"DEBUG: Final attendance_status: {attendance_status}")
    
    # 日本時間での今日の最新のレポートを取得（表示用）
    jst_now = timezone.localtime(timezone.now())
    today = jst_now.date()
    last_clock_in = Report.objects.filter(
        user=request.user,
        work_date=today
    ).order_by('-created_at').first()
    print(f"DEBUG: last_clock_in: {last_clock_in}")

    # 今日の出発記録をチェック
    departure_record = DepartureRecord.objects.filter(
        user=request.user,
        departure_date=today
    ).first()

    # 既存のcontextに、新しいデータを追加
    context = {
        'title': 'Resulta',
        'message': '勤怠管理システムへようこそ',
        'user': request.user,      # ◀ ログインユーザー情報を追加
        'report': latest_report,   # ◀ 最新のレポート情報を追加
        'attendance_status': attendance_status,
        'last_clock_in': last_clock_in,
        'departure_record': departure_record,
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
            # 日本時間での現在日付を取得
            jst_now = timezone.localtime(timezone.now())
            jst_date = jst_now.date()
            
            new_report = Report.objects.create(
                user=request.user,
                carrier=carrier,
                report_type='DISPATCH',
                work_date=jst_date,
                close_number=0,
                swing_number=0,
            )
            print(f"DEBUG: Created new report: {new_report}")
            print(f"DEBUG: Report clock_out_time: {new_report.clock_out_time}")
            report_image = form.save(commit=False)
            report_image.report = new_report
            report_image.save()
            
            # Reportモデルにclock_out_timeは設定しない（出勤時はnullのまま）
            # 退勤時にclock_out_timeを設定する
            
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
    # 日本時間での今日の最新のレポートを取得
    jst_now = timezone.localtime(timezone.now())
    today = jst_now.date()
    last_clock_in = Report.objects.filter(
        user=request.user,
        work_date=today
    ).order_by('-created_at').first()

    if request.method == 'POST':
        # Reportモデルのclock_out_timeを設定
        if last_clock_in:
            last_clock_in.clock_out_time = timezone.now()
            last_clock_in.save()
        # 完了したらマイページに戻る
        return redirect('kintai_top')

    # 通常通りページを表示する場合 (GETリクエスト)
    context = {
        'user': request.user,
        'last_clock_in': last_clock_in,
    }
    return render(request, 'kintai/checkout_page.html', context)



@login_required
def departure_view(request):
    """出発ボタン処理"""
    today = timezone.localtime(timezone.now()).date()
    
    # 今日の出発記録が既に存在するかチェック
    existing_departure = DepartureRecord.objects.filter(
        user=request.user,
        departure_date=today
    ).first()
    
    if existing_departure:
        messages.warning(request, '本日は既に出発ボタンを押しています。')
        return redirect('kintai_top')
    
    # 出発記録を作成
    departure_record = DepartureRecord.objects.create(
        user=request.user,
        departure_date=today
    )
    
    # 出発完了画面にリダイレクト
    return redirect('departure_complete')


@login_required
def departure_complete_view(request):
    """出発完了画面"""
    today = timezone.localtime(timezone.now()).date()
    
    # 今日の出発記録を取得
    departure_record = DepartureRecord.objects.filter(
        user=request.user,
        departure_date=today
    ).first()
    
    if not departure_record:
        messages.warning(request, '出発記録が見つかりません。')
        return redirect('kintai_top')
    
    context = {
        'user': request.user,
        'departure_time': departure_record.departure_time,
    }
    
    return render(request, 'kintai/departure_complete.html', context)


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
    
    # 生産性を計算（総クローズ件数÷稼働日数）
    productivity = round(total_close_number / total_reports, 2) if total_reports > 0 else 0
    
    
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
    
    # 出勤日数（月ごとのレポート数）
    monthly_work_days = [monthly_stats[m]['count'] for m in monthly_labels]
    
    # MNP件数（月ごとのMNP件数合計）
    monthly_mnp_totals = [monthly_stats[m]['mnp_close_number'] for m in monthly_labels]
    
    # 生産性（月ごとの総クローズ件数÷出勤日数）
    monthly_productivity = [
        (monthly_stats[m]['close_number'] / monthly_stats[m]['count']) if monthly_stats[m]['count'] else 0
        for m in monthly_labels
    ]

    context = {
        'title': '個人実績',
        'user': request.user,
        'reports': reports[:10],  # 最新10件
        'total_reports': total_reports,
        'total_close_number': total_close_number,
        'total_mnp_close_number': total_mnp_close_number,
        'productivity': productivity,
        'monthly_stats': monthly_stats,
        # グラフ用
        'monthly_labels': monthly_labels,
        'monthly_work_days': monthly_work_days,
        'monthly_mnp_totals': monthly_mnp_totals,
        'monthly_productivity': monthly_productivity,
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
    
    # デバッグ情報を追加
    print(f"DEBUG: selected_date = {selected_date}")
    print(f"DEBUG: selected_date_obj = {selected_date_obj}")
    print(f"DEBUG: selected_date_str = {selected_date}")
    
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
    
    # 日本時間での今日の最新のレポートを取得
    jst_now = timezone.localtime(timezone.now())
    today = jst_now.date()
    last_clock_in = Report.objects.filter(
        user=request.user,
        work_date=today
    ).order_by('-created_at').first()

    # 「退勤を確定」ボタンが押された場合 (POSTリクエスト)
    if request.method == 'POST':
        form = ClockOutReportForm(request.POST)
        if form.is_valid():
            # 既存のレポートに退勤時刻を設定
            if last_clock_in:
                last_clock_in.clock_out_time = timezone.now()
                last_clock_in.save()
            
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


# @staff_member_required  # 一時的にコメントアウト
def admin_carriers_view(request):
    """キャリア管理画面"""
    from datetime import date
    from dateutil.relativedelta import relativedelta
    from django.db.models import Count, Sum
    
    # 期間選択（デフォルトは6ヶ月）
    months_back = int(request.GET.get('months', 6))
    end_date = date.today()
    start_date = end_date - relativedelta(months=months_back)
    
    # 全キャリアを取得（テスト運送を除外）
    carriers = Carrier.objects.exclude(carrier_name="テスト運送").order_by('carrier_name')
    
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
        
        # 生産性を計算（1日あたりの平均クローズ件数）
        productivity = round(total_close / total_work_days, 1) if total_work_days > 0 else 0.0
        
        carrier_stats[carrier] = {
            'monthly_stats': monthly_stats,
            'total_work_days': total_work_days,
            'total_close': total_close,
            'total_new': total_new,
            'total_upg': total_upg,
            'total_mnp': total_mnp,
            'productivity': productivity,
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
def admin_carrier_detail_view(request, carrier_id):
    """キャリア詳細画面"""
    try:
        carrier = Carrier.objects.get(id=carrier_id)
    except Carrier.DoesNotExist:
        return redirect('admin_carriers')

    # 期間選択（デフォルトは3ヶ月）
    months_back = int(request.GET.get('months', 3))
    end_date = date.today()
    start_date = end_date - relativedelta(months=months_back)
    
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
                'reports': [],
                'productivity': 0.0
            }
        
        monthly_stats[month_key]['work_days'] += 1
        monthly_stats[month_key]['total_close'] += report.close_number or 0
        monthly_stats[month_key]['new_close'] += report.new_close_number or 0
        monthly_stats[month_key]['upg_close'] += report.upg_close_number or 0
        monthly_stats[month_key]['mnp_close'] += report.mnp_close_number or 0
        monthly_stats[month_key]['reports'].append(report)
        
        # 生産性を計算
        if monthly_stats[month_key]['work_days'] > 0:
            monthly_stats[month_key]['productivity'] = round(
                monthly_stats[month_key]['total_close'] / monthly_stats[month_key]['work_days'],
                1
            )
    
    # 全体統計
    stats = {
        'monthly_stats': monthly_stats,
        'total_work_days': reports.count(),
        'total_close': sum(report.close_number or 0 for report in reports),
        'total_new': sum(report.new_close_number or 0 for report in reports),
        'total_upg': sum(report.upg_close_number or 0 for report in reports),
        'total_mnp': sum(report.mnp_close_number or 0 for report in reports),
    }
    
    context = {
        'carrier': carrier,
        'stats': stats,
        'months_back': months_back,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'admin/carrier_detail.html', context)


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
    selected_month = request.GET.get('selected_month', '')  # 特定月選択用（YYYY-MM形式）
    
    # 1ヶ月表示で特定月が選択されている場合
    if months_back == 1 and selected_month:
        try:
            # 選択された月の開始日と終了日を設定
            year, month = map(int, selected_month.split('-'))
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        except (ValueError, IndexError):
            # 無効な形式の場合はデフォルトに戻す
            end_date = date.today()
            start_date = end_date - relativedelta(months=months_back)
    else:
        # 通常の期間選択
        end_date = date.today()
        start_date = end_date - relativedelta(months=months_back)
    
    reports = Report.objects.filter(
        user=target_user,
        work_date__gte=start_date,
        work_date__lte=end_date
    ).order_by('-work_date')
    
    # 円グラフ用のレポート（メインと同じ期間を使用）
    pie_reports = reports
    
    # 統計情報を計算
    total_reports = reports.count()
    total_close_number = sum(report.close_number or 0 for report in reports)
    total_mnp_close_number = sum(report.mnp_close_number or 0 for report in reports)
    
    # 生産性を計算（指定された期間の総クローズ件数÷指定された期間の稼働日数）
    productivity = round(total_close_number / total_reports, 2) if total_reports > 0 else 0
    
    # 稼働月リストを取得（1ヶ月表示の時に使用）
    available_months = []
    if months_back == 1:
        # ユーザーが稼働したすべての月を取得
        all_reports = Report.objects.filter(user=target_user).values('work_date').distinct()
        months_set = set()
        for report in all_reports:
            month_key = report['work_date'].strftime('%Y-%m')
            months_set.add(month_key)
        
        # 月でソート（新しい順）
        available_months = sorted(list(months_set), reverse=True)
        
        # 現在選択されている月を設定（デフォルトは最新月）
        if not selected_month and available_months:
            selected_month = available_months[0]
            # デフォルト月が選択された場合、期間を再設定
            try:
                year, month = map(int, selected_month.split('-'))
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
                
                # 再計算が必要
                reports = Report.objects.filter(
                    user=target_user,
                    work_date__gte=start_date,
                    work_date__lte=end_date
                ).order_by('-work_date')
                
                # 円グラフ用のレポートも更新
                pie_reports = reports
                
                total_reports = reports.count()
                total_close_number = sum(report.close_number or 0 for report in reports)
                total_mnp_close_number = sum(report.mnp_close_number or 0 for report in reports)
                productivity = round(total_close_number / total_reports, 2) if total_reports > 0 else 0
            except (ValueError, IndexError):
                pass
    
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
        'productivity': productivity,
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
        'start_date': start_date,
        'end_date': end_date,
        'available_months': available_months,  # 稼働月リスト
        'selected_month': selected_month,      # 選択中の月
    }
    
    return render(request, 'admin/user_performance.html', context)


# @staff_member_required  # 一時的にコメントアウト
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
    
    # 出勤中または出発記録があるユーザーをフィルタ
    working_users = [data for data in attendance_data if data['status'] == 'CLOCKED_IN' or data.get('departure_record') is not None]
    
    # 出勤率を計算（出勤人数 ÷ 全ユーザー数 × 100）
    working_count = len(working_users)
    total_count = len(all_users)
    attendance_rate = round((working_count / total_count * 100), 1) if total_count > 0 else 0.0
    
    # 出発記録を取得
    departure_records = DepartureRecord.objects.filter(
        departure_date=selected_date
    ).select_related('user')
    
    # 出発記録をユーザーデータに追加
    departure_dict = {record.user.id: record for record in departure_records}
    for data in attendance_data:
        data['departure_record'] = departure_dict.get(data['user'].id)
    
    context = {
        'all_users': attendance_data,
        'working_users': working_users,
        'working_count': working_count,
        'total_count': total_count,
        'attendance_rate': attendance_rate,
        'selected_date': selected_date,
        'today': date.today(),
        'departure_records': departure_records,
    }
    
    return render(request, 'admin/attendance_management.html', context)





@login_required
def profile_view(request):
    """プロフィール画面（パスワード変更）"""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'パスワードが正常に変更されました。')
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'kintai/profile.html', {
        'form': form,
    })


@staff_member_required
def admin_create_user_view(request):
    """管理者用新規ユーザー作成画面"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        is_staff = request.POST.get('is_staff') == 'True'
        
        # バリデーション
        if not username:
            messages.error(request, 'ユーザー名を入力してください。')
        elif not password1:
            messages.error(request, 'パスワードを入力してください。')
        elif password1 != password2:
            messages.error(request, 'パスワードが一致しません。')
        elif len(password1) < 8:
            messages.error(request, 'パスワードは8文字以上で入力してください。')
        else:
            # ユーザー名の重複チェック
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                messages.error(request, 'このユーザー名は既に使用されています。')
            else:
                # ユーザー作成
                try:
                    user = User.objects.create_user(
                        username=username,
                        password=password1,
                        is_staff=is_staff
                    )
                    messages.success(request, f'ユーザー「{username}」を作成しました。')
                    return redirect('admin_users')
                except Exception as e:
                    messages.error(request, f'ユーザー作成中にエラーが発生しました: {str(e)}')
    
    return render(request, 'admin/create_user.html')


@staff_member_required
def admin_delete_user_view(request):
    """管理者用ユーザー削除画面"""
    User = get_user_model()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        confirm_password = request.POST.get('confirm_password')
        
        # バリデーション
        if not user_id:
            messages.error(request, '削除するユーザーを選択してください。')
        elif not confirm_password:
            messages.error(request, '確認パスワードを入力してください。')
        elif confirm_password != 'delete12345':
            messages.error(request, '確認パスワードが正しくありません。')
        else:
            try:
                user = User.objects.get(id=user_id)
                username = user.username
                
                # 自分自身を削除しようとした場合のチェック
                if user == request.user:
                    messages.error(request, '自分自身を削除することはできません。')
                else:
                    user.delete()
                    messages.success(request, f'ユーザー「{username}」を削除しました。')
                    return redirect('admin_users')
            except User.DoesNotExist:
                messages.error(request, '選択されたユーザーが見つかりません。')
            except Exception as e:
                messages.error(request, f'ユーザー削除中にエラーが発生しました: {str(e)}')
    
    # 全ユーザーを取得（自分以外）
    users = User.objects.exclude(id=request.user.id).order_by('username')
    
    return render(request, 'admin/delete_user.html', {
        'users': users,
    })


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


