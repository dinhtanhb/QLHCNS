"""Finance UI and confirmation workflow UAT on an external synthetic SQLite demo."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--packages-dir',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8782)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];folder=args.directory.resolve()
    if folder==root or root in folder.parents:parser.error('Synthetic runtime must be external.')
    marker=json.loads((folder/'synthetic-demo.json').read_text(encoding='utf-8'))
    if marker.get('synthetic_only') is not True:parser.error('Synthetic marker required.')
    os.environ.update(APP_ENV='test',DB_ENGINE='django.db.backends.sqlite3',DJANGO_SETTINGS_MODULE='config.settings',SECRET_KEY=marker['secret_key'],M365_STORAGE_ENABLED='False',DJANGO_ALLOW_ASYNC_UNSAFE='true')
    sys.path[:0]=[str(root/'src'),str(args.packages_dir.resolve())]
    import config.settings as cfg
    cfg.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(folder/'synthetic.sqlite3')}};cfg.MEDIA_ROOT=folder/'media'
    for handler in cfg.LOGGING['handlers'].values():
        if 'filename' in handler:handler['filename']=str(folder/Path(handler['filename']).name)
    import django
    django.setup()
    from apps.security.models import Role,User
    from apps.hrm.models import Employee
    from apps.payroll.models import EmployeeSalary,EmployeeDependent,PayrollPeriod,Payroll,InsuranceRateConfig,TaxDeductionConfig,PersonalIncomeTaxBracket
    from django.urls import reverse
    from playwright.sync_api import sync_playwright
    password=next(x.split(': ',1)[1] for x in (folder/'DEMO_ACCOUNTS.txt').read_text(encoding='utf-8').splitlines() if x.startswith('Mật khẩu'))
    role,_=Role.objects.get_or_create(role_code='FINANCE_OFFICER',defaults={'role_name':'Kế toán giả'})
    person=Employee.objects.order_by('pk').first()
    user,_=User.objects.get_or_create(username='demo-finance',defaults={'role':role,'employee':person})
    user.set_password(password);user.save()
    EmployeeSalary.objects.get_or_create(employee=person,effective_date=date(2026,1,1),defaults={'current_basic_salary':12345678})
    person.full_name='Nhân viên giả lập có họ tên dài để kiểm tra cột lương và người phụ thuộc';person.save(update_fields=['full_name'])
    EmployeeDependent.objects.get_or_create(employee=person,full_name='Người phụ thuộc giả có tên dài để thử bố cục',registered_from=date(2026,1,1),defaults={'relationship':'Con'})
    period,_=PayrollPeriod.objects.get_or_create(payroll_year=2026,payroll_month=10,defaults={'start_date':date(2026,10,1),'end_date':date(2026,10,31),'status':'Open'})
    row,_=Payroll.objects.get_or_create(employee=person,payroll_period=period,defaults={'basic_salary':12345678,'allowance':1000000,'overtime_amount':500000,'deduction_amount':100000})
    InsuranceRateConfig.objects.get_or_create(effective_from=date(2026,1,1),defaults={k:v for k,v in [('employee_social_insurance_rate',8),('employee_health_insurance_rate',1.5),('employee_unemployment_insurance_rate',1),('employer_social_insurance_rate',17.5),('employer_health_insurance_rate',3),('employer_unemployment_insurance_rate',1)]})
    TaxDeductionConfig.objects.get_or_create(effective_from=date(2026,1,1),defaults={'self_deduction_monthly':11000000,'dependent_deduction_monthly':4400000})
    PersonalIncomeTaxBracket.objects.get_or_create(effective_from=date(2026,1,1),bracket_no=1,defaults={'income_from_monthly':0,'income_to_monthly':None,'tax_rate':5})
    output=folder/'finance-followup-uat';output.mkdir(exist_ok=True);report={'synthetic_only':True,'checks':[],'failures':[]};base=f'http://127.0.0.1:{args.port}'
    def check(ok,label):report['checks' if ok else 'failures'].append(label)
    routes=[reverse('portal:'+r,args=[period.pk] if r=='finance_payroll_run' else []) for r in ('finance_salary_list','finance_dependent_list','finance_tax_config','finance_period_list','finance_payroll_run')]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True);context=browser.new_context(service_workers='block',reduced_motion='reduce');page=context.new_page()
        page.goto(base+'/portal/login/');page.locator('[name=username]').fill(user.username);page.locator('[name=password]').fill(password);page.locator('main button[type=submit]').click();page.wait_for_load_state('networkidle')
        for route in routes:
            response=page.goto(base+route,wait_until='networkidle');check(response.status==200,route+' authorized')
            for width in (1920,1440,1024,768,390):
                page.set_viewport_size({'width':width,'height':1000})
                for theme in ('light','dark'):
                    page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme);page.wait_for_timeout(40)
                    label=f'{route} {width} {theme}'
                    check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),label+' no page overflow')
                    metrics=page.locator('main button,main input:not([type=hidden]):not(.ui-number-source),main select').evaluate_all('''xs=>xs.filter(x=>x.getBoundingClientRect().width && !x.closest('dialog')).map(x=>({height:x.getBoundingClientRect().height,font:parseFloat(getComputedStyle(x).fontSize),tag:x.tagName,id:x.id,name:x.name,classes:x.className}))''')
                    check(all(x['height']>=43.5 and x['font']>=14 for x in metrics),label+' controls 44px and 14px')
                    if any(x['height']<43.5 or x['font']<14 for x in metrics):report.setdefault('small_controls',{})[label]=[x for x in metrics if x['height']<43.5 or x['font']<14]
                    page.keyboard.press('Tab');check(page.evaluate('document.activeElement!==document.body'),label+' keyboard focus')
                    if width in (1440,390):page.screenshot(path=str(output/(route.strip('/').replace('/','-')+f'-{width}-{theme}.png')),full_page=True)
        page.goto(base+routes[-1]);button=page.get_by_role('button',name='Tính lương toàn bộ kỳ này',exact=True)
        initial=row.calculated_at;button.focus();page.keyboard.press('Enter');check(page.locator('#ui-confirm-dialog').is_visible(),'Enter opens calculate confirmation');page.keyboard.press('Escape');check(not page.locator('#ui-confirm-dialog').is_visible(),'Escape closes calculate confirmation');row.refresh_from_db();check(row.calculated_at==initial,'cancel does not calculate')
        manual={k:getattr(row,k) for k in ('allowance','overtime_amount','deduction_amount')}
        button.click();page.locator('[data-ui-confirm-accept]').click();page.wait_for_load_state('networkidle');row.refresh_from_db();check(row.calculated_at is not None and (initial is None or row.calculated_at>initial),'confirm persists new calculation timestamp');check(all(getattr(row,k)==v for k,v in manual.items()),'manual payroll inputs retained');check('Đã tính lương' in page.locator('main').inner_text(),'calculation success notice');check(page.url.endswith(routes[-1]),'calculation returns to period')
        page.goto(base+routes[1]);page.locator('[name=full_name]').fill('Người phụ thuộc UAT '+str(EmployeeDependent.objects.count()));page.locator('[name=relationship]').fill('Con');page.locator('[name=registered_from]').fill('2026-10-01');before=EmployeeDependent.objects.count();page.get_by_role('button',name='Thêm người phụ thuộc',exact=True).click();page.wait_for_load_state('networkidle');check(EmployeeDependent.objects.count()==before+1,'dependent persisted');check('Đã thêm người phụ thuộc' in page.locator('main').inner_text(),'dependent success notice')
        page.goto(base+'/portal/');check(page.locator('main').is_visible(),'dashboard remains available after finance writes')
        context.close()
        context=browser.new_context(service_workers='block',reduced_motion='reduce');page=context.new_page()
        page.goto(base+'/portal/login/');page.locator('[name=username]').fill('demo-hr');page.locator('[name=password]').fill(password);page.locator('main button[type=submit]').click();page.wait_for_load_state('networkidle')
        page.goto(base+reverse('portal:hr_employee_list'))
        for width in (1920,1440,1024,768,390):
            page.set_viewport_size({'width':width,'height':1000})
            for theme in ('light','dark'):
                page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
                check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'employee list {width} {theme} no overflow')
                button=page.locator('[popovertarget]').first;button.focus();page.keyboard.press('Enter')
                check(page.locator('.ui-row-popover:popover-open').count()==1,f'employee actions {width} {theme} keyboard opens')
                page.keyboard.press('Tab');check(page.locator('.ui-row-popover:popover-open a:focus').count()==1,f'employee actions {width} {theme} link focus')
                page.keyboard.press('Escape');check(page.locator('.ui-row-popover:popover-open').count()==0,f'employee actions {width} {theme} Escape closes')
        browser.close()
    (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'checks':len(report['checks']),'failures':report['failures']},ensure_ascii=False));return 1 if report['failures'] else 0


if __name__=='__main__':raise SystemExit(main())
