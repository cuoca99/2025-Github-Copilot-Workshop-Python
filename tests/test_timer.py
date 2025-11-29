"""PomodoroTimerクラスのユニットテスト"""

import pytest
from pomodoro.timer import PomodoroTimer, TimerConfig, TimerState, format_seconds


class TestFormatSeconds:
    """format_seconds関数のテスト"""
    
    def test_format_zero(self):
        assert format_seconds(0) == "00:00"
    
    def test_format_seconds_only(self):
        assert format_seconds(45) == "00:45"
    
    def test_format_one_minute(self):
        assert format_seconds(60) == "01:00"
    
    def test_format_25_minutes(self):
        assert format_seconds(25 * 60) == "25:00"
    
    def test_format_mixed(self):
        assert format_seconds(5 * 60 + 30) == "05:30"


class TestTimerConfig:
    """TimerConfig のテスト"""
    
    def test_default_values(self):
        config = TimerConfig()
        assert config.work_duration == 25 * 60
        assert config.short_break_duration == 5 * 60
        assert config.long_break_duration == 15 * 60
        assert config.pomodoros_until_long_break == 4
    
    def test_custom_values(self):
        config = TimerConfig(
            work_duration=30 * 60,
            short_break_duration=10 * 60
        )
        assert config.work_duration == 30 * 60
        assert config.short_break_duration == 10 * 60


class TestPomodoroTimer:
    """PomodoroTimerクラスのテスト"""
    
    def test_initial_state(self):
        """初期状態のテスト"""
        timer = PomodoroTimer()
        
        assert timer.state == TimerState.IDLE
        assert timer.remaining_seconds == 25 * 60
        assert timer.completed_pomodoros == 0
        assert not timer.is_running()
    
    def test_start_timer(self):
        """タイマー開始のテスト"""
        # モック時間プロバイダー
        current_time = [0.0]
        def mock_time():
            return current_time[0]
        
        timer = PomodoroTimer(time_provider=mock_time)
        
        result = timer.start()
        
        assert result is True
        assert timer.is_running()
        assert timer.state == TimerState.WORK
    
    def test_start_already_running(self):
        """すでに実行中のタイマーを開始しようとした場合"""
        current_time = [0.0]
        timer = PomodoroTimer(time_provider=lambda: current_time[0])
        
        timer.start()
        result = timer.start()  # 2回目
        
        assert result is False
    
    def test_stop_timer(self):
        """タイマー停止のテスト"""
        current_time = [0.0]
        def mock_time():
            return current_time[0]
        
        timer = PomodoroTimer(time_provider=mock_time)
        timer.start()
        
        # 10秒経過
        current_time[0] = 10.0
        
        result = timer.stop()
        
        assert result is True
        assert not timer.is_running()
        assert timer.remaining_seconds == 25 * 60 - 10
    
    def test_stop_not_running(self):
        """実行していないタイマーを停止しようとした場合"""
        timer = PomodoroTimer()
        
        result = timer.stop()
        
        assert result is False
    
    def test_reset_timer(self):
        """タイマーリセットのテスト"""
        current_time = [0.0]
        timer = PomodoroTimer(time_provider=lambda: current_time[0])
        timer.start()
        current_time[0] = 30.0
        
        timer.reset()
        
        assert timer.state == TimerState.IDLE
        assert timer.remaining_seconds == 25 * 60
        assert not timer.is_running()
    
    def test_remaining_time_decreases(self):
        """残り時間が減少することを確認"""
        current_time = [0.0]
        def mock_time():
            return current_time[0]
        
        timer = PomodoroTimer(time_provider=mock_time)
        timer.start()
        
        # 60秒経過
        current_time[0] = 60.0
        
        assert timer.remaining_seconds == 24 * 60  # 25分 - 1分
    
    def test_is_finished(self):
        """タイマー終了判定のテスト"""
        current_time = [0.0]
        def mock_time():
            return current_time[0]
        
        timer = PomodoroTimer(time_provider=mock_time)
        timer.start()
        
        # 25分経過
        current_time[0] = 25 * 60
        
        assert timer.is_finished()
    
    def test_complete_work_session_to_short_break(self):
        """作業セッション完了→短い休憩への遷移"""
        timer = PomodoroTimer()
        timer._state = TimerState.WORK
        
        next_state = timer.complete_session()
        
        assert next_state == TimerState.SHORT_BREAK
        assert timer.remaining_seconds == 5 * 60
        assert timer.completed_pomodoros == 1
    
    def test_complete_work_session_to_long_break(self):
        """4回目の作業セッション完了→長い休憩への遷移"""
        timer = PomodoroTimer()
        timer._state = TimerState.WORK
        timer._completed_pomodoros = 3  # 3回完了済み
        
        next_state = timer.complete_session()
        
        assert next_state == TimerState.LONG_BREAK
        assert timer.remaining_seconds == 15 * 60
        assert timer.completed_pomodoros == 4
    
    def test_complete_break_session_to_work(self):
        """休憩セッション完了→作業への遷移"""
        timer = PomodoroTimer()
        timer._state = TimerState.SHORT_BREAK
        
        next_state = timer.complete_session()
        
        assert next_state == TimerState.WORK
        assert timer.remaining_seconds == 25 * 60
    
    def test_get_state_label(self):
        """状態ラベル取得のテスト"""
        timer = PomodoroTimer()
        
        assert timer.get_state_label() == "待機中"
        
        timer._state = TimerState.WORK
        assert timer.get_state_label() == "作業中"
        
        timer._state = TimerState.SHORT_BREAK
        assert timer.get_state_label() == "短い休憩"
        
        timer._state = TimerState.LONG_BREAK
        assert timer.get_state_label() == "長い休憩"
    
    def test_format_time(self):
        """時間フォーマットのテスト"""
        timer = PomodoroTimer()
        
        assert timer.format_time() == "25:00"
        
        timer._remaining_seconds = 5 * 60 + 30
        assert timer.format_time() == "05:30"
    
    def test_custom_config(self):
        """カスタム設定でのタイマー"""
        config = TimerConfig(work_duration=30 * 60)
        timer = PomodoroTimer(config=config)
        
        assert timer.remaining_seconds == 30 * 60
