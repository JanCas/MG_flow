#!/usr/bin/env python3
"""Build the static report and GitHub Pages site from one research register."""
import csv
import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / 'data/research.json').read_text())
S = {s['id']: s for s in D['sources']}
P = D['profiles']
J = D['projects']
COUNTRY = D['countries']
QUALITY_TRADE = D['quality_trade']
PROCESSES = D['processes']
US_DEVELOPMENT = D['us_development']
FIGURE_DIR = Path('figures/v1')
CHARTS = json.loads((ROOT/FIGURE_DIR/'charts.json').read_text())['charts']
E = html.escape
GENERATED = []

# Compact comparison labels; full qualifications stay in the linked profiles.
BRIEF = {
 'baowu': ('Dolomite; operating Chaohu mine; Wutai resource/approvals; associate Qingyang','Vertical-retort silicothermic','Not located in reviewed sources','2025 / H1 2026 filings','100,000 primary baseline; expansions separate'),
 'tianyu': ('Dolomite; quarry undisclosed, Fugu','Thermal; current plant detail incomplete','32,000 historical','2017','50,000 historical'),
 'yinguang': ('Dolomite; integrated Wenxi mining, quarry unnamed','Thermal; current plant detail incomplete','31,000 historical (Huasheng)','2017','65,000 Huasheng; group 100,000 overlaps'),
 'bada': ('Captive dolomite mine; ~8 km from Wenxi plant','Thermal; current plant detail incomplete','29,800 historical; 35,000 undated claim','2017 / undated','40,000 company (undated); 50,000 USGS (2023 table)'),
 'jinwantong': ('Dolomite inferred from cluster; quarry unknown','Silicothermic demonstration line confirmed, Feb 2026','28,500 historical','2017','40,000 (2017); 42,000 (USGS 2023 table)'),
 'yide': ('Dolomite, source unknown; integrated FeSi','Pidgeon, plant-specific confirmation','Not disclosed','Dec 2025 visit','20,000 primary'),
 'huiye': ('Undisclosed facility-specific feed','Not verified at facility','33,300 historical','2017','50,000 historical'),
 'regal': ('Undisclosed facility-specific feed','Not verified at facility','26,700 historical','2017','30,000 primary; 100,000 Mg alloys (undated company page)'),
 'remt': ('Dolomite; captive Baishan mine; Hami source unknown','Thermal; current trading/tolling separate','12,373 annual / 1,680 half-year sales, not production','2025 / H1 2026 (latter: indexed filing mirror)','Hami 45,000 / Baishan 75,000 historical, not available supply'),
 'dead-sea-magnesium': ('Dead Sea brine → internal carnallite','VAMI chloride electrolysis','~17,800 primary','2025','21,000 / 34,000 conflicting USGS bases'),
 'rima': ('Captive dolomite, mine unnamed; internal FeSi','Proprietary RIMA silicothermic','Not disclosed; Brazil 20,000 estimate only','2025 national estimate','22,000 primary (country/sole producer)'),
 'solikamsk': ('Carnallite; Uralkali historically, current contract unverified','Chloride electrolysis','Not disclosed; 15,336 historical sales','2019 sales','18,200 historical'),
 'uktmp': ('External carnallite + internal recycled MgCl2','Chloride electrolysis; titanium loop','19,043–19,568 crude process stream','Annual range in 2021–2022; not a two-year total','21,000 national estimate; plant basis unresolved'),
 'kar-mineral': ('Dolomite; specific quarry/supplier unknown','Pidgeon','Not disclosed; Türkiye 15,000 estimate only','2025 national estimate','15,000 primary'),
 'ferdows': ('Dolomite; domestic source, exact mine unknown','Pidgeon','No company annual actual; reportedly idle','Sep 2026 status; Iran estimate is not plant output','6,000 design; available capacity unverified'),
 'us-magnesium': ('Great Salt Lake brine; company ponds','Historical chloride electrolysis','0 national primary; facility inactive','2024–2025','63,500 company; idle'),
 'avisma': ('Historical carnallite + internal returned MgCl2','Electrolysis; titanium loop','Not verified','No recent actual','Not verified'),
 'qinghai': ('Qarhan brine-derived chloride → liquid Mg','Electrolysis; trial operation documented','292.705 liquid Mg / 265 ingot, overlapping','One-cell trial Feb–Apr 2025; not annual','100,000 primary design claim; 56,000 former alloy casthouse'),
 'magontec': ('Diecaster scrap + purchased primary alloy','Remelt/refine/alloy; anodes','~700 distributed primary alloy, six months','H2 2025 shipments','24,000 recycling (2024)'),
 'amacor': ('Industrial Mg scrap; suppliers unnamed','Remelt/refine/alloy','Not disclosed','No annual actual','50,000 undated recycling claim'),
 'luxfer': ('Primary metal + machining returns/swarf','Alloy manufacture, remelting, fabrication','Not disclosed','No annual actual','Not disclosed'),
}

GROUPS = [
 ('Commercial primary producers and integrated groups', ['baowu','yinguang','bada','yide','dead-sea-magnesium','rima','solikamsk','uktmp','kar-mineral']),
 ('Established facilities with limited recent evidence or interruptions', ['tianyu','jinwantong','regal','remt']),
 ('Inactive or unresolved primary facilities', ['huiye','ferdows','us-magnesium','avisma','qinghai']),
 ('Recycling, alloy manufacture and fabrication', ['magontec','amacor','luxfer']),
]
BY_ID = {p['id']:p for p in P}

SUMMARY = [
 ('Who produces it?', 'China dominates primary supply. Baowu is a leading integrated group; Fugu’s many producers form a major cluster. Outside China, established supply includes RIMA, ICL Dead Sea Magnesium, Solikamsk, UKTMP and Kar Mineral. The directory separates current commercial evidence, interruptions, older evidence and downstream processors. [S01] [S02] [S53]'),
 ('What do they start with?', 'Most covered Chinese operations, RIMA and Kar Mineral use dolomite. ICL uses Dead Sea brine-derived carnallite; chloride-fed plants also include Solikamsk and UKTMP. Recyclers start with metal scrap and purchased metal. Exact quarry contracts and numerical feed assays are often undisclosed. [S02] [S18] [S23] [S28] [S33] [S35] [S45]'),
 ('How is the metal made?', 'Thermal producers heat dolomite into a reactive oxide mixture, then use a silicon-bearing material to release magnesium. Electrolytic producers prepare dry magnesium chloride and use electricity to separate the metal. Both routes finish with refining and casting or alloying. Recycling starts with existing metal and remelts it. [S13] [S21] [S23] [S33] [S45]'),
 ('How much?', 'USGS estimates 1.1 million t of world primary production in 2025, including 950,000 t in China. ICL reports about 17,800 t of metal in 2025. Many other company figures are nameplates, old actuals, sales or mixed-material totals; a reliable current company league table cannot be constructed from the reviewed public evidence. [S01] [S18]'),
 ('Who buys it?', 'Evidence usually identifies sectors rather than direct ingot buyers. Documented links include Baowu component deliveries to Geely StarDrive, VREMT and ZF, UKTMP’s internal titanium production, and Magontec’s automotive scrap loop. Future project offtake and letters of intent are kept separate. [S02] [S32] [S45] [S56]'),
]

