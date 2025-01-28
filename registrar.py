from flask import Blueprint,redirect,url_for,render_template,request,flash,session,abort,jsonify
from database import execute_query
from sendmail import send_email
from key import salt,salt2
import werkzeug.security as bcrypt
from ctokens import create_token,verify_token
import os
registrar_bp = Blueprint('registrar',__name__,url_prefix='/registrar')


def remove_file_if_exists(land_id, owner_id):
    # Define file upload mappings (field name -> (subfolder, filename pattern))
    file_uploads = [
        ('land_doc', f"{owner_id}_{land_id}_land_doc.jpg"),
        ('land_photo', f"{owner_id}_{land_id}_land_photo_1.jpg"),
        ('land_photo', f"{owner_id}_{land_id}_land_photo_2.jpg"),
        ('land_photo', f"{owner_id}_{land_id}_land_photo_3.jpg")
    ]

    for (subfolder, filename_pattern) in file_uploads:
        file_path = os.path.join(registrar_bp.root_path, 'static', 'uploads', subfolder, filename_pattern)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"File '{file_path}' removed successfully.")
            except OSError as e:
                print(f"Error: {e} - Failed to remove file '{file_path}'.")
        else:
            print(f"File '{file_path}' does not exist.")

@registrar_bp.route('/dashboard')   
def dashboard():
    print(session.get('user_type'))
    if session.get('user_type') != 'registrar':
        return redirect(url_for('auth.login'))
    return render_template('registrar/dashboard.html')
        
@registrar_bp.route("/view_requests")
def view_requests():
    if session.get('user_type') != 'registrar':
        return redirect(url_for('auth.login'))
    land_details = execute_query("""
    SELECT l.land_id, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number,l.is_registered,
                concat_ws(' ',u.first_name , u.last_name) AS full_name
            FROM lands l
            JOIN users u ON l.owner_id = u.user_id
            LEFT JOIN transactions t ON l.land_id = t.land_id
            WHERE l.is_registered = 0
    """)
    return render_template('registrar/view_requests.html',land_details=land_details)




@registrar_bp.route('/view_land/<int:land_id>')
def view_land(land_id):
    if session.get('user_type') != 'registrar':
        return redirect(url_for('auth.login'))
    land_details = execute_query("""
    SELECT l.land_id, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number,
       u.first_name AS owner_first_name, u.last_name AS owner_last_name, u.username AS owner_username,
       u.date_of_birth AS owner_date_of_birth, u.email AS owner_email, u.phone_number AS owner_phone_number, u.user_type AS owner_user_type
FROM lands l
JOIN users u ON l.owner_id = u.user_id
WHERE l.land_id = %s AND l.is_registered = 0
    """,(land_id,),fetch_one=True)
    return render_template('registrar/view_land.html',land_details=land_details)


@registrar_bp.route("/approve_land/<int:land_id>",methods=['GET','POST'])
def approve_land(land_id):
    if session.get('user_type') != 'registrar':
        return redirect(url_for('auth.login'))
    execute_query("Update lands set is_registered=1 where land_id=%s",(land_id,),commit=True)
    seller_details = execute_query("SELECT concat_ws(' ',u.first_name, u.last_name) as Full_Name,u.email FROM lands l JOIN users u ON l.owner_id = u.user_id WHERE l.land_id =%s",(land_id,),fetch_one=True)
    subject = "Your Land got Approved to publish on Website"
    body = f"Hello {seller_details['Full_Name']}!,\n Your identity and land Documents are verified by registrar and it can now be available on website for Sale."
    send_email(receiver_email=seller_details['email'],subject=subject,body=body)
    flash("Land Successfully Approved")
    return redirect(url_for('registrar.approved_lands'))

@registrar_bp.route('/reject_land/<int:land_id>')
def reject_land(land_id):
    if session.get('user_type') == 'registrar' or session.get('user_type') == 'citizen':
        seller_details = execute_query("SELECT concat_ws(' ',u.first_name, u.last_name) as Full_Name,u.email,l.owner_id FROM lands l JOIN users u ON l.owner_id = u.user_id WHERE l.land_id =%s",(land_id,),fetch_one=True)
        remove_file_if_exists(land_id,seller_details['owner_id'])
        execute_query("delete from lands where land_id=%s",(land_id,),commit=True)
        if session.get('user_type')=='registrar':
            subject = "Your Land got Rejected to publish on Website"
            body = f"Hello {seller_details['Full_Name']}!,\n Your identity and land Documents are verified by registrar and As your documents found to be incorrect it can't be available on website for Sale."
            send_email(receiver_email=seller_details['email'],subject=subject,body=body)
            flash("Land Successfully Rejected")
            return redirect(url_for('registrar.view_requests'))
        if session.get('user_type')=='citizen':
            flash("Land Successfully Deleted")
            return redirect(url_for('citizen.dashboard'))
    else:
        return redirect(url_for('auth.login'))

    


@registrar_bp.route("/approved_lands")
def approved_lands():
    if session.get('user_type') != 'registrar':
        return redirect(url_for('auth.login'))
    land_details = execute_query("SELECT concat_ws(' ',u.first_name, u.last_name) as Full_Name,u.email,l.land_area_sqft,l.location,l.price,l.survey_number,l.land_id FROM lands l JOIN users u ON l.owner_id = u.user_id where l.is_registered=1")
    return render_template('registrar/approved_lands.html',land_details=land_details)

@registrar_bp.route('/approve_view_land/<int:land_id>')
def approve_view_land(land_id):
    if session.get('user_type') != 'registrar':
        return redirect(url_for('auth.login'))
    land_details = execute_query("""
    SELECT l.land_id, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number,
       u.first_name AS owner_first_name, u.last_name AS owner_last_name, u.username AS owner_username,
       u.date_of_birth AS owner_date_of_birth, u.email AS owner_email, u.phone_number AS owner_phone_number, u.user_type AS owner_user_type
FROM lands l
JOIN users u ON l.owner_id = u.user_id
WHERE l.land_id = %s AND l.is_registered = 1
    """,(land_id,),fetch_one=True)
    return render_template('registrar/approve_view_land.html',land_details=land_details)


@registrar_bp.route('/logout')
def logout():
    if session.get('user_type')=='registrar':
        session.pop('user_type')
        session.pop('user_id')
        session.pop('name')
        session.clear()
        flash('logout Success!')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('auth.login'))

