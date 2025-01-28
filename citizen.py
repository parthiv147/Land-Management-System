from flask import Blueprint,redirect,url_for,render_template,request,flash,session,abort,jsonify
from database import execute_query
from sendmail import send_email
from key import salt,salt2
from datetime import datetime,timedelta
import os,razorpay

citizen_bp = Blueprint('citizen',__name__,url_prefix='/citizen')

# Initialize Razorpay client with your key and secret
razorpay_client = razorpay.Client(auth=("rzp_test_SWFL6BUt4Tupkp", "jQ53BbGGyEbZoHzYfRjYOQxS"))

# Define the list of directory names for different file types
directory_names = ['aadhar', 'land_doc', 'photo', 'sign', 'land_photo','bank']

# Get the base path for storing uploaded files
base_path = os.path.join(citizen_bp.root_path, 'static/uploads')

# Check if the base path already exists
if not os.path.exists(base_path):
    # Create the base path if it doesn't exist
    os.makedirs(base_path, exist_ok=True)

    # Create subdirectories within the base path
    for directory_name in directory_names:
        directory_path = os.path.join(base_path, directory_name)
        os.makedirs(directory_path, exist_ok=True)

# ********** File uploads **********
# Define allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder, filename):
    if file and allowed_file(file.filename):
        file_path = os.path.join(citizen_bp.root_path, 'static/uploads', folder, filename)
        file.save(file_path)
        return file_path
    return None



@citizen_bp.route('/dashboard')
def dashboard():
    if session.get('user_type') != 'citizen':
        flash('Access denied. Please log in as a citizen.')
        return redirect(url_for('auth.login'))
    land_details = execute_query("""SELECT l.land_id,l.land_title, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number, l.is_registered
FROM lands l
WHERE l.is_registered=1
  AND l.land_id NOT IN (
    SELECT t.land_id
    FROM transactions t
    WHERE t.land_id = l.land_id
)""")
    return render_template('home/cardContainer.html',land_details=land_details)

@citizen_bp.route('/sell',methods=['GET','POST'])
def sell():
    if session.get('user_type') != 'citizen':
        return render_template('error/401.html')
    if request.method == 'POST':
        owner_id = session.get("user_id")
        land_title = request.form.get('land_title', type=str)
        land_area_sqft = request.form.get('land_area_sqft', type=float)
        location = request.form.get('location', type=str)
        price = request.form.get('price', type=float)
        survey_number = request.form.get('survey_number', type=str)
        survey_number_count = execute_query('Select count(*) as count from lands where survey_number=%s',(survey_number,),fetch_one=True)['count']
        if survey_number_count==1:
            flash("Land With given Survey Number Already in Sale")
            return redirect(url_for('citizen.sell'))
        
        if len(request.files.getlist('land_photo')) != 3:
            flash("Please upload exactly 3 Land Photos")
            return redirect(url_for('citizen.sell'))

        execute_query("Insert into lands (land_title,owner_id,land_area_sqft,location,price,survey_number) values(%s,%s,%s,%s,%s,%s)",(land_title,owner_id,land_area_sqft,location,price,survey_number),commit=True)

        land_id = execute_query("Select land_id from lands where survey_number=%s",(survey_number,),fetch_one=True)['land_id']
        print(survey_number)

        # Define file upload mappings (field name -> (subfolder, filename pattern))
        file_uploads = {
            'aadhar': ('aadhar', f"{owner_id}_aadhar.jpg"),
            'photo': ('photo', f"{owner_id}_photo.jpg"),
            'sign': ('sign', f"{owner_id}_sign.jpg"),
            'bank': ('bank', f"{owner_id}_bank.jpg"),
            'land_doc': ('land_doc', f"{owner_id}_{land_id}_land_doc.jpg"),
            'land_photo': ('land_photo', f"{owner_id}_{land_id}_land_photo")
        }

        uploaded_files = {}

        
        for field_name, (subfolder, filename_pattern) in file_uploads.items():
            if field_name in request.files:
                files = request.files.getlist(field_name)  # Get list of uploaded files for the field
                print(files)
                if field_name == 'land_photo':
                    if len(files) != 3:
                        flash("Please upload exactly 3 Land Photos")
                        return redirect(url_for('citizen.sell'))
                    
                    # Handle multiple land photos
                    for i, file in enumerate(files, 1):  # Iterate over each file with index starting from 1
                        filename = f"{filename_pattern}_{i}.jpg"
                        file_path = save_uploaded_file(file, subfolder, filename)
                        if file_path:
                            uploaded_files[f"{field_name}_{i}"] = file_path
                else:
                    # Handle single file upload
                    file = request.files[field_name]
                    print(file)
                    filename = f"{filename_pattern}"
                    file_path = save_uploaded_file(file, subfolder, filename)
                    if file_path:
                        uploaded_files[field_name] = file_path


        flash("Your Land Selling Detials has been sent to Registrar for Approval. You Will be notified once it approved.")
        return redirect(url_for('citizen.dashboard'))

    return render_template("sell.html")

