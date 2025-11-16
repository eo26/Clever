# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 20:28:38 2025

@author: eleib
"""

#/--------------------------------------------------------------------------------------------------
# USEFUL LINKS AND RESOURCES
#/--------------------------------------------------------------------------------------------------

# https://developerdocs.instructure.com/services/catalog/openapi/users
# https://developerdocs.instructure.com/services/datasync/grades-oas


#/--------------------------------------------------------------------------------------------------
# IMPORTS
#/--------------------------------------------------------------------------------------------------
import requests
import json

#/--------------------------------------------------------------------------------------------------
# CONSTANTS
#/--------------------------------------------------------------------------------------------------
# [000] Establish credentials
# Replace with your actual Canvas info
# how did I figure out Ethan's access token?
# for each school district will need an easy way to populate the base URL, just start with Broward for now
ACCESS_TOKEN = "1773~BNxkQuBnxcZ2BDPEQNAJ2fnvQYG2LMHEUPnfnKBvykFJeXMX7nQ76HLCZtNhz4nA"
BASE_URL = "https://browardschools.instructure.com"
#USER_ID =  483270
#TERM_ID = "3133"
#ACCOUNT_ID=278


headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
params = {"per_page": 100}

#/--------------------------------------------------------------------------------------------------
# FUNCTIONS
#/--------------------------------------------------------------------------------------------------
def update_endpoints_dict(USER_ID=67, COURSE_ID=123):
    return {"user_info": f"api/v1/users/{USER_ID}",
            "user_self": f"api/v1/users/self",
            "courses":f"api/v1/courses",
            "course_grades": f"api/v1/users/{USER_ID}/enrollments",
            "submission_grades": f"api/v1/courses/{COURSE_ID}/students/submissions",
            "assignments": f"api/v1/courses/{course_id}/assignments",
            "enrollments": f"api/v1/courses/{COURSE_ID}/enrollments"}    

def get_all_pages(url):
    """Generic helper function to get all pages from Canvas API"""
    all_items = []
    while url:
        response = requests.get(url, headers=headers)
        all_items.extend(response.json())
        url = response.links.get('next', {}).get('url')
    return all_items

def call_endpoint(endpoint, params):
    response = requests.get(f"{BASE_URL}/{endpoint}", headers=headers,params=params)
    response.raise_for_status()
    return response.json()

def get_all_enrollments(course_id):
    ''' function to iterate and consolidate pagination of api'''
    all_enrollments = []
    url = f"{BASE_URL}/api/v1/courses/{course_id}/enrollments?per_page=100"
    
    while url:
        response = requests.get(url, headers=headers)
        all_enrollments.extend(response.json())
                
        # Extract next URL from Link header
        links = response.links
        url = links['next']['url'] if 'next' in links else None    
    return all_enrollments

def filter_enrollments(all_enrollments):
    ''' filter the total student enrollments for a class to just those is the user's section'''
    user = list(filter(lambda record: record.get('user_id') == USER_ID, enrollments))[0]
    course_section = user.get('course_section_id')  

    # COURSE SECTION ID IS THE ACTUAL CLASS THAT THE USER STUDENT IS PART OF SO CAN GRAB IT AND THEN QUERY FOR PARTICULAR CLASS
    classmates=[]
    for s in enrollments:
        if s['course_section_id'] == course_section and s['enrollment_state'] == 'active':
            classmates.append(s['user']['sortable_name'])
    return classmates
    
def get_assignments(course_id):
    assignments_url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments?per_page=100"
    assignments = get_all_pages(assignments_url)
    
    for d in assignments:
        d.pop('secure_params', None) 
        d.pop('description', None)
    
    return assignments


#/--------------------------------------------------------------------------------------------------
# STUDENT INFO
#/--------------------------------------------------------------------------------------------------
# establish initial endpoint dict ithout user_id our course_info
endpoints_dict = update_endpoints_dict()

# [001] Get User Info
user_data = call_endpoint(endpoints_dict.get('user_self'), params)
USER_ID = user_data['id']

#update endpoint dict with the now retrieved user data
endpoints_dict = update_endpoints_dict(USER_ID=USER_ID)

# [010] Get enrolled courses
courses = call_endpoint(endpoints_dict.get('courses'),params)
accessible_courses = [course for course in courses if not course.get("access_restricted_by_date")]

# filter for current year's courses
current_courses = [course for course in courses if course.get("enrollment_term_id")==3133]

# visually inspect course names
for course in current_courses:
    print(f"{course['id']}: {course['name']}")

# [015] Get info about current term
TERM_ID = accessible_courses[0]['enrollment_term_id']

# NO PERMISSIONS for this
#term_info = requests.get(f"{BASE_URL}/api/v1/accounts/1/terms/{TERM_ID}", headers=headers).json()

# [020] See enrolled students for a particular class
# get all students enrolled in a class
enrollments = get_all_enrollments('1964182')

# get specific students in same section as the user
classmates = filter_enrollments(enrollments)

#/--------------------------------------------------------------------------------------------------
# COURSE ASSIGNMENTS INFO
#/--------------------------------------------------------------------------------------------------
# THIS IS WHERE I LEFT OFF 11/12/25
# [110] Get current assignments for a single class
Hist = get_assignments('1964160')
Math = get_assignments('1964103')
Science = get_assignments('1964182')
Technology = get_assignments('1964205') 
English = get_assignments('1963027')

class_list = [Hist,Math,Science,Technology,English]
labels = ['History','Math','Science','Technology','English']

combined = {}

for label,c in zip(labels,class_list):
    combined[label] = c

combined_string = json.dumps(combined, indent = 0)

with open('combined_json','w') as f:
    json.dump(combined,f)

for a in assignments:
    print(f"{a['name']} - Due: {a['due_at']}")

#/--------------------------------------------------------------------------------------------------
    
# [210] Retrieve course grades
course_grades_data = call_endpoint(endpoints_dict.get('course_grades'),params)


# [260] Retrieve submissions grades
submissions_params = {
    "student_ids[]": "self",  # "self" = current student
    "include[]": ["assignment", "rubric_assessment", "submission_comments"],
    "per_page": 100}

# !!!be sure to run the endpoints dictionary after entering the correct COURSE_ID
data_submission_grades = call_endpoint(endpoints_dict.get('submission_grades'),submissions_params)


# haven't started on this yet
response = requests.get(
    "https://api.us2.kimonocloud.com/v2/grades/exchanges",
    headers={"Authorization":ACCESS_TOKEN,"Accept":"*/*"},
)
dataG = response.json()


# new attempt 11/2/25
# Get a specific submission with full details
course_id = "1964160"
assignment_id = "48611645"

response = requests.get(
    f"{BASE_URL}/courses/{course_id}/assignments/{assignment_id}/submissions/self",
    headers=headers,
   params={"include[]": ["submission_comments", "rubric_assessment"]})

submission = response.json()

print(f"Score: {submission.get('score')} / {submission.get('assignment', {}).get('points_possible')}")
print(f"Grade: {submission.get('grade')}")
print(f"Graded At: {submission.get('graded_at')}")
print(f"Late: {submission.get('late')}")

GET /api/v1/users/:user_id/enrollments

# Get all assignments for a specific course
course_id = 1964160  # Example: History course

response = requests.get(
    f"{BASE_URL}/courses/{course_id}/assignments",
    headers=headers,
    params={"include[]": ["submission"]}
)

assignments = response.json()

for assignment in assignments:
    print(f"\n{assignment['name']}")
    print(f"  Points Possible: {assignment.get('points_possible')}")
    
    if 'submission' in assignment:
        submission = assignment['submission']
        print(f"  Score: {submission.get('score')}")
        print(f"  Grade: {submission.get('grade')}")
        print(f"  Submitted: {submission.get('submitted_at')}")


