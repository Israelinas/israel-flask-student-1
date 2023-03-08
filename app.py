from flask import Flask, render_template, redirect, url_for, request, session, abort
from setup_db import execute_query
import crud
import base64
import sqlite3
import datetime
import random


app = Flask(__name__)

app.secret_key = 'secret_key'



def time_message():
    now = datetime.datetime.now()
    if now.hour >= 5 and now.hour < 12:
        message = "Good morning"
        return message
    elif now.hour >= 12 and now.hour < 18:
        message = "Good afternoon"
        return message
    else:
        message = "Good evening"
        return message

@app.before_request
def auth():
    path_teacher_list = ['/teacher_panel']
    # path_student_list = ['/student']
    if "role" not in session.keys():
        session["username"]='anonymous'
        session["role"]='anonymous'
    if session["role"] != 'Admin':
        if 'admin' in request.full_path:
            return abort(403)
    if session["role"] != 'Teacher':
        if any(route in request.full_path for route in path_teacher_list):
            return abort(403)
    # if session["role"] != ['Student']:
    #     if any(route in request.full_path for route in path_student_list):
    #         return abort(403)


               

@app.route('/', methods = ['GET', 'POST'])
def home():
    if request.method == 'GET':
        new_courses = execute_query(f"""
        SELECT name, start_date, end_date from active_courses
        JOIN courses ON active_courses.course_id = courses.course_id
        ORDER BY start_date
        DESC LIMIT 5
        """)
        teacher_names = []
        teacher_images = []
        teachers_tuple = execute_query("SELECT * FROM teachers")
        for teacher in teachers_tuple:
            teacher_names.append(teacher[2])
            teacher_images.append(teacher[3])
        random_names = random.sample(teacher_names, 3)
        random_images = [teacher_images[teacher_names.index(name)] for name in random_names]

        for teacher_name, teacher_image in zip(random_names, random_images):
            teacher_name, teacher_image

        student_names = []
        student_images = []
        students_tuple = execute_query("SELECT * FROM students")
        for student in students_tuple:
            student_names.append(student[2])
            student_images.append(student[3])
        random_names = random.sample(student_names, 3)
        random_images = [student_images[student_names.index(name)] for name in random_names]

        for student_name, student_image in zip(random_names, random_images):
            student_name, student_image
        
        return render_template("index.html", new_courses=new_courses, teacher_name=teacher_name, teacher_image=teacher_image, student_name=student_name, student_image=student_image)
    else:
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        city = request.form["city"]
        execute_query(f"""
        INSERT INTO leads (name, phone, email, city)
        VALUES ('{name}','{phone}','{email}',"{city}")
        """)
        return render_template("index.html", name=name, phone=phone, email=email, city=city)



### GET - ADMIN PAGE VIEW
@app.route('/admin')
def admin():
    teachers = crud.show_all(table="teachers")
    courses = crud.show_all(table="courses")
    active_courses = execute_query(f"""
    SELECT active_courses.active_course_id, 
           courses.name
    FROM active_courses
    JOIN courses ON active_courses.course_id = courses.course_id
    """)
    students = crud.show_all(table="students")
    roles = execute_query(f"SELECT DISTINCT role FROM users")
    message = time_message()
    return render_template("admin.html", teachers=teachers, courses=courses, active_courses=active_courses, students=students, roles = roles, message=message)

### CREATE A NEW COURSE
@app.route('/create_course', methods=["POST"])
def create_course():
    course_name = request.form['course_name']
    course_desc = request.form['course_desc']
    course_image = request.form['course_image']
    execute_query(f"""
    INSERT INTO courses ('name', 'desc', 'image')
    VALUES ('{course_name}', '{course_desc}', '{course_image}')
    """)
    return redirect(url_for("admin"))

