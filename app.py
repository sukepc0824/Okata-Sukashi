from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import random
import os
from functools import wraps

app = Flask(__name__)

def check_auth(username, password):
    return username == 'admin' and password == 'sukashi'

def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

groups = {}
quizzes = []
game_state = {}

def reset_all(num_groups=5, four_person_groups=None):
    global groups, quizzes, game_state
    
    if four_person_groups is None:
        four_person_groups = []
        
    new_groups = {}
    
    for i in range(num_groups):
        group_id = str(i + 1)
        
        is_four_person = group_id in four_person_groups
        members = 4 if is_four_person else 3
        werewolf_range = 4 if is_four_person else 3
        
        new_groups[group_id] = {
            "name": group_id,
            "members": members,
            "werewolf": random.randint(1, werewolf_range),
            "reward": 0,
            "answered": False,
            "answer": None,
            "score": None,
            "total_score": 0
        }
        
    groups = new_groups
    
    quizzes = [
        {
            "question": "私は身長何cm？声から当ててみよ",
            "correct": 160
        },
        {
            "question": "H2Oの接合角、何度?",
            "correct": 104.5
        },
        {
            "question": "日本にある活火山の個数は？",
            "correct": 111
        },
        {
            "question": "犬の染色体の本数は？",
            "correct": 78
        },
        {
            "question": "日本で二番目に高い山の標高は？",
            "correct": 3193
        },
        {
            "question": "この赤色の波長は何nm？",
            "correct": 610
        },
        {
            "question": "2025年度に日本に起こった 震度4以上の地震の回数は？",
            "correct": 112
        },
        {
            "question": "最新コンピュータは英数字記号7桁のパスワードの突破に何日かかる？",
            "correct": 302
        },
        {
            "question": "ビャンビャンメン 何画?",
            "correct": 130
        }
    ]
    game_state = {
        "status": "waiting",
        "current_index": -1
    }

@app.route("/", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        group = request.form["group"].strip()
        player_char = request.form["player"].upper().strip()
        group_name_input = request.form.get("group_name", "").strip()

        mapping = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
        player_num = mapping.get(player_char, 0)
        
        if player_num == 0:
             pass

        if group not in groups:
            groups[group] = {
                "name": group_name_input if group_name_input else group,
                "members": 3,
                "werewolf": random.randint(1, 3),
                "answered": False,
                "answer": None,
                "score": None,
                "total_score": 0
            }
        else:
            if group_name_input:
                groups[group]["name"] = group_name_input

        return redirect(url_for("quiz", group=group, player=player_char))

    return render_template("join.html")

@app.route("/quiz")
def quiz():
    group = request.args.get("group")
    player = request.args.get("player")
    group_name = groups[group]["name"] if group in groups else group
    return render_template(
        "quiz.html",
        group=group,
        group_name=group_name,
        player=player
    )

@app.route("/api/state")
def state():
    group_id = request.args.get("group")
    player_param = request.args.get("player")

    mapping = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
    try:
        player_num = int(player_param)
    except:
        player_num = mapping.get(player_param, 0)

    idx = game_state["current_index"]
    quiz = quizzes[idx] if idx >= 0 else None

    is_werewolf = (
        group_id in groups and
        player_num == groups[group_id]["werewolf"]
    )

    answered = groups[group_id]["answered"] if group_id in groups else False

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
        ranking_list = sorted(
            groups.items(),
            key=lambda x: x[1]["total_score"],
            reverse=True
        )
        ranking_data = [
            {"group": v["name"], "score": v["total_score"]}
            for g, v in ranking_list
        ]
        
        return jsonify({
            "status": "result",
            "correct": quiz["correct"],
            "score": groups[group_id]["score"],
            "total_score": groups[group_id]["total_score"],
            "ranking": ranking_data
        })
    if game_state["status"] == "ranking":
        ranking = sorted(
        groups.items(),
        key=lambda x: x[1]["total_score"]
        )

        return jsonify({
            "status": "ranking",
            "ranking": [
                {"group": v["name"], "score": v["total_score"]}
                for g, v in ranking
            ]
        })
    return jsonify({"status": "waiting"})

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

@app.route("/admin")
@requires_auth
def admin():
    idx = game_state["current_index"]
    quiz = quizzes[idx] if idx >= 0 else None
    
    sorted_groups = sorted(
        groups.items(),
        key=lambda x: x[1]["total_score"],
        reverse=True
    )
    
    return render_template(
        "admin.html",
        groups=groups,
        sorted_groups=sorted_groups,
        quiz=quiz,
        status=game_state["status"]
    )

@app.route("/admin/next", methods=["POST"])
@requires_auth
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
@requires_auth
def result():
    idx = game_state["current_index"]
    correct = quizzes[idx]["correct"]
    scores_with_groups = []
    for group_name, g in groups.items():
        if g["answer"] is not None:
            abs_diff = abs(g["answer"] - correct)
            scores_with_groups.append((group_name, g, abs_diff))

    scores_with_groups.sort(key=lambda x: x[2])
    for rank, (group_name, g, abs_diff) in enumerate(scores_with_groups):
        points = (len(scores_with_groups) - rank)*100
        g["score"] = points
        g["total_score"] += points

    for group_name, g in groups.items():
        if g["answer"] is None:
            g["score"] = 0

    game_state["status"] = "result"
    return jsonify({"ok": True})

@app.route("/admin/reset", methods=["POST"])
@requires_auth
def admin_reset():
    data = request.json
    num_groups = 5
    four_person = []
    
    if data:
        if "num_groups" in data:
            try:
                num_groups = int(data["num_groups"])
            except:
                pass
        if "four_person" in data:
             fp = data["four_person"]
             if isinstance(fp, str):
                 four_person = [x.strip() for x in fp.split(",") if x.strip()]
             elif isinstance(fp, list):
                 four_person = fp
                 
    reset_all(num_groups=num_groups, four_person_groups=four_person)
    return jsonify({"ok": True})

if __name__ == "__main__":
    reset_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
