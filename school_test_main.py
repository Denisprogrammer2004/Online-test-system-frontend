import sys
import werkzeug
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask import Flask, render_template, redirect, request, abort, jsonify
#from data import db_session
from test_selection_form import SelectTestForm
from display_test_question_form import DisplayTestForm
from test_result_form import TestResultForm
from requests import get, post, delete, put
from user import User
from datetime import datetime
from flask import make_response
from loginform import LoginForm
from register_form import RegisterForm
from teacher_main_form import TeacherForm
from add_test_form import AddTestForm
from add_question_form import AddQuestionForm
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


login_manager = LoginManager()
login_manager.init_app(app)

backend = ""


@app.route('/',  methods=['GET', 'POST'])
@login_required
def index():
    tsts = get("http://{}:8080/api/tests".format(backend)).json()
    form = SelectTestForm()
    form.tests.choices = [(item["id"], item["name"]) for item in tsts["tests"]]
    if form.validate_on_submit():
        test_id = form.tests.data
        test = None
        for tst in tsts["tests"]:
            tst_id = tst["id"]
            if tst_id == test_id:
                test = tst
                break
        if test is None:
            return redirect('/')
        if not test["questions"]:
            abort(404, message=f"Test {test_id} not found")
        post("http://{}:8080/api/test_results".format(backend),
             json={
                 "test_id": test_id,
                 "student_id": current_user.id,
                 "score": 0})
        results = get("http://{}:8080/api/test_results".format(backend)).json()
        test_result_id = 0
        for item in results["test_results"]:
            if item["test_id"] == test_id and item["student_id"] == current_user.id:
                test_result_id = item["id"]
        return redirect('/tests/questions/{}/{}/{}'.format(test_id, test["questions"][0]["id"], test_result_id))
    return render_template("test_selection.html", title='Выбор теста',
                           form=form)


@login_manager.user_loader
def load_user(user_id):
    result = get("http://{}:8080/api/users/{}".format(backend, user_id)).json()
    user = None
    if result:
        user = User()
        user.id = result["user"]["id"]
        user.name = result["user"]["name"]
        user.is_teacher = result["user"]["is_teacher"]
    return user


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        result = get("http://{}:8080/api/users".format(backend)).json()
        for item in result["users"]:
            if item["email"] == form.email.data and \
                    werkzeug.security.check_password_hash(item["hashed_password"], form.password.data):
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Такой пользователь уже есть")
        post("http://{}:8080/api/users".format(backend),
             json={
                 "name": form.name.data,
                 "email": form.email.data,
                 "hashed_password": werkzeug.security.generate_password_hash(form.password.data),
                 "group": form.group.data,
                 "is_teacher": form.is_teacher.data})
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = get("http://{}:8080/api/users".format(backend)).json()
        for item in result["users"]:
            if item["email"] == form.email.data and \
                    werkzeug.security.check_password_hash(item["hashed_password"], form.password.data):
                user = User()
                user.id = item["id"]
                user.name = item["name"]
                user.is_teacher = item["is_teacher"]
                login_user(user, remember=form.remember_me.data)
                if user.is_teacher:
                    return redirect("/tests")
                return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)

    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/tests/questions/<int:test_id>/<int:question_id>/<int:test_result_id>',  methods=['GET', 'POST'])
@login_required
def answer_questions(test_id, question_id, test_result_id):
    print(test_result_id)
    tst = get("http://{}:8080/api/tests/{}".format(backend, test_id)).json()
    question = None
    for qst in tst["test"]["questions"]:
        qst_id = qst["id"]
        if question_id == qst_id:
            question = qst
            break
    if question is None:
        return redirect('/test_results/{}'.format(test_result_id))
    form = DisplayTestForm()
    form.options.choices = [(item["id"], item["text"]) for item in question["options"]]
    if form.validate_on_submit():
        test_ids = form.options.data
        lst_of_true = []
        for opt in question["options"]:
            if opt["is_correct"]:
                lst_of_true.append(opt["id"])
        if test_ids == lst_of_true:
            print('Зачисляем {} баллов'.format(question["score"]))
            result = get("http://{}:8080/api/test_results/{}".format(backend, test_result_id)).json()
            put("http://{}:8080/api/test_results/{}".format(backend, test_result_id),
                 json={"test_id": result["test_result"]["test_id"], "student_id": result["test_result"]["student_id"],
                       "score": result["test_result"]["score"] + question["score"]})
        return redirect('/tests/questions/{}/{}/{}'.format(test_id, question_id + 1, test_result_id))
    return render_template("answer_question.html", title='Вопрос № {}'.format(question_id),
                           question=question["question_text"], form=form)


