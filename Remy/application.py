import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# 利用helper作為外部customised library
# 可以至helper.py增加或刪減
from helpers import apology, login_required, usd

# 新增日期功能
import time


# Configure application
# python設定配置為flask
app = Flask(__name__)


# Ensure templates are auto-reloaded
# 配置自動更新所有的html頁面
# 更改模板時重新加載模板。如果未設置，它將在調試模式下啟用。
# https://flask.palletsprojects.com/en/1.0.x/config/
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
# 更改所有標頭，設定HTTP環境
# https://ithelp.ithome.com.tw/articles/10205041
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
# 環境中設定使用jinja語法時
# 使用usd函數，讓此數值加上錢幣符號
app.jinja_env.filters["usd"] = usd


# Configure session to use filesystem (instead of signed cookies)
# SESSION_FILE_DIR就是指這些傳送的資料儲存位置，這裡用mkdtemp()開一個暫存資料夾
# SESSION_PERMANENT若為False，瀏覽器關閉，再開啟就要重新登入，不會一直登入
# 上述資料主要儲存在cs50 IDE
app.config["SESSION_FILE_DIR"] = mkdtemp() #暫存資料夾
app.config["SESSION_PERMANENT"] = False #session不會永久儲存，關閉將會消失
app.config["SESSION_TYPE"] = "filesystem"
Session(app) #讓此程式可以使用flask_session，把user id儲存於cs50 IDE裡


# Configure CS50 Library to use SQLite database
# 配置CS50的SQL資料庫
db = SQL("sqlite:///finance.db")


##############################################################################################
######################### 自行定義的頁面功能 ##################################################
##############################################################################################


##################
# 首頁，待修正問題
##################
# login_required函式是flask官方文件的建議寫法
# 就是說要求進入網站時，會先檢查session的user_id，看需不需要登入，之後每個功能都需要登入，所以都要附上去
# 在templates裡面的index.html裡，製作一份表格，把這裡的欄位用迴圈方式丟入
# @app.route("/") - 修改總結呈現最後的資料彙總
@app.route("/")
@login_required
def index():   
    # 篩選所有資料
    rows = db.execute("""
        SELECT type, name, amount, note
        FROM account
        WHERE user_id = :user_id
        GROUP by name
        HAVING amount >0;
    """, user_id=session["user_id"])
    # 設定變數
    A_balances = []
    L_balances = []
    R_balances = []
    E_balances = []
    grand_asset = 0
    grand_liability = 0
    grand_revenue = 0
    grand_expense = 0
    balance = 0
    profit = 0
    # 把使用者過去交易儲存
    for row in rows:
        # 資產總額
        if row["type"] == "A":
            A_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_asset += row["amount"]
        # 負債總額
        elif row["type"] == "L":
            L_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_liability += row["amount"]
        # 收入總額
        elif row["type"] == "R":
            R_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_revenue += row["amount"]
        else: # row["type"] == "E": 費用總額
            E_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_expense += row["amount"]
    # 計算剩餘價值
    balance = usd(grand_asset - grand_liability)
    # 計算結餘
    profit = usd(grand_revenue - grand_expense)
    print("Now Running index()")
    print("使用者所有歷史交易 {rows}".format(rows=rows))   
    print("資產總額 {grand_asset}, 負債總額 {grand_liability}, 收入總額 {grand_revenue} 及費用總額 {grand_expense}".format(grand_asset=grand_asset, grand_liability=grand_liability, grand_revenue=grand_revenue, grand_expense=grand_expense))
    print("剩餘價值 {balance}, 結餘 {profit}".format(balance=balance, profit=profit))
    return render_template("index.html", A_balances=A_balances, L_balances=L_balances, R_balances=R_balances, E_balances=E_balances, balance=balance, profit=profit)


