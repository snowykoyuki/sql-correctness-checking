from flask import Flask, render_template, request, redirect, url_for, session, abort #install flask
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import re
import json
import time
from datetime import timedelta
import config

# install pycryptodome
from Crypto.Cipher import AES 
from Crypto.Random import get_random_bytes

app = Flask(__name__)

@app.route('/login/', methods=['POST', 'GET'])
def login():
    if (request.method=='POST'):
        username=request.form['username'].lower()
        password=request.form['passw']

        # open database
        conn = sqlite3.connect("app.db")
        # Specify how we want to receive results
        conn.row_factory = sqlite3.Row 
        # Obtain a cursor for executing queries

        f = '%Y-%m-%d %H:%M:%S'
        now = time.gmtime()
        currenttimestamp = time.strftime(f, now)

        cur = conn.cursor()
        cur.execute("SELECT id, password, usertype, active FROM user WHERE username = ?;", (username,))
        #cur.execute("SELECT username FROM user WHERE username = 'as';")
        #print(userexists)
        userinfo = cur.fetchone()

        if userinfo is not None:
            loginsuccess=check_password_hash(userinfo['password'], password)
            if (userinfo['active']==0):
                return render_template('login.html', error='Your account has been disabled. Contact an administrator.')
            if loginsuccess:
                print(currenttimestamp + " LOGIN " + username)
                session.permanent=True
                session['user'] = {'uid': userinfo['id'], 'username':username, 'role': userinfo['usertype']}
                
                #update last login time
                cur.execute("UPDATE user SET lastlogin = datetime('now') WHERE username = ?;", (username, ))
                conn.commit()
                
                cur.close()
                conn.close()
                return redirect(url_for('home'))
            else:
                print(currenttimestamp + " LOGIN FAIL" + username)
                cur.close()
                conn.close()
                return render_template('login.html', error='Username or password is incorrect')
            
        else:
            print(currenttimestamp + " LOGIN FAIL" + username)
            cur.close()
            conn.close()
            return render_template('login.html', error='Username or password is incorrect')
        
    # display login page
    return render_template('login.html')


@app.route('/register/', methods=['POST', 'GET'])
def register():
    if (request.method=='POST'):
        username=request.form['username'].lower()
        password=request.form['passw']
        #print(username)
        #print(password)
        # open database
        conn = sqlite3.connect("app.db")
        #print(conn)
        # Specify how we want to receive results
        conn.row_factory = sqlite3.Row 
        # Obtain a cursor for executing queries
        cur = conn.cursor()

        cur.execute("SELECT username FROM user WHERE username = ?;", (username, ))
        #print(userexists)
        userexists = cur.fetchone()
        
        if userexists is not None:
            cur.close()
            conn.close()
            return render_template('register.html', usernametaken="Username already exists")

        passwordhash=generate_password_hash(password)
        #print(passwordhash)

        f = '%Y-%m-%d %H:%M:%S'
        now = time.gmtime()
        currenttimestamp = time.strftime(f, now)

        try:
            print(currenttimestamp + " REGISTER " + username)
            cur.execute("INSERT INTO user (username, password, datecreated, lastlogin) VALUES (?, ?, datetime('now'), datetime('now'))", (username, passwordhash,))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('login', register=True))
            
        except Exception as e:
            print (e)
            cur.close()
            conn.close()
            #print("databasefail")
            return render_template("register.html", databasefail=True)
        
    else:
        return render_template('register.html')


