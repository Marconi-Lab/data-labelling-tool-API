from itsdangerous import URLSafeTimedSerializer
from flask import current_app
import os

# generate token
def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(os.getenv("SECRET"))
    return serializer.dumps(email, salt=os.getenv("SECURITY_PASSWORD_SALT"))

def confirm_verification_token(token, expiration=36000000):
    print("Verifying tokenn")
    serializer = URLSafeTimedSerializer(os.getenv("SECRET"))
    try:
        email = serializer.loads(
            token,
            salt=os.getenv("SECURITY_PASSWORD_SALT"),
            max_age=expiration
        ) 
    except Exception as e:
        print(e)
        return e
    print("Email verified")
    return email
