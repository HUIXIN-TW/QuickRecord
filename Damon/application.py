from flask import Flask, flash, redirect, render_template, request


# Configure application
# 告訴flask需要refer the current file
# just because
app = Flask(__name__)


@app.route("/")
# 在URL上看不到/
# 就是最一開始的頁面
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return "TODO for login"
# 在CS50 IDE中只需要在terminal打flask run
# 在一般python編輯器和pip附加的extentive Flask需要加上以下code
if __name__ == '__main__':
    app.debug = True
    app.run()
#或
#if __name__ == "__main__":
    #app.run(debug=True)