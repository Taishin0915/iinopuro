import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Carrier, Report, DepartureRecord
from kintai.models import Timestamp


class Command(BaseCommand):
    help = 'CSVファイルからデータをインポートします'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='インポートするCSVファイルのパス')
        parser.add_argument('model_type', type=str, choices=['users', 'carriers', 'reports', 'timestamps', 'departures'],
                          help='インポートするモデルの種類')
        parser.add_argument('--encoding', type=str, default='utf-8', help='CSVファイルのエンコーディング (デフォルト: utf-8)')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        model_type = options['model_type']
        encoding = options['encoding']

        if not os.path.exists(csv_file):
            raise CommandError(f'ファイルが見つかりません: {csv_file}')

        try:
            with open(csv_file, 'r', encoding=encoding) as file:
                reader = csv.DictReader(file)
                
                if model_type == 'users':
                    self.import_users(reader)
                elif model_type == 'carriers':
                    self.import_carriers(reader)
                elif model_type == 'reports':
                    self.import_reports(reader)
                elif model_type == 'timestamps':
                    self.import_timestamps(reader)
                elif model_type == 'departures':
                    self.import_departures(reader)
                    
        except Exception as e:
            raise CommandError(f'インポートエラー: {str(e)}')

    def import_users(self, reader):
        """
        ユーザーをインポート
        CSVフォーマット: id,user_name,created_at または username,email,first_name,last_name,password,is_staff
        """
        count = 0
        for row in reader:
            try:
                # 既存データ形式（id,user_name,created_at）の場合
                if 'user_name' in row:
                    username = row['user_name']
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': f'{username}@example.com',
                            'first_name': username,
                            'last_name': '',
                        }
                    )
                    if created:
                        user.set_password('password123')
                        user.save()
                        count += 1
                        self.stdout.write(f'ユーザー作成: {user.username}')
                    else:
                        self.stdout.write(f'ユーザー既存: {user.username}')
                # 新形式（username,email,first_name,last_name,password,is_staff）の場合
                else:
                    user, created = User.objects.get_or_create(
                        username=row['username'],
                        defaults={
                            'email': row.get('email', ''),
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'is_staff': row.get('is_staff', 'False').lower() == 'true',
                        }
                    )
                    if created:
                        password = row.get('password', 'password123')
                        user.set_password(password)
                        user.save()
                        count += 1
                        self.stdout.write(f'ユーザー作成: {user.username}')
                    else:
                        self.stdout.write(f'ユーザー既存: {user.username}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ユーザー作成エラー: {row.get("username", row.get("user_name", "unknown"))} - {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'ユーザーインポート完了: {count}件作成'))

    def import_carriers(self, reader):
        """
        キャリアをインポート
        CSVフォーマット: carrier_name
        """
        count = 0
        for row in reader:
            try:
                carrier, created = Carrier.objects.get_or_create(
                    carrier_name=row['carrier_name']
                )
                if created:
                    count += 1
                    self.stdout.write(f'キャリア作成: {carrier.carrier_name}')
                else:
                    self.stdout.write(f'キャリア既存: {carrier.carrier_name}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'キャリア作成エラー: {row.get("carrier_name", "unknown")} - {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'キャリアインポート完了: {count}件作成'))

    def import_reports(self, reader):
        """
        レポートをインポート
        既存データ形式: report_id,user_id,close_number,swing_number,carrier,created_at,user_name,work_date,new_close_number,upg_close_number,mnp_close_number,tv_close_number,net_close_number,tel_close_number,tos_close_num
        新形式: username,carrier_name,report_type,work_date,close_number,swing_number,new_close_number,upg_close_number,mnp_close_number,tv_close_number,net_close_number,tel_close_number,tos_close_number
        """
        count = 0
        
        # キャリアID→キャリア名のマッピング（既存データ用）
        carrier_mapping = {
            '1': 'au',        # ID 1 → au
            '2': 'SB',        # ID 2 → SB  
            '3': 'J:COM',     # ID 3 → J:COM
            '4': 'その他'      # ID 4 → その他
        }
        
        for row in reader:
            try:
                # 既存データ形式の場合
                if 'user_name' in row and 'carrier' in row:
                    username = row['user_name']
                    carrier_id = str(row['carrier'])
                    carrier_name = carrier_mapping.get(carrier_id, 'ドコモ')
                    
                    # ユーザーを取得または作成
                    user, _ = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': f'{username}@example.com',
                            'first_name': username,
                            'password': 'password123'
                        }
                    )
                    
                    # キャリアを取得または作成
                    carrier, _ = Carrier.objects.get_or_create(carrier_name=carrier_name)
                    
                    # 日付の解析
                    work_date = datetime.strptime(row['work_date'], '%Y-%m-%d').date()
                    
                    # 整数フィールドの処理
                    def parse_int(value):
                        return int(value) if value and str(value).strip() and str(value) != '' else None
                    
                    report = Report.objects.create(
                        user=user,
                        carrier=carrier,
                        report_type='WIND',  # デフォルトでWIND
                        work_date=work_date,
                        close_number=int(row['close_number']),
                        swing_number=int(row['swing_number']),
                        new_close_number=parse_int(row.get('new_close_number')),
                        upg_close_number=parse_int(row.get('upg_close_number')),
                        mnp_close_number=parse_int(row.get('mnp_close_number')),
                        tv_close_number=parse_int(row.get('tv_close_number')),
                        net_close_number=parse_int(row.get('net_close_number')),
                        tel_close_number=parse_int(row.get('tel_close_number')),
                        tos_close_number=parse_int(row.get('tos_close_num')),  # 注意：列名がtos_close_num
                    )
                    count += 1
                    self.stdout.write(f'レポート作成: {user.username} - {work_date}')
                    
                # 新形式の場合
                else:
                    user = User.objects.get(username=row['username'])
                    carrier = Carrier.objects.get(carrier_name=row['carrier_name'])
                    
                    work_date = datetime.strptime(row['work_date'], '%Y-%m-%d').date()
                    
                    def parse_int(value):
                        return int(value) if value and value.strip() else None
                    
                    report = Report.objects.create(
                        user=user,
                        carrier=carrier,
                        report_type=row.get('report_type', 'WIND'),
                        work_date=work_date,
                        close_number=int(row['close_number']),
                        swing_number=int(row['swing_number']),
                        new_close_number=parse_int(row.get('new_close_number')),
                        upg_close_number=parse_int(row.get('upg_close_number')),
                        mnp_close_number=parse_int(row.get('mnp_close_number')),
                        tv_close_number=parse_int(row.get('tv_close_number')),
                        net_close_number=parse_int(row.get('net_close_number')),
                        tel_close_number=parse_int(row.get('tel_close_number')),
                        tos_close_number=parse_int(row.get('tos_close_number')),
                    )
                    count += 1
                    self.stdout.write(f'レポート作成: {user.username} - {work_date}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'レポート作成エラー: {str(e)} - Row: {row}'))
        
        self.stdout.write(self.style.SUCCESS(f'レポートインポート完了: {count}件作成'))

    def import_timestamps(self, reader):
        """
        勤怠記録をインポート
        CSVフォーマット: username,status,timestamp
        """
        count = 0
        for row in reader:
            try:
                user = User.objects.get(username=row['username'])
                
                # 日時の解析
                timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                timestamp = timezone.make_aware(timestamp)
                
                timestamp_obj = Timestamp.objects.create(
                    user=user,
                    status=row['status'],
                    timestamp=timestamp
                )
                count += 1
                self.stdout.write(f'勤怠記録作成: {user.username} - {row["status"]} - {timestamp}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'ユーザーが見つかりません: {row.get("username", "unknown")}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'勤怠記録作成エラー: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'勤怠記録インポート完了: {count}件作成'))

    def import_departures(self, reader):
        """
        出発記録をインポート
        CSVフォーマット: username,departure_date
        """
        count = 0
        for row in reader:
            try:
                user = User.objects.get(username=row['username'])
                departure_date = datetime.strptime(row['departure_date'], '%Y-%m-%d').date()
                
                departure, created = DepartureRecord.objects.get_or_create(
                    user=user,
                    departure_date=departure_date
                )
                if created:
                    count += 1
                    self.stdout.write(f'出発記録作成: {user.username} - {departure_date}')
                else:
                    self.stdout.write(f'出発記録既存: {user.username} - {departure_date}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'ユーザーが見つかりません: {row.get("username", "unknown")}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'出発記録作成エラー: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'出発記録インポート完了: {count}件作成'))
