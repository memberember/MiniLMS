from flask import render_template, request, json, redirect, flash, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from sweater import app, db
from sweater.models import User, Department, Discipline, DegreeProgramm, Faculty, Student, Group, Teacher
from sweater.utils import get_user_type_int


@app.route('/', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('inputEmail')
    password = request.form.get('inputPassword')

    if login and password:
        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            next_page = request.args.get('next')
            if next_page != None:
                return redirect(next_page)
            return redirect(url_for('about'))

        else:
            flash('Логин и пароль не верные')
    return render_template('login_page.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('inputEmail')
    password = request.form.get('inputPassword')
    password2 = request.form.get('inputPassword2')
    fio = request.form.get('fio')

    if request.method == 'POST':
        if not (login or password or password2):
            flash('Please, fill all fields!')
        elif password != password2:
            flash('Passwords are not equal!')
        else:
            hash_pwd = generate_password_hash(password)
            new_user = User(login=login, password=hash_pwd, type=2, fio=fio)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login_page'))
    return render_template('register_page.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))


# страница "О нас"
@app.route('/about')
@login_required
def about():
    return render_template('about.html')


# страница "О нас"
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    data = {}

    # если преподаватель то выполняется следующий участок кода
    if current_user.type == 1:
        # вытаскиваем текущего преподавателя
        teacher = Teacher.query.get(current_user.id)
        disciplines = Discipline.query.filter_by(teacher_id=teacher.id).all()

        # пакуем все в словарь из двух переменных
        data = {
            'teacher': teacher,
            'disciplines': disciplines
        }

    # если студент, то выполняется следующий участок кода
    if current_user.type == 2:

        # вытаскиваем текущего студента
        student = Student.query.get(current_user.id)
        disciplines = []

        # вытаскиваем его дисциплины
        for discipline_id in str(student.group.disciplines).split(' '):
            disciplines.append(Discipline.query.get(discipline_id))

        # пакуем все в словарь из двух переменных
        data = {
            'student': student,
            'disciplines': disciplines
        }

    # инициализация данных
    password = request.form.get('inputPassword')
    password2 = request.form.get('inputPassword2')
    fio = request.form.get('fio')

    # запрос в бд на получение пользователя с id текущего пользователя
    user = User.query.get(current_user.id)

    if request.method == 'POST':

        # если не меняли пароль
        if not (password or password2):
            print("password or password2")
            user.fio = fio
            flash(('s', 'Сохранено'))

        # если пароли тоже изменились но не совпадают
        elif password != password2:
            print("password != password2")
            flash(('e', 'Пароли не совпадают!'))

        # если сменили пароль
        else:
            user.fio = fio
            hash_pwd = generate_password_hash(password)
            user.password = hash_pwd
            flash(('s', 'Сохранено'))
    db.session.add(user)
    db.session.commit()
    return render_template('profile.html', data=data)


# страница пользователей
@app.route('/users')
@login_required
def users():
    items = User.query.order_by(User.id).all()
    return render_template('users.html', data=items)


# страница направлений
@app.route('/degree_programms')
@login_required
def degree_programms():
    items = DegreeProgramm.query.order_by(DegreeProgramm.id).all()
    for it in items:
        it.faculty_id = Faculty.query.get(it.faculty_id).name
    return render_template('degreeProgramms.html', data=items)


# страница кафедр
@app.route('/departments')
@login_required
def departments():
    # вытаскиваем список кафедр для отображения
    departments = Department.query.order_by(Department.faculty_id).all()

    divided = []

    # вытаскиваем список факультетов для меню выбора при добавлении
    faculties = Faculty.query.all()

    # делим список кафедр на списки из факультетов и их кафедр
    for it in faculties:
        department_list = []
        for department in departments:
            if department.faculty_id == it.id:
                department_list.append(department)
        divided.append({
            'faculty': it,
            'departments': department_list
        })

    data = {
        'departments': divided,
        'faculties': faculties
    }

    return render_template('departments.html', data=data)


# страница факультетов
@app.route('/faculties')
@login_required
def faculties():
    items = Faculty.query.order_by(Faculty.id).all()
    return render_template('faculties.html', data=items)


# страница дисциплин
@app.route('/disciplines')
@login_required
def disciplines():
    items = Discipline.query.order_by(Discipline.id).all()
    return render_template('disciplines.html', data=items)


# адрес для ajax запроса изменения пользователя
@app.route('/editUser', methods=['POST'])
def edit_user_ajax():
    fio = request.form.get('fio')
    user_id = request.form.get('user_id')
    try:
        user = User.query.get(user_id)
        user.fio = fio
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': f'Успешно сохранен: {user.fio}'})
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса удаления пользователя
@app.route('/deleteUser', methods=['POST'])
def delete_user_ajax():
    user_id = request.form.get('user_id')
    fio = request.form.get('fio')

    try:
        User.query.filter(User.id == user_id).delete()
        db.session.commit()
        return jsonify({'success': f'Успешно удален: {fio}'})
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса добавления пользователя
@app.route('/addUser', methods=['POST'])
def add_user_ajax():
    # вытаскиваем данные с полученной формы
    login = request.form.get('login')
    password = request.form.get('password')
    fio = request.form.get('fio')
    user_type = request.form.get('user_type')

    # хешируем пароль
    hash_pwd = generate_password_hash(password)

    # проверка заполненности полей
    if not (login and password and fio):
        return jsonify({'error': 'Все поля должны быть заполнены'})

    # отловщик ошибок
    try:

        # создание объекта User
        user = User(login=login, password=hash_pwd, fio=fio, type=user_type)
        user.fio = fio
        user.type = user_type
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': f'Успешно добавлен: {fio}'})

    # если поймалась ошибка, то выполняется этот блок
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса добавления факультета
@app.route('/addFaculty', methods=['POST'])
def add_faculty_ajax():
    # вытаскиваем данные с полученной формы
    name = request.form.get('name')

    # проверка заполненности полей
    if not name:
        return jsonify({'error': 'Название не должно быть пустым'})

    # отловщик ошибок
    try:

        # создание объекта User
        faculty = Faculty(name=name)
        faculty.name = name
        db.session.add(faculty)
        db.session.commit()
        return jsonify({'success': f'Успешно добавлен: {name}'})

    # если поймалась ошибка, то выполняется этот блок
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса удаления факультета
@app.route('/deleteFaculty', methods=['POST'])
def delete_faculty_ajax():
    faculty_id = request.form.get('faculty_id')
    name = request.form.get('name')

    try:
        Faculty.query.filter(Faculty.id == faculty_id).delete()
        db.session.commit()
        return jsonify({'success': f'Успешно удален: {name}'})
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса изменения факультета
@app.route('/editFaculty', methods=['POST'])
def edit_faculty_ajax():
    faculty_id = request.form.get('faculty_id')
    name = request.form.get('name')

    try:
        faculty = Faculty.query.get(faculty_id)
        faculty.name = name
        db.session.add(faculty)
        db.session.commit()
        return jsonify({'success': f'Успешно сохранен: {faculty.name}'})
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса добавления кафедры
@app.route('/addDepartment', methods=['POST'])
def add_department_ajax():
    # вытаскиваем данные с полученной формы
    name = request.form.get('name')
    faculty_id = request.form.get('faculty_id')

    # проверка заполненности полей
    if not name:
        return jsonify({'error': 'Название не должно быть пустым'})

    # отловщик ошибок
    try:

        # создание объекта User
        department = Department(name=name)
        department.name = name
        department.faculty_id = faculty_id
        db.session.add(department)
        db.session.commit()
        return jsonify({'success': f'Успешно добавлен: {name}'})

    # если поймалась ошибка, то выполняется этот блок
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса удаления кафедры
@app.route('/deleteDepartment', methods=['POST'])
def delete_department_ajax():
    department_id = request.form.get('department_id')
    name = request.form.get('name')

    try:
        Department.query.filter(Department.id == department_id).delete()
        db.session.commit()
        return jsonify({'success': f'Успешно удален: {name}'})
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# адрес для ajax запроса изменения кафедры
@app.route('/editDepartment', methods=['POST'])
def edit_department_ajax():
    department_id = request.form.get('department_id')
    name = request.form.get('name')

    try:
        department = Department.query.get(department_id)
        department.name = name
        db.session.add(department)
        db.session.commit()
        return jsonify({'success': f'Успешно сохранен: {department.name}'})
    except:
        return jsonify({'error': 'Что то пошло не так, попробуйте позже'})


# перенаправление на логин при неавторизованном пользователе
@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)
    return response
