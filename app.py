import os
from datetime import datetime

from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, url_for
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client[os.getenv("MONGO_DBNAME", "studybuddy")]
profiles = db["profiles"]
requests = db["requests"]


def oid(value):
    try:
        return ObjectId(value)
    except Exception:
        abort(404)


def split_courses(text):
    return [c.strip().upper() for c in text.split(",") if c.strip()]


@app.route("/")
def home():
    items = list(requests.find().sort("created_at", -1))
    names = {p["_id"]: p["name"] for p in profiles.find({}, {"name": 1})}
    for item in items:
        item["organizer_name"] = names.get(item.get("organizer_id"), "Unknown")
    return render_template("home.html", items=items)


@app.route("/requests/new", methods=["GET", "POST"])
def new_request():
    people = list(profiles.find().sort("name", 1))
    if request.method == "POST":
        doc = {
            "course": request.form["course"].strip().upper(),
            "topic": request.form["topic"].strip(),
            "time": request.form["time"].strip(),
            "location": request.form["location"].strip(),
            "organizer_id": oid(request.form["organizer_id"]),
            "joined_ids": [],
            "created_at": datetime.utcnow(),
        }
        res = requests.insert_one(doc)
        return redirect(url_for("request_detail", request_id=res.inserted_id))
    return render_template("new_request.html", people=people)


@app.route("/requests/<request_id>")
def request_detail(request_id):
    item = requests.find_one({"_id": oid(request_id)})
    if item is None:
        abort(404)
    organizer = profiles.find_one({"_id": item["organizer_id"]})
    joined = list(profiles.find({"_id": {"$in": item.get("joined_ids", [])}}))
    people = list(profiles.find().sort("name", 1))
    return render_template(
        "request_detail.html", item=item, organizer=organizer, joined=joined, people=people
    )


@app.route("/requests/<request_id>/join", methods=["POST"])
def join_request(request_id):
    pid = oid(request.form["profile_id"])
    requests.update_one({"_id": oid(request_id)}, {"$addToSet": {"joined_ids": pid}})
    return redirect(url_for("request_detail", request_id=request_id))


@app.route("/profiles")
def profile_list():
    people = list(profiles.find().sort("name", 1))
    return render_template("profiles.html", people=people)


@app.route("/profiles/new", methods=["GET", "POST"])
def new_profile():
    if request.method == "POST":
        doc = {
            "name": request.form["name"].strip(),
            "courses": split_courses(request.form["courses"]),
            "availability": request.form["availability"].strip(),
            "bio": request.form["bio"].strip(),
            "created_at": datetime.utcnow(),
        }
        res = profiles.insert_one(doc)
        return redirect(url_for("profile_detail", profile_id=res.inserted_id))
    return render_template("new_profile.html")


@app.route("/profiles/<profile_id>")
def profile_detail(profile_id):
    person = profiles.find_one({"_id": oid(profile_id)})
    if person is None:
        abort(404)
    posted = list(requests.find({"organizer_id": person["_id"]}).sort("created_at", -1))
    return render_template("profile.html", person=person, posted=posted)


@app.errorhandler(404)
def not_found(err):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
