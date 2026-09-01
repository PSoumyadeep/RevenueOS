from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .db import get_conn
def retrieve(query,k=5):
    c=get_conn(); rows=c.execute('SELECT id,title,content,category FROM knowledge').fetchall(); c.close()
    if not rows:return []
    docs=[r['title']+'\n'+r['content'] for r in rows]
    v=TfidfVectorizer(stop_words='english',ngram_range=(1,2)); X=v.fit_transform(docs); q=v.transform([query]); sims=cosine_similarity(q,X).flatten()
    return [{'id':rows[i]['id'],'title':rows[i]['title'],'content':rows[i]['content'],'category':rows[i]['category'],'score':round(float(sims[i]),3)} for i in sims.argsort()[::-1][:k] if sims[i]>0]
