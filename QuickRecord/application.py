from logging import raiseExceptions
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
#import numpy as np
#import matplotlib.pyplot as plt #pip install matplotlib first


# Configure application
# python設定配置為flask
# $env:FLASK_APP = "application"
# flask run
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
    # 相同方式篩選
    # 但選擇大於0的會計科目顯在在首頁面   
    A_balances, L_balances, R_balances, E_balances, balance, profit = allaccounts_gt0()
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
        find_missing_errors = is_provided("name") or is_provided("amount")
        if find_missing_errors:
            return find_missing_errors
        # 若amount不是金額
        elif not request.form.get("amount").isdigit():
            return apology("invalid amount, please enter 0-9")
        # 不能加入自己
        if session["user_name"] == request.form.get("share"):
            return apology("Cannot share with yourself", 403)

        # 搜尋accounts資料
        name = request.form.get("name")
        rows = db.execute("SELECT id, user_id, name, type, share, sharestatus, note, amount FROM accounts WHERE name = :name AND user_id = :user_id",
                        user_id = session["user_id"],
                        name = name)
        print("搜尋會計科目 {rows}, 若無資料代表將新增".format(rows=rows))
        
        # 如果accounts資料找不到，代表尚未新增，可開始新增          
        if len(rows) != 1:
            
            # 是否共用會計科目前置設定
            share=request.form.get("share") # 分享給的好友名字
            sharestatus='None' # 假設為None，不分享給其他人
            
            if share != "": # 不等於空白代表分享該帳戶
                try:
                    share, sharestatus = shareaccount(name, share) # 聯結到helper function
                    print("Share with {share}, Status {sharestatus}".format(share=share, sharestatus=sharestatus))
                except:
                    print("No Friend Error, Fail to share the account... waiting for acceptance")
                    return apology("Not friend yet", 403)
            else: #不分享帳戶
                #用自己的id搭配accounts名稱(accounts名稱已UNIQUE，且分辦大小寫)
                db.execute("""INSERT INTO accounts (user_id,type,name,amount,note,share,sharestatus,initial,asker_id) VALUES (:user_id,:type,:name,:amount,:note,:share,:sharestatus,:initial,:asker_id) """,
                user_id=session["user_id"], # 目前使用者
                type=request.form.get("type"), # 會計類別
                name=name, # 會計科目
                amount=request.form.get("amount"), # 輸入金額
                note=request.form.get("note"), # 輸入附註
                share=share, # 分享給的好友名字
                sharestatus=sharestatus, # 因為是否share with friend而不同狀態
                initial=request.form.get("amount"), # 起始金額
                asker_id=session["user_id"], # 鎖住分錄創立者
                )
                flash("Add Successfully!")
                print("Share with {share}, Status {sharestatus}".format(share=share, sharestatus=sharestatus))
            print("\n")
            print("------Now Running add_account()------")
            print("新增會計科目 {name}".format(name=name))
            return render_template("add_account.html")
        #accounts已存在accounts database中
        else:
            return apology("Account already exised", 403)
    # request.method == "GET"         
    else:
        return render_template("add_account.html")

    
###########################
# 分錄，待修正問題
###########################
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
        delete = False # 與delete共用同一個功能update account
        updateaccount(debit, credit, amount, note, delete) # 與delete共用同一個功能update account
        return redirect("/history")
    
    else: # GET
        A_balances, L_balances, R_balances, E_balances, balance, profit = allaccounts_ge0()
        wait_approvalaccounts  = db.execute("""SELECT * 
                                       FROM accounts
                                       WHERE user_id=:user_id and sharestatus=:sharestatus""",
                                       user_id=session["user_id"], # 請求對方授權的會計科目
                                       sharestatus="Waiting for approval")
        ask_approvalaccounts  = db.execute("""SELECT * 
                                       FROM accounts
                                       WHERE user_id=:user_id and sharestatus=:sharestatus and asker_id!=:user_id""",
                                       user_id=session["user_id"], # 要求本人授權的會計科目
                                       sharestatus="Fill the info")
        print("\n")
        print("------列印出所有要求本人授權的會計科目------")
        for ask_approvalaccount in ask_approvalaccounts:
            print(ask_approvalaccount)
        print("\n")
        print("------列印出所有請求對方授權的會計科目------")
        for wait_approvalaccount in wait_approvalaccounts:
            print(wait_approvalaccount)
        return render_template("journalentry.html", A_balances=A_balances, L_balances=L_balances, R_balances=R_balances, E_balances=E_balances, balance=balance, profit=profit, ask_approvalaccounts=ask_approvalaccounts, wait_approvalaccounts=wait_approvalaccounts)

