# ポモドーロタイマー Webアプリケーション アーキテクチャ設計書

## 概要

Flask + HTML/CSS/JavaScript を使用したポモドーロタイマーWebアプリケーションの設計書です。
ユニットテストのしやすさを重視し、ビジネスロジックをフロントエンド/バックエンドから分離した3層アーキテクチャを採用します。

## プロジェクト構造

```
/workspaces/2025-Github-Copilot-Workshop-Python/
├── app.py                      # Flaskアプリ（ルーティングのみ）
├── pomodoro/                   # ビジネスロジック層（テスト対象）
│   ├── __init__.py
│   ├── timer.py                # タイマーロジック（状態管理）
│   └── progress.py             # 進捗管理（完了数・集中時間計算）
├── templates/
│   └── index.html              # ポモドーロタイマーUI
├── static/
│   ├── css/
│   │   └── style.css           # 円形プログレスバー、レイアウト
│   └── js/
│       └── timer.js            # タイマーロジック、進捗管理
├── tests/                      # テストディレクトリ
│   ├── __init__.py
│   ├── test_timer.py           # タイマーロジックのテスト
│   ├── test_progress.py        # 進捗管理のテスト
│   └── test_app.py             # Flask APIのテスト
├── requirements.txt            # Python依存関係
└── pytest.ini                  # pytestの設定
```

## 機能要件

UIモックに基づく主要機能：

| 機能 | 説明 |
|------|------|
| タイマー表示 | 25:00分のカウントダウン表示 |
| 円形プログレスバー | 残り時間を視覚的に表示 |
| 状態表示 | 「作業中」「休憩中」などの状態を表示 |
| 開始/リセットボタン | タイマーの制御 |
| 今日の進捗 | 完了数と集中時間の表示 |

## アーキテクチャ詳細

### 1. Flask層 (`app.py`)

- **責務**: ルーティングとビジネスロジック呼び出しのみ
- **エンドポイント**:
  - `GET /` - index.htmlを配信
  - `GET /api/status` - タイマー状態取得（オプション）
  - `POST /api/progress` - 進捗データ保存（オプション）

### 2. ビジネスロジック層 (`pomodoro/`)

#### `timer.py` - PomodoroTimerクラス

- **責務**: タイマーの状態管理
- **状態**: WORK（作業中）/ SHORT_BREAK（短い休憩）/ LONG_BREAK（長い休憩）
- **メソッド**: start(), stop(), reset(), get_remaining_time()
- **テスト容易性**: 時間取得関数を依存性注入可能にする

#### `progress.py` - ProgressTrackerクラス

- **責務**: 進捗データの管理
- **機能**: 完了数カウント、集中時間の累積計算
- **テスト容易性**: 純粋関数・メソッドとして実装

### 3. フロントエンド層 (`static/`, `templates/`)

#### `index.html`

- タイマー表示、状態表示、ボタン、進捗セクションのレイアウト

#### `style.css`

- 円形プログレスバー（SVG または CSS conic-gradient）
- ボタンスタイル
- カード風UIデザイン

#### `timer.js`

- カウントダウンロジック
- 開始/リセット操作
- 状態管理（作業中/休憩中）
- 進捗データのlocalStorage保存
- UIとロジックを分離（計算関数を純粋関数として切り出し）

## テスト設計

### テスト容易性のための設計原則

| 原則 | 適用箇所 |
|------|---------|
| **依存性注入** | `PomodoroTimer` に時間取得関数を注入可能に（`time.time` をモック可能） |
| **純粋関数** | 時間フォーマット、進捗計算などを副作用なしの関数として実装 |
| **状態と振る舞いの分離** | タイマー状態はデータクラス、操作は別メソッド |
| **Flask test client** | `app.test_client()` でAPI統合テスト |

### テストファイル構成

| ファイル | テスト対象 |
|----------|-----------|
| `test_timer.py` | PomodoroTimerクラスの状態遷移、時間計算 |
| `test_progress.py` | ProgressTrackerクラスの完了数・時間計算 |
| `test_app.py` | Flask APIエンドポイントの統合テスト |

## 技術スタック

- **バックエンド**: Flask (Python 3.11)
- **フロントエンド**: HTML5, CSS3, JavaScript (Vanilla)
- **テスト**: pytest, pytest-cov
- **データ永続化**: localStorage（ブラウザ側）

## 今後の検討事項

1. **進捗データの永続化**: localStorageで十分か、Flask + SQLiteでサーバー側に保存すべきか
2. **休憩タイマー機能**: 作業25分→短い休憩5分→長い休憩15分のサイクル実装
3. **通知機能**: タイマー終了時のブラウザ通知（Notification API）や音声アラート
4. **フロントエンドテスト**: Jest導入によるJavaScriptテストの検討
