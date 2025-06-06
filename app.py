# Imports ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
from flask_mysqldb import MySQL, MySQLdb
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
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'projectlaundry'
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


def make_pie(counts, statuses):
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
    fig, ax = plt.subplots(figsize=(6, 5))

    # Create a table for services and prices
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     cellLoc='center',
                     loc='center')

    # Plot the text (date placed and total price)
    ax.text(0.5, 0.95, f"Date Follows (YYYY-MM-DD) Format", ha='center', va='center', fontsize=6,
            transform=ax.transAxes)
    ax.text(0.5, 1, f"Order Placed on : {date_placed}", ha='center', va='center', fontsize=12, transform=ax.transAxes)
    ax.text(0.5, 0.05, f"Total Price : {total_price:.2f}", ha='center', va='center', fontsize=12,
            transform=ax.transAxes)

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

@app.route('/', methods=['GET', 'POST'])
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
        result = cursor.execute("SELECT userid, username, password, role FROM users WHERE username = %s", [username])
        customer = cursor.fetchone()

        if result > 0 and customer and password == customer['password']:
            session['username'] = customer['userid']  # Store the user ID in the session
            session['role'] = customer['role']        # Store the role in the session
            session['logged_in_username'] = customer['username']  # Store the username separately in session
            return url_for('index')
        else:
            return jsonify("Invalid Credentials")

# New User ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/newuser', methods=['GET', 'POST'])
def nuser():
    return render_template('nuser.html')


@app.route('/makeuser', methods=['GET', 'POST'])
def makeuser():
    if request.method == 'POST':
        # Get form data
        user = request.form['username']
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        phone = request.form['phone']
        passw = request.form['password']
        add = request.form['address']
        dob = request.form['dob']

        # Set up the cursor
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Check if user, email, or phone already exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (user,))
            result1 = cursor.fetchone()

            cursor.execute("SELECT * FROM users WHERE emailID = %s", (email,))
            result2 = cursor.fetchone()

            cursor.execute("SELECT * FROM users WHERE PhoneNumber = %s", (phone,))
            result3 = cursor.fetchone()

            if result1 or result2 or result3:
                return jsonify("A user with same Phone No./Email/Username already exists")

            # Insert the user into the database (do not include UserID, it will auto-increment)
            cursor.execute(
                "INSERT INTO users (username, password, emailID, PhoneNumber, name, Address, dob,role) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)",
                [user, passw, email, phone, fname + ' ' + lname, add, dob,"USR"]
            )
            mysql.connection.commit()  # Commit the transaction

            # Redirect to login page
            return redirect(url_for('index'))  # Redirect to login page (index route)

        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of an error
            return jsonify("There was an error creating the user.")

    # If GET request, render the user creation form
    return render_template('nuser.html')