@citizen_bp.route('/payment/<int:land_id>/<int:buyer_id>/<int:price>/<name>', methods=['GET','POST'])
def payment(land_id,buyer_id,price,name):
    if session.get('user_type')!= 'citizen':
        flash('Access denied. Please log in to continue')
        return redirect(url_for('auth.login'))
    # Create Razorpay order
    order_data = {
        'amount': price*100,
        'currency': 'INR',
        'receipt': 'order_receipt',  # Replace with your order ID or receipt number
        'payment_capture': 1  # Auto-capture payment when order is created
    }

    try:
        order = razorpay_client.order.create(data=order_data)
    except razorpay.errors.BadRequestError as e:
        return f"Error creating Razorpay order: {e}"

    return render_template('citizen/payment.html', order=order, item_name=name,land_id=land_id,buyer_id=buyer_id,price=price)

@citizen_bp.route('/success/<int:land_id>/<int:buyer_id>/<int:price>/<name>', methods=['GET','POST'])
def success(land_id,buyer_id,price,name):
    razorpay_payment_id = request.form['razorpay_payment_id']
    razorpay_order_id = request.form['razorpay_order_id']
    if not razorpay_order_id or not razorpay_payment_id:
        flash("We're facing bank related issues right now! please try again after some time")
        return redirect(url_for("citizen.dashboard"))
    execute_query("Insert into transactions (buyer_id,land_id,order_id,transaction_no) values(%s,%s,%s,%s)",(buyer_id,land_id,razorpay_order_id,razorpay_payment_id),commit=True)

    flash(f"Payment successful! Payment ID: {razorpay_payment_id}, Order ID: {razorpay_order_id}")
    return redirect(url_for("citizen.buyed_lands"))

@citizen_bp.route('/cancel')
def cancel():
    flash("Payment cancelled.")
    return redirect(url_for('citizen.dashboard'))
           
@citizen_bp.route('/buyed_lands')
def buyed_lands():
    if session.get('user_type')!= 'citizen':
       return render_template('error/401.html')
    land_details = execute_query("""SELECT l.land_id,l.land_title, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number, l.is_registered
FROM lands l
JOIN transactions t ON l.land_id = t.land_id
WHERE t.buyer_id = %s
""",(session.get('user_id'),))
    return render_template('profile/bought.html',land_details=land_details,active='bought')

@citizen_bp.route('/selled_lands')
def selled_lands():
    if session.get('user_type')!= 'citizen':
        return render_template('error/401.html')
    land_details = execute_query("""SELECT l.land_id,l.land_title, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number, l.is_registered
    FROM lands l
    JOIN transactions t ON l.land_id = t.land_id
    WHERE l.owner_id =%s
    """,(session.get('user_id'),))
    print(land_details)
    return render_template('profile/sold.html',land_details=land_details,active='sold')

@citizen_bp.route('/on_sale_lands')
def on_sale_lands():
    if session.get('user_type')!= 'citizen':
       return render_template('error/401.html')
    land_details = execute_query("""SELECT l.land_id,l.land_title, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number, l.is_registered
FROM lands l
WHERE l.owner_id = %s
  AND l.is_registered=1
  AND l.land_id NOT IN (
    SELECT t.land_id
    FROM transactions t
    WHERE t.land_id = l.land_id
)

""",(session.get('user_id'),))
    return render_template('profile/sale.html',land_details=land_details,active='sale')

@citizen_bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Fetch individual search parameters
        location = request.form.get('location', type=str)
        min_price = request.form.get('minPrice', type=int)
        max_price = request.form.get('maxPrice', type=int)
        min_sqft = request.form.get('minSqft', type=int)
        max_sqft = request.form.get('maxSqft', type=int)

        # Prepare base query without any specific parameter
        base_query = """
            SELECT l.land_id, l.land_title, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number, l.is_registered,
                   u.first_name AS owner_first_name, u.last_name AS owner_last_name, u.username AS owner_username,
                   u.date_of_birth AS owner_date_of_birth, u.email AS owner_email, u.phone_number AS owner_phone_number, u.user_type AS owner_user_type
            FROM lands l
            JOIN users u ON l.owner_id = u.user_id
            LEFT JOIN transactions t ON l.land_id = t.land_id
            WHERE l.is_registered = 1
              AND (t.transaction_id IS NULL OR t.transaction_id = '')
        """

        parameters = []
        
        # Add parameters to the query based on form input
        if location:
            base_query += " AND l.location = %s"
            parameters.append(location)
        if min_price is not None:
            base_query += " AND l.price >= %s"
            parameters.append(min_price)
        if max_price is not None:
            base_query += " AND l.price <= %s"
            parameters.append(max_price)
        if min_sqft is not None:
            base_query += " AND l.land_area_sqft >= %s"
            parameters.append(min_sqft)
        if max_sqft is not None:
            base_query += " AND l.land_area_sqft <= %s"
            parameters.append(max_sqft)

        # Execute the SQL query with parameters
        land_details = execute_query(base_query, tuple(parameters))

        return render_template('citizen/search.html', land_details=land_details,location=location,min_sqft=min_sqft,max_sqft=max_sqft,min_price=min_price,max_price=max_price)
    
    # If not a POST request, redirect to the dashboard
    return redirect(url_for('citizen.dashboard'))

@citizen_bp.route('/logout')
def logout():
    if session.get('user_type')=='citizen':
        session.pop('user_type')
        session.pop('user_id')
        # session.pop('name')
        session.clear()
        flash('logout Success!')
        return redirect(url_for('index'))
    else:
        return redirect(url_for('auth.login'))
