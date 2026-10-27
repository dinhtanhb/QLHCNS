"""Inventory visual roles in Edge; enforce phase 1 on Dashboard and lint authored UI.

Uses the existing synthetic-only route/account runner. Other routes are inventoried
for phase 2, not reported as having passed the Dashboard component contract.
"""
import json
from pathlib import Path
import re
import sys


def css_blocks(text, ancestors=()):
    """Yield nested declaration blocks, retaining media/selector context."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    cursor = 0
    while cursor < len(text):
        start = text.find('{', cursor)
        if start < 0:
            return
        label = text[cursor:start].strip()
        depth, end, quote = 1, start + 1, None
        while end < len(text) and depth:
            char = text[end]
            if quote:
                if char == quote and text[end - 1] != '\\':
                    quote = None
            elif char in '\"\'':
                quote = char
            elif char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            end += 1
        if depth:
            raise ValueError(f'Unclosed CSS block: {label}')
        body = text[start + 1:end - 1]
        context = (*ancestors, label)
        if label.startswith('@'):
            yield from css_blocks(body, context)
        else:
            yield context, body
        cursor = end


def literal_font_sizes(text):
    errors = []
    for context, body in css_blocks(text):
        # Frozen paper geometry is intentionally independent of screen tokens.
        if any('@media' in c and 'print' in c for c in context):
            continue
        if any(re.search(r'\.hcns-(?:paper|document-|draft-mark|signatures|appointment|decision-)', c) for c in context):
            continue
        for match in re.finditer(r'(?<![-\w])font-size\s*:\s*([^;}]+)', body):
            value = match[1].strip()
            if not value.startswith('var(') and value not in ('inherit', 'initial', 'unset'):
                errors.append({'context': ' > '.join(context), 'value': value})
    return errors


def arrow_labels(text):
    """Only rendered labels, not meaningful arrows in prose/data or comments."""
    text = re.sub(r'<!--.*?-->|{#.*?#}', '', text, flags=re.S)
    return [match[0] for match in re.finditer(
        r'<(?:a|button|summary)\b[^>]*>(?:(?!</(?:a|button|summary)>).)*?\u2192'
        r'(?:(?!</(?:a|button|summary)>).)*?</(?:a|button|summary)>', text, re.S)]


def lint_source(root):
    errors = []
    for path in sorted((root / 'src/static/css').glob('*.css')):
        if path.name in ('ui_tokens.css', 'tailwind.css', 'print_forms.css'):
            continue  # Canonical tokens, generated utilities, frozen paper stylesheet.
        for error in literal_font_sizes(path.read_text(encoding='utf-8')):
            errors.append({'file': str(path.relative_to(root)), **error})
    for directory in (root / 'src/apps', root / 'src/templates'):
        for path in sorted(directory.rglob('*.html')):
            text = path.read_text(encoding='utf-8')
            for label in arrow_labels(text):
                errors.append({'file': str(path.relative_to(root)), 'label': label})
            for style in re.findall(r'<style\b[^>]*>(.*?)</style>', text, re.S):
                for error in literal_font_sizes(style):
                    errors.append({'file': str(path.relative_to(root)), **error})
            for style in re.findall(r'\bstyle=[\"\']([^\"\']*)[\"\']', text):
                for error in literal_font_sizes('.inline {' + style + '}'):
                    errors.append({'file': str(path.relative_to(root)), **error})
    return errors


MEASURE = r"""() => {
 const violations=[], measurements={scope:document.querySelector('.home-dashboard')?'phase1':'phase2-inventory'};
 const main=document.querySelector('.ui-main');if(!main)return {violations,measurements};
 const visible=x=>x.checkVisibility()&&!x.closest('.sr-only,.hcns-paper,.hcns-editor,.home-info-body');
 const nodes=[...main.querySelectorAll('*')].filter(visible),rect=x=>x.getBoundingClientRect();
 const fail=(code,node,detail)=>violations.push({code,selector:node.id||node.className||node.tagName,detail});
 measurements.fontSizes=[...new Set(nodes.filter(x=>x.textContent.trim()).map(x=>getComputedStyle(x).fontSize))].sort();
 measurements.headings=nodes.filter(x=>/^H[123]$/.test(x.tagName)).map(x=>{const s=getComputedStyle(x);return {tag:x.tagName,text:x.textContent.trim(),size:s.fontSize,weight:s.fontWeight,line:s.lineHeight,height:rect(x).height}});
 measurements.componentFamilies=[...new Set(nodes.flatMap(x=>[...x.classList].filter(c=>/header$|link-action$|text-link$/.test(c))))];
 const root=main.querySelector('.home-dashboard');if(!root)return {violations,measurements};
 const allowedSizes=new Set([14,16,20,24,36]);
 for(const x of root.querySelectorAll('*'))if(visible(x)&&x.textContent.trim()&&!(x instanceof SVGElement)&&!allowedSizes.has(parseFloat(getComputedStyle(x).fontSize)))fail('TYPE_FAMILY',x,getComputedStyle(x).fontSize);
 const links=[...root.querySelectorAll('.ui-link-action')].filter(visible);
 measurements.links=links.map(x=>({text:x.textContent.trim(),rects:x.getClientRects().length,whiteSpace:getComputedStyle(x).whiteSpace}));
 for(const x of links)if(innerWidth>=360&&(x.getClientRects().length!==1||getComputedStyle(x).whiteSpace!=='nowrap'))fail('ACTION_LINE',x,x.textContent);
 const roles={H1:[24,600,32],H2:[20,600,28],H3:[16,600,24]};
 for(const x of root.querySelectorAll('h1,h2,h3'))if(visible(x)){
  const s=getComputedStyle(x),actual=[parseFloat(s.fontSize),Number(s.fontWeight),parseFloat(s.lineHeight)];
  if(actual.some((n,i)=>Math.abs(n-roles[x.tagName][i])>.1))fail('HEADING_ROLE',x,{actual,expected:roles[x.tagName]});
 }
 measurements.headers=[];
 for(const header of root.querySelectorAll('.ui-card-header,.ui-section-header'))if(visible(header)){
  const title=header.querySelector('h2,h3'),actions=header.querySelector(':scope > :is(.ui-header-actions,.ui-card-actions)'),r=rect(header),s=getComputedStyle(header);
  const available=header.clientWidth-parseFloat(s.paddingLeft)-parseFloat(s.paddingRight);
  measurements.headers.push({id:title?.id,height:r.height,available});
  if(title&&actions&&[...actions.querySelectorAll('a,button,summary')].some(visible)&&available>=288){const a=rect(title),b=rect(actions);if(Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)<=0)fail('HEADER_ACTION_ROW',header,{title:a.y,actions:b.y});}
 }
 measurements.headerOnlyCards=0;measurements.backgroundLayers=[];
 for(const card of root.querySelectorAll('.ui-card'))if(visible(card)){
  const header=card.querySelector(':scope > .ui-card-header'),body=card.querySelector(':scope > .ui-card-body');
  const content=body||card;
  const children=[...content.children].filter(x=>visible(x)&&!x.matches('header,h1,h2,h3,h4,h5,h6'));
  const hasContent=children.some(x=>x.textContent.trim()||x.matches('svg,canvas,img,input')||x.querySelector('svg,canvas,img,input'));
  if((header&&!body)||!hasContent){measurements.headerOnlyCards++;fail('HEADER_ONLY_CARD',card,'missing readable content');}
  if(header&&body){const background=[card,header,body].map(x=>getComputedStyle(x).backgroundColor).filter(x=>!['transparent','rgba(0, 0, 0, 0)'].includes(x));const layers=[...new Set(background)];measurements.backgroundLayers.push(layers);if(layers.length>1)fail('CARD_BACKGROUND',card,layers);}
 }
 for(const pair of root.querySelectorAll('.home-row,.home-my-work-grid')){
  if(getComputedStyle(pair).gridTemplateColumns.split(' ').length<2)continue;
  const headers=[...pair.querySelectorAll(':scope > .ui-card > .ui-card-header')].filter(visible);
  if(headers.length===2&&Math.abs(rect(headers[0]).height-rect(headers[1]).height)>1)fail('PAIRED_HEADERS',pair,headers.map(x=>rect(x).height));
 }
 const stream=root.querySelector('.home-dashboard-stream');
 if(stream&&parseFloat(getComputedStyle(stream).rowGap)<32)fail('GROUP_GAP',stream,getComputedStyle(stream).rowGap);
 for(const section of root.querySelectorAll('.ui-section')){
  if(Math.abs(parseFloat(getComputedStyle(section).rowGap)-12)>1)fail('TITLE_CONTENT_GAP',section,getComputedStyle(section).rowGap);
 }
 for(const pair of root.querySelectorAll('.home-row,.home-my-work-grid'))if(Math.abs(parseFloat(getComputedStyle(pair).columnGap)-16)>1)fail('CONTENT_GAP',pair,getComputedStyle(pair).columnGap);
 return {violations,measurements};
}"""


def main():
    root = Path(__file__).resolve().parents[1]
    errors = lint_source(root)
    if '--lint-only' in sys.argv:
        print(json.dumps({'errors': errors}, ensure_ascii=False, indent=2))
        return bool(errors)
    if errors:
        print(json.dumps(errors, ensure_ascii=False, indent=2))
        return 1
    import run_layout_alignment_audit as runner
    # Run the complete existing alignment contract in the same browser visit.
    # This keeps the full route/role matrix while avoiding a second Edge fleet.
    runner.MEASURE = "() => {const layout=(" + runner.MEASURE + ")();const visual=(" + MEASURE + ")();return {violations:[...layout.violations,...visual.violations],measurements:{...layout.measurements,...visual.measurements}}}"
    return runner.main()


if __name__ == '__main__':
    raise SystemExit(main())
