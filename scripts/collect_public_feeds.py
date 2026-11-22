#!/usr/bin/env python3
"""Collect public RSS/Atom discovery leads; NEVER create approved map projects.
GitHub Actions fetches feeds and writes data/leads.json and data/collection_status.json.
Only Python stdlib required. Respect publisher content: title, short snippet, URL, dates.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
UTC=timezone.utc
NOW=lambda:datetime.now(UTC)

class PlainText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)

def strip_html(s):
    parser=PlainText()
    try:parser.feed(s or '')
    except Exception:return ''
    return re.sub(r'\s+',' ',' '.join(parser.parts)).strip()

def normal_date(s):
    s=(s or '').strip()
    if not s:return ''
    try:
        d=parsedate_to_datetime(s)
        if d.tzinfo is None:d=d.replace(tzinfo=UTC)
        return d.astimezone(UTC).isoformat(timespec='seconds')
    except (ValueError,TypeError,OverflowError):pass
    try:
        d=datetime.fromisoformat(s.replace('Z','+00:00'))
        if d.tzinfo is None:d=d.replace(tzinfo=UTC)
        return d.astimezone(UTC).isoformat(timespec='seconds')
    except (ValueError,TypeError):return ''

def node_text(item,*paths):
    for path in paths:
        el=item.find(path)
        if el is not None and el.text and el.text.strip():return el.text.strip()
    return ''

def select_link(node,atom=False):
    if atom:
        for link in node.findall('{http://www.w3.org/2005/Atom}link'):
            href=link.attrib.get('href','');rel=link.attrib.get('rel','alternate')
            if rel=='alternate' and href:return href
    return node_text(node,'link')

def parse_rss(xml_bytes,source):
    root=ET.fromstring(xml_bytes)
    res=[]
    is_atom=root.tag.endswith('feed')
    entries=root.findall('{http://www.w3.org/2005/Atom}entry') if is_atom else root.findall('.//item')
    for entry in entries:
        atom='{http://www.w3.org/2005/Atom}'
        title=strip_html(node_text(entry,atom+'title' if is_atom else 'title'))
        link=select_link(entry,is_atom).strip()
        if not title or not link or urlparse(link).scheme not in ('http','https'):continue
        desc=strip_html(node_text(entry,atom+'summary',atom+'content') if is_atom else node_text(entry,'description'))[:320]
        d=normal_date(node_text(entry,atom+'published',atom+'updated') if is_atom else node_text(entry,'pubDate','{http://purl.org/dc/elements/1.1/}date'))
        # Google News RSS may wrap publisher pages under news.google.com. Keep original URL, do not pretend to resolve.
        publisher=node_text(entry,'source') or source['label']
        normalized_title=re.sub(r'[^\w\u4e00-\u9fff]+','',title.casefold())
        key=hashlib.sha256((normalized_title+'|'+publisher.casefold()).encode('utf-8')).hexdigest()[:20]
        res.append({'id':key,'title':title[:260],'url':link,'publisher':publisher[:120],
                    'source_label':source['label'],'source_id':source['id'],'source_method':source.get('method','rss'),
                    'category_hint':source.get('category',''), 'published_at':d,'first_seen_at':'',
                    'summary_excerpt':desc,'review_status':'unverified_discovery'})
    return res

def fetch_feed(s,timeout=16):
    if s['method']=='google_news_search':
        url='https://news.google.com/rss/search?'+urlencode({'q':s['query'],'hl':'en-PH','gl':'PH','ceid':'PH:en'})
    elif s['method']=='rss':url=s['feed_url']
    else:raise ValueError('Unknown source method: '+str(s['method']))
    req=Request(url,headers={'User-Agent':'PHInfraWatch/7.1 (+GitHub public project monitor; RSS reader)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9,*/*;q=0.5'})
    with urlopen(req,timeout=timeout) as resp:
        if int(resp.headers.get('Content-Length','0') or '0')>3_000_000:raise ValueError('feed too large')
        body=resp.read(3_000_001)
    if len(body)>3_000_000:raise ValueError('feed exceeds limit')
    return body,url

def read_json(path,default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return default

def collect(root=ROOT,fixtures_dir=None,dry_run=False):
    config=read_json(root/'config/sources.json',{})
    source_list=config.get('sources',[])
    if not source_list:raise ValueError('sources.json missing sources')
    now=NOW();stamp=now.isoformat(timespec='seconds')
    prev=read_json(root/'data/leads.json',{'leads':[]})
    old={x['id']:x for x in prev.get('leads',[]) if isinstance(x,dict) and x.get('id')}
    status=[];success=0;new_count=0
    cutoff=now-timedelta(days=int(config.get('retention_days',365)))
    for source in source_list:
        start=time.monotonic();entry={'source_id':source['id'],'label':source['label'],'state':'error','items_seen':0,'new_items':0,'checked_at':stamp,'error':''}
        try:
            if fixtures_dir:
                path=Path(fixtures_dir)/(source['id']+'.xml')
                if not path.is_file():raise FileNotFoundError('No test fixture '+path.name)
                xml_bytes=path.read_bytes()
            else:
                xml_bytes,_=fetch_feed(source)
            incoming=parse_rss(xml_bytes,source)[:int(config.get('max_items_per_source',35))]
            entry['items_seen']=len(incoming)
            for x in incoming:
                pid=x['id']
                if pid not in old:
                    x['first_seen_at']=stamp
                    old[pid]=x;new_count+=1;entry['new_items']+=1
                else:
                    # Preserve manual verification and review notes from any existing file.
                    saved=old[pid]
                    for k in ('url','summary_excerpt','published_at','publisher','source_label','source_id','category_hint'):
                        if not saved.get(k) and x.get(k):saved[k]=x[k]
            entry['state']='ok';success+=1
        except Exception as exc:
            entry['error']=str(exc)[:180]
        entry['elapsed_ms']=int((time.monotonic()-start)*1000)
        status.append(entry)
        print(f"{entry['state']:5} {source['id']:25} {entry['items_seen']:3} items; +{entry['new_items']:3} {entry['error']}")
    if not success:
        print('ERROR: all sources failed. Existing leads files have not been overwritten.',file=sys.stderr)
        return 2
    leads=[]
    for x in old.values():
        when=normal_date(x.get('published_at')) or normal_date(x.get('first_seen_at'))
        try:
            if when and datetime.fromisoformat(when)<cutoff:continue
        except ValueError:pass
        leads.append(x)
    leads.sort(key=lambda x:x.get('published_at') or x.get('first_seen_at') or '',reverse=True)
    leads=leads[:2500]
    output={'schema_version':'discovery-leads-1.0','generated_at':stamp,'source_note':'RSS feeds and Google News site-restricted discovery indexes; not a complete registry or verified projects. Links may be Google News redirect URLs.',
            'leads':leads}
    stat={'generated_at':stamp,'success_sources':success,'total_sources':len(source_list),'new_leads':new_count,'stored_leads':len(leads),'sources':status}
    if not dry_run:
        (root/'data').mkdir(exist_ok=True)
        (root/'data/leads.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (root/'data/collection_status.json').write_text(json.dumps(stat,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Completed: {success}/{len(source_list)} feeds; {len(leads)} lead records; +{new_count} new')
    return 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixtures-dir',help='Offline test folder with source_id.xml')
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--dry-run',action='store_true')
    a=parser.parse_args()
    return collect(a.root,a.fixtures_dir,a.dry_run)
if __name__=='__main__':sys.exit(main())