###########################
# 新增會計科目，待修正問題
###########################
@app.route("/add_account", methods=["GET", "POST"])
@login_required
def add_account():
    if request.method == "POST":
        # 確認是否來自於選單
        if request.form.get("type") not in ["A", "L", "R", "E"]:
            return apology("The Type Only Accept Asset, Liability, Revenue or Expense", 403)
        # 若無輸入name, amount or note
        find_missing_errors = is_provided("name") or is_provided("amount") or is_provided("amount")
        if find_missing_errors:
            return find_missing_errors
        # 若amount不是金額
        elif not request.form.get("amount").isdigit():
            return apology("invalid amount, please enter 0-9")
        # 搜尋account資料
        rows = db.execute("SELECT name, type FROM account WHERE name = :name AND user_id = :user_id",
                          user_id = session["user_id"],
                          name=request.form.get("name"))
        # 是否共用會計科目
        if request.form.get("share") != "":
            # 搜尋好友資料
            rows_friend = db.execute("SELECT username FROM friends WHERE user_id = :user_id AND username = :username",
                            user_id = session["user_id"],
                            username=request.form.get("share"))
            # 如果好友資料找不到，代表尚未新增         
            if len(rows_friend) != 1:
                return apology("Add friend first", 403)
        
        # 如果account資料找不到，代表尚未新增           
        if len(rows) != 1:
            #用自己的id搭配account名稱(account名稱已UNIQUE，且分辦大小寫)
            db.execute("""INSERT INTO account (user_id,type,name,amount,note,share,initial) VALUES (:user_id,:type,:name,:amount,:note,:share,:initial) """,
            user_id = session["user_id"],
            type=request.form.get("type"),
            name=request.form.get("name"),
            amount=request.form.get("amount"),
            note=request.form.get("note"),
            share=request.form.get("share"),
            initial=request.form.get("amount")
            )
            flash("Add Successfully!")
            print("Now Running add_account()")
            print("新增會計科目 {newaccount}".format(newaccount=request.form.get("name")))
            return render_template("add_account.html")
        #account已存在account database中
        else:
            return apology("Account already exised", 403)
    # request.method == "GET"         
    else:
        return render_template("add_account.html")
        
    
###########################
# 分錄，待修正問題
###########################
# 歷史交易保存
@app.route("/journalentry", methods=["GET", "POST"])
@login_required
def journalentry():
    """記錄一筆分錄"""
    if request.method == "POST":
        # 若無輸入debit or credit or amount
        find_missing_errors = is_provided("debit") or is_provided("credit") or is_provided("amount")
        if find_missing_errors:
            return find_missing_errors
        # 若amount不是金額
        elif not request.form.get("amount").isdigit():
            return apology("invalid amount, please enter 0-9")
        # 轉換變數
        debit = request.form.get("debit")
        credit = request.form.get("credit")
        amount = int(request.form.get("amount"))
        note = request.form.get("note")
        
        
        ################
        # 確認是否有該科目
        ################
        rows_debit = db.execute("SELECT type, name, amount FROM account WHERE name = :debit and user_id=:user_id",
                         user_id=session["user_id"],
                         debit=debit
                         )
        rows_credit = db.execute("SELECT type, name, amount FROM account WHERE name = :credit and user_id=:user_id",
                         user_id=session["user_id"],
                         credit=credit
                         )
        print("使用者會計科目資料庫搜尋結果")
        print(rows_debit, rows_credit)            
        #確認account.db是否有該account
        #找到資料 >>> [{'name': 'cash'}]
        #找不到資料 >>> []
        if len(rows_debit) != 1:
            flash("please add new debit account")
            return render_template("add_account.html")
        if len(rows_credit) != 1:
            flash("please add new credit account")
            return render_template("add_account.html")
        
        
        #############
        # 更新借貸金額
        #############
        # 從資料庫拉出借方科目金額
        debittype = rows_debit[0]["type"]
        debitamount = rows_debit[0]['amount']
        # 從資料庫拉出貸方科目金額
        credittype = rows_credit[0]["type"]
        creditamount = rows_credit[0]['amount']
        # 確認借方是否足夠
        # 禁止借方科目為負
        if debittype == "A" or debittype == "E":
            updated_debitamount = debitamount + amount
        else:
            updated_debitamount = debitamount - amount
        if updated_debitamount < 0:
            return apology("debit account cannot be negative")
        # 確認貸方是否足夠
        # 禁止貸方科目為負
        if credittype == "A" or credittype == "E":
            updated_creditamount = creditamount - amount
        else:
            updated_creditamount = creditamount + amount
        if updated_creditamount < 0:
            return apology("credit account cannot be negative")
        # 更新借方金額
        db.execute("UPDATE account SET amount = :updated_debitamount WHERE name = :debit and user_id=:user_id",
                debit=debit,
                updated_debitamount=updated_debitamount, 
                user_id=session["user_id"])
        # 更新貸方金額
        db.execute("UPDATE account SET amount = :updated_creditamount WHERE name = :credit and user_id=:user_id",
                credit=credit,
                updated_creditamount=updated_creditamount, 
                user_id=session["user_id"])
        print("Now Running jornalentry() 更新會計科目資料庫餘額")
        print("更新借方金額 {rows_debit}: {updated_debitamount}".format(rows_debit=rows_debit, updated_debitamount=updated_debitamount))
        print("更新貸方金額 {rows_credit}: {updated_creditamount}".format(rows_credit=rows_credit, updated_creditamount=updated_creditamount))    
        
        
        ################
        # 加入歷史交易分錄
        ################
        db.execute(""" 
            INSERT INTO transactions
                (user_id, debit, credit, amount, note) 
            VALUES (:user_id, :debit, :credit, :amount, :note)
            """,
                user_id = session["user_id"],
                debit = debit,
                credit = credit,
                amount = amount,
                note = note
            )
        flash("You are a Good Accountant!")
        print("Now Running jornalentry() 成功加入歷史交易分錄")
        return redirect("/history")
    
    else:
        return render_template("journalentry.html") 
 
 
