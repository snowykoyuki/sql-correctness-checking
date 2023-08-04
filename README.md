# sql-correctness-checking
This project attempts to adress the gap in technology where engines for the verification of SQL equivalencies are not put into use in education. 

There are three types of users: Admin, Teacher, and Student.
Through the system, 
Teachers can:
- Put out assignments for students;
- Change whether students are allowed to check answers for the assignments;
- Check submission status of students;
- See the content of students’ submissions;
- Write feedback and give score to students; and
- Check the equivalencies of two SQL statements by direct input. If not, also show counterexamples.
 
Students can: 
- Follow teacher accounts;
- Check followed accounts assignments;
- Submit answers to teachers’ assignments;
- Check state of own submission;
- Modify own submissions (if before deadline);
- Check whether the assignment is done correctly using Cosette (if allowed by teacher); and
- Check the equivalencies of two SQL statements by direct input. If not, also show counterexamples.


Admins can: 
- Disable any account;
- Create teacher account; and
- All teacher permissions.


## How to install
1. Download and install [Python 3.6](https://www.python.org/downloads/)
2. Install the latest version of pip (`python -m ensurepip --upgrade`)
3. Run the following commands:
    ```
    pip install pycryptodome
    pip install flask
    pip install flask-session
    pip install requests
    ```

    If you built Python from source, you should also run this:
    ```
    pip install pysqlite3 
    ```
    
    if `python3` is used, replace `pip` with `pip3`
4. Download the source code

## Setup
1. Open terminal
2. Navigate to the directory with the source code
3. Move the directory to another location if necessary
4. Ensure you have a stable internet connection
5. Ensure you have permissions to execute files and modify files in the directory
6. Run `python main.py` (if python is python 3)/`python3 main.py` (Linux)/`py main.py` (Windows)
7. Access the website on any browser using `<ip/domain>:5000`

## How to use
A default admin user with username `admin` and password `admin` has been created by default.

To create a teacher account, log in using the admin account and click on "user" in the navigation menu.

To create a student account, click on register after logging out.

Log in as each role to use the role specific functionalities.
