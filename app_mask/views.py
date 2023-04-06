import datetime
import json
import os
import random
from app_mask import app, config, local_db, face_detect, ocr, account
from flask import render_template, request, jsonify, make_response, send_from_directory, url_for, redirect, flash
from flask_login import UserMixin, login_required, current_user, login_user, logout_user, LoginManager
import uuid


@app.route('/login/', methods=['GET', 'POST'])  # 登录
def login():
    if request.method == 'POST':
        username = request.form['username']
        userpasswd = request.form['userpasswd']
        user_remember_me = False
        if request.form['remember_me'] == 'on':
            user_remember_me = True
        user = account.find_user(username)
        if user:
            if user.check_password(userpasswd):  # 校验密码
                login_user(user, remember=user_remember_me)  # 创建用户 Session
                flash('Logged in successfully!')
                msg = "success"
                return jsonify({'msg': msg})
            else:
                msg = "用户名或密码有误"
                return jsonify({'msg': msg})
        else:
            msg = "用户名或密码有误"
            return jsonify({'msg': msg})
    return render_template('login.html')


@app.route('/logout')  # 登出
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/settings", methods=['GET'])
@login_required
def settings():
    return render_template('setting.html',
                           id=current_user.id,
                           username=current_user.username,
                           mail=current_user.mail,
                           sex=current_user.sex,
                           position=current_user.position,
                           status=current_user.status)


@app.route('/home/', methods=['GET'])
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/about/', methods=['GET'])
def about():
    return render_template('about.html')


@app.route('/console/', methods=['GET'])
@login_required
def console():
    return render_template('console.html', username=current_user.username)


@app.route('/face_view/', methods=['GET'])
@login_required
def face_view():
    return render_template('face_view.html', username=current_user.username)


# check
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def create_uuid():
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(0, 100)
    if random_num <= 10:
        random_num = str(0) + str(random_num)
    unique_num = str(now_time) + str(random_num)
    return unique_num


