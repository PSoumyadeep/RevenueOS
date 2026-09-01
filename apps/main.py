from pathlib import Path
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import hmac,hashlib,json
from .db import init_db,get_conn
from .seed import seed
from .agent import investigate,create_case,execute_case
from .config import settings
app=FastAPI(title='RevenueOS')
STATIC=Path(__file__).parent/'static';app.mount('/static',StaticFiles(directory=STATIC),name='static')
@app.on_event('startup')
def startup():
 init_db();c=get_conn();n=c.execute('SELECT COUNT(*) n FROM customers').fetchone()['n'];c.close();seed() if n==0 else None
@app.get('/')
def home():return FileResponse(STATIC/'index.html')
@app.get('/api/overview')
def overview():
 c=get_conn();risk=c.execute("SELECT COALESCE(SUM(amount),0)n FROM transactions WHERE status='failed'").fetchone()['n'];rec=c.execute("SELECT COALESCE(SUM(recovered_amount),0)n FROM recovery_cases").fetchone()['n'];cases=c.execute('SELECT COUNT(*)n FROM recovery_cases').fetchone()['n'];rc=c.execute("SELECT COUNT(*)n FROM recovery_cases WHERE status='RECOVERED'").fetchone()['n'];fp=c.execute("SELECT COUNT(*)n FROM transactions WHERE status='failed'").fetchone()['n'];c.close();return {'at_risk':risk,'recovered':rec,'recovery_rate':round(rec/risk*100,1) if risk else 0,'cases':cases,'recovered_cases':rc,'failed_payments':fp,'mode':'DEMO' if settings.demo_mode or not(settings.razorpay_key_id and settings.razorpay_key_secret) else 'RAZORPAY TEST'}
@app.get('/api/transactions')
def transactions():
 c=get_conn();r=c.execute('SELECT t.*,c.name customer_name,c.email,c.preferred_method FROM transactions t JOIN customers c ON t.customer_id=c.id ORDER BY t.created_at DESC').fetchall();c.close();return [dict(x) for x in r]
@app.get('/api/cases')
def cases():
 c=get_conn();r=c.execute('SELECT rc.*,t.failure_code,t.description,c.name customer_name FROM recovery_cases rc JOIN transactions t ON rc.transaction_id=t.id JOIN customers c ON t.customer_id=c.id ORDER BY rc.created_at DESC').fetchall();c.close();return [dict(x) for x in r]
@app.get('/api/cases/{cid}/audit')
def audit(cid):
 c=get_conn();r=c.execute('SELECT * FROM audit_logs WHERE case_id=? ORDER BY id',(cid,)).fetchall();c.close();return [dict(x) for x in r]
class Req(BaseModel):transaction_id:str
@app.post('/api/analyze')
def analyze(x:Req):
 try:return investigate(x.transaction_id)
 except ValueError as e:raise HTTPException(404,str(e))
@app.post('/api/cases')
def make_case(x:Req):
 try:cid,r=create_case(x.transaction_id);return {'case_id':cid,'analysis':r}
 except ValueError as e:raise HTTPException(404,str(e))
class ExecReq(BaseModel):case_id:str
@app.post('/api/execute')
def execute(x:ExecReq):
 try:return execute_case(x.case_id)
 except ValueError as e:raise HTTPException(404,str(e))
@app.post('/api/reset')
def reset():seed();return {'ok':True}
@app.post('/webhooks/razorpay')
async def webhook(request:Request):
 body=await request.body();sig=request.headers.get('x-razorpay-signature','');secret='change-me-in-dashboard';expected=hmac.new(secret.encode(),body,hashlib.sha256).hexdigest()
 if sig and not hmac.compare_digest(sig,expected):raise HTTPException(400,'Invalid signature')
 return {'ok':True}
@app.get('/demo-pay/{ref}',response_class=HTMLResponse)
def demo_pay(ref):return HTMLResponse(f'<h1>RevenueOS Demo Payment</h1><p>Recovery reference: <b>{ref}</b></p><p>Local payment simulator. Configure Razorpay Test Mode to create a real test Payment Link.</p>')
