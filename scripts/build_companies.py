#!/usr/bin/env python3
"""Build source-aware company directory from explicit project relationships.
Never infer ownership, investment, EPC or subcontracting beyond projects.json fields.
Existing manually curated company descriptions are retained by name on re-runs.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# Each curated introduction is backed by an official company page. Rewrites are short summaries.
OFFICIAL={
 'Energy Development Corporation': ('菲律宾可再生能源开发与运营企业，属于 First Gen 业务体系，开展地热以及风、光、水电相关业务。','https://energy.com.ph/who-we-are/','https://energy.com.ph/'),
 'Energy Development Corporation (EDC)': ('菲律宾可再生能源开发与运营企业，属于 First Gen 业务体系，开展地热以及风、光、水电相关业务。','https://energy.com.ph/who-we-are/','https://energy.com.ph/'),
 'Aboitiz Power Corporation': ('菲律宾能源企业，业务涉及发电、电力配送及零售供电；可再生能源投资通过其相关实体开展。','https://aboitiz.com/about-us/our-businesses','https://www.aboitizpower.com/'),
 'Converge ICT Solutions Inc.': ('菲律宾光纤宽带与信息技术服务企业，提供网络连接和企业数字化服务。','https://corporate.convergeict.com/corporate-profile','https://corporate.convergeict.com/'),
 'STT GDC Philippines': ('ST Telemedia Global Data Centres 在菲律宾的数据中心业务相关实体；所属集团提供数据中心基础设施与运营服务。','https://assets.sttelemediagdc.com/sttgdc/global_en/public/2025-06/stt_gdc_esg_report_2024.pdf','https://www.sttelemediagdc.com/'),
 'Meralco PowerGen Corporation (MGEN)': ('Meralco 集团的电力发电业务平台之一；集团业务涵盖电力配送、发电、零售及能源解决方案。','https://www.meralco.com.ph/about','https://www.meralco.com.ph/'),
 'MGen Renewables / Meralco PowerGen': ('项目库中的企业角色名称引用 Meralco PowerGen 及其可再生能源业务；具体法律主体和项目股权需查项目原始公告。','https://www.meralco.com.ph/about','https://www.meralco.com.ph/'),
}

def build():
    data=json.loads((ROOT/'data/projects.json').read_text(encoding='utf-8'))
    outpath=ROOT/'data/companies.json'
    existing={}
    if outpath.exists():
        try: existing={r['name']:r for r in json.loads(outpath.read_text(encoding='utf-8')).get('companies',[]) if r.get('name')}
        except (ValueError,KeyError,TypeError): pass
    firms=defaultdict(lambda:{'roles':set(),'project_ids':set(),'sources':set()})
    rolekeys={'项目主体':'owner','投资方':'investors','建设方':'contractors','分包商':'subcontractors'}
    for p in data['projects']:
        for label,key in rolekeys.items():
            v=p.get(key) or []
            names=[v] if isinstance(v,str) else v if isinstance(v,list) else []
            for name in names:
                if not isinstance(name,str) or not name.strip():continue
                name=name.strip(); rec=firms[name]
                rec['roles'].add(label);rec['project_ids'].add(p['id'])
                if p.get('source_url'):rec['sources'].add(p['source_url'])
    result=[]
    for name,vals in sorted(firms.items(),key=lambda x:x[0].casefold()):
        old=existing.get(name,{})
        official=OFFICIAL.get(name)
        record={
          'name':name,'roles':sorted(vals['roles']),'project_ids':sorted(vals['project_ids']),
          'description':old.get('description') or (official[0] if official else ''),
          'description_source_url':old.get('description_source_url') or (official[1] if official else ''),
          'website':old.get('website') or (official[2] if official else ''),
          'description_status':old.get('description_status') or ('official_source_summary' if official else 'not_verified'),
          'project_evidence_urls':sorted(vals['sources'])[:10],
        }
        result.append(record)
    payload={'schema_version':'company-atlas-1.0','generated_at':datetime.now(timezone.utc).date().isoformat(),
        'notice':'未具备公司介绍证据时，仅展示其在项目库中的记录与角色，不推断公司主营业务或股权关系。',
        'companies':result}
    outpath.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(result)} company records, {sum(bool(x["description"]) for x in result)} supported company introductions')
if __name__=='__main__':build()