@app.route('/profile/', methods=['GET'])
@app.route('/profile/<profile>', methods=['GET'])
def profile(profile=None):
    
    if 'user' in session:
        #check if profile viewing is self profile
        if profile is None:
            return render_template('search.html')
        elif profile == session['user']['username']:
            viewself=True
        else:
            viewself=False

        #make username from url lowercase
        profile=profile.lower()
        action = request.args.get('action')

        # open database
        conn = sqlite3.connect("app.db")
        # Specify how we want to receive results
        conn.row_factory = sqlite3.Row 
        # Obtain a cursor for executing queries
        cur = conn.cursor()
        
        #get info of requested profile
        cur.execute("SELECT id AS uid, username, usertype AS role, datecreated, lastlogin, active FROM user WHERE username = ?;", (profile,))
        profileinfo=cur.fetchone()

        if not (profileinfo):
            cur.close()
            conn.close()
            return render_template('search.html', profilenotfound=True)

        #check whether user is subscribed to/being subscribed by the profile
        if session['user']['role']==0:
            cur.execute("SELECT active, datesub from subscription WHERE student = ? AND teacher = ?;", (session['user']['uid'], profileinfo['uid'],))
        else:
            cur.execute("SELECT active, datesub from subscription WHERE teacher = ? AND student = ?;", (session['user']['uid'], profileinfo['uid'],))
        subscription=cur.fetchone()

        if subscription is None:
            followstatus = "Never followed"
            followflag = 0

            #follow only available for student to teacher/admin
            if (session['user']['role']==0 and profileinfo['role']!=0):
                #follow action
                if action == "follow":
                    f = '%Y-%m-%d %H:%M:%S'
                    now = time.gmtime()
                    currenttimestamp = time.strftime(f, now)
                    print(currenttimestamp + " " + session['user']['username'] + " FOLLOW " + profileinfo['username'])
                    cur.execute("INSERT INTO subscription (teacher, student, datesub) VALUES (?, ?, datetime('now'))", (profileinfo['uid'], session['user']['uid'],))
                    conn.commit()
                    followstatus = "Followed on " + currenttimestamp
                    followflag = 1

        elif subscription['active'] == 0:
            followstatus = "Unfolowed on " + subscription['datesub']
            followflag = 0

            #follow only available for student to teacher/admin
            if (session['user']['role']==0 and profileinfo['role']!=0):
                #follow action
                if action == "follow":
                    f = '%Y-%m-%d %H:%M:%S'
                    now = time.gmtime()
                    currenttimestamp = time.strftime(f, now)
                    cur.execute("UPDATE subscription SET active = 1, datesub = datetime('now') WHERE student = ? AND teacher = ?;", (session['user']['uid'], profileinfo['uid'],))
                    conn.commit()
                    followstatus = "Followed on " + currenttimestamp
                    followflag = 1

        else:
            followstatus = "Followed on " + subscription['datesub']
            followflag = 1
            
            #follow only available for student to teacher/admin
            if (session['user']['role']==0 and profileinfo['role']!=0):
                #follow action
                if action == "unfollow":
                    f = '%Y-%m-%d %H:%M:%S'
                    now = time.gmtime()
                    currenttimestamp = time.strftime(f, now)
                    cur.execute("UPDATE subscription SET active = 0, datesub = datetime('now') WHERE student = ? AND teacher = ?;", (session['user']['uid'], profileinfo['uid'],))
                    conn.commit()
                    followstatus = "Unfollowed on " + currenttimestamp
                    followflag = 0

        followable=False

        #if profile is teacher
        if (profileinfo['active']==0):
            roletext = "Disabled account"
            followable=False
        elif (profileinfo['role']==1):
            roletext = "Teacher"
            if session['user']['role']==0:
                followable=True
        
        #if profile is admin
        elif (profileinfo['role']==2):
            if session['user']['role']==0:
                followable=True
                roletext = "Teacher" #hide user is admin to student
            else:
                roletext = "Admin" #show user as admin to teacher and admin

        #if user is student
        else:
            roletext = "Student"

        if (session['user']['role']==2):
            #ban action
            if action == "ban":
                cur.execute("UPDATE user SET active=0 WHERE id=?;", (profileinfo['uid'],))
                conn.commit()
                roletext="Disabled Account"
            elif action == "unban":
                cur.execute("UPDATE user SET active=1 WHERE id=?;", (profileinfo['uid'],))
                conn.commit()
                roletext="Account reactivated"
        cur.close()
        conn.close()
        return render_template('profile.html', viewself=viewself, profileinfo=profileinfo, role=roletext, followable=followable, followflag=followflag, followstatus=followstatus)
  
    #not logged in
    else:
        return redirect(url_for('login'))

