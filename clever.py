# -*- coding: utf-8 -*-
"""
Clever Data Project - Refactored to use CanvasClient
"""

import json
from canvas_client import CanvasClient, CanvasAPIError

#/--------------------------------------------------------------------------------------------------
# CONSTANTS & CONFIGURATION
#/--------------------------------------------------------------------------------------------------
ACCESS_TOKEN = "1773~BNxkQuBnxcZ2BDPEQNAJ2fnvQYG2LMHEUPnfnKBvykFJeXMX7nQ76HLCZtNhz4nA"
BASE_URL = "https://browardschools.instructure.com"
CURRENT_TERM_ID = 3133

# Initialize the robust API client
client = CanvasClient(BASE_URL, ACCESS_TOKEN)

#/--------------------------------------------------------------------------------------------------
# HELPER FUNCTIONS (Project Specific)
#/--------------------------------------------------------------------------------------------------
def filter_enrollments_by_section(all_enrollments, user_id):
    """Filter the total student enrollments for a class to just those in the user's section."""
    try:
        user_record = list(filter(lambda record: record.get('user_id') == user_id, all_enrollments))[0]
        course_section = user_record.get('course_section_id')  

        classmates = [s['user']['sortable_name'] for s in all_enrollments 
                      if s['course_section_id'] == course_section and s['enrollment_state'] == 'active']
        return classmates
    except IndexError:
        return []

#/--------------------------------------------------------------------------------------------------
# MAIN EXECUTION FLOW
#/--------------------------------------------------------------------------------------------------
try:
    # [001] Get User Info
    user_data = client.get_user_self()
    USER_ID = user_data['id']
    print(f"Authenticated as: {user_data['name']} (ID: {USER_ID})")

    # [010] Get enrolled courses
    courses = client.get_courses(params={"per_page": 100})
    current_courses = [c for c in courses if c.get("enrollment_term_id") == CURRENT_TERM_ID]

    print("\n--- Current Courses ---")
    for course in current_courses:
        print(f"{course['id']}: {course['name']}")

    # [020] See enrolled students for a particular class (Science: 1964182)
    enrollments = client.get_enrollments('1964182', params={"per_page": 100})
    classmates = filter_enrollments_by_section(enrollments, USER_ID)
    print(f"\nFound {len(classmates)} classmates in section.")

    # [110] Get current assignments for core classes
    labels = ['History', 'Math', 'Science', 'Technology', 'English']
    course_ids = ['1964160', '1964103', '1964182', '1964205', '1963027']

    combined = {}
    print("\n--- Fetching Assignments ---")
    for label, cid in zip(labels, course_ids):
        print(f"Fetching {label}...")
        assignments = client.get_assignments(cid, params={"per_page": 100})
        
        # Cleanup data (preserve original logic)
        for a in assignments:
            a.pop('secure_params', None) 
            a.pop('description', None)
        
        combined[label] = assignments

    # [210] Retrieve course grades for the user (all terms, includes concluded)
    # include[]=grades ensures the grades sub-object is populated.
    # state[]=active&state[]=completed pulls both current and prior-term enrollments.
    all_enrollments = client.get_user_enrollments(
        USER_ID,
        params={"state[]": ["active", "completed"]},
    )
    print(f"Retrieved grades for {len(all_enrollments)} enrollments.")

    # Build a lookup: course_id -> enrollment grades object
    enrollment_by_course: dict = {}
    for enr in all_enrollments:
        cid = str(enr.get("course_id"))
        if cid not in enrollment_by_course:
            enrollment_by_course[cid] = enr

    # [220] Fetch per-grading-period (Q1, Q2, …) grades for each core course
    print("\n--- Fetching Grading Periods & Quarter Grades ---")
    grades_by_course: dict = {}
    for label, cid in zip(labels, course_ids):
        grading_periods = client.get_grading_periods(cid)
        period_grades: dict = {}

        for period in grading_periods:
            pid = period["id"]
            title = period["title"]
            # Enrollments filtered to a grading period return per-period grades
            period_enrollments = client.get_enrollments(
                cid,
                params={
                    "user_id": USER_ID,
                    "grading_period_id": pid,
                    "include[]": "grades",
                    "per_page": 100,
                },
            )
            if period_enrollments:
                g = period_enrollments[0].get("grades", {})
                period_grades[title] = {
                    "current_score": g.get("current_score"),
                    "final_score": g.get("final_score"),
                    # letter grades are non-null only when course has a grading scheme
                    "current_grade": g.get("current_grade"),
                    "final_grade": g.get("final_grade"),
                }
            else:
                period_grades[title] = None

        # Overall grade from the user's enrollment record
        overall = enrollment_by_course.get(cid, {}).get("grades", {})
        grades_by_course[label] = {
            "overall": {
                "current_score": overall.get("current_score"),
                "final_score": overall.get("final_score"),
                "current_grade": overall.get("current_grade"),
                "final_grade": overall.get("final_grade"),
            },
            "by_period": period_grades,
        }
        print(f"  {label}: {len(grading_periods)} grading period(s) found.")

    combined["grades"] = grades_by_course

    # Re-save consolidated data with grades included
    with open('combined_json', 'w') as f:
        json.dump(combined, f, indent=4)
    print("\nGrades added to 'combined_json'")

except CanvasAPIError as e:
    print(f"\nAn API error occurred: {e}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
