from django import forms
from core.models import ReportImage
from core.models import Carrier,Report
from kintai.models import Timestamp# ◀ Carrierを追加
from PIL import Image
import os

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
    
    def clean_upload_img(self):
        """
        画像ファイルのバリデーション
        - ファイルタイプの検証
        - ファイルサイズの検証
        - MIMEタイプの検証
        """
        img = self.cleaned_data.get('upload_img')
        
        if not img:
            raise forms.ValidationError('画像ファイルを選択してください。')
        
        # ファイルサイズの検証（最大10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        if img.size > max_size:
            raise forms.ValidationError(f'画像ファイルのサイズは10MB以下にしてください。現在: {img.size / 1024 / 1024:.2f}MB')
        
        # 許可されたファイル拡張子
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_name = img.name.lower()
        
        # 拡張子の検証
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise forms.ValidationError(f'画像ファイルのみアップロードできます。対応形式: {", ".join(allowed_extensions)}')
        
        # MIMEタイプの検証
        allowed_mime_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if img.content_type not in allowed_mime_types:
            raise forms.ValidationError('画像ファイルのみアップロードできます。')
        
        # PILを使用して実際に画像ファイルかどうかを検証
        try:
            img.seek(0)
            with Image.open(img) as im:
                im.verify()
            img.seek(0)
        except Exception:
            raise forms.ValidationError('不正な画像ファイルです。')
        
        return img




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

# ドロップダウンで表示する数字の選択肢を定義（例：0から50まで）
NUMBER_CHOICES = [(i, str(i)) for i in range(51)]

# ... (他のフォームクラスはそのまま) ...

# kintai/forms.py

NUMBER_CHOICES = [(i, str(i)) for i in range(51)]


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

        # Carrierの選択肢を運送会社名で表示し、必須項目にする（「テスト運送」を除外）
        self.fields['carrier'].queryset = Carrier.objects.exclude(carrier_name='テスト運送')
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


class UserRegistrationForm(forms.Form):
    """新規アカウント作成フォーム"""
    username = forms.CharField(
        label='ユーザー名',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'ユーザー名を入力',
            'required': True
        })
    )
    password1 = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'パスワードを入力',
            'required': True
        })
    )
    password2 = forms.CharField(
        label='パスワード（確認）',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'パスワードを再入力',
            'required': True
        })
    )
    first_name = forms.CharField(
        label='姓',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '姓を入力',
            'required': True
        })
    )
    last_name = forms.CharField(
        label='名',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '名を入力',
            'required': True
        })
    )
    email = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'メールアドレスを入力',
            'required': True
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('このユーザー名は既に使用されています。')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('パスワードが一致しません。')
        
        return cleaned_data