@app.route('/edit/profile/', methods=['GET', 'POST'])
def editprofile():
    return render_template('editprofile.html')


#home
@app.route('/home/', methods=['GET'])
def home():
    if 'user' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

#redirect to home
@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/assignments/create/', methods=['GET', 'POST'])
def createassignment():
    if 'user' in session:
        # if user is student, 403
        if session['user']['role']==0:
            abort(403)
        else:
            if (request.method!='POST'):
                return render_template("createassignment.html", title="Create an Assignment")
            else:
                title=request.form['title']
                if (title is None or title==""):
                    title="Untitled Assignment"
                description=request.form['description']
                startdate=request.form['startdate']
                enddate=request.form['enddate']
                sampleanswer=request.form['sampleanswer']
                sampleanswer_allowviewing=request.form['sampleanswer_allowviewing']
            
                tablenames = request.form.getlist('tablename[]')
                attributenames = request.form.getlist('attributename[]')
                attributetypes = request.form.getlist('attributetype[]')
                attributenum = request.form.getlist('attributenum[]') #list of number of attributes per table
                symbolic = request.form.getlist('symbolic[]') #if symbolic attributes exist
                totalattribute = 0

                tableschema = ""

                for j in range(0, len(attributenum)):
                    #tableschema : schema s1(uid:int, uname:varchar, city:int);
                    tableschema += "schema s" + str(j) + "("
                    for i in range(0, int(attributenum[j])):
                        #add comma if there exists a prior element
                        if (i>0):
                            tableschema += ", "
                        tableschema += attributenames[totalattribute] + ":" + attributetypes[totalattribute]
                        totalattribute+=1
                    if symbolic[j] == 1:
                        tableschema += ", ??"
                    tableschema += ");\n"
                    #tableschema : table user(s1);
                    tableschema += "table " + tablenames[j] + "(s" + str(j) +");\n\n"

                if (startdate is None or startdate ==""):
                    f = '%Y-%m-%d %H:%M:%S'
                    now = time.gmtime()
                    startdate = time.strftime(f, now)
                    
                # open database
                conn = sqlite3.connect("app.db")
                # Specify how we want to receive results
                conn.row_factory = sqlite3.Row
                # Obtain a cursor for executing queries
                cur = conn.cursor()

                cur.execute("""
                INSERT INTO assignment (title, description, teacher, start_date, end_date, tableschema, sampleanswer, sampleanswer_allowviewing)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (title, description, session['user']['uid'], startdate, enddate, tableschema, sampleanswer, sampleanswer_allowviewing,))
                conn.commit()
                return redirect(url_for('assignments'))

    else:
        return redirect(url_for('login'))


@app.route('/assignments/', methods=['GET'])
@app.route('/assignments/<assignment>', methods=['GET'])
def assignments(assignment=None):
    if 'user' in session:
        # open database
        conn = sqlite3.connect("app.db")
        # Specify how we want to receive results
        conn.row_factory = sqlite3.Row 
        # Obtain a cursor for executing queries
        cur = conn.cursor()
        
        # if assignment ID is not specified in URL
        if assignment is None:
            #for selecting table for students
            if session['user']['role']==0:
                cur.execute("""SELECT a.id, a.title, a.description, a.teacher AS teacherID, a.start_date AS startdate, a.end_date AS enddate, u.username as teachername, IFNULL((SELECT s.id FROM submission s, assignment a2 WHERE a2.id=s.assignment AND s.active=1 AND a2.active=1 AND s.student=? AND a2.id=a.id), -1) AS submitted
                            FROM assignment a, user u
                            WHERE a.teacher = u.id
                            AND a.active=1
                            AND startdate<=DATE('now')
                            AND ( (enddate>=DATE('now')) OR (NOT EXISTS(SELECT s.id FROM submission s WHERE s.assignment=a.id AND s.active=1)) )
                            AND a.teacher IN (SELECT teacher FROM subscription WHERE student = ? AND active=1)
                            ORDER BY enddate ASC;
                            """, (session['user']['uid'], session['user']['uid'],))
                
            #for selecting table for teachers
            else:
                cur.execute("""SELECT a.id, a.title, a.description, a.start_date AS startdate, a.end_date AS enddate, a.maxscore, count(s.id) AS submitted
                            FROM assignment a LEFT JOIN (SELECT * FROM submission WHERE active=1) s ON a.id = s.assignment
                            WHERE a.teacher = ?
                            AND (a.end_date >=DATE('now','-1 months') OR EXISTS (SELECT s.id FROM submission s WHERE a.maxscore>0 AND s.assignment=a.id AND s.active=1 AND s.id NOT IN (SELECT scr2.submission from score scr2)))
                            GROUP BY a.id
                            ORDER BY enddate ASC;
                            """, (session['user']['uid'],))
                
            assignments=cur.fetchall()
            cur.close()
            conn.close()
            return render_template('assignments.html', assignments=assignments)
        
        # if assignment ID is specified in URL
        else:
            #if user is a student
            if session['user']['role']==0:
                cur.execute("""SELECT date('now') AS currentdate, a.id, a.title, a.description, a.teacher AS teacherID, a.start_date AS startdate, a.end_date AS enddate, u.username as teachername, a.tableschema, a.sampleanswer, a.sampleanswer_allowviewing, a.maxscore, IFNULL((SELECT s2.id FROM submission s2, assignment a2 WHERE a2.id=s2.assignment AND s2.active=1 AND a2.active=1 AND s2.student=? AND a2.id=a.id), -1) AS submitted, (SELECT scr.score FROM submission s, score scr WHERE s.assignment=a.id AND scr.submission=s.id AND s.student=?) AS score
                            FROM assignment a, user u
                            WHERE a.teacher = u.id
                            AND a.id=?;
                            """, (session['user']['uid'], session['user']['uid'], assignment,))
                
            #if user is a teacher
            else:
                cur.execute("""SELECT date('now') AS currentdate, a.id, a.title, a.description, u.username as teachername, a.start_date AS startdate, a.end_date as enddate, a.tableschema, a.sampleanswer, a.sampleanswer_allowviewing, a.maxscore, count(s.id) AS submitted
                            FROM assignment a LEFT JOIN (SELECT * FROM submission WHERE active=1) s ON a.id = s.assignment, user u
                            WHERE u.id = a.teacher
                            GROUP BY a.id
                            HAVING a.id=?
                            """, (assignment,))
            
            #only need to get the data related to the specified assignment
            assignmentdata=cur.fetchone()
            if (assignmentdata['enddate']<=assignmentdata['currentdate']):
                assignmentexpired=True
            else:
                assignmentexpired=False
            cur.close()
            conn.close()
            return render_template('assignment.html', assignmentdata=assignmentdata, assignmentexpired=assignmentexpired)

    else:
        return redirect(url_for('login'))

@app.route('/assignments/<assignment>/submit/', methods=['GET', 'POST'])
def submit(assignment=None):
    # if assignment is not defined, redirect to asignment list
    if assignment is None:
        return redirect(url_for('assignments'))
    
    if 'user' in session:
        if session['user']['role']==0:
            if request.method=="POST":
                #get answer from form
                answer=request.form['answer']
                # open database
                conn = sqlite3.connect("app.db")
                # Specify how we want to receive results
                conn.row_factory = sqlite3.Row 
                # Obtain a cursor for executing queries
                cur = conn.cursor()
                #check if active submission exists
                cur.execute("SELECT id FROM submission WHERE student=? and assignment=? AND active=1;", (session['user']['uid'], assignment,))
                submitted = cur.fetchone()

                #update old submission to inactive if already submitted
                if (submitted):
                    cur.execute("UPDATE submission SET active=0 WHERE id=?;", (submitted['id'],))

                #insert into table the new submission
                cur.execute("""INSERT INTO submission (student, assignment, submitdate, content)
                            VALUES (?, ?, datetime('now'), ?);
                            """, (session['user']['uid'], assignment, answer,))
                
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('assignments', assignment=assignment))
            
            else:
                # open database
                conn = sqlite3.connect("app.db")
                # Specify how we want to receive results
                conn.row_factory = sqlite3.Row 
                # Obtain a cursor for executing queries
                cur = conn.cursor()
                cur.execute("""SELECT a.id, a.title, a.description, u.username as teachername, a.tableschema, a.sampleanswer, a.sampleanswer_allowviewing, a.maxscore, IFNULL((SELECT s2.id FROM submission s2, assignment a2 WHERE a2.id=s2.assignment AND s2.active=1 AND a2.active=1 AND s2.student=? AND a2.id=a.id), -1) AS submitted
                            FROM assignment a, user u
                            WHERE a.teacher = u.id
                            AND a.id=?;
                            """, (session['user']['uid'], assignment,))
                assignmentdata=cur.fetchone()
                cur.close()
                conn.close()
                return render_template('submit.html', assignmentdata=assignmentdata)
            
        # if user is not a student, why are you trying to submit?
        else:
            return redirect(url_for('assignments', assignment=assignment))
    #user not logged in
    else:
        return redirect(url_for('login'))
    
@app.route('/assignment/<assignment>/submitted/')
def submittedlist(assignment):
    if 'user' in session:
        # list of students submitted is only visible to teachers
        if session['user']['role']==0:
            abort(403)
        else:
            # open database
            conn = sqlite3.connect("app.db")
            # Specify how we want to receive results
            conn.row_factory = sqlite3.Row 
            # Obtain a cursor for executing queries
            cur = conn.cursor()

            cur.execute("""SELECT date('now') AS currentdate, a.id, a.title, a.description, u.username AS teachername, a.teacher AS teacherid, a.start_date AS startdate, a.end_date as enddate, a.tableschema, a.sampleanswer, a.sampleanswer_allowviewing, a.maxscore, count(s.id) AS submitted
                            FROM assignment a LEFT JOIN (SELECT * FROM submission WHERE active=1) s ON a.id = s.assignment, user u
                            WHERE u.id = a.teacher
                            GROUP BY a.id
                            HAVING a.id=?
                            """, (assignment,))
            assignmentdata=cur.fetchone()

            # if user is not teacher for this assignment and not an admin, 403
            if ((session['user']['uid']!=assignmentdata['teacherid']) and session['user']['role']!=2):
                cur.close()
                conn.close()
                abort(403)

            cur.execute("""
            SELECT u.username AS studentname, scr.score, s.id, s.submitdate, scr.scoredate
            FROM user u, assignment a, submission s LEFT JOIN score scr ON s.id=scr.submission
            WHERE a.id=s.assignment
            AND u.id=s.student
            AND s.active=1
            AND a.id=?
            """, assignment)
            submittedlist=cur.fetchall()
            
            cur.close()
            conn.close()
            return render_template('submittedlist.html', assignmentdata=assignmentdata, submittedlist=submittedlist)
    else:
        return redirect(url_for('login'))


@app.route('/submissions/<submission>', methods=['GET', 'POST'])
def submission(submission=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    #if submission id is not defined, this webpage cannot be displayed
    if (submission is None):
        return redirect(url_for("assignments"))
    
    conn = sqlite3.connect("app.db")
    # Specify how we want to receive results
    conn.row_factory = sqlite3.Row 
    # Obtain a cursor for executing queries
    cur = conn.cursor()
    cur.execute("""SELECT a.id, a.title, a.description, a.teacher AS teacherid, s.content, a.start_date AS startdate, a.end_date AS enddate, s.student as studentid, u.username as studentname, s.submitdate, a.tableschema, a.sampleanswer, a.sampleanswer_allowviewing, a.maxscore, scr.score, s.active, s.id as submission
                        FROM assignment a, user u, submission s LEFT JOIN score scr ON scr.submission = s.id
                        WHERE s.id=?
                        AND s.student=u.id
                        AND s.assignment=a.id;
                        """, (submission,))
    
    #only need to get the data related to the specified assignment
    submissiondata=cur.fetchone()

    #if the selected submission is updated, redirect to newest one
    if (submissiondata['active']==0):
        cur.execute("SELECT id FROM submission WHERE assignment=? AND student=? AND active=1;", (submissiondata['id'], submissiondata['studentid'],))
        newsubmission=cur.fetchone()
        cur.close()
        conn.close()
        return redirect(url_for('submission', submission=newsubmission['id']))

    if (submissiondata['enddate']<=submissiondata['submitdate']):
        assignmentexpired=True
    else:
        assignmentexpired=False

    if (request.method=='GET'):
        cur.close()
        conn.close()

        # if user is not teacher for this assignment and not an admin, 403
        if ((session['user']['uid']!=submissiondata['teacherid']) and session['user']['role']!=2 and session['user']['uid']!=submissiondata['studentid']):
            abort(403)

        return render_template('submission.html', assignmentdata=submissiondata, assignmentexpired=assignmentexpired)
    else:
        # if the user requested to compare
        if request.form['type']=='compare':
            output= submissiondata['tableschema'] + '\n\n'
            output += "query q1 \n`" + submissiondata['sampleanswer'].replace("\r", "").replace(";", "") +'`;\n'
            output += "query q2 \n`" + submissiondata['content'].replace("\r", "").replace(";", "") +'`;\n\n'
            output += "verify q1 q2;\n"

            r = requests.post("https://demo.cosette.cs.washington.edu/solve", 
                  data={"api_key":config.api_key, "query":output}, verify=False)
            
            cosetteout = r.json()
            if cosetteout['result']=='NEQ':
                compareresult={'code':1, 'result': "The queries are not equivalent", 'counterexamples':cosetteout['counterexamples']}
            elif cosetteout['result']=='ERROR':
                compareresult={'code':-1, 'cos':output, 'result':"The queries return an error.", 'error':cosetteout['error_msg'].replace('\\n', '\n').replace('\\\"', '\"')}
            elif cosetteout['result']=='EQ':
                compareresult={'code':0, 'result':"The queries are equivalent"}
            else:
                compareresult={'code':0, 'result':"Cosette cannot prove or disprove the equivalencies of the queries"}
            return render_template('submission.html', assignmentdata=submissiondata, assignmentexpired=assignmentexpired, compareresult=compareresult)

        #if the user requested to set score
        elif request.form['type']=='score':
            #user is not authorized to score
            if ((session['user']['uid']!=submissiondata['teacherid']) and session['user']['role']!=2):
                return redirect(url_for('submission', submission=submission))
            else:
                score=request.form['score']
                cur.execute("SELECT 1 FROM score WHERE submission=?;", (submission,))
                scoreexists=cur.fetchone()

                if (scoreexists):
                    cur.execute("UPDATE score SET score=?, scoredate=datetime('now') WHERE submission=?;", (score, submission,))
                else:
                    cur.execute("INSERT INTO score (submission, score, scoredate) VALUES (?, ?, datetime('now'));", (submission, score,))
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for('submission', submission=submission))


@app.route('/history/', methods=['GET'])
def history():
    if 'user' in session:
        # open database
        conn = sqlite3.connect("app.db")
        # Specify how we want to receive results
        conn.row_factory = sqlite3.Row 
        # Obtain a cursor for executing queries
        cur = conn.cursor()
        
        #for selecting table for students
        if session['user']['role']==0:
            cur.execute("""SELECT a.id, a.title, a.description, a.teacher AS teacherID, a.start_date AS startdate, a.end_date AS enddate, u.username as teachername, IFNULL((SELECT s.id FROM submission s, assignment a2 WHERE a2.id=s.assignment AND s.active=1 AND a2.active=1 AND s.student=? AND a2.id=a.id), -1) AS submitted, a.maxscore, (SELECT scr.score FROM submission s, score scr WHERE s.assignment=a.id AND scr.submission=s.id AND s.student=?) AS score
                        FROM assignment a, user u
                        WHERE a.teacher = u.id
                        AND a.active=1
                        AND startdate<=DATE('now')
                        AND a.id IN (SELECT assignment FROM submission WHERE student=?)
                        ORDER BY startdate DESC;
                        """, (session['user']['uid'], session['user']['uid'], session['user']['uid'],))
            
        #for selecting table for teachers
        else:
            cur.execute("""SELECT a.id, a.title, a.description, a.start_date AS startdate, a.end_date AS enddate, a.maxscore, count(s.id) AS submitted
                        FROM assignment a LEFT JOIN (SELECT * FROM submission WHERE active=1) s ON a.id = s.assignment
                        WHERE a.teacher = ?
                        GROUP BY a.id
                        ORDER BY startdate DESC;
                        """, (session['user']['uid'],))
            
        assignments=cur.fetchall()
        cur.close()
        conn.close()
        return render_template('history.html', assignments=assignments)

@app.route('/sqlcheck/')
def checkinputsql():
    if 'user' in session:
        return render_template('checkinputsql.html')
    else:
        return redirect(url_for('login'))
           
#logs out the user
@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/registerteacher/', methods=['POST', 'GET'])
def registerteacher():
    if (request.method=='POST'):
        username=request.form['username'].lower()
        password=request.form['passw']
        #print(username)
        #print(password)
        # open database
        conn = sqlite3.connect("app.db")
        #print(conn)
        # Specify how we want to receive results
        conn.row_factory = sqlite3.Row 
        # Obtain a cursor for executing queries
        cur = conn.cursor()

        cur.execute("SELECT password FROM user WHERE id=?;", (session['user']['uid'],))
        checkhash=cur.fetchone()
        print(checkhash['password'])

        if (checkhash):
            passwordcorrect=check_password_hash(checkhash['password'], request.form['password'])
        else:
            redirect(url_for('logout'))

        print(passwordcorrect)
        if (not passwordcorrect):
            cur.close()
            conn.close()
            return render_template('registerteacher.html', adminpassword="Admin password incorrect")

        cur.execute("SELECT username FROM user WHERE username = ?;", (username, ))
        #print(userexists)
        userexists = cur.fetchone()
        
        if userexists is not None:
            cur.close()
            conn.close()
            return render_template('registerteacher.html', usernametaken="Username already exists")

        passwordhash=generate_password_hash(password)
        #print(passwordhash)

        f = '%Y-%m-%d %H:%M:%S'
        now = time.gmtime()
        currenttimestamp = time.strftime(f, now)

        try:
            print(currenttimestamp + " REGISTER " + username)
            cur.execute("INSERT INTO user (username, password, datecreated, lastlogin, usertype) VALUES (?, ?, datetime('now'), datetime('now'), 1);", (username, passwordhash,))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('profile', profile=username))
            
        except Exception as e:
            print (e)
            cur.close()
            conn.close()
            print("databasefail")
            return render_template("registerteacher.html", databasefail=True)
        
    else:
        return render_template('registerteacher.html')

@app.route('/result/', methods=['POST', 'GET'])
def results():
    if 'user' not in session:
        return redirect(url_for('login'))
    #if method is incorrect return to input page
    if (request.method!='POST'):
        return redirect(url_for('checkinputsql'))
    
    #check if the user is posting from result page, render seperately
    if 'cosettecode' in request.form:
        cosettecode = request.form['cosettecode']
        cosettecode = cosettecode.replace("\r", "") #sanitize windows newline
        r = requests.post("https://demo.cosette.cs.washington.edu/solve", 
                  data={"api_key":config.api_key, "query":cosettecode}, verify=False)

        cosetteout = r.json()
        #print(cosetteout['result'])
        if cosetteout['result']=='NEQ':
            #print(cosetteout['counterexamples'])
            return render_template('results.html', cos=cosettecode, result="The queries are not equivalent.", counterexamples=cosetteout['counterexamples'])
        elif cosetteout['result']=='ERROR':
            #print(cosetteout['error_msg'])
            return render_template('results.html', cos=cosettecode, result="The queries return an error.", error_msg=cosetteout['error_msg'].replace('\\n', '\n').replace('\\\"', '\"'))
        elif cosetteout['result']=='EQ':
            return render_template('results.html', cos=cosettecode, result="The queries are equivalent.")
        else:
            return render_template('results.html', cos=cosettecode, result="Cosette cannot prove or disprove the equivalencies of the queries")

    else:
        tablenames = request.form.getlist('tablename[]')
        attributenames = request.form.getlist('attributename[]')
        attributetypes = request.form.getlist('attributetype[]')
        attributenum = request.form.getlist('attributenum[]') #list of number of attributes per table
        symbolic = request.form.getlist('symbolic[]') #if symbolic attributes exist
        totalattribute = 0

        # end of line from form could be passed using \r\n, which creates an exception when sent to cosette, sanitize
        # remove ";" at the end of sql because cosette does not accept it
        sql1=request.form['sql1'].replace("\r", "").replace(";", "")
        sql2=request.form['sql2'].replace("\r", "").replace(";", "")

        output = ""

        for j in range(0, len(attributenum)):
            #output : schema s1(uid:int, uname:varchar, city:int);
            output += "schema s" + str(j) + "("
            for i in range(0, int(attributenum[j])):
                #add comma if there exists a prior element
                if (i>0):
                    output += ", "
                output += attributenames[totalattribute] + ":" + attributetypes[totalattribute]
                totalattribute+=1
            if symbolic[j] == 1:
                output += ", ??"
            output += ");\n"
            #output : table user(s1);
            output += "table " + tablenames[j] + "(s" + str(j) +");\n\n"
        
        output += "query q1 \n`" + sql1 +'`;\n'
        output += "query q2 \n`" + sql2 +'`;\n\n'
        output += "verify q1 q2;\n"
        
        r = requests.post("https://demo.cosette.cs.washington.edu/solve", 
                    data={"api_key":config.api_key, "query":output}, verify=False)

        cosetteout = r.json()
        #print(cosetteout['result'])
        if cosetteout['result']=='NEQ':
            #print(cosetteout['counterexamples'])
            return render_template('results.html', cos=output.replace("\n", "\r\n"), sql1=sql1, sql2=sql2, result="The queries are not equivalent.", counterexamples=cosetteout['counterexamples'])
        elif cosetteout['result']=='ERROR':
            #print(cosetteout['error_msg'])
            return render_template('results.html', cos=output.replace("\n", "\r\n"), sql1=sql1, sql2=sql2, result="The queries return an error.", error_msg=cosetteout['error_msg'].replace('\\n', '\n').replace('\\\"', '\"'))
        elif cosetteout['result']=='EQ':
            return render_template('results.html', cos=output.replace("\n", "\r\n"), sql1=sql1, sql2=sql2, result="The queries are equivalent.")
        else:
            return render_template('results.html', cos=output.replace("\n", "\r\n"),sql1=sql1, sql2=sql2, result="Cosette cannot prove or disprove the equivalencies of the queries")


if __name__ == "__main__":
    app.debug = True
    app.secret_key = config.secret_key
    app.run(port=5000)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
