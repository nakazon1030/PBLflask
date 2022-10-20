from flask import Flask, render_template, request
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

            """グループIDとパスワードの照合(未作成)
            con = connect()
            cur = con.cursor()
            cur.excute("""""")
            con.commit()
            con.close()
            """

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO usertable
                        (user_id,user_name,pass,group_id)
                        VALUES ("%(user_id)s", %(name)s, %(pass)s,"%(group_id)s")
                        """,{"user_id":user_id, "name":name, "pass":password, "group_id":group_id} )

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

            con = connect()
            cur = con.cursor()
            cur.execute("""
                        INSERT INTO grouptable
                        (group_id,group_name,pass)
                        VALUES ("%(id)s", %(name)s, %(pass)s)
                        """,{"id":group_id, "name":group_name, "pass":password} )

            con.commit()
            con.close()
            return render_template("home.html")
        
        elif password != password_sam:
            return render_template("gregister.html", msg="パスワードが一致しません")

@app.route("/login", methods=["GET","POST"])
def login():
    ##ログイン処理(未実装)
    return render_template("login.html")

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

        con = connect()
        cur = con.cursor()
        cur.execute("""
                    INSERT INTO tasklisttable
                    (tasklist_name,body)
                    VALUES ("%(name)s", "%(body)s")
                    """,{"name":name, "body":body} )

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
        id = "0000000000000001"

        con = connect()
        cur = con.cursor()
        cur.execute("""
                     UPDATE tasklisttable
                     SET name = "%(name)s" body = "%(body)s"
                     WHERE tasklist_id = "%(id)d"
                    """,{"id" :id, "name":name, "body":body} )

        con.commit()
        con.close()
    return render_template("home.html")


@app.route("/task", methods=["GET","POST"])
def task():
    ##タスク追加,修正処理
    return render_template("task.html")


if __name__ == "__main__":
        ##db.create_all()
        app.run(debug=True)
