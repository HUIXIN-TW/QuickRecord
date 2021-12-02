import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
#利用helper作為外部customised library
#可以至helper.py增加或刪減
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
Session(app) # 讓此程式可以使用flask_session，把user id儲存於cs50 IDE裡


# Configure CS50 Library to use SQLite database
# 配置CS50的SQL資料庫
db = SQL("sqlite:///finance.db")
# db = SQL("c:/Users/Huixin/OneDrive/桌面/CodeProject/OwnAccount/Remy/finance.db")


# Make sure API key is set
# 在環境裡引入外部API
# 若不使用finance資料庫的股價應該不需要
#if not os.environ.get("API_KEY"):
    #raise RuntimeError("API_KEY not set")


##############################################################################################
######################### 自行定義的頁面功能 ##################################################
##############################################################################################


# 作業8的新增功能
@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    if request.method == "POST":
        db.execute(""" UPDATE users
        SET cash = cash + :amount
        WHERE id=:user_id
        """, amount=request.form.get("cash"),
        user_id = session["user_id"])
        flash("Add Cash!")
        return redirect("/")
    else:
        return render_template("add_cash.html")
    
    
# 8/27 
# 開始寫加好友的Code 
###########################
# 待修正問題
###########################
# 資料庫中id皆為null
# 資料庫好友圈未獨立 - 嘗試以判斷id方式修改
# 朋友清單無法顯示friend_list.html

@app.route("/add_friends", methods=["GET", "POST"])
@login_required
def add_friends():
    if request.method == "POST":
        rows = db.execute("SELECT username FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) != 1:
            return apology("invalid username", 403)

        #搜尋好友資料
        rows_friend = db.execute("SELECT username FROM friends WHERE user_id = :user_id AND username = :username",
                          user_id = session["user_id"],
                          username=request.form.get("username"))

        #如果好友資料找不到，代表尚未新增
        if len(rows_friend) != 1:

            db.execute("""INSERT INTO friends (user_id,username) VALUES (:user_id,:username) """,
            user_id = session["user_id"],
            username=request.form.get("username")
            )
            flash("Add Successfully!")
            return friend_list()
        else:
            return apology("Friend already exised", 403)
             
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

##############################################################################################
############################# 原始的頁面功能 ##################################################
##############################################################################################


# 首頁
# login_required函式是flask官方文件的建議寫法
# 就是說要求進入網站時，會先檢查session的user_id，看需不需要登入，之後每個功能都需要登入，所以都要附上去
# 此作業需要先在sqlite資料庫內，建立transactions表格
# transactions表格的欄位有：id(設定為Primary Key), user_id, symbol(公司簡稱), shares(股票張數), price, transacted(購買時間，Default Value為CURRENT_TIMESTAMP)
# 在templates裡面的index.html裡，製作一份表格，把這裡的欄位用迴圈方式丟入
###########################
# 待修正問題
###########################
# @app.route("/") - 修改總結呈現最後的資料彙總

@app.route("/")
@login_required
def index():
    #最後呈現的資料總結
    # 我們需要在使用者登入後，於首頁顯示使用者目前持有的股票訊息
    # 先從資料庫內抓取該名使用者過去購買過的股票、股票張數
    rows = db.execute("""
        SELECT symbol, SUM(shares) as totalShares
        FROM transactions
        WHERE user_id = :user_id
        GROUP BY symbol
        HAVING totalShares >0;
    """, user_id=session["user_id"])
    holdings = []
    grand_total = 0
    # 把使用者過去購買的股票名稱(Symbol)、公司名稱、張數、目前價格、該股票總金額丟入一個list裡
    for row in rows:
        stock = "TEST"
        #stock = lookup(row["symbol"])
        holdings.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "shares": row["totalShares"],
            "price": usd(stock["price"]),
            "total": usd(stock["price"] * row["totalShares"])
        })
        grand_total += stock["price"] * row["totalShares"]
    rows = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id=session["user_id"])
    cash = rows[0]["cash"]
    # 另外加總使用者目前手頭上的現金及股票總價值
    grand_total += cash
    return render_template("index.html", holdings=holdings, cash=usd(cash), grand_total=usd(grand_total))


#減少現金
#屬於支出
#XX費用
#  現金
###########################
# 待修正問題
###########################
# 更改buy
# 同步修改借貸方transaction db
# 將現金換成其他資產
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """記錄一筆分錄"""
    #POST 記錄一筆分錄
    if request.method == "POST":
        # 若無輸入accountname
        find_missing_errors = is_provided("accountname") or is_provided("amount")
        if find_missing_errors:
            return find_missing_errors
        # 若amount不是金額
        elif not request.form.get("amount").isdigit():
            return apology("invalid amount, please enter 0-9")
        # 轉換變數
        accountname = request.form.get("accountname").upper()
        amount = int(request.form.get("amount"))
        
        # lookup 在helper function中
        # API尋找股市資料庫
        #stock = lookup(symbol)
        #if stock is None:
            #return apology("invalid symbol")
            
        # 從資料庫拉出貸方科目金額
        rows = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
        cash = rows[0]["cash"]
        
        # 更新貸方科目
        # 確認貸方是否足夠，不必確認借方科目
        # 禁止借方科目為負
        updated_cash = cash - amount
        if updated_cash < 0:
            return apology("cannot afford")
        
        # 更新貸方金額
        # 目前僅使用現金
        db.execute("UPDATE users SET cash =:updated_cash WHERE id=:id", 
                updated_cash=updated_cash, 
                id=session["user_id"])
        #############
        # 更新借方金額
        #############
        
        
        
        # 加入交易分錄
        # 需新增借貸方
        db.execute(""" 
            INSERT INTO transactions
                (user_id, accountname, amount) 
            VALUES (:user_id, :accountname, :amount)
            """,
                user_id = session["user_id"],
                accountname = accountname,
                amount = amount
            )
        flash("Bought!")
        return redirect("/")
     
    else:
        return render_template("buy.html")


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
 
 
###########################
# 待修正問題
###########################
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("""
        SELECT symbol, shares, price, transacted
        FROM transactions
        WHERE user_id =:user_id
    """, user_id=session["user_id"])
    for i in range(len(transactions)):
        transactions[i]["price"] = usd(transactions[i]["price"])
    return render_template("history.html", transactions=transactions)


def is_provided(field):
    if not request.form.get(field):
        return apology(f"must provide {field}", 400)
            
# 搜尋股票價格
# 修改搜尋科目餘額
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        result_checks = is_provided("symbol")
        if result_checks != None:
            return result_checks
        symbol = request.form.get("symbol").upper()
        stock = "TEST"
        #stock = lookup(symbol)
        if stock is None:
            return apology("invalid symbol", 400)
        return render_template("quoted.html", stockName={
            'name': stock['name'],
            'symbol': stock['symbol'],
            'price': usd(stock['price'])
        })
    else:
        return render_template("quote.html")


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
