from flask import Blueprint,redirect,url_for,render_template,request,flash,session,abort,jsonify
from key import salt,salt2
from ctokens import generate_otp,create_token,verify_token
from database import execute_query
from sendmail import send_email
import werkzeug.security as bcrypt

auth_bp = Blueprint('auth',__name__,url_prefix='/auth')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    user_type_dashboard_map = {"registrar": 'registrar.dashboard', "citizen": 'citizen.dashboard'}
    if 'user_type' in session and session['user_type'] in user_type_dashboard_map:
        flash("You've Already Logged in")
        return redirect(url_for(user_type_dashboard_map[session['user_type']]))

    
    if request.method == 'POST':
        first_name = request.form.get('first_name', 'None').strip()
        last_name = request.form.get('last_name', 'None').strip()
        user_name = request.form.get('user_name', 'None').strip()
        dob = request.form.get('dob','None').strip()
        email = request.form.get('email', 'None').strip()
        mobileno = request.form.get('mobile','None').strip()
        password = request.form.get('password', 'None').strip()
        user_type = request.form.get('user_type', 'None').strip()
        hashed_password = bcrypt.generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        otp = generate_otp()
        data = {'First Name': first_name,'Last Name':last_name,'User Name':user_name,'Date Of Birth':dob, 'Email': email,'Mobileno':mobileno, 'Password': hashed_password, 'user_type': user_type,'OTP': otp,}

        # Handling for registrar user_type
        if user_type == 'registrar':
            registrar_count = execute_query("SELECT COUNT(*) as count FROM users WHERE user_type=%s", ('registrar',), fetch_one=True)
            if registrar_count['count'] == 1:
                flash('An registrar already exists. Only one registrar is allowed.')
                return redirect(url_for('auth.signup'))


        email_count = execute_query("SELECT COUNT(*) as count FROM users WHERE email=%s", (email,), fetch_one=True)['count']
        user_name_count = execute_query("SELECT COUNT(*) as count FROM users WHERE username=%s", (user_name,), fetch_one=True)['count']
        mobileno_count = execute_query("SELECT COUNT(*) as count FROM users WHERE phone_number=%s", (mobileno,), fetch_one=True)['count']
        if email_count == 1:
            flash('Email Already Exists!')
            return redirect(url_for('auth.signup'))
        if user_name_count == 1:
            flash('User Name Already Exists!')
            return redirect(url_for('auth.signup'))
        if mobileno_count == 1:
            flash('Mobile No Already Exists!')
            return redirect(url_for('auth.signup'))

        subject = 'Verify your OTP to Sign In'
        body = f'Dear User,\nPlease use the following One Time Password (OTP) to complete your verification process:\n{otp}'
        send_email(receiver_email=email, subject=subject, body=body)

        flash('OTP sent to mail! Verify your OTP.')
        return redirect(url_for('auth.otp', token=create_token(data, salt=salt)))
    else:
        return render_template('auth/signup.html')

@auth_bp.route('/otp/<token>', methods=['GET', 'POST'])
def otp(token):
    data = verify_token(token, salt=salt, expiration=600)
    if data:
        if request.method == 'POST':
            uotp = request.form.get('otp')
            if data['OTP'] == uotp:
                try:
                    user_exists = execute_query("SELECT COUNT(*) as count FROM users WHERE email=%s", (data['Email'],), fetch_one=True)['count']
                    if user_exists == 1:
                        flash('User Already Registered! Please Login to Continue.')
                        return redirect(url_for('auth.login'))

                    # Insert into users table
                    execute_query("INSERT INTO users (first_name,last_name,username,date_of_birth, email, phone_number, password_hash, user_type) VALUES (%s, %s, %s, %s,%s,%s,%s,%s)", (data['First Name'], data['Last Name'],data['User Name'],data['Date Of Birth'],data['Email'],data['Mobileno'], data['Password'], data['user_type']), commit=True)

                    flash(f"You've successfully registered as {data['user_type']}")
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    print(e)
                    return 'Something Happened! Check the server logs.'
            else:
                flash('OTP not matched!')
                return render_template('auth/otp.html', token=token)
        else:
            return render_template('auth/otp.html', token=token)
    else:
        flash('OTP Expired')
        return redirect(url_for('auth.signup'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    user_type_dashboard_map = {"registrar": 'registrar.dashboard', "citizen": 'citizen.dashboard'}
    if 'user_type' in session and session['user_type'] in user_type_dashboard_map:
        flash("You've Already Logged in")
        return redirect(url_for(user_type_dashboard_map[session['user_type']]))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = execute_query("SELECT user_id, password_hash, user_type,concat_ws(' ',first_name,last_name) as full_name FROM users WHERE email=%s", (email,), fetch_one=True)
            if user and bcrypt.check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['user_type'] = user['user_type']
                session['name'] = user['full_name']
                
                flash('Login successful')
                return redirect(url_for(user_type_dashboard_map[user['user_type']]))
            else:
                flash('Invalid email or password')
                return redirect(url_for('auth.login'))
        except Exception as e:
            print(e)
            return "Something happened! Check the server logs."
    else:
        return render_template('auth/login.html')

@auth_bp.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        email = request.form.get('email').strip()

        try:
            user = execute_query("SELECT email FROM users WHERE email = %s", (email,), fetch_one=True)

            if user:
                token_url = url_for('auth.verify', token=create_token({'email': email}, salt=salt2), _external=True)
                subject = 'Password Reset Link'
                body = f'Dear User,\nPlease use the following link to reset your password:\n{token_url}'

                send_email(receiver_email=email, subject=subject, body=body)
                flash('Reset link has been sent to your email.')
                return redirect(url_for('auth.login'))
            else:
                flash('User not registered or invalid email')
                return render_template('auth/forgot.html')
        except Exception as e:
            print(e)
            return 'Something happened! Check the server logs.'
    else:
        return render_template('auth/forgot.html')

@auth_bp.route('/verify/<token>', methods=['GET', 'POST'])
def verify(token):
    email_data = verify_token(token=token, salt=salt2, expiration=600)
    
    if email_data:
        email = email_data['email']
        if request.method == 'POST':
            new_password = request.form.get('npassword')
            confirm_password = request.form.get('cpassword')

            if new_password == confirm_password:
                try:
                    hashed_password = bcrypt.generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
                    execute_query("UPDATE users SET password_hash = %s WHERE email = %s", (hashed_password, email), commit=True)
                    flash("Password reset successful")
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    print(e)
                    return 'Something happened! Check the server logs.'
            else:
                flash('Passwords do not match')
                return render_template('auth/verify.html', token=token)
        else:
            return render_template('auth/verify.html', token=token)
    else:
        flash('Link expired or invalid')
        return redirect(url_for('auth.forget'))

