from flask import Flask,render_template
from key import secret_key
from auth import auth_bp
from registrar import registrar_bp
from citizen import citizen_bp
from database import execute_query


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SESSION_TYPE'] = 'FILESYSTEM'

@app.route('/')
def index():
    land_details = execute_query("""SELECT l.land_id,l.land_title, l.owner_id, l.land_area_sqft, l.location, l.price, l.survey_number, l.is_registered
FROM lands l
WHERE l.is_registered=1
  AND l.land_id NOT IN (
    SELECT t.land_id
    FROM transactions t
    WHERE t.land_id = l.land_id
)""")
    return render_template('home/cardContainer.html',land_details=land_details)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

# Registering blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(registrar_bp)
app.register_blueprint(citizen_bp)

if __name__ == "__main__":
    app.run(debug=True)