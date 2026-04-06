import os
import sys
from flask import Flask,jsonify,request,render_template
from flask_cors import CORS
from datetime import datetime

from src.models import Poem
from config import db,APP_API_KEY,COCOBASE_API_KEY


app = Flask("name")
CORS(app)
app.json.ensure_ascii = False

route_name = "/poems"

@app.route(route_name,methods=["GET"])
def get_all_poems():
    poems = db.list_documents("poems")
    formatted_poems = []
    for p in poems:
        formatted_poems.append({
            "id": p.id,
            "data": p.data
        })
    
    return jsonify(formatted_poems), 200
 
@app.route("/poem",methods=["GET"])
def get_poem():
    data = request.get_json()

    target_id = data.get("id")

    if not target_id:
        return jsonify({"error": "ID is required"}), 400

    all_records = db.list_documents("poems")
    poem = next((p for p in all_records if p.id == target_id), None)

    if poem:
        return jsonify({
            "id": poem.id,
            "data": poem.data
        }), 200
    
    return jsonify({"error": "Poem not found"}), 404

@app.route(route_name,methods=["POST"])
def create_poem():
    data = request.get_json()

    api_key = data.get("api_key")
    title = data.get("title")
    content = data.get("content")
    date = datetime.now()

    poem = Poem(title,content,date)

    if not title or not content:
        return jsonify({"error": "Title and content are required"}), 400

    if api_key != APP_API_KEY:
        jsonify({"error":"API_KEY is invalid"}),401

    try:
        db.create_document("poems", {
            "title": poem.title,
            "content": poem.content,
            "date": poem.date.isoformat()
        })
    except CocobaseError as e:
        if "200" not in str(e):
            raise e

    return jsonify({
        "title": poem.title,
        "content": poem.content,
        "date": poem.date.isoformat()
    }), 201

@app.route("/poem", methods=["PUT"])
def update_poem():
    data = request.get_json()
    poem_id = data.get("id")
    api_key = data.get("api_key")
    
    if api_key != APP_API_KEY:
        return jsonify({"error": "API_KEY is invalid"}), 401

    if not poem_id:
        return jsonify({"error": "Poem ID is required"}), 400

    update_data = {}
    if data.get("title"):
        update_data["title"] = data.get("title")
    if data.get("content"):
        update_data["content"] = data.get("content")
    
    update_data["date"] = datetime.now().isoformat()

    try:
        db.update_document("poems", poem_id, update_data)
    except CocobaseError as e:
        if "200" not in str(e):
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Poem updated successfully", "id": poem_id}), 200


@app.route("/",methods=["GET"])
def index():
    return render_template("pages/index.html", title="Aishat's Poem API")

if __name__ == "__main__":
    print(COCOBASE_API_KEY)
    app.run()