# -*- coding: utf-8 -*-
"""
Canvas API Explorer — Step 1: Connection test & data inventory.

Run this script to verify the API key works and see a structured
summary of every data category accessible for the student.

Usage:
    python explore.py
"""

import json
from canvas_client import CanvasClient, CanvasAPIError, CanvasAuthError

ACCESS_TOKEN = "1773~BNxkQuBnxcZ2BDPEQNAJ2fnvQYG2LMHEUPnfnKBvykFJeXMX7nQ76HLCZtNhz4nA"
BASE_URL = "https://browardschools.instructure.com"
CURRENT_TERM_ID = 3133

SEP = "-" * 60


def section(title: str) -> None:
    print(f"\n{SEP}\n  {title}\n{SEP}")


def dump(obj, indent: int = 2) -> None:
    print(json.dumps(obj, indent=indent, default=str))


def main() -> None:
    client = CanvasClient(BASE_URL, ACCESS_TOKEN)

    # ------------------------------------------------------------------ #
    # [1] Authentication & user profile
    # ------------------------------------------------------------------ #
    section("1 · AUTHENTICATION & USER PROFILE")
    user = client.get_user_self()
    user_id = user["id"]

    PROFILE_FIELDS = [
        "id", "name", "short_name", "sortable_name",
        "email", "login_id", "locale", "time_zone",
        "avatar_url", "bio", "effective_locale",
    ]
    print(f"  Status : OK — connected as '{user['name']}'")
    print(f"  User ID: {user_id}")
    print("\n  Full profile fields available:")
    for key in user:
        marker = "  *" if key in PROFILE_FIELDS else "   "
        print(f"{marker}  {key}: {user[key]}")

    # ------------------------------------------------------------------ #
    # [2] Courses
    # ------------------------------------------------------------------ #
    section("2 · COURSES")
    all_courses = client.get_courses(params={"per_page": 100, "include[]": "term"})
    current_courses = [c for c in all_courses if c.get("enrollment_term_id") == CURRENT_TERM_ID]

    print(f"  Total courses returned : {len(all_courses)}")
    print(f"  Current-term courses   : {len(current_courses)}")
    print("\n  Current course list:")
    for c in current_courses:
        print(f"    [{c['id']}] {c['name']}  (code: {c.get('course_code', '—')})")

    if all_courses:
        print("\n  Sample course fields (first course):")
        for k, v in all_courses[0].items():
            print(f"    {k}: {v}")

    # ------------------------------------------------------------------ #
    # [3] Enrollments (grades) via user endpoint
    # ------------------------------------------------------------------ #
    section("3 · ENROLLMENTS / GRADES")
    enrollments = client._get_all(
        f"api/v1/users/{user_id}/enrollments",
        params={"per_page": 100, "include[]": "current_points"}
    )
    print(f"  Total enrollment records: {len(enrollments)}")

    current_enrollments = [
        e for e in enrollments
        if e.get("enrollment_term_id") == CURRENT_TERM_ID
        or e.get("course_id") in {c["id"] for c in current_courses}
    ]
    print(f"  Current-term enrollments: {len(current_enrollments)}")
    print("\n  Grade snapshot:")
    for e in current_enrollments:
        grades = e.get("grades", {})
        course_name = e.get("course", {}).get("name", f"course {e.get('course_id')}")
        print(
            f"    {course_name[:40]:<40}  "
            f"current: {grades.get('current_grade', '—'):>4}  "
            f"final: {grades.get('final_grade', '—'):>4}  "
            f"score: {grades.get('current_score', '—')}"
        )

    if enrollments:
        print("\n  Sample enrollment fields (first record):")
        for k, v in enrollments[0].items():
            print(f"    {k}: {v}")

    # ------------------------------------------------------------------ #
    # [4] Assignments + submissions for each current course
    # ------------------------------------------------------------------ #
    section("4 · ASSIGNMENTS & SUBMISSIONS")
    for course in current_courses:
        cid = course["id"]
        cname = course["name"]
        try:
            assignments = client.get_assignments(
                cid,
                params={"per_page": 100, "include[]": ["submission", "score_statistics"]}
            )
        except CanvasAPIError as exc:
            print(f"  [{cid}] {cname}: skipped — {exc}")
            continue

        graded = [a for a in assignments if a.get("submission", {}).get("grade") is not None]
        missing = [a for a in assignments if a.get("submission", {}).get("missing")]
        late = [a for a in assignments if a.get("submission", {}).get("late")]

        print(f"\n  [{cid}] {cname}")
        print(f"    total assignments : {len(assignments)}")
        print(f"    graded            : {len(graded)}")
        print(f"    missing           : {len(missing)}")
        print(f"    late              : {len(late)}")

        if assignments:
            print("    sample fields available on assignment object:")
            for k in list(assignments[0].keys())[:20]:
                print(f"      - {k}")

    # ------------------------------------------------------------------ #
    # [5] Submission history (alternative endpoint)
    # ------------------------------------------------------------------ #
    section("5 · SUBMISSION HISTORY (per-course)")
    for course in current_courses[:2]:   # just first 2 to keep output manageable
        cid = course["id"]
        try:
            subs = client._get_all(
                f"api/v1/courses/{cid}/students/submissions",
                params={
                    "student_ids[]": "all",
                    "per_page": 100,
                    "include[]": ["assignment", "visibility"],
                }
            )
            print(f"\n  [{cid}] {course['name']}: {len(subs)} submission records")
            if subs:
                print("    sample submission fields:")
                for k in list(subs[0].keys())[:15]:
                    print(f"      - {k}")
        except CanvasAPIError as exc:
            print(f"  [{cid}] {course['name']}: skipped — {exc}")

    # ------------------------------------------------------------------ #
    # [6] Section / classmates snapshot
    # ------------------------------------------------------------------ #
    section("6 · CLASSMATES (first current course)")
    if current_courses:
        cid = current_courses[0]["id"]
        try:
            section_enrollments = client.get_enrollments(
                cid,
                params={"per_page": 100, "include[]": "avatar_url"}
            )
            # Find this student's section
            my_record = next(
                (e for e in section_enrollments if e.get("user_id") == user_id), None
            )
            if my_record:
                my_section_id = my_record["course_section_id"]
                classmates = [
                    e["user"]["sortable_name"]
                    for e in section_enrollments
                    if e["course_section_id"] == my_section_id
                    and e["enrollment_state"] == "active"
                ]
                print(f"  Section ID : {my_section_id}")
                print(f"  Classmates : {len(classmates)}")
                for name in sorted(classmates):
                    print(f"    {name}")
            else:
                print("  Could not locate this user in course enrollments.")
        except CanvasAPIError as exc:
            print(f"  Skipped — {exc}")

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    section("SUMMARY — DATA AVAILABLE VIA THIS API KEY")
    print("""
  Category                 Endpoint
  ──────────────────────── ──────────────────────────────────────────────
  User profile             GET /api/v1/users/self
  Courses list             GET /api/v1/courses
  Grades (per enrollment)  GET /api/v1/users/:id/enrollments
  Assignments              GET /api/v1/courses/:id/assignments
  Submissions              GET /api/v1/courses/:id/students/submissions
  Classmates / sections    GET /api/v1/courses/:id/enrollments
  Course sections          GET /api/v1/courses/:id/sections
  Discussion topics        GET /api/v1/courses/:id/discussion_topics
  Announcements            GET /api/v1/announcements?context_codes[]=course_:id
  Calendar events          GET /api/v1/calendar_events
  To-do items              GET /api/v1/users/self/todo
  Upcoming events          GET /api/v1/users/self/upcoming_events
    """)


if __name__ == "__main__":
    try:
        main()
    except CanvasAuthError:
        print("\n[ERROR] Authentication failed. Check ACCESS_TOKEN.")
    except CanvasAPIError as exc:
        print(f"\n[ERROR] API error: {exc}")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n[ERROR] Unexpected error: {exc}")
        raise
