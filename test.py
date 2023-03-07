@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
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
    SELECT students.student_id
         , students.name
         , active_courses.active_course_id
         , courses.name
    FROM active_courses
    JOIN students_courses ON active_courses.active_course_id = students_courses.active_course_id
    JOIN courses ON active_courses.course_id = courses.course_id
    JOIN students ON students_courses.student_id = students.student_id 
    WHERE active_courses.teacher_id = {teachers[0][0]}
    """)

    if request.method == 'POST':
        attendance_date = request.form["attendance_date"]
        student_id = request.form['student_id']
        active_course_id = request.form['active_course_id']
        attendance_status = request.form['attendance_status']
        try:
            execute_query(f"""
            INSERT INTO attendance (active_course_id, student_id, status, attend_date)
            VALUES ('{active_course_id}','{student_id}','{attendance_status}','{attendance_date}')
            """)
            return redirect(request.referrer)
        except:
            execute_query(f"""
            UPDATE attendance
            SET status = '{attendance_status}'
            WHERE student_id = '{student_id}' AND active_course_id = '{active_course_id}' AND attend_date = '{attendance_date}'
            """)
            return redirect(request.referrer)
    
    return render_template("attendance.html", active_courses=active_courses, teachers=teachers, message=message, current_date=current_date, students=students)