### CREATE ACTIVE COURSE (SET TEACHER AND DATES)
@app.route('/active_course', methods=["POST"])
def teacher_course():
    course_id = request.form['course_id']
    teacher_id = request.form['teacher_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    crud.add_active_course(course_id=course_id, teacher_id=teacher_id, start_date=start_date, end_date=end_date)
    return redirect(url_for("admin"))

### UPLOAD IMAGE TO AN EXISTING COURSE
@app.route('/upload_image_to_course', methods=["POST"])
def upload_image_to_course():
    course_id=request.form["course_id"]
    image = request.form["image"]
    execute_query(f"""
        UPDATE courses
        SET image = '{image}'
        WHERE course_id = {course_id}
    """)
    return redirect(url_for('admin'))

@app.route('/leads', methods = ['GET', 'POST'])
def show_leads():
    if request.method == 'GET':
        leads = execute_query("SELECT * FROM leads")
        return render_template("leads.html", leads=leads)
    else:
        lead_id = request.form['lead_id']
        if request.form.get('update_status'):
            status = request.form['status']
            execute_query(f"""
            UPDATE leads
            SET status = '{status}'
            WHERE lead_id = {lead_id}
            """)
        elif request.form.get('delete_lead'):
            execute_query(f"DELETE FROM leads WHERE lead_id = {lead_id}")
        return redirect(url_for("show_leads"))



### ADD STUDENT TO COURSE
@app.route('/course_student', methods=["POST"])
def method_name():
    active_course_id = request.form['active_course_id']
    student_id = request.form['student_id']
    crud.add_active_course_student(active_course_id=active_course_id, student_id=student_id)
    return redirect(url_for("admin"))

### NEW USER REGISTRATION
@app.route('/register', methods=["POST"])
def register():
    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]
    crud.new_user(email=email, password=password, role=role)
    # execute_query(f"""
    #       INSERT INTO user (user_email, user_password, role)
    #       VALUES ('{email}','{password}', '{role}')
    #       """)
    return redirect(url_for("admin"))


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_data = execute_query(f"""
            SELECT role 
                 , user_id
            FROM users
            WHERE email='{email}' 
            AND password='{password}'
            """)
        if not user_data:
            message = "The email address or password is incorrect. Please try again"
            return render_template("login.html", message)

        session['username'] = email
        session['role'] = user_data[0][0]
        session['user_id'] = user_data[0][1]
        return redirect(url_for('home'))
        
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route('/teacher_panel', methods = ['GET', 'POST'])
def teacher_panel():
    message = time_message()

    user_id = session['user_id']
    teachers = execute_query(f"""
    SELECT teacher_id,
           name
    FROM teachers
    WHERE user_id = {user_id}
    """)
    courses = execute_query(f"""
    SELECT active_courses.active_course_id,
           courses.name    
    FROM active_courses
    JOIN courses ON active_courses.course_id = courses.course_id
    WHERE teacher_id = {teachers[0][0]}
    """)
    
    if request.method == "POST":
        try:
            active_course_id = request.form["active_course_id"]
            students = execute_query(f"""
            SELECT students_courses.students_courses_id,
                   students_courses.grade,
                   students.student_id,
                   students.name,
                   courses.name
            FROM students_courses
            JOIN students ON students_courses.student_id = students.student_id
            JOIN active_courses ON students_courses.active_course_id = active_courses.active_course_id
            JOIN courses ON active_courses.course_id = courses.course_id
            WHERE active_courses.active_course_id = {active_course_id}
            """)
            return render_template("teacher_panel.html", students=students, courses=courses,
                                   teachers=teachers, message=message)
        except:
            error_message = "Please select a course"
            return render_template("teacher_panel.html", courses=courses, teachers=teachers, message=message, error_message=error_message)
  
    return render_template("teacher_panel.html", courses=courses, message=message, teachers=teachers)

@app.route('/update_grade', methods=["POST"])
def update_grade():
    student_id = request.form["student_id"]
    grade = request.form["grade"]
    execute_query(f"""
        UPDATE students_courses
        SET grade = '{grade}'
        WHERE student_id = {student_id}
        """)
    return redirect(request.referrer)
 


@app.route('/students1', methods = ['GET', 'POST'])
def students():
    students_db = crud.show_all(table='students')
    if request.method == 'POST':
        student_id = request.form["student_id"].split(" - ")[0]

        student_info = execute_query(f"""
                SELECT students.student_id, 
                       students.user_id, 
                       name, 
                       image, 
                       gender, 
                       birth_date, 
                       phone, 
                       address, 
                       user.email 
                       FROM  students
                JOIN users on students.user_id = users.user_id
                WHERE students.student_id = {student_id}
        """)
        return render_template("students1.html", students=students_db)
    return render_template("students1.html", student_info=student_info)



