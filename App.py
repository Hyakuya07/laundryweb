# Imports ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
from flask_mysqldb import MySQL,MySQLdb
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import base64
import datetime


# Classes Defined ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





# Flask App parameters ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Change this to a random, secure key
app.config['UPLOAD_FOLDER'] = 'data/cache'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


# Defined Functions ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def make_table(counts, statuses):
    # Create a DataFrame from the counts and statuses
    df = pd.DataFrame({'Status': statuses, 'Count': counts})
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(3, 2))
    # Hide axes
    ax.axis('off')
    # Create a table and add it to the figure
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     cellLoc='center',
                     loc='center')
    # Add a title
    ax.set_title(f'Order Status')
    table.scale(1, 1.5)
    # Adjust layout
    fig.tight_layout()

    # Save the plot as an image file
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Encode the image to base64 string
    table_image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return table_image_base64

def make_pie(counts,statuses):

    # Create a pie chart
    plt.figure(figsize=(3, 2))
    plt.pie(counts, labels=statuses, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Save it to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Encode the image to base64 string
    pie_chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return pie_chart_base64


def make_bill(services, prices, total_price, date_placed):
    # Create a DataFrame for services and prices
    df = pd.DataFrame({'Service': services, 'Price': prices})
    
    # Generate the bill using matplotlib
    fig, ax = plt.subplots(figsize=(6,5))
    
     # Create a table for services and prices
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     cellLoc='center',
                     loc='center')

    # Plot the text (date placed and total price)
    ax.text(0.5, 0.95, f"Date Follows (YYYY-MM-DD) Format", ha='center', va='center', fontsize=6, transform=ax.transAxes)
    ax.text(0.5, 1, f"Order Placed on : {date_placed}", ha='center', va='center', fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.05, f"Total Price : {total_price:.2f}", ha='center', va='center', fontsize=12, transform=ax.transAxes)
    
    for col in range(len(df.columns)):
        table[0, col].set_facecolor('lightblue')

    # Hide axes
    ax.axis('off')
    
    # Adjust table layout
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)  # Adjust table scaling as needed
    
    # Adjust layout
    fig.tight_layout()
    
    # Save the plot as an image file in memory (BytesIO)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Encode the image to base64 string
    bill_image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return bill_image_base64


# Index (this has nothing, it only decides whether to show homepage or login page) ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/', methods = ['GET','POST'])
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

# Login Logic ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/ajax_login', methods=['POST'])
def ajax_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cursor.execute("SELECT pass FROM customers WHERE user = %s", [username])
        customer = cursor.fetchone()

        if result > 0 and customer and password == customer['pass']:
            session['username'] = username
            if username == "admin":
                session['role'] = True
            else:
                session['role'] = False
            return url_for('index'), 200
        else:
            return jsonify("Invalid Credentials")

# New User ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/newuser', methods = ['GET','POST'])
def nuser():
    return render_template('nuser.html')



@app.route('/makeuser', methods = ['GET','POST'])
def makeuser():
    user = request.form['username']
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    phone = request.form['phone']
    passw = request.form['password']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT * FROM customers WHERE user = %s", (user,))
    result1 = cursor.fetchone()

    cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
    result2 = cursor.fetchone()

    cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
    result3 = cursor.fetchone()

    if result1 or result2 or result3:
        return jsonify("A user with same Phone No./Email/Username already exists") 
    else:
        result = cursor.execute("INSERT INTO customers(user, pass, email, phone, fname, lname) VALUES(%s,%s,%s,%s,%s,%s)", [user,passw,email,phone,fname,lname])
        mysql.connection.commit()

        return url_for('index'), 200
    
        


