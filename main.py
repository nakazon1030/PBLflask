import re
from flask import Flask, render_template, request
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
import MySQLdb
import html
import datetime

def connect():
    con = MySQLdb.connect(
        host="localhost",
        user="root",
        password="1030",
        db="pbldb",
        use_unicode=True,
        charset="utf8")
    return con


app = Flask(__name__)

@app.route("/")
@app.route("/index")
def main():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", msg="新規登録をしてください")

    elif request.method == "POST":
        user_id = request.form.get("user_id")
        name = request.form.get("name")
        password = request.form.get("password")
        password_sam = request.form.get("password_sam")
        group_id = request.form.get('group_id')
        group_password = request.form.get('group_password')

        if password == password_sam:
            hashpass = gph(password)
            con = connect()
            cur = con.cursor()
            cur.execute("""
                        SELECT * FROM user WHERE user_id=%(user_id)s
                        """,{"user_id":user_id})
            data=[]
            for row in cur:
                data.append(row)
            if len(data)!=0:
                return render_template(register.html, msg="すでに使用されているユーザー名です。")
            con.commit()
            con.close()

            #グループIDとパスワードの照合
            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT pass 
                          FROM grouplist
                          WHERE group_id=%(id)s
                        """, {"id":group_id})
            data=[]
            for row in cur:
                data.append(row[0])
            if len(data)==0:
                con.close()
                return render_template("register.html", msg = "組織IDが存在しません")
            if cph(data[0], group_password):
                con.close()
                #登録処理に移行
            else:
                con.close()
                return render_template("login.html", msg="組織パスワードが間違っています")
            
            #登録処理
            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO user
                        (user_id,user_name,pass,group_id)
                        VALUES ("%(user_id)s", %(name)s, %(pass)s,"%(group_id)s")
                        """,{"user_id":user_id, "name":name, "pass":hashpass, "group_id":group_id} )

            con.commit()
            con.close()
            return render_template("home.html")
        
        elif password != password_sam:
            return render_template("register.html", msg="パスワードが一致しません")


@app.route("/gregister", methods=["GET","POST"])
def group_register():
    if request.method == "GET":
        return render_template("gregister.html", msg="新規登録をしてください")

    elif request.method == "POST":
        group_id = request.form.get("group_id")
        group_name = request.form.get("group_name")
        password = request.form.get("password")
        password_sam = request.form.get("password_sam")

        if password == password_sam:
            hashpass = gph(password)

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        SELECT * FROM grouplist WHERE group_id=%(id)s
                        """, {"id":group_id})
            data = []
            for row in cur:
                data.append(row)
            if len(data)!=0:
                return render_template("gregister.html", msg="すでに存在するメールアドレスです")
            con.commit()
            con.close()

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO grouplist
                        (group_id,group_name,pass)
                        VALUES ("%(id)s", %(name)s, %(pass)s)
                        """,{"id":group_id, "name":group_name, "pass":hashpass} )

            con.commit()
            con.close()
            return render_template("index.html")
        
        elif password != password_sam:
            return render_template("gregister.html", msg="パスワードが一致しません")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]
        con = connect()
        cur = con.cursor()
        cur.execute("""
                    SELECT pass
                    FROM user
                    WHERE user_id=%(id)s
                    """,{"id",user_id})
        data=[]
        for row in cur:
            data.append(row[0])
        if len(data)==0:
            con.close()
            return render_template("login.html", msg="IDが間違っています")
        if cph(data[0], password):
            con.close()
            return render_template("home.html")
        else:
            con.close()
            return render_template("login.html", msg="パスワードが間違っています")


@app.route("/home", methods=["GET","POST"])
def home():
    #タスク・タスクリスト表示,消去,完了,未完了(未実装)
    return render_template("home.html")

@app.route("/create-tasklist", methods=["GET","POST"])
def createtasklist():
    ##タスクリスト追加処理
    if request.method == "GET":
        return render_template("create-tasklist.html", msg="タスクリストを登録してください")

    elif request.method == "POST":
        name = request.form.get("name")
        body = request.form.get("body")
        date = datetime.date.today()

        con = connect()
        cur = con.cursor()
        cur.execute("""
                    INSERT INTO tasklist
                    (tasklist_name,body,date)
                    VALUES (%(name)s, %(body)s, %(date)s)
                    """,{"name":name, "body":body, "date":date} )

        con.commit()
        con.close()

    return render_template("home.html")
    
@app.route("/edit-tasklist", methods=["GET","POST"])
def edittasklist():
    ##タスクリスト更新処理
    if request.method == "GET":
        return render_template("edit-tasklist.html", msg="タスクリストを登録してください")

    elif request.method == "POST":
        name = request.form.get("name")
        body = request.form.get("body")
        id = 3
        date = datetime.date.today()

        con = connect()
        cur = con.cursor()
        cur.execute("""
                     UPDATE tasklist
                     SET    tasklist_name = %(name)s, body = %(body)s, date = %(date)s
                     WHERE  tasklist_id = %(id)s
                    """,{"name":name, "body":body, "date":date, "id":id})

        con.commit()
        con.close()
    return render_template("home.html")


@app.route("/create-task", methods=["GET","POST"])
def createtask():
    ##タスク追加処理
    if request.method == "GET":
        return render_template("create-task.html", msg="タスクリストを登録してください")

    elif request.method == "POST":
        name = request.form.get("name")
        body = request.form.get("body")
        date = datetime.date.today()
        status = 0

        con = connect()
        cur = con.cursor()
        cur.execute("""
                    INSERT INTO task
                    (task_name,body,date,status)
                    VALUES (%(name)s, %(body)s, %(date)s, %(status)s)
                    """,{"name":name, "body":body, "date":date, "status":status} )

        con.commit()
        con.close()

    return render_template("home.html")
    
@app.route("/edit-task", methods=["GET","POST"])
def edittask():
    ##タスク更新処理
    if request.method == "GET":
        return render_template("edit-task.html", msg="タスクを更新してください")

    elif request.method == "POST":
        name = request.form.get("name")
        body = request.form.get("body")
        status = request.form.get("status")
        id = 1
        date = datetime.date.today()

        con = connect()
        cur = con.cursor()
        cur.execute("""
                     UPDATE task 
                     SET    task_name = %(name)s, body = %(body)s, date = %(date)s, status = %(status)s
                     WHERE  task_id = %(id)s
                    """,{"name":name, "body":body, "date":date,"status":status, "id":id})

        con.commit()
        con.close()
    return render_template("home.html")



if __name__ == "__main__":
        ##db.create_all()
        app.run(debug=True)