### UPDATE STUDENT INFO
@app.route('/update_profile/student', methods = ['GET', 'POST'])
def update_student_profile():  

    user_id = session["user_id"]

    students_db = execute_query(f"""
    SELECT name, 
           image, 
           gender, 
           birth_date, 
           phone, 
           address, 
           users.email, 
           users.password , 
           students.user_id
    FROM students
    JOIN users ON students.user_id = users.user_id
    WHERE students.user_id = {user_id}
    """)

    if request.method == 'POST' and 'personal_info' in request.form:
        name = request.form["name"].title()
        image = request.form["image"]
        gender = request.form["gender"]
        birth_date = request.form["birth_date"]
        phone = request.form["phone"]
        address = request.form["address"]
        execute_query(f"""
        UPDATE students
        SET name = '{name}'
          , image = '{image}'
          , gender = '{gender}'
          , birth_date = '{birth_date}'
          , phone = '{phone}'
          , address = '{address}'
        WHERE students.user_id = {user_id}
        """)

        return redirect(url_for("update_student_profile"))
    elif request.method == 'POST' and 'credentials' in request.form:
        email = request.form["email"]
        password = request.form["password"]
        execute_query(f"""
        UPDATE users
        SET email = '{email}'
          , password = '{password}'
        WHERE users.user_id = (
                              SELECT user_id FROM students WHERE user_id = {user_id}
                              )
        """)     

        return redirect(url_for("update_student_profile"))

    message = time_message()
    return render_template("update_student_profile.html", student_info=students_db, message=message)


### UPDATE TEACHER INFO
@app.route('/update_profile/teacher', methods = ['GET', 'POST'])
def update_teacher_profile():  

    user_id = session["user_id"]

    teachers_db = execute_query(f"""
    SELECT name, 
           image, 
           gender, 
           birth_date, 
           phone, 
           address, 
           users.email, 
           users.password , 
           teachers.user_id
    FROM teachers
    JOIN users ON teachers.user_id = users.user_id
    WHERE teachers.user_id = {user_id}
    """)

    if request.method == 'POST' and 'personal_info' in request.form:
        name = request.form["name"].title()
        image = request.form["image"]
        gender = request.form["gender"]
        birth_date = request.form["birth_date"]
        phone = request.form["phone"]
        address = request.form["address"]
        execute_query(f"""
        UPDATE teachers
        SET name = '{name}'
          , image = '{image}'
          , gender = '{gender}'
          , birth_date = '{birth_date}'
          , phone = '{phone}'
          , address = '{address}'
        WHERE teachers.user_id = {user_id}
        """)
        return redirect(url_for("update_teacher_profile"))

    elif request.method == 'POST' and 'credentials' in request.form:
        email = request.form["email"]
        password = request.form["password"]
        execute_query(f"""
        UPDATE users
        SET email = '{email}'
          , password = '{password}'
        WHERE users.user_id = (
                              SELECT user_id FROM teachers WHERE user_id = {user_id}
                              )
        """)     

        return redirect(url_for("update_teacher_profile"))

    message = time_message()
    return render_template("update_teacher_profile.html", teacher_info=teachers_db, message=message)


### TEACHER UPDATE GRADE TO A STUDENT IN ACTIVE COURSE

# TEACHER MUST BE A STUDENT TEACHER
# TEACHER MUST BE A TEACHER IN THE SPECIFIC ACTIVE COURSE
# TEACHER WILL SEARCH FOR A STUDENT A UPDATE HIS GRADE
# OR TEACHER WILL CHOOSE A COURSE BY A COURSE NUMBER AND SEE ALL STUDENTS IN THE COURSE, THERE TEACHER COULD UPDATE THE GRADE FOR EACH STUDENT
# @app.route('/teacher/update_grade', methods=['GET', 'POST'])
# def update_grade():
#     if request.method == 'POST':
#         return
#     return render_template("teacher_management.html", )

        
### SHOW STUDENTS
@app.route('/students')
def show_students():
    students_tupple = execute_query(f"""
        SELECT name
             , gender
             , phone
             , birth_date
             , round((julianday(CURRENT_DATE)-julianday(birth_date))/365,2) as age
             , email
        FROM students
        INNER JOIN users ON students.user_id = users.user_id
        """)
    students = [ [student for student in student_tup] for student_tup in students_tupple ]
    images_blob = execute_query("SELECT image FROM students")
    blob_list = [image_blob[0] for image_blob in images_blob]

    images = []
    for image in blob_list:
        try:
            encoded_data = [base64.b64encode(image).decode('utf-8')]
            images.append(encoded_data)
        except:
            images.append(list("null"))

    student_images = list(map(list.__add__, students, images))

    return render_template('students.html', students=student_images)

