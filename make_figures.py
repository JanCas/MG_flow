#!/usr/bin/env python3
"""Render the six slide charts. Choose a new output version when inputs/layout change."""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String, Rect, Line, Circle
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'data/research.json').read_text())
SOURCE=next(s for s in DATA['sources'] if s['id']=='S01')
W,H=960,540
INK='#20313D'; MUTED='#586872'; TEAL='#087E83'; ORANGE='#C96B33'; GRAY='#DDE5E8'; BLUE='#4C68A8'
CHARTS=[]; DRAWINGS=[]

def text(d,x,y,value,size=16,color=INK,bold=False,anchor='start'):
    font='Helvetica-Bold' if bold else 'Helvetica'
    # Catch accidental margin overflow before producing slide images.
    width=stringWidth(value,font,size)
    left=x if anchor=='start' else x-width if anchor=='end' else x-width/2
    assert left>=0 and left+width<=W, (value,left,width)
    d.add(String(x,y,value,fontName=font,fontSize=size,fillColor=HexColor(color),textAnchor=anchor))

def line(d,x1,y1,x2,y2,color=GRAY,width=1):
    d.add(Line(x1,y1,x2,y2,strokeColor=HexColor(color),strokeWidth=width))

def base(number,title,subtitle,notes,source_note='Source: USGS, Mineral Commodity Summaries 2026 (S01).'):
    d=Drawing(W,H)
    d.add(Rect(0,0,W,H,fillColor=HexColor('#FFFFFF'),strokeColor=None))
    d.add(Rect(54,487,34,4,fillColor=HexColor(ORANGE),strokeColor=None))
    text(d,101,484,'MAGNESIUM ATLAS  /  U.S. DEVELOPMENT CASE',10,MUTED,bold=True)
    text(d,906,484,f'{number:02d} / 06',10,MUTED,anchor='end')
    for i,t in enumerate(title.split('\n')): text(d,54,450-i*33,t,28,bold=True)
    text(d,54,401 if '\n' not in title else 373,subtitle,14,MUTED)
    for i,n in enumerate(notes): text(d,54,88-i*17,n,11.5,MUTED)
    line(d,54,46,906,46)
    text(d,54,27,source_note,10,MUTED)
    text(d,906,27,'Research cutoff: 27 Sep 2026',10,MUTED,anchor='end')
    return d

def record(slug,title,alt,caption,headers,rows,source_ids=('S01',),analysis=False):
    CHARTS.append(dict(id=slug,title=title,alt=alt,caption=caption,source_ids=list(source_ids),analysis=analysis,
                       csv_headers=headers,csv_rows=rows))

def stack(d,values,labels,colors,y=240,height=80):
    left=54; total=sum(values); full=852
    for value,label,color in zip(values,labels,colors):
        width=full*value/total
        d.add(Rect(left,y,width,height,fillColor=HexColor(color),strokeColor=None))
        text(d,left+width/2,y+height/2-9,label,24,'#FFFFFF' if color!=GRAY else INK,bold=True,anchor='middle')
        left+=width

def bars(d,labels,values,colors,ys,x=260,width=570,max_value=100,suffix='%'):
    for label,value,color,y in zip(labels,values,colors,ys):
        text(d,x-20,y+5,label,17,anchor='end')
        d.add(Rect(x,y-4,width*value/max_value,28,fillColor=HexColor(color),strokeColor=None))
        text(d,x+width*value/max_value+12,y+5,f'{value:g}{suffix}',18,bold=True)
    line(d,x,min(ys)-12,x,max(ys)+34)


