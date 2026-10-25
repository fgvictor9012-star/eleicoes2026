"""Fetch official EA20 presidential totals. No fabricated election data."""
import json, os, time, urllib.request, datetime, pathlib, sys
ROOT=pathlib.Path(__file__).parent
OUT=ROOT/'data'/'results.json'
UF='AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO ZZ'.split()
URL='https://resultados.tse.jus.br/oficial/ele2026/{ele}/dados/{uf}/{uf}-c0001-e{ele:06d}-u.json'
ELECTIONS={'1':6257,'2':6258}
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'ObservatorioEleitoral2026/1.0 (public election results)','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=18) as r: return json.load(r)
def candidates(doc):
 result=[]
 def walk(node,depth=0):
  if depth>12:return
  if isinstance(node,dict):
   if 'cand' in node and isinstance(node['cand'],list):
    for c in node['cand']:
     if isinstance(c,dict) and ('vap' in c or 'pvap' in c):
      try:v=int(str(c.get('vap',0)).replace('.',''))
      except (ValueError,TypeError):continue
      result.append({'name':str(c.get('nmu') or c.get('nm') or 'Candidato'),'number':str(c.get('n') or ''),'votes':v,'party':str(node.get('sg') or '')})
   for k,v in node.items():
    if k!='cand':walk(v,depth+1)
  elif isinstance(node,list):
   for x in node:walk(x,depth+1)
 walk(doc.get('carg',[]))
 unique={}
 for c in result:
  key=(c['number'],c['name'])
  if key not in unique:unique[key]=c
 return sorted(unique.values(),key=lambda x:-x['votes'])
def extract(doc,uf,turn):
 cs=candidates(doc)
 if not cs:raise ValueError('EA20 sem estrutura cand/vap reconhecível')
 # The denominator is vote totals of ALL presidential candidates in this geography/round.
 valid=sum(c['votes'] for c in cs)
 if valid<=0: raise ValueError('Sem votos válidos apurados')
 s=doc.get('s',{}) or {}
 progress=s.get('pst')
 return {'uf':uf,'round':turn,'candidates':cs,'valid_votes':valid,'sections_percent':progress,'tse_generated_at':(' '.join(str(doc.get(k,'')) for k in ('dg','hg'))).strip(),'source':URL.format(ele=ELECTIONS[turn],uf=uf.lower())}
def main():
 old={}
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf-8'))
  except Exception:pass
 entries={(r['uf'],r['round']):r for r in old.get('results',[]) if isinstance(r,dict) and 'uf' in r and 'round' in r}
 errors=[];success=0
 for turn,ele in ELECTIONS.items():
  for uf in ['BR']+UF:
   url=URL.format(ele=ele,uf=uf.lower())
   try:
    new=extract(fetch(url),uf,turn)
    entries[(uf,turn)]=new;success+=1
   except Exception as ex:
    errors.append({'uf':uf,'round':turn,'error':str(ex)[:140]})
   time.sleep(.12)
 payload={'project':'Observatório Eleitoral 2026','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'success_this_check':success,'errors_count':len(errors),'recent_errors':errors[:12], 'coverage':'Brasil, 27 UFs e agregado exterior (ZZ). Municípios e países individuais ainda não integrados.','results':sorted(entries.values(),key=lambda x:(x['uf'],x['round']))}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Consultas válidas:',success,'Falhas:',len(errors),'Registros disponíveis:',len(entries))
 # Exit successfully when TSE temporarily fails, retaining last-known-good records.
if __name__=='__main__':main()