#########
# 歷史交易
#########
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("""
        SELECT debit, credit, amount, transacted, note
        FROM transactions
        WHERE user_id =:user_id
    """, user_id=session["user_id"])
    # 金額格式化
    for i in range(len(transactions)):
        transactions[i]["amount"] = usd(transactions[i]["amount"])
    print("Now Running history() 成功查詢歷史交易分錄")
    return render_template("history.html", transactions=transactions)


#################
# 搜尋科目餘額
#################          
@app.route("/balance", methods=["GET", "POST"])
@login_required
def balance():
    """Get account balance."""
    # 是否在網頁中輸入會計科目
    if request.method == "POST":
        result_checks = is_provided("name")
        if result_checks != None:
            return result_checks
        # 轉換變數
        name = request.form.get("name")
        date = request.form.get("date") + " 23:59:59"
        today = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print("Now Running balance() 正在讀取日期")
        print("輸入日期 {date}".format(date=date))
        print("現在日期 {today}".format(today=today))
        # 查詢是否存在會計科目資料庫中，並取得現在的餘額
        rows_account = db.execute("SELECT type, name, amount, initial, note FROM account WHERE name = :name and user_id=:user_id",
                         user_id=session["user_id"],
                         name=name
                         )
        if len(rows_account) != 1:
            return apology("invalid account", 403)
        # 轉換變數
        type = rows_account[0]["type"]
        amount = rows_account[0]['amount']
        initial = rows_account[0]['initial']
        note = rows_account[0]["note"]
        print("Now Running balance() 成功查詢目前會計科目餘額")
        print("{rows_account} on {date}".format(rows_account=rows_account, date=date))
        print("{name} 起始: {initial} 餘額: {amount}".format(name=name, initial=initial, amount=amount))
        
        # 查詢歷史資料庫中的金額，累積借方及累積貸方，再加上初始值
        d_transactions = db.execute("""SELECT sum(amount) as amount
                                  FROM transactions
                                  WHERE debit = :debit and user_id = :user_id and transacted <= :date""",
                                  user_id=session["user_id"],
                                  debit=name,
                                  date=date
                                  )
        # 判斷是否有該科目，若沒有，抓金額只有None，金額則為零
        if str(d_transactions[0]["amount"]) == 'None':
            d_amount = 0
        else:
            d_amount = d_transactions[0]["amount"]
        print("期末交易借方金額 {d_amount}".format(d_amount=d_amount))
        
        # 查詢歷史資料庫中的金額，累積借方及累積貸方，再加上初始值
        c_transactions = db.execute("""SELECT sum(amount) as amount
                                  FROM transactions
                                  WHERE credit = :credit and user_id = :user_id and transacted <= :date""",
                                  user_id=session["user_id"],
                                  credit=name,
                                  date=date)
        if str(c_transactions[0]["amount"]) == "None":
            c_amount = 0
        c_amount = c_transactions[0]["amount"]
        print("期末交易貸方金額 {c_amount}".format(c_amount=c_amount))
        periodamount = usd(float(d_amount) + float(c_amount) + float(initial))
        print("期末交易餘額 {periodamount}".format(periodamount=periodamount))
        return render_template("balance.html", accountbalance={'type': type, 'name': name, 'amount': periodamount, 'note': note})
    else:        
        accountbalance = {'type': '', 'name': '', 'amount': '0.00', 'note': ''}
        return render_template("balance.html", accountbalance=accountbalance) 


