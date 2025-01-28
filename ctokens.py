from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import random
from key import secret_key
import os
from dotenv import load_dotenv
load_dotenv()
from key import secret_key,salt

serializer = URLSafeTimedSerializer(secret_key)

# Function to Generate OTP
def generate_otp(length=6):
    return ''.join([str(random.randint(0,9)) for _ in range(length)])

# Function to create token
def create_token(data,salt):
    token = serializer.dumps(data,salt=salt)
    return token


# Function to verify the created tokens
def verify_token(token,salt,expiration=300):
    try:
        token_data = serializer.loads(token,salt=salt,max_age=expiration)
        return token_data
    except SignatureExpired:
        print('Token Expired')
        return None

# if __name__=='__main__':
#     data = {'Name':'Kesava','Mobile':'8977544095'}
#     # token = create_token(data,salt=salt)
#     tokens = 'eyJOYW1lIjoiS2VzYXZhIiwiTW9iaWxlIjoiODk3NzU0NDA5NSJ9.ZfKURw.kBeJg29ZThRkK6dMP2hjLjpdNRo'
#     print('Encrypted token:',tokens)
#     token_data = verify_token(tokens,salt=salt)
#     print('Decrypted Token data:',token_data)