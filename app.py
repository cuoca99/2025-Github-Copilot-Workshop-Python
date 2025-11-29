"""ポモドーロタイマー Flaskアプリケーション"""

from flask import Flask, render_template, jsonify, request

from pomodoro import PomodoroTimer, ProgressTracker, GamificationTracker

app = Flask(__name__)

# グローバルインスタンス（シンプルな実装）
# 本番環境ではセッション管理やDB連携を検討
progress_tracker = ProgressTracker()
gamification_tracker = GamificationTracker()


@app.route("/")
def index():
    """メインページを配信"""
    return render_template("index.html")


@app.route("/api/progress", methods=["GET"])
def get_progress():
    """今日の進捗データを取得"""
    return jsonify(progress_tracker.to_dict())


@app.route("/api/progress/complete", methods=["POST"])
def complete_pomodoro():
    """ポモドーロ完了を記録"""
    data = request.get_json() or {}
    focus_seconds = data.get("focus_seconds", 25 * 60)  # デフォルト25分
    
    progress = progress_tracker.add_completed_pomodoro(focus_seconds)
    gamification_result = gamification_tracker.record_pomodoro(focus_seconds)
    
    return jsonify({
        "success": True,
        "progress": {
            "completed_pomodoros": progress.completed_pomodoros,
            "total_focus_seconds": progress.total_focus_seconds,
            "total_focus_time": progress.format_focus_time()
        },
        "gamification": gamification_result
    })


@app.route("/api/progress/reset", methods=["POST"])
def reset_progress():
    """今日の進捗をリセット"""
    progress_tracker.reset_today()
    return jsonify({"success": True})


@app.route("/api/gamification", methods=["GET"])
def get_gamification():
    """ゲーミフィケーションデータを取得"""
    return jsonify(gamification_tracker.to_dict())


@app.route("/api/gamification/weekly", methods=["GET"])
def get_weekly_stats():
    """週間統計を取得"""
    return jsonify(gamification_tracker.get_weekly_stats())


@app.route("/api/gamification/monthly", methods=["GET"])
def get_monthly_stats():
    """月間統計を取得"""
    return jsonify(gamification_tracker.get_monthly_stats())


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
