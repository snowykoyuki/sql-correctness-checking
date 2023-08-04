--table to store user data
CREATE TABLE user(
 id int PRIMARY KEY AUTO_INCREMENT,
 username varchar(16) UNIQUE,
 password varbin(1024),
 usertype tinyint DEFAULT 0, -- 0 student, 1 teacher, 2 admin
 datecreated datetime DEFAULT CURRENT_TIMESTAMP(),
 lastlogin timestamp DEFAULT CURRENT_TIMESTAMP(), 
 active bool DEFAULT 1 --banned user 0
);

--table to store teacher-student relationships
CREATE TABLE subscription(
 teacher int,             --user foreign key
 student int,             --user foreign key
 datsubscribed timestamp DEFAULT CURRENT_TIMESTAMP(), --date when student sub/unsubscribed to teacher
 active bool DEFAULT 1,   --end subscription 0
 PRIMARY KEY (teacher, student),
 FOREIGN KEY (teacher) REFERENCES user(id),
 FOREIGN KEY (student) REFERENCES user(id)
);

--table to store teacher assignments
CREATE TABLE assignment(
 id int PRIMARY KEY AUTO_INCREMENT,
 title varchar(128),        --title for assignment
 description varchar(2048),
 teacher int,               --user foreign key
 start_date timestamp,
 end_date timestamp,        --deadline for assignment
 sample_answer mediumtext,  --teacher provided answer
 active bool DEFAULT 1,     --deleted assignment 0
 FOREIGN KEY (teacher) REFERENCES user(id)
);

--table to store student submissions to assignments
CREATE TABLE submission(
 id int PRIMARY KEY AUTO_INCREMENT,
 student int,              --user foreign key
 assignment int,           --assignment foreign key
 submitdate timestamp DEFAULT CURRENT_TIMESTAMP(), --date submitted
 content mediumtext,
 active bool DEFAULT 1,    --deleted submission 0
 FOREIGN KEY (student) REFERENCES user(id),
 FOREIGN KEY (assignment) REFERENCES assignment(id)
);