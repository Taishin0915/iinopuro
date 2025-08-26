# wind_app/views.py

from django.shortcuts import render
from .models import Report  # Reportモデルをインポート

# URL設定で指定した関数を定義
def index(request): # あなたのurls.pyに合わせて関数名をindexにしました
    
    # データベースから全てのReportオブジェクトを取得し、新しい順に並べる
    reports = Report.objects.all().order_by('-created_at')
    
    # テンプレートに渡すためのデータを辞書形式で作成
    context = {
        'reports': reports,
    }
    
    # データをテンプレートに渡して、HTMLを生成する
    return render(request, 'wind_app/job_wind.html', context)