# CSVインポート機能の使用方法

このアプリケーションでは、CSVファイルからデータをインポートする機能を提供しています。

## 方法1: Django管理コマンドを使用（推奨）

### 基本的な使用方法

```bash
python manage.py import_csv <CSVファイルパス> <モデルタイプ> [--encoding <エンコーディング>]
```

### モデルタイプ

- `users`: ユーザー
- `carriers`: キャリア
- `reports`: レポート
- `timestamps`: 勤怠記録
- `departures`: 出発記録

### 使用例

```bash
# ユーザーをインポート
python manage.py import_csv sample_data/users.csv users

# キャリアをインポート
python manage.py import_csv sample_data/carriers.csv carriers

# レポートをインポート
python manage.py import_csv sample_data/reports.csv reports

# 勤怠記録をインポート
python manage.py import_csv sample_data/timestamps.csv timestamps

# 出発記録をインポート
python manage.py import_csv sample_data/departures.csv departures

# エンコーディングを指定（Shift_JISなど）
python manage.py import_csv data.csv users --encoding shift_jis
```

## 方法2: Django管理画面を使用

1. Django管理画面にログイン: http://localhost:8000/admin/
2. 各モデルの管理画面に移動
3. "Import CSV"ボタンをクリック
4. CSVファイルを選択してアップロード

## CSVファイルの形式

### 1. ユーザー (users.csv)
```csv
username,email,first_name,last_name,password,is_staff
user01,user01@example.com,太郎,田中,password123,false
```

### 2. キャリア (carriers.csv)
```csv
carrier_name
ドコモ
au
ソフトバンク
```

### 3. レポート (reports.csv)
```csv
username,carrier_name,report_type,work_date,close_number,swing_number,new_close_number,upg_close_number,mnp_close_number,tv_close_number,net_close_number,tel_close_number,tos_close_number
user01,ドコモ,WIND,2025-09-28,5,10,2,1,1,0,1,0,0
```

### 4. 勤怠記録 (timestamps.csv)
```csv
username,status,timestamp
user01,CLOCK_IN,2025-09-28 09:00:00
user01,CLOCK_OUT,2025-09-28 18:00:00
```

**ステータス値:**
- `CLOCK_IN`: 出勤
- `CLOCK_OUT`: 退勤
- `BREAK_START`: 休憩開始
- `BREAK_END`: 休憩終了

### 5. 出発記録 (departures.csv)
```csv
username,departure_date
user01,2025-09-28
```

## 重要な注意事項

1. **順序**: データの依存関係により、以下の順序でインポートしてください:
   1. users (ユーザー)
   2. carriers (キャリア)
   3. reports (レポート)
   4. timestamps (勤怠記録)
   5. departures (出発記録)

2. **エンコーディング**: 
   - デフォルトはUTF-8です
   - 日本語のCSVファイルがShift_JISの場合は `--encoding shift_jis` を指定

3. **日付形式**:
   - 日付: `YYYY-MM-DD` (例: 2025-09-28)
   - 日時: `YYYY-MM-DD HH:MM:SS` (例: 2025-09-28 09:00:00)

4. **必須フィールド**:
   - ユーザー: `username` は必須
   - レポート: `username`, `carrier_name`, `work_date`, `close_number`, `swing_number` は必須
   - 勤怠記録: `username`, `status`, `timestamp` は必須

5. **エラーハンドリング**:
   - 存在しないユーザーやキャリアを参照している場合はエラーになります
   - 重複データは基本的にスキップされます（ユーザー、キャリア、出発記録）

## サンプルデータ

`sample_data/` ディレクトリにサンプルCSVファイルが用意されています:
- `users.csv`: サンプルユーザー
- `carriers.csv`: サンプルキャリア
- `reports.csv`: サンプルレポート
- `timestamps.csv`: サンプル勤怠記録
- `departures.csv`: サンプル出発記録

## テストインポート

サンプルデータを使ってテストインポートを実行:

```bash
cd winddev
python manage.py import_csv sample_data/users.csv users
python manage.py import_csv sample_data/carriers.csv carriers
python manage.py import_csv sample_data/reports.csv reports
python manage.py import_csv sample_data/timestamps.csv timestamps
python manage.py import_csv sample_data/departures.csv departures
```
