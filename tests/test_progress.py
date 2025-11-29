"""ProgressTrackerクラスのユニットテスト"""

import pytest
from pomodoro.progress import (
    ProgressTracker,
    DailyProgress,
    format_duration,
    calculate_focus_percentage
)


class TestFormatDuration:
    """format_duration関数のテスト"""
    
    def test_zero_seconds(self):
        assert format_duration(0) == "0分"
    
    def test_only_minutes(self):
        assert format_duration(30 * 60) == "30分"
    
    def test_one_hour(self):
        assert format_duration(60 * 60) == "1時間0分"
    
    def test_hours_and_minutes(self):
        assert format_duration(90 * 60) == "1時間30分"
    
    def test_multiple_hours(self):
        assert format_duration(2 * 60 * 60 + 15 * 60) == "2時間15分"


class TestCalculateFocusPercentage:
    """calculate_focus_percentage関数のテスト"""
    
    def test_zero_target(self):
        assert calculate_focus_percentage(100, 0) == 0.0
    
    def test_half_complete(self):
        assert calculate_focus_percentage(50, 100) == 0.5
    
    def test_full_complete(self):
        assert calculate_focus_percentage(100, 100) == 1.0
    
    def test_over_complete(self):
        assert calculate_focus_percentage(150, 100) == 1.5


class TestDailyProgress:
    """DailyProgressデータクラスのテスト"""
    
    def test_default_values(self):
        progress = DailyProgress(date="2025-11-29")
        
        assert progress.date == "2025-11-29"
        assert progress.completed_pomodoros == 0
        assert progress.total_focus_seconds == 0
    
    def test_total_focus_minutes(self):
        progress = DailyProgress(
            date="2025-11-29",
            total_focus_seconds=90 * 60  # 90分
        )
        
        assert progress.total_focus_minutes == 90
    
    def test_format_focus_time_minutes_only(self):
        progress = DailyProgress(
            date="2025-11-29",
            total_focus_seconds=45 * 60
        )
        
        assert progress.format_focus_time() == "45分"
    
    def test_format_focus_time_with_hours(self):
        progress = DailyProgress(
            date="2025-11-29",
            total_focus_seconds=100 * 60  # 1時間40分
        )
        
        assert progress.format_focus_time() == "1時間40分"


class TestProgressTracker:
    """ProgressTrackerクラスのテスト"""
    
    def test_initial_state(self):
        """初期状態のテスト"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        
        assert tracker.get_completed_count() == 0
        assert tracker.get_total_focus_seconds() == 0
    
    def test_add_completed_pomodoro(self):
        """ポモドーロ完了の記録"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        
        result = tracker.add_completed_pomodoro(25 * 60)
        
        assert result.completed_pomodoros == 1
        assert result.total_focus_seconds == 25 * 60
        assert tracker.get_completed_count() == 1
    
    def test_add_multiple_pomodoros(self):
        """複数のポモドーロ完了"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        
        tracker.add_completed_pomodoro(25 * 60)
        tracker.add_completed_pomodoro(25 * 60)
        tracker.add_completed_pomodoro(25 * 60)
        
        assert tracker.get_completed_count() == 3
        assert tracker.get_total_focus_seconds() == 75 * 60
    
    def test_get_total_focus_time_formatted(self):
        """集中時間のフォーマット取得"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        
        # 4ポモドーロ = 100分 = 1時間40分
        for _ in range(4):
            tracker.add_completed_pomodoro(25 * 60)
        
        assert tracker.get_total_focus_time_formatted() == "1時間40分"
    
    def test_reset_today(self):
        """今日の進捗リセット"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        
        tracker.add_completed_pomodoro(25 * 60)
        tracker.add_completed_pomodoro(25 * 60)
        
        tracker.reset_today()
        
        assert tracker.get_completed_count() == 0
        assert tracker.get_total_focus_seconds() == 0
    
    def test_to_dict(self):
        """辞書形式での取得"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        tracker.add_completed_pomodoro(25 * 60)
        
        result = tracker.to_dict()
        
        assert result["date"] == "2025-11-29"
        assert result["completed_pomodoros"] == 1
        assert result["total_focus_seconds"] == 25 * 60
        assert result["total_focus_time"] == "25分"
    
    def test_date_change_creates_new_progress(self):
        """日付が変わると新しい進捗が作成される"""
        current_date = ["2025-11-29"]
        tracker = ProgressTracker(date_provider=lambda: current_date[0])
        
        # 1日目
        tracker.add_completed_pomodoro(25 * 60)
        assert tracker.get_completed_count() == 1
        
        # 日付変更
        current_date[0] = "2025-11-30"
        
        # 新しい日は0から
        assert tracker.get_completed_count() == 0
    
    def test_today_progress_property(self):
        """today_progressプロパティのテスト"""
        tracker = ProgressTracker(date_provider=lambda: "2025-11-29")
        
        progress = tracker.today_progress
        
        assert isinstance(progress, DailyProgress)
        assert progress.date == "2025-11-29"
