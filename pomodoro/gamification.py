"""ポモドーロタイマーのゲーミフィケーション機能"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, Callable, List
from enum import Enum


class BadgeType(Enum):
    """バッジの種類"""
    FIRST_POMODORO = "first_pomodoro"          # 初めてのポモドーロ
    STREAK_3 = "streak_3"                       # 3日連続
    STREAK_7 = "streak_7"                       # 7日連続
    STREAK_30 = "streak_30"                     # 30日連続
    WEEKLY_10 = "weekly_10"                     # 週10ポモドーロ
    WEEKLY_25 = "weekly_25"                     # 週25ポモドーロ
    MONTHLY_50 = "monthly_50"                   # 月50ポモドーロ
    MONTHLY_100 = "monthly_100"                 # 月100ポモドーロ
    LEVEL_5 = "level_5"                         # レベル5達成
    LEVEL_10 = "level_10"                       # レベル10達成
    FOCUS_MASTER = "focus_master"               # 累計100時間集中


BADGE_INFO = {
    BadgeType.FIRST_POMODORO: {
        "name": "初めての一歩",
        "description": "初めてのポモドーロを完了",
        "icon": "🎯"
    },
    BadgeType.STREAK_3: {
        "name": "3日連続",
        "description": "3日連続でポモドーロを完了",
        "icon": "🔥"
    },
    BadgeType.STREAK_7: {
        "name": "1週間継続",
        "description": "7日連続でポモドーロを完了",
        "icon": "⭐"
    },
    BadgeType.STREAK_30: {
        "name": "習慣化達成",
        "description": "30日連続でポモドーロを完了",
        "icon": "🏆"
    },
    BadgeType.WEEKLY_10: {
        "name": "週間アクティブ",
        "description": "1週間で10ポモドーロを完了",
        "icon": "📅"
    },
    BadgeType.WEEKLY_25: {
        "name": "週間マスター",
        "description": "1週間で25ポモドーロを完了",
        "icon": "💪"
    },
    BadgeType.MONTHLY_50: {
        "name": "月間アクティブ",
        "description": "1ヶ月で50ポモドーロを完了",
        "icon": "📆"
    },
    BadgeType.MONTHLY_100: {
        "name": "月間マスター",
        "description": "1ヶ月で100ポモドーロを完了",
        "icon": "🌟"
    },
    BadgeType.LEVEL_5: {
        "name": "レベル5達成",
        "description": "レベル5に到達",
        "icon": "🎖️"
    },
    BadgeType.LEVEL_10: {
        "name": "レベル10達成",
        "description": "レベル10に到達",
        "icon": "👑"
    },
    BadgeType.FOCUS_MASTER: {
        "name": "集中マスター",
        "description": "累計100時間の集中を達成",
        "icon": "🧠"
    },
}


@dataclass
class Badge:
    """バッジデータ"""
    badge_type: BadgeType
    earned_at: str  # ISO format date
    
    @property
    def info(self) -> dict:
        """バッジ情報を取得"""
        return BADGE_INFO.get(self.badge_type, {})
    
    def to_dict(self) -> dict:
        """辞書形式で取得"""
        info = self.info
        return {
            "type": self.badge_type.value,
            "name": info.get("name", ""),
            "description": info.get("description", ""),
            "icon": info.get("icon", ""),
            "earned_at": self.earned_at
        }


def calculate_level(xp: int) -> int:
    """XPからレベルを計算（純粋関数）
    
    レベルアップに必要なXPは徐々に増加
    Level 1: 0 XP
    Level 2: 100 XP
    Level 3: 250 XP (100 + 150)
    Level 4: 450 XP (250 + 200)
    ...
    
    Args:
        xp: 経験値
    
    Returns:
        int: レベル（1以上）
    """
    if xp < 0:
        return 1
    
    level = 1
    xp_required = 0
    xp_increment = 100
    
    while xp >= xp_required:
        level += 1
        xp_required += xp_increment
        xp_increment += 50
    
    return level - 1


def calculate_xp_for_level(level: int) -> int:
    """特定レベルに必要な累計XPを計算（純粋関数）
    
    Args:
        level: レベル
    
    Returns:
        int: 必要な累計XP
    """
    if level <= 1:
        return 0
    
    xp_required = 0
    xp_increment = 100
    
    for _ in range(1, level):
        xp_required += xp_increment
        xp_increment += 50
    
    return xp_required


def calculate_xp_progress(xp: int) -> dict:
    """現在のXPから進捗情報を計算（純粋関数）
    
    Args:
        xp: 現在の経験値
    
    Returns:
        dict: 進捗情報
    """
    current_level = calculate_level(xp)
    current_level_xp = calculate_xp_for_level(current_level)
    next_level_xp = calculate_xp_for_level(current_level + 1)
    xp_in_current_level = xp - current_level_xp
    xp_needed_for_next = next_level_xp - current_level_xp
    
    return {
        "level": current_level,
        "total_xp": xp,
        "xp_in_current_level": xp_in_current_level,
        "xp_needed_for_next": xp_needed_for_next,
        "progress_percent": round((xp_in_current_level / xp_needed_for_next) * 100, 1) if xp_needed_for_next > 0 else 0
    }


def calculate_pomodoro_xp(focus_seconds: int, streak_days: int = 0) -> int:
    """ポモドーロ完了時の獲得XPを計算（純粋関数）
    
    基本XP: 集中時間（分）
    ストリークボーナス: +10% per streak day (max 50%)
    
    Args:
        focus_seconds: 集中時間（秒）
        streak_days: 連続日数
    
    Returns:
        int: 獲得XP
    """
    base_xp = focus_seconds // 60  # 1分 = 1XP
    streak_bonus = min(streak_days * 0.1, 0.5)  # 最大50%ボーナス
    total_xp = int(base_xp * (1 + streak_bonus))
    return total_xp


def calculate_streak(dates: List[str], today: str) -> int:
    """連続日数を計算（純粋関数）
    
    Args:
        dates: ポモドーロを完了した日付のリスト（YYYY-MM-DD形式）
        today: 今日の日付（YYYY-MM-DD形式）
    
    Returns:
        int: 連続日数
    """
    if not dates:
        return 0
    
    # 日付をソートして重複を除去
    unique_dates = sorted(set(dates), reverse=True)
    
    if not unique_dates:
        return 0
    
    # 今日または昨日から始まっているかチェック
    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    most_recent = datetime.strptime(unique_dates[0], "%Y-%m-%d").date()
    
    # 今日または昨日でなければストリークは0
    if (today_date - most_recent).days > 1:
        return 0
    
    # 連続日数をカウント
    streak = 1
    for i in range(len(unique_dates) - 1):
        current = datetime.strptime(unique_dates[i], "%Y-%m-%d").date()
        prev = datetime.strptime(unique_dates[i + 1], "%Y-%m-%d").date()
        
        if (current - prev).days == 1:
            streak += 1
        else:
            break
    
    return streak


@dataclass
class DailyStats:
    """1日の統計データ"""
    date: str  # YYYY-MM-DD形式
    completed_pomodoros: int = 0
    total_focus_seconds: int = 0
    xp_earned: int = 0


class GamificationTracker:
    """ゲーミフィケーション管理クラス
    
    XP、レベル、バッジ、ストリークを管理
    """
    
    def __init__(
        self,
        date_provider: Optional[Callable[[], str]] = None
    ):
        """
        Args:
            date_provider: 今日の日付を返す関数（テスト時にモック可能）
        """
        self._date_provider = date_provider or (lambda: date.today().isoformat())
        self._total_xp = 0
        self._total_focus_seconds = 0
        self._badges: List[Badge] = []
        self._daily_stats: dict[str, DailyStats] = {}
    
    def _get_today(self) -> str:
        """今日の日付を取得"""
        return self._date_provider()
    
    @property
    def level(self) -> int:
        """現在のレベルを取得"""
        return calculate_level(self._total_xp)
    
    @property
    def total_xp(self) -> int:
        """累計XPを取得"""
        return self._total_xp
    
    @property
    def streak_days(self) -> int:
        """連続日数を取得"""
        dates = list(self._daily_stats.keys())
        return calculate_streak(dates, self._get_today())
    
    @property
    def badges(self) -> List[Badge]:
        """獲得したバッジのリストを取得"""
        return self._badges.copy()
    
    def _get_or_create_daily_stats(self, date_str: str) -> DailyStats:
        """指定日の統計を取得または作成"""
        if date_str not in self._daily_stats:
            self._daily_stats[date_str] = DailyStats(date=date_str)
        return self._daily_stats[date_str]
    
    def record_pomodoro(self, focus_seconds: int) -> dict:
        """ポモドーロ完了を記録
        
        Args:
            focus_seconds: 集中時間（秒）
        
        Returns:
            dict: 獲得したXPと新しいバッジ
        """
        today = self._get_today()
        stats = self._get_or_create_daily_stats(today)
        
        # ストリークを計算（記録前）
        streak = self.streak_days
        
        # XP計算と加算
        xp_earned = calculate_pomodoro_xp(focus_seconds, streak)
        self._total_xp += xp_earned
        self._total_focus_seconds += focus_seconds
        
        # 日別統計を更新
        stats.completed_pomodoros += 1
        stats.total_focus_seconds += focus_seconds
        stats.xp_earned += xp_earned
        
        # バッジチェック
        new_badges = self._check_badges()
        
        return {
            "xp_earned": xp_earned,
            "total_xp": self._total_xp,
            "level": self.level,
            "new_badges": [b.to_dict() for b in new_badges],
            "streak_days": self.streak_days
        }
    
    def _has_badge(self, badge_type: BadgeType) -> bool:
        """指定バッジを所持しているか"""
        return any(b.badge_type == badge_type for b in self._badges)
    
    def _award_badge(self, badge_type: BadgeType) -> Badge:
        """バッジを付与"""
        badge = Badge(badge_type=badge_type, earned_at=self._get_today())
        self._badges.append(badge)
        return badge
    
    def _check_badges(self) -> List[Badge]:
        """バッジ獲得条件をチェックし、新規バッジを付与"""
        new_badges = []
        today = self._get_today()
        
        # 初めてのポモドーロ
        if not self._has_badge(BadgeType.FIRST_POMODORO):
            total_pomodoros = sum(s.completed_pomodoros for s in self._daily_stats.values())
            if total_pomodoros >= 1:
                new_badges.append(self._award_badge(BadgeType.FIRST_POMODORO))
        
        # ストリークバッジ
        streak = self.streak_days
        if streak >= 3 and not self._has_badge(BadgeType.STREAK_3):
            new_badges.append(self._award_badge(BadgeType.STREAK_3))
        if streak >= 7 and not self._has_badge(BadgeType.STREAK_7):
            new_badges.append(self._award_badge(BadgeType.STREAK_7))
        if streak >= 30 and not self._has_badge(BadgeType.STREAK_30):
            new_badges.append(self._award_badge(BadgeType.STREAK_30))
        
        # 週間バッジ
        weekly_count = self._get_weekly_pomodoros()
        if weekly_count >= 10 and not self._has_badge(BadgeType.WEEKLY_10):
            new_badges.append(self._award_badge(BadgeType.WEEKLY_10))
        if weekly_count >= 25 and not self._has_badge(BadgeType.WEEKLY_25):
            new_badges.append(self._award_badge(BadgeType.WEEKLY_25))
        
        # 月間バッジ
        monthly_count = self._get_monthly_pomodoros()
        if monthly_count >= 50 and not self._has_badge(BadgeType.MONTHLY_50):
            new_badges.append(self._award_badge(BadgeType.MONTHLY_50))
        if monthly_count >= 100 and not self._has_badge(BadgeType.MONTHLY_100):
            new_badges.append(self._award_badge(BadgeType.MONTHLY_100))
        
        # レベルバッジ
        level = self.level
        if level >= 5 and not self._has_badge(BadgeType.LEVEL_5):
            new_badges.append(self._award_badge(BadgeType.LEVEL_5))
        if level >= 10 and not self._has_badge(BadgeType.LEVEL_10):
            new_badges.append(self._award_badge(BadgeType.LEVEL_10))
        
        # 集中マスター（100時間 = 360000秒）
        if self._total_focus_seconds >= 360000 and not self._has_badge(BadgeType.FOCUS_MASTER):
            new_badges.append(self._award_badge(BadgeType.FOCUS_MASTER))
        
        return new_badges
    
    def _get_weekly_pomodoros(self) -> int:
        """今週のポモドーロ数を取得"""
        today = datetime.strptime(self._get_today(), "%Y-%m-%d").date()
        week_start = today - timedelta(days=today.weekday())
        
        count = 0
        for date_str, stats in self._daily_stats.items():
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            if d >= week_start and d <= today:
                count += stats.completed_pomodoros
        
        return count
    
    def _get_monthly_pomodoros(self) -> int:
        """今月のポモドーロ数を取得"""
        today = datetime.strptime(self._get_today(), "%Y-%m-%d").date()
        month_start = today.replace(day=1)
        
        count = 0
        for date_str, stats in self._daily_stats.items():
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            if d >= month_start and d <= today:
                count += stats.completed_pomodoros
        
        return count
    
    def get_weekly_stats(self) -> dict:
        """週間統計を取得"""
        today = datetime.strptime(self._get_today(), "%Y-%m-%d").date()
        week_start = today - timedelta(days=today.weekday())
        
        daily_data = []
        total_pomodoros = 0
        total_focus_seconds = 0
        
        for i in range(7):
            d = week_start + timedelta(days=i)
            date_str = d.isoformat()
            stats = self._daily_stats.get(date_str, DailyStats(date=date_str))
            
            daily_data.append({
                "date": date_str,
                "day_name": ["月", "火", "水", "木", "金", "土", "日"][i],
                "completed_pomodoros": stats.completed_pomodoros,
                "focus_minutes": stats.total_focus_seconds // 60
            })
            
            if d <= today:
                total_pomodoros += stats.completed_pomodoros
                total_focus_seconds += stats.total_focus_seconds
        
        # 平均計算
        days_passed = today.weekday() + 1
        avg_pomodoros = round(total_pomodoros / days_passed, 1) if days_passed > 0 else 0
        avg_focus_minutes = round((total_focus_seconds / 60) / days_passed, 1) if days_passed > 0 else 0
        
        return {
            "week_start": week_start.isoformat(),
            "daily_data": daily_data,
            "total_pomodoros": total_pomodoros,
            "total_focus_minutes": total_focus_seconds // 60,
            "avg_pomodoros_per_day": avg_pomodoros,
            "avg_focus_minutes_per_day": avg_focus_minutes
        }
    
    def get_monthly_stats(self) -> dict:
        """月間統計を取得"""
        today = datetime.strptime(self._get_today(), "%Y-%m-%d").date()
        month_start = today.replace(day=1)
        
        # 月の日数を計算
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        days_in_month = (next_month - month_start).days
        
        total_pomodoros = 0
        total_focus_seconds = 0
        active_days = 0
        
        for date_str, stats in self._daily_stats.items():
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            if d >= month_start and d <= today:
                total_pomodoros += stats.completed_pomodoros
                total_focus_seconds += stats.total_focus_seconds
                if stats.completed_pomodoros > 0:
                    active_days += 1
        
        days_passed = (today - month_start).days + 1
        
        return {
            "month": today.strftime("%Y-%m"),
            "total_pomodoros": total_pomodoros,
            "total_focus_minutes": total_focus_seconds // 60,
            "active_days": active_days,
            "days_passed": days_passed,
            "days_in_month": days_in_month,
            "completion_rate": round((active_days / days_passed) * 100, 1) if days_passed > 0 else 0
        }
    
    def get_xp_progress(self) -> dict:
        """XP進捗を取得"""
        return calculate_xp_progress(self._total_xp)
    
    def to_dict(self) -> dict:
        """全データを辞書形式で取得（API用）"""
        return {
            "level": self.level,
            "total_xp": self._total_xp,
            "xp_progress": self.get_xp_progress(),
            "streak_days": self.streak_days,
            "badges": [b.to_dict() for b in self._badges],
            "total_focus_seconds": self._total_focus_seconds,
            "weekly_stats": self.get_weekly_stats(),
            "monthly_stats": self.get_monthly_stats()
        }