# face_register
@app.route('/register/', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        name = request.form['name']
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = file.filename
            ext = filename.rsplit('.', 1)[1]
            filename = create_uuid() + '.' + ext
            file.save(config.APP_PATH + "/"+app.config['UPLOAD_FOLDER'] + 'REGISTER/' + filename)
            # 转到数据库存储
            trans_id = local_db.register_trans(name=name, path=app.config['UPLOAD_FOLDER'] + 'REGISTER/' + filename)
            # 上传百度云
            result = face_detect.face_register(path=app.config['UPLOAD_FOLDER'] + "REGISTER/" + filename,
                                               trans_id=trans_id)
            # 如果检测失败了，就应该把刚刚的数据删掉
            if result == 'SUCCESS':
                return jsonify({'msg': 'SUCCESS'})
            else:
                local_db.delete_trans(trans_id)
                return jsonify({'msg': 'face already exist'})
        else:
            return jsonify({'msg': 'ILLEGAL'})
    return render_template('register.html',  username=current_user.username)


@app.route('/check_add_photo/', methods=['GET', 'POST'])
@login_required
def check_add_photo():
    if request.method == 'POST':
        file = request.files['photo']
        pos = request.form['position']
        check_time = request.form['time']
        if check_time == '':
            return jsonify({'msg': 'ERROR: need time'})
        if file and allowed_file(file.filename):
            filename = file.filename
            ext = filename.rsplit('.', 1)[1]
            filename = create_uuid() + '.' + ext
            file.save(config.APP_PATH + "/" + app.config['UPLOAD_FOLDER'] + 'ADD_PHOTO/check/' + filename)
            res = face_detect.mask_detect(path=app.config['UPLOAD_FOLDER'] + "ADD_PHOTO/check/" + filename)
            if res['msg'] == 'SUCCESS':
                for n in range(res['num']):
                    local_db.enter(student_id=res['info'][n]['student_id'], path=str(app.config['UPLOAD_FOLDER'] +
                                                                                     "ADD_PHOTO/check/" + filename),
                                   is_mask=res['info'][n]['is_mask'], position=pos, time=check_time)
                    return jsonify({"msg": "SUCCESS"})
        else:
            return jsonify({'msg': 'FILE ILLEGAL'})
    else:
        return render_template('check_add_photo.html',  username=current_user.username)


@app.route('/check_result/', methods=['GET'])
@login_required
def check_result():
    return render_template('check_result.html',  username=current_user.username)


# homework
@app.route('/homework_add_photo/', methods=['GET', 'POST'])
@login_required
def homework_add_photo():
    if request.method == 'POST':
        subject = request.form['subject']
        time = request.form['time']
        file = request.files['photo']
        homework = request.form['homework']
        if file and allowed_file(file.filename):
            filename = file.filename
            ext = filename.rsplit('.', 1)[1]
            filename = create_uuid() + '.' + ext
            file.save(config.APP_PATH + "/" + app.config['UPLOAD_FOLDER'] + 'ADD_PHOTO/homework/' + filename)
            res = ocr.ocr(path=app.config['UPLOAD_FOLDER'] + "ADD_PHOTO/homework/" + filename)
            res = json.loads(res)
            # 处理部分
            data = res['forms'][0]['body']
            people_num = 0  # 一共有多少人
            is_commit_row = 0
            name_row = 0  # 名字矩形的序号,这个要到第一个名字就加 1
            for i in data:
                if i['column'][0] == 1:
                    if people_num < i['row'][0]:
                        people_num = i['row'][0]
                else:
                    break
            people_num = people_num - 1
            for i, element in enumerate(data):
                if element['word'] == '姓名':
                    name_row = i  # name_row = 4
                    break

            for i, element in enumerate(data):
                if element['word'] in config.is_commit_word:
                    is_commit_row = i  # is_commit_row = 8
                    break

            for i in range(people_num):  # 因为这个range默认从0开始 所以要加 1
                if data[is_commit_row + i + 1]['word'] == '1':
                    is_commit = 1
                else:
                    is_commit = 0
                ldb_res = local_db.add_homework(name=data[name_row + i + 1]['word'],
                                                path=app.config['UPLOAD_FOLDER'] + "ADD_PHOTO/homework/" + filename,
                                                subject=subject, homework=homework,
                                                is_commit=is_commit, time=time)
                if ldb_res['msg'] == 'FAIL':
                    return jsonify({'msg': 'Fail: unregister name!'})

            return jsonify({'msg': 'SUCCESS'})
        else:
            return jsonify({'msg': 'FILE ILLEGAL'})
    return render_template('homework_add_photo.html',  username=current_user.username)


@app.route('/homework_result/', methods=['GET', 'POST'])
@login_required
def homework_result():
    if request.method == 'POST':
        res = {}
        subject = ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "信息技术", "通用技术"]
        for i in subject:
            num = local_db.get_homework_num(i)
            info = local_db.get_homework_data(i)
            res[i] = {"info": info, "num": num}
        return jsonify(res)
    return render_template("homework_result.html",  username=current_user.username)


# class
@app.route('/class_add_photo/', methods=['GET', 'POST'])
@login_required
def class_add_photo():
    if request.method == 'POST':
        file = request.files['photo']
        name = request.form['name']
        lesson = request.form['lesson']
        reason = request.form['reason']
        time = request.form['time']
        if file and allowed_file(file.filename):
            filename = file.filename
            ext = filename.rsplit('.', 1)[1]
            filename = create_uuid() + '.' + ext
            file.save(config.APP_PATH + "/" + app.config['UPLOAD_FOLDER'] + 'ADD_PHOTO/class/' + filename)
            local_db.class_add_photo(name=name, path=app.config['UPLOAD_FOLDER'] + "ADD_PHOTO/class/" + filename,
                                     lesson=lesson, time=time, annotation=reason)
            return jsonify({'msg': 'SUCCESS'})
        else:
            return jsonify({'msg': 'FILE ILLEGAL'})
    return render_template('class_add_photo.html',  username=current_user.username)


@app.route('/class_result/', methods=['GET', 'POST'])
@login_required
def class_result():
    if request.method == "POST":
        info = local_db.get_class()
        num = local_db.get_class_num()
        return jsonify({"info": info, "num": num})
    return render_template('class_result.html',  username=current_user.username)


