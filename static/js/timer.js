/**
 * ポモドーロタイマー JavaScript
 * 
 * タイマーロジック、状態管理、ゲーミフィケーション機能を担当
 */

// タイマー設定（秒）
const CONFIG = {
    WORK_DURATION: 25 * 60,        // 25分
    SHORT_BREAK_DURATION: 5 * 60,  // 5分
    LONG_BREAK_DURATION: 15 * 60,  // 15分
    POMODOROS_UNTIL_LONG_BREAK: 4  // 長い休憩までのポモドーロ数
};

// タイマー状態
const TimerState = {
    IDLE: 'idle',
    WORK: 'work',
    SHORT_BREAK: 'short_break',
    LONG_BREAK: 'long_break'
};

// 状態ラベル
const STATE_LABELS = {
    [TimerState.IDLE]: '待機中',
    [TimerState.WORK]: '作業中',
    [TimerState.SHORT_BREAK]: '短い休憩',
    [TimerState.LONG_BREAK]: '長い休憩'
};

// ========================================
// 純粋関数（テスト可能）
// ========================================

/**
 * 秒数をMM:SS形式にフォーマット
 * @param {number} seconds - 秒数
 * @returns {string} MM:SS形式の文字列
 */
function formatSeconds(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 秒数を「X時間Y分」形式にフォーマット
 * @param {number} seconds - 秒数
 * @returns {string} フォーマットされた時間文字列
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}時間${mins}分`;
    }
    return `${mins}分`;
}

/**
 * 進捗リングのオフセットを計算
 * @param {number} remaining - 残り秒数
 * @param {number} total - 全体秒数
 * @returns {number} stroke-dashoffset値
 */
function calculateProgressOffset(remaining, total) {
    const circumference = 2 * Math.PI * 90; // 半径90のSVG円
    const progress = remaining / total;
    return circumference * (1 - progress);
}

// ========================================
// タイマークラス
// ========================================

class PomodoroTimer {
    constructor() {
        this.state = TimerState.IDLE;
        this.remainingSeconds = CONFIG.WORK_DURATION;
        this.totalSeconds = CONFIG.WORK_DURATION;
        this.isRunning = false;
        this.intervalId = null;
        this.completedPomodoros = 0;
        
        // ゲーミフィケーションデータ
        this.gamificationData = {
            level: 1,
            totalXp: 0,
            xpProgress: { xp_in_current_level: 0, xp_needed_for_next: 100, progress_percent: 0 },
            streakDays: 0,
            badges: [],
            weeklyStats: null,
            monthlyStats: null
        };
        
        // 進捗データ（localStorageから復元）
        this.loadProgress();
    }
    
    /**
     * タイマーを開始
     */
    start() {
        if (this.isRunning) return;
        
        if (this.state === TimerState.IDLE) {
            this.state = TimerState.WORK;
        }
        
        this.isRunning = true;
        this.intervalId = setInterval(() => this.tick(), 1000);
        this.updateUI();
    }
    
    /**
     * タイマーを停止
     */
    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.updateUI();
    }
    
    /**
     * タイマーをリセット
     */
    reset() {
        this.stop();
        this.state = TimerState.IDLE;
        this.remainingSeconds = CONFIG.WORK_DURATION;
        this.totalSeconds = CONFIG.WORK_DURATION;
        this.updateUI();
    }
    
    /**
     * 1秒経過時の処理
     */
    tick() {
        this.remainingSeconds--;
        
        if (this.remainingSeconds <= 0) {
            this.completeSession();
        }
        
        this.updateUI();
    }
    
    /**
     * セッション完了時の処理
     */
    async completeSession() {
        this.stop();
        
        if (this.state === TimerState.WORK) {
            // ポモドーロ完了
            this.completedPomodoros++;
            await this.recordCompletion();
            
            // 次の状態を決定
            if (this.completedPomodoros % CONFIG.POMODOROS_UNTIL_LONG_BREAK === 0) {
                this.state = TimerState.LONG_BREAK;
                this.totalSeconds = CONFIG.LONG_BREAK_DURATION;
            } else {
                this.state = TimerState.SHORT_BREAK;
                this.totalSeconds = CONFIG.SHORT_BREAK_DURATION;
            }
        } else {
            // 休憩終了、作業に戻る
            this.state = TimerState.WORK;
            this.totalSeconds = CONFIG.WORK_DURATION;
        }
        
        this.remainingSeconds = this.totalSeconds;
        this.updateUI();
        
        // 通知（ブラウザが対応している場合）
        this.showNotification();
    }
    
    /**
     * ポモドーロ完了をサーバーに記録
     */
    async recordCompletion() {
        try {
            const response = await fetch('/api/progress/complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ focus_seconds: CONFIG.WORK_DURATION })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateProgressUI(data.progress);
                
                // ゲーミフィケーションデータを更新
                if (data.gamification) {
                    this.handleGamificationUpdate(data.gamification);
                }
                
                this.saveProgress();
            }
        } catch (error) {
            console.error('進捗の記録に失敗:', error);
            // ローカルでも記録
            this.saveProgress();
        }
    }
    
    /**
     * ゲーミフィケーション更新を処理
     */
    handleGamificationUpdate(gamification) {
        // XP獲得通知を表示
        this.showXpNotification(gamification.xp_earned);
        
        // レベルアップチェック
        const oldLevel = this.gamificationData.level;
        this.gamificationData.level = gamification.level;
        this.gamificationData.totalXp = gamification.total_xp;
        this.gamificationData.streakDays = gamification.streak_days;
        
        if (gamification.level > oldLevel) {
            this.showLevelUpNotification(gamification.level);
        }
        
        // 新規バッジ通知
        if (gamification.new_badges && gamification.new_badges.length > 0) {
            gamification.new_badges.forEach(badge => {
                this.showBadgeNotification(badge);
                this.gamificationData.badges.push(badge);
            });
        }
        
        // UIを更新
        this.updateGamificationUI();
    }
    
    /**
     * XP獲得通知を表示
     */
    showXpNotification(xp) {
        const notification = document.getElementById('xpNotification');
        notification.querySelector('.xp-amount').textContent = `+${xp} XP`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 2000);
    }
    
    /**
     * レベルアップ通知を表示
     */
    showLevelUpNotification(level) {
        const notification = document.getElementById('badgeNotification');
        notification.querySelector('.badge-icon').textContent = '🎉';
        notification.querySelector('.badge-message').innerHTML = 
            `おめでとうございます！<br><span class="badge-name">レベル ${level}</span> に到達しました！`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    /**
     * バッジ獲得通知を表示
     */
    showBadgeNotification(badge) {
        setTimeout(() => {
            const notification = document.getElementById('badgeNotification');
            notification.querySelector('.badge-icon').textContent = badge.icon;
            notification.querySelector('.badge-message').innerHTML = 
                `新しいバッジを獲得！<br><span class="badge-name">${badge.name}</span>`;
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }, 2500); // XP通知の後に表示
    }
    
    /**
     * 通知を表示
     */
    showNotification() {
        if ('Notification' in window && Notification.permission === 'granted') {
            const message = this.state === TimerState.WORK 
                ? '休憩終了！作業を開始しましょう。' 
                : 'お疲れ様！休憩しましょう。';
            
            new Notification('ポモドーロタイマー', {
                body: message,
                icon: '/static/favicon.ico'
            });
        }
    }
    
    /**
     * UIを更新
     */
    updateUI() {
        // タイマー表示
        const timerDisplay = document.getElementById('timerDisplay');
        timerDisplay.textContent = formatSeconds(this.remainingSeconds);
        
        // 進捗リング
        const progressRing = document.getElementById('progressRing');
        const offset = calculateProgressOffset(this.remainingSeconds, this.totalSeconds);
        progressRing.style.strokeDashoffset = offset;
        
        // 状態ラベル
        const statusLabel = document.getElementById('statusLabel');
        statusLabel.textContent = STATE_LABELS[this.state];
        
        // ボタン
        const startBtn = document.getElementById('startBtn');
        if (this.isRunning) {
            startBtn.textContent = '停止';
            startBtn.classList.add('running');
        } else {
            startBtn.textContent = '開始';
            startBtn.classList.remove('running');
        }
    }
    
    /**
     * 進捗UIを更新
     */
    updateProgressUI(progress) {
        document.getElementById('completedCount').textContent = progress.completed_pomodoros;
        document.getElementById('focusTime').textContent = progress.total_focus_time;
    }
    
    /**
     * ゲーミフィケーションUIを更新
     */
    updateGamificationUI() {
        // レベル表示
        document.getElementById('levelDisplay').textContent = this.gamificationData.level;
        
        // XPバー
        const xpProgress = this.gamificationData.xpProgress || { progress_percent: 0, xp_in_current_level: 0, xp_needed_for_next: 100 };
        document.getElementById('xpFill').style.width = `${xpProgress.progress_percent}%`;
        document.getElementById('xpText').textContent = 
            `${xpProgress.xp_in_current_level} / ${xpProgress.xp_needed_for_next} XP`;
        
        // ストリーク表示
        document.getElementById('streakCount').textContent = this.gamificationData.streakDays;
        
        // バッジ表示
        this.updateBadgesUI();
        
        // 週間統計
        if (this.gamificationData.weeklyStats) {
            this.updateWeeklyStatsUI();
        }
    }
    
    /**
     * バッジUIを更新
     */
    updateBadgesUI() {
        const container = document.getElementById('badgesContainer');
        
        if (this.gamificationData.badges.length === 0) {
            container.innerHTML = '<div class="no-badges">バッジはまだありません</div>';
            return;
        }
        
        container.innerHTML = this.gamificationData.badges.map(badge => `
            <div class="badge-item" title="${badge.description}">
                <span class="icon">${badge.icon}</span>
                <span class="name">${badge.name}</span>
            </div>
        `).join('');
    }
    
    /**
     * 週間統計UIを更新
     */
    updateWeeklyStatsUI() {
        const stats = this.gamificationData.weeklyStats;
        const chartContainer = document.getElementById('weeklyChart');
        
        // 最大値を計算（最小5）
        const maxPomodoros = Math.max(5, ...stats.daily_data.map(d => d.completed_pomodoros));
        
        chartContainer.innerHTML = stats.daily_data.map(day => {
            const heightPercent = (day.completed_pomodoros / maxPomodoros) * 100;
            return `
                <div class="chart-bar">
                    <div class="bar-container">
                        <div class="bar-fill" style="height: ${heightPercent}%"></div>
                    </div>
                    <span class="bar-label">${day.day_name}</span>
                </div>
            `;
        }).join('');
        
        // 統計サマリー
        document.getElementById('weeklyPomodoros').textContent = stats.total_pomodoros;
        document.getElementById('avgFocusTime').textContent = `${stats.avg_focus_minutes_per_day}分`;
    }
    
    /**
     * 進捗をlocalStorageに保存
     */
    saveProgress() {
        const today = new Date().toISOString().split('T')[0];
        const progress = {
            date: today,
            completedPomodoros: this.completedPomodoros,
            gamification: this.gamificationData
        };
        localStorage.setItem('pomodoroProgress', JSON.stringify(progress));
    }
    
    /**
     * 進捗をlocalStorageから復元
     */
    loadProgress() {
        const saved = localStorage.getItem('pomodoroProgress');
        if (saved) {
            const progress = JSON.parse(saved);
            const today = new Date().toISOString().split('T')[0];
            
            if (progress.date === today) {
                this.completedPomodoros = progress.completedPomodoros || 0;
                if (progress.gamification) {
                    this.gamificationData = { ...this.gamificationData, ...progress.gamification };
                }
            }
        }
    }
    
    /**
     * サーバーから進捗を取得
     */
    async fetchProgress() {
        try {
            const response = await fetch('/api/progress');
            if (response.ok) {
                const data = await response.json();
                this.updateProgressUI(data);
            }
        } catch (error) {
            console.error('進捗の取得に失敗:', error);
        }
    }
    
    /**
     * サーバーからゲーミフィケーションデータを取得
     */
    async fetchGamification() {
        try {
            const response = await fetch('/api/gamification');
            if (response.ok) {
                const data = await response.json();
                this.gamificationData = {
                    level: data.level,
                    totalXp: data.total_xp,
                    xpProgress: data.xp_progress,
                    streakDays: data.streak_days,
                    badges: data.badges,
                    weeklyStats: data.weekly_stats,
                    monthlyStats: data.monthly_stats
                };
                this.updateGamificationUI();
            }
        } catch (error) {
            console.error('ゲーミフィケーションデータの取得に失敗:', error);
        }
    }
}

// ========================================
// 初期化
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    const timer = new PomodoroTimer();
    
    // ボタンイベント
    document.getElementById('startBtn').addEventListener('click', () => {
        if (timer.isRunning) {
            timer.stop();
        } else {
            timer.start();
        }
    });
    
    document.getElementById('resetBtn').addEventListener('click', () => {
        timer.reset();
    });
    
    // 初期UI更新
    timer.updateUI();
    timer.fetchProgress();
    timer.fetchGamification();
    
    // 通知許可をリクエスト
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});
