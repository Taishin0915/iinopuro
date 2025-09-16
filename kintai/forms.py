from django import forms
from core.models import ReportImage
from core.models import Carrier,Report
from kintai.models import Timestamp# ◀ Carrierを追加

class ReportImageForm(forms.ModelForm):
    """
    レポート画像をアップロードするためのフォーム
    """
    class Meta:
        model = ReportImage
        fields = ['upload_img']
        widgets = {
            'upload_img': forms.FileInput(attrs={
                # 'class': 'hidden',  # テスト中: コメントアウト
                'accept': 'image/*',
                # 'capture': 'environment',  # テスト中: コメントアウト
                # 'style': 'display: none !important; visibility: hidden !important;'  # テスト中: コメントアウト
            })
        }




class ClockOutForm(forms.ModelForm):
    # Carrierを選択するためのフィールドを追加
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.all(),
        label="運送会社",
        empty_label="運送会社を選択してください"
    )

    class Meta:
        model = Timestamp
        # フォームで使うフィールドを指定 (statusとtimestampはビューで設定するので不要)
        fields = ['carrier'] 



# kintai/forms.py

from django import forms
from core.models import Report, Carrier

# ドロップダウンで表示する数字の選択肢を定義（例：0から20まで）
NUMBER_CHOICES = [(i, str(i)) for i in range(21)]

# ... (他のフォームクラスはそのまま) ...

# kintai/forms.py

NUMBER_CHOICES = [(i, str(i)) for i in range(21)]


class ClockOutReportForm(forms.ModelForm):
    class Meta:
        model = Report
        # フォームに表示したいフィールドをリストアップ
        fields = [
            'carrier', 
            'close_number', 
            'swing_number', 
            'new_close_number', 
            'upg_close_number', 
            'mnp_close_number', 
            'tv_close_number', 
            'net_close_number', 
            'tel_close_number', 
            'tos_close_number',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Carrierの選択肢を運送会社名で表示し、必須項目にする
        self.fields['carrier'].queryset = Carrier.objects.all()
        self.fields['carrier'].label = "キャリア"
        self.fields['carrier'].empty_label = "選択してください"
        self.fields['carrier'].required = True

        # ドロップダウンに変更したい数値フィールドのリスト（実際のフィールド名）
        number_fields = [
            'close_number', 'swing_number', 'new_close_number', 'upg_close_number',
            'mnp_close_number', 'tv_close_number', 'net_close_number',
            'tel_close_number', 'tos_close_number'
        ]

        # フィールド名と日本語ラベルのマッピング
        field_labels = {
            'close_number': 'クローズ件数',
            'swing_number': 'スウィング件数',
            'new_close_number': '新規件数',
            'upg_close_number': 'UPG件数',
            'mnp_close_number': 'MNP件数',
            'tv_close_number': 'TV件数',
            'net_close_number': 'NET件数',
            'tel_close_number': 'TEL件数',
            'tos_close_number': 'TOS件数'
        }

        # ループ処理ですべての数値フィールドをドロップダウンに変更
        for field_name in number_fields:
            self.fields[field_name].widget = forms.Select(choices=NUMBER_CHOICES)
            self.fields[field_name].label = field_labels.get(field_name, field_name) # 日本語ラベルを設定

        # J:COMの時だけ表示するフィールドに、目印となるCSSクラスを追加
        jcom_fields = [
            'tv_close_number', 
            'net_close_number', 
            'tel_close_number', 
            'tos_close_number'
        ]
        for field_name in jcom_fields:
            self.fields[field_name].widget.attrs.update({'class': 'jcom-field'})