@app.route('/tests', methods=['GET', 'POST'])
@login_required
def tests():
    tsts = get("http://{}:8080/api/tests".format(backend)).json()
    results = get("http://{}:8080/api/test_results".format(backend)).json()
    form = TeacherForm()
    form.tests.choices = [(item["id"], item["name"]) for item in tsts["tests"]]
    if form.validate_on_submit():
        if form.add_test.data:
            return redirect("/tests/add")
        elif form.edit_test.data:
            test_id = form.tests.data
            return redirect("/tests/edit/{}".format(test_id))

    return render_template('teacher_main.html', title='Информация о тестах', form=form, results=results)


@app.route('/tests/add', methods=['GET', 'POST'])
@login_required
def tests_add():
    form = AddTestForm()
    if form.validate_on_submit():
        post("http://{}:8080/api/tests".format(backend),
             json={
                 "name": form.name.data,
                 "subject": form.subject.data,
                 "group": form.group.data,
                 "teacher_name": current_user.name})
        results = get("http://{}:8080/api/tests".format(backend)).json()
        for item in results["tests"]:
            if item["name"] == form.name.data and \
               item["subject"] == form.subject.data and \
               item["group"] == form.group.data and \
               item["teacher"]["name"] == current_user.name:
                test_id = item["id"]
                return redirect("/tests/add_question/{}".format(test_id))
    return render_template('add_test.html', title='Информация о тестe', form=form)


@app.route('/tests/add_question/<int:test_id>',  methods=['GET', 'POST'])
@login_required
def add_questions(test_id):
    tst = get("http://{}:8080/api/tests/{}".format(backend, test_id)).json()
    form = AddQuestionForm()
    if form.validate_on_submit():
        tst["test"]["questions"].append({"question_text": form.question.data, "score": form.score.data, "options": []})
        options = tst["test"]["questions"][-1]["options"]
        if form.option1.data:
            options.append({"text": form.option1.data, "is_correct": str(form.option1_chb.data)})
        if form.option2.data:
            options.append({"text": form.option2.data, "is_correct": str(form.option2_chb.data)})
        if form.option3.data:
            options.append({"text": form.option3.data, "is_correct": str(form.option3_chb.data)})
        if form.option4.data:
            options.append({"text": form.option4.data, "is_correct": str(form.option4_chb.data)})
        if form.option5.data:
            options.append({"text": form.option5.data, "is_correct": str(form.option5_chb.data)})
        tst["test"]["teacher_name"] = tst["test"]["teacher"]["name"]
        print("after", tst)
        put("http://{}:8080/api/tests/{}".format(backend, test_id), json=tst["test"])
        if form.add_quest.data:
            return redirect("/tests/add_question/{}".format(test_id))
        elif form.complete_quest.data:
            return redirect("/tests")
    return render_template("add_question.html", title='Добавить вопрос', form=form)


@app.route('/tests/edit/<int:test_id>', methods=['GET', 'POST'])
@login_required
def tests_edit(test_id):
    form = AddTestForm()
    form.add_test.label.text = "Изменить"
    tst = get("http://{}:8080/api/tests/{}".format(backend, test_id)).json()
    if request.method == "GET":
        form.name.data = tst["test"]["name"]
        form.group.data = tst["test"]["group"]
        form.subject.data = tst["test"]["subject"]
    if form.validate_on_submit():
        put("http://{}:8080/api/tests/{}".format(backend, test_id),
             json={
                 "name": form.name.data,
                 "subject": form.subject.data,
                 "group": form.group.data,
                 "teacher_name": current_user.name,
                 "questions": tst["test"]["questions"]})
        question_id = tst["test"]["questions"][0]["id"]
        return redirect("/tests/edit_question/{}/{}".format(test_id, question_id))
    return render_template('add_test.html', title='Информация о тестe', form=form)