def updateaccount(debit, credit, amount, note="", delete=True):
    # 確認是否有該科目
    rows_debit = db.execute("SELECT type, name, amount, share, sharestatus, shareaccountid FROM accounts WHERE name = :debit and user_id=:user_id",
                        user_id=session["user_id"],
                        debit=debit
                        )
    rows_credit = db.execute("SELECT type, name, amount, share, sharestatus, shareaccountid FROM accounts WHERE name = :credit and user_id=:user_id",
                        user_id=session["user_id"],
                        credit=credit
                        )
    print("使用者會計科目資料庫搜尋結果")
    print(rows_debit, rows_credit)            
    #確認accounts.db是否有該account
    #找到資料 >>> [{'name': 'cash'}]
    #找不到資料 >>> []
    if len(rows_debit) != 1:
        flash("please add new debit account")
        return render_template("add_account.html")
    if len(rows_credit) != 1:
        flash("please add new credit account")
        return render_template("add_account.html")
    
    # 更新借貸金額
    # 從資料庫拉出借方科目金額
    debittype = rows_debit[0]["type"]
    debitamount = rows_debit[0]['amount']
    debitshare = rows_debit[0]["share"]
    debitsharestatus = rows_debit[0]["sharestatus"]
    debitshareaccountid = rows_debit[0]["shareaccountid"]
    
    # 從資料庫拉出貸方科目金額
    credittype = rows_credit[0]["type"]
    creditamount = rows_credit[0]['amount']
    creditshare = rows_credit[0]["share"]
    creditsharestatus = rows_credit[0]["sharestatus"]
    creditshareaccountid = rows_credit[0]["shareaccountid"]
    
    # 調整刪除科目的金額
    if delete == True:
        amount = amount * (-1)
    
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
        
    if delete == False:
        # 加入歷史交易分錄
        message_id = db.execute(""" 
            INSERT INTO transactions
                (user_id, debit, credit, amount, note, debitshare, debitsharestatus, debitshareaccountid, creditshare, creditsharestatus, creditshareaccountid) 
            VALUES (:user_id, :debit, :credit, :amount, :note, :debitshare, :debitsharestatus, :debitshareaccountid, :creditshare, :creditsharestatus, :creditshareaccountid)
            """,
                user_id = session["user_id"],
                debit = debit,
                credit = credit,
                amount = amount,
                note = note,
                debitshare = debitshare, 
                debitsharestatus = debitsharestatus,
                debitshareaccountid = debitshareaccountid, 
                creditshare = creditshare, 
                creditsharestatus = creditsharestatus,
                creditshareaccountid = creditshareaccountid
            )
        if debitshare != "" or creditshare != "":
            create_message(message_id) #helper function 處理分享資訊
            flash("You are a Good Accountant! Shared the transaction with Your Partner")
        else:
            flash("You are a Good Accountant!")
        print("\n")
        print("------Now Running jornalentry() 成功加入歷史交易分錄------")
        print("分錄編號 {message_id}".format(message_id=message_id))
        
    # 更新借方金額
    db.execute("UPDATE accounts SET amount = :updated_debitamount WHERE name = :debit and user_id=:user_id",
            debit=debit,
            updated_debitamount=updated_debitamount, 
            user_id=session["user_id"])
    # 更新貸方金額
    db.execute("UPDATE accounts SET amount = :updated_creditamount WHERE name = :credit and user_id=:user_id",
            credit=credit,
            updated_creditamount=updated_creditamount, 
            user_id=session["user_id"])
    print("\n")
    print("------Now Running jornalentry() 更新會計科目資料庫餘額------")
    print("更新借方金額 {rows_debit}: {updated_debitamount}".format(rows_debit=rows_debit, updated_debitamount=updated_debitamount))
    print("更新貸方金額 {rows_credit}: {updated_creditamount}".format(rows_credit=rows_credit, updated_creditamount=updated_creditamount))    
    

