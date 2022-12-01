import re
from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from datetime import timedelta
import MySQLdb
import html
import datetime 
import secrets
import numpy as np

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
app.secret_key = secrets.token_urlsafe(16)
app.permanent_session_lifetime = timedelta(minutes=60)

@app.route("/")
@app.route("/index")
def main():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        session.clear()
        return render_template("register.html", msg="新規登録をしてください")

    elif request.method == "POST":
        user_id = request.form.get("user_id")
        name = request.form.get("name")
        password = request.form.get("password")
        password_sam = request.form.get("password_sam")
        group_id = request.form.get("group_id")
        group_password = request.form.get("group_password")

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
                          WHERE group_id = %(id)s
                        """, {"id":group_id})
            data=[]
            for row in cur:
                data.append(row[0])
            if len(data)==0:
                con.close()
                return render_template("register.html", msg = "組織IDが存在しません")
            elif cph(data[0], group_password):
                con.close()
                #登録処理に移行

            else:
                con.close()
                return render_template("register.html", msg="組織パスワードが間違っています") 
            
            #登録処理
            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO user
                        (user_id,user_name,pass,group_id)
                        VALUES (%(user_id)s, %(name)s, %(pass)s,%(group_id)s)
                        """,{"user_id":user_id, "name":name, "pass":hashpass, "group_id":group_id} )
            con.commit()   
            con.close()

            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT group_name 
                        FROM grouplist
                        WHERE group_id = %(id)s
                    """, {"id":group_id})
            
            group_name = row
            con.commit()   
            con.close()

            session["group_id"] = group_id
            session["user_id"] = user_id
            session["name"] = name
            session["group_name"] = group_name


            return redirect("/home")
        
        elif password != password_sam:
            return render_template("register.html", msg="パスワードが一致しません")
        
        else:
            return render_template("register.html", msg="エラー")


@app.route("/gregister", methods=["GET","POST"])
#グループ登録処理
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
                        VALUES (%(id)s, %(name)s, %(pass)s)
                        """,{"id":group_id, "name":group_name, "pass":hashpass} )

            con.commit()
            con.close()
            return redirect("/register")
        
        elif password != password_sam:
            return render_template("gregister.html", msg="パスワードが一致しません")

@app.route("/login", methods=["GET","POST"])
#ログイン処理
def login():
    if request.method == "GET":
        session.clear()
        return render_template("login.html")
    elif request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT pass 
                        FROM user
                        WHERE user_id = %(id)s
                    """, {"id":user_id})
        data=[]
        for row in cur:
            data.append(row[0])
        if len(data)==0:
            con.close()
            return render_template("login.html", msg="IDが間違っています")
        if cph(data[0], password):
               
            con.close()

            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT user_name 
                        FROM user
                        WHERE user_id = %(id)s
                    """, {"id":user_id})
            for row in cur:
                name = row[0]
            con.commit()   
            con.close()
            
            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT group_id 
                        FROM user
                        WHERE user_id = %(id)s
                    """, {"id":user_id})
            for row in cur:
                group_id = row[0]
            con.commit()   
            con.close()

            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT group_name
                        FROM grouplist
                        WHERE group_id = %(id)s
                    """, {"id":group_id})
            for row in cur:
                group_name = row[0]
            con.commit()   
            con.close()

            session["group_id"] = group_id
            session["user_id"] = user_id
            session["name"] = name
            session["group_name"] = group_name

            return redirect("/home")
        else:
            con.close()
            return render_template("login.html", msg="パスワードが間違っています")


@app.route("/home", methods=["GET"])
def home():
    #タスク表示
    if "group_id" in session:
        group_name = session["group_name"]
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT *
                        FROM task
                        WHERE group_id = %(id)s
                    """, {"id":group_name})
        data = [] 
        for row in cur:
            data.append(row)
        
        con.close()
        
        return render_template("home.html", tasklist = data, group_name = group_name)
    else:
        return redirect("/")
@app.route("/create", methods=["GET","POST"])
def create():
    ##タスク追加処理
    if "group_id" in session:
        if request.method == "GET":
            return render_template("create.html", msg="タスクを登録してください")

        elif request.method == "POST":
            name = request.form.get("name")
            body = request.form.get("body")
            date = datetime.date.today()
            group_id = session["group_id"]
            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO task
                        (group_id,task_name,body,date,status)
                        VALUES (%(id)s,%(name)s, %(body)s, %(date)s,0)
                        """,{"id":group_id,"name":name, "body":body, "date":date} )

            con.commit()
            con.close()
            return redirect("/home")
    else:
        return redirect("/")
    
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    ##タスク更新処理
    if "group_id" in session:
        if request.method == "GET":

            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT *
                            FROM task
                            WHERE task_id = %(id)s
                        """, {"id":id})
            
            for row in cur:
                title = row[2]
                body = row[3]
            
            con.close()
            return render_template("edit.html", msg="タスクリストを編集してください", title = title, body = body, id = id)

        elif request.method == "POST":
            name = request.form.get("name")
            body = request.form.get("body")
            date = datetime.date.today()

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        UPDATE task
                        SET    task_name = %(name)s, body = %(body)s, date = %(date)s
                        WHERE  task_id = %(id)s
                        """,{"name":name, "body":body, "date":date, "id":id})

            con.commit()
            con.close()
        return redirect("/home")
    else:
        redirect("/")

@app.route("/status1/<int:id>", methods=["GET"])
def status1(id):
    ##タスク完了処理
    if "group_id" in session:
        date = datetime.date.today()

        con = connect()
        cur = con.cursor()
        cur.execute("""
                        UPDATE task
                        SET    status = "1", date = %(date)s
                        WHERE  task_id = %(id)s
                    """,{"date":date, "id":id})

        con.commit()
        con.close()
        return redirect("/home")
    else :
        return redirect("/")

@app.route("/status0/<int:id>", methods=["GET"])
def status0(id):
    ##タスク未完了処理
    if "group_id" in session:
        date = datetime.date.today()

        con = connect()
        cur = con.cursor()
        cur.execute("""
                        UPDATE task
                        SET    status = "0", date = %(date)s
                        WHERE  task_id = %(id)s
                    """,{"date":date, "id":id})

        con.commit()
        con.close()
        return redirect("/home")
    else :
        return redirect("/")

@app.route("/delete/<int:id>", methods=["GET"])
def delete(id):
    ##タスク未完了処理
    if "group_id" in session:

        con = connect()
        cur = con.cursor()
        cur.execute("""
                        DELETE FROM task
                        WHERE  task_id = %(id)s
                    """,{"id":id})

        con.commit()
        con.close()
        return redirect("/home")
    else :
        return redirect("/")
@app.route("/logout")
def logout():
    #ログアウト処理
    session.clear()
    return redirect("/")


if __name__ == "__main__":
        ##db.create_all()
        app.run(debug=True)
