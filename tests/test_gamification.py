"""GamificationTrackerクラスのユニットテスト"""

import pytest
from pomodoro.gamification import (
    GamificationTracker,
    BadgeType,
    Badge,
    BADGE_INFO,
    calculate_level,
    calculate_xp_for_level,
    calculate_xp_progress,
    calculate_pomodoro_xp,
    calculate_streak,
)


class TestCalculateLevel:
    """calculate_level関数のテスト"""
    
    def test_level_1_at_zero_xp(self):
        assert calculate_level(0) == 1
    
    def test_level_1_at_99_xp(self):
        assert calculate_level(99) == 1
    
    def test_level_2_at_100_xp(self):
        assert calculate_level(100) == 2
    
    def test_level_3_at_250_xp(self):
        assert calculate_level(250) == 3
    
    def test_negative_xp_returns_level_1(self):
        assert calculate_level(-100) == 1
    
    def test_high_xp(self):
        # 高いXPでも正しくレベルが計算される
        level = calculate_level(10000)
        assert level > 10


class TestCalculateXpForLevel:
    """calculate_xp_for_level関数のテスト"""
    
    def test_level_1_requires_0_xp(self):
        assert calculate_xp_for_level(1) == 0
    
    def test_level_2_requires_100_xp(self):
        assert calculate_xp_for_level(2) == 100
    
    def test_level_3_requires_250_xp(self):
        assert calculate_xp_for_level(3) == 250
    
    def test_level_0_returns_0(self):
        assert calculate_xp_for_level(0) == 0


class TestCalculateXpProgress:
    """calculate_xp_progress関数のテスト"""
    
    def test_zero_xp(self):
        result = calculate_xp_progress(0)
        assert result["level"] == 1
        assert result["total_xp"] == 0
        assert result["xp_in_current_level"] == 0
    
    def test_partial_progress(self):
        result = calculate_xp_progress(50)
        assert result["level"] == 1
        assert result["xp_in_current_level"] == 50
        assert result["progress_percent"] == 50.0
    
    def test_exact_level_up(self):
        result = calculate_xp_progress(100)
        assert result["level"] == 2
        assert result["xp_in_current_level"] == 0


class TestCalculatePomodoroXp:
    """calculate_pomodoro_xp関数のテスト"""
    
    def test_25_minutes_no_streak(self):
        xp = calculate_pomodoro_xp(25 * 60, 0)
        assert xp == 25
    
    def test_25_minutes_with_streak(self):
        xp = calculate_pomodoro_xp(25 * 60, 3)
        assert xp == 32  # 25 * 1.3 = 32.5 -> 32
    
    def test_max_streak_bonus(self):
        xp = calculate_pomodoro_xp(25 * 60, 10)  # 10日連続でも最大50%ボーナス
        assert xp == 37  # 25 * 1.5 = 37.5 -> 37


class TestCalculateStreak:
    """calculate_streak関数のテスト"""
    
    def test_empty_dates(self):
        assert calculate_streak([], "2025-11-29") == 0
    
    def test_single_day_today(self):
        assert calculate_streak(["2025-11-29"], "2025-11-29") == 1
    
    def test_single_day_yesterday(self):
        assert calculate_streak(["2025-11-28"], "2025-11-29") == 1
    
    def test_three_consecutive_days(self):
        dates = ["2025-11-27", "2025-11-28", "2025-11-29"]
        assert calculate_streak(dates, "2025-11-29") == 3
    
    def test_gap_breaks_streak(self):
        dates = ["2025-11-25", "2025-11-27", "2025-11-29"]
        assert calculate_streak(dates, "2025-11-29") == 1
    
    def test_old_dates_no_streak(self):
        dates = ["2025-11-20", "2025-11-21"]
        assert calculate_streak(dates, "2025-11-29") == 0
    
    def test_duplicate_dates(self):
        dates = ["2025-11-28", "2025-11-28", "2025-11-29", "2025-11-29"]
        assert calculate_streak(dates, "2025-11-29") == 2


class TestBadge:
    """Badgeデータクラスのテスト"""
    
    def test_badge_info(self):
        badge = Badge(badge_type=BadgeType.FIRST_POMODORO, earned_at="2025-11-29")
        info = badge.info
        
        assert "name" in info
        assert "description" in info
        assert "icon" in info
    
    def test_badge_to_dict(self):
        badge = Badge(badge_type=BadgeType.FIRST_POMODORO, earned_at="2025-11-29")
        result = badge.to_dict()
        
        assert result["type"] == "first_pomodoro"
        assert result["earned_at"] == "2025-11-29"
        assert result["name"] == "初めての一歩"
        assert result["icon"] == "🎯"


