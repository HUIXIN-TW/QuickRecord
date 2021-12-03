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
    
    
###########################
# 增加好友，待修正問題
###########################
# 資料庫中id皆為null - 修正v12.2
# 資料庫好友圈未獨立 - 嘗試以判斷id方式修改 v12.2
# 朋友清單無法顯示friend_list.html - 修正 before v12.2
@app.route("/add_friends", methods=["GET", "POST"])
@login_required
def add_friends():
    if request.method == "POST":
        #是否在users database中
        #在users database好友資料庫中搜尋username from /add_friends，且不得為自己
        #取得使用者所輸入的add_frined.html中欄位的資料，username=request.form.get("username")
        rows = db.execute("SELECT username, id FROM users WHERE username = :username AND id != :id",
                          id = session["user_id"],
                          username=request.form.get("username"))
               
        #確認users database是否有該成員
        #找到資料 >>> [{'usersname': 'zzz'}]
        #找不到資料 >>> []
        if len(rows) != 1:
            return apology("invalid username", 403)

        #搜尋好友資料
        rows_friend = db.execute("SELECT username FROM friends WHERE user_id = :user_id AND username = :username",
                          user_id = session["user_id"],
                          username=request.form.get("username"))
        #如果好友資料找不到，代表尚未新增           
        if len(rows_friend) != 1:
            #用自己的id搭配好友名稱(好友名稱已UNIQUE)
            db.execute("""INSERT INTO friends (user_id,username) VALUES (:user_id,:username) """,
            user_id = session["user_id"],
            username=request.form.get("username")
            )
            flash("Add Successfully!")
            return friend_list()
        #好友已存在friend database中
        else:
            return apology("Friend already exised", 403)
    # request.method == "GET"         
    else:
        return render_template("add_friends.html")


#好友清單呈現
@app.route("/friend_list")
@login_required
def friend_list():
    """Show friend list"""
    friends = db.execute("""
        SELECT username 
        FROM friends
        WHERE user_id =:user_id
    """, user_id=session["user_id"])

    return render_template("friend_list.html", friends=friends)  


###########################
# 首頁，待修正問題
###########################
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
        #資產負債總額
        if row["type"] == "A":
            A_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": row["amount"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_asset += row["amount"]
        elif row["type"] == "L":
            L_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": row["amount"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_liability += row["amount"]
        elif row["type"] == "R":
            R_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": row["amount"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_revenue += row["amount"]
        else: # row["type"] == "E":
            E_balances.append({
            "type": row["type"],
            "name": row["name"],
            "amount": row["amount"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_expense += row["amount"]
    print(rows)    
    print(grand_asset)
    print(grand_liability)
    print(grand_revenue)
    print(grand_expense)
    balance = grand_asset - grand_liability
    profit = grand_revenue - grand_expense
    return render_template("index.html", A_balances=A_balances, L_balances=L_balances, R_balances=R_balances, E_balances=E_balances, balance=balance, profit=profit)

###########################
# 新增會計科目，待修正問題
###########################
@app.route("/add_account", methods=["GET", "POST"])
@login_required
def add_account():
    if request.method == "POST":
        # 搜尋account資料
        rows = db.execute("SELECT name, type FROM account WHERE name = :name AND user_id = :user_id",
                          user_id = session["user_id"],
                          name=request.form.get("name"))
        # 確認是否來自於選單
        if request.form.get("type") not in ["A", "L", "R", "E"]:
            return apology("The Type Only Accept Asset, Liability, Revenue or Expense", 403)
        #如果account資料找不到，代表尚未新增           
        if len(rows) != 1:
            #用自己的id搭配account名稱(account名稱已UNIQUE，且分辦大小寫)
            db.execute("""INSERT INTO account (user_id,type,name,note) VALUES (:user_id,:type,:name,:note) """,
            user_id = session["user_id"],
            type=request.form.get("type"),
            name=request.form.get("name"),
            note=request.form.get("note")
            )
            flash("Add Successfully!")
            return render_template("add_account.html")
        #account已存在account database中
        else:
            return apology("Account already exised", 403)
    # request.method == "GET"         
    else:
        return render_template("add_account.html")
        
    
###########################
# 費用，待修正問題
###########################
# 歷史交易保存
@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
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
        print(rows_debit)
        print(rows_credit)            
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
        
        
        ################
        # 加入歷史交易分錄
        ################
        db.execute(""" 
            INSERT INTO transactions
                (user_id, debit, credit, amount) 
            VALUES (:user_id, :debit, :credit, :amount)
            """,
                user_id = session["user_id"],
                debit = debit,
                credit = credit,
                amount = amount
            )
        flash("You are a Good Accountant!")
        return render_template("history.html")
     
    else:
        return render_template("expense.html")

#################
# 收入，待修正問題
#################
# 歷史交易保存
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        print(request.form.get("symbol"))
        find_missing_errors = is_provided("symbol") or is_provided("shares")
        if find_missing_errors:
            return find_missing_errors
        elif not request.form.get("shares").isdigit():
            return apology("invalid number of shares")
        symbol = request.form.get("symbol").upper()
        shares = int(request.form.get("shares"))
        stock = "TEST"
        #stock = lookup(symbol)
        if stock is None:
            return apology("invalid symbol")
            
        rows = db.execute("""
            SELECT symbol, SUM(shares) as totalShares
            FROM transactions
            WHERE user_id=:user_id
            GROUP BY symbol
            HAVING totalShares >0;
        """, user_id=session["user_id"])
        for row in rows:
            if row["symbol"] == symbol:
                if shares > row["totalShares"]:
                    return apology("too many shares")
            
        rows = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        cash = rows[0]["cash"]
        
        updated_cash = cash + shares * stock['price']
        if updated_cash < 0:
            return apology("cannot afford")
        db.execute("UPDATE users SET cash =:updated_cash WHERE id=:id", 
                updated_cash=updated_cash, 
                id=session["user_id"]) 
        db.execute(""" 
            INSERT INTO transactions
                (user_id, symbol, shares, price) 
            VALUES (:user_id, :symbol, :shares, :price)
            """,
                user_id = session["user_id"],
                symbol = stock["symbol"],
                shares = -1 * shares,
                price = stock["price"]
            )
        flash("Sold!")
        return redirect("/")
     
    else:
        rows = db.execute("""
            SELECT symbol
            FROM transactions
            WHERE user_id = :user_id
            GROUP BY symbol
            HAVING SUM(shares) > 0;
        """, user_id=session["user_id"])
        
        return render_template("sell.html", symbols=[row["symbol"] for row in rows])
 
 
#########
# 歷史交易
#########
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("""
        SELECT debit, credit, amount, transacted
        FROM transactions
        WHERE user_id =:user_id
    """, user_id=session["user_id"])
    for i in range(len(transactions)):
        transactions[i]["amount"] = usd(transactions[i]["amount"])
    return render_template("history.html", transactions=transactions)
            

#################
# 修改搜尋科目餘額
#################          
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get account balance."""
    if request.method == "POST":
        result_checks = is_provided("name")
        if result_checks != None:
            return result_checks
        name = request.form.get("name")
        rows_account = db.execute("SELECT type, name, amount FROM account WHERE name = :name and user_id=:user_id",
                         user_id=session["user_id"],
                         name=name
                         )
        print(rows_account)
        type = rows_account[0]["type"]
        amount = rows_account[0]['amount']
        if len(rows_account) != 1:
            flash("Account doesn't exist")
            return render_template("quote.html")
        return render_template("quoted.html", accountbalance={'type': type, 'name': name, 'amount': amount})
    else:
        return render_template("quote.html")

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

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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
