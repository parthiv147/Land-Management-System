import os
from dotenv import load_dotenv
load_dotenv()
secret_key = os.getenv('SECRET_KEY').encode()
salt='otp_verication'
salt2='reset_conirmation'
add_verify_details = 'add_verify_confirmation'
update_verify_details = 'update_verify_confirmation'