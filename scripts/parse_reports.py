"""Parses saved moonsighting.org.uk monthly report pages (report-YYYY-MM.html saved as rYYYY-MM.html)
for Morocco's Awqaf sighting result and announced start date.
Usage: python scripts/parse_reports.py <dir_with_html> data/reports_parsed.json"""
import re,html,glob,json,sys,os
out={}
for f in sorted(glob.glob(sys.argv[1]+'/r*.html')):
    key=os.path.basename(f)[1:8]
    t=open(f,encoding='utf-8',errors='ignore').read()
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S); t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
    r={'size':len(t)}
    m=re.search(r'(positive|negative) (?:moon )?(?:sighting )?report from (?:the )?Morocco',t,re.I)
    if m: r['awqaf']=m.group(1).lower()
    m=re.search(r'Morocco \(Regional\):[^.]{0,40}month of [^.]{0,40}? will (?:start|begin) (?:on|from) ([A-Za-z]+,? \d+\w* [A-Za-z]+ \d{4})',t)
    if m: r['ma_start']=m.group(1)
    m=re.search(r'(?:On|on) ([A-Z][a-z]+day,? \d+\w* [A-Za-z]+ \d{4}),? \((?:29th|29) [^)]*?\)',t)
    if m: r['ev29']=m.group(1)
    ctx=[t[max(0,x.start()-150):x.start()+150] for x in re.finditer(r'sighted in Morocco|seen in Morocco|in all regions of Morocco|Kingdom of Morocco|Moroccan Ministry|Morocco Awqaf|Morocco announced|Morocco will',t)]
    r['ctx']=ctx[:4]
    out[key]=r
json.dump(out,open(sys.argv[2],'w'),indent=1)
for k,r in out.items(): print(k, r.get('size'), r.get('ev29'),'|',r.get('awqaf'),'|',r.get('ma_start'),'| nctx',len(r['ctx']))