METHODS = [
 ('Scope and cutoff','Research cutoff: 27 September 2026. This is a public-source desk review of major established primary producers, selected recyclers/alloy makers, and separately identified development projects. It is not a census of every Chinese smelter or every global scrap remelter. “Latest located” means latest year-qualified figure in the reviewed evidence, not a claim that no newer private or inaccessible disclosure exists.'),
 ('What counts as primary metal','Primary production is new metallic magnesium extracted from mineral/brine/residue feed. Recovery from old industrial residues may be described as recycling by a developer, but is separated here from remelting already metallic scrap. Magnesium oxide, hydroxide, chloride, carbonate, potash and dolomite tonnage are excluded from metal totals. Alloy output includes other elements; shipments may include trading and inventory movements.'),
 ('Avoiding double counting','Do not add a group to its subsidiaries, primary metal to the alloys subsequently made from it, a regional total to its firms, or recycled metal to primary supply. UKTMP/AVISMA internal MgCl2 regeneration can repeatedly circulate the same magnesium. Gross electrolytic output, merchant ingot and virgin primary supply are different measures. Project nameplates and inactive plant capacities are excluded from current production.'),
 ('Quantity conventions','t means metric tonnes; t/y means metric tonnes per year. Numbers in source tables reported in thousand tonnes are multiplied by 1,000. Approximate values and estimates retain their labels. Annual actuals, national estimates, sales, partial-year shipments and historical capacities are shown on separate bases. Unknown values remain blank in numeric exports, never imputed as zero. USGS dashes mean zero and are displayed as such; they are different from unknown company quantities.'),
 ('Feedstock analytical basis','Report Mg, MgO and MgCl2 as stated; do not silently convert among them. Raw ore/brine, dolime (calcined dolomite), prepared chloride, scrap alloy and final metal are distinct sampling boundaries. Dry/wet basis, impurities and preparation are retained when disclosed; otherwise marked unavailable. No theoretical stoichiometric ore requirement is represented as an observed industrial consumption rate.'),
 ('Process names','Silicothermic means using silicon, normally supplied in ferrosilicon, to remove oxygen and release magnesium. Aluminothermic uses aluminum instead. These materials are called reductants. Pidgeon names a thermal route; VAMI identifies the electrolytic technology used at Dead Sea Magnesium. Facility-specific explanations follow the feed through preparation, metal production and finishing.'),
 ('Customers and applications','A named OEM at the end of a component chain is not automatically an ingot buyer. Current deliveries, historical relationships, internal consumption, development partnerships, future offtake and nonbinding LOIs are identified separately. General industry applications are context, not a producer-specific sales allocation. [S65]'),
 ('Source hierarchy and access','Preference is given to filings, company operational disclosures, government reports, permits and technical references. Industry reporting fills status gaps; historical conferences and directories are clearly dated. Mirrors and search-index-only access are identified in the source register. Sources are linked, not archived; no private customer data or confidential annual production is assumed.'),
 ('Why there is no current producer ranking','Company magnesium-only annual volumes are sparse. Chinese private producers often disclose only capacities; older tables do not prove current operations. Baowu’s consolidated nonferrous tonnage includes aluminum. REMT publishes product sales. Russian and Kazakh figures require reconciliation with titanium loops. Even national series conflict: Baowu cites CNIA’s China 2025 primary output of 1,093,500 t, versus USGS’s 950,000 t estimate. The CNIA figure is not inserted into USGS’s world denominator. [S01] [S02] [S15] [S33]'),
 ('Remaining work for a definitive census','Priority gaps are dated company primary output, current commissioning/utilization of Chinese expansions, mine-linked feed assays, purchased/captive splits and named customer tonnage. The historical leading-producer table also lists Wenxi Zhenxin, Sun and Jingfu; they are acknowledged as coverage gaps rather than silently assumed closed or assigned unsupported profiles. [S05]'),
]

COVERAGE = [
 ('Baowu / major Chinese private groups','Leading integrated group and historically large smelters','Good group/process evidence; uneven mine detail; weak current Mg-only actuals','Use site-specific profiles; do not rank capacities as output. [S02] [S05]'),
 ('ICL Dead Sea Magnesium','Established electrolytic primary producer','Current company metal actual and integrated feed chain; customers unnamed','Strongest recent annual company metal observation in this review. [S18]'),
 ('RIMA / Kar Mineral','Established national primary suppliers','Government route evidence; company annual tonnage absent','National estimates remain proxies. [S23] [S35]'),
 ('Solikamsk / UKTMP / AVISMA','Primary and titanium-linked chloride operations','Useful technical/historical evidence; current virgin/returned split weak','Separate fresh supply, gross process streams and merchant metal. [S27] [S33] [S44]'),
 ('Magontec / AMACOR / Luxfer','Recyclers, alloy makers and fabricators','Good input/product descriptions; annual mass quantities limited','Keep separate from virgin primary totals. [S45] [S48] [S51]'),
 ('US Magnesium / Qinghai / REMT','Major historical chains with status changes','Cessation, exit or suspension evidence; restart details incomplete','Legacy nameplate is not verified current supply. [S01] [S16] [S40] [S45]'),
]

GENERAL_MARKETS = [
 ('Aluminum alloying','Mg metal → aluminum alloy → sheet, extrusions or castings','Packaging, transport and other aluminum products. This is an alloying addition, not a magnesium component. [S54]'),
 ('Magnesium alloys','Primary/recycled Mg → alloy ingot → cast or wrought part','Vehicle components, portable equipment and other lightweight structures; no OEM allocation inferred. [S54] [S65]'),
 ('Iron and steel treatment','Mg powder/granules or treatment alloy → melt treatment','Desulfurization and iron treatment; metal is consumed as a reagent. [S54]'),
 ('Titanium reduction','Mg → titanium-chloride reduction → titanium sponge','Internal metallurgical consumption, often with magnesium-chloride regeneration. [S32] [S33]'),
 ('Sacrificial anodes','Mg alloy → anode → corrosion protection','Water-heater/tank protection is documented in Magontec’s business; not a volume allocation across all producers. [S45]'),
]

def plain(value):
    return re.sub(r'\s*\[S\d+\]', '', str(value))

def rich(value):
    def cite(m):
        s=S[m[1]]
        return f'<a class="cite" href="{E(s["url"],quote=True)}" title="{E(s["publisher"]+": "+s["title"],quote=True)}">{m[1]}</a>'
    return re.sub(r'\[(S\d+)\]', cite, E(str(value)))

def md(value):
    return re.sub(r'\[(S\d+)\](?!\()',lambda m:f'[{m[1]}]({S[m[1]]["url"]})',str(value))

def para(value,css=''):
    return f'<p{(" class="+chr(34)+css+chr(34)) if css else ""}>{rich(value)}</p>'

