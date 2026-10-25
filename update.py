"""Fetch official EA20 presidential totals. No fabricated election data."""
import json, os, time, urllib.request, urllib.error, datetime, pathlib, sys
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
HISTORY=ROOT/'data'/'history.json'
PUBLISHED=os.environ.get('PAGES_BASE_URL','https://fgvictor9012-star.github.io/eleicoes2026').rstrip('/')

def safe_number(value):
 try: return float(str(value).replace(',','.'))
 except (TypeError,ValueError): return None

def load_published_history():
 """Load the previous *deployed* history. Actions does not commit generated data."""
 url=PUBLISHED+'/data/history.json'
 for attempt in range(3):
  try:
   doc=fetch(url+'?nocache='+str(int(time.time())))
   if isinstance(doc,dict) and isinstance(doc.get('locations'),dict):return doc
   raise ValueError('Unexpected history schema')
  except urllib.error.HTTPError as err:
   if err.code==404:return {'version':1,'locations':{}}
   print('Historico remoto HTTP:',err.code)
  except Exception as err:
   print('Nao foi possivel obter historico publicado:',str(err)[:180])
  time.sleep(1+attempt)
 return None

def persist_history(new_round2,checked_at):
 """Append real, time-stamped second-round snapshots; never backfill missed stages."""
 old=load_published_history()
 if old is None:
  print('Historico remoto indisponivel: nao recriar dados historicos; esta coleta segue sem historia.')
  return
 loc=old['locations']
 for row in new_round2:
  progress=safe_number(row.get('sections_percent'))
  if progress is None or progress<=0:continue
  cs=row.get('candidates',[])
  counts=[0,0,0]
  for c in cs:
   n=str(c.get('number','')); name=str(c.get('name','')).upper()
   votes=int(c.get('votes') or 0)
   if n=='13' or 'LULA' in name:counts[0]+=votes
   elif n=='22' or ('FLAVIO' in name and 'BOLSONARO' in name):counts[1]+=votes
   else:counts[2]+=votes
  point={'time':checked_at,'sections_percent':progress,'valid_votes':int(row['valid_votes']),'counts':counts,'tse_generated_at':row.get('tse_generated_at','')}
  records=loc.setdefault(row['uf'],[])
  # No duplicate snapshots when official tally is unchanged.
  if records and records[-1].get('sections_percent')==progress and records[-1].get('counts')==counts:continue
  records.append(point)
  # Preserve detailed history through the count; limit very long series.
  if len(records)>3000:loc[row['uf']]=records[-3000:]
 HISTORY.parent.mkdir(parents=True,exist_ok=True)
 HISTORY.write_text(json.dumps(old,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 print('Historico registrado:',sum(len(v) for v in loc.values()),'observacoes para',len(loc),'localidades')

def main():
 old={}
 if OUT.exists():
  try:old=json.loads(OUT.read_text(encoding='utf-8'))
  except Exception:pass
 entries={(r['uf'],r['round']):r for r in old.get('results',[]) if isinstance(r,dict) and 'uf' in r and 'round' in r}
 errors=[];success=0;fresh_second=[]
 for turn,ele in ELECTIONS.items():
  for uf in ['BR']+UF:
   url=URL.format(ele=ele,uf=uf.lower())
   try:
    new=extract(fetch(url),uf,turn)
    entries[(uf,turn)]=new;success+=1
    if turn=='2':fresh_second.append(new)
   except Exception as ex:
    errors.append({'uf':uf,'round':turn,'error':str(ex)[:140]})
   time.sleep(.12)
 payload={'project':'Observatório Eleitoral 2026','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'success_this_check':success,'errors_count':len(errors),'recent_errors':errors[:12], 'coverage':'Brasil, 27 UFs e agregado exterior (ZZ). Municípios e países individuais ainda não integrados.','results':sorted(entries.values(),key=lambda x:(x['uf'],x['round']))}
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 persist_history(fresh_second,payload['checked_at'])
 print('Consultas válidas:',success,'Falhas:',len(errors),'Registros disponíveis:',len(entries))
 print('Erros por turno:', {t:sum(e['round']==t for e in errors) for t in ELECTIONS})
 for e in errors[:3]: print('Amostra de falha:',e)
 # Exit successfully when TSE temporarily fails, retaining last-known-good records.
if __name__=='__main__':main()
