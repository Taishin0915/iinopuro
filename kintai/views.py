# kintai/views.py

from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
# 🔽 Report, ReportImage, Carrier モデルをインポート
from core.models import Report, ReportImage, Carrier
# 🔽 作成したフォームをインポート
from .forms import ReportImageForm
from .models import Timestamp
from .forms import ClockOutForm
from .forms import ClockOutReportForm 






@login_required
def kintai_view(request):
    """
    勤怠管理のトップページを表示するビュー
    """
    # ログインしているユーザーの最新のレポートを1件取得
    latest_report = Report.objects.filter(user=request.user).order_by('-work_date').first()

    # 既存のcontextに、新しいデータを追加
    context = {
        'title': '勤怠管理システム',
        'message': '勤怠管理システムへようこそ',
        'user': request.user,      # ◀ ログインユーザー情報を追加
        'report': latest_report,   # ◀ 最新のレポート情報を追加
    }
    
    return render(request, 'kintai/mypage_top.html', context)


# kintai/views.py の checkin_view を修正

# kintai/views.py


@login_required
def checkin_view(request):
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
def checkout_complete_view(request):
    context = {
        'user': request.user,
    }
    return render(request, 'kintai/mypage_top.html', context)




@login_required
def kintai_clockout_view(request):
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
            return redirect('kintai_top')

    # 通常通りページを表示する場合 (GETリクエスト)
    else:
        form = ClockOutReportForm()

    context = {
        'user': request.user,
        'last_clock_in': last_clock_in,
        'form': form, # ◀ フォームをテンプレートに渡す
    }
    return render(request, 'kintai/checkout_page.html', context)