### SHOW TEACHERS
@app.route('/teachers')
def show_teachers():
    teachers_tupple = execute_query(f"""
    SELECT teachers.name
         , gender
         , phone
         , birth_date
         , round((julianday(CURRENT_DATE)-julianday(birth_date))/365,2) as AGE
         , email
    FROM teachers
    JOIN users ON teachers.user_id = users.user_id
    """)
    teachers = [ [teacher for teacher in teacher_tup] for teacher_tup in teachers_tupple ]
    image_blobs = execute_query("SELECT image FROM teachers")
    blob_list = [image_blob[0] for image_blob in image_blobs]

    images = []
    for image in blob_list:
        try:
            encoded_data = [base64.b64encode(image).decode('utf-8')]
            images.append(encoded_data)
        except:
            images.append(list("null"))
    teacher_images = list(map(list.__add__, teachers, images))
    return render_template('teachers.html', teachers=teacher_images)


### SHOW COURSES
@app.route('/courses')
def show_courses():
    courses = execute_query("SELECT * FROM courses")
    return render_template('courses.html', courses=courses)



### CHECK WHY IT DOESN'T WORK
@app.route('/newsletter_subscriber', methods =['POST'])
def newsletter_subscribe():
    subscriber_email = request.form['subscriber_email']
    execute_query(f"INSERT INTO subscribers (email) VALUES('{subscriber_email}')")
    return redirect(request.referrer)


### SEARCH IN NAVBAR
@app.route('/search')
def search():
    search = request.args["search"]
    if len(search) != 0:
        results = execute_query(f"""
        SELECT students.name, teachers.name, courses.name FROM students
        JOIN students_courses ON students.student_id = students_courses.student_id
        JOIN active_courses ON students_courses.active_course_id = active_courses.active_course_id
        JOIN teachers ON active_courses.teacher_id = teachers.teacher_id
        JOIN courses ON active_courses.course_id = courses.course_id
        WHERE students.name LIKE '{search}%'
            """)

        if len(results) != 0:
            return render_template("search.html", students = results)

        results = execute_query(f"""
        SELECT teachers.name, courses.name FROM teachers
        JOIN active_courses ON teachers.teacher_id = active_courses.teacher_id
        JOIN courses on active_courses.course_id = courses.course_id
        WHERE teachers.name LIKE '{search}%'
        """)
        if len(results) != 0:
            return render_template("search.html", teachers=results)

        results = execute_query(f"""
        SELECT name, 
               desc 
        FROM courses
        WHERE name LIKE '{search}%'
        """)
        if len(results) != 0:
            return render_template("search.html", courses=results)

        return redirect(url_for("home"))
    return redirect(request.referrer)
    
#### PROJECT 2 #####
    # JOIN attendance ON students.student_id = attendance.student_id
    #      , attendance.status
@app.route('/attendance', methods=['GET'])
def attendance():
    message = time_message()
    user_id = session['user_id']
    teachers = execute_query(f"""
    SELECT teacher_id, name 
    FROM teachers 
    WHERE user_id = {user_id}
    """)
    active_courses = execute_query(f"""
    SELECT active_courses.active_course_id
         , courses.name
    FROM active_courses
    JOIN courses ON active_courses.course_id = courses.course_id
    WHERE teacher_id = {teachers[0][0]}
    """)

    return render_template("attendance.html", active_courses=active_courses, teachers=teachers, message=message)

@app.route('/attendance/<int:active_course_id>', methods=['GET', 'POST'])
def course_attendance(active_course_id):
    current_date = datetime.datetime.now().date().strftime("%Y-%m-%d")
    message = time_message()

    user_id = session['user_id']
    teachers = execute_query(f"""
    SELECT teacher_id, name 
    FROM teachers 
    WHERE user_id = {user_id}
    """)
    active_courses = execute_query(f"""
    SELECT active_courses.active_course_id
         , courses.name
    FROM active_courses
    JOIN courses ON active_courses.course_id = courses.course_id
    WHERE teacher_id = {teachers[0][0]}
    """)

    students = execute_query(f"""
    SELECT
        active_courses.active_course_id,
        students.name,
        students.student_id,
        attendance.status,
        courses.name,
        attendance.attend_date
    FROM active_courses
    JOIN students_courses ON active_courses.active_course_id = students_courses.active_course_id
    JOIN students ON students_courses.student_id = students.student_id
    LEFT JOIN attendance ON active_courses.active_course_id = attendance.active_course_id 
    AND attendance.attend_date = '{current_date}' AND students.student_id = attendance.student_id
    JOIN courses ON active_courses.course_id = courses.course_id
    WHERE active_courses.active_course_id = {active_course_id}
    """)

    if request.method == 'POST':
        attendance_date = request.form["attendance_date"]
        student_id = request.form['student_id']
        attendance_status = request.form['attendance_status']
        try:
            execute_query(f"""
            INSERT INTO attendance (active_course_id, student_id, status, attend_date)
            VALUES ('{active_course_id}','{student_id}','{attendance_status}','{attendance_date}')
            """)
        except:
            execute_query(f"""
            UPDATE attendance
            SET status = '{attendance_status}'
            WHERE student_id = '{student_id}' AND active_course_id = '{active_course_id}' AND attend_date = '{attendance_date}'
            """)
        
        return redirect(url_for('course_attendance', active_course_id=active_course_id))

    return render_template("attendance_courses.html", active_courses=active_courses, teachers=teachers, message=message, current_date=current_date, students=students)


