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
    username = req_data['username']
    password = req_data['password']
    print("checking db for login")
    query = "SELECT * FROM users WHERE uname = '{}' AND pass = '{}'".format(username,password)
    exists_user = db.session.execute(query).fetchone()
    print(exists_user)
    d = {}
    # rowproxy.items() returns an array like [(key0, value0), (key1, value1)]
    for column, value in exists_user.items():
        # build up the dictionary
        d = {**d, **{column: value}}
    print(d)
    return jsonify(d)



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