###############
# 圖像化資產負債
###############
@app.route("/quote_bar")
@login_required
def quote_bar():
    """Show account list"""
    labels  = db.execute("""
        SELECT name, amount
        FROM account
        WHERE user_id =:user_id
    """, user_id=session["user_id"])
    
    if len(labels) < 1:
        flash("No data to show! Create a Journal Entry first!")
        return render_template("journalentry.html")

    #搜尋最大值當作Bar Chart的高度
    maxs = db.execute("""
        SELECT MAX(amount) as amount
        FROM account
        WHERE user_id =:user_id
    """, user_id=session["user_id"])

    maxs = maxs[0]["amount"]

    return render_template("quote_bar.html",title='Bar', maxs=maxs, labels=labels)
   

###########################
# 合併新增好友及好友清單功能
###########################
# 資料庫中id皆為null - 修正v12.2
# 資料庫好友圈未獨立 - 嘗試以判斷id方式修改 v12.2
# 朋友清單無法顯示friend_list.html - 修正 before v12.2
    
# helper function
@app.route("/acceptornot", methods=['POST'])
def acceptornot():
    
    if request.form.get("accept"):
        friendname=request.form['accept']
        print("ACCEPT")
        print(friendname)
    
        # 自己加入
        db.execute("""INSERT INTO friends (user_id,username,status) VALUES (:user_id,:username,:status)""",
            user_id = session["user_id"],
            username=friendname,
            status='Accepted'
            )
        
        # 更新對方資料
        friendid = db.execute("""SELECT id FROM users WHERE username = :friendname""",
                            friendname=friendname)
        print(friendid)
        print(int(friendid[0]["id"]))
        # 找出對方資料
        update_status = "Accepted"
        db.execute("UPDATE friends set status = :update_status WHERE user_id = :user_id and username = :username",
            user_id=int(friendid[0]["id"]),
            username=session["user_name"],
            update_status=update_status
            )
        flash("Add Successfully!")
        return friend()

    else:
        friendname=request.form['reject']
        print("REJECT")
        print(friendname)
        
        # 更新對方資料
        friendid = db.execute("""SELECT id FROM users WHERE username = :friendname""",
                            friendname=friendname)
        print(friendid)
        print(int(friendid[0]["id"]))
           
        # 找出對方資料
        update_status = "Rejected"
        db.execute("UPDATE friends set status = :update_status WHERE user_id = :user_id and username = :username",
            user_id=int(friendid[0]["id"]),
            username=session["user_name"],
            update_status=update_status
            )
        db.execute("DELETE friends WHERE user_id = :user_id AND status = :update_status",
                   user_id=int(friendid[0]["id"]),
                   update_status=update_status
                   )
                   
        flash("Removed!")
        return friend()


