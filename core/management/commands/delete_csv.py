import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.models import Q
from core.models import Carrier, Report


class Command(BaseCommand):
    help = '指定CSVに該当するデータを削除します（対象: reports）'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='削除対象のCSVファイルパス')
        parser.add_argument('model_type', type=str, choices=['reports'], help='削除するモデルの種類（現状reportsのみ）')
        parser.add_argument('--encoding', type=str, default='utf-8', help='CSVファイルのエンコーディング')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        model_type = options['model_type']
        encoding = options['encoding']

        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                if model_type == 'reports':
                    deleted = self.delete_reports(reader)
                    self.stdout.write(self.style.SUCCESS(f'削除完了: {deleted} 件のReportを削除しました'))
        except FileNotFoundError:
            raise CommandError(f'ファイルが見つかりません: {csv_file}')
        except Exception as e:
            raise CommandError(f'削除エラー: {str(e)}')

    def _parse_int_nullable(self, value):
        if value is None:
            return None
        s = str(value).strip()
        if s == '':
            return None
        return int(s)

    def delete_reports(self, reader):
        """
        import_csv.import_reports と同じ2形式を想定し、
        行ごとに一意性の高い条件で Report を削除します。
        既存形式: user_name, carrier(数値ID), work_date, close_number, swing_number, ...
        新形式: username, carrier_name, report_type, work_date, close_number, swing_number, ...
        """
        carrier_mapping = {
            '1': 'au',
            '2': 'SB',
            '3': 'J:COM',
            '4': 'その他',
        }

        total_deleted = 0

        for row in reader:
            try:
                # 既存形式
                if 'user_name' in row and 'carrier' in row:
                    username = row['user_name']
                    carrier_id = str(row['carrier'])
                    carrier_name = carrier_mapping.get(carrier_id, 'ドコモ')

                    # 必須キー
                    work_date = datetime.strptime(row['work_date'], '%Y-%m-%d').date()
                    close_number = int(row['close_number'])
                    swing_number = int(row['swing_number'])

                    user_q = Q(user__username=username)
                    carrier_q = Q(carrier__carrier_name=carrier_name)
                    date_q = Q(work_date=work_date)
                    base_q = user_q & carrier_q & date_q & Q(close_number=close_number) & Q(swing_number=swing_number)

                    # オプション項目（null許容）
                    new_q = self._optional_q('new_close_number', row, 'new_close_number')
                    upg_q = self._optional_q('upg_close_number', row, 'upg_close_number')
                    mnp_q = self._optional_q('mnp_close_number', row, 'mnp_close_number')
                    tv_q = self._optional_q('tv_close_number', row, 'tv_close_number')
                    net_q = self._optional_q('net_close_number', row, 'net_close_number')
                    tel_q = self._optional_q('tel_close_number', row, 'tel_close_number')
                    tos_q = self._optional_q('tos_close_number', row, 'tos_close_num')

                    qs = Report.objects.filter(base_q & new_q & upg_q & mnp_q & tv_q & net_q & tel_q & tos_q)

                # 新形式
                else:
                    username = row['username']
                    carrier_name = row['carrier_name']
                    work_date = datetime.strptime(row['work_date'], '%Y-%m-%d').date()
                    close_number = int(row['close_number'])
                    swing_number = int(row['swing_number'])

                    base_q = (
                        Q(user__username=username)
                        & Q(carrier__carrier_name=carrier_name)
                        & Q(work_date=work_date)
                        & Q(close_number=close_number)
                        & Q(swing_number=swing_number)
                    )

                    # report_type は省略されることがあるため、存在時のみ一致させる
                    if 'report_type' in row and row['report_type']:
                        base_q &= Q(report_type=row['report_type'])

                    new_q = self._optional_q('new_close_number', row, 'new_close_number')
                    upg_q = self._optional_q('upg_close_number', row, 'upg_close_number')
                    mnp_q = self._optional_q('mnp_close_number', row, 'mnp_close_number')
                    tv_q = self._optional_q('tv_close_number', row, 'tv_close_number')
                    net_q = self._optional_q('net_close_number', row, 'net_close_number')
                    tel_q = self._optional_q('tel_close_number', row, 'tel_close_number')
                    tos_q = self._optional_q('tos_close_number', row, 'tos_close_number')

                    qs = Report.objects.filter(base_q & new_q & upg_q & mnp_q & tv_q & net_q & tel_q & tos_q)

                deleted_count, _ = qs.delete()
                total_deleted += deleted_count
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'削除エラー: {str(e)} - Row: {row}'))

        return total_deleted

    def _optional_q(self, field_name, row, row_key):
        """
        可変項目の一致条件を返す。CSVに値が空/欠損なら isnull=True で一致させる。
        値がある場合は等価一致。
        """
        if row_key not in row:
            # CSV側に列がない場合は条件に含めない（緩める）
            return Q()
        value = self._parse_int_nullable(row.get(row_key))
        if value is None:
            return Q(**{f'{field_name}__isnull': True})
        return Q(**{field_name: value})


