"""ポモドーロタイマーの進捗管理"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Callable
import time


@dataclass
class DailyProgress:
    """1日の進捗データ"""
    date: str  # YYYY-MM-DD形式
    completed_pomodoros: int = 0
    total_focus_seconds: int = 0
    
    @property
    def total_focus_minutes(self) -> int:
        """集中時間（分）を取得"""
        return self.total_focus_seconds // 60
    
    def format_focus_time(self) -> str:
        """集中時間を「X時間Y分」形式でフォーマット"""
        return format_duration(self.total_focus_seconds)


class ProgressTracker:
    """進捗管理クラス
    
    完了したポモドーロ数と集中時間を追跡する。
    テスト容易性のため、日付取得関数を依存性注入可能にしている。
    
    Attributes:
        today_progress: 今日の進捗データ
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
        self._progress_data: dict[str, DailyProgress] = {}
    
    def _get_today(self) -> str:
        """今日の日付を取得"""
        return self._date_provider()
    
    @property
    def today_progress(self) -> DailyProgress:
        """今日の進捗を取得"""
        today = self._get_today()
        if today not in self._progress_data:
            self._progress_data[today] = DailyProgress(date=today)
        return self._progress_data[today]
    
    def add_completed_pomodoro(self, focus_seconds: int) -> DailyProgress:
        """ポモドーロ完了を記録
        
        Args:
            focus_seconds: 集中した時間（秒）
        
        Returns:
            DailyProgress: 更新後の今日の進捗
        """
        progress = self.today_progress
        progress.completed_pomodoros += 1
        progress.total_focus_seconds += focus_seconds
        return progress
    
    def get_completed_count(self) -> int:
        """今日の完了ポモドーロ数を取得"""
        return self.today_progress.completed_pomodoros
    
    def get_total_focus_seconds(self) -> int:
        """今日の総集中時間（秒）を取得"""
        return self.today_progress.total_focus_seconds
    
    def get_total_focus_time_formatted(self) -> str:
        """今日の総集中時間をフォーマットして取得"""
        return self.today_progress.format_focus_time()
    
    def reset_today(self) -> None:
        """今日の進捗をリセット"""
        today = self._get_today()
        self._progress_data[today] = DailyProgress(date=today)
    
    def to_dict(self) -> dict:
        """進捗データを辞書形式で取得（API用）"""
        progress = self.today_progress
        return {
            "date": progress.date,
            "completed_pomodoros": progress.completed_pomodoros,
            "total_focus_seconds": progress.total_focus_seconds,
            "total_focus_time": progress.format_focus_time()
        }


def format_duration(seconds: int) -> str:
    """秒数を「X時間Y分」形式にフォーマット（純粋関数）
    
    Args:
        seconds: 秒数
    
    Returns:
        str: フォーマットされた時間文字列
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}時間{minutes}分"
    else:
        return f"{minutes}分"


def calculate_focus_percentage(focus_seconds: int, target_seconds: int) -> float:
    """目標に対する集中時間の達成率を計算（純粋関数）
    
    Args:
        focus_seconds: 実際の集中時間（秒）
        target_seconds: 目標時間（秒）
    
    Returns:
        float: 達成率（0.0〜1.0、1.0を超える場合もある）
    """
    if target_seconds <= 0:
        return 0.0
    return focus_seconds / target_seconds
