# StudyBuddy

A little exercise to build a web application following an agile development process. See the [instructions](./instructions.md) for more detail.

## Team members

- [Krishiv Seth](https://github.com/krishivseth)
- [manzim7](https://github.com/manzim7)
- [ogngnaoh](https://github.com/ogngnaoh)
- [sallyhegab](https://github.com/sallyhegab)

## Product vision statement

StudyBuddy helps students find classmates to study with by letting them post, browse, and search study sessions for the courses they are taking.

## User stories

All user stories are tracked as [GitHub Issues](https://github.com/krishivseth/web-app-exercise/issues).

## Steps necessary to run the software

You need Python 3.10 or newer, pip, and git installed. You also need a MongoDB database. A free MongoDB Atlas cluster works, or a local MongoDB server running on the default port 27017.

### 1. Clone the repository

```
git clone https://github.com/krishivseth/web-app-exercise.git
cd web-app-exercise
```

### 2. Run the course setup script

Every team member runs this once in each fresh clone. Fix anything it reports.

```
python3 .automations/setup.py
```

On Windows use `python .automations/setup.py`.

### 3. Create and activate a virtual environment

```
python3 -m venv .venv
source .venv/bin/activate
```

On Windows run `.venv\Scripts\activate` instead of the source command.

### 4. Install dependencies

```
pip install -r requirements.txt
```

### 5. Configure the database connection

Copy `env.example` to a new file named `.env` in the project root and fill in the real values. The `.env` file is ignored by git and must never be committed. Get the real values from a teammate through the team channel.

```
cp env.example .env
```

The `.env` file contains these variables:

```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster-host>/?retryWrites=true&w=majority
MONGO_DBNAME=studybuddy
FLASK_SECRET_KEY=any-long-random-string
```

For a local MongoDB server use `MONGO_URI=mongodb://localhost:27017`.

### 6. Run the app

```
flask --app app run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser. The app is designed for a phone-sized screen, so use the browser's mobile view (in Chrome, open DevTools and press the device toolbar toggle) for the intended layout.

## Task boards

Both sprint boards are linked from the repository [Projects page](https://github.com/krishivseth/web-app-exercise/projects).

- [StudyBuddy - Sprint 1](https://github.com/users/krishivseth/projects/2)
- [StudyBuddy - Sprint 2](https://github.com/users/krishivseth/projects/3)
