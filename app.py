from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
import sqlite3
import hashlib
from datetime import datetime
from random import randint


# Настройки приложения 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vkr.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'hdwajdiwajfiojwaofjoaiwjfiojfwaojfwo'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'batareika12345678@gmail.com'
app.config['MAIL_DEFAULT_SENDER'] = 'batareika12345678@gmail.com'
app.config['MAIL_PASSWORD'] = 'ltrsfinkifghcrsx'
app.app_context().push()

db = SQLAlchemy(app)
mail = Mail(app)

number = 0

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к этой странице"
login_manager.login_message_category = "success"


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id)


# Определение классов

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(300), nullable=False)
    password = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return '<Account %r>' % self.id

class UserLogin():
    def fromDB(self, user_id):
        datebase = sqlite3.connect('instance/vkr.db')
        sql = datebase.cursor()
        sql.execute(f"SELECT * FROM account WHERE id='{user_id[0]}' LIMIT 1")
        res = sql.fetchone()
        if res is not None:
            self.__user = res
        else:
            print("Пользователь не найден")
        return self
    
    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.__user[0])
    
    def get_role(self):
        return str(self.__user[4])

def str_to_list(var):
    var = var.replace("'", "").replace("(", "").replace(")", "").split(", ")
    return var

# Основные страницы

@app.route('/')
@app.route('/home')
def home():
    try:
        return render_template("index.html", role = current_user.get_role())
    except:
        return render_template("index.html")

@app.route('/settings', methods = ['POST', 'GET'])
@login_required
def settings():
    cursor = sqlite3.connect('instance/vkr.db').cursor()
    cursor.execute("SELECT * FROM account")
    account_list = [item for item in cursor.fetchall()]
    try:
        return render_template("settings.html", account_list = account_list, role = current_user.get_role())
    except:
        return render_template("settings.html", account_list = account_list)

@app.route('/settings/<string:setting_user>', methods = ['POST', 'GET'])
@login_required
def setting(setting_user):
    datebase = sqlite3.connect('instance/vkr.db')
    cursor = datebase.cursor()
    cursor.execute(f"SELECT * FROM account WHERE name = '{setting_user}'")
    user_list = [item for item in cursor.fetchone()]
    if request.method == 'POST':
        datebase.execute(f"UPDATE account SET name = '{request.form['new_login']}', email = '{request.form['new_email']}', role = '{request.form.get('select_role')}' WHERE name = '{user_list[1]}'")
        datebase.commit()
        return redirect("/settings")
    try:
        return render_template("setting_user.html", user_list = user_list, role = current_user.get_role())
    except:
        return render_template("setting_user.html", user_list = user_list)
    
# Личный кабинет, авторизация

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect("/home")
    
    if request.method == 'POST':
        cursor = sqlite3.connect('instance/vkr.db').cursor()
        password = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
        cursor.execute(f"SELECT * FROM account WHERE name = '{request.form['username']}' and password = '{password}' LIMIT 1")
        user = cursor.fetchone()
        if user and (str(user[3]) == str(password)):
            userLogin = UserLogin().create(user)
            remainme = True if request.form.get('remainme') else False
            login_user(userLogin, remember = remainme)
            return redirect(request.args.get("next") or '/home')
        else:
            if not user:
                flash("Пользователь не найден", "error")
            elif str(user[3]) != str(password):
                flash("Пароль неверный", "error")
    try:
        return render_template("login.html", role = current_user.get_role())
    except:
        return render_template("login.html")

@app.route('/register-account', methods = ['POST', 'GET'])
def account():
    if request.method == 'POST':
        if request.form['password'] == request.form['repeat_password']:
            cursor = sqlite3.connect('instance/vkr.db').cursor()
            cursor.execute(f"SELECT * FROM account WHERE name = '{request.form['username']}' or email = '{request.form['email']}'")
            if cursor.fetchone():
                flash("Данный логин уже занят")
            else:
                hash_password = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
                new_account = Account(name = request.form['username'], email = request.form['email'], password = hash_password, role = 'Гость')
                if new_account:
                    db.session.add(new_account)
                    db.session.commit()
                    flash("Вы успешно зарегистрировались", "success")
                    return redirect('/login')
                else:
                    flash("При создании аккаунта произошла ошибка", "error")
        else:
            flash("Пароли не совпадают", "error")
    try:
        return render_template("register_account.html", role = current_user.get_role())        
    except:
        return render_template("register_account.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из профиля")
    return redirect("/login")


