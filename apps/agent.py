import json,uuid
from datetime import datetime,timezone
from .db import get_conn
from .knowledge import retrieve
from .razorpay_client import RazorpayClient
def now():return datetime.now(timezone.utc).isoformat()
def log(case_id,event,actor,msg,meta=None):
 c=get_conn();c.execute('INSERT INTO audit_logs(case_id,event_type,actor,message,metadata,created_at) VALUES(?,?,?,?,?,?)',(case_id,event,actor,msg,json.dumps(meta or {}),now()));c.commit();c.close()
def investigate(tid):
 c=get_conn();tx=c.execute('''SELECT t.*,c.name,c.email,c.phone,c.tenure_months,c.successful_payments,c.previous_failures,c.disputes,c.preferred_method FROM transactions t JOIN customers c ON t.customer_id=c.id WHERE t.id=?''',(tid,)).fetchone();c.close()
 if not tx:raise ValueError('Transaction not found')
 q=f"failed payment {tx['failure_code']} amount {tx['amount']} customer history {tx['successful_payments']} successes {tx['previous_failures']} failures preferred {tx['preferred_method']} merchant retry payment link policy"
 docs=retrieve(q)
 score=.50; reasons=[]
 if tx['successful_payments']>=5:score+=.18;reasons.append(f"{tx['successful_payments']} previous successful payments")
 if tx['disputes']==0:score+=.08;reasons.append('no previous disputes')
 if tx['retry_count']==0:score+=.10;reasons.append('no recovery attempt yet')
 if tx['failure_code'] in ('NETWORK_ERROR','TEMPORARY_DECLINE','BANK_TIMEOUT'):score+=.12;reasons.append('failure appears temporary')
 if tx['amount']>=50000:score-=.18;reasons.append('high-value transaction')
 if tx['retry_count']>=2:score-=.25;reasons.append('retry limit reached')
 confidence=max(.05,min(.98,score))
 if tx['retry_count']<1 and tx['failure_code'] in ('NETWORK_ERROR','TEMPORARY_DECLINE','BANK_TIMEOUT') and tx['amount']<50000:action='retry_payment'
 elif confidence>=.45 and tx['retry_count']<2:action='create_payment_link'
 else:action='human_review'
 risk='LOW' if confidence>=.75 else ('MEDIUM' if confidence>=.50 else 'HIGH')
 return {'transaction':dict(tx),'confidence':round(confidence,3),'risk':risk,'action':action,'explanation':'; '.join(reasons),'retrieved':docs}
def create_case(tid):
 r=investigate(tid);cid='RVR-'+uuid.uuid4().hex[:8].upper();tx=r['transaction'];c=get_conn();c.execute('INSERT INTO recovery_cases VALUES(?,?,?,?,?,?,?,?,?,?,?)',(cid,tid,'PLANNED',r['risk'],r['confidence'],r['explanation'],r['action'],tx['amount'],now(),now(),0));c.commit();c.close();log(cid,'INVESTIGATION','recovery_agent','Recovery strategy selected.',{'action':r['action'],'confidence':r['confidence'],'retrieved':[d['title'] for d in r['retrieved']]});return cid,r
def execute_case(cid):
 c=get_conn();case=c.execute('SELECT * FROM recovery_cases WHERE id=?',(cid,)).fetchone();tx=c.execute('SELECT t.*,c.email,c.phone FROM transactions t JOIN customers c ON t.customer_id=c.id WHERE t.id=?',(case['transaction_id'],)).fetchone();c.close()
 violations=[]
 if case['confidence']<.45 and case['action']!='human_review':violations.append('confidence below threshold')
 if tx['retry_count']>=2 and case['action']=='retry_payment':violations.append('retry limit exceeded')
 if tx['amount']>=50000 and case['action']!='human_review':violations.append('high-value transaction requires human review')
 if violations:
  c=get_conn();c.execute("UPDATE recovery_cases SET status='ESCALATED',updated_at=? WHERE id=?",(now(),cid));c.commit();c.close();log(cid,'GUARDRAIL_BLOCK','policy_engine','Action blocked by deterministic guardrails.',{'violations':violations});return {'status':'ESCALATED','violations':violations}
 log(cid,'GUARDRAIL_PASS','policy_engine','Action passed deterministic safety checks.')
 if case['action']=='human_review':
  c=get_conn();c.execute("UPDATE recovery_cases SET status='ESCALATED',updated_at=? WHERE id=?",(now(),cid));c.commit();c.close();log(cid,'ESCALATION','recovery_agent','Insufficient confidence for autonomous recovery.');return {'status':'ESCALATED'}
 if case['action']=='retry_payment':
  recovered=tx['amount'] if tx['failure_code'] in ('NETWORK_ERROR','TEMPORARY_DECLINE','BANK_TIMEOUT') else 0
  c=get_conn();c.execute('UPDATE transactions SET retry_count=retry_count+1,recovered=? WHERE id=?',(1 if recovered else 0,tx['id']));c.execute('UPDATE recovery_cases SET status=?,recovered_amount=?,updated_at=? WHERE id=?',('RECOVERED' if recovered else 'RETRY_FAILED',recovered,now(),cid));c.commit();c.close();log(cid,'ACTION_EXECUTED','action_agent','Retry executed in demo payment simulator.',{'recovered_amount':recovered});log(cid,'VERIFICATION','verifier','Payment outcome verified.',{'status':'captured' if recovered else 'failed'});return {'status':'RECOVERED' if recovered else 'RETRY_FAILED','recovered_amount':recovered}
 link=RazorpayClient().create_payment_link(tx['amount'],cid,tx['description'] or 'Revenue recovery',tx['email'],tx['phone']);c=get_conn();c.execute('UPDATE transactions SET retry_count=retry_count+1 WHERE id=?',(tx['id'],));c.execute("UPDATE recovery_cases SET status='ACTION_SENT',updated_at=? WHERE id=?",(now(),cid));c.commit();c.close();log(cid,'ACTION_EXECUTED','action_agent','Payment recovery link created.',{'payment_link_id':link.get('id'),'demo':link.get('demo',False)});return {'status':'ACTION_SENT','payment_link':link}
