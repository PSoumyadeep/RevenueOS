import requests
from .config import settings
class RazorpayClient:
    def __init__(self): self.enabled=bool(settings.razorpay_key_id and settings.razorpay_key_secret)
    def create_payment_link(self,amount,reference_id,description,email=None,phone=None):
        if not self.enabled:return {'id':'plink_demo_'+reference_id,'short_url':f'http://localhost:8000/demo-pay/{reference_id}','status':'issued','demo':True}
        payload={'amount':int(amount),'currency':'INR','description':description,'reference_id':reference_id}
        if email or phone:
            payload['customer']={}
            if email:payload['customer']['email']=email
            if phone:payload['customer']['contact']=phone
        r=requests.post('https://api.razorpay.com/v1/payment_links',auth=(settings.razorpay_key_id,settings.razorpay_key_secret),json=payload,timeout=15); r.raise_for_status(); return r.json()