def make():
    countries={c['country']:c for c in DATA['countries']}
    world=countries['World (rounded)']['output_2025_estimate_t']
    china=countries['China']['output_2025_estimate_t']; rest=world-china
    share=100*china/world
    d=base(1,'China supplies about 86% of primary magnesium','World primary metal production, 2025 estimates',
           ['Other countries = rounded world total minus China; not a sum of country estimates.',
            'Primary metal only. Recycling, compounds and nameplate capacity are excluded.'])
    text(d,54,343,'Share of world primary production',14,MUTED)
    stack(d,[china,rest],[f'China  {share:.0f}%',f'{100-share:.0f}%'],[TEAL,GRAY])
    for x,value,label in [(54,'1.1 million t','World total'),(370,'950,000 t','China'),(675,'~150,000 t','Other countries, derived')]:
        text(d,x,172,value,25,bold=True);text(d,x,146,label,13,MUTED)
    record('01-global-concentration','China supplies about 86% of primary magnesium',
           'China: 950,000 metric tonnes, approximately 86% of the rounded 1.1 million tonne world total in 2025. Other countries: approximately 150,000 tonnes, derived as the residual.',
           'Use to establish global concentration. The residual outside China is calculated from the rounded world total; it is not an independently reported regional total.',
           ['category','production_t','basis','source_id','source_url'],
           [['China',china,'2025 USGS estimate','S01',SOURCE['url']],['Other countries',rest,'Derived: rounded world total minus China','S01',SOURCE['url']],['World total',world,'Rounded 2025 estimate; denominator, not an additional segment','S01',SOURCE['url']]])
    DRAWINGS.append(d)

    # Explicit transcription of the report's source-checked domestic consumption series.
    years=[2023,2024,2025]; consumption=[53000,46000,40000]; production=[0,0,0]
    assert '53,000 → 46,000 → 40,000' in json.dumps(DATA,ensure_ascii=False)
    assert countries['United States']['output_2025_estimate_t']==0
    d=base(2,'No U.S. primary output, yet 40,000 t consumed','U.S. primary magnesium: production and reported consumption, 2023-2025',
           ['2025 consumption is estimated. Reported primary consumption is not total apparent consumption.',
            'Domestic recycling is outside these series. The observed consumption trend is downward.'])
    x0,y0,chart_h=122,155,215
    for tick in [0,20,40,60]:
        y=y0+chart_h*tick/60
        line(d,x0,y,860,y)
        text(d,x0-12,y-4,str(tick),12,MUTED,anchor='end')
    text(d,x0,387,'Thousand metric tonnes',12,MUTED)
    for x,year,value in zip([270,495,720],years,consumption):
        h=chart_h*(value/1000)/60
        d.add(Rect(x-54,y0,108,h,fillColor=HexColor(TEAL),strokeColor=None))
        text(d,x,y0+h+12,f'{value/1000:g}',21,bold=True,anchor='middle')
        text(d,x,y0-25,str(year),15,anchor='middle')
    line(d,230,y0,760,y0,ORANGE,3)
    for x in [270,495,720]:
        d.add(Circle(x,y0,6,fillColor=HexColor('#FFFFFF'),strokeColor=HexColor(ORANGE),strokeWidth=3))
        text(d,x+15,y0+8,'0',13,ORANGE,bold=True)
    d.add(Rect(482,385,11,11,fillColor=HexColor(TEAL),strokeColor=None));text(d,502,385,'Consumption',12,MUTED)
    line(d,668,390,690,390,ORANGE,3);text(d,700,385,'Production',12,MUTED)
    record('02-us-production-gap','No U.S. primary output, yet 40,000 t consumed',
           'Reported U.S. primary consumption fell from 53,000 tonnes in 2023 to 46,000 in 2024 and an estimated 40,000 in 2025. U.S. primary production was zero in all three years.',
           'Use to motivate domestic supply against an existing market, without implying rising demand. Consumption is the USGS reported primary series, not a total addressable market estimate.',
           ['year','primary_production_t','reported_primary_consumption_t','consumption_basis','source_id','source_url'],
           [[y,p,c,'estimated' if y==2025 else 'reported','S01',SOURCE['url']] for y,p,c in zip(years,production,consumption)])
    DRAWINGS.append(d)

    origins=['Israel','Türkiye','Russia','China','Other']; shares=[47,31,8,6,8]
    assert sum(shares)==100
    d=base(3,'Israel and Türkiye supplied 78%\nof U.S. pure-metal imports','U.S. import origins, 2021-2024 pooled shares',
           ['USGS metal category: 99.8% purity. This is a multi-year origin mix, not a 2025 snapshot.',
            'Import origins differ from the geography of world primary production.'])
    bars(d,origins,shares,[TEAL,ORANGE,GRAY,BLUE,GRAY],[322,278,234,190,146],x=210,width=620,max_value=55)
    record('03-us-import-origins','Israel and Türkiye supplied 78% of U.S. pure-metal imports',
           '2021-2024 U.S. pure-metal import shares: Israel 47%, Türkiye 31%, Russia 8%, China 6%, other 8%.',
           'Use alongside the global concentration chart. The United States sourced directly from several countries; China’s world share is not its share of U.S. imports.',
           ['origin','share_percent','period','product_boundary','source_id','source_url'],
           [[o,v,'2021-2024','USGS magnesium metal (99.8% purity)','S01',SOURCE['url']] for o,v in zip(origins,shares)])
    DRAWINGS.append(d)

    uses=['Castings','Aluminum alloying','Iron / steel desulfurization','Other']; shares=[69,15,9,7]
    assert sum(shares)==100
    d=base(4,'Castings dominate U.S. primary magnesium use','Share of reported primary magnesium consumption, 2025 estimates',
           ['Castings are principally for the automotive industry; 69% is not an automotive-only share.',
            'Applies to primary consumption. It does not describe all recycled magnesium or named buyers.'])
    bars(d,uses,shares,[TEAL,GRAY,ORANGE,GRAY],[327,269,211,153],x=306,width=500,max_value=80)
    record('04-us-end-uses','Castings dominate U.S. primary magnesium use',
           'Estimated 2025 U.S. reported primary magnesium consumption: castings 69%, aluminum alloying 15%, iron and steel desulfurization 9%, other uses 7%.',
           'Use to identify established markets for a new producer. These national application shares are not company-specific sales allocations or customer contracts.',
           ['application','share_percent','year','basis','source_id','source_url'],
           [[a,v,2025,'Estimated share of reported primary consumption','S01',SOURCE['url']] for a,v in zip(uses,shares)])
    DRAWINGS.append(d)

    d=base(5,'Recycling does not all return as pure Mg ingot','Forms in which U.S. secondary magnesium was recovered, 2025 estimates',
           ['Shares are of recovered magnesium, not the gross weight of aluminum-alloy products.',
            'New and old scrap are included. This is recovery form, not the separate end-use mix.'])
    text(d,54,343,'Share of recovered secondary magnesium',14,MUTED)
    stack(d,[53,47],['53%','47%'],[TEAL,GRAY])
    text(d,54,198,'In aluminum-base alloys',21,bold=True)
    text(d,54,173,'Magnesium stays within an alloy stream.',13,MUTED)
    text(d,542,198,'Mg castings, ingot and other',21,bold=True)
    text(d,542,173,'A mixed group, not all pure merchant ingot.',13,MUTED)
    record('05-recycling-boundary','Recycling does not all return as pure Mg ingot',
           'In 2025, an estimated 53% of U.S. recovered secondary magnesium was in aluminum-base alloys; 47% was in magnesium-based castings, ingot and other materials.',
           'Use to explain why a large recycling total cannot simply be treated as interchangeable primary ingot. It supports a complementary role for primary production and recycling.',
           ['recovery_form','share_percent','year','basis','source_id','source_url'],
           [['Aluminum-base alloys',53,2025,'Share of recovered secondary Mg, new and old scrap','S01',SOURCE['url']],['Mg-based castings, ingot and other materials',47,2025,'Share of recovered secondary Mg, new and old scrap','S01',SOURCE['url']]])
    DRAWINGS.append(d)

    energies=[10,15,20]; prices=list(range(20,101,10)); colors=[TEAL,ORANGE,BLUE]
    d=base(6,'Electricity price and consumption both matter','Illustrative scenarios: electricity cost per kilogram of accepted magnesium',
           ['Assumed total plant electricity: 10, 15 or 20 kWh/kg; these are not measured plant results.',
            'Electricity only. Excludes direct fuel, feed, reagents, labor, capital and other costs.'],
           'Method: analyst scenarios; cost = kWh/kg x US$/MWh / 1,000.')
    chart=LinePlot();chart.x=110;chart.y=157;chart.width=610;chart.height=211
    chart.data=[[(p,e*p/1000) for p in prices] for e in energies]
    chart.xValueAxis.valueMin=20;chart.xValueAxis.valueMax=100;chart.xValueAxis.valueStep=20
    chart.yValueAxis.valueMin=0;chart.yValueAxis.valueMax=2.2;chart.yValueAxis.valueStep=.5
    for axis in [chart.xValueAxis,chart.yValueAxis]:
        axis.labels.fontName='Helvetica';axis.labels.fontSize=12;axis.labels.fillColor=HexColor(MUTED)
        axis.strokeColor=HexColor('#BAC7CD');axis.strokeWidth=.8
    chart.yValueAxis.visibleGrid=1;chart.yValueAxis.gridStrokeColor=HexColor('#E6ECEE')
    chart.yValueAxis.labelTextFormat=lambda v:f'{v:.1f}'
    for i,color in enumerate(colors):chart.lines[i].strokeColor=HexColor(color);chart.lines[i].strokeWidth=3
    d.add(chart)
    text(d,110,384,'Electricity cost (US$/kg Mg)',12,MUTED)
    text(d,415,117,'Electricity price (US$/MWh)',13,MUTED,anchor='middle')
    for e,color in zip(energies,colors):text(d,738,157+211*(e*.1)/2.2-5,f'{e} kWh/kg',16,color,bold=True)
    px=110+610*.5;py=157+211*.9/2.2
    d.add(Circle(px,py,5,fillColor=HexColor(ORANGE),strokeColor=HexColor('#FFFFFF'),strokeWidth=1.5))
    text(d,120,332,'15 kWh/kg at US$60/MWh',14,INK,bold=True)
    text(d,120,311,'= US$0.90/kg electricity cost',14,INK)
    assert abs(15*60/1000-.90)<1e-12
    record('06-electricity-sensitivity','Electricity price and consumption both matter',
           'Analyst scenarios for electricity-only cost at assumed plant consumption of 10, 15 and 20 kWh/kg and electricity prices of US$20-100/MWh. At 15 kWh/kg and US$60/MWh, electricity costs US$0.90 per kg.',
           'Use to explain the sensitivity a development program must measure. All inputs are assumptions. This is not a production-cost estimate, a current tariff quotation or a comparison of specific producers.',
           ['assumed_electricity_kwh_per_kg','assumed_price_usd_per_mwh','electricity_cost_usd_per_kg','basis'],
           [[e,p,round(e*p/1000,4),'Analyst scenario; electricity cost only'] for e in energies for p in prices],source_ids=(),analysis=True)
    DRAWINGS.append(d)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True)
    out=Path(parser.parse_args().output_dir);out.mkdir(parents=True,exist_ok=True)
    make()
    pdf=Canvas(str(out/'magnesium-slide-charts.pdf'),pagesize=(W,H))
    pdf.setTitle('Magnesium Atlas - Six slide-ready charts');pdf.setAuthor('Magnesium Atlas')
    for chart,drawing in zip(CHARTS,DRAWINGS):
        renderPDF.draw(drawing,pdf,0,0)
        if chart['source_ids']:pdf.linkURL(SOURCE['url'],(54,21,650,42),relative=0)
        pdf.showPage()
        svg=renderSVG.drawToString(drawing)
        # SVG descriptions make the standalone vector files accessible.
        start=svg.index('>',svg.index('<svg'))+1
        svg=svg[:start]+f'<title>{escape(chart["title"])}</title><desc>{escape(chart["alt"])}</desc>'+svg[start:]
        (out/(chart['id']+'.svg')).write_text(svg)
        with (out/(chart['id']+'.csv')).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(chart.pop('csv_headers'));writer.writerows(chart.pop('csv_rows'))
    pdf.save()
    subprocess.run(['pdftoppm','-scale-to','3840','-png',str(out/'magnesium-slide-charts.pdf'),str(out/'page')],check=True,capture_output=True)
    for n,chart in enumerate(CHARTS,1):
        (out/f'page-{n}.png').rename(out/(chart['id']+'.png'))
    metadata={'version':'v1','cutoff':DATA['cutoff'],'width_px':3840,'height_px':2160,
              'aspect_ratio':'16:9','generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_sha256':hashlib.sha256((ROOT/'data/research.json').read_bytes()).hexdigest(),
              'charts':CHARTS}
    (out/'charts.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    with (out/'source-register.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(SOURCE));writer.writeheader();writer.writerow(SOURCE)
    print(f'Rendered {len(CHARTS)} charts: PNG, SVG, CSV, combined PDF and provenance records.')

if __name__=='__main__':main()