@app.route('/show_attendance', methods=['GET', 'POST'])
def show_attendance():
    message = time_message()

    user_id = session['user_id']
    teachers = execute_query(f"""
    SELECT teacher_id, name 
    FROM teachers 
    WHERE user_id = {user_id}
    """)

    if request.method == 'POST':
        active_course_id = request.form['active_course_id']
        attend_dates = execute_query(f"""
        SELECT DISTINCT attend_date
        FROM attendance
        WHERE active_course_id = {active_course_id}
        """)

        if request.form.get('attend_date'):
            attend_date = request.form['attend_date']
            attendance = execute_query(f"""
            SELECT attendance.student_id,
            students.name, 
            attendance.status
            FROM attendance
            JOIN students ON attendance.student_id = students.student_id
            WHERE attendance.active_course_id = {active_course_id}
            AND attendance.attend_date = '{attend_date}'
            ORDER BY students.name
            """)
            return render_template("show_attendance.html", attendance=attendance, attend_dates=attend_dates, active_course_id=active_course_id, teachers=teachers, message=message)

        return render_template("show_attendance.html", attend_dates=attend_dates, active_course_id=active_course_id, teachers=teachers, message=message)

    active_courses = execute_query(f"""
    SELECT active_courses.active_course_id, courses.name
    FROM active_courses
    JOIN courses ON active_courses.course_id = courses.course_id
    WHERE teacher_id = {teachers[0][0]}
    """)
    return render_template("show_attendance.html", active_courses=active_courses, teachers=teachers, message=message)



@app.route('/student_attendance', methods=['GET', 'POST'])
def student_attendance():
    students = execute_query("""
    SELECT DISTINCT 
    students.student_id,
    students.name
    FROM students
    JOIN students_courses ON students.student_id = students_courses.student_id
    JOIN active_courses ON students_courses.active_course_id = active_courses.active_course_id
    JOIN attendance ON active_courses.active_course_id = attendance.active_course_id
    """)

    if 'student' in request.args:
        student = request.args.get("student")

        if student == '':
            return redirect(request.referrer)
        
        courses = execute_query(f"""
        SELECT DISTINCT active_courses.active_course_id,
           courses.name,
           students.name,
        students.student_id
        FROM active_courses
        JOIN courses ON active_courses.course_id = courses.course_id
        JOIN attendance ON active_courses.active_course_id = attendance.active_course_id AND students.student_id = attendance.student_id
        JOIN students ON attendance.student_id = students.student_id
        WHERE attendance.student_id = {student}
        """)
        student_id = courses[0][1]
        student_name = courses[0][3]
    else:
        student_name = None
        courses = None
    
    if 'course' in request.args:
        course = request.args.get("course")

        if course == '':
            return redirect(request.referrer)
        

        attendance = execute_query(f"""
        SELECT attendance.status,
               attendance.attend_date,
               courses.name,
               active_courses.active_course_id,
               students.name
        FROM attendance
        JOIN active_courses ON attendance.active_course_id = active_courses.active_course_id
		JOIN courses ON active_courses.course_id = courses.course_id
        JOIN students ON attendance.student_id = students.student_id
        WHERE active_courses.active_course_id = {course}
        """)

        course_name = attendance[0][2]
        student_name = attendance[0][4]

    else:
        course_name = None
        attendance = None
    
    return render_template("student_attendance.html", students=students, student=student_name, courses=courses, course=course_name, attendance=attendance)


if __name__ == "__main__":
    app.run(debug=True)