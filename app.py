from flask import Flask, render_template, request, jsonify, redirect, url_for
import random

app = Flask(__name__)

groups = {
    "A": {
        "members": 3,
        "werewolf": random.randint(1, 3),
        "reward": 0,
        "answered": False,
        "answer": None,
        "score": None,      # ←追加
        "total_score": 0   # ←累積用（任意）
    }
}

quizzes = [
    {
        "question": "√2 を小数で答えよ",
        "correct": 1.41421356
    },
    {
        "question": "円周率を小数第3位まで",
        "correct": 3.142
    },
    {
        "question": "2^10 はいくつ？",
        "correct": 1024
    }
]


game_state = {
    "status": "waiting",
    "current_index": -1 
}

# 参加画面
@app.route("/", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        group = request.form["group"]
        if group not in groups:
            groups[group] = {
                "members": 3,
                "reward": 0,
                "answered": False,
                "answer": None
            }
        return redirect(url_for("quiz", group=group))
    return render_template("join.html")

@app.route("/quiz")
def quiz():
    group = request.args.get("group")
    return render_template("quiz.html", group=group)

@app.route("/admin/next", methods=["POST"])
def next_quiz():
    game_state["current_index"] += 1

    if game_state["current_index"] >= len(quizzes):
        return jsonify({"error": "no more quiz"}), 400

    game_state["status"] = "answering"

    # 回答リセット
    for g in groups.values():
        g["answered"] = False
        g["answer"] = None
        g["score"] = None

    return jsonify({"ok": True})


# 状態取得（ポーリング用）
@app.route("/api/state")
def state():
    group = request.args.get("group")
    player = int(request.args.get("player"))

    idx = game_state["current_index"]
    quiz = quizzes[idx] if idx >= 0 else None

    is_werewolf = (
        group in groups and
        player == groups[group]["werewolf"]
    )

    # クイズ中
    if game_state["status"] == "answering":
        data = {
            "status": "answering",
            "question": quiz["question"],
            "is_werewolf": is_werewolf
        }

        # 人狼だけ正解が見える
        if is_werewolf:
            data["correct"] = quiz["correct"]

        return jsonify(data)

    # 正解発表
    if game_state["status"] == "result":
        return jsonify({
            "status": "result",
            "correct": quiz["correct"],
            "score": groups[group]["score"],
            "total_score": groups[group]["total_score"]
        })

    return jsonify({"status": "waiting"})


# 回答送信
@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.json
    group = data["group"]

    try:
        ans = float(data["answer"])
    except ValueError:
        return jsonify({"error": "number only"}), 400

    if group in groups:
        groups[group]["answered"] = True
        groups[group]["answer"] = ans

    return jsonify({"ok": True})


# --- 管理者側 ---

@app.route("/admin")
def admin():
    return render_template("admin.html", groups=groups)

@app.route("/admin/start/<int:quiz_id>", methods=["POST"])
def start_quiz(quiz_id):
    game_state["current_quiz"] = quiz_id
    game_state["status"] = "answering"

    for g in groups.values():
        g["answered"] = False
        g["answer"] = None

    return jsonify({"ok": True})

@app.route("/admin/result", methods=["POST"])
def show_result():
    idx = game_state["current_index"]
    correct = quizzes[idx]["correct"]

    for g in groups.values():
        if g["answer"] is not None:
            score = abs(g["answer"] - correct)
            g["score"] = score
            g["total_score"] += score

    game_state["status"] = "result"
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)