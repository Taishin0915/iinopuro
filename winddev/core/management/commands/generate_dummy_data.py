from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, date
import random
from core.models import Carrier, Report, ReportImage, DepartureRecord
from kintai.models import Timestamp


class Command(BaseCommand):
    help = 'Generate one year of dummy data for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of users to create (default: 5)'
        )
        parser.add_argument(
            '--carriers',
            type=int,
            default=3,
            help='Number of carriers to create (default: 3)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting dummy data generation...'))
        
        # ユーザーとキャリアを作成
        users = self.create_users(options['users'])
        carriers = self.create_carriers(options['carriers'])
        
        # 一年分のデータを生成
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        
        self.generate_reports(users, carriers, start_date, end_date)
        self.generate_timestamps(users, start_date, end_date)
        self.generate_departure_records(users, start_date, end_date)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated dummy data for {len(users)} users and {len(carriers)} carriers')
        )

    def create_users(self, num_users):
        """ダミーユーザーを作成"""
        users = []
        # 既存のユーザー数を確認
        existing_count = User.objects.count()
        start_index = existing_count + 1
        
        for i in range(num_users):
            user_index = start_index + i
            username = f'dummy_user_{user_index}'
            email = f'dummy{user_index}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'User{user_index}',
                    'last_name': 'Dummy',
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                users.append(user)
            else:
                # 既存のユーザーの場合もリストに追加（データ生成のため）
                users.append(user)
            
        self.stdout.write(f'Created/Found {len(users)} users')
        return users

    def create_carriers(self, num_carriers):
        """ダミーキャリアを作成"""
        carriers = []
        carrier_names = ['softbank', 'au', 'docomo']
        
        for carrier_name in carrier_names:
            carrier, created = Carrier.objects.get_or_create(
                carrier_name=carrier_name
            )
            carriers.append(carrier)
            
        self.stdout.write(f'Created {len(carriers)} carriers')
        return carriers

    def generate_reports(self, users, carriers, start_date, end_date):
        """レポートデータを生成"""
        report_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # 土日は基本的にレポートなし（たまにあり）
            if current_date.weekday() < 5 or random.random() < 0.1:
                # 各ユーザーがランダムにレポートを作成
                for user in users:
                    if random.random() < 0.8:  # 80%の確率でレポート作成
                        carrier = random.choice(carriers)
                        report_type = random.choice(['DISPATCH', 'WIND'])
                        
                        # 基本フィールド
                        close_number = random.randint(1, 50)
                        swing_number = random.randint(1, 30)
                        
                        report = Report.objects.create(
                            user=user,
                            carrier=carrier,
                            work_date=current_date,
                            report_type=report_type,
                            close_number=close_number,
                            swing_number=swing_number,
                            clock_out_time=timezone.now() + timedelta(hours=random.randint(8, 12))
                        )
                        
                        # Wind Reportの場合、追加フィールドを設定
                        if report_type == 'WIND':
                            report.new_close_number = random.randint(1, 20)
                            report.upg_close_number = random.randint(1, 15)
                            report.mnp_close_number = random.randint(1, 10)
                            report.tv_close_number = random.randint(1, 8)
                            report.net_close_number = random.randint(1, 12)
                            report.tel_close_number = random.randint(1, 18)
                            report.tos_close_number = random.randint(1, 5)
                            report.save()
                        
                        report_count += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'Generated {report_count} reports')

    def generate_timestamps(self, users, start_date, end_date):
        """勤怠データを生成"""
        timestamp_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # 土日は基本的に勤怠なし（たまにあり）
            if current_date.weekday() < 5 or random.random() < 0.1:
                for user in users:
                    if random.random() < 0.9:  # 90%の確率で出勤
                        # 出勤時刻（8:00-10:00の間でランダム）
                        clock_in_hour = random.randint(8, 10)
                        clock_in_minute = random.randint(0, 59)
                        clock_in_time = datetime.combine(current_date, datetime.min.time().replace(
                            hour=clock_in_hour, minute=clock_in_minute
                        ))
                        
                        Timestamp.objects.create(
                            user=user,
                            status='CLOCK_IN',
                            timestamp=timezone.make_aware(clock_in_time)
                        )
                        timestamp_count += 1
                        
                        # 退勤時刻（17:00-20:00の間でランダム）
                        if random.random() < 0.95:  # 95%の確率で退勤
                            clock_out_hour = random.randint(17, 20)
                            clock_out_minute = random.randint(0, 59)
                            clock_out_time = datetime.combine(current_date, datetime.min.time().replace(
                                hour=clock_out_hour, minute=clock_out_minute
                            ))
                            
                            Timestamp.objects.create(
                                user=user,
                                status='CLOCK_OUT',
                                timestamp=timezone.make_aware(clock_out_time)
                            )
                            timestamp_count += 1
                        
                        # 休憩時間（50%の確率で休憩）
                        if random.random() < 0.5:
                            # 休憩開始（12:00-13:00の間）
                            break_start_hour = random.randint(12, 13)
                            break_start_minute = random.randint(0, 30)
                            break_start_time = datetime.combine(current_date, datetime.min.time().replace(
                                hour=break_start_hour, minute=break_start_minute
                            ))
                            
                            Timestamp.objects.create(
                                user=user,
                                status='BREAK_START',
                                timestamp=timezone.make_aware(break_start_time)
                            )
                            timestamp_count += 1
                            
                            # 休憩終了（30分-1時間後）
                            break_end_time = break_start_time + timedelta(minutes=random.randint(30, 60))
                            Timestamp.objects.create(
                                user=user,
                                status='BREAK_END',
                                timestamp=timezone.make_aware(break_end_time)
                            )
                            timestamp_count += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'Generated {timestamp_count} timestamps')

    def generate_departure_records(self, users, start_date, end_date):
        """出発記録を生成"""
        departure_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # 土日は基本的に出発なし（たまにあり）
            if current_date.weekday() < 5 or random.random() < 0.1:
                for user in users:
                    if random.random() < 0.3:  # 30%の確率で出発記録
                        departure_time = datetime.combine(current_date, datetime.min.time().replace(
                            hour=random.randint(9, 11),
                            minute=random.randint(0, 59)
                        ))
                        
                        DepartureRecord.objects.create(
                            user=user,
                            departure_date=current_date,
                            departure_time=timezone.make_aware(departure_time)
                        )
                        departure_count += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'Generated {departure_count} departure records')
