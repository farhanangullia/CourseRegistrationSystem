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
    print(accountid)
    print(modulecode)
    # query = "SELECT * FROM users WHERE uname = '{}' AND pass = '{}'".format(username,password)
    # add_enrollment(id varchar(50), mod varchar(50))
    
    try:
        print("debug 1")
        # method 1
        # db.session.execute(text("CALL add_enrollment(:param,:param2)"), {"param":accountid,"param2":modulecode})
        # method 2 Not working
        # db.session.execute("CALL add_enrollment('{}','{}')".format(accountid,modulecode))
        # db.engine.raw_connection().commit()


        # method 3
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("CALL add_enrollment('{}', '{}');".format(accountid,modulecode))
        cursor.close()
        conn.commit()

        # # do the call. The actual parameter does not matter, could be ['lala'] as well
        # results = conn.cursor().callproc('add_enrollment', ['e12348','FC101'])
        # conn.close()   # commit

        # conn.cursor().execute("CALL switch_to_new_semester(2021, 1);")


        # print(results) # will print (<out param result>)
        print("debug 2")
        # query = "SELECT * FROM courses;"
        # courses = db.session.execute(query)
        # print(result)
        
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
    query = "SELECT moduleCode,name,currentSize FROM Attends NATURAL JOIN courses WHERE accountid = '{}';".format(accountid)
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
(SELECT accountID AS studentID, year * count(*) AS priority
FROM Students NATURAL LEFT JOIN Completed
GROUP BY accountID, year)
SELECT studentID, moduleCode, name AS moduleName, currentSize, quota, priority
FROM Bypasses NATURAL JOIN Courses NATURAL JOIN P
WHERE isBypassed IS NULL AND '{}'= Bypasses.adminID
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
    print(req_data)
    print("updateBypassRequest")
    query = """UPDATE Bypasses SET isBypassed = {} WHERE '{}'= Bypasses.studentID;""".format(isBypassed,studentid)
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()
    conn.commit()
    response = jsonify({"status":"success"})
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