@app.route("/friend", methods=["GET", "POST"])
@login_required
def friend():
    if request.method == "POST":
        # 將加入的好友
        friendname = request.form.get("username")
 
        #不可加自己為好友
        if friendname == session["user_name"]:
            return apology("cannot add yourself", 403)
        
        #是否在users database中
        rows = db.execute("""SELECT username FROM users WHERE username = :friendname""",
                          friendname=friendname)
        
        #確認users database是否有該成員
        print("確認users database是否有該成員")
        print(rows)
        if len(rows) != 1:
            return apology("invalid username", 403)
        
        #是否在自己的friends database中
        rows_friend = db.execute("SELECT username, status FROM friends WHERE user_id = :user_id AND username = :friendname",
                          user_id=session["user_id"],
                          friendname=friendname
                          )
        
        
        #如果好友資料找不到，代表尚未新增
        print("如果好友資料找不到，代表尚未新增")
        print(rows_friend)          
        if len(rows_friend) < 1:
            
            # 自己將送出好友邀請
            # 用自己的id搭配好友名稱(好友名稱已UNIQUE)
            # 加入好友資料庫且status顯示requested
            db.execute("""INSERT INTO friends (user_id,username,status) VALUES (:user_id,:username,:status) """,
                user_id = session["user_id"],
                username=friendname,
                status='Requested'
                )
            """Show friend list"""
            friends = db.execute("""
                SELECT username, status 
                FROM friends
                WHERE user_id = :user_id
            """, user_id=session["user_id"])
            flash("Sent Successfully!")         
            
            
            # 對方將收到好友邀請
            # 注意：換角度思考 - 找自己的名字是否在別人的資料庫
            """Show friendrequest list"""
            friendrequests = db.execute("""
                SELECT users.username
                FROM friends
                JOIN users
                ON users.id=friends.user_id
                WHERE friends.username =:username and friends.status = :status 
            """, username=session["user_name"], status="Requested"
            )
            print("列印出哪些待核准朋友")            
            print(friendrequests)
            return render_template("friend.html", friends=friends, friendrequests=friendrequests)
                    
        #好友已存在friend database中
        else:
            return apology("Friend already exised or still pending", 403)
    # request.method == "GET"         
    else:
        # 在下方直接顯示資料表
        """Show friend list"""
        friends = db.execute("""
            SELECT username, status 
            FROM friends
            WHERE user_id =:user_id
        """, user_id=session["user_id"])
        print("列印出所有朋友")            
        print(friends)
        
        # 對方將收到好友邀請
        # 注意：換角度思考 - 找自己的名字是否在別人的資料庫
        """Show friendrequest list"""
        friendrequests = db.execute("""
            SELECT users.username
            FROM friends
            JOIN users
            ON users.id=friends.user_id
            WHERE friends.username =:username and friends.status = :status 
        """, username=session["user_name"], status="Requested"
        )        
        print("列印出哪些待核准朋友")            
        print(friendrequests)
        
        # 若無好友資料
        if len(friends) < 0:
            friends = [{'username': 'NONE', 'status': 'Sent a friend request first'}]
            return render_template("friend.html", friends=friends, friendrequests=friendrequests)
        # 有好友資料，顯示好友資料
        else:
            return render_template("friend.html", friends=friends, friendrequests=friendrequests) 


#################
# 修改會計科目餘
#################
# 尚未開始
# 刪除會計科目，已做分錄不行刪
# 刪除歷史交易
# 刪除朋友
@app.route("/balance", methods=["GET", "POST"])
@login_required
def test():
    # 預期內容：
        # html使用彈出視窗
        # 顯示會計科目新增、變動、刪除、修改金額
        # 詢問是否同意
        # 若不同意發送新訊息給對方
        # 若同意必須做分錄入帳
        # 呼叫確認雙方餘額，顯示餘額相符
        # 影響add_account、journalentry
    if request.method == "POST":
        return render_template("index.html")
    else:
        return render_template("index.html")


##############################################################################################
############################# 原始的頁面功能 ##################################################
##############################################################################################


###########################
# 以下不必修改，保持原本code
###########################
# 類似helper function
def is_provided(field):
    if not request.form.get(field):
        return apology(f"must provide {field}", 400)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username and password was submitted
        result_checks = is_provided("username") or is_provided("password") 
        if result_checks != None:
            return result_checks
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in, id and name
        session["user_id"] = rows[0]["id"]
        session["user_name"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        result_checks = is_provided("username") or is_provided("password") or is_provided("confirmation")
        if result_checks != None:
            return result_checks
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match")
        try:
            prim_key = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                        username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password")))
        except:
            return apology("username already exists.", 400)
        if prim_key is None:
            return apology("registration error.", 400)
        session["user_id"] = prim_key
        return redirect("/")
    else:
        return render_template("register.html")  


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