# Homepage ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/home')
def home():
    
    if 'username' in session:
        user = session['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cursor.execute("SELECT fname FROM customers WHERE user = %s", [user])
        customer = cursor.fetchone()
        
        #SQL Queries
        
        query = "SELECT status, COUNT(*) as count FROM orders WHERE user = %s GROUP BY status ORDER BY status"
        cursor.execute(query,[user])
        orders = cursor.fetchall()
        statuses = [order['status'] for order in orders]
        counts = [order['count'] for order in orders]
        if statuses:
            return render_template('home.html',fname = customer['fname'],piechart = make_pie(counts,statuses), statuses = make_table(counts,statuses))
        else:
            return render_template('home2.html', fname = customer['fname'])
    else:
        return redirect(url_for('index'))
    
# Logout Logic ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))


# EXPENSES ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/expense')
def expense():
    if 'username' in session:
        user = session['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cursor.execute("SELECT orderid, status, paid, dateplaced FROM orders WHERE user = %s ORDER BY orderid DESC", [user])
        table = cursor.fetchall()
        return render_template('expense.html', expenses = table)
    else:
        return redirect(url_for('index'))

@app.route('/ajax_bill', methods = ['POST','GET'])
def ajax_bill():
    oid = request.form['txtorderid']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    result = cursor.execute("SELECT services,prices,dateplaced FROM expenses where orderid = %s", [oid])
    table = cursor.fetchone()

    services = table['services'].split(',')
    prices = [int(price) for price in table['prices'].split(',')]
    
    bill = make_bill(services,prices,sum(prices),table['dateplaced'])
    return jsonify(bill)


# Page Users/Customers ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/users')
def users():
    if 'username' in session and session['role']:
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            result = cur.execute("SELECT * FROM customers ORDER BY user")
            customers = cur.fetchall()
            return render_template('users.html',customers = customers)

    else:
        return redirect(url_for('index'))
    
@app.route("/ajax_add2",methods=["POST","GET"])
def ajax_add2():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtuser = request.form['txtuser']
        txtpass = request.form['txtpass']
        txtemail = request.form['txtemail']
        txtphone = request.form['txtphone']
        txtfname = request.form['txtfname']
        txtlname = request.form['txtlname'] 
        if txtuser == '':
           msg = 'Please Input name'   
        elif txtpass == '':
           msg = 'Please Input pass'
        elif txtemail == '':
            msg = 'Please Input txtemail'   
        elif txtphone == '':
           msg = 'Please Input phone'   
        elif txtfname == '':
           msg = 'Please Input fname'
        elif txtlname == '':
           msg = 'Please Input txtlname'      
        else:        
            cur.execute("INSERT INTO customers (user,pass,email,phone,fname,lname) VALUES (%s,%s,%s,%s,%s,%s)",[txtuser,txtpass,txtemail,txtphone,txtfname,txtlname])
            mysql.connection.commit()       
            cur.close()
            msg = 'New record created successfully'    
    return jsonify(msg)

@app.route("/ajax_update2",methods=["POST","GET"])
def ajax_update2():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtuser = request.form['txtuser']
        txtpass = request.form['txtpass']
        txtemail = request.form['txtemail']
        txtphone = request.form['txtphone']
        txtfname = request.form['txtfname']
        txtlname = request.form['txtlname']
        txtcid = request.form['txtcid']
#potential bug lies below if we change customerid to an customerid that already exists
        cur.execute("UPDATE customers SET user = %s, pass = %s, email = %s, phone = %s, fname = %s, lname = %s WHERE cid = %s ", [txtuser,txtpass,txtemail,txtphone,txtfname,txtlname,txtcid])
        mysql.connection.commit()       
        cur.close()
        msg = 'Record successfully Updated! Please Wait'   
    return jsonify(msg)    

@app.route("/ajax_delete2",methods=["POST","GET"])
def ajax_delete2():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtcustomerid = request.form['txtcid']
        cur.execute('DELETE FROM customers WHERE cid = %s',[txtcustomerid])
        mysql.connection.commit()       
        cur.close()
        msg = 'Record deleted successfully'    
    return jsonify(msg) 


# Page Orders ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/orders')
def orders():
    if 'username' in session and session['role']:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cur.execute("SELECT * FROM orders ORDER BY orderid")
        orders = cur.fetchall()
        return render_template('orders.html',orders = orders)
    else:
        return redirect(url_for('index'))


@app.route("/ajax_add",methods=["POST","GET"])
def ajax_add():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtorderid = request.form['txtorderid']
        txtuser = request.form['txtuser']
        txtstatus = request.form['txtstatus']
        txtdateplaced = request.form['txtdateplaced']
        txtdatecompletion = request.form['txtdatecompletion']
        txtpaid = request.form['txtpaid']
        if txtorderid == '':
            msg = 'Please Input orderid'   
        elif txtuser == '':
           msg = 'Please Input user'
        elif txtstatus == '':
           msg = 'Please Input status'     
        elif txtdateplaced == 'None':
           msg = 'Please Input dateplaced' 
        elif txtdatecompletion == 'None':
           msg = 'Please Input datecompletion'  
        elif txtpaid == '':
           msg = 'Please Input paid' 
        else:    
            cur.execute("INSERT INTO orders(user,status,dateplaced,datecompletion,paid) VALUES (%s,%s,%s,%s,%s)",[txtuser,txtstatus,txtdateplaced,txtdatecompletion,txtpaid])
            mysql.connection.commit()       
            cur.close()
            msg = 'New record created successfully'    
    return jsonify(msg)

@app.route("/ajax_update",methods=["POST","GET"])
def ajax_update():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtorderid = request.form['txtorderid']
        txtstatus = request.form['txtstatus']
        txtdatecompletion = request.form['txtdatecompletion']
        if txtdatecompletion == '':
            txtdatecompletion = None
        # Assuming your SQL UPDATE statement is correct and adjusts to the new schema
        cursor.execute("""
                UPDATE orders 
                SET status = %s,
                    datecompletion = %s
                WHERE orderid = %s
                """, (txtstatus, txtdatecompletion, txtorderid))
        mysql.connection.commit()
        cursor.close()
        msg = 'Record successfully Updated! Please Wait'
        return jsonify(msg)

@app.route("/ajax_delete",methods=["POST","GET"])
def ajax_delete():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtorderid = request.form['txtorderid']
        cur.execute('DELETE FROM orders WHERE orderid = %d',[int(txtorderid)])
        mysql.connection.commit()
        cur.close()
        msg = 'Record deleted successfully'    
    return jsonify(msg) 

# Services ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/services')
def services():
    if 'username' in session and session['role']:
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM services")
        services = cur.fetchall()
        return render_template('services.html',services=services)
    
    else:
        return redirect(url_for('index'))

@app.route("/ajax_add3",methods=["POST","GET"])
def ajax_add3():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtserviceid = request.form['txtserviceid']
        txtsname = request.form['txtsname']
        txtprice = request.form['txtprice']

        if txtserviceid == '':
            msg = 'Please Input Service ID'
        elif txtsname == '':
           msg = 'Please Input Service Name'
        elif txtprice == '':
           msg = 'Please Input Price'     
        else:
            try:     
                cur.execute("INSERT INTO services VALUES (%s,%s,%s)",[txtserviceid,txtsname,txtprice])
                mysql.connection.commit()       
                cur.close()
                msg = 'New record created successfully'  
            except:
                msg = 'Service ID already used'
    return jsonify(msg)

@app.route("/ajax_update3",methods=["POST","GET"])
def ajax_update3():

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtserviceid = request.form['txtserviceid']
        txtsname = request.form['txtsname']
        txtprice = request.form['txtprice']
        cursor.execute("""
            UPDATE services 
            SET sname = %s, 
                price = %s
            WHERE serviceid = %s
            """, (txtsname, txtprice,txtserviceid))
        mysql.connection.commit()
        cursor.close()
        msg = 'Record successfully Updated! Please Wait'
        return jsonify(msg)

@app.route("/ajax_delete3",methods=["POST","GET"])
def ajax_delete3():
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtserviceid = request.form['txtserviceid']
        cur.execute('DELETE FROM services WHERE serviceid = %s',[txtserviceid])
        mysql.connection.commit()
        cur.close()
        msg = 'Record deleted successfully'    
    return jsonify(msg) 


# PAGE ORDERNOW  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/ordernow')
def ordernow():
    if 'username' in session:
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM services")
        services = cur.fetchall()
        return render_template('ordernow.html',services=services)
    
    else:
        return redirect(url_for('index'))


@app.route('/ajax_placeorder', methods=['POST'])
def ajax_placeorder():

    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    services = request.json.get('selected_services', [])
    date = (datetime.date.today()).strftime("%Y-%m-%d")
    
    amount = 0
    prices = ''
    snames = ''

    for i in services:
        cur.execute("select sname, price from services where serviceid = %s",[i])
        x = cur.fetchone()
        if x:
            amount= amount+ int(x['price'])
            prices = prices +','+ x['price']
            snames = snames + ',' + x['sname']
        else:
            return jsonify("Requested Service Does Not Exist, Please Refresh Page")
    
    prices = prices[1:]
    snames = snames[1:]

    cur.execute("INSERT INTO orders (dateplaced, paid, user, status) VALUES (%s, %s,%s, %s)", [date, amount, session['username'],"In-Progress"])
    oid = cur.lastrowid

    cur.execute("INSERT INTO expenses (orderid, services, prices, dateplaced) VALUES (%s, %s, %s, %s)", (oid, snames, prices, date))

    mysql.connection.commit()       
    cur.close()
    return jsonify("Order Placed Successfully! ")


# Income ------------------------------------------------------------------------------------------------------------------------------------

@app.route('/income')
def income():
    if 'username' in session and session['role']:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orderid, user, status, paid, dateplaced FROM orders ORDER BY orderid DESC")
        income = cur.fetchall()
        return render_template('income.html',income = income)
    
    else:
        return redirect(url_for('index'))



# Init the App ------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)