@app.route('/password', methods = ['POST', 'GET'])
def password():
    if request.method == 'POST':
        cursor = sqlite3.connect('instance/vkr.db').cursor()
        cursor.execute(f"SELECT * FROM account WHERE email = '{request.form['email']}'")
        if cursor.fetchone():
            global number
            number = randint(100000, 999999)
            msg = Message('Восстановление пароля', sender = "batareika12345678@gmail.com", recipients = [request.form['email']])
            msg.body = f"Ключ для восстановления пароля: {number}"
            mail.send(msg)
            return redirect(f"/reset-password/{request.form['email']}")
        else:
            flash("Аккаунта с данной почтой не существует", "error")
    try:
        return render_template("password.html", role = current_user.get_role())
    except:
        return render_template("password.html")
   
    

@app.route('/reset-password/<string:email>', methods = ['POST', 'GET'])
def reset_password(email):
    if request.method == 'POST':
        if int(request.form['number']) == int(number):
            if request.form['password'] == request.form['repeat_password']:
                datebase = sqlite3.connect('instance/vkr.db')
                datebase.execute(f"UPDATE account SET password = '{hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()}' WHERE email = '{email}'")
                datebase.commit()
                return redirect("/login")
            else:
                flash("Пароли не совпадают", "error")
        else:
            flash("Введеный код неверен", "error")
    try:
        return render_template("reset_password.html", role = current_user.get_role())
    except:
        return render_template("reset_password.html")
    


@app.route('/my-project')
@login_required
def my_project():
    cursor = sqlite3.connect('instance/vkr.db').cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    projects = [item[0] for item in cursor.fetchall()]
    projects.pop(0)
    cursor.execute(f"SELECT name FROM account WHERE id = '{current_user.get_id()}'")
    result = cursor.fetchone()
    project_list = {}
    for i in range(len(projects)):
        cursor.execute(f"SELECT meaning FROM '{projects[i]}'")
        if current_user.get_role() == 'Админ':
            project_list[i] = [item[0] for item in cursor.fetchall()]
        elif cursor.fetchall()[6] == result:
            cursor.execute(f"SELECT meaning FROM '{projects[i]}'")
            project_list[i] = [item[0] for item in cursor.fetchall()]
    try:
        return render_template("my_project.html", project_list = project_list, role=current_user.get_role())
    except:
        return render_template("my_project.html", project_list = project_list)
    
@app.route('/delete-user/<string:user_name>')
@login_required
def delete_user(user_name):
    datebase = sqlite3.connect('instance/vkr.db')
    datebase.execute(f"DELETE FROM account WHERE name = '{user_name}'")
    datebase.commit()
    return redirect('/settings')

# Работа с проектами

@app.route('/project')
@login_required
def project():
    cursor = sqlite3.connect('instance/vkr.db').cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    projects = [item[0] for item in cursor.fetchall()]
    projects.pop(0)
    project_list = {}
    for i in range(len(projects)):
        cursor.execute(f"SELECT meaning FROM '{projects[i]}'")
        project_list[i] = [item[0] for item in cursor.fetchall()]
    try:
        return render_template("project.html", project_list = project_list, role = current_user.get_role())
    except:
        return render_template("project.html", project_list = project_list)
    


@app.route('/project/<string:study_title>')
@login_required
def project_detail(study_title):
    cursor = sqlite3.connect('instance/vkr.db').cursor()
    cursor.execute(f"SELECT * FROM '{study_title}'")
    project = [item for item in cursor.fetchall()]
    try:
        return render_template("project_detail.html", project = project, project_name = project[0][1], role = current_user.get_role())
    except:
        return render_template("project_detail.html", project = project, project_name = project[0][1])


@app.route('/project/view/<string:study_title>', methods=['POST', 'GET'])
@login_required
def view(study_title):
    cursor = sqlite3.connect('instance/vkr.db').cursor()
    cursor.execute(f"SELECT * FROM '{study_title}'")
    project = [item for item in cursor.fetchall()]
    cursor.execute(f"SELECT * FROM '{study_title}' WHERE name = 'Запись'")
    records = [item for item in cursor.fetchall()]
    try:
        return render_template("view.html", project = project, project_name = project[0][1], role = current_user.get_role(), records = records)
    except:
        return render_template("view.html", project = project, project_name = project[0][1], records = records)
    


@app.route('/project/<project>/<project_name>/edit', methods=['POST', 'GET'])
@login_required
def project_edit(project, project_name):
    datebase = sqlite3.connect('instance/vkr.db')
    cursor = datebase.cursor()
    cursor.execute(f"SELECT name FROM account WHERE id = '{current_user.get_id()}'")
    result = cursor.fetchone()
    current_time = datetime.now().strftime("%H:%M:%S")
    project_name = str_to_list(project_name)
    project = str_to_list(project)
    if request.method == 'POST':
        datebase.execute(f"UPDATE '{project_name[0]}' SET name = '{request.form['item_name']}', meaning = '{request.form.get('point_value')}' WHERE name = '{project[0]}' and meaning = '{project[1]}'")
        datebase.execute(f"UPDATE '{project_name[0]}' SET meaning = '{result[0]}' WHERE name = 'Кем редактировано'")
        datebase.execute(f"UPDATE '{project_name[0]}' SET meaning = '{current_time}' WHERE name = 'Время последнего редактирования'")
        datebase.commit()
        return redirect(f"/project/{project_name[0]}")
    try:
        return render_template("edit.html", project = project, role = current_user.get_role())
    except:
        return render_template("edit.html", project = project)
    


