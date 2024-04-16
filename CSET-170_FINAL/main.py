from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from sqlalchemy import create_engine, text
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

def login_required(
    f,
):  # redirects to login if not logged in, idk what it does otherwise
    # Decorate routes to require login.

    # http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def manager_page(
    f,
):  # redirects to login if not logged in, idk what it does otherwise
    # Decorate routes to require login.

    # http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("isAdmin") == False:
            return apology("This is admin page, u no have access", 400)
        return f(*args, **kwargs)

    return decorated_function

def user_page(
    f,
):  # redirects to login if not logged in, idk what it does otherwise
    # Decorate routes to require login.

    # http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("isAdmin") == True:
            return apology("This is user page, u no have access", 400)
        return f(*args, **kwargs)

    return decorated_function

#configure application
app = Flask(__name__)

#configure session to use file system
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# connection string is in the format mysql://user:password@server/database
conn_str = "mysql://root:ethanpoe125@localhost/bank"
engine = create_engine(conn_str) # echo=True tells you if connection is successful or not
conn = engine.connect()

@app.route("/")
def main_page():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        #store login info
        username = request.form.get("username")
        password = request.form.get("password")
        
        #check all info exists
        if not username or not password:
            return apology("missing information", 400)
        
        #call username and check password
        params = {"username":username, "password":password}
        users = conn.execute(text("select * from accounts where username = :username"), params).all()
        user_password = conn.execute(text("select pass from accounts where username = :username"), params).all()

        # Check if the password matches their hashed version in the database
        if len(users) != 1 or not check_password_hash(user_password[0][0], password):
            return apology("invalid username and or password", 400)
        
        if users[0][8] != "true":
            return apology("Account not yet approved", 400)
        
        # Sign the user in as their current username and make the session "loggedIn"
        session["user_id"] = username
        session["loggedIn"] = True

        if users[0][7] == "true":
            session["isAdmin"] = True
        else:
            session["isAdmin"] = False
        
        return render_template("index.html")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        #store all data
        username = request.form.get("username")
        first = request.form.get("first")
        last = request.form.get("last")
        ssn = request.form.get("ssn")
        address = request.form.get("address")
        phone = request.form.get("phone")
        password = request.form.get("password")
        check_password = request.form.get("confirmation")

        #make sure all info exists
        if not username or not password or not check_password or not last or not first or not ssn or not address or not phone:
            return apology("Missing information")

        #check if username already exists
        params = {"username":username}
        users = conn.execute(text("select * from accounts where username = :username"), params).all()
        if len(users) > 0:
            return apology("user exists already", 400)
        
        #check confirmation password
        if password != check_password:
            return apology("passwords don't match", 400)

        #generate hash and store in database
        hashed = generate_password_hash(password)
        params = {"username":username, "first":first, "last":last, "ssn":ssn, "address":address, "phone":phone, "hashed":hashed}
        conn.execute(text("insert into accounts (username, first_name, last_name, social, address, phone_number, pass) values (:username, :first, :last, :ssn, :address, :phone, :hashed)"), params)
        conn.commit()
        
        return render_template("login.html")
    
    else:
        return render_template("register.html")

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return render_template("index.html")

@app.route("/myaccount")
@login_required
@user_page
def my_account():
    params = {"username":session["user_id"]}
    user = conn.execute(text("select * from accounts where username = :username"), params).all()
    bank_acct_numb = conn.execute(text("select * from bank_number where username = :username"), params).all()
    return render_template("my_account.html", user=user, bank_acct_numb=bank_acct_numb)

@app.route("/approve", methods = ["GET", "POST"])
@login_required
@manager_page
def approve():
    if request.method == "POST":
        user = request.form.get("user")
        choice = request.form.get("choice")
        params = {"username":user}
        
        if choice == "approve":
            conn.execute(text("update accounts set approved = 'true' where username = :username"), params)
            conn.commit()
            conn.execute(text("insert into bank_number (username) values (:username)"), params)
            conn.commit()
        elif choice == "disapprove":
            conn.execute(text("delete from accounts where username = :username"), params)
            conn.commit()
        
        accounts = conn.execute(text("select * from accounts where approved = 'false'")).all()
        return render_template("approve.html", accounts=accounts)
    else:
        #select all accounts that are not approved
        accounts = conn.execute(text("select * from accounts where approved = 'false'")).all()
        return render_template("approve.html", accounts=accounts)
    
@app.route("/deposit", methods = ["GET", "POST"])
@login_required
@user_page
def deposit_funds():
    if request.method == "POST":
        amount = request.form.get("amount")
        params = {"username":session["user_id"]}
        user = conn.execute(text("select balance from bank_number where username = :username"), params).all()
        # Adds the new funds to the user's account
        new_amount = user[0][0] + float(amount)
        params = {"new_amount":new_amount, "username":session["user_id"]}
        conn.execute(text("update bank_number set balance = :new_amount where username = :username"), params)
        conn.commit()
        return render_template("deposit.html")
    else:
        return render_template("deposit.html")
    
@app.route("/sendfunds", methods = ["GET", "POST"])
@login_required
@user_page
def send_funds():
    if request.method == "POST":
        # Gets the general data like amount they want to send and the current user
        amount = request.form.get("amount")
        reciever = request.form.get("recipient")
        params = {"reciever":reciever}
        user = conn.execute(text("select * from bank_number where acct_numb = :reciever"), params).all()
        params = {"username":session["user_id"]}
        current_bank_acct = conn.execute(text("select * from bank_number where username = :username"), params).all()
        # Checks if bank number is valid
        if len(user) < 1:
            return apology("Invalid bank number", 400)
        # Checks if the user has enough funds
        if current_bank_acct[0][2] >= float(amount):
            # Subtracts funds from the sender
            new_total = current_bank_acct[0][2] - float(amount)
            params = {"new_total":new_total, "username":session["user_id"]}
            conn.execute(text("update bank_number set balance = :new_total where username = :username"), params)
            conn.commit()
            # Adds funds to the reciever
            new_total = user[0][2] + float(amount)
            params = {"new_total":new_total, "acct_numb":user[0][0]}
            conn.execute(text("update bank_number set balance = :new_total where acct_numb = :acct_numb"), params)
            conn.commit()
        else:
            return apology("Not enough funds", 400)
        
        if session["user_id"] == user[0][1]:
            return apology("Can't send money to self", 400)
        
        return render_template("send_funds.html")
    else:
        return render_template("send_funds.html")

#apology, will be called if error happens
def apology(message, code=400):
    # Render message as an apology to user.
    def escape(s):
        # Escape special characters.

        # https://github.com/jacebrowning/memegen#special-characters

        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

if __name__ == '__main__':
    app.run(debug=True) # Auto restarts cause of debug mode when changes to code are made