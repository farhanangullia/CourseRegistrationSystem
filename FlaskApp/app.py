from flask import Flask, jsonify, request 
from flask_cors import CORS, cross_origin

from __init__ import db, login_manager
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import create_session
from sqlalchemy import create_engine
from sqlalchemy import text

app = Flask(__name__)

CORS(app)



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
    query = """SELECT moduleCode, name, departmentID, currentSize, quota
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
AND (SELECT isGraduate FROM Students WHERE '{0}' = Students.accountID) = C.isGraduateCourse;""".format(accountid)
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
    print(accountid)
    print(modulecode)

    try:

        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("CALL add_enrollment('{}', '{}');".format(accountid,modulecode))
        cursor.close()
        conn.commit()


        
        return jsonify({"status":"success"})
    except SQLAlchemyError as e:
        print("ERROR")
        print(e)
        response = jsonify({"error":e})
   
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/retrieveMyStudentCourses", methods=["POST"])
def retrieveMyStudentCourses():
    req_data = request.get_json()
    accountid = req_data['accountid']
    print(req_data)
    print("retrieveMyStudentCourses")
    query = "SELECT moduleCode,name,departmentID,currentSize,quota FROM Attends NATURAL JOIN courses WHERE accountid = '{}';".format(accountid)
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


@app.route("/retrieveBypassRequests", methods=["POST"])
def retrieveBypassRequests():
    req_data = request.get_json()
    accountid = req_data['accountid']
    print(req_data)
    print("retrieveMyStudentCourses")
    query = """WITH P AS
(SELECT accountID AS studentID, departmentID, year * (100 / (1 + count(moduleCode))) AS n
FROM Students NATURAL LEFT JOIN Attends
GROUP BY accountID, year)
SELECT Bypasses.studentID, moduleCode, name AS moduleName, currentSize, quota, n * (CASE WHEN Courses.departmentID = P.departmentID THEN 2 ELSE 1 END) AS priority
FROM Bypasses NATURAL JOIN Courses INNER JOIN P ON Bypasses.studentID = P.studentID
WHERE isBypassed IS NULL AND '{}' = Bypasses.adminID
ORDER BY priority DESC;""".format(accountid)
    bypassRequests = db.session.execute(query)
    # print(courses)
    d, a = {}, []
    for rowproxy in bypassRequests:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    # print(a)
    return jsonify(a)

@app.route("/updateBypassRequest", methods=["POST"])
def updateBypassRequest():
    req_data = request.get_json()
    studentid = req_data['studentid']
    isBypassed = req_data['isBypassed']
    modulecode = req_data['modulecode']
    print(req_data)
    print("updateBypassRequest")
    
    query = """UPDATE Bypasses SET isBypassed = {} WHERE '{}'= Bypasses.studentID AND '{}' = Bypasses.moduleCode;""".format(isBypassed,studentid,modulecode)
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()
    conn.commit()
    response = jsonify({"status":"success"})
    return response

@app.route("/retrieveStudentProfile", methods=["POST"])
def retrieveStudentProfile():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = "SELECT * FROM Students WHERE accountID = '{}';".format(accountid)
    profile = db.session.execute(query).fetchone()
    print(profile)
    d = {}
    # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
    for column, value in profile.items():
        # build up the dictionary
        d = {**d, **{column: value}}
    print(d)
    return jsonify(d)

@app.route("/retrieveStudentClasses", methods=["POST"])
def retrieveStudentClasses():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = """SELECT 'Student' AS role, classID, Teaches.moduleCode, Teachers.name, roomID
FROM ((Teachers INNER JOIN Teaches ON Teachers.accountID = Teaches.teacherID) NATURAL JOIN CurrentAY) INNER JOIN Attends ON Teaches.moduleCode = Attends.moduleCode
WHERE '{0}' = Attends.accountID
UNION
SELECT 'Teaching assistant' AS role, classID, Teaches.moduleCode, Teachers.name, roomID
FROM ((Teachers INNER JOIN Teaches ON Teachers.accountID = Teaches.teacherID) NATURAL JOIN CurrentAY) INNER JOIN TA ON Teaches.moduleCode = TA.moduleCode
WHERE '{0}' = TA.accountID;""".format(accountid)
    classes = db.session.execute(query)
    d, a = {}, []
    for rowproxy in classes:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return jsonify(a)

@app.route("/retrieveStudentCompletedModules", methods=["POST"])
def retrieveStudentCompletedModules():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = "SELECT moduleCode, name FROM Completed NATURAL JOIN Courses WHERE accountId = '{}';".format(accountid)
    completedModules = db.session.execute(query)
    d, a = {}, []
    for rowproxy in completedModules:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return jsonify(a)


@app.route("/retrieveAdminProfile", methods=["POST"])
def retrieveAdminProfile():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = "SELECT accountID, name, (SELECT year FROM CurrentAY), (SELECT semNum FROM CurrentAY)  FROM Administrators WHERE accountID = '{}';".format(accountid)
    profile = db.session.execute(query).fetchone()
    print(profile)
    d = {}
    # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
    for column, value in profile.items():
        # build up the dictionary
        d = {**d, **{column: value}}
    print(d)
    return jsonify(d)

@app.route("/retrieveAdminCourses", methods=["POST"])
def retrieveAdminCourses():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = "SELECT moduleCode, name, departmentID FROM Courses WHERE adminID = '{}';".format(accountid)
    admincourses = db.session.execute(query)
    d, a = {}, []
    for rowproxy in admincourses:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return jsonify(a)

@app.route("/retrieveTeacherProfile", methods=["POST"])
def retrieveTeacherProfile():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = "SELECT * FROM Teachers WHERE '{}' = Teachers.accountID;".format(accountid)
    profile = db.session.execute(query).fetchone()
    print(profile)
    d = {}
    # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
    for column, value in profile.items():
        # build up the dictionary
        d = {**d, **{column: value}}
    print(d)
    return jsonify(d)


@app.route("/retrieveTeacherCourses", methods=["POST"])
def retrieveTeacherCourses():
    req_data = request.get_json()
    accountid = req_data['accountid']
    query = "SELECT moduleCode, name, semnum, year FROM Teaches NATURAL JOIN Courses WHERE teacherid = '{}';".format(accountid)
    teachercourses = db.session.execute(query)
    d, a = {}, []
    for rowproxy in teachercourses:
        # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
        for column, value in rowproxy.items():
            # build up the dictionary
            d = {**d, **{column: value}}
        a.append(d)
    return jsonify(a)


@app.route("/updateCurrentAY", methods=["POST"])
def updateCurrentAY():
    print("updateCurrentAY")
    
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("CALL switch_to_new_semester();")
        cursor.close()
        conn.commit()

        return jsonify({"status":"success"})
    except SQLAlchemyError as e:
        print("ERROR")
        print(e)
        response = jsonify({"error":e})
   
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

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




if __name__ == "__main__":
    app.run(
        debug=True,
        host='localhost',
        port=5000
    )