def table(headers,rows,caption=''):
    head=''.join(f'<th scope="col">{E(h)}</th>' for h in headers)
    body=''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)
    return f'<div class="table-scroll" role="region" aria-label="{E(caption or headers[0])}" tabindex="0"><table><caption>{E(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

def mdtable(headers,rows):
    def cell(v): return md(v).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |']+['| '+' | '.join(cell(c) for c in row)+' |' for row in rows])+'\n\n'

NAV=[('Overview','index.html'),('Producers','producers/index.html'),('Comparisons','compare/output.html'),('Processes','processes.html'),('Quality & trade','quality-trade.html'),('U.S. case','us-development.html'),('Charts','charts.html'),('Projects','projects/index.html'),('Sources','sources.html')]
def writepage(path,title,eyebrow,lead,body,active=''):
    depth=len(Path(path).parts)-1
    prefix='../'*depth
    nav=''.join(f'<a href="{prefix}{url}"'+(' aria-current="page"' if label==active else '')+f'>{label}</a>' for label,url in NAV)
    content=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} | Magnesium Atlas</title><meta name="description" content="{E(plain(lead),quote=True)}">
<link rel="stylesheet" href="{prefix}assets/style.css"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="{prefix}index.html"><span class="element">Mg<small>12</small></span><span>MAGNESIUM<br><b>ATLAS</b></span></a><nav aria-label="Main navigation">{nav}</nav><a class="report-link" href="{prefix}report.md" download>Download report ↓</a></header>
<main id="main"><div class="page-head"><p class="eyebrow">{E(eyebrow)}</p><h1>{E(title)}</h1>{para(lead,'lead')}</div>{body}</main>
<footer><div><strong>Magnesium Atlas</strong><p>Research cutoff · 27 September 2026</p></div><div><a href="{prefix}methods.html">Scope &amp; methods</a><a href="{prefix}downloads.html">Data downloads</a><a href="{prefix}report.html">Read full report</a></div><p class="footer-note">Metric tonnes unless a source unit is explicitly qualified. Capacity, output, sales and recycled metal are distinct measures.</p></footer></body></html>'''
    target=ROOT/path; target.parent.mkdir(exist_ok=True,parents=True); target.write_text(content)
    GENERATED.append(path)

def subnav(current):
    return '<nav class="tabs" aria-label="Comparison pages">'+''.join(f'<a href="{f}.html"'+(' aria-current="page"' if f==current else '')+f'>{label}</a>' for f,label in [('feedstocks','Feedstocks & routes'),('output','Output & capacity'),('markets','Buyers & applications')])+'</nav>'

def sourcecards(ids,prefix=''):
    return '<ul class="source-list">'+''.join(f'<li><span class="source-id">{i}</span><div><a href="{E(S[i]["url"],quote=True)}">{E(S[i]["title"])}</a><p>{E(S[i]["publisher"])} · {E(S[i]["date"])}</p><small>{E(S[i]["locator"])}</small> <a class="register" href="{prefix}sources.html#{i}">Register notes ↗</a></div></li>' for i in ids)+'</ul>'

PROFILE_SECTIONS=[
 ('company','Company and facilities',[('Ownership','ownership'),('Main products','products')]),
 ('feedstock','Feedstock and preparation',[('Starting material','feedstock'),('Source and purchasing','origin'),('Grade and impurities','grade'),('Consumption and boundaries','ratio'),('Supply dependencies','constraints')]),
 ('process','Production process',[('Route at the covered facility','route')]),
 ('output','Output and capacity',[('Actual output and reporting year','actual'),('Capacity, t/y','capacity'),('Interpretation and recent trend','output_note')]),
 ('markets','Buyers and applications',[('Documented buyers / partners','buyers'),('Intermediate products','intermediate'),('Final applications','applications'),('Relationship basis','relationship')]),
 ('gaps','Evidence gaps',[('What remains unresolved','gaps')]),
]

def profilebody(p,full=False):
    sections=''
    for anchor,title,fields in PROFILE_SECTIONS:
        id=p['id']+'-'+anchor if full else anchor
        sections+=f'<section id="{id}"><h2>{title}</h2><dl class="facts">'+''.join(f'<div><dt>{label}</dt><dd>{rich(p[key])}</dd></div>' for label,key in fields)+'</dl></section>'
        if anchor=='process':
            sections+=f'<p class="small"><a href="{"" if full else "../"}processes.html">Read the detailed production-process guide ↗</a></p>'
    return sections

def create_profiles():
    for p in P:
        toc='<aside class="toc"><strong>In this profile</strong>'+''.join(f'<a href="#{a}">{t}</a>' for a,t,_ in PROFILE_SECTIONS)+'<a href="#references">Sources</a><hr><a href="index.html">← Producer directory</a></aside>'
        status=f'<div class="status-line"><span class="tag">{E(p["category"])}</span><span>{E(p["status"])}</span></div>'
        body=status+f'<div class="article-layout">{toc}<article>{profilebody(p)}<section id="references"><h2>Sources for this profile</h2>{sourcecards(p["sources"],"../")}</section></article></div>'
        writepage('producers/'+p['id']+'.html',p['name'],p['country']+' / Producer profile',p['facility'],body,'Producers')

def create_directory():
    rows=''
    for title,ids in GROUPS:
        rows+=f'<section><h2>{E(title)}</h2><div class="directory">'
        for id in ids:
            p=BY_ID[id]; b=BRIEF[id]
            rows+=f'<a class="directory-row" href="{id}.html"><div><small>{E(p["country"])}</small><h3>{E(p["name"])}</h3><p>{E(p["status"])}</p></div><div><span class="tag">{E(p["category"])}</span><p>{E(b[0])}</p></div><span class="go" aria-hidden="true">↗</span></a>'
        rows+='</div></section>'
    writepage('producers/index.html','Producer directory','21 profiles / Distinct production boundaries','Browse established primary producers, interrupted and historical facilities, and downstream metal processors. Inclusion is not a current output ranking.',rows,'Producers')

def create_comparisons():
    for kind in ['feedstocks','output','markets']:
        content=subnav(kind)
        if kind=='feedstocks':
            headers=['Producer / facility','Feedstock and source','Production route']
            title='Feedstocks & production routes'
            lead='Follow the raw resource to the prepared feed and the metal-making step. Detailed assays, purchasing boundaries and gaps are in each profile.'
        elif kind=='output':
            headers=['Producer','Actual or other reported quantity (t)','Reporting period / basis','Capacity (t/y)','Main products']
            title='Output & capacity'
            lead='Read the basis before comparing the numbers. Historical actuals, national estimates, sales and partial-year shipments are explicitly labeled; they do not form a current ranking.'
        else:
            headers=['Producer','Documented buyer / partner','Intermediate product','Final application / relationship basis']
            title='Buyers & applications'
            lead='Commercial evidence is often sector-level. A component customer, historical partner or future offtaker is not automatically a current buyer of primary ingot.'
            content+='<section><h2>General industry pathways</h2>'+para('Context only: the table below is not a list of customers or a sales allocation for each producer.')+table(['Market','Intermediate chain','Final application / evidence'],[[rich(c) for c in row] for row in GENERAL_MARKETS])+'</section>'
        for group,ids in GROUPS:
            rows=[]
            for id in ids:
                p=BY_ID[id]; b=BRIEF[id]
                link=f'<a href="../producers/{id}.html">{E(p["name"])}</a>'
                cites=' '.join('['+s+']' for s in p['sources'])
                if kind=='feedstocks': rows.append([link+para(p['facility'],'small'),rich(b[0]),rich(b[1])+para(cites,'small')])
                elif kind=='output': rows.append([link,rich(b[2]),rich(b[3])+para(cites,'small'),rich(b[4]),rich(p['products'])])
                else: rows.append([link,rich(p['buyers']),rich(p['intermediate']),rich(p['applications'])+para(p['relationship'],'small')])
            content+=f'<section><h2>{E(group)}</h2>'+table(headers,rows,group)+'</section>'
        content+=f'<p class="download-line"><a href="../data/{kind}.csv" download>Download this comparison (CSV) ↓</a> <a href="../methods.html">Definitions & limitations</a></p>'
        if kind=='output':
            content+='<section><h2>Country context, on one statistical basis</h2>'+para('USGS MCS 2026 estimates. Capacity includes idle facilities; primary production only. Rounded totals are not a sum of company profiles. [S01]')+countrytable()+'</section>'
        writepage('compare/'+kind+'.html',title,'Comparisons / Magnesium metal',lead,content,'Comparisons')

def countrytable():
    rows=[]
    for c in COUNTRY:
        values=[]
        for k in ['output_2024_t','output_2025_estimate_t','capacity_2025_t_per_y']:
            v=c[k]
            values.append('—' if v==0 else f'{v:,.0f}')
        rows.append([E(c['country'])]+values)
    return table(['Country','2024 production, mostly estimates (t)','2025 production, estimate (t)','2025 capacity, mixed basis (t/y)'],rows,'USGS national primary magnesium series [S01]; — = zero in source; 2024 China/Israel and capacity US/Israel/Türkiye reported; other nonzero entries estimated')

def create_projects():
    cards=''
    for j in J:
        body='<div class="notice">Development / demonstration evidence. Excluded from established commercial primary production totals.</div>'
        for key,title in [('status','Company, site and status'),('feedstock','Feedstock and source'),('route','Proposed or demonstrated route'),('volume','Actual versus design scale'),('markets','Future buyers and applications'),('gaps','Unresolved dependencies')]:
            body+=f'<section><h2>{title}</h2>{para(j[key])}</section>'
        body+='<section><h2>Sources</h2>'+sourcecards(j['sources'],'../')+'</section><p><a href="index.html">← All projects</a></p>'
        writepage('projects/'+j['id']+'.html',j['name'],'Project profile / Separate from operating supply',j['location'],body,'Projects')
        cards+=f'<a class="project-row" href="{j["id"]}.html"><small>{E(j["location"])}</small><h2>{E(j["name"])}</h2><p>{E(plain(j["status"]))}</p><span>Read project profile ↗</span></a>'
    cards+='<section><h2>Expansions within existing groups</h2>'+para('Baowu’s Chaohu, Wutai and associate Baomei expansions are addressed in its producer profile. They are not added again as independent companies or fully utilized operating capacity. [S03]')+'<a href="../producers/baowu.html">Read Baowu profile ↗</a></section>'
    writepage('projects/index.html','Proposed & developing projects',f'{len(J)} project profiles / No contribution assumed','A pilot ingot, mineral licence, offtake agreement or magnesium-oxide campaign does not establish annual commercial magnesium-metal production.',cards,'Projects')

def create_sources():
    content='<p class="download-line"><a href="data/sources.csv" download>Download source register (CSV) ↓</a></p>'
    for s in S.values():
        used=[f'<a href="producers/{p["id"]}.html">{E(p["name"])}</a>' for p in P if s['id'] in p['sources']]+[f'<a href="projects/{j["id"]}.html">{E(j["name"])}</a>' for j in J if s['id'] in j['sources']]
        if '['+s['id']+']' in json.dumps(QUALITY_TRADE):
            used.append('<a href="quality-trade.html">Purity requirements &amp; commodity flows</a>')
        if '['+s['id']+']' in json.dumps(PROCESSES):
            used.append('<a href="processes.html">Production processes</a>')
        if '['+s['id']+']' in json.dumps(US_DEVELOPMENT):
            used.append('<a href="us-development.html">U.S. electrochemical development case</a>')
        if any(s['id'] in c['source_ids'] for c in CHARTS):
            used.append('<a href="charts.html">Slide-ready charts</a>')
        content+=f'<section class="source-entry" id="{s["id"]}"><span class="source-id">{s["id"]}</span><div><h2><a href="{E(s["url"],quote=True)}">{E(s["title"])}</a></h2><p class="small">{E(s["publisher"])} · {E(s["date"])} · Accessed {s["accessed"]}</p><p><strong>Where to look:</strong> {E(s["locator"])}</p><p><strong>Supports:</strong> {E(s["supports"])}</p>'
        if s['limitation']: content+=f'<p class="limitation"><strong>Limit:</strong> {E(s["limitation"])}</p>'
        content+='<p class="small">Used in: '+(', '.join(used) if used else 'Overview / methods / national comparison')+'</p></div></section>'
    writepage('sources.html','Source catalog',f'{len(S)} references / Accessible provenance','Company filings, government statistics and technical records, supplemented by dated industry reporting. Each entry records its evidence boundary and access limitations.',content,'Sources')

def create_home():
    intro='A producer-led guide to magnesium metal: who makes it, what goes in, how much comes out, and where it goes.'
    top='<div class="overview-grid"><section class="opening"><p class="opening-text">Primary supply is concentrated in China.<br>Company-level output is much less transparent.</p>'+para('USGS’s 2025 estimate puts China at about 86% of world primary output. Public disclosures are not sufficient to rank today’s individual producers reliably. [S01]')+'<a class="button" href="producers/index.html">Explore producers ↗</a><a class="text-link" href="report.html">Read the report</a></section><aside class="stat-panel"><p class="eyebrow">2025 / USGS estimates</p><div class="stat"><strong>1.1m <small>t</small></strong><span>World primary magnesium</span></div><div class="stat"><strong>950k <small>t</small></strong><span>China primary magnesium</span></div><p>Metric tonnes. Rounded estimates.<br>Capacity and recycled metal excluded. <a class="cite" href="'+S['S01']['url']+'">S01</a></p></aside></div>'
    body=top+'<section><div class="section-heading"><h2>Five questions, one supply chain</h2><a href="methods.html">How to read the evidence ↗</a></div><div class="question-list">'
    for i,(title,text) in enumerate(SUMMARY,1):
        body+=f'<div class="question"><span class="number">0{i}</span><h3>{E(title)}</h3>{para(text)}</div>'
    body+='</div></section><section class="route-section"><h2>Three distinct material pathways</h2><div class="routes">'
    for tag,title,steps in [('01','Thermal primary','Dolomite → heated oxide feed + silicon-bearing material → magnesium → ingot / alloy'),('02','Electrolytic primary','Brine / carnallite → prepared dry chloride → electricity separates metal → ingot / internal use'),('03','Recycling & conversion','Metal scrap + purchased metal → remelting / alloying → reusable alloy / components')]:
        body+=f'<div><span>{tag}</span><h3>{title}</h3><p>{steps}</p></div>'
    body+='</div>'+para('Illustrative route families; each profile states what is confirmed at its facility. [S13] [S21] [S33] [S45]','small')+'<a class="button" href="processes.html">Follow the production process in detail ↗</a></section>'
    body+='<section><div class="section-heading"><h2>Read across producers</h2><a href="downloads.html">All downloads ↗</a></div><div class="comparison-links">'
    for url,title,desc in [('feedstocks','Feedstocks & routes','Mine, brine or scrap stream; captive versus purchased inputs.'),('output','Output & capacity','Actuals, reporting years and incompatible volume bases.'),('markets','Buyers & applications','Named relationships, internal consumers and supported sectors.')]:
        body+=f'<a href="compare/{url}.html"><h3>{title} ↗</h3><p>{desc}</p></a>'
    body+='</div></section><section><h2>From specification to sale</h2>'+para(QUALITY_TRADE['lead'])+'<a class="button" href="quality-trade.html">Explore purity &amp; commodity flows ↗</a></section><section><h2>What changed in the supply picture</h2><div class="updates">'
    for title,text,url in [('Hami suspension','REMT arranged temporary suspension during environmental upgrades in August 2026. [S16]','producers/remt.html'),('Qinghai metal trials','A one-cell trial produced metal in 2025; whole-site annual commercial output remains unresolved. Magontec exited its alloy operation. [S80] [S81] [S45]','producers/qinghai.html'),('Huiye liquidation','An April 2026 court notice confirms consolidated bankruptcy liquidation. Successor plant operation remains unverified. [S78]','producers/huiye.html')]:
        body+=f'<article><h3><a href="{url}">{title} ↗</a></h3>{para(text)}</article>'
    body+='</div></section>'
    body+='<section><h2>A case for domestic U.S. production</h2>'+para(US_DEVELOPMENT['lead'])+'<a class="button" href="us-development.html">Explore the electrochemical development case ↗</a><a class="text-link" href="charts.html">Slide-ready charts ↗</a></section>'
    writepage('index.html','Magnesium, from feedstock to market','Global producers / Research cutoff 27 September 2026',intro,body,'Overview')

def create_methods():
    body='<p><a href="review.md">Read the accuracy, freshness and readability review log (27 September 2026) ↗</a></p>'
    body+=''.join(f'<section><h2>{title}</h2>{para(text)}</section>' for title,text in METHODS)
    body+='<section><h2>Initial producer and source-coverage assessment</h2>'+table(['Producer set','Reason for inclusion','Source coverage','Interpretation'],[[rich(c) for c in r] for r in COVERAGE])+'</section>'
    writepage('methods.html','Scope, sources & limitations','Research methods','The unit of comparison matters as much as the number. These rules keep virgin metal, recycling, alloys and mineral compounds separate.',body)

def topic_content(topic,markdown=False):
    content=[]
    for s in topic['sections']:
        content.append(f'### {s["title"]}\n\n' if markdown else f'<section id="{s["id"]}"><h2>{E(s["title"])}</h2>')
        content.extend(md(p)+'\n\n' if markdown else para(p) for p in s['paragraphs'])
        if s.get('steps'):
            if not markdown: content.append('<ol class="process-steps">')
            for i,(title,description) in enumerate(s['steps'],1):
                content.append(f'{i}. **{title}.** {md(description)}\n\n' if markdown else f'<li><h3>{E(title)}</h3>{para(description)}</li>')
            if not markdown: content.append('</ol>')
        if s.get('paths'):
            if not markdown: content.append('<div class="routes">')
            for i,(title,path) in enumerate(s['paths'],1):
                content.append(f'**{title}:** {md(path)}\n\n' if markdown else f'<div><span>0{i}</span><h3>{E(title)}</h3>{para(path)}</div>')
            if not markdown: content.append('</div>')
        if 'table' in s:
            t=s['table']
            content.append(mdtable(t['headers'],t['rows']) if markdown else table(t['headers'],[[rich(c) for c in row] for row in t['rows']],s['title']))
            content.append(f'[Download table](data/{t["csv"]})\n\n' if markdown else f'<p class="download-line"><a href="data/{t["csv"]}" download>Download table (CSV) ↓</a></p>')
        content.extend(md(p)+'\n\n' if markdown else para(p) for p in s.get('after',[]))
        if not markdown: content.append('</section>')
    return ''.join(content)

def create_topic(path,topic,label):
    toc='<aside class="toc"><strong>In this section</strong>'+''.join(f'<a href="#{s["id"]}">{E(s["title"])}</a>' for s in topic['sections'])+'</aside>'
    body=f'<div class="article-layout">{toc}<article>{topic_content(topic)}</article></div>'
    if path=='us-development.html':
        body='<p class="download-line"><a href="charts.html">Six slide-ready charts ↗</a> <a href="magnesium-slide-charts.zip" download>Download chart pack ↓</a></p>'+body
    writepage(path,topic['title'],label+' / Magnesium metal',topic['lead'],body,label)

def create_charts():
    body='<p class="download-line"><a href="magnesium-slide-charts.zip" download>Download all charts and data (ZIP) ↓</a> <a href="figures/v1/magnesium-slide-charts.pdf">Six-page slide PDF ↗</a> <a href="figures/v1/MANIFEST.md">Version and methods</a></p>'
    body+='<p>Use PNG for easy insertion into a slideshow, or SVG for scalable vector artwork. Each image is 16:9 (3840 × 2160 px) with its reporting period and source note. Keep those notes visible when presenting. Five charts use USGS statistics; the electricity chart uses explicitly assumed scenarios.</p>'
    body+='<nav class="tabs" aria-label="Chart selection">'+''.join(f'<a href="#{c["id"]}">{i:02d}</a>' for i,c in enumerate(CHARTS,1))+'</nav>'
    for i,c in enumerate(CHARTS,1):
        base=f'{FIGURE_DIR.as_posix()}/{c["id"]}'
        body+=f'<section id="{c["id"]}" class="chart-card"><p class="eyebrow">{i:02d} / '+('Illustrative scenario' if c['analysis'] else 'Source-based statistics')+f'</p><h2>{E(c["title"])}</h2>'
        body+=f'<figure><a href="{base}.png" aria-label="Open chart {i} at full resolution"><img src="{base}.png" alt="{E(c["alt"],quote=True)}" width="3840" height="2160" loading="lazy"></a><figcaption>{E(c["caption"])}</figcaption></figure>'
        body+='<p class="download-line">'+''.join(f'<a href="{base}.{ext}" download>{label} ↓</a>' for ext,label in [('png','PNG image'),('svg','SVG vector'),('csv','Plotted data CSV')])+'</p>'
        body+=para('Source: '+' '.join('['+s+']' for s in c['source_ids']),'small') if c['source_ids'] else '<p class="small">Analyst calculation: kWh/kg × US$/MWh ÷ 1,000 = US$/kg electricity cost. Inputs are assumptions, not measured plant values.</p>'
        body+='</section>'
    writepage('charts.html','Charts for your slideshow','Six figures / 16:9 / Version 1','A visual argument for domestic magnesium development: supply, markets, recycling and the electricity-cost question.',body,'Charts')
    with zipfile.ZipFile(ROOT/'magnesium-slide-charts.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted((ROOT/'figures').rglob('*')):
            if file.is_file(): archive.write(file,file.relative_to(ROOT))

def export_csv(name,fields,rows):
    # CSVs are plain machine-readable data exports, not formatted workbooks.
    with (ROOT/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(fields); w.writerows(rows)

def create_data():
    urls=lambda refs:' ; '.join(S[x]['url'] for x in refs)
    export_csv('sources.csv',list(next(iter(S.values())).keys()),[[s[k] for k in next(iter(S.values())).keys()] for s in S.values()])
    export_csv('producers.csv',['producer_id','producer','country','category','status_at_cutoff','facilities','ownership','products','source_ids','source_urls'],[[p['id'],p['name'],p['country'],p['category'],p['status'],p['facility'],plain(p['ownership']),p['products'],' '.join(p['sources']),urls(p['sources'])] for p in P])
    export_csv('feedstocks.csv',['producer_id','producer','facility','raw_feedstock','source_and_purchase_boundary','prepared_feed_and_route','grade_and_analytical_basis','consumption_ratio_and_boundary','supply_constraints','source_ids','source_urls'],[[p['id'],p['name'],p['facility']]+[plain(p[k]) for k in ['feedstock','origin','route','grade','ratio','constraints']]+[' '.join(p['sources']),urls(p['sources'])] for p in P])
    export_csv('output.csv',['producer_id','producer','reported_quantity_t_and_basis','reporting_period','capacity_t_per_y_and_basis','products','output_notes','source_ids','source_urls'],[[p['id'],p['name'],BRIEF[p['id']][2],BRIEF[p['id']][3],BRIEF[p['id']][4],p['products'],plain(p['output_note']),' '.join(p['sources']),urls(p['sources'])] for p in P])
    export_csv('markets.csv',['producer_id','producer','documented_buyer_or_partner','intermediate_product','final_application','relationship_basis','source_ids','source_urls'],[[p['id'],p['name']]+[plain(p[k]) for k in ['buyers','intermediate','applications','relationship']]+[' '.join(p['sources']),urls(p['sources'])] for p in P])
    export_csv('quantities.csv',list(D['quantities'][0])+['source_url'],[[q[k] for k in D['quantities'][0]]+[S[q['source_id']]['url']] for q in D['quantities']])
    export_csv('countries.csv',list(COUNTRY[0])+['basis_note','source_url'],[[c[k] for k in COUNTRY[0]]+['USGS primary series; 2025 estimated; zero represents source dash; basis columns distinguish reported from estimated; world rounded',S['S01']['url']] for c in COUNTRY])
    export_csv('projects.csv',['project_id','project','location','status','feedstock','route','capacity_or_output_with_units','future_markets','gaps','source_ids','source_urls'],[[j['id'],j['name'],j['location']]+[plain(j[k]) for k in ['status','feedstock','route','volume','markets','gaps']]+[' '.join(j['sources']),urls(j['sources'])] for j in J])
    for section in QUALITY_TRADE['sections']+PROCESSES['sections']+US_DEVELOPMENT['sections']:
        if 'table' not in section: continue
        t=section['table']; rows=[]
        for row in t['rows']:
            refs=sorted(set(re.findall(r'\[(S\d+)\]', ' '.join(row))))
            rows.append([plain(c) for c in row]+[' '.join(refs),urls(refs)])
        export_csv(t['csv'],t['headers']+['source_ids','source_urls'],rows)
    definitions='''# Data dictionary

Research cutoff: 2026-09-27. CSV encoding: UTF-8 with BOM. Delimiter: comma. Quoted cells may contain commas; use a CSV parser.

- `research.json`: canonical full research text, profiles, projects, national figures, numeric observations and source register. `[Snn]` tokens refer to source IDs.
- `producers.csv`: company/facility directory and classification; one row per profile, sometimes a consolidated group, never automatically additive.
- `feedstocks.csv`: raw inputs, origin/purchasing, preparation/route, grade basis, ratios and constraints.
- `output.csv`: human-readable comparison preserving quantities, periods and incompatible capacity bases. Numeric-looking text is intentionally qualified.
- `quantities.csv`: numeric observations only. `value_t` is metric tonnes, or the lower value of a reported range; `value_max_t` is its upper value. Empty upper bounds mean not a range. `period` is text because annual, half-year and unallocated two-year ranges coexist. `metric` and `note` must be used before comparing or aggregating. No all-producer total is valid.
- `countries.csv`: one USGS statistical series, converted from thousand metric tonnes to tonnes. 2025 values are estimates, not producer actuals. Capacity uses t/y and may include idle plants. World total is rounded; do not add it to country rows. Source dashes are coded 0 (zero in source), not missing company observations.
- `markets.csv`: buyer evidence with intermediate and final uses; future and historical relationships explicitly labeled.
- `projects.csv`: proposed/demonstration/stalled projects, excluded from current commercial primary supply.
- `sources.csv`: ID, title, publisher, publication/reporting date, URL, locator, supported claims, limitations and access date. An undated source remains undated.
- `purity-specifications.csv`: selected supplier/benchmark product specifications; composition in percent as published, not batch assays or a complete standard.
- `application-requirements.csv`: acceptance considerations by use; public evidence versus undisclosed buyer limits.
- `commodity-flows.csv`: qualitative material and commercial routes, with documented examples; no shipment tonnage assigned.
- `trade-context.csv`: regional shares with their original periods and product boundaries; not a common-year global flow balance.
- `price-benchmarks.csv`: grade, location, delivery, lot and currency/unit definitions; no current price observations.
- `trade-codes.csv`: six-digit HS category guide; national legal subdivisions require separate checking.
- `facility-processes.csv`: documented preparation, extraction and finishing at named facilities; evidence dates and limits remain explicit.
- `process-input-boundaries.csv`: historical reference inputs, prepared-charge recipe and chloride-stage recovery on incompatible bases; not current plant consumption estimates.
- `us-supply-case.csv`: U.S. supply indicators, periods and incompatible material boundaries; analysis alongside cited statistics.
- `us-trade.csv`: revised 2025 and first-half 2026 imports from USGS Q2 2026, preserving category-specific weight bases; not a primary-ingot market size.
- `us-route-options.csv`: chloride electrolysis, oxide electrolysis and an alternative thermal route; commercial precedents versus research/development.
- `us-development-criteria.csv`: proposed engineering evidence requirements, with units and supporting context; not observed performance or published pass/fail thresholds.

