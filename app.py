import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from bson.errors import InvalidId
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, url_for, session
from pymongo import MongoClient
from flask_wtf import FlaskForm
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import EmailField, PasswordField, StringField, TextAreaField, DateTimeLocalField, IntegerField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    Optional,
    ValidationError,
    NumberRange,
)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client[os.getenv("MONGO_DBNAME", "studybuddy")]
profiles = db["profiles"]
requests = db["requests"]
NEW_YORK = ZoneInfo("America/New_York")

class User(UserMixin):
    def __init__(self, profile):
        self.id = str(profile["_id"])
        self.name = profile["name"]

@login_manager.user_loader
def load_user(user_id):
    try:
        profile_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None

    profile = profiles.find_one(
        {"_id": profile_id},
        {"name": 1, "password_hash": 1}
    )

    if profile is None or not profile.get("password_hash"):
        return None

    return User(profile)

def oid(value):
    try:
        return ObjectId(value)
    except Exception:
        abort(404)


def split_courses(text):
    return [c.strip().upper() for c in text.split(",") if c.strip()]

class SignupForm(FlaskForm):
    name = StringField(
        "Display name",
        validators=[DataRequired(), Length(max=80)],
    )

    email = EmailField(
        "Email",
        validators=[DataRequired(), Length(max=254), Email()],
        filters=[lambda value: value.strip().lower() if value else value],
        render_kw={"autocomplete": "email"},
    )

    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(min=12, max=128)],
        render_kw={"autocomplete": "new-password"},
    )

    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            InputRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
        render_kw={"autocomplete": "new-password"},
    )

    courses = StringField(
        "Your courses",
        validators=[DataRequired(), Length(max=500)],
        render_kw={
            "placeholder": "e.g. CSCI-UA 201, CSCI-UA 202",
            "aria-describedby": "courses-help",
        },
    )

    availability = StringField(
        "When can you study?",
        validators=[DataRequired(), Length(max=200)],
    )

    bio = TextAreaField(
        "About you (optional)",
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3},
    )

    def validate_courses(self, field):
        if not split_courses(field.data):
            raise ValidationError("Enter at least one course code.")

class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[DataRequired(), Length(max=254), Email()],
        filters=[lambda value: value.strip().lower() if value else value],
        render_kw={"autocomplete": "email"},
    )

    password = PasswordField(
        "Password",
        validators=[InputRequired(), Length(max=128)],
        render_kw={"autocomplete": "current-password"},
    )

class LogoutForm(FlaskForm):
    pass

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(
            url_for("profile_detail", profile_id=current_user.id)
        )

    form = SignupForm()

    if form.validate_on_submit():
        doc = {
            "name": form.name.data.strip(),
            "email": form.email.data,
            "password_hash": generate_password_hash(form.password.data),
            "courses": split_courses(form.courses.data),
            "availability": form.availability.data.strip(),
            "bio": (form.bio.data or "").strip(),
            "created_at": datetime.utcnow(),
        }

        try:
            result = profiles.insert_one(doc)
        except DuplicateKeyError:
            form.email.errors.append(
                "An account with this email already exists."
            )

        else:
            doc["_id"] = result.inserted_id
            session.clear()
            login_user(User(doc))

            return redirect(
                url_for("profile_detail", profile_id=result.inserted_id)
            )

    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        profile = profiles.find_one(
            {"email": form.email.data},
            {"name": 1, "password_hash": 1},
        )

        password_hash = (
            profile.get("password_hash") if profile is not None else None
        )

        if (
            password_hash
            and check_password_hash(password_hash, form.password.data)
        ):
            session.clear()
            login_user(User(profile))
            return redirect(url_for("home"))

        form.password.errors.append("Incorrect email or password.")

    return render_template("login.html", form=form)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    form = LogoutForm()

    if request.method == "POST":
        if not form.validate_on_submit():
            abort(400)

        logout_user()
        session.pop("csrf_token", None)
        return redirect(url_for("home"))

    return render_template("logout.html", form=form)

class NewRequestForm(FlaskForm):
    course = StringField(
        "Course",
        validators=[DataRequired(), Length(max=80)],
        render_kw={"placeholder": "CSCI-UA 201"},
    )

    topic = StringField(
        "What will you study?",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Problem set 5, dynamic programming"},
    )

    description = TextAreaField(
        "Description (optional)",
        validators=[Optional()],
        render_kw={"placeholder": "What will you be studying?"},
    )

    max_participants = IntegerField(
        "Maximum Participants",
        validators=[InputRequired(), NumberRange(min=2, max=20)],
        default=5,
        render_kw={"min": 2, "max": 20},
    )

    time = DateTimeLocalField(
        "Date and time (New York)",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )

    location = StringField(
        "Location",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Bobst 5th floor"},
    )

    def validate_time(self, field):
        if field.data is None:
            return

        local_time = field.data.replace(tzinfo=NEW_YORK)

        if local_time.utcoffset() != local_time.replace(fold=1).utcoffset():
            raise ValidationError(
                "this time falls during a daylight saving clock change."
                "please choose another time."
            )

        if local_time.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValidationError("choose a future date and time.")


