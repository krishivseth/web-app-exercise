# StudyBuddy team plan

Four people, two one-week sprints. Each person owns a slice of the app end to end (route, template, database code) and reviews one teammate's pull requests. Swap names in below.

## Screens and which issue they satisfy

| Screen | Route | Requirement | Issue |
|---|---|---|---|
| Feed of open sessions | `/` | displays data | #3 |
| Session detail with join | `/requests/<id>` | displays data | #3 |
| Post a session | `/requests/new` | adds data | #2 |
| People list | `/profiles` | displays data | #4 |
| Create profile | `/profiles/new` | adds data | #1 |
| Profile detail | `/profiles/<id>` | displays data | #4 |
| Edit profile | `/profiles/<id>/edit` | edits data | #5 (sprint 2) |
| Delete session | `/requests/<id>/delete` | deletes data | #6 (sprint 2) |
| Search by course or topic | `/?q=` | searches data | #7 (sprint 2) |
| Sign up and log in | `/signup`, `/login` | flask-login | #8 (sprint 2) |

## Sprint 1 (due now)

Person 1, infrastructure. Owns `app.py` setup, the MongoDB connection, `env.example`, `requirements.txt`, `base.html`, `style.css`, and the README. Merges the skeleton PR and reviews everyone else's PRs. Sets up the shared MongoDB Atlas cluster and shares the `.env` in the team channel.

Person 2, sessions. Owns `/requests/new` and `/requests/<id>` (issues #2 and #3). Adds form validation (reject blank fields, trim whitespace), a cleaner date/time input, and a "you joined" state on the detail page.

Person 3, profiles. Owns `/profiles/new`, `/profiles`, and `/profiles/<id>` (issues #1 and #4). Adds validation for duplicate names, a course chip layout, and shows which sessions a person has joined (not just posted).

Person 4, feed and polish. Owns `/` (issue #3) and the mobile CSS pass. Sorts the feed with soonest sessions first, adds a "my course" filter chip row above the feed (groundwork for search), and tests every screen on a real phone or Chrome device mode. Also posts the daily standup summaries and books the sprint 1 stakeholder demo.

## Sprint 2

Person 1 builds search by course (#7), a search box on the feed (`/?q=`) that matches course or topic with a case-insensitive regex and combines with the course chips and My courses filter.


Person 2 builds delete (#6), a confirm screen at `/requests/<id>/delete` plus the POST that removes the document, only allowed for the organizer.

Person 3 builds edit profile (#5), a prefilled form at `/profiles/<id>/edit` and the POST that calls `update_one`.

Person 4 builds sign up and log in (#8) with flask-login. Once it works, replace the "Posting as" and "Join as" dropdowns with the logged-in user, and lock edit and delete to the owner.

## Process rules (from the course instructions)

Work on a branch per issue, named like `3-feed` or `5-edit-profile`. Open a PR against this repo's `main` (check the base repo is ours, not the professor's). A different teammate approves and merges. Move the issue card on the sprint board to In Progress when you start and to Done when merged. Three standups a week, under ten minutes, one summary post per standup in the team channel.
