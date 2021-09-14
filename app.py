from flask import Flask, request, jsonify, session as _s, abort
from flask_sqlalchemy import SQLAlchemy
# postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
import psycopg2

# end of postgres
from sqlalchemy.orm import backref, relationship
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_marshmallow import Marshmallow
from flask_cors import CORS, cross_origin
import sys
from sqlalchemy.sql.schema import ForeignKey

from werkzeug.utils import redirect
print("this is where my packages are", sys.path)


app = Flask(__name__)
CORS(app)

database_url = 'postgresql+psycopg2://postgres:liveurlife@localhost:5432/postgres'

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///question.db'
app.config['SECRET_KEY'] = 'mysecret'
db = SQLAlchemy(app)
ma = Marshmallow(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
admin = Admin(app)



@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': Users}

# Postgresql
Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(60))
    password = Column(String(25))
    is_admin = Column(Boolean, default=False)
    questions = relationship('Question', backref='user')
    answer = relationship('Answer', backref='user')

    def __str__(self) -> str:
        return self.username


class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    answer = relationship('Question', backref='subject')

    def __str__(self) -> str:
        return self.name

class Question(Base):
    __tablename__ = 'question'
    id = Column(Integer, primary_key=True)
    qtn = Column(String(100))
    subject_id = Column(Integer, ForeignKey('subject.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    answers = relationship('Answer',backref='question')

    def __str__(self) -> str:
        return self.qtn

class Answer(Base):
    __tablename__ = 'answer'
    id = Column(Integer, primary_key=True)
    ans = Column(String(50))
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('question.id'))

    def __str__(self) -> str:
        return self.ans
Base.metadata.create_all(engine)

# class Users(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(60))
#     password = db.Column(db.String(25))
#     authenticated = db.Column(db.Boolean, default=False)
#     is_admin = db.Column(db.Boolean, default=False)
#     questions = db.relationship('Question', backref='user')
#     answer = db.relationship('Answer', backref='user')

#     def __str__(self) -> str:
#         return self.username

# class Subject(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100))
#     questions = db.relationship('Question', backref='subject')

#     def __str__(self) -> str:
#         return self.name



# class Question(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     qtn = db.Column(db.String(150))
#     subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     answers = db.relationship('Answer', backref='question')


#     def __str__(self) -> str:
#         return self.qtn

# class Answer(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     ans = db.Column(db.String(100))
#     question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#     def __str__(self) -> str:
#         return self.ans

class QuestionSchema(ma.Schema):
    class Meta:
        fields = ('id', 'qtn', 'subject_id', 'answers')
question_schema = QuestionSchema()
questions_schema = QuestionSchema(many=True)


# admin.add_view(ModelView(Users, db.session))
# admin.add_view(ModelView(Subject, db.session))
# admin.add_view(ModelView(Question, db.session))
# admin.add_view(ModelView(Answer, db.session))
admin.add_view(ModelView(Users, session))
admin.add_view(ModelView(Subject, session))
admin.add_view(ModelView(Question, session))
admin.add_view(ModelView(Answer, session))

def check_user_login(username, password):
    # user = Users.query.filter_by(username=username).filter_by(password=password).first()
    user = session.query(Users).filter_by(username=username).filter_by(password=password).first()

    return user

def check_if_admin(username, password):
    user = check_user_login(username=username, password=password)
    return user.is_admin



@app.route('/add', methods=['POST'])
def post_question():
    username = request.headers['username']
    password = request.headers['password']
    user = session.query(Users).filter_by(username=username).filter_by(password=password).first()
    # user = check_user_login(username, password)
    if not user and user.is_admin == True:
        return abort(403)

    if request.method == 'POST':

        question = request.json['qtn']
        print(question)
        subject_id = request.json['subject_id']
        user_id = user.id
        print("user_id", user_id)

        
        new_attempt = Question(qtn=question, subject_id=subject_id, user_id=user_id)
        # print("this is new: ", type(new_attempt))
        try:
            print("attempting to add to db")
            session.add(new_attempt)
            print("i adding has passed")
            print("moving on to committing")
            session.commit()
            print("committing has passed")
        except:
            return "there was a problem committing the data"
        new_f = dict()
        new_f['qtn'] = new_attempt.qtn
        new_f['sub_id'] = new_attempt.subject_id
        resp = jsonify(new_f)
        return resp


@app.route('/qtn')
def get_all_qtn():
    # qtn = Question.query.all()
    qtn = session.query(Question)
    all_items = []
    # print("this is qtn: ", qtn)
    for ja in qtn:
        qtn_all = dict()
        qtn_all['id'] = ja.id
        qtn_all['qtn'] = ja.qtn
        qtn_all['subject_id'] = ja.subject_id
        ansa = []
        for joe in ja.answers:
            print("this are answers", joe.user.username)
            anss = dict()
            anss['id'] = joe.id
            anss['ans'] = joe.ans
            anss['user'] = joe.user.username
            anss['q_id'] = joe.question_id
            ansa.append(anss)
        qtn_all['answer'] = ansa
        all_items.append(qtn_all)
    return jsonify(all_items)

@app.route('/qtn/<int:id>')
def get_question(id):
    # qtn = Question.query.filter_by(id=id).first()
    qtn = session.query(Question).filter_by(id=id).first()
    if qtn:
        result = dict()
        result['id'] = qtn.id
        result['qtn'] = qtn.qtn
        result['subject_id'] = qtn.subject_id
        return jsonify(result)
    return "there is no question with that id"

@app.route('/qtn/<int:id>/update', methods=['PUT'])
def update(id):
    username = request.headers['username']
    password = request.headers['password']
    user = check_user_login(username, password)
    if user and user.is_admin == False:
        return abort(403)
    # qtn = Question.query.filter_by(id=id).first()
    qtn = session.query(Question).filter_by(id=id).first()
    if qtn:
        qtn.qtn = request.json['qtn']
        qtn.subject_id = request.json['subject_id']
        session.merge(qtn)
        session.commit()
        # db.session.merge(qtn)
        # db.session.commit()
        return jsonify("the data is successfully updated")
    return "theres no object with that id"
    
@app.route("/qtn/<int:id>/delete", methods=['DELETE'])
def delete(id):
    user = check_if_admin
    if user:
        qtn = session.query(Question).filter_by(id=id).first()
        if qtn:
            session.delete(qtn)
            session.commit()
            return jsonify("item has successfully been deleted")
        return jsonify("select an object")


@app.route("/subjects", methods=['GET'])
def get_all_subjects():
    subjects = session.query(Subject)
    # print("this are subjects: ", subjects)
    list_of_subjects = []
    for subject in subjects:
        subb = dict()
        subb['id'] = subject.id
        subb['name'] = subject.name
        list_of_subjects.append(subb)
    return jsonify(list_of_subjects)

@app.route("/register", methods=['POST'])
def register():
    # username = request.form.get('username').lower().strip
    username = request.headers['username']
    password = request.headers['password']
    confirm_password = request.headers['confirm_password']
    response = dict()
    if password != confirm_password:
        response['code'] = 403
        # response['errorMsg'] = "your passwords dont match"
        return jsonify(response)
    # all_user = Users.query.all()
    all_user = session.query(Users)
    print("this are all: ",all_user)
    # user = Users.query.filter_by(username=username).first()
    user = session.query(Users).filter_by(username=username).first()
    print("this is user: ", user)
    if user:
        response['code'] = 409
        return jsonify(response)
    entry = Users(username=username, password=password)
    session.add(entry)
    session.commit()
    response['username'] = entry.username
    response['is_admin'] = entry.is_admin
    response['code'] = 200
    _s['user_session'] = entry.username
    return jsonify(response)
    # return redirect("/qnt")



@app.route('/login', methods=['POST'])
def login():
    username = request.headers['username']
    password = request.headers['password']
    print("username: ", username)
    # user = Users.query.filter_by(username=username).first()
    user = session.query(Users).filter_by(username=username).first()
    print("this is user: ", user)
    if not user or user.password != password:
        print("wrong credentials")
        return jsonify("you credentials are wrong"), 403
    _s['user_session'] = user.username

    print("user loged in successfully")
    user_dic = dict()
    user_dic['username'] = user.username
    user_dic['is_admin'] = user.is_admin
    user_dic['password'] = user.password
    user_dic['code'] = 200
    print(user_dic)
    return jsonify(user_dic), 200

@app.route('/answer', methods=['POST'])
def post_answer():
    username = request.headers['username']
    password = request.headers['password']
    user = check_user_login(username, password)

    if not user:
        return abort(403)
    
    if user:
        answer = request.json['ans']
        question_id = request.json['question_id']
        user_id = user.id

    if len(answer) < 1:
        return jsonify(abort(411))
    # user = Users.query.filter_by(id=user_id).first()
    # if not user:
    #     return jsonify(abort(204))
    question = session.query(Question).filter_by(id=question_id).first()
    
    if not question:
        return jsonify(abort(204))
    question_ans = question.answers
    print("this are questions: ", question_ans)
    for i in question_ans:
        if i.user.username == username:
            i.ans = request.json['ans']
            session.merge(i)
            session.commit()
            return jsonify("answer marged successfully")
    question_entry = Answer(ans=answer, question_id=question_id, user_id=user_id)
    session.add(question_entry)
    session.commit()
    return jsonify("ansers have been  submited")

@app.route('/logout')
def logout():
    _s['user_session'] = ''
    return jsonify("you are loged out")



if __name__ == "__main__":
    app.run(debug=True)
    # db.create_all()
    # @app.before_first_request
    # def create_tables():
    #     db.create_all()