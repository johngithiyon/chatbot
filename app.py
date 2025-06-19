from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import re
from fuzzywuzzy import process

app = Flask(__name__)

# Load Q&A dataset from JSON
with open("qa_dataset.json") as f:
    qa_pairs = json.load(f)

users = {
    "john@example.com": {"password": "1234"},
    "jane@example.com": {"password": "5678"}
}
   

# Extract questions from dataset
questions = [pair["question"] for pair in qa_pairs]

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/chat")
def chat_page():
    return render_template("index.html")

# Serve static reports (PDF)
@app.route("/reports/<filename>")
def download_report(filename):
    return send_from_directory("reports", filename, as_attachment=True)

# Serve images from 'images/' directory
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory("images", filename)

# API endpoint for chatbot messages
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").lower().strip()

    if not user_input:
        return jsonify({"response": "Please ask a question."})

    # ✅ Match "report day X"
    report_match = re.search(r"report.*day\s*(\d+)", user_input)
    if report_match:
        day = report_match.group(1)
        filename = f"day{day}.pdf"
        if os.path.exists(os.path.join("reports", filename)):
            return jsonify({
                "response": f" Report for Day {day}...",
                "download_url": f"/reports/{filename}"
            })
        return jsonify({"response": f"Report for Day {day} not found."})

    # ✅ Match "image day X"
    image_match = re.search(r"image.*day\s*(\d+)", user_input)
    if image_match:
        day = image_match.group(1)
        filename = f"day{day}.jpg"
        if os.path.exists(os.path.join("images", filename)):
            return jsonify({
                "response": f"Here is the image for Day {day}.",
                "image_url": f"/images/{filename}"
            })
        return jsonify({"response": f"Image for Day {day} not found."})

    # ✅ Match Q&A using fuzzy logic
    best_match, score = process.extractOne(user_input, questions)
    if score > 70:
        for pair in qa_pairs:
            if pair["question"] == best_match:
                return jsonify({"response": pair["answer"]})

    return jsonify({"response": "Sorry, I don't understand that question."})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    user = users.get(email)
    if not user or user["password"] != password:
        return jsonify({"success": False, "message": "Invalid email or password."}), 401
    else:
        return jsonify({"success": True, "message": "Login successful.", "redirect_url": "/chat"})

if __name__ == "__main__":
    app.run(debug=True)