class JoinRequestForm(FlaskForm):
    pass

class DeleteRequestForm(FlaskForm):
    pass

@app.route("/")
def home():
    selected_course = request.args.get("course", "").strip().upper()
    show_my_courses = request.args.get("scope") == "mine"

    if show_my_courses and not current_user.is_authenticated:
        return redirect(url_for("login"))

    query = {}
    my_courses = []

    if show_my_courses:
        selected_course = ""

        profile = profiles.find_one(
            {"_id": ObjectId(current_user.id)},
            {"courses": 1},
        )

        if profile is not None:
            my_courses = profile.get("courses", [])

        query["course"] = {"$in": my_courses}

    elif selected_course:
        query["course"] = selected_course

    upcoming = {"$gte": datetime.now(timezone.utc)}
    query["starts_at"] = upcoming

    items = list(requests.find(query).sort([("starts_at", 1), ("_id", 1),]))

    courses = sorted(
        course
        for course in requests.distinct("course", {"starts_at": upcoming})
        if isinstance(course, str) and course.strip()
    )

    names = {}
    for person in profiles.find({}, {"name": 1}):
        names[person["_id"]] = person["name"]

    for item in items:
        item["organizer_name"] = names.get(
            item.get("organizer_id"), "Unknown"
        )

    return render_template(
        "home.html",
        items=items,
        courses=courses,
        selected_course=selected_course,
        show_my_courses=show_my_courses,
        my_courses=my_courses,
    )

@app.route("/requests/new", methods=["GET", "POST"])
@login_required
def new_request():
    form = NewRequestForm()

    if form.validate_on_submit():
        local_time = form.time.data.replace(tzinfo=NEW_YORK)
        starts_at = local_time.astimezone(timezone.utc)

        doc = {
            "course": form.course.data.strip().upper(),
            "topic": form.topic.data.strip(),
            "description": (form.description.data or "").strip(),
            "max_participants": form.max_participants.data,
            "starts_at": starts_at,
            "time": local_time.strftime("%b %d, %Y at %I:%M %p %Z"),
            "location": form.location.data.strip(),
            "organizer_id": ObjectId(current_user.id),
            "joined_ids": [],
            "created_at": datetime.utcnow(),
        }

        result = requests.insert_one(doc)

        return redirect(
            url_for("request_detail", request_id=result.inserted_id)
        )

    return render_template("new_request.html", form=form)

@app.route("/requests/<request_id>")
def request_detail(request_id):
    item = requests.find_one({"_id": oid(request_id)})
    if item is None:
        abort(404)

    organizer = profiles.find_one(
        {"_id": item["organizer_id"]},
        {"name": 1},
    )

    joined_ids = item.get("joined_ids", [])
    joined = list(
        profiles.find(
            {"_id": {"$in": joined_ids}},
            {"name": 1},
        )
    )

    viewer_id = (
        ObjectId(current_user.id)
        if current_user.is_authenticated
        else None
    )

    return render_template(
        "request_detail.html",
        item=item,
        organizer=organizer,
        joined=joined,
        join_form=JoinRequestForm(),
        is_organizer=(
            viewer_id is not None
            and viewer_id == item["organizer_id"]
        ),
        has_joined=(
            viewer_id is not None
            and viewer_id in joined_ids
        ),
    )

@app.route("/requests/<request_id>/join", methods=["POST"])
@login_required
def join_request(request_id):
    form = JoinRequestForm()
    if not form.validate_on_submit():
        abort(400)

    session_id = oid(request_id)
    item = requests.find_one({"_id": session_id})
    if item is None:
        abort(404)

    profile_id = ObjectId(current_user.id)

    if item["organizer_id"] == profile_id:
        abort(403)

    result = requests.update_one(
        {"_id": session_id},
        {"$addToSet": {"joined_ids": profile_id}},
    )

    if result.matched_count == 0:
        abort(404)

    return redirect(
        url_for("request_detail", request_id=session_id)
    )

@app.route("/requests/<request_id>/delete", methods=["GET", "POST"])
@login_required
def delete_request(request_id):
    item = requests.find_one({"_id": oid(request_id)})

    if item is None:
        abort(404)

    if item["organizer_id"] != ObjectId(current_user.id):
        abort(403)

    form = DeleteRequestForm()

    if request.method == "POST":
        if not form.validate_on_submit():
            abort(400)

        requests.delete_one({"_id": item["_id"]})
        return redirect(url_for("home"))

    return render_template(
        "delete_request.html",
        item=item,
        form=form,
    )

@app.route("/profiles")
def profile_list():
    people = list(profiles.find().sort("name", 1))
    return render_template("profiles.html", people=people)


@app.route("/profiles/new", methods=["GET", "POST"])
def new_profile():
    return redirect(url_for("signup"))


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

@app.cli.command("init-db")
def init_db():
    profiles.create_index(
        "email",
        unique=True,
        partialFilterExpression={"email": {"$type": "string"}},
        name="unique_profile_email",
    )

    print("Database indexes are ready.")

if __name__ == "__main__":
    app.run(debug=True)