@app.route('/tests/edit_question/<int:test_id>/<int:question_id>',  methods=['GET', 'POST'])
@login_required
def edit_questions(test_id, question_id):
    tst = get("http://{}:8080/api/tests/{}".format(backend, test_id)).json()
    question = None
    next_question = None
    for i, item in enumerate(tst["test"]["questions"]):
        if item["id"] == question_id:
            question = item
            if i < len(tst["test"]["questions"]) - 1:
                next_question = tst["test"]["questions"][i + 1]
            break
    form = AddQuestionForm()
    form.add_quest.label.text = "Изменить и перейти к следующему"
    form.complete_quest.label.text = "Изменить и закончить"
    if request.method == "GET":
        form.question.data = question["question_text"]
        form.score.data = question["score"]
        number_of_options = len(question["options"])
        if number_of_options > 0:
            form.option1.data = question["options"][0]["text"]
            form.option1_chb.data = question["options"][0]["is_correct"]
        if number_of_options > 1:
            form.option2.data = question["options"][1]["text"]
            form.option2_chb.data = question["options"][1]["is_correct"]
        if number_of_options > 2:
            form.option2.data = question["options"][2]["text"]
            form.option2_chb.data = question["options"][2]["is_correct"]
        if number_of_options > 3:
            form.option3.data = question["options"][3]["text"]
            form.option3_chb.data = question["options"][3]["is_correct"]
        if number_of_options > 4:
            form.option4.data = question["options"][4]["text"]
            form.option4_chb.data = question["options"][4]["is_correct"]

    if form.validate_on_submit():
        question["question_text"] = form.question.data
        question["score"] = form.score.data
        question["options"].clear()

        if form.option1.data:
            question["options"].append({"text": form.option1.data, "is_correct": str(form.option1_chb.data)})
        if form.option2.data:
            question["options"].append({"text": form.option2.data, "is_correct": str(form.option2_chb.data)})
        if form.option3.data:
            question["options"].append({"text": form.option3.data, "is_correct": str(form.option3_chb.data)})
        if form.option4.data:
            question["options"].append({"text": form.option4.data, "is_correct": str(form.option4_chb.data)})
        if form.option5.data:
            question["options"].append({"text": form.option5.data, "is_correct": str(form.option5_chb.data)})
        tst["test"]["teacher_name"] = tst["test"]["teacher"]["name"]
        put("http://{}:8080/api/tests/{}".format(backend, test_id), json=tst["test"])
        if form.add_quest.data:
            if next_question:
                return redirect("/tests/edit_question/{}/{}".format(test_id, next_question["id"]))
            else:
                return redirect("/tests/add_question/{}".format(test_id))
        elif form.complete_quest.data:
            return redirect("/tests")
    return render_template("add_question.html", title='Изменить вопрос', form=form)


@app.route('/test_results/<int:test_result_id>',  methods=['GET', 'POST'])
@login_required
def test_result(test_result_id):
    form = TestResultForm()
    if form.validate_on_submit():
        return redirect('/')
    result = get("http://{}:8080/api/test_results/{}".format(backend, test_result_id)).json()
    return render_template("test_result.html", title='Результат теста',
                           result="Вы набрали {} баллов".format(result["test_result"]["score"]), form=form)


def main():
    if len(sys.argv) > 1:
        global backend
        backend = sys.argv[1]
        print(backend)
        app.debug = True
        app.run(port=8090, host='0.0.0.0')
    else:
        print("Backend host name is not specified. Exit")


if __name__ == '__main__':
    main()