@app.route('/delete_project/<project_name>')
@login_required
def delete_project(project_name):
    datebase = sqlite3.connect('instance/vkr.db')
    datebase.execute(f"DROP TABLE '{project_name}'")
    datebase.commit()
    return redirect("/project")


@app.route('/delete_detail_project/<project_name>/<name>/<meaning>')
@login_required
def delete_detail_project(project_name, name, meaning):
    datebase = sqlite3.connect('instance/vkr.db')
    datebase.execute(f"DELETE FROM '{project_name}' WHERE name = '{name}' and meaning = '{meaning}'")
    datebase.commit()
    return redirect(f"/project/{project_name}")


@app.route('/new-project', methods=['POST', 'GET'])
@login_required
def new_project():
    if request.method == 'POST':
        datebase = sqlite3.connect('instance/vkr.db')
        cursor = datebase.cursor()
        cursor.execute(f"SELECT name FROM account WHERE id = '{current_user.get_id()}'")
        result = cursor.fetchone()
        current_time = datetime.now().strftime("%H:%M:%S")
        try:
            datebase.execute(f"CREATE TABLE '{request.form['title_project']}' (name, meaning)")
            datebase.execute(f"""INSERT INTO '{request.form['title_project']}' VALUES
                ('Название', '{request.form['title_project']}'),
                ('Цель исследования', '{request.form['purpose_project']}'),
                ('Статус', 'Активна'),
                ('Время создания проекта', '{current_time}'),
                ('Кем создан проект', '{result[0]}'), 
                ('Время последнего редактирования', '{current_time}'),
                ('Кем редактировано', '{result[0]}')
            """)
            datebase.commit()
            return redirect(f"/new-project-shablon/{request.form['title_project']}")
        except:
            flash("Ошибка при создании таблицы")
    try:
        return render_template("new_project.html", role = current_user.get_role())
    except:
        return render_template("new_project.html")
    


@app.route('/new-project-shablon/<string:study_title>', methods=['POST', 'GET'])
@login_required
def new_project_shablon(study_title):
    if request.method == 'POST':
        datebase = sqlite3.connect('instance/vkr.db')
        datebase.execute(f"""INSERT INTO '{study_title}' VALUES
            ('ФИО', '{request.form['name']}'),
            ('Дата рождения', '{request.form['birthday']}'),
            ('Рост', '{request.form['height']}'),
            ('Вес', '{request.form['weight']}'),
            ('Пол', '{request.form['sex']}'),
            ('Место жительства', '{request.form['home']}'),
            ('Номер телефона', '{request.form['number_telephone']}'),
            ('Электронная почта', '{request.form['email']}')
        """)
        datebase.commit()
        return redirect(f"/new-project/{study_title}")
    try:
        return render_template("new_project_shablon.html", role = current_user.get_role())
    except:
        return render_template("new_project_shablon.html")
    


@app.route('/new-project/<string:study_title>', methods=['POST', 'GET'])
@login_required
def new_project_detail(study_title):
    datebase = sqlite3.connect('instance/vkr.db')
    if request.method == 'POST':
        datebase.execute(f"INSERT INTO '{study_title}' VALUES ('{request.form['item_name']}', '{request.form['point_value']}')")
        datebase.commit()
    cursor = datebase.cursor()
    cursor.execute(f"SELECT * FROM '{study_title}'")
    project = [item for item in cursor.fetchall()]
    del project[0:2]
    try:
        return render_template("new_project_detail.html", project = project, role = current_user.get_role())
    except:
        return render_template("new_project_detail.html", project = project)
    

@app.route('/new-record/<string:project_name>', methods=['POST', 'GET'])
@login_required
def new_record(project_name):
    datebase = sqlite3.connect('instance/vkr.db')
    if request.method == 'POST':
        datebase.execute(f"INSERT INTO '{project_name}' VALUES ('Запись', '{request.form.get('new-record')}')")
        datebase.commit()
        return redirect(f"/project/view/{project_name}")
    cursor = datebase.cursor()
    cursor.execute(f"SELECT * FROM '{project_name}'")
    project = [item for item in cursor.fetchall()]
    try:
        return render_template("new_record.html", project = project, project_name = project[0][1], role = current_user.get_role())
    except:
        return render_template("new_record.html", project = project, project_name = project[0][1])
    

if __name__ == "__main__":
    app.run(debug=True)
