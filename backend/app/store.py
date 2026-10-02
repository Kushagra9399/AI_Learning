import threading,uuid,datetime
class Store:
    def __init__(self): self.jobs={}; self.submissions={}; self.results={}; self.lock=threading.Lock()
    def job(self,kind,payload):
        with self.lock:
            jid="job_"+uuid.uuid4().hex[:12]; self.jobs[jid]={"id":jid,"type":kind,"status":"queued","progress":0,"result":None,"error":None,"payload":payload}
            return self.jobs[jid]
    def run_async(self,job,fn):
        def run():
            try:
                job["status"]="running"; job["progress"]=20
                job["result"]=fn(); job["progress"]=100; job["status"]="completed"
            except Exception as e: job["status"]="failed"; job["error"]=str(e)
        threading.Thread(target=run,daemon=True).start()
    def get(self,jid): return self.jobs.get(jid)
    def ack(self,jid):
        if jid in self.jobs: self.jobs[jid]["acknowledged"]=True
    def submit(self,p):
        with self.lock:
            aid=p["assessment_id"]
            if aid in self.submissions: return False
            self.submissions[aid]=p; return True
    def assessor(self,aid):
        return {"assessment_id":aid,"submission":self.submissions.get(aid),"result":self.results.get(aid),"final_authority":"human_assessor"}
    def signoff(self,aid,p):
        self.results.setdefault(aid,{})["assessor_signoff"]=p
        return {"assessment_id":aid,"signed_off":True,"final_authority":"human_assessor"}
store=Store()
