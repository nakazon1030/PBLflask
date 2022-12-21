import re
from flask import Flask, render_template, request, session, redirect, jsonify
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from datetime import timedelta
import MySQLdb
import html
import datetime 
import secrets
import numpy as np
import dicttoxml

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
app.config['JSON_AS_ASCII'] = False

@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

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
        user_id = html.escape(request.form.get("user_id"))
        name = html.escape(request.form.get("name"))
        password = html.escape(request.form.get("password"))
        password_sam = html.escape(request.form.get("password_sam"))
        group_name = html.escape(request.form.get("group_name"))
        group_password = html.escape(request.form.get("group_password"))

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
                return render_template("register.html", msg="すでに使用されているユーザー名です。")
            con.commit()
            con.close()

            #グループIDとパスワードの照合
            con = connect()
            cur = con.cursor()
            cur.execute("""SELECT pass 
                          FROM grouplist
                          WHERE group_name = %(id)s
                        """, {"id":group_name})
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
                        (user_id,user_name,pass,group_name)
                        VALUES (%(user_id)s, %(name)s, %(pass)s,%(group_name)s)
                        """,{"user_id":user_id, "name":name, "pass":hashpass, "group_name":group_name} )
            con.commit()   
            con.close()


            session["group_name"] = group_name
            session["user_id"] = user_id
            session["name"] = name



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
        group_name = html.escape(request.form.get("group_name"))
        password = html.escape(request.form.get("password"))
        password_sam = html.escape(request.form.get("password_sam"))

        if password == password_sam:
            hashpass = gph(password)

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        SELECT * FROM grouplist WHERE group_name=%(id)s
                        """, {"id":group_name})
            data = []
            for row in cur:
                data.append(row)
            if len(data)!=0:
                return render_template("gregister.html", msg="すでに存在する組織名です")
            con.commit()
            con.close()

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO grouplist
                        (group_name,pass)
                        VALUES (%(id)s, %(pass)s)
                        """,{"id":group_name, "pass":hashpass} )

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
        user_id = html.escape(request.form.get("user_id"))
        password = html.escape(request.form.get("password"))
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
            cur.execute("""SELECT group_name 
                        FROM user
                        WHERE user_id = %(id)s
                    """, {"id":user_id})
            for row in cur:
                group_name = row[0]
            con.commit()   
            con.close()

            session["group_name"] = group_name
            session["user_id"] = user_id
            session["name"] = name

            return redirect("/home")
        else:
            con.close()
            return render_template("login.html", msg="パスワードが間違っています")


@app.route("/home", methods=["GET"])
def home():
    #タスク表示
    if "group_name" in session:
        group_name = session["group_name"]
        user_name = session["name"]
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT *
                        FROM task
                        WHERE group_name = %(id)s
                    """, {"id":group_name})
        data = [] 
        for row in cur:
            data.append(row)
        
        con.close()
        
        return render_template("home.html", tasklist = data, group_name = group_name, user_name=user_name)
    else:
        return redirect("/")
@app.route("/create", methods=["GET","POST"])
def create():
    ##タスク追加処理
    if "group_name" in session:
        if request.method == "GET":
            return render_template("create.html", msg="タスクを登録してください")

        elif request.method == "POST":
            name = html.escape(request.form.get("name"))
            body = html.escape(request.form.get("body"))
            date = datetime.date.today()
            user = session["name"]
            group_name = session["group_name"]
            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO task
                        (group_name,task_name,body,date,status,create_user,user_name)
                        VALUES (%(id)s,%(name)s, %(body)s, %(date)s,0,%(user)s,%(user)s)
                        """,{"id":group_name,"name":name, "body":body, "date":date, "user":user} )

            con.commit()
            con.close()
            return redirect("/home")
    else:
        return redirect("/")
    
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    ##タスク更新処理
    if "group_name" in session:
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT group_name
                        FROM task
                        WHERE task_id = %(id)s
                    """, {"id":id})
            
        for row in cur:
            group_name = row[0]
        con.close()
        if session["group_name"] == group_name:
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
                name = html.escape(request.form.get("name"))
                body = html.escape(request.form.get("body"))
                date = datetime.date.today()
                user = session["name"]

                con = connect()
                cur = con.cursor()
                cur.execute("""
                            UPDATE task
                            SET    task_name = %(name)s, body = %(body)s, date = %(date)s, user_name = %(user)s
                            WHERE  task_id = %(id)s
                            """,{"name":name, "body":body, "date":date, "id":id, "user":user})

                con.commit()
                con.close()
            return redirect("/home")
        else:
            return redirect("/home")
    else:
        redirect("/")

@app.route("/status1/<int:id>", methods=["GET"])
def status1(id):
    ##タスク完了処理
    if "group_name" in session:
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT group_name
                        FROM task
                        WHERE task_id = %(id)s
                    """, {"id":id})
            
        for row in cur:
            group_name = row[0]
        con.close()
        if session["group_name"] == group_name:
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
        else:
            return redirect("/home")
    else :
        return redirect("/")

@app.route("/status0/<int:id>", methods=["GET"])
def status0(id):
    ##タスク未完了処理
    if "group_name" in session:
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT group_name
                        FROM task
                        WHERE task_id = %(id)s
                    """, {"id":id})
            
        for row in cur:
            group_name = row[0]
        con.close()
        if session["group_name"] == group_name:
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
        else:
            return redirect("/home")
    else :
        return redirect("/")

@app.route("/delete/<int:id>", methods=["GET"])
def delete(id):
    ##タスク未完了処理
    if "group_name" in session:
        con = connect()
        cur = con.cursor()
        cur.execute("""SELECT group_name
                        FROM task
                        WHERE task_id = %(id)s
                    """, {"id":id})
            
        for row in cur:
            group_name = row[0]
        con.close()
        if session["group_name"] == group_name:
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
            return redirect("/home")
    else :
        return redirect("/")
@app.route("/logout")
def logout():
    #ログアウト処理
    session.clear()
    return redirect("/")

@app.route("/json/<group_name>", methods=["GET"])
def json(group_name):
    ##json出力処理
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT *
                    FROM task
                    WHERE group_name = %(id)s
                """, {"id":group_name})
    tasklist = [] 
    for row in cur:
        tasklist.append(row)
    con.close()
    dic = {}
    dic["team_name"] = group_name

    for task in tasklist:
        dic[task[2]+"_name"] = task[2]
        dic[task[2]+"_body"] = task[3]
        dic[task[2]+"_date"] = task[4]
        dic[task[2]+"_status"] = task[5]

    return jsonify(dic)

@app.route("/xml/<group_name>", methods=["GET"])
def xml(group_name):
    ##xml出力処理 
    con = connect()
    cur = con.cursor()
    cur.execute("""SELECT *
                    FROM task
                    WHERE group_name = %(id)s
                """, {"id":group_name})
    tasklist = [] 
    for row in cur:
        tasklist.append(row)
    con.close()
    dic = {}
    dic["team_name"] = group_name

    for task in tasklist:
        dic[task[2]+"_name"] = task[2]
        dic[task[2]+"_body"] = task[3]
        dic[task[2]+"_date"] = task[4]
        dic[task[2]+"_status"] = task[5]
    
    xml = dicttoxml.dicttoxml(dic)
    resp = app.make_response(xml)
    resp.mimetype = "text/xml"

    return resp


if __name__ == "__main__":
        ##db.create_all()
        app.run(debug=True)