# import the Flask class from the flask module
from flask import Flask, render_template, Response, redirect, url_for, request, session, flash, g, jsonify
from functools import wraps
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import io
import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from flask_cors import CORS
import pandas as pd
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__, template_folder="templates")
CORS(app)

# config
app.secret_key = 'my secret key'

# db connection  
try:
  conn = mysql.connector.connect(
    user='root', 
    password='password',
    host='dbinstance.cx9nlstfg2vl.us-east-1.rds.amazonaws.com',
    port=3306,
    database='root')
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)

df = pd.read_sql_query("select * from ultrasincomas;", conn)

df = df.drop([ 8484,  8776,  8777, 14237, 14238, 14239, 28425, 28426, 28427,
            42961, 42962, 44141, 44142, 5750, 13643, 27197, 30022, 31029, 31275, 34447, 35148, 36576,
            40828, 41889, 42740, 48356, 52673, 54471, 55464, 56212, 58042,
            58044, 59024, 59087, 60035, 60048, 60117,1427, 28424, 42960, 44140, 44787])

df["MTTR hours"] = pd.to_numeric(df["MTTR hours"])

df = df[df['Service'] != 'N/A']

dfcriticas = df[df['Priority']=='Critical']

#get percentil 95 critical critical
a = []
for i in dfcriticas['MTTR hours']:
    a.append(i)
a = sorted(a)
n = len(a)*0.95
p95 = a[:int(n)]

dfcriticas_percentil = dfcriticas[dfcriticas['MTTR hours'] < max(p95)]

dfcriticas_service = dfcriticas_percentil.groupby(['Service'])['MTTR hours'].sum().reset_index()

def availability_criticas():
    available  = []
    for i in dfcriticas_service['MTTR hours']:
        available.append (((4320-i)/4320)*100)
    return available

column_availability = availability_criticas()
dfcriticas_service['Availability'] = column_availability

# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

# use decorators to link the function to a url
@app.route('/')
@login_required
def home():
    return render_template('overview.html')

@app.route('/director')
@login_required
def director():
    return render_template('director.html')

@app.route('/director_average_time')
@login_required
def director_average_time():
    return render_template('director_average_time.html')

@app.route('/director_number_of_incidences')
@login_required
def director_number_of_incidences():
    return render_template('director_number_of_incidences.html')

@app.route('/manager')
@login_required
def manager():
    return render_template('manager.html')

@app.route('/manager_average_time')
@login_required
def manager_average_time():
    return render_template('manager_average_time.html')

@app.route('/manager_number_of_incidences')
@login_required
def manager_number_of_incidences():
    return render_template('manager_number_of_incidences.html')

@app.route('/manager_table_critical')
@login_required
def manager_table_critical():
    return render_template('manager_table_critical.html')

@app.route('/manager_table_high')
@login_required
def manager_table_high():
    return render_template('manager_table_high.html')

@app.route('/manager_table_medium')
@login_required
def manager_table_medium():
    return render_template('manager_table_medium.html')

@app.route('/manager_table_low')
@login_required
def manager_table_low():
    return render_template('manager_table_low.html')




# # route for handling the login page logic
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != 'admin' or request.form['password'] != 'admin':
#             error = 'Insert valid credentials to continue'
#         else:
#             session['logged_in'] = True
#             return redirect(url_for('home'))
#     return render_template('iberialogin.html', error=error)

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'ceo' and request.form['password'] == 'ceo':
            session['logged_in'] = True
            return redirect(url_for('home'))
        elif request.form['username'] == 'director' and request.form['password'] == 'director':
            session['logged_in'] = True
            return redirect(url_for('director'))
        elif request.form['username'] == 'manager' and request.form['password'] == 'manager':
            session['logged_in'] = True
            return redirect(url_for('manager'))

        else:
            error = 'Insert valid credentials to continue'
    return render_template('iberialogin.html', error=error)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/availability")
def availability():
    Critical_Services = []
    for i in range(len(dfcriticas_service['Service'])):
        empDict = {
        'Service': dfcriticas_service['Service'][i],
        'Availability': dfcriticas_service.iloc[i][2].round(4)}
        Critical_Services.append(empDict)
        i+=1
    return jsonify(Critical_Services)

@app.route('/query', methods=['POST'])
def update_record():
    # read database configuration
    conn = mysql.connector.connect(
        user='root', 
        password='password',
        host='dbinstance.cx9nlstfg2vl.us-east-1.rds.amazonaws.com',
        port=3306,
        database='root')
    
    status = request.form['status']
    incident_id = request.form['incident-id']
    
    # prepare query and data
    query = """ UPDATE ultrasincomas
                SET Status = %s
                WHERE `Incident ID` = %s """
 
    data = (status, incident_id)
 
    cursor = conn.cursor()
    cursor.execute(query, data)
    
    conn.commit()
    return redirect(url_for('manager'))
# start the server
if __name__ == '__main__':
    app.run(debug=True)