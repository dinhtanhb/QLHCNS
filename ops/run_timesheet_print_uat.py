"""Measure BCC print geometry and PDF content on an external synthetic database."""
import argparse
import calendar
from datetime import date
from decimal import Decimal
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--packages-dir', type=Path, required=True)
    parser.add_argument('--pdf-packages-dir', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8780)
    parser.add_argument('--phase', choices=('before', 'after'), required=True)
    parser.add_argument('--source-root', type=Path, help='Read-only archived source for the before query/formula probe.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = args.directory.resolve()
    if folder == root or root in folder.parents:
        parser.error('Synthetic database/media must be outside source.')
    marker = json.loads((folder / 'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:
        parser.error('Synthetic marker required.')
    source = args.source_root.resolve() if args.source_root else root
    sys.path[:0] = [str(source / 'src'), str(args.packages_dir.resolve()), str(args.pdf_packages_dir.resolve())]
    os.environ.update(DJANGO_SETTINGS_MODULE='config.settings', APP_ENV='test',
        DB_ENGINE='django.db.backends.sqlite3', SECRET_KEY=marker['secret_key'],
        M365_STORAGE_ENABLED='False', DJANGO_ALLOW_ASYNC_UNSAFE='true')
    import config.settings as cfg
    cfg.DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3', 'NAME':str(folder / 'synthetic.sqlite3')}}
    cfg.MEDIA_ROOT = folder / 'media'
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = str(folder / ('bcc-' + Path(handler['filename']).name))
    import django
    django.setup()
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from apps.security.models import User
    from apps.attendance.models import TimesheetEntry, Holiday, MonthlyAttendanceSummary, ProjectTimeAllocation
    from apps.project.models import Project
    from apps.leave.models import LeaveBalance
    from playwright.sync_api import sync_playwright
    import pdfplumber
    setup_test_environment()
    hr = User.objects.get(username='demo-hr')
    person = hr.employee
    manager = User.objects.get(username='demo-director').employee
    person.manager = manager
    person.save(update_fields=['manager'])
    project, _ = Project.objects.get_or_create(project_code='INC3B', defaults={'project_name':'Dự án Hòa nhập 3b giả lập'})
    other, _ = Project.objects.get_or_create(project_code='BCC2', defaults={'project_name':'Dự án thứ hai giả lập'})
    cases = [('single',2026,9,True), ('multiple',2026,11,True), ('empty',2026,10,True),
             ('no-project',2026,12,True), ('february',2027,2,True),
             ('no-balance',2028,2,False), ('long',2027,3,True), ('approved',2027,4,True)]
    # Seed once so before/after comparisons use exactly the same persisted data.
    fixture = folder / 'bcc-fixture.json'
    if not fixture.exists():
        for label, year, month, has_balance in cases:
            if has_balance:
                LeaveBalance.objects.get_or_create(employee=person,year=year,defaults={'allocated_days':20})
            Holiday.objects.get_or_create(holiday_date=date(year,month,1),defaults={'holiday_code':f'BCC-{year}-{month}-1','holiday_name':'Ngày lễ giả lập đầu tháng'})
            Holiday.objects.get_or_create(holiday_date=date(year,month,2),defaults={'holiday_code':f'BCC-{year}-{month}-2','holiday_name':'Ngày lễ giả lập thứ hai'})
            summary, _ = MonthlyAttendanceSummary.objects.get_or_create(employee=person,year=year,month=month)
            summary.sick_days = Decimal('1.5')
            summary.annual_leave_days = Decimal('2')
            summary.save()
            if label == 'empty':
                continue
            for day in range(1,calendar.monthrange(year,month)[1]+1):
                dt = date(year,month,day)
                if dt.weekday() >= 5 and day != 12:
                    continue
                description = 'Retreat 2026 cuối tuần' if day == 12 else 'Rà soát dữ liệu và tổng hợp công việc giả lập'
                if label == 'long' and day == 5:
                    description = ('Tổng hợp nội dung công việc dài, kiểm tra dữ liệu và phối hợp các đơn vị. ' * 5)[:490]
                TimesheetEntry.objects.get_or_create(employee=person,work_date=dt,project=None if label=='no-project' else project,
                    defaults={'task_description':description,'hours':8})
                if label == 'multiple' and dt.weekday() < 5:
                    TimesheetEntry.objects.get_or_create(employee=person,work_date=dt,project=other,defaults={'task_description':'Công việc dự án thứ hai','hours':2})
        fixture.write_text(json.dumps({'synthetic_only':True,'employee_id':person.pk}),encoding='utf-8')
    fixture_data = json.loads(fixture.read_text(encoding='utf-8'))
    if not fixture_data.get('empty_holiday_covered'):
        # Only the explicitly marked synthetic employee and seeded fixture dates.
        for _, year, month, _ in cases:
            TimesheetEntry.objects.filter(employee=person,work_date=date(year,month,2)).delete()
        fixture_data['empty_holiday_covered'] = True
        fixture.write_text(json.dumps(fixture_data),encoding='utf-8')
    if not fixture_data.get('empty_october_without_holidays'):
        Holiday.objects.filter(holiday_code__startswith='BCC-2026-10-').delete()
        fixture_data['empty_october_without_holidays'] = True
        fixture.write_text(json.dumps(fixture_data),encoding='utf-8')
    if not fixture_data.get('two_work_lines_covered'):
        for day in (3,4,7,8):
            entry=TimesheetEntry.objects.get(employee=person,work_date=date(2026,9,day),project=project)
            entry.hours=4
            entry.save()
            TimesheetEntry.objects.get_or_create(employee=person,work_date=entry.work_date,project=None,
                defaults={'hours':4,'task_description':'Làm TQT các nhóm cá nhân và đơn vị giả lập'})
        fixture_data['two_work_lines_covered']=True
        fixture.write_text(json.dumps(fixture_data),encoding='utf-8')
    approved,_=MonthlyAttendanceSummary.objects.get_or_create(employee=person,year=2027,month=4)
    if approved.status!='Approved':
        approved.sick_days=Decimal('1.5');approved.annual_leave_days=Decimal('2');approved.status='Approved';approved.save()
    LeaveBalance.objects.get_or_create(employee=person,year=2027,defaults={'allocated_days':20})
    for pr, percent in ((project,60),(other,40)):
        ProjectTimeAllocation.objects.get_or_create(employee=person,project=pr,year=2026,month=11,
            defaults={'allocation_percent':percent})
    password = next(line.split(': ',1)[1] for line in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if line.startswith('Mật khẩu'))
    output = folder / ('bcc-print-' + args.phase)
    output.mkdir(exist_ok=True)
    report = {'synthetic_only':True,'phase':args.phase,'checks':[],'failures':[],'cases':{}}
    def check(ok, label):
        report['checks' if ok else 'failures'].append(label)

    client = Client(); client.force_login(hr)
    reference = root / 'design-system/reference/print/BCC_T9.2026 - Tân.pdf'
    if reference.exists():
        with pdfplumber.open(reference) as pdf:
            report['reference'] = {'pages':len(pdf.pages),'size':[pdf.pages[0].width,pdf.pages[0].height],
                'font_sizes':sorted({round(c['size'],2) for c in pdf.pages[0].chars}),
                'blue_fills':len([r for p in pdf.pages for r in p.rects if is_blue(r.get('non_stroking_color'))])}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge',headless=True)
        context = browser.new_context(service_workers='block',locale='vi-VN',viewport={'width':794,'height':1123})
        page = context.new_page(); base = f'http://127.0.0.1:{args.port}'
        page.goto(base+'/portal/login/')
        page.locator('[name=username]').fill('demo-hr');page.locator('[name=password]').fill(password)
        page.locator('main form button[type=submit]').click();page.wait_for_load_state('networkidle')
        for label,year,month,has_balance in cases:
            person.manager=None if label=='no-balance' else manager
            if label == 'long':
                person.full_name = 'Nhân viên giả lập có họ tên rất dài để kiểm tra bố cục chữ ký và khối thông tin'
                person.save(update_fields=['full_name','manager'])
            else:
                person.full_name = 'Nhân viên giả lập BCC'
                person.save(update_fields=['full_name','manager'])
            route = f'/portal/timesheet/?month={month}&year={year}'
            with CaptureQueriesContext(connection) as queries:
                response = client.get(route)
            ctx = response.context
            formula = {key:str(ctx[key]) for key in ('total_hours','required_hours','diff_hours')}
            page.goto(base+route,wait_until='networkidle')
            for width in (1920,1440,1024,768,390):
                page.set_viewport_size({'width':width,'height':1000})
                for theme in ('light','dark'):
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                    check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'{label} screen {width} {theme} fits')
                    check(page.locator('button',has_text='In bảng công').is_visible(),f'{label} screen print button')
            if label == 'single':
                row = page.locator('.ui-timesheet-weekend').filter(has_text='Retreat 2026')
                check(row.count()==1,'weekend work and hours visible on screen')
            # emulate_media alone retains the screen viewport. Measure a second
            # layout at the named page's content width, not at full paper width.
            content_mm=186 if args.phase=='before' else 163
            page.set_viewport_size({'width':round(content_mm*96/25.4),'height':1009})
            page.emulate_media(media='print')
            geometry = page.locator('.timesheet-document').evaluate('''d=>{
                const t=d.querySelector('table'), main=document.querySelector('main'),wrap=document.querySelector('.ui-main-wrap');
                const box=x=>{const r=x.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width,height:r.height}};
                return {document:box(d),table:box(t),main:box(main),wrap:box(wrap),columns:[...t.querySelector('thead tr').cells].map(box),font:getComputedStyle(t).fontFamily,fontSize:getComputedStyle(t).fontSize,
                    signatures:[...d.querySelectorAll('.ui-timesheet-signature')].map(s=>({heading:box(s.firstElementChild),name:box(s.lastElementChild)}))};}''')
            geometry['content_width_mm']=content_mm
            check(geometry['table']['right']<=geometry['document']['right']+1,label+' emulated content width contains table')
            case = {'geometry':geometry,'query_count':len(queries),'formula':formula,'pdfs':{}}
            for mode in ('css','a4-default'):
                for theme in ('light','dark'):
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                    path = output / f'{label}-{mode}-{theme}.pdf'
                    page.pdf(path=str(path),prefer_css_page_size=mode=='css',format='A4',print_background=True)
                    metrics = inspect_pdf(path,month,year)
                    case['pdfs'][mode+'-'+theme] = metrics
                    prefix=f'{label} {mode} {theme} '
                    check(metrics['a4'],prefix+'A4 dimensions')
                    check(metrics['bounds_ok'],prefix+'all table borders inside 30/17mm margins')
                    check(metrics['right_border'],prefix+'right border present')
                    check(metrics['blue_rows']==sum(date(year,month,d).weekday()>=5 for d in range(1,calendar.monthrange(year,month)[1]+1)),prefix+'all weekend rows blue')
                    check(metrics['logo'] and metrics['appendix'],prefix+'logo and appendix')
                    check(35<=metrics['logo_width_mm']<=37,prefix+'logo width 36mm')
                    check(metrics['title_bold_size']>=16,prefix+'bold title >=16pt')
                    check(metrics['serif_body'],prefix+'serif table font >=10pt')
                    check(not metrics['status_printed'],prefix+'approval state excluded')
                    check(metrics['signature_gap_mm']>=22,prefix+'signature gap >=22mm')
                    check(metrics['pages']<=2 and not metrics['blank_pages'],prefix+'one or two nonblank pages')
                    check(metrics['header_repeated'],prefix+'table header repeats')
                    check(metrics['ending_together'],prefix+'last two days totals and signatures together')
                    check(metrics['right_aligned'],prefix+'daily hours right aligned')
                    if label=='single':check(metrics['weekend_work'],prefix+'Saturday work and 8 hours preserved')
                    if label=='single':check('+ Nghỉ lễ:' in metrics['text'],prefix+'empty holiday label retained')
                    if label=='multiple':check('Phân bổ thời gian (INC3B)' in metrics['text'] and 'Phân bổ thời gian (BCC2)' in metrics['text'],prefix+'multiple project allocations retained')
            for mode in ('css','a4-default'):
                light=case['pdfs'][mode+'-light'];dark=case['pdfs'][mode+'-dark']
                check(light==dark,label+' '+mode+' light/dark PDF geometry and text identical')
            if args.phase=='after':
                old_path=folder/'bcc-print-before/result.json'
                if old_path.exists():
                    old=json.loads(old_path.read_text(encoding='utf-8'))['cases'][label]
                    check(len(queries)<=old['query_count'],label+' queries do not increase')
                    check(formula==old['formula'],label+' formulas unchanged')
            report['cases'][label]=case
            page.emulate_media(media='screen')
            page.screenshot(path=str(output/(label+'-screen.png')),full_page=True)
        browser.close()
    report['passed']=not report['failures']
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(report['checks']),'failures':report['failures'],'cases':len(cases)},ensure_ascii=False))
    return 0 if args.phase=='before' or report['passed'] else 1


def is_blue(color):
    return isinstance(color,(list,tuple)) and len(color)>=3 and all(abs(a-b)<.012 for a,b in zip(color,(91/255,155/255,213/255)))


def inspect_pdf(path,month,year):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        texts=[p.extract_text() or '' for p in pdf.pages]
        words=[p.extract_words(extra_attrs=['fontname','size']) for p in pdf.pages]
        chars=[c for p in pdf.pages for c in p.chars]
        # Table rules have at least 0.4pt stroke; thin rules are grouped by page.
        # Chromium paints collapsed borders as narrow filled rectangles rather
        # than stroked lines. Include those, excluding white/card/chart fills.
        rules=[(i,e) for i,p in enumerate(pdf.pages) for e in p.rects
               if min(e['width'],e['height'])<=1.2 and max(e['width'],e['height'])>3
               and is_ink(e.get('non_stroking_color'))]
        left=30*72/25.4;right=pdf.pages[0].width-17*72/25.4
        bounds=bool(rules) and all(e['x0']>=left-.8 and e['x1']<=right+.5 for _,e in rules)
        right_border=any(abs(e['x0']-right)<1.5 and abs(e['x1']-right)<1.5 and e['height']>10 for _,e in rules)
        blue=[r for p in pdf.pages for r in p.rects if is_blue(r.get('non_stroking_color')) and r['width']>10]
        # A filled table row is emitted as three cell rectangles.
        blue_rows=len({(i,round(r['top'],1)) for i,p in enumerate(pdf.pages) for r in p.rects if is_blue(r.get('non_stroking_color'))})
        alltext='\n'.join(texts)
        title=[c for c in chars if 'Bold' in c['fontname'] and c['size']>=16]
        body=[c for c in chars if c['text'].isdigit() and c['size']<16]
        serif=bool(body) and all(any(font in c['fontname'] for font in ('Times','LiberationSerif')) and c['size']>=9.95 for c in body)
        signature_gap=0
        for p in pdf.pages:
            heads=p.search('Quản lý trực tiếp') or []
            if heads:
                h=heads[-1]
                candidates=[w for w in p.extract_words() if w['top']>h['bottom'] and w['x0']>=h['x0']-20]
                if candidates:signature_gap=(min(w['top'] for w in candidates)-h['bottom'])*25.4/72
        totals=[i for i,t in enumerate(texts) if 'Tổng số giờ làm việc trong tháng' in t]
        signature=[i for i,t in enumerate(texts) if 'Quản lý trực tiếp' in t]
        endok=len(totals)==1 and totals==signature
        if endok:
            for day in (calendar.monthrange(year,month)[1]-1,calendar.monthrange(year,month)[1]):
                endok=endok and any(w['text']==str(day) and w['x0']<left+20 for w in words[totals[0]])
        daily_right=[]
        for ws in words:
            daily_right.extend(w['x1'] for w in ws if w['text'] in ('0','8','10') and w['x0']>right-40)
        aligned=bool(daily_right) and max(daily_right)-min(daily_right)<=1
        weekend=False
        for p in pdf.pages:
            for r in p.rects:
                if is_blue(r.get('non_stroking_color')) and r['width']>100:
                    rowtext=p.crop((left-.5,r['top']-.1,right+.5,r['bottom']+.1)).extract_text() or ''
                    if 'Retreat 2026' in rowtext and '8' in rowtext:weekend=True
        return {'pages':len(pdf.pages),'a4':all(abs(p.width-595.28)<1 and abs(p.height-841.89)<1 for p in pdf.pages),
            'bounds_ok':bounds,'right_border':right_border,'max_rule_x1':round(max((e['x1'] for _,e in rules),default=0),2),'print_right':round(right,2),
            'blue_rows':blue_rows,'blue_rects':len(blue),'logo':any(p.images for p in pdf.pages),
            'logo_width_mm':round(max((im['width'] for p in pdf.pages for im in p.images),default=0)*25.4/72,2),'appendix':'Phụ lục 1' in alltext,
            'title_bold_size':round(max((c['size'] for c in title),default=0),2),'serif_body':serif,'status_printed':any(s in alltext for s in ('Chờ quản lý duyệt','Đã duyệt')),
            'signature_gap_mm':round(signature_gap,2),'blank_pages':any(len(t.strip())<20 for t in texts),'header_repeated':all('Công việc' in t and 'Ngày' in t for t in texts),
            'ending_together':bool(endok),'right_aligned':aligned,'weekend_work':weekend,'text':alltext}


def is_ink(color):
    return isinstance(color,(tuple,list)) and all(value<.6 for value in color)


if __name__=='__main__':
    raise SystemExit(main())
