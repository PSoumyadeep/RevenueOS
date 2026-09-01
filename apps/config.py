import os
from dotenv import load_dotenv
load_dotenv()
class Settings:
    demo_mode=os.getenv('DEMO_MODE','true').lower()=='true'
    razorpay_key_id=os.getenv('RAZORPAY_KEY_ID','')
    razorpay_key_secret=os.getenv('RAZORPAY_KEY_SECRET','')
settings=Settings()
