"""Flask APIのユニットテスト"""

import pytest
import json
from app import app


@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """/ ルートのテスト"""
    
    def test_index_returns_200(self, client):
        """メインページが200を返すこと"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_returns_html(self, client):
        """メインページがHTMLを返すこと"""
        response = client.get('/')
        assert b'<!DOCTYPE html>' in response.data
        assert 'text/html' in response.content_type
    
    def test_index_contains_timer_elements(self, client):
        """メインページにタイマー要素が含まれること"""
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        assert 'ポモドーロタイマー' in html
        assert 'timerDisplay' in html
        assert 'startBtn' in html
        assert 'resetBtn' in html
    
    def test_index_contains_settings_section(self, client):
        """メインページに設定セクションが含まれること"""
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # 設定セクションの存在確認
        assert 'settingsSection' in html
        assert 'settingsHeader' in html
        assert 'settingsContent' in html
        
        # 作業時間設定オプション
        assert 'workDurationOptions' in html
        assert 'data-value="15"' in html
        assert 'data-value="25"' in html
        assert 'data-value="35"' in html
        assert 'data-value="45"' in html
        
        # 休憩時間設定オプション
        assert 'shortBreakOptions' in html
        assert 'data-value="5"' in html
        assert 'data-value="10"' in html
        
        # テーマ設定オプション
        assert 'themeOptions' in html
        assert 'data-value="light"' in html
        assert 'data-value="dark"' in html
        assert 'data-value="focus"' in html
        
        # サウンド設定
        assert 'soundStart' in html
        assert 'soundEnd' in html
        assert 'soundTick' in html


class TestProgressAPI:
    """進捗API のテスト"""
    
    def test_get_progress(self, client):
        """GET /api/progress が進捗データを返すこと"""
        response = client.get('/api/progress')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'date' in data
        assert 'completed_pomodoros' in data
        assert 'total_focus_seconds' in data
        assert 'total_focus_time' in data
    
    def test_complete_pomodoro(self, client):
        """POST /api/progress/complete がポモドーロを記録すること"""
        response = client.post(
            '/api/progress/complete',
            data=json.dumps({'focus_seconds': 25 * 60}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'progress' in data
        assert data['progress']['completed_pomodoros'] >= 1
    
    def test_complete_pomodoro_returns_gamification(self, client):
        """POST /api/progress/complete がゲーミフィケーションデータも返すこと"""
        response = client.post(
            '/api/progress/complete',
            data=json.dumps({'focus_seconds': 25 * 60}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'gamification' in data
        assert 'xp_earned' in data['gamification']
        assert 'level' in data['gamification']
        assert 'streak_days' in data['gamification']
    
    def test_complete_pomodoro_default_duration(self, client):
        """POST /api/progress/complete がデフォルトで25分を使用すること"""
        response = client.post(
            '/api/progress/complete',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
    
    def test_reset_progress(self, client):
        """POST /api/progress/reset が進捗をリセットすること"""
        # まず完了を記録
        client.post(
            '/api/progress/complete',
            data=json.dumps({'focus_seconds': 25 * 60}),
            content_type='application/json'
        )
        
        # リセット
        response = client.post('/api/progress/reset')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # 進捗が0になっていることを確認
        response = client.get('/api/progress')
        data = json.loads(response.data)
        assert data['completed_pomodoros'] == 0


class TestGamificationAPI:
    """ゲーミフィケーションAPI のテスト"""
    
    def test_get_gamification(self, client):
        """GET /api/gamification がゲーミフィケーションデータを返すこと"""
        response = client.get('/api/gamification')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'level' in data
        assert 'total_xp' in data
        assert 'xp_progress' in data
        assert 'streak_days' in data
        assert 'badges' in data
        assert 'weekly_stats' in data
        assert 'monthly_stats' in data
    
    def test_get_weekly_stats(self, client):
        """GET /api/gamification/weekly が週間統計を返すこと"""
        response = client.get('/api/gamification/weekly')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'week_start' in data
        assert 'daily_data' in data
        assert 'total_pomodoros' in data
        assert 'total_focus_minutes' in data
        assert 'avg_pomodoros_per_day' in data
    
    def test_get_monthly_stats(self, client):
        """GET /api/gamification/monthly が月間統計を返すこと"""
        response = client.get('/api/gamification/monthly')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'month' in data
        assert 'total_pomodoros' in data
        assert 'total_focus_minutes' in data
        assert 'active_days' in data
        assert 'completion_rate' in data


class TestAPIContentType:
    """API レスポンスのContent-Typeテスト"""
    
    def test_progress_returns_json(self, client):
        """APIがJSONを返すこと"""
        response = client.get('/api/progress')
        assert 'application/json' in response.content_type
    
    def test_complete_returns_json(self, client):
        """完了APIがJSONを返すこと"""
        response = client.post(
            '/api/progress/complete',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert 'application/json' in response.content_type
    
    def test_gamification_returns_json(self, client):
        """ゲーミフィケーションAPIがJSONを返すこと"""
        response = client.get('/api/gamification')
        assert 'application/json' in response.content_type