# Homepage ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/home')
def home():
    if 'username' in session:
        userid = session['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cursor.execute("SELECT name FROM users WHERE userid = %s", (userid,))
        customer = cursor.fetchone()

        # Call the `CheckBirthday` procedure
        cursor.execute("CALL CheckBirthday()")
        birthday_results = cursor.fetchall()

        # Check if it's the user's birthday
        msg = None
        for result in birthday_results:
            if result['UserID'] == userid and result['BirthdayMessage'] != 'FALSE':
                msg = result['BirthdayMessage']
                break

        query = "SELECT status, COUNT(*) as count FROM orders WHERE userid = %s GROUP BY status ORDER BY status"
        cursor.execute(query, [userid])
        orders = cursor.fetchall()
        statuses = [order['status'] for order in orders]
        counts = [order['count'] for order in orders]
        if statuses:
            return render_template('home.html', fname=customer['name'], piechart=make_pie(counts, statuses),
                                   statuses=make_table(counts, statuses),msg=msg)
        else:
            return render_template('home2.html', fname=customer['name'],msg=msg)
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
        # Assuming you store UserID in session or somewhere else
        cursor.execute("SELECT orderid, status, total, DateOfPlacement FROM orders WHERE UserID = %s ORDER BY orderid DESC", [user])
        table = cursor.fetchall()
        return render_template('expense.html', expenses=table)
    else:
        return redirect(url_for('index'))



@app.route('/ajax_bill', methods=['POST', 'GET'])
def ajax_bill():
    oid = request.form['txtorderid']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    result = cursor.execute("SELECT bill FROM orders where orderid = %s", [oid])
    table = cursor.fetchone()
    bill = table['bill']
    return jsonify(bill)


# Page Users/Customers ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/users')
def users():
    if 'username' in session and session['role']:

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cur.execute("SELECT * FROM users ORDER BY username")
        customers = cur.fetchall()
        return render_template('users.html', customers=customers)

    else:
        return redirect(url_for('index'))


@app.route("/ajax_add2", methods=["POST", "GET"])
def ajax_add2():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        # Get form data
        txtuser = request.form['txtuser']
        txtrole = request.form['txtrole']
        txtemail = request.form['txtemail']
        txtphone = request.form['txtphone']
        txtname = request.form['txtname']
        txtaddress = request.form['txtaddress']
        txtdob = request.form['txtdob']

        # Validate form data
        if txtuser == '':
            msg = 'Please Input Username'
        elif txtrole == '':
            msg = 'Please Input Role'
        elif txtemail == '':
            msg = 'Please Input Email'
        elif txtphone == '':
            msg = 'Please Input Phone Number'
        elif txtname == '':
            msg = 'Please Input Name'
        elif txtaddress == '':
            msg = 'Please Input Address'
        elif txtdob == '':
            msg = 'Please Input Date of Birth'
        else:
            try:
                # Insert the new record into the database
                cur.execute('''INSERT INTO users (Username, Role, EmailID, PhoneNumber, Name, Address, DOB)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                            [txtuser, txtrole, txtemail, txtphone, txtname, txtaddress, txtdob])
                mysql.connection.commit()
                msg = 'New record created successfully'
            except Exception as e:
                # Handle error (if any)
                mysql.connection.rollback()
                msg = f'Failed to create record: {str(e)}'
            finally:
                cur.close()

    return jsonify(msg)


@app.route("/ajax_update2", methods=["POST", "GET"])
def ajax_update2():
    if request.method == 'POST':
        txtuser = request.form['txtuser']  # Updated username
        txtrole = request.form['txtrole']  # Updated password
        txtemail = request.form['txtemail']  # Updated email
        txtphone = request.form['txtphone']  # Updated phone
        txtname = request.form['txtname']  # Updated name
        txtaddress = request.form['txtaddress']  # Updated address
        txtdob = request.form['txtdob']  # Updated date of birth

        # Set up the cursor
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Update the record in the database
            cur.execute('''
                UPDATE users SET 
                    Role = %s, 
                    emailID = %s, 
                    PhoneNumber = %s, 
                    name = %s, 
                    Address = %s, 
                    dob = %s
                WHERE username = %s
            ''', (txtrole, txtemail, txtphone, txtname, txtaddress, txtdob, txtuser))

            # Commit the transaction
            mysql.connection.commit()
            msg = 'Record updated successfully'
        except Exception as e:
            # Rollback in case of any error
            mysql.connection.rollback()
            msg = f'Failed to update record: {e}'
        finally:
            cur.close()

        return jsonify(msg)


@app.route("/ajax_delete2", methods=["POST", "GET"])
def ajax_delete2():
    if request.method == 'POST':
        # Get the Username from the request
        username = request.form['txtcid']

        # Set up the cursor
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        try:
            # Delete the record based on Username
            cur.execute('DELETE FROM users WHERE Username = %s', [username])
            mysql.connection.commit()
            msg = 'Record deleted successfully'
        except Exception as e:
            # Rollback in case of any error
            mysql.connection.rollback()
            print(f"Error: {e}")
            msg = 'Failed to delete record'
        finally:
            cur.close()

        return jsonify(msg)




# Page Orders ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/orders')
def orders():
    if 'username' in session and session['role']:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cur.execute("SELECT * FROM orders ORDER BY orderid")
        orders = cur.fetchall()
        return render_template('orders.html', orders=orders)
    else:
        return redirect(url_for('index'))


@app.route("/ajax_update", methods=["POST", "GET"])
def ajax_update():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtorderid = request.form['txtorderid']
        txtstatus = request.form['txtstatus']
        txtpaid = request.form['txtpaid']
        txtdatecompletion = request.form['txtdatecompletion']
        if txtdatecompletion == '':
            txtdatecompletion = None
        # Assuming your SQL UPDATE statement is correct and adjusts to the new schema
        cursor.execute("""
                UPDATE orders 
                SET status = %s,
                    dateofcompletion = %s,
                    paid = %s
                WHERE orderid = %s
                """, (txtstatus, txtdatecompletion, txtpaid,txtorderid))
        mysql.connection.commit()
        cursor.close()
        msg = 'Record successfully Updated! Please Wait'
        return jsonify(msg)


# Services ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/services')
def services():
    if 'username' in session and session['role']:

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM services")
        services = cur.fetchall()
        return render_template('services.html', services=services)

    else:
        return redirect(url_for('index'))


@app.route("/ajax_add3", methods=["POST", "GET"])
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
                cur.execute("INSERT INTO services VALUES (%s,%s,%s)", [txtserviceid, txtsname, txtprice])
                mysql.connection.commit()
                cur.close()
                msg = 'New record created successfully'
            except:
                msg = 'Service ID already used'
    return jsonify(msg)


@app.route("/ajax_update3", methods=["POST", "GET"])
def ajax_update3():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtserviceid = request.form['txtserviceid']
        txtsname = request.form['txtsname']
        txtprice = request.form['txtprice']
        cursor.execute("""
            UPDATE services 
            SET servicename = %s, 
                price = %s
            WHERE serviceid = %s
            """, (txtsname, txtprice, txtserviceid))
        mysql.connection.commit()
        cursor.close()
        msg = 'Record successfully Updated! Please Wait'
        return jsonify(msg)


@app.route("/ajax_delete3", methods=["POST", "GET"])
def ajax_delete3():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        txtserviceid = request.form['txtserviceid']
        cur.execute('DELETE FROM services WHERE serviceid = %s', [txtserviceid])
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
        return render_template('ordernow.html', services=services)

    else:
        return redirect(url_for('index'))


@app.route('/ajax_placeorder', methods=['POST'])
def ajax_placeorder():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get the selected services from the request
    services = request.json.get('selected_services', [])

    # Get the current date
    date = (datetime.date.today()).strftime("%Y-%m-%d")

    # Initialize the variables
    amount = 0
    prices = ''
    snames = ''
    services_list = []  # List to store the services for bill generation
    prices_list = []  # List to store the prices for bill generation

    # Loop through the selected services to fetch service details
    for i in services:
        cur.execute("SELECT servicename, price FROM services WHERE serviceid = %s", [i])
        x = cur.fetchone()
        if x:
            amount += int(x['price'])  # Add to the total amount
            prices = f"{prices},{x['price']}"
            snames = f"{snames},{x['servicename']}"

            # Add to the lists for bill generation
            services_list.append(x['servicename'])
            prices_list.append(float(x['price']))
        else:
            return jsonify("Requested Service Does Not Exist, Please Refresh Page")

    # Remove the initial comma
    prices = prices[1:]
    snames = snames[1:]
    # Generate the bill
    billstr = make_bill(services_list, prices_list, amount, date)
    # Insert order into the 'orders' table
    cur.execute("INSERT INTO orders (dateofplacement, total, userid, bill, status) VALUES (%s, %s,%s,%s, %s)",
                [date, amount, session['username'], billstr,"Collecting"])
    oid = cur.lastrowid
    # Insert the ordered services into the 'ORDERED_SERVICES' table
    cur.execute("INSERT INTO ORDERED_SERVICES (orderid, services, price) VALUES (%s, %s, %s)",
                (oid, snames, amount))

    # Commit changes and close the cursor
    mysql.connection.commit()
    cur.close()



    cur.close()
    return jsonify("Order Placed Successfully! ")


# Income ------------------------------------------------------------------------------------------------------------------------------------

@app.route('/income')
def income():
    if 'username' in session and session['role']:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch the income details
        cur.execute("SELECT orderid, userid, status, total, dateofplacement FROM orders ORDER BY orderid DESC")
        income = cur.fetchall()

        # Fetch summary data
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN Paid = 'Not Yet Paid' THEN 1 END) AS unpaid_count,
                COUNT(CASE WHEN Paid = 'Paid' THEN 1 END) AS paid_count,
                SUM(CASE WHEN Paid = 'Not Yet Paid' THEN Total ELSE 0 END) AS pending_amount,
                SUM(Total) AS total_amount
            FROM ORDERS
        """)
        summary = cur.fetchone()

        return render_template('income.html', income=income, summary=summary)

    else:
        return redirect(url_for('index'))


# Reviews ------------------------------------------------------------------------------------------------------------------------------------

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if 'username' in session and session['role']:  # Check if the user is logged in and has the required role
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch the list of orders for the logged-in user
        username = session['logged_in_username']  # Get the username from the session
        cursor.execute("SELECT OrderID, DateOfPlacement FROM ORDERS WHERE UserID = (SELECT UserID FROM USERS WHERE Username = %s)", (username,))
        orders = cursor.fetchall()  # Fetch all orders associated with the user
        print(f"Fetched {len(orders)} orders from the database.")  # Debug: Check number of orders fetched

        if request.method == 'POST':
            # Get form data
            order_id = request.form['order_id']  # Get the selected order ID
            review_content = request.form['review_content']
            rating = request.form['rating']

            # Fetch the UserID of the logged-in user
            cursor.execute("SELECT UserID FROM USERS WHERE Username = %s", (username,))
            user_data = cursor.fetchone()
            if user_data:
                user_id = user_data['UserID']
            else:
                print(f"User with username '{username}' not found in the database.")
                return redirect(url_for('reviews'))  # Redirect back to reviews page if user not found

            # Insert new review into the database
            cursor.execute(
                "INSERT INTO REVIEWS (UserID, Content, Rating) VALUES (%s, %s, %s)",
                (user_id, review_content, rating)
            )
            mysql.connection.commit()

            # Get the last inserted ReviewID
            cursor.execute("SELECT LAST_INSERT_ID() AS ReviewID")
            review_id = cursor.fetchone()['ReviewID']

            # Insert into ORDER_REVIEWS (assuming you need to link the review to an order)
            cursor.execute(
                "INSERT INTO ORDER_REVIEWS (ReviewID, OrderID) VALUES (%s, %s)",
                (review_id, order_id)  # Use the selected order ID here
            )
            mysql.connection.commit()

            # Redirect to the GET request to prevent resubmission on refresh
            return redirect(url_for('reviews'))

        # Fetch reviews and associated data
        cursor.execute("""
            SELECT r.ReviewID, r.Content, r.Rating, u.Username, orv.OrderID
            FROM REVIEWS r 
            JOIN USERS u ON r.UserID = u.UserID
            LEFT JOIN ORDER_REVIEWS orv ON r.ReviewID = orv.ReviewID
            ORDER BY r.ReviewID DESC
        """)
        reviews = cursor.fetchall()

        print(f"Fetched {len(reviews)} reviews from the database.")  # Debugging output

        # Return the template with orders and reviews
        return render_template('reviews.html', orders=orders, reviews=reviews)

    else:
        return redirect(url_for('index'))  # Redirect if the user is not logged in or has no role


@app.route("/delete_review", methods=["POST"])
def delete_review():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        reviewid = request.form['txtrid']  # Get the review ID from the AJAX request
        cur.execute('DELETE FROM reviews WHERE reviewid = %s', [reviewid])  # Update table/column names as needed
        mysql.connection.commit()
        cur.close()
        msg = 'Review deleted successfully'
        return jsonify(msg=msg)  # Return a JSON response with the success message
    return jsonify(msg='Invalid request'), 400



# Init the App ------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)