# 歷史交易
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("""
        SELECT *
        FROM transactions
        WHERE user_id =:user_id
    """, user_id=session["user_id"])
    # 金額格式化
    for i in range(len(transactions)):
        transactions[i]["amount"] = usd(transactions[i]["amount"])
    print("\n")
    print("------Now Running history() 成功查詢歷史交易分錄------")
    for transaction in transactions:
        print(transaction)
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
        print("\n")
        print("------Now Running balance() 正在讀取日期------")
        print("輸入日期 {date}".format(date=date))
        print("現在日期 {today}".format(today=today))
        # 查詢是否存在會計科目資料庫中，並取得現在的餘額
        rows_account = db.execute("SELECT type, name, amount, initial, note FROM accounts WHERE name = :name and user_id=:user_id",
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
        print("\n")
        print("------Now Running balance() 成功查詢目前會計科目餘額------")
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
        else:
            c_amount = c_transactions[0]["amount"]
        print("期末交易貸方金額 {c_amount}".format(c_amount=c_amount))
        
        # 總整交易金額
        periodamount=0
        if type == "A" or type == "E":
            periodamount = usd(float(d_amount) - float(c_amount) + float(initial))
        else:
            periodamount = usd(float(c_amount) - float(d_amount) + float(initial))
        print("期末交易餘額 {periodamount}".format(periodamount=periodamount))
        
        # plot 借方、紅色
        d_plot = db.execute("""SELECT amount, transacted
                                FROM transactions
                                WHERE debit = :debit and user_id = :user_id and transacted <= :date""",
                                user_id=session["user_id"],
                                debit=name,
                                date=date
                                )
        print("PLOT")
        print(d_plot)
        d_amt=[]
        d_trans=[]
        for plot in d_plot:
            d_amt.append(plot['amount'])
            d_trans.append(plot['transacted'])
        # plt.plot(d_trans, d_amt, 'o', color='blue')
        
        # plot 貸方、藍色
        c_plot = db.execute("""SELECT amount, transacted
                                FROM transactions
                                WHERE credit = :credit and user_id = :user_id and transacted <= :date""",
                                user_id=session["user_id"],
                                credit=name,
                                date=date
                                )
        #print("PLOT")
        #print(c_plot)
        c_amt=[]
        c_trans=[]
        for plot in c_plot:
            c_amt.append(plot['amount'])
            c_trans.append(plot['transacted'])
        # plt.plot(c_trans, c_amt, 'o', color='blue')
        
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
        FROM accounts
        WHERE user_id =:user_id
    """, user_id=session["user_id"])
    
    if len(labels) < 1:
        flash("No data to show! Create a Journal Entry first!")
        return render_template("journalentry.html")

    #搜尋最大值當作Bar Chart的高度
    maxs = db.execute("""
        SELECT MAX(amount) as amount
        FROM accounts
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
@app.route("/friend", methods=["GET", "POST"])
@login_required
def friend():
    if request.method == "POST":
        # 將加入的好友
        friendname = request.form.get("username")
 
        #不可加自己為好友
        if friendname == session["user_name"]:
            return apology("cannot add yourself", 403)
        
        #搜尋users database
        rows_users = db.execute("""SELECT username FROM users WHERE username = :friendname""",
                          friendname=friendname)
        
        #確認users database是否有該成員
        print("確認users database是否有該成員")
        print(rows_users)
        if len(rows_users) != 1:
            return apology("invalid username", 403)
        
        #搜尋自己的friends database
        rows_friends = db.execute("SELECT username, status FROM friends WHERE user_id = :user_id AND username = :friendname",
                          user_id=session["user_id"],
                          friendname=friendname
                          )    
        
        #如果好友資料找不到，代表尚未新增
        print("如果好友資料找不到，代表尚未新增")
        print(rows_friends)          
        if len(rows_friends) < 1:
            
            # 自己將送出好友邀請
            # 用自己的id搭配好友名稱(好友名稱已UNIQUE)
            # 加入好友資料庫且status顯示requested
            # 插入好友至自己的資料庫
            db.execute("""INSERT INTO friends (user_id,username,status) VALUES (:user_id,:username,:status) """,
                user_id = session["user_id"],
                username=friendname,
                status='Requested'
                )
            flash("Sent Successfully!") 
            
            # 好友清單顯示
            acceptfriends, requestfriends, rejectfriends, friendrequests = friendlist()
            return render_template("friend.html", acceptfriends=acceptfriends, requestfriends=requestfriends, rejectfriends=rejectfriends, friendrequests=friendrequests)
                    
        #好友已存在friend database中
        else:
            return apology("Friend already exised or still pending", 403)
    # request.method == "GET"         
    else:
        # 好友清單顯示
        acceptfriends, requestfriends, rejectfriends, friendrequests = friendlist()
        return render_template("friend.html", acceptfriends=acceptfriends, requestfriends=requestfriends, rejectfriends=rejectfriends, friendrequests=friendrequests)


##################
# Helper Function
##################
# 預期內容：
# 顯示會計科目新增、變動、刪除、修改金額
# 呼叫確認雙方餘額，顯示餘額相符
# 影響add_account、journalentry
  
# helper function for journalentry() 大於等於0
@login_required
def allaccounts_ge0():
    # 篩選所有資料
    # 會計科目sharestatus
    #"None" #沒有與其他人分享的會計科目
    #"Approved" #已與對方共用
    #"Waiting for approval" #等待對方核准同步
    #"Fill the info" #尚未填寫會計科目資料
    
    #分享狀態
    noshare="None"
    share="Shared"
    pending="Waiting for approval"
    
    rows = db.execute("""
        SELECT *
        FROM accounts
        WHERE user_id=:user_id and (sharestatus=:noshare or sharestatus=:share or sharestatus=:pending)
        GROUP by name
        HAVING amount >=0;
    """, user_id=session["user_id"], noshare=noshare, share=share, pending=pending)
    A_balances, L_balances, R_balances, E_balances, balance, profit = accountformat(rows) 
    return (A_balances, L_balances, R_balances, E_balances, balance, profit)


# helper function for index() 大於0
@login_required
def allaccounts_gt0():
    # 篩選所有資料
    # 會計科目sharestatus
    #"None" #沒有與其他人分享的會計科目
    #"Approved" #已與對方共用
    #"Waiting for approval" #等待對方核准同步
    #"Fill the info" #尚未填寫會計科目資料
    
    #分享狀態
    noshare="None"
    share="Shared"
    pending="Waiting for approval"
    
    rows = db.execute("""
        SELECT *
        FROM accounts
        WHERE user_id=:user_id and (sharestatus=:noshare or sharestatus=:share or sharestatus=:pending)
        GROUP by name
        HAVING amount >0;
    """, user_id=session["user_id"], noshare=noshare, share=share, pending=pending)
    A_balances, L_balances, R_balances, E_balances, balance, profit = accountformat(rows)
    return (A_balances, L_balances, R_balances, E_balances, balance, profit)


# helper function for allaccounts_ge0() and allaccounts_gt0()
@login_required
def accountformat(rows):
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
    # 把使用者過去交易儲存，需修改usd格式，故沒有直接append row
    for row in rows:
        # 資產總額
        if row["type"] == "A":
            A_balances.append({
            "id": row['id'],
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "share": row["share"],
            "sharestatus": row["sharestatus"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_asset += row["amount"]
        # 負債總額
        elif row["type"] == "L":
            L_balances.append({
            "id": row['id'],
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "share": row["share"],
            "sharestatus": row["sharestatus"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_liability += row["amount"]
        # 收入總額
        elif row["type"] == "R":
            R_balances.append({
            "id": row['id'],
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "share": row["share"],
            "sharestatus": row["sharestatus"],
            "note" : row["note"]
            #若需要匯率轉參考以下
            #"rate": usd(row["rate"]),
            #"exchange": usd(row["totalamount"] * row["rate"])
            })
            grand_revenue += row["amount"]
        else: # row["type"] == "E": 費用總額
            E_balances.append({
            "id": row['id'],
            "type": row["type"],
            "name": row["name"],
            "amount": usd(row["amount"]),
            "share": row["share"],
            "sharestatus": row["sharestatus"],
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
    print("\n")
    print("------Now Running index()------")
    print("------使用者所有會計科目------")
    for row in rows:
        print(row)
    print("\n")
    print("------使用者所有交易總結------")
    print("資產總額 {grand_asset}, 負債總額 {grand_liability}, 收入總額 {grand_revenue} 及費用總額 {grand_expense}".format(grand_asset=grand_asset, grand_liability=grand_liability, grand_revenue=grand_revenue, grand_expense=grand_expense))
    print("剩餘價值 {balance}, 結餘 {profit}".format(balance=balance, profit=profit))
    return (A_balances, L_balances, R_balances, E_balances, balance, profit)


@login_required
def shareaccount(name, share):
    print("\n")
    print("------Now Run shareaccount(name, share)------")
    # 搜尋好友資料
    rows_friends = db.execute("SELECT username FROM friends WHERE user_id = :user_id AND username = :username AND status = :status",
                    user_id=session["user_id"],
                    username=share,
                    status="Accepted")
    print("Share with {rows_friends}".format(rows_friends=rows_friends))
    
    # 如果好友資料找不到，代表尚未新增        
    if rows_friends == []:
        raise BaseException("No Friend Error")
    
    # 搜尋好友id
    friendid = db.execute("SELECT id FROM users WHERE username = :username",
        username=share,
        )
    
    # 修改分享狀態，顯示等待回應
    sharestatus='Waiting for approval'
    
    #用自己的id搭配accounts名稱(accounts名稱已UNIQUE，且分辦大小寫)
    accountid = db.execute("""INSERT INTO accounts (user_id,type,name,amount,note,share,sharestatus,initial,asker_id) VALUES (:user_id,:type,:name,:amount,:note,:share,:sharestatus,:initial,:asker_id) """,
                    user_id=session["user_id"], # 目前使用者
                    type=request.form.get("type"), # 會計類別
                    name=name, # 會計科目
                    amount=request.form.get("amount"), # 輸入金額
                    note=request.form.get("note"), # 輸入附註
                    share=share, # 分享給的好友名字
                    sharestatus=sharestatus, # 因為是否share with friend而不同狀態
                    initial=request.form.get("amount"), # 起始金額
                    asker_id=session["user_id"], # 鎖住分錄創立者
                    )
    print("自己會計科目ID {accountid}".format(accountid=accountid))
    
    
    # 新增對方會計科目資料
    counterpartyid = db.execute("""INSERT INTO accounts (user_id,type,name,amount,note,share,sharestatus,shareaccountid,initial,asker_id) VALUES (:user_id,:type,:name,:amount,:note,:share,:sharestatus,:shareaccountid,:initial,:asker_id) """,
        user_id=friendid[0]["id"], # 對方使用者ID
        type=request.form.get("type"), # 會計類別，可修改，待更新
        name="Wait", # 會計科目，待更新
        amount=request.form.get("amount"), # 輸入金額
        note=request.form.get("note"), # 輸入附註，待更新
        share=session["user_name"], # 輸入自己的名字
        sharestatus="Fill the info", # 因為是否share with friend而不同狀態，對方待填寫
        shareaccountid=accountid, # 填入自己的會計科目ID
        initial=request.form.get("amount"), # 起始金額
        asker_id=session["user_id"]
        )
    
    print("對方會計科目ID {counterpartyid}".format(counterpartyid=counterpartyid))
        
    # 更新該會計科目資料 
    db.execute("UPDATE accounts SET shareaccountid=:shareaccountid WHERE id=:id",
                shareaccountid=counterpartyid,
                id=accountid # 填入自己的會計科目ID
                )
    
    print("顯示等待回應")                                
    flash("Sent Successfully!")
    return share, sharestatus
    
@app.route("/approveornot", methods=["GET", "POST"])
@login_required
def approveornot():
    if request.method == "POST":
        if request.form.get("approve"): # 若核准則導入其他頁面
            session["accountdata"]=eval(request.form['approve'])
            return render_template("add_shareaccount.html")
        
        elif request.form.get("reject"):
            accountdata=eval(request.form['reject'])
            print("\n")
            print("------REJECT------")
            print(accountdata)
            
            sharestatus='Rejected'
            
            # 找出對方資料
            db.execute("UPDATE accounts set sharestatus = :sharestatus WHERE id = :id",
                id=int(accountdata["id"]),
                sharestatus=sharestatus
                )
            
            flash("Removed Link!")
            return redirect("/journalentry")
        
        else:
            print("Check the status of shared account")
            return redirect("/journalentry")
    
    
@app.route("/add_shareaccount", methods=["GET", "POST"])
@login_required
def add_shareaccount(): # 核准共同會計科目
    if request.method == "POST":
        print("\n")
        print("------APPROVE------")
        print(session)
        accountdata=session["accountdata"]
        session.pop("accountdata")   #只刪除"accountdata"
        print("分開會計科目資料")
        print(session)
        print(accountdata)
        
        id=int(accountdata["id"]) # 找到對方分享給你的
        counterpartyid=int(accountdata["shareaccountid"])
        sharestatus='Shared'

        # 自己加入
        print("更新會計科目資料")
        print(request.form.get("type"))
        print(request.form.get("name"))
        print(request.form.get("note"))
        db.execute("UPDATE accounts set type = :type, sharestatus = :sharestatus, note=:note, name=:name WHERE id=:id",
                    type=request.form.get("type"),
                    sharestatus=sharestatus,
                    note=request.form.get("note"),
                    name=request.form.get("name"),
                    id=id # 找到對方分享給你的
                    )  
        print("修改自己的會計科目{id}".format(id=id))
        
        # 找出對方資料
        db.execute("UPDATE accounts set sharestatus = :sharestatus WHERE id = :counterpartyid",
            counterpartyid=counterpartyid,
            sharestatus=sharestatus
            )
        print("修改對方的會計科目{counterpartyid}".format(counterpartyid=counterpartyid))
        flash("Approved Successfully!")
        return redirect("/journalentry")
    else:
        print("\n")
        print("------NO APPROVE POST------")
        print(session)
        return render_template("journalentry.html")


@app.route("/history_share", methods=["GET", "POST"])
@login_required
def history_share():
    if request.method == "GET":
        # 拉出所有借方或貸方共享的會計交易
        transactions = db.execute("SELECT * FROM messages WHERE receiver_id=:id",
                                  id=session["user_id"])

        # 排除對方的未共享的科目
        print("------收到之共享的科目------")
        for transaction in transactions:
            print(transaction)

        return render_template("history_share.html", transactions=transactions)
    else:
        print("------No POST------")


@login_required
def create_message(messageid):
    message=db.execute("SELECT * FROM transactions WHERE id=:messageid", messageid=messageid)
    print("/n")
    print("------寫入Messages分享資料庫------")
    print(message)
    
    creater_name=db.execute("SELECT username FROM users WHERE id=:id", id=message[0]["user_id"])
    
    
    if message[0]["debitshare"] != "":
        receiver_id=db.execute("SELECT id FROM users WHERE username=:username",  username=message[0]["debitshare"])
        
        accountname=db.execute("SELECT name FROM accounts WHERE id=:id", id=message[0]["debitshareaccountid"])
        
        db.execute(""" 
        INSERT INTO messages
            (transaction_id, creater_id, creater_name, receiver_id, receiver_name, account_id, accountname, amount, transacted, sharestatus, note) 
        VALUES (:transaction_id, :creater_id, :creater_name, :receiver_id, :receiver_name, :account_id, :accountname, :amount, :transacted, :sharestatus, :note)
        """,
        transaction_id=message[0]["id"],
        creater_id=message[0]["user_id"], 
        creater_name=creater_name[0]["username"],
        receiver_id=receiver_id[0]["id"],
        receiver_name=message[0]["debitshare"],
        account_id=message[0]["debitshareaccountid"], 
        accountname=accountname[0]["name"], 
        amount=message[0]["amount"], 
        transacted=message[0]["transacted"], 
        sharestatus=message[0]["debitsharestatus"], 
        note=message[0]["note"]
        )
    
    if message[0]["creditshare"] != "":
        
        receiver_id=db.execute("SELECT id FROM users WHERE username=:username", username=message[0]["creditshare"])
        
        accountname=db.execute("SELECT name FROM accounts WHERE id=:id", id=message[0]["creditshareaccountid"])
        
        db.execute(""" 
        INSERT INTO messages
            (transaction_id, creater_id, creater_name, receiver_id, receiver_name, account_id, accountname, amount, transacted, sharestatus, note) 
        VALUES (:transaction_id, :creater_id, :creater_name, :receiver_id, :receiver_name, :account_id, :accountname, :amount, :transacted, :sharestatus, :note)
        """,
        transaction_id=message[0]["id"],
        creater_id=message[0]["user_id"], 
        creater_name=creater_name[0]["username"],
        receiver_id=receiver_id[0]["id"],
        receiver_name=message[0]["creditshare"],
        account_id=message[0]["creditshareaccountid"], 
        accountname=accountname[0]["name"], 
        amount=message[0]["amount"], 
        transacted=message[0]["transacted"], 
        sharestatus=message[0]["creditsharestatus"], 
        note=message[0]["note"]
        )
    

@app.route("/acceptornot", methods=["GET", "POST"])
@login_required
def acceptornot():
    
    if request.form.get("accept"):
        friendname=request.form['accept']
        print("\n")
        print("------ACCEPT------")
    
        # 自己加入
        db.execute("""INSERT INTO friends (user_id,username,status) VALUES (:user_id,:username,:status)""",
            user_id = session["user_id"],
            username=friendname,
            status='Accepted'
            )
        
        # 更新對方資料
        friendid = db.execute("""SELECT id FROM users WHERE username = :friendname""",
                            friendname=friendname)
        print("Accept {friendid} {friendname}".format(friendname=friendname,friendid=friendid))
        
        # 找出對方資料
        update_status = "Accepted"
        db.execute("UPDATE friends set status = :update_status WHERE user_id = :user_id and username = :username",
            user_id=int(friendid[0]["id"]),
            username=session["user_name"],
            update_status=update_status
            )
        flash("Add Successfully!")
        return redirect("/friend")  

    else:
        friendname=request.form['reject']
        print("\n")
        print("------REJECT------")
        
        # 更新對方資料
        friendid = db.execute("""SELECT id FROM users WHERE username = :friendname""",
                            friendname=friendname)
        print("Reject {friendid} {friendname}".format(friendname=friendname,friendid=friendid))
           
        # 找出對方資料
        update_status = "Rejected"
        db.execute("UPDATE friends set status = :update_status WHERE user_id = :user_id and username = :username",
            user_id=int(friendid[0]["id"]),
            username=session["user_name"],
            update_status=update_status
            )
        db.execute("DELETE from friends WHERE user_id = :user_id AND status = :update_status",
                   user_id=int(friendid[0]["id"]),
                   update_status=update_status
                   )
                   
        flash("Removed!")
    return render_template("friend.html")


# helper function for friend()
def friendlist():
    # 列出所有好友的清單
    """Show friend list"""
    friends = db.execute("""
        SELECT id, username, status 
        FROM friends
        WHERE user_id = :user_id
    """, user_id=session["user_id"])        

    # 分三類資料
    # 自己的資料庫
    acceptfriends=[]
    requestfriends=[]
    rejectfriends=[]
    for friend in friends:
        if friend['status'] == 'Accepted':
            acceptfriends.append(friend)
        elif friend['status'] == 'Requested':
            requestfriends.append(friend)
        elif friend['status'] == 'Rejected':
            rejectfriends.append(friend)
        else:
            username=friend['username']
            print("Check the status of {username} friends").format(username=username)
            return render_template("friend.html")
    print("\n")
    print('------原始清單------')
    for friend in friends:
        print(friend)
    print("\n")    
    print('------已接受的朋友清單------')
    for acceptfriend in acceptfriends:
        print(acceptfriend)
    print("\n")
    print('------已送出朋友邀請------')
    for requestfriend in requestfriends:
        print(requestfriend)
    print("\n")           
    print('------已被拒絕的朋友------')
    for rejectfriend in rejectfriends:
        print(rejectfriend)          


    # 別人的資料庫
    # 對方將收到好友邀請
    # 注意：換角度思考 - 找自己的名字是否在別人的資料庫
    """Show friendrequest list"""
    friendrequests = db.execute("""
        SELECT friends.id, users.username
        FROM friends
        JOIN users
        ON users.id=friends.user_id
        WHERE friends.username =:username and friends.status = :status 
    """, username=session["user_name"], status="Requested"
    )
    print("\n")
    print("------列印出哪些待核准朋友------")            
    print(friendrequests)
    return acceptfriends, requestfriends, rejectfriends, friendrequests 


# 刪除會計科目，應該不會刪除掉交易紀錄，但是彙總或表格會變得很怪
@app.route("/deleteaccount", methods=["GET", "POST"])
@login_required
def deleteaccount():
    if request.form.get("delete"):
        accountid=request.form["delete"]
        print("\n")
        print("------DELETE ACCOUNT------")
        print(accountid)  
        
        # 該會計科目是否與他人共享
        sharestatus = db.execute("""
            SELECT sharestatus
            FROM accounts
            WHERE id =:accountid
        """, accountid=accountid)
        # share[0]["share"] != ""
        if sharestatus == "Shared": # 與他人共享
            return apology("Cannot delete the shared account", 403) # 不可刪除，必須先改變狀態
        
        db.execute("""DELETE from accounts WHERE id = :accountid""",
                accountid=accountid
                )    
        flash("Deleted Successfully!")
        return redirect("/journalentry")        
    else:
        flash("check the status of account")
        print("check the status of account")  
        return redirect("/journalentry")
       
       
# 刪除歷史交易，有朋友需要使用通知
@app.route("/deleteentry", methods=["GET", "POST"])
@login_required
def deleteentry(): # 必須提醒好友
    if  request.form.get("delete"):
        entryid=request.form['delete']
        print("\n")
        print("------DELETE TRANSACTION------")
        print(entryid)
        
        
        # 該分錄是否與他人共享
        """Show history of transactions"""
        transaction = db.execute("""
            SELECT *
            FROM transactions
            WHERE id =:entryid
        """, entryid=entryid)
        print("------ Share Status------")
        print("Credit {creditsharestatus}".format(creditsharestatus=transaction[0]["creditsharestatus"]))
        print("Credit {debitsharestatus}".format(debitsharestatus=transaction[0]["debitsharestatus"]))
        if transaction[0]["creditsharestatus"] == "Shared" or transaction[0]["debitsharestatus"] == "Shared":
            return apology("Cannot Delete the History of shared account.", 403)
        
        debit=transaction[0]["debit"]
        credit=transaction[0]["credit"]
        amount=transaction[0]["amount"]
        
        updateaccount(debit, credit, amount, note="", delete=True) # 與journalentry 共用同一個update account function
        
        # 刪除分錄
        db.execute("""DELETE FROM transactions WHERE id = :entryid""",
                entryid=entryid
                )
            
        flash("Deleted Successfully!")
        return history()  
    else:
        flash("check the status of transaction")
        print("check the status of transaction")   
        return history()   
 
 
# 刪除朋友，應該不會刪除掉共享會計科目及歷史交易        
@app.route("/deletefriend", methods=["GET", "POST"])
@login_required
def deletefriend():
    if  request.form.get("delete"):
        delete=eval(request.form["delete"])
        id=delete["id"]
        friendname=delete["username"]
        print("\n")
        print("------DELETE FRIEND ITEM------")
        print("好友清單 {delete}".format(delete=delete))
        
        
        # 搜尋目前與好友狀態
        status = delete["status"]
        
        # 刪除自己的好友
        db.execute("""DELETE from friends WHERE id = :id""",id=id)    
                
        # 找到好友ID
        friendid=db.execute("SELECT id FROM users WHERE username = :friendname",
                             friendname=friendname)
        
        # 刪除對方的好友
        if friendid != [] and status == "Accepted":
            db.execute("""DELETE FROM friends WHERE user_id = :user_id AND username = :user_name""",
                user_id=friendid[0]["id"], #對方的使用者ID
                user_name=session["user_name"] #我在對方資料庫的名字
            )
        
        sharestatus = "UNLINKED" # 代表原存在聯結
        # 更新相連會計科目之狀態 | 自己及對方ID
        accountid = db.execute("SELECT shareaccountid, id FROM accounts WHERE user_id=:user_id and share=:share",
                   user_id=session["user_id"], # 找會計科目資料庫，自己且與該位朋友共享
                   share=friendname,
                   )
        if accountid != []:
            print("\n")
            print("------RELATED ACCOUNTS------")
            print(accountid)
            for id in accountid: # 所有與該朋友的會計科目
                # 更新自己的會計科目
                updateid_self=id["id"]
                db.execute("UPDATE accounts set sharestatus = :sharestatus WHERE id=:id",
                   id=int(updateid_self), #會計科目ID
                   sharestatus=sharestatus #更新會計科目狀態
                )
                
                # 更新對方的會計科目
                updateid_share=id["shareaccountid"]
                db.execute("UPDATE accounts set sharestatus = :sharestatus WHERE id=:id",
                   id=int(updateid_share), #會計科目ID
                   sharestatus=sharestatus #更新會計科目狀態
                )
                print("\n")
                print("{accountid} No LINKED ACCOUNTS WITH {friendname}".format(accountid=accountid, friendname=friendname))
            flash("Deleted Successfully! No LINKED ACCOUNTS WITH {friendname}".format(friendname=friendname))
            print("No LINKED ACCOUNTS WITH {friendname}".format(friendname=friendname))
        else:
            print("\n")
            print("------NO RELATED ACCOUNTS------")
            flash("Deleted Successfully!")
        return redirect("/friend") 
    elif request.form.get("share"):
        friendname=request.form["share"]
        return redirect("/add_account")
    else:
        print("check the status of friend")     
        return redirect("/friend")     


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
        session["user_name"] = request.form.get("username")
        print("-------------------------------------------------------------------------------------------")
        print(request.form.get("name"))
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
