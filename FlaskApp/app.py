from flask import Flask, jsonify, request 

from __init__ import db, login_manager
# from views import view

app = Flask(__name__)

# Routing
# app.register_blueprint(view)


# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{username}:{password}@{host}:{port}/{database}'\
    .format(
        username='postgres',
        password='password',
        host='localhost',
        port=5432,
        database='postgres'
    )
app.config['SECRET_KEY'] = 'A random key to use CRF for forms'

# Initialize other components
db.init_app(app)
login_manager.init_app(app)

coursesJson = {'course':['cs2102','cs1020']}

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
    return 'Logged in'


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