from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # determine role: from query params on GET, from form on POST
    if request.method == "POST":
        role = request.form.get('role')
        # TODO: Authenticate user
        email = request.form["email"]
        password = request.form["password"]
        # Add authentication logic here
        flash("Login functionality not yet implemented.", "info")
        return redirect(url_for("home"))

    # GET
    role = request.args.get('role')
    return render_template("login.html", role=role)


@app.route('/admin-login')
def admin_login():
    return render_template('adminlogin.html')


@app.route('/instructor-login')
def instructor_login():
    return render_template('instructorlogin.html')


@app.route('/student-login')
def student_login():
    return render_template('studentlogin.html')


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # TODO: Save user details to DB
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        year_level = request.form["year_level"]
        course = request.form["course"]
        track = request.form["track"]
        # Add user creation logic here
        flash("Signup functionality not yet implemented.", "info")
        return redirect(url_for("login"))
    return render_template("signup.html")


if __name__ == "__main__":
    app.run(debug=True)
