# -*- coding: utf-8 -*-
"""
Clever Student Portal — Flask web application.

Usage:
    pip install -r requirements.txt
    python app.py
    Open http://localhost:5000
"""

import os
from flask import Flask, jsonify, render_template
from canvas_client import CanvasClient, CanvasAPIError, CanvasAuthError

ACCESS_TOKEN = os.environ.get(
    "CANVAS_TOKEN",
    "1773~BNxkQuBnxcZ2BDPEQNAJ2fnvQYG2LMHEUPnfnKBvykFJeXMX7nQ76HLCZtNhz4nA"
)
BASE_URL = "https://browardschools.instructure.com"
CURRENT_TERM_ID = 3133

app = Flask(__name__)


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

        courses = client.get_courses(params={
            "per_page": 100,
            "enrollment_type": "student",
            "enrollment_state": "active",
            "include[]": [
                "total_scores",
                "current_grading_period_scores",
                "grading_period_scores",
                "course_image",
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
            gp_scores = enrollment.get("grading_period_scores") or {}
            quarters = [
                {
                    "id": gp["id"],
                    "title": gp["title"],
                    "score": (gp_scores.get(str(gp["id"])) or {}).get("current_score"),
                    "grade": (gp_scores.get(str(gp["id"])) or {}).get("current_grade"),
                }
                for gp in grading_periods
            ]
            formatted_courses.append({
                "id": course["id"],
                "name": course["name"],
                "course_code": course.get("course_code", ""),
                "current_grade": enrollment.get("computed_current_grade"),
                "current_score": enrollment.get("computed_current_score"),
                "final_grade": enrollment.get("computed_final_grade"),
                "final_score": enrollment.get("computed_final_score"),
                "image_url": course.get("image_download_url"),
                "quarters": quarters,
            })

        return jsonify({
            "student": {
                "id": user_id,
                "name": user.get("name"),
                "avatar_url": user.get("avatar_url"),
                "email": user.get("email") or user.get("login_id"),
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
