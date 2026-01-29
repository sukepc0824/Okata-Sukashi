from flask import Flask, render_template, request, jsonify, redirect, url_for
import random

app = Flask(__name__)

# ===== データ =====

groups = {
    "A": {
        "members": 4,
        "werewolf": random.randint(1, 4),
        "reward": 0,
        "answered": False,
        "answer": None,
        "score": None,
        "total_score": 0
    },
    "B": {
        "members": 4,
        "werewolf": random.randint(1, 4),
        "reward": 0,
        "answered": False,
        "answer": None,
        "score": None, 
        "total_score": 0  
    }
}
  # { "A": {...} }

quizzes = [
    {
        "question": "木崎の身長",
        "correct": 170
    },
    {
        "question": "木崎の体重",
        "correct": 48
    },
    {
        "question": "木崎の部屋番号",
        "correct": 404
    }
]

game_state = {
    "status": "waiting",
    "current_index": -1
}

# 初期化用関数
def reset_all():
    global groups, quizzes, game_state
    groups = {
        "A": {
            "members": 4,
            "werewolf": random.randint(1, 4),
            "reward": 0,
            "answered": False,
            "answer": None,
            "score": None,
            "total_score": 0
        },
        "B": {
            "members": 4,
            "werewolf": random.randint(1, 4),
            "reward": 0,
            "answered": False,
            "answer": None,
            "score": None,
            "total_score": 0
        }
    }
    quizzes = [
        {
            "question": "木崎の身長",
            "correct": 170
        },
        {
            "question": "木崎の体重",
            "correct": 48
        },
        {
            "question": "木崎の部屋番号",
            "correct": 404
        }
    ]
    game_state = {
        "status": "waiting",
        "current_index": -1
    }

# ===== 参加 =====

@app.route("/", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        group = request.form["group"].upper()
        player = int(request.form["player"])

        if group not in groups:
            groups[group] = {
                "members": 4,
                "werewolf": random.randint(1, 4),
                "answered": False,
                "answer": None,
                "score": None,
                "total_score": 0
            }

        return redirect(url_for("quiz", group=group, player=player))

    return render_template("join.html")

# ===== クイズ画面 =====

@app.route("/quiz")
def quiz():
    return render_template(
        "quiz.html",
        group=request.args.get("group"),
        player=request.args.get("player")
    )

# ===== 状態取得 =====

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

    answered = groups[group]["answered"] if group in groups else False

    if game_state["status"] == "answering":
        data = {
            "status": "answering",
            "question": quiz["question"],
            "is_werewolf": is_werewolf,
            "answered": answered
        }
        if is_werewolf:
            data["correct"] = quiz["correct"]
        return jsonify(data)

    if game_state["status"] == "result":
        return jsonify({
            "status": "result",
            "correct": quiz["correct"],
            "score": groups[group]["score"],
            "total_score": groups[group]["total_score"]
        })
    if game_state["status"] == "ranking":
        ranking = sorted(
        groups.items(),
        key=lambda x: x[1]["total_score"]
        )

        return jsonify({
            "status": "ranking",
            "ranking": [
                {"group": g, "score": v["total_score"]}
                for g, v in ranking
            ]
        })
    return jsonify({"status": "waiting"})

# ===== 回答 =====

@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.json
    group = data["group"]

    if game_state["status"] != "answering":
        return jsonify({"error": "closed"}), 403

    if group not in groups:
        return jsonify({"error": "invalid group"}), 400

    if groups[group]["answered"]:
        return jsonify({"error": "already answered"}), 403

    try:
        ans = float(data["answer"])
    except ValueError:
        return jsonify({"error": "number only"}), 400

    groups[group]["answered"] = True
    groups[group]["answer"] = ans

    return jsonify({"ok": True})

# ===== admin =====

@app.route("/admin")
def admin():
    idx = game_state["current_index"]
    quiz = quizzes[idx] if idx >= 0 else None
    return render_template(
        "admin.html",
        groups=groups,
        quiz=quiz,
        status=game_state["status"]
    )

@app.route("/admin/next", methods=["POST"])
def next_quiz():
    game_state["current_index"] += 1
    if game_state["current_index"] >= len(quizzes):
        return jsonify({"error": "no more quiz"}), 400

    game_state["status"] = "answering"

    for g in groups.values():
        g["answered"] = False
        g["answer"] = None
        g["score"] = None

    return jsonify({"ok": True})

@app.route("/admin/result", methods=["POST"])
def result():
    idx = game_state["current_index"]
    correct = quizzes[idx]["correct"]

    for g in groups.values():
        if g["answer"] is not None:
            g["score"] = abs(g["answer"] - correct)
            g["total_score"] += g["score"]

    game_state["status"] = "result"
    return jsonify({"ok": True})

@app.route("/admin/ranking", methods=["POST"])
def ranking():
    game_state["status"] = "ranking"
    return jsonify({"ok": True})


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    reset_all()
    return jsonify({"ok": True})




# ===== 起動 =====

if __name__ == "__main__":
    app.run(debug=True)
