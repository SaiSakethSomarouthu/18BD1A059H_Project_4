import requests
from flask import Flask, render_template, request, session, redirect
from twilio.rest import Client
from flask_session import Session
import random

account_sid = ""
auth_token = ""
client = Client(account_sid, auth_token)
app = Flask(__name__, "/static")


@app.route('/')
def index():
    session["user"] = None
    data_json = requests.get("https://api.covid19india.org/v4/data.json").json()
    data = {}
    for state in data_json:
        districts_list = []
        if "districts" not in data_json[state].keys():
            continue
        data_list = data_json[state]["districts"]
        for district in data_list:
            if "total" not in data_list[district].keys():
                continue
            if "confirmed" not in data_list[district]["total"].keys():
                continue
            if "meta" not in data_list[district].keys():
                continue
            if "population" not in data_list[district]["meta"].keys():
                continue
            districts_list.append(district)
        if len(districts_list) == 0:
            continue
        data[state] = districts_list
    return render_template("index.html", data=data)


@app.route("/verify", methods=["POST"])
def verify():
    session["user"] = request.form
    string = str(random.randint(0, 9))
    string += str(random.randint(0, 9))
    string += str(random.randint(0, 9))
    string += str(random.randint(0, 9))
    mobile_number = request.form["mobile_number"]
    client.messages.create("+91" + str(mobile_number), from_="",
                           body="OTP for ePass registration is " + string)
    session["otp"] = string
    return render_template("verify.html", number=mobile_number, otp=string, check="0")


@app.route("/verification", methods=["POST"])
def verification():
    if session["user"] is None:
        return redirect("/")
    string = request.form["1"]
    string += request.form["2"]
    string += request.form["3"]
    string += request.form["4"]
    if string == session["otp"]:
        return redirect("/status")
    else:
        return render_template("verify.html", number=session["user"]["mobile_number"], otp=string, check="1")


@app.route("/status", methods=["GET"])
def details():
    if session["user"] is None:
        return redirect("/")
    first_name = session["user"]["first_name"]
    last_name = session["user"]["last_name"]
    aadhaar_number = session["user"]["aadhaar_number"]
    from_state = session["user"]["from_state"]
    from_district = session["user"]["from_district"]
    to_state = session["user"]["to_state"]
    to_district = session["user"]["to_district"]
    mobile_number = session["user"]["mobile_number"]
    from_date = session["user"]["from_date"]
    to_date = session["user"]["to_date"]
    data = requests.get("https://api.covid19india.org/v4/data.json").json()
    count = data[to_state]["districts"][to_district]["total"]["confirmed"]
    total = data[to_state]["districts"][to_district]["meta"]["population"]
    percentage = (count / total) * 100
    if percentage < 20:
        status = "CONFIRMED"
    else:
        status = "NOT CONFIRMED"
    client.messages.create("+91" + str(mobile_number), from_="",
                           body="Hello " + first_name + " " + last_name + ", your travel from " + from_district + " to " + to_district + " is " + status.lower() + ".")
    session["user"] = None
    return render_template("status.html", var1=first_name + " " +  last_name, var2=aadhaar_number, var3=from_state,
                           var4=from_district, var5=to_state, var6=to_district, var7=mobile_number, var8=from_date,
                           var9=to_date, var10=status)


if __name__ == "__main__":
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
    app.run(port=1000, debug=True)
