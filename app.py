# -*- coding: utf-8 -*-
"""
Clever Student Portal — Flask web application.

Usage:
    pip install -r requirements.txt
    python app.py
    Open http://localhost:5000
"""

import os
import re
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from canvas_client import CanvasClient, CanvasAPIError, CanvasAuthError

load_dotenv()
ACCESS_TOKEN = os.environ.get("CANVAS_TOKEN", "")
BASE_URL = "https://browardschools.instructure.com"
CURRENT_TERM_ID = 3133

app = Flask(__name__)


def _parse_period(section_name: str) -> int:
    """Extract period number from a section name for sort ordering."""
    if not section_name:
        return 999
    # "Period 1", "Per 1", "Per. 01", etc.
    m = re.search(r'\bper(?:iod)?\.?\s*(\d{1,2})\b', section_name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Bare "P1", "P2" not preceded by another letter
    m = re.search(r'(?<![a-zA-Z])P(\d{1,2})\b', section_name)
    if m:
        return int(m.group(1))
    return 999


def _score_to_grade(score: float) -> str:
    if score >= 90: return 'A'
    if score >= 80: return 'B'
    if score >= 70: return 'C'
    if score >= 60: return 'D'
    return 'F'


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/dashboard")
def api_dashboard():
    """Return student profile + current courses with grades."""
    try:
        client = CanvasClient(BASE_URL, ACCESS_TOKEN)

        user = client.get_user_self()
        user_id = user["id"]

        # Fetch profile and missing submissions alongside courses.
        profile = client.get_user_profile()
        missing_subs = client.get_missing_submissions()

        # Build a per-course missing count before iterating courses.
        missing_by_course: dict = {}
        for sub in missing_subs:
            cid = sub.get("course_id")
            if cid:
                missing_by_course[cid] = missing_by_course.get(cid, 0) + 1

        courses = client.get_courses(params={
            "per_page": 100,
            "enrollment_type": "student",
            "enrollment_state": "active",
            "include[]": [
                "total_scores",
                "current_grading_period_scores",
                "grading_period_scores",
                "course_image",
                "sections",
            ],
        })

        current_courses = [
            c for c in courses
            if c.get("enrollment_term_id") == CURRENT_TERM_ID
        ]

        # Grading periods are term-wide — fetch once from the first course.
        grading_periods = []
        if current_courses:
            try:
                grading_periods = client.get_grading_periods(
                    current_courses[0]["id"]
                )
            except CanvasAPIError:
                pass

        formatted_courses = []
        for course in current_courses:
            enrollment = next(
                (e for e in course.get("enrollments", []) if e.get("type") == "student"),
                {}
            )
            # include[]=sections returns only the sections this student is enrolled in,
            # so the first entry is the student's section — no id matching needed.
            sections = course.get("sections", [])
            section_obj = sections[0] if sections else {}
            section_name = section_obj.get("name", "")
            period = _parse_period(section_name)

            gp_scores = enrollment.get("grading_period_scores") or {}
            quarters = []
            for gp in grading_periods:
                gp_data = gp_scores.get(str(gp["id"])) or {}
                score = gp_data.get("current_score")
                grade = gp_data.get("current_grade") or (
                    _score_to_grade(score) if score is not None else None
                )
                quarters.append({
                    "id": gp["id"],
                    "title": gp["title"],
                    "score": score,
                    "grade": grade,
                })
            formatted_courses.append({
                "id": course["id"],
                "name": course["name"],
                "course_code": course.get("course_code", ""),
                "section_name": section_name,
                "period": period,
                "current_grade": enrollment.get("computed_current_grade"),
                "current_score": enrollment.get("computed_current_score"),
                "final_grade": enrollment.get("computed_final_grade"),
                "final_score": enrollment.get("computed_final_score"),
                "image_url": course.get("image_download_url"),
                "missing_count": missing_by_course.get(course["id"], 0),
                "quarters": quarters,
            })

        formatted_courses.sort(key=lambda c: c["period"])

        return jsonify({
            "student": {
                "id": user_id,
                "name": profile.get("name") or user.get("name"),
                "short_name": profile.get("short_name", ""),
                "sortable_name": profile.get("sortable_name", ""),
                "avatar_url": profile.get("avatar_url") or user.get("avatar_url"),
                "email": profile.get("primary_email") or user.get("email") or user.get("login_id"),
                "login_id": profile.get("login_id", ""),
                "sis_user_id": profile.get("sis_user_id", ""),
                "bio": profile.get("bio") or "",
                "time_zone": profile.get("time_zone", ""),
                "locale": profile.get("locale") or "",
            },
            "courses": formatted_courses,
        })

    except CanvasAuthError:
        return jsonify({
            "error": "auth",
            "message": "Invalid or expired API token. Generate a new one in Canvas → Account → Settings."
        }), 401
    except CanvasAPIError as exc:
        return jsonify({"error": "api", "message": str(exc)}), 500
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": "unknown", "message": str(exc)}), 500


@app.route("/api/todo")
def api_todo():
    """Return upcoming to-do items (assignments needing submission) across all courses."""
    try:
        client = CanvasClient(BASE_URL, ACCESS_TOKEN)
        items = client.get_todo_items()

        formatted = []
        for item in items:
            if item.get("type") != "submitting":
                continue
            assignment = item.get("assignment") or {}
            formatted.append({
                "course_id": item.get("course_id"),
                "assignment_id": assignment.get("id"),
                "name": assignment.get("name", ""),
                "due_at": assignment.get("due_at"),
                "points_possible": assignment.get("points_possible"),
                "html_url": assignment.get("html_url", ""),
            })

        formatted.sort(key=lambda x: x["due_at"] or "9999-99-99")
        return jsonify({"items": formatted})

    except CanvasAuthError:
        return jsonify({"error": "auth", "message": "Invalid or expired API token."}), 401
    except CanvasAPIError as exc:
        return jsonify({"error": "api", "message": str(exc)}), 500
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": "unknown", "message": str(exc)}), 500


@app.route("/course/<int:course_id>")
def course_detail(course_id: int):
    return render_template("course.html", course_id=course_id)


@app.route("/course/<int:course_id>/classmates")
def course_classmates(course_id: int):
    return render_template("classmates.html", course_id=course_id)


@app.route("/api/course/<int:course_id>")
def api_course(course_id: int):
    """Return course info and classmates in the student's section."""
    try:
        client = CanvasClient(BASE_URL, ACCESS_TOKEN)

        user = client.get_user_self()
        user_id = user["id"]

        course = client.get_course(course_id)

        # Find the current student's section in this course.
        my_enrollments = client.get_enrollments(course_id, params={
            "user_id": user_id,
            "type[]": "StudentEnrollment",
        })
        if not my_enrollments:
            return jsonify({"error": "not_enrolled", "message": "Not enrolled."}), 404

        enrollment = my_enrollments[0]
        section_id = enrollment["course_section_id"]
        section = client.get_section(section_id)

        # All students in the same section.
        raw = client.get_section_enrollments(section_id, params={
            "type[]": "StudentEnrollment",
            "include[]": "avatar_url",
            "per_page": 100,
        })

        students = []
        for e in raw:
            u = e.get("user", {})
            students.append({
                "id": u.get("id"),
                "name": u.get("name", ""),
                "sortable_name": u.get("sortable_name", ""),
                "avatar_url": u.get("avatar_url"),
                "is_self": u.get("id") == user_id,
            })
        students.sort(key=lambda s: s["sortable_name"].lower())

        grades = enrollment.get("grades", {})

        return jsonify({
            "course": {
                "id": course_id,
                "name": course.get("name", ""),
                "course_code": course.get("course_code", ""),
                "current_score": grades.get("current_score"),
                "final_score": grades.get("final_score"),
            },
            "section": {
                "id": section_id,
                "name": section.get("name", ""),
            },
            "students": students,
        })

    except CanvasAuthError:
        return jsonify({"error": "auth", "message": "Invalid or expired API token."}), 401
    except CanvasAPIError as exc:
        return jsonify({"error": "api", "message": str(exc)}), 500
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": "unknown", "message": str(exc)}), 500


@app.route("/api/course/<int:course_id>/assignments")
def api_course_assignments(course_id: int):
    """Return assignments with full submission data (including comments) for a course."""
    try:
        client = CanvasClient(BASE_URL, ACCESS_TOKEN)

        groups = client.get_assignment_groups(course_id)
        group_map = {g["id"]: g["name"] for g in groups}

        assignments = client.get_assignments(course_id, params={
            "include[]": ["submission"],
            "per_page": 100,
            "order_by": "due_at",
        })

        # Fetch full submission objects (with teacher comments) separately,
        # then merge into assignments by assignment_id.
        raw_subs = client.get_student_submissions(course_id, params={
            "include[]": "submission_comments",
        })
        sub_map = {s["assignment_id"]: s for s in raw_subs}

        formatted = []
        for a in assignments:
            sub = sub_map.get(a["id"]) or a.get("submission") or {}
            score = sub.get("score")
            pts = a.get("points_possible") or 0
            pct = round(score / pts * 100, 1) if (score is not None and pts > 0) else None

            comments = [
                {
                    "author": c.get("author_name", ""),
                    "body": c.get("comment", ""),
                    "created_at": c.get("created_at"),
                }
                for c in (sub.get("submission_comments") or [])
            ]

            sub_type_map = {
                "online_text_entry": "Text",
                "online_upload": "File Upload",
                "online_quiz": "Quiz",
                "discussion_topic": "Discussion",
                "media_recording": "Media",
                "external_tool": "External Tool",
                "on_paper": "On Paper",
            }
            raw_type = sub.get("submission_type") or ""
            sub_type = sub_type_map.get(raw_type, raw_type.replace("_", " ").title() if raw_type else None)

            formatted.append({
                "id": a["id"],
                "name": a.get("name", ""),
                "group": group_map.get(a.get("assignment_group_id"), "Other"),
                "group_id": a.get("assignment_group_id"),
                "due_at": a.get("due_at"),
                "points_possible": pts,
                "score": score,
                "pct": pct,
                "status": sub.get("workflow_state", "unsubmitted"),
                "submitted_at": sub.get("submitted_at"),
                "late": sub.get("late", False),
                "attempt": sub.get("attempt"),
                "submission_type": sub_type,
                "comments": comments,
                "html_url": a.get("html_url", ""),
            })

        return jsonify({"assignments": formatted})

    except CanvasAuthError:
        return jsonify({"error": "auth", "message": "Invalid or expired API token."}), 401
    except CanvasAPIError as exc:
        return jsonify({"error": "api", "message": str(exc)}), 500
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": "unknown", "message": str(exc)}), 500


@app.route("/activity")
def activity():
    return render_template("activity.html")


@app.route("/api/activity")
def api_activity():
    """Return announcements and upcoming events for all current courses."""
    try:
        client = CanvasClient(BASE_URL, ACCESS_TOKEN)

        courses = client.get_courses(params={
            "enrollment_type": "student",
            "enrollment_state": "active",
            "per_page": 100,
        })
        current = [c for c in courses if c.get("enrollment_term_id") == CURRENT_TERM_ID]
        course_map = {c["id"]: c["name"] for c in current}
        context_codes = [f"course_{c['id']}" for c in current]

        items = []

        # Announcements
        try:
            announcements = client.get_announcements(context_codes)
        except CanvasAPIError:
            announcements = []

        for ann in announcements:
            ccode = ann.get("context_code", "")
            cid = int(ccode.replace("course_", "")) if ccode.startswith("course_") else None
            items.append({
                "type": "announcement",
                "id": ann["id"],
                "title": ann.get("title", ""),
                "body": ann.get("message", ""),
                "course_id": cid,
                "course_name": course_map.get(cid, ccode),
                "date": ann.get("posted_at"),
                "html_url": ann.get("html_url", ""),
            })

        # Upcoming events (assignment due dates + calendar events)
        try:
            events = client.get_upcoming_events()
        except CanvasAPIError:
            events = []

        for ev in events:
            ccode = ev.get("context_code", "")
            cid = int(ccode.replace("course_", "")) if ccode.startswith("course_") else None
            is_assignment = bool(ev.get("assignment"))
            items.append({
                "type": "assignment" if is_assignment else "event",
                "id": ev.get("id"),
                "title": ev.get("title", ""),
                "body": "",
                "course_id": cid,
                "course_name": ev.get("context_name") or course_map.get(cid, ccode or ""),
                "date": ev.get("start_at"),
                "html_url": ev.get("html_url", ""),
            })

        items.sort(key=lambda x: x["date"] or "9999", reverse=True)

        return jsonify({
            "items": items,
            "courses": [{"id": c["id"], "name": c["name"]} for c in current],
        })

    except CanvasAuthError:
        return jsonify({"error": "auth", "message": "Invalid or expired API token."}), 401
    except CanvasAPIError as exc:
        return jsonify({"error": "api", "message": str(exc)}), 500
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": "unknown", "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