# student
@app.route('/search/', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == "POST":
        tid = local_db.name_to_trans_id(request.form['name'])
        path = local_db.path_search_by_id(tid)
        # check_res = local_db.check_search_by_id(tid)
        # homework_res = local_db.homework_search_by_id(tid)
        # class_res = local_db.class_search_by_id(tid)
        check_res = 1
        homework_res = 1
        class_res = 1
        return jsonify({"msg": "SUCCESS",
                        "info": {
                            "name": request.form['name'],
                            "id": tid,
                            "path": path
                        },
                        "check": check_res,
                        "homework": homework_res,
                        "class": class_res})
    return render_template('search.html',  username=current_user.username)


@app.route('/stu/<string:student_id>', methods=['GET', 'POST'])
@login_required
def get_stu(student_id):
    if request.method == 'POST':
        content = request.json
        student_id = content['student_id']
        return jsonify()
    return render_template('stu.html')


@app.errorhandler(401)
def unauthorized(e):
    return redirect(url_for('login'))



# ----------------------- api_part ----------------------------------


@app.route('/api/update_homework/', methods=['POST'])
@login_required
def update_homework():
    content = request.json
    name = content['name']
    subject = content['subject']
    homework = content['homework']
    local_db.homework_update(name, homework, subject)
    return jsonify({"msg": "SUCCESS"})


@app.route('/api/delete/student_by_name/', methods=['POST'])
@login_required
def delete_student_by_name():
    content = request.json
    name = content['name']
    trans_id = local_db.name_to_trans_id(name)
    local_db.delete_trans(trans_id)
    res = face_detect.user_delete(trans_id)
    return jsonify(res)


@app.route('/api/get_data/<path:need>', methods=['POST'])
@login_required
def api_get_data(need):
    if need == 'face_view/':
        info = local_db.get_students_info()
        num = local_db.count_person()
        return jsonify({"info": info, "num": num})

    if need == 'check_result/':
        content = request.json
        date = content['date']
        pass_row_data = local_db.count_pass(date)
        mask_wearing_chart_data = local_db.count_mask()
        commuting_chart_data = local_db.count_commuting()
        donut_chart = local_db.sum_mask()
        date = local_db.get_date()
        system_judge = []
        for col in date:
            system_judge.append({"date": col, "score": random.randint(90, 100)})
        return jsonify({"mask_wearing_chart_data": mask_wearing_chart_data,
                        "commuting_chart_data": commuting_chart_data,
                        "pass_row_data": pass_row_data,
                        "system_judge": system_judge,
                        "donut_chart": donut_chart,
                        "date": date})


@app.route('/api/get_pic/<path:path>', methods=['GET'])
@login_required
def api_get_pic(path):
    if path is None:
        pass
    else:
        ext = path.rsplit('.', 1)[1]
        apath = config.APP_PATH.replace('\\', '/') + '/'
        print("apath is ................ "+apath)
        image_data = open(apath + path, "rb").read()
        response_data = make_response(image_data)
        if ext == 'jpg' or ext == 'JPG' or ext == 'JPEG' or ext == 'jpeg':
            response_data.headers['Content-Type'] = 'image/jpeg'
        if ext == 'png' or ext == 'PNG':
            response_data.headers['Content-Type'] = 'image/png'
        return response_data


@app.route('/download/<path:path>', methods=['GET'])
@login_required
def download(path):
    path, filename = os.path.split(path)
    # apath = config.APP_PATH.replace('\\', '/') + '/'
    return send_from_directory(config.APP_PATH + path, filename=filename, as_attachment=True)


@app.route('/api/search_check_result/', methods=['POST'])
@login_required
def search_check_result():
    date = request.form['date']
    pass_row_data = local_db.count_pass(date)
    mask_wearing_chart_data = local_db.count_mask()
    commuting_chart_data = local_db.count_commuting()
    donut_chart = local_db.sum_mask()
    date = local_db.get_date()
    system_judge = []
    for col in date:
        system_judge.append({"date": col, "score": random.randint(90, 100)})
    return jsonify({"mask_wearing_chart_data": mask_wearing_chart_data,
                    "commuting_chart_data": commuting_chart_data,
                    "pass_row_data": pass_row_data,
                    "system_judge": system_judge,
                    "donut_chart": donut_chart,
                    "date": date})