The six quality/trade exports use descriptive column headers, including units, plus source IDs and URLs. Their source text lives under `quality_trade` in `research.json`. Percentage limits, ranges and inequalities remain text to preserve their meaning. Empty or undisclosed limits are not zero.

The two process exports follow the same convention and live under `processes`. The historical DLR 2013 case is separate from current producer data. RIMA's recipe uses the explicit stage-i statement and flags the conflicting stage-iv wording.

The four U.S. development exports live under `us_development`. Recommendations are analyst synthesis, distinct from source observations. The illustrative electricity calculation uses assumed inputs, not a plant estimate or current tariff. The Big Blue project retains the company's undefined “tons/year” label; it is not converted into the metric numeric-observation table.

Unknown company annual quantities are omitted from `quantities.csv`, and explained in `output.csv`; absence does not mean zero. Values are not normalized to elemental magnesium unless the original source uses that basis. Grades retain Mg, MgO, MgCl2, alloy or product basis. No confidential number is inferred from plant capacity.
'''
    (ROOT/'data/README.md').write_text(definitions)
    files=[('report.md','Full report','Markdown report with all profiles, comparisons and citations'),('report.html','Read report in browser','Single-page version for reading or browser printing'),('data/producers.csv','Producer directory','Company, facilities, category and status'),('data/feedstocks.csv','Feedstock table','Provenance, assays, preparation and consumption boundaries'),('data/output.csv','Output comparison','Reported quantities, years, capacity and products'),('data/quantities.csv','Numeric observations','Amounts with explicit metric, period and source'),('data/countries.csv','Country series','USGS primary output and capacity'),('data/markets.csv','Markets table','Buyers, intermediate products and applications'),('data/projects.csv','Project register','Development status and future relationships'),('data/sources.csv','Source register','All references with access notes and claim locators'),('data/research.json','Complete structured dataset','Full profile text and research records'),('data/README.md','Data dictionary','Definitions, units and aggregation rules')]
    files.insert(2,('review.md','Review log','Corrections, newer documents checked and remaining access gaps'))
    files.insert(2,('charts.html','Slide-ready charts','Six 16:9 charts, PNG and SVG images, plotted data and a slide PDF'))
    files.insert(3,('magnesium-slide-charts.zip','Download chart pack','All six charts, underlying data and source notes'))
    files[3:3]=[('data/'+s['table']['csv'],s['title'],'Purity and trade reference table with source links') for s in QUALITY_TRADE['sections'] if 'table' in s]
    files[3:3]=[('data/'+s['table']['csv'],s['title'],'Production-process reference table with source links') for s in PROCESSES['sections'] if 'table' in s]
    files[3:3]=[('data/'+s['table']['csv'],s['title'],'U.S. development evidence and analysis with source links') for s in US_DEVELOPMENT['sections'] if 'table' in s]
    body='<div class="downloads">'+''.join(f'<a href="{f}"'+(' download' if not f.endswith('.html') else '')+f'><h2>{t} <span>↓</span></h2><p>{d}</p><small>{f}</small></a>' for f,t,d in files)+'</div>'
    writepage('downloads.html','Report & data downloads','Reusable research / Open files','Download the report and source-linked tables. Read the data dictionary before combining quantities with different reporting boundaries.',body)

def create_report():
    report=['# Global magnesium metal producers\n\nResearch cutoff: **27 September 2026**. Tonnages are metric unless an explicitly labeled source uses an undefined “tons” basis.\n\nRead the [accuracy, freshness and readability review log](review.md), or browse the [slide-ready charts](charts.html) with [versioned data and methods](figures/v1/MANIFEST.md).\n\n']
    report+=['## Contents\n\n- [Overview](#overview)\n- [Leading producers and source coverage](#leading-producers-and-source-coverage)\n- [Country context](#country-context)\n- [How magnesium metal is produced](#how-magnesium-metal-is-produced)\n- [Purity requirements and commodity flows](#purity-requirements-and-commodity-flows)\n- [A U.S. case for electrochemical magnesium](#a-us-case-for-electrochemical-magnesium)\n- [Comparisons](#comparisons)\n- [Producer profiles](#producer-profiles)\n- [Proposed and developing projects](#proposed-and-developing-projects)\n- [Methods and gaps](#methods-and-gaps)\n- [Source register](#source-register)\n\n']
    report+=['## Overview\n\n']+[f'### {t}\n\n{md(v)}\n\n' for t,v in SUMMARY]
    report+=['## Leading producers and source coverage\n\nThe initial screening prioritized major commercial primary suppliers and the source quality needed to answer the five questions. Recent annual company output is the weakest common field. Inclusion below is not a current ranking.\n\n',mdtable(['Producer set','Reason for inclusion','Source coverage','Interpretation'],COVERAGE)]
    report+=['## Country context\n\nUSGS MCS 2026 primary-magnesium series. The 2025 column is estimated; 2024 remains a national statistical figure rather than a company account. Capacity can include idle plants. [S01]\n\n',mdtable(['Country','2024 production, mostly estimates (t)','2025 production, estimate (t)','2025 capacity, mixed basis (t/y)'],[[c['country']]+['—' if c[k]==0 else f'{c[k]:,.0f}' for k in ['output_2024_t','output_2025_estimate_t','capacity_2025_t_per_y']] for c in COUNTRY])]
    report+=['— means zero in the source. The 2024 China and Israel entries are reported; other nonzero 2024 production is estimated. Capacity for the US, Israel and Türkiye is reported; other capacity is estimated. World totals are rounded. China’s share is about 86% on this one USGS basis. Baowu cites CNIA’s higher final 2025 China primary figure of 1,093,500 t (+6.6%) and alloy output of 428,400 t (+8.0%). These cannot be spliced into the USGS world series. Fugu’s separately reported 557,700 t primary output and 802,500 t/y capacity are regional totals overlapping its individual firms. [S01] [S02] [S53]\n\n']
    report+=['## How magnesium metal is produced\n\n'+md(PROCESSES['lead'])+'\n\n',topic_content(PROCESSES,markdown=True)]
    report+=['## Purity requirements and commodity flows\n\n'+md(QUALITY_TRADE['lead'])+'\n\n',topic_content(QUALITY_TRADE,markdown=True)]
    report+=['## A U.S. case for electrochemical magnesium\n\n'+md(US_DEVELOPMENT['lead'])+'\n\n',topic_content(US_DEVELOPMENT,markdown=True)]
    report+=['## Comparisons\n\nThese tables preserve incompatible bases. Follow the profile for actual-versus-capacity qualifications and status. No producer total is computed.\n\n']
    report+=['### General industry applications\n\nContext only; not company-specific sales allocations or customer identifications.\n\n',mdtable(['Market','Intermediate chain','Final application / evidence'],GENERAL_MARKETS)]
    for kind,title,headers in [('feedstocks','Feedstock, origin and route',['Producer / facility','Feedstock and source','Route']),('output','Actuals and capacity',['Producer','Reported quantity (t)','Period / basis','Capacity (t/y)','Products']),('markets','Buyers and applications',['Producer','Buyer / partner','Intermediate','Application / relationship'])]:
        report+=[f'### {title}\n\n']
        for group,ids in GROUPS:
            report += [f'#### {group}\n\n']
            rows=[]
            for id in ids:
                p=BY_ID[id]; b=BRIEF[id]; refs=' '.join('['+s+']' for s in p['sources'])
                if kind=='feedstocks':rows.append([p['name']+' — '+p['facility'],b[0],b[1]+' '+refs])
                elif kind=='output':rows.append([p['name'],b[2],b[3]+' '+refs,b[4],p['products']])
                else:rows.append([p['name'],p['buyers'],p['intermediate'],p['applications']+' '+p['relationship']])
            report+=[mdtable(headers,rows)]
    report+=['## Producer profiles\n\n']
    reporthtml='<p><a href="charts.html">Browse six slide-ready charts</a> · <a href="figures/v1/magnesium-slide-charts.pdf">Read the chart PDF</a></p><nav class="tabs" aria-label="Report contents"><a href="#overview">Overview</a><a href="#coverage">Coverage</a><a href="#production-processes">Processes</a><a href="#quality-trade">Quality &amp; trade</a><a href="#us-development">U.S. case</a><a href="#profiles">Profiles</a><a href="#projects">Projects</a><a href="#methods">Methods</a><a href="sources.html">Source catalog</a></nav>'
    reporthtml+='<section id="overview"><h2>Overview</h2>'+''.join('<h3>'+t+'</h3>'+para(v) for t,v in SUMMARY)+'</section><section id="coverage"><h2>Leading producers and source coverage</h2>'+table(['Producer set','Reason for inclusion','Coverage','Interpretation'],[[rich(v) for v in r] for r in COVERAGE])+'</section><section><h2>Country context</h2>'+countrytable()+para('Sources and definitions: [S01]. Alternative Chinese series and country estimates are discussed under methods.')+'</section><section><h2>Producer comparisons</h2><p><a href="compare/feedstocks.html">Feedstocks and routes</a> · <a href="compare/output.html">Output and capacity</a> · <a href="compare/markets.html">Buyers and applications</a></p></section><section id="production-processes"><h2>How magnesium metal is produced</h2>'+topic_content(PROCESSES)+'</section><section id="quality-trade"><h2>Purity requirements &amp; commodity flows</h2>'+topic_content(QUALITY_TRADE)+'</section><section id="us-development"><h2>A U.S. case for electrochemical magnesium</h2>'+para(US_DEVELOPMENT['lead'])+topic_content(US_DEVELOPMENT)+'</section><section id="profiles"><h2>Producer profiles</h2></section>'
    for group,ids in GROUPS:
        report+=[f'### {group}\n\n']
        for id in ids:
            p=BY_ID[id]
            report+=[f'### {p["name"]}\n\n**Country:** {p["country"]}. **Category:** {p["category"]}.\n\n**Facilities:** {p["facility"]}.\n\n**Status:** {p["status"]}.\n\n']
            reporthtml+=f'<article class="report-profile"><p class="eyebrow">{E(p["country"])} / {E(p["category"])}</p><h2>{E(p["name"])}</h2>{para(p["facility"])}{para(p["status"])}'+profilebody(p,True)+'</article>'
            for _,title,fields in PROFILE_SECTIONS:
                report+=[f'#### {title}\n\n']
                report += [f'**{label}.** {md(p[k])}\n\n' for label,k in fields]
    report+=['## Proposed and developing projects\n\nExcluded from established commercial primary output. Capacity targets are not realized production.\n\n']
    reporthtml+='<section id="projects"><h2>Proposed and developing projects</h2></section>'
    for j in J:
        report+=[f'### {j["name"]}\n\n**Location:** {j["location"]}.\n\n']
        reporthtml+=f'<article class="report-profile"><h2>{E(j["name"])}</h2>{para(j["location"])}'
        for k,title in [('status','Status'),('feedstock','Feedstock'),('route','Route'),('volume','Production and capacity'),('markets','Buyers and future agreements'),('gaps','Gaps')]:
            report+=[f'**{title}.** {md(j[k])}\n\n']
            reporthtml+='<h3>'+title+'</h3>'+para(j[k])
        reporthtml+='</article>'
    report+=['## Methods and gaps\n\n']+[f'### {t}\n\n{md(v)}\n\n' for t,v in METHODS]
    reporthtml+='<section id="methods"><h2>Methods and gaps</h2>'+''.join('<h3>'+t+'</h3>'+para(v) for t,v in METHODS)+f'</section><section><h2>Complete source register</h2><p><a href="sources.html">Read all {len(S)} source entries and access notes</a> · <a href="data/sources.csv" download>Download register CSV</a></p></section>'
    report+=['## Source register\n\nAll sources accessed 27 September 2026. Locators are document sections or printed page references where available. A reference may be a company filing hosted by a mirror; that limitation is explicit.\n\n']
    for s in S.values():
        report += [f'### {s["id"]} — {s["title"]}\n\n{s["publisher"]}; {s["date"]}. [Open source]({s["url"]}).\n\n**Locator:** {s["locator"]}. **Supports:** {s["supports"]}.\n\n'+(f'**Limit:** {s["limitation"]}\n\n' if s['limitation'] else '')]
    report+=['## Downloadable data\n\nSee [data dictionary](data/README.md), [producer directory](data/producers.csv), [feedstocks](data/feedstocks.csv), [output comparison](data/output.csv), [numeric observations](data/quantities.csv), [markets](data/markets.csv), [country series](data/countries.csv), [projects](data/projects.csv), [process guide and tables](processes.html), [purity and trade tables](quality-trade.html), [U.S. development case and tables](us-development.html), [slide-ready charts](charts.html), and [source register](data/sources.csv).\n']
    # Resolve overview tokens; already-linked citations are left unchanged.
    (ROOT/'report.md').write_text(md(''.join(report)))
    writepage('report.html','Global magnesium metal producers','Full report / 27 September 2026','A source-linked review of producers, feedstock provenance, production volumes and markets. Download the Markdown report for the complete tables and source register.',reporthtml)

def main():
    create_profiles(); create_directory(); create_comparisons(); create_projects()
    create_sources(); create_home(); create_methods()
    create_topic('quality-trade.html',QUALITY_TRADE,'Quality & trade')
    create_topic('processes.html',PROCESSES,'Processes')
    create_topic('us-development.html',US_DEVELOPMENT,'U.S. case')
    create_charts(); create_data(); create_report()
    (ROOT/'.nojekyll').touch()
    (ROOT/'data/site-manifest.json').write_text(json.dumps(GENERATED,indent=2)+'\n')
    with zipfile.ZipFile(ROOT/'magnesium-atlas.zip','w',zipfile.ZIP_DEFLATED) as archive:
        files=[ROOT/p for p in GENERATED]+list((ROOT/'data').glob('*'))+list((ROOT/'assets').glob('*'))
        files += list((ROOT/'figures').rglob('*'))
        files += [ROOT/p for p in ['report.md','review.md','README.md','build.py','check.py','make_figures.py','magnesium-slide-charts.zip','.nojekyll']]
        for file in files:
            if file.is_file(): archive.write(file,file.relative_to(ROOT))
    print(f'Built {len(GENERATED)} HTML pages, report.md and {len(list((ROOT/"data").glob("*.csv")))} CSV data tables.')

if __name__=='__main__': main()
