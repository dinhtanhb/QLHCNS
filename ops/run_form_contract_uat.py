"""Compare existing form wire contracts/query counts on external synthetic data."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path

from run_layout_alignment_audit import configure, inventory


class FormContract(HTMLParser):
    """Retain DOM submission order, defaults and validation; omit presentation."""
    ignored = {'class','id','style','placeholder','lang','rows','cols','tabindex',
               'aria-describedby','aria-labelledby','aria-label','aria-live','aria-invalid',
               'data-ui-form','data-ui-date','list'}

    def __init__(self, html):
        super().__init__()
        self.forms=[]
        self.form=None
        self.field=None
        self.option=None
        self.in_datalist=False
        self.feed(html)

    def attrs(self, pairs):
        attrs={key:value for key,value in pairs if key not in self.ignored and not key.startswith('aria-')}
        if attrs.get('name')=='csrfmiddlewaretoken':attrs['value']='CSRF_PRESENT'
        return attrs

    def handle_starttag(self, tag, pairs):
        if tag=='datalist':self.in_datalist=True;return
        if self.in_datalist:return
        attrs=self.attrs(pairs)
        if tag=='form':
            self.form={'attrs':attrs,'fields':[]};self.forms.append(self.form)
        elif self.form is not None and tag in ('input','select','textarea','button'):
            self.field={'tag':tag,'attrs':attrs}
            self.form['fields'].append(self.field)
        elif self.field is not None and tag=='option':
            self.option={'attrs':attrs,'text':''};self.field.setdefault('options',[]).append(self.option)

    def handle_data(self,data):
        if self.option is not None:self.option['text']+=data
        elif self.field is not None and self.field['tag']=='textarea':self.field['text']=self.field.get('text','')+data

    def handle_endtag(self,tag):
        if tag=='datalist':self.in_datalist=False;return
        if self.in_datalist:return
        if tag=='option' and self.option is not None:self.option['text']=self.option['text'].strip();self.option=None
        if tag in ('select','textarea','button'):self.field=None
        if tag=='form':self.form=None;self.field=None


def normalize_finance_choices(forms, old_forms, route):
    """Accept only the three explicitly requested native choice controls.

    All other fields, form attributes, defaults and query counts stay audited.
    A baseline already containing selects is compared without normalization.
    """
    specifications = {
        'portal:finance_period_list': {
            'payroll_month': ('number', '1', '12', [''] + [str(n) for n in range(1, 13)]),
            'payroll_year': ('number', '2000', '2100', [''] + [str(n) for n in range(2000, 2101)]),
        },
        'portal:finance_dependent_list': {
            'relationship': ('text', None, None, ['', 'Con', 'Vợ', 'Chồng', 'Cha', 'Mẹ', 'Cha vợ/chồng', 'Mẹ vợ/chồng', 'Khác']),
        },
    }
    for name, (kind, minimum, maximum, values) in specifications.get(route, {}).items():
        previous = [f for form in old_forms or [] for f in form['fields'] if f['attrs'].get('name') == name]
        current = [f for form in forms or [] for f in form['fields'] if f['attrs'].get('name') == name]
        expected = {'name': name, 'type': kind, 'value': '', 'required': None}
        if minimum is not None:
            expected.update(min=minimum, max=maximum)
        if len(previous) != 1 or len(current) != 1 or previous[0] != {'tag': 'input', 'attrs': expected}:
            continue
        field = current[0]
        options = field.get('options', [])
        if field['tag'] == 'select' and field['attrs'] == {'name': name, 'required': None} and [o['attrs'] for o in options] == [{'value': value} for value in values]:
            field.clear()
            field.update(previous[0])


def normalize_task_catalog(forms, old_forms):
    """Only task_create's exact selector/name replacement is approved."""
    from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
    for name in ('act_code', 'task_name'):
        old_name = 'task_code' if name == 'act_code' else name
        old = [f for form in old_forms or [] for f in form['fields'] if f['attrs'].get('name') == old_name]
        new = [f for form in forms or [] for f in form['fields'] if f['attrs'].get('name') == name]
        if len(old) != 1 or len(new) != 1:
            continue
        expected_old = ({'tag': 'select', 'attrs': {'name': 'task_code', 'required': None}, 'options': [
            {'attrs': {'value': ''}, 'text': '-- Chọn mã ActCode --'},
            *[{'attrs': {'value': code, 'data-search': title}, 'text': code} for code, title in ACTIVITY_CODE_NAMES.items()],
        ]} if name == 'act_code' else {'tag': 'input', 'attrs': {'type': 'text', 'name': name, 'value': '', 'readonly': None}})
        if old[0] != expected_old:
            continue
        if name == 'act_code':
            expected = {'tag': 'select', 'attrs': {'name': name, 'required': None}, 'options': [
                {'attrs': {'value': ''}, 'text': '-- Chọn mã ActCode --'},
                *[{'attrs': {'value': code}, 'text': code+' — '+title} for code, title in ACTIVITY_CODE_NAMES.items()],
                {'attrs': {'value': '__OTHER__'}, 'text': 'Khác (công việc hành chính)'},
            ]}
        else:
            expected = {'tag': 'input', 'attrs': {'type': 'text', 'name': name, 'value': '', 'maxlength': '300'}}
        if new[0] == expected:
            new[0].clear()
            new[0].update(old[0])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,required=True);p.add_argument('--source-root',type=Path)
    p.add_argument('--phase',choices=('before','after'),required=True);p.add_argument('--only',nargs='+')
    p.add_argument('--allow-event-mode',action='store_true',help='Allow only the approved attendance_mode select addition on event_list.')
    p.add_argument('--allow-finance-choices',action='store_true',help='Allow only the requested month/year/relationship input-to-select conversions with exact values.')
    p.add_argument('--allow-task-catalog',action='store_true',help='Allow the approved ActCode catalog selector and derived title on task_create only.')
    args=p.parse_args();root=(args.source_root or Path(__file__).resolve().parents[1]).resolve();folder=args.directory.resolve()
    if root==folder or root in folder.parents:p.error('External synthetic runtime required')
    configure(root,folder)
    from django.core.cache import cache
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from apps.security.models import User
    routes=inventory(args.only)
    report={'synthetic_only':True,'cases':{},'failures':[]}
    baseline=json.loads((folder/'form-contract-before.json').read_text(encoding='utf-8')) if args.phase=='after' else None
    for account in ('demo-layout-admin','demo-hr','demo-director','demo-manager','demo-employee','demo-finance','demo-hr-officer','demo-sys','demo-unlinked'):
        client=Client();client.force_login(User.objects.get(username=account))
        for route in routes:
            if 'url' not in route:continue
            cache.clear()
            connection.queries_log.clear()
            with CaptureQueriesContext(connection) as queries:response=client.get(route['url'],HTTP_HOST='127.0.0.1')
            key=account+' '+route['name']
            case={'status':response.status_code,'selects':sum(q['sql'].lstrip().upper().startswith('SELECT') for q in queries)}
            if response.status_code==200 and 'text/html' in response.get('Content-Type',''):
                case['forms']=FormContract(response.content.decode()).forms
            if getattr(response,'streaming',False):response.close()
            report['cases'][key]=case
            if case['status'] in (400,500):report['failures'].append(key+' unexpected HTTP '+str(case['status']))
            if baseline:
                old=baseline['cases'].get(key)
                if old is None:report['failures'].append(key+' missing baseline')
                else:
                    import copy
                    if old['status']!=case['status']:report['failures'].append(key+' HTTP status changed')
                    if case['selects']>old['selects']:report['failures'].append(key+' SELECT count increased')
                    normalized=copy.deepcopy(case.get('forms'))
                    if args.allow_task_catalog and route['name'] == 'portal:task_create':
                        normalize_task_catalog(normalized, old.get('forms'))
                    if args.allow_finance_choices:
                        normalize_finance_choices(normalized, old.get('forms'), route['name'])
                    if args.allow_event_mode and route['name']=='portal:event_list':
                        modes=[f for form in normalized or [] for f in form['fields'] if f['attrs'].get('name')=='attendance_mode']
                        allowed=len(modes)==1 and modes[0]['tag']=='select' and modes[0]['attrs']=={'name':'attendance_mode'} and modes[0].get('options')==[{'attrs':{'value':'Online'},'text':'Online'},{'attrs':{'value':'Offline','selected':None},'text':'Offline'}]
                        old_modes=[f for form in old.get('forms') or [] for f in form['fields'] if f['attrs'].get('name')=='attendance_mode']
                        # The exception is only for a baseline created before the
                        # approved field existed.  A matching field must remain
                        # part of the contract when the baseline already has it.
                        if allowed and not old_modes:
                            for form in normalized:form['fields']=[f for f in form['fields'] if f['attrs'].get('name')!='attendance_mode']
                    if normalized!=old.get('forms'):report['failures'].append(key+' form contract changed')
    (folder/('form-contract-'+args.phase+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'cases':len(report['cases']),'failures':report['failures']}))
    return bool(report['failures'])


if __name__=='__main__':raise SystemExit(main())