class TestGamificationTracker:
    """GamificationTrackerクラスのテスト"""
    
    def test_initial_state(self):
        """初期状態のテスト"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        assert tracker.level == 1
        assert tracker.total_xp == 0
        assert tracker.streak_days == 0
        assert len(tracker.badges) == 0
    
    def test_record_pomodoro_earns_xp(self):
        """ポモドーロ完了でXPが獲得される"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        result = tracker.record_pomodoro(25 * 60)
        
        # ストリーク1日目なので10%ボーナス: 25 * 1.1 = 27
        assert result["xp_earned"] == 27
        assert tracker.total_xp == 27
    
    def test_first_pomodoro_badge(self):
        """初めてのポモドーロでバッジ獲得"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        result = tracker.record_pomodoro(25 * 60)
        
        assert len(result["new_badges"]) == 1
        assert result["new_badges"][0]["type"] == "first_pomodoro"
    
    def test_level_up_with_multiple_pomodoros(self):
        """複数のポモドーロでレベルアップ"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        # 4ポモドーロ = 100 XP = レベル2
        for _ in range(4):
            tracker.record_pomodoro(25 * 60)
        
        assert tracker.level == 2
    
    def test_streak_calculation(self):
        """連続日数の計算"""
        current_date = ["2025-11-27"]
        tracker = GamificationTracker(date_provider=lambda: current_date[0])
        
        # 1日目
        tracker.record_pomodoro(25 * 60)
        assert tracker.streak_days == 1
        
        # 2日目
        current_date[0] = "2025-11-28"
        tracker.record_pomodoro(25 * 60)
        assert tracker.streak_days == 2
        
        # 3日目
        current_date[0] = "2025-11-29"
        tracker.record_pomodoro(25 * 60)
        assert tracker.streak_days == 3
    
    def test_streak_badge_at_3_days(self):
        """3日連続でストリークバッジ獲得"""
        current_date = ["2025-11-27"]
        tracker = GamificationTracker(date_provider=lambda: current_date[0])
        
        tracker.record_pomodoro(25 * 60)
        current_date[0] = "2025-11-28"
        tracker.record_pomodoro(25 * 60)
        current_date[0] = "2025-11-29"
        result = tracker.record_pomodoro(25 * 60)
        
        badge_types = [b["type"] for b in result["new_badges"]]
        assert "streak_3" in badge_types
    
    def test_weekly_stats(self):
        """週間統計の取得"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")  # 土曜日
        
        tracker.record_pomodoro(25 * 60)
        tracker.record_pomodoro(25 * 60)
        
        stats = tracker.get_weekly_stats()
        
        assert "daily_data" in stats
        assert len(stats["daily_data"]) == 7
        assert stats["total_pomodoros"] == 2
    
    def test_monthly_stats(self):
        """月間統計の取得"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        tracker.record_pomodoro(25 * 60)
        
        stats = tracker.get_monthly_stats()
        
        assert stats["month"] == "2025-11"
        assert stats["total_pomodoros"] == 1
        assert stats["active_days"] == 1
    
    def test_xp_progress(self):
        """XP進捗の取得"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        # 2ポモドーロ: 27 + 27 = 54 XP (ストリーク1日で10%ボーナス)
        tracker.record_pomodoro(25 * 60)
        tracker.record_pomodoro(25 * 60)
        
        progress = tracker.get_xp_progress()
        
        assert progress["level"] == 1
        assert progress["total_xp"] == 54
        assert progress["progress_percent"] == 54.0
    
    def test_to_dict(self):
        """辞書形式での取得"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        tracker.record_pomodoro(25 * 60)
        
        result = tracker.to_dict()
        
        assert "level" in result
        assert "total_xp" in result
        assert "xp_progress" in result
        assert "streak_days" in result
        assert "badges" in result
        assert "weekly_stats" in result
        assert "monthly_stats" in result
    
    def test_badge_not_awarded_twice(self):
        """同じバッジは2回獲得されない"""
        tracker = GamificationTracker(date_provider=lambda: "2025-11-29")
        
        result1 = tracker.record_pomodoro(25 * 60)
        result2 = tracker.record_pomodoro(25 * 60)
        
        # 初回のみバッジ獲得
        first_badge_count = len([b for b in result1["new_badges"] if b["type"] == "first_pomodoro"])
        second_badge_count = len([b for b in result2["new_badges"] if b["type"] == "first_pomodoro"])
        
        assert first_badge_count == 1
        assert second_badge_count == 0
    
    def test_streak_bonus_increases_xp(self):
        """ストリークボーナスでXPが増加する"""
        current_date = ["2025-11-27"]
        tracker = GamificationTracker(date_provider=lambda: current_date[0])
        
        # 1日目 (ストリーク1) - 今日のデータがあるのでストリーク1
        result1 = tracker.record_pomodoro(25 * 60)
        
        # 2日目 (ストリーク2)
        current_date[0] = "2025-11-28"
        result2 = tracker.record_pomodoro(25 * 60)
        
        # 3日目 (ストリーク3)
        current_date[0] = "2025-11-29"
        result3 = tracker.record_pomodoro(25 * 60)
        
        # ストリークが増えるとXPも増える
        assert result1["xp_earned"] == 27  # ストリーク1: 25 * 1.1 = 27.5 -> 27
        assert result2["xp_earned"] == 30  # ストリーク2: 25 * 1.2 = 30
        assert result3["xp_earned"] == 32  # ストリーク3: 25 * 1.3 = 32.5 -> 32


class TestBadgeInfo:
    """BADGE_INFO辞書のテスト"""
    
    def test_all_badges_have_info(self):
        """全てのバッジに情報がある"""
        for badge_type in BadgeType:
            assert badge_type in BADGE_INFO
            info = BADGE_INFO[badge_type]
            assert "name" in info
            assert "description" in info
            assert "icon" in info
