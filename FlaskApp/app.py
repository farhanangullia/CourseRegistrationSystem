from flask import Flask, jsonify, request 
from flask_cors import CORS, cross_origin

from __init__ import db, login_manager
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

# from views import view

app = Flask(__name__)

CORS(app)

# Routing
# app.register_blueprint(view)


# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{username}:{password}@{host}:{port}/{database}'\
    .format(
        username='postgres',
        password='password',
        host='localhost',
        port=5432,
        database='crsdb'
    )
app.config['SECRET_KEY'] = 'A random key to use CRF for forms'

# Initialize other components
db.init_app(app)
login_manager.init_app(app)

coursesJson = {'course':['cs2102','cs1020']}


# For resultproxy = db_session.execute(query)
# d, a = {}, []
# for rowproxy in resultproxy:
#     # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
#     for column, value in rowproxy.items():
#         # build up the dictionary
#         d = {**d, **{column: value}}
#     a.append(d)

# For resultproxy = db_session.execute(query).fetchone()
# d = {}
# for column, value in rowproxy.items():
#         # build up the dictionary
#   d = {**d, **{column: value}}

@app.route('/getCourses', methods=['GET'])
def get_courses():

    return jsonify(coursesJson)


@app.route("/login", methods=["POST"])
def login():
    req_data = request.get_json()
    accountid = req_data['accountid']
    password = req_data['password']
    print("checking db for login")
    # query = "SELECT * FROM users WHERE uname = '{}' AND pass = '{}'".format(username,password)
    query = "SELECT AC.accountID, CASE WHEN EXISTS(SELECT 1 FROM administrators a WHERE a.accountid = AC.accountid) THEN 'admin' WHEN EXISTS(SELECT 1 FROM students s WHERE s.accountid = AC.accountid) THEN 'student' ELSE 'teacher' END AS Type FROM accounts AC WHERE AC.accountid = '{}' AND AC.password = '{}';".format(accountid,password)
    user = db.session.execute(query).fetchone()
    print(user)
    d = {}
    # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
    for column, value in user.items():
        # build up the dictionary
        d = {**d, **{column: value}}
    print(d)
    return jsonify(d)


@app.route("/retrieveCoursesForRegistration", methods=["POST"])
def retrieveCoursesForRegistration():
    req_data = request.get_json()
    accountid = req_data['accountid']
    print(req_data)
    print("retrieveCoursesForRegistration")
    query = """SELECT moduleCode, name, currentSize, quota
FROM Courses C
WHERE CURRENT_DATE <= (SELECT registrationDeadline FROM CurrentAY)
AND
(EXISTS (SELECT 1 FROM Teaches T WHERE C.moduleCode = T.moduleCode AND T.year = (SELECT year FROM CurrentAY) AND T.semNum = (SELECT semNum FROM CurrentAY)))
AND
(NOT EXISTS (SELECT 1
FROM (SELECT * FROM Completed WHERE '{0}' = Completed.accountID) AS Cm RIGHT JOIN Prerequisites P
ON Cm.moduleCode = P.prereq
WHERE C.moduleCode = P.moduleCode
AND Cm.accountID IS NULL))
AND
(C.moduleCode NOT IN (SELECT moduleCode FROM Completed WHERE '{0}' = Completed.accountID))
AND (SELECT isGraduate FROM Students WHERE '{0}' = Students.accountID) = C.isGraduateCourse;
""".format(accountid)
    courses = db.session.execute(query)
    # print(courses)
    d, a = {}, []
    for rowproxy in courses:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    # print(a)
    return jsonify(a)

@app.route("/registerCourse", methods=["POST"])
def registerCourse():
    req_data = request.get_json()
    accountid = req_data['accountid']
    modulecode = req_data['modulecode']
    print("registerCourse")
    # query = "SELECT * FROM users WHERE uname = '{}' AND pass = '{}'".format(username,password)
    # add_enrollment(id varchar(50), mod varchar(50))
    try:
        result = db.session.execute("SELECT switch_to_new_semester({},{})".format(x,y)).fetchone()
        query = "SELECT * FROM courses;"
        courses = db.session.execute(query)
        print(courses)
    except SQLAlchemyError as e:
        print("ERROR")
        print(e)
   
    



@app.route("/testSP", methods=["GET"])
def testSP():
    x = 2019
    y = 1
    try:
        result = db.session.execute("SELECT switch_to_new_semester({},{})".format(x,y)).fetchone()
        print(result)
        print("success")
    except SQLAlchemyError as e:
        print("ERROR")
        print(e)


# query parameters for GET
# @app.route("/login", methods=["GET"])
# def login():
#     username  = request.args.get('username', None)
#     password  = request.args.get('password', None)
#     query = "SELECT * FROM web_user WHERE username = '{}'".format(username)
#     exists_user = db.session.execute(query).fetchone()


if __name__ == "__main__":
    app.run(
        debug=True,
        host='localhost',
        port=5000
    )