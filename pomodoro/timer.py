"""ポモドーロタイマーのタイマーロジック"""

import time
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional


class TimerState(Enum):
    """タイマーの状態"""
    IDLE = "idle"
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass
class TimerConfig:
    """タイマーの設定"""
    work_duration: int = 25 * 60  # 25分（秒）
    short_break_duration: int = 5 * 60  # 5分（秒）
    long_break_duration: int = 15 * 60  # 15分（秒）
    pomodoros_until_long_break: int = 4  # 長い休憩までのポモドーロ数


class PomodoroTimer:
    """ポモドーロタイマークラス
    
    タイマーの状態管理を行う。
    テスト容易性のため、時間取得関数を依存性注入可能にしている。
    
    Attributes:
        config: タイマーの設定
        state: 現在の状態
        remaining_seconds: 残り時間（秒）
    """
    
    def __init__(
        self,
        config: Optional[TimerConfig] = None,
        time_provider: Callable[[], float] = time.time
    ):
        """
        Args:
            config: タイマーの設定（省略時はデフォルト値）
            time_provider: 現在時刻を返す関数（テスト時にモック可能）
        """
        self.config = config or TimerConfig()
        self._time_provider = time_provider
        self._state = TimerState.IDLE
        self._remaining_seconds = self.config.work_duration
        self._start_time: Optional[float] = None
        self._paused_remaining: Optional[int] = None
        self._completed_pomodoros = 0
    
    @property
    def state(self) -> TimerState:
        """現在の状態を取得"""
        return self._state
    
    @property
    def remaining_seconds(self) -> int:
        """残り時間（秒）を取得"""
        if self._start_time is not None:
            elapsed = self._time_provider() - self._start_time
            remaining = self._paused_remaining - int(elapsed)
            return max(0, remaining)
        return self._remaining_seconds
    
    @property
    def completed_pomodoros(self) -> int:
        """完了したポモドーロ数を取得"""
        return self._completed_pomodoros
    
    def start(self) -> bool:
        """タイマーを開始
        
        Returns:
            bool: 開始に成功した場合True
        """
        if self._start_time is not None:
            return False  # すでに実行中
        
        if self._state == TimerState.IDLE:
            self._state = TimerState.WORK
        
        self._paused_remaining = self._remaining_seconds
        self._start_time = self._time_provider()
        return True
    
    def stop(self) -> bool:
        """タイマーを一時停止
        
        Returns:
            bool: 停止に成功した場合True
        """
        if self._start_time is None:
            return False  # 実行中でない
        
        self._remaining_seconds = self.remaining_seconds
        self._start_time = None
        self._paused_remaining = None
        return True
    
    def reset(self) -> None:
        """タイマーをリセット"""
        self._state = TimerState.IDLE
        self._remaining_seconds = self.config.work_duration
        self._start_time = None
        self._paused_remaining = None
    
    def is_running(self) -> bool:
        """タイマーが実行中かどうか"""
        return self._start_time is not None
    
    def is_finished(self) -> bool:
        """タイマーが終了したかどうか"""
        return self.remaining_seconds <= 0
    
    def complete_session(self) -> TimerState:
        """現在のセッションを完了し、次の状態に遷移
        
        Returns:
            TimerState: 遷移後の状態
        """
        self._start_time = None
        self._paused_remaining = None
        
        if self._state == TimerState.WORK:
            self._completed_pomodoros += 1
            
            # 長い休憩の条件をチェック
            if self._completed_pomodoros % self.config.pomodoros_until_long_break == 0:
                self._state = TimerState.LONG_BREAK
                self._remaining_seconds = self.config.long_break_duration
            else:
                self._state = TimerState.SHORT_BREAK
                self._remaining_seconds = self.config.short_break_duration
        else:
            # 休憩終了後は作業に戻る
            self._state = TimerState.WORK
            self._remaining_seconds = self.config.work_duration
        
        return self._state
    
    def get_state_label(self) -> str:
        """現在の状態の日本語ラベルを取得"""
        labels = {
            TimerState.IDLE: "待機中",
            TimerState.WORK: "作業中",
            TimerState.SHORT_BREAK: "短い休憩",
            TimerState.LONG_BREAK: "長い休憩",
        }
        return labels.get(self._state, "不明")
    
    def format_time(self) -> str:
        """残り時間を MM:SS 形式でフォーマット"""
        return format_seconds(self.remaining_seconds)


def format_seconds(seconds: int) -> str:
    """秒を MM:SS 形式にフォーマット（純粋関数）
    
    Args:
        seconds: 秒数
    
    Returns:
        str: MM:SS形式の文字列
    """
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"
