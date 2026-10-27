/* Opt-in validation and confirmation. Native form names/actions/CSRF are preserved. */
(() => {
 'use strict';
 document.querySelectorAll('.ui-row-dropdown button[popovertarget]').forEach(button => {
  const menu=document.getElementById(button.getAttribute('popovertarget'));
  if(!menu)return;
  function position(){
   const rect=button.getBoundingClientRect();
   const width=menu.offsetWidth,height=menu.offsetHeight,gap=8;
   menu.style.left=Math.max(gap,Math.min(rect.right-width,innerWidth-width-gap))+'px';
   const below=innerHeight-rect.bottom-gap;
   menu.style.top=Math.max(gap,below>=height?rect.bottom+gap:Math.min(rect.top-height-gap,innerHeight-height-gap))+'px';
  }
  menu.addEventListener('toggle',event=>{
   const open=event.newState==='open';button.setAttribute('aria-expanded',String(open));
   if(open){position();menu.querySelector('a')?.focus({preventScroll:true});}
  });
  menu.addEventListener('keydown',event=>{
   const links=Array.from(menu.querySelectorAll('a'));
   if(event.key==='Escape'){event.preventDefault();menu.hidePopover();button.focus();}
   else if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
    event.preventDefault();const index=links.indexOf(document.activeElement);
    const target=event.key==='Home'?0:event.key==='End'?links.length-1:(index+(event.key==='ArrowDown'?1:-1)+links.length)%links.length;
    links[target]?.focus();
   }
  });
  const close=()=>{if(menu.matches(':popover-open'))menu.hidePopover();};
  window.addEventListener('resize',close);
  document.addEventListener('scroll',event=>{
   if(!menu.contains(event.target)&&menu.matches(':popover-open'))position();
  },true);
 });
 document.querySelectorAll('[data-ui-disclosure-close]').forEach(button => {
  button.addEventListener('click',()=>{
   const disclosure=button.closest('details');
   if(disclosure){disclosure.open=false;disclosure.querySelector('summary')?.focus();}
  });
 });
 document.querySelectorAll('form[data-ui-form]').forEach(form => {
  const summary=form.querySelector('[data-ui-errors]');
  const controls=()=>Array.from(form.elements).filter(e=>e.matches?.('input,select,textarea')&&e.type!=='hidden'&&e.willValidate&&!e.classList.contains('ui-number-display'));
  function errors(){
   if(!summary)return;
   const list=summary.querySelector('ul');list.replaceChildren();
   controls().forEach(control=>{
    const target=control.classList.contains('ui-number-source')?control.nextElementSibling:control;
    if(!target?.id)return;
    let error=document.getElementById(target.id+'-error');
    if(!error){error=document.createElement('p');error.className='ui-field-error';error.id=target.id+'-error';target.after(error);}
    const bad=!control.validity.valid||(target!==control&&!target.validity.valid);
    const v=control.validity;
    const display=value=>window.IhrmsNumbers?.format(String(value))||String(value);
    const message=v.valueMissing?'Vui lòng nhập thông tin này.':v.rangeUnderflow?'Giá trị tối thiểu là '+display(control.min)+'.':v.rangeOverflow?'Giá trị tối đa là '+display(control.max)+'.':v.typeMismatch||v.badInput?'Thông tin chưa đúng định dạng.':v.stepMismatch?'Giá trị chưa đúng bước tăng cho phép.':v.tooLong?'Thông tin vượt quá độ dài cho phép.':v.patternMismatch?'Thông tin chưa đúng định dạng yêu cầu.':target.validationMessage||control.validationMessage;
    target.setAttribute('aria-invalid',String(bad));
    const described=(target.getAttribute('aria-describedby')||'').split(/\s+/).filter(x=>x&&x!==error.id);
    if(bad)described.push(error.id);
    if(described.length)target.setAttribute('aria-describedby',described.join(' '));else target.removeAttribute('aria-describedby');
    error.hidden=!bad;error.textContent=bad?message:'';
    if(bad){const item=document.createElement('li'),link=document.createElement('a');link.href='#'+target.id;const label=Array.from(form.querySelectorAll('label')).find(l=>l.htmlFor===target.id);link.textContent=(label?.textContent.trim().replace(/\s*\*$/, '')||target.getAttribute('aria-label')||target.name)+': '+message;item.append(link);list.append(item);}
   });
   summary.hidden=!list.children.length;
  }
  form.noValidate=true;
  form.addEventListener('invalid',event=>event.preventDefault(),true);
  form.addEventListener('submit',event=>{if(!form.checkValidity()){event.preventDefault();errors();summary?.focus();}});
  form.addEventListener('input',()=>{if(summary&&!summary.hidden)errors();});
  summary?.addEventListener('click',event=>{const link=event.target.closest('a[href^="#"]');if(link){const field=document.getElementById(link.hash.slice(1));if(field){event.preventDefault();(field.classList.contains('ui-number-source')?field.nextElementSibling:field).focus();}}});
  if(summary&&!summary.hidden)summary.focus();
 });
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){document.querySelectorAll('.ui-row-menu[open]').forEach(menu=>{if(menu.contains(document.activeElement)){menu.open=false;menu.querySelector('summary').focus();}});}});
 const dialog=document.getElementById('ui-confirm-dialog');
 if(!dialog||!dialog.showModal)return;
 let pending=null,origin=null;
 const approved=new WeakSet();
 document.addEventListener('submit',event=>{
  const form=event.target;
  if(!form.matches('form[data-ui-confirm]'))return;
  if(approved.has(form)){approved.delete(form);return;}
  if(event.defaultPrevented)return;
  event.preventDefault();pending={form,submitter:event.submitter};origin=event.submitter||document.activeElement;
  document.getElementById('ui-confirm-title').textContent=form.dataset.uiConfirmTitle||'Xác nhận thao tác';
  document.getElementById('ui-confirm-description').textContent=form.dataset.uiConfirm;
  const accept=dialog.querySelector('[data-ui-confirm-accept]');
  accept.textContent=form.dataset.uiConfirmLabel||'Xác nhận';
  accept.className='ui-button '+(form.dataset.uiConfirmTone==='primary'?'ui-button--primary':'ui-button--danger');
  dialog.showModal();dialog.querySelector('[data-ui-confirm-cancel]').focus();
 });
 dialog.addEventListener('keydown',event=>{if(event.key!=='Tab')return;const targets=Array.from(dialog.querySelectorAll('button,a[href],input,select,textarea,[tabindex="0"]')).filter(e=>!e.disabled&&e.getClientRects().length);const first=targets[0],last=targets.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}});
 dialog.querySelector('[data-ui-confirm-cancel]').addEventListener('click',()=>dialog.close());
 dialog.querySelector('[data-ui-confirm-accept]').addEventListener('click',()=>{const action=pending;if(!action)return;pending=null;approved.add(action.form);dialog.close();action.form.requestSubmit(action.submitter||undefined);});
 dialog.addEventListener('close',()=>{pending=null;if(origin?.isConnected)origin.focus();});
})();

/* Native dates remain usable without JavaScript; only their readable echo is added. */
(() => {
 'use strict';
 function enhanceDates() {
  document.querySelectorAll('input[type=date],input[type=month]').forEach((input,index) => {
   if(input.closest('.hcns-paper'))return;
   input.lang='vi';
   if(input.dataset.dateEchoReady)return;
   input.dataset.dateEchoReady='true';
   const echo=document.createElement('p');echo.className='ui-date-echo ui-screen-only';
   echo.id=(input.id||('ui-date-'+index))+'-echo';echo.setAttribute('aria-live','polite');
   input.after(echo);
   input.setAttribute('aria-describedby',[input.getAttribute('aria-describedby'),echo.id].filter(Boolean).join(' '));
   const update=()=>{
    const match=input.value.match(/^(\d{4})-(\d{2})(?:-(\d{2}))?$/);
    if(!match){echo.textContent='';const query=input.closest('.ui-query-bar');if(query)query.classList.toggle('ui-query-bar--date-echo',[...query.querySelectorAll('.ui-date-echo')].some(x=>x.textContent));return;}
    const date=new Date(Number(match[1]),Number(match[2])-1,Number(match[3]||1));
    const text=input.type==='month'?new Intl.DateTimeFormat('vi-VN',{month:'long',year:'numeric'}).format(date):new Intl.DateTimeFormat('vi-VN',{weekday:'long'}).format(date)+', '+match[3]+'/'+match[2]+'/'+match[1];
    echo.textContent=text.charAt(0).toUpperCase()+text.slice(1);
    const query=input.closest('.ui-query-bar');
    if(query)query.classList.toggle('ui-query-bar--date-echo',[...query.querySelectorAll('.ui-date-echo')].some(x=>x.textContent));
   };
   input.addEventListener('input',update);input.addEventListener('change',update);update();
  });
 }
 enhanceDates();
 new MutationObserver(enhanceDates).observe(document.body,{childList:true,subtree:true});
 // Align the actual controls, including wrapped labels, without changing DOM order.
 let rowFrame;
 const alignRows=()=>{
  rowFrame=undefined;
  document.querySelectorAll('.ui-form-grid').forEach(grid=>{
   if(!grid.checkVisibility()||grid.closest('.hcns-paper,.hcns-editor'))return;
   const fields=[...grid.children].filter(x=>x.matches('.ui-field')&&x.checkVisibility());
   for(const field of fields){const label=field.querySelector(':scope > label');if(label)label.style.minHeight='';}
   const rows=[];
   for(const field of fields){const y=field.getBoundingClientRect().y;let row=rows.find(r=>Math.abs(r.y-y)<1);if(!row){row={y,fields:[]};rows.push(row);}row.fields.push(field);}
   for(const row of rows){const labels=row.fields.map(x=>x.querySelector(':scope > label')).filter(Boolean);const height=Math.max(0,...labels.map(x=>x.getBoundingClientRect().height));for(const label of labels)label.style.minHeight=height+'px';}
   if(grid.matches('.ui-form-grid--inline,.ui-form-grid--event')){
    const actions=grid.querySelector(':scope > .ui-form-actions'),last=fields.at(-1),label=last?.querySelector(':scope > label');
    if(actions&&last&&label){const sameRow=Math.abs(actions.getBoundingClientRect().y-last.getBoundingClientRect().y)<80;actions.style.marginTop=(sameRow?label.getBoundingClientRect().height+parseFloat(getComputedStyle(label).marginBottom):0)+'px';}
   }
  });
 };
 const scheduleRows=()=>{if(rowFrame===undefined)rowFrame=requestAnimationFrame(alignRows);};
 const rowObserver=new ResizeObserver(scheduleRows);
 document.querySelectorAll('.ui-form-grid').forEach(x=>rowObserver.observe(x));
 window.addEventListener('resize',scheduleRows);document.addEventListener('toggle',scheduleRows,true);scheduleRows();
})();

/* Shared responsive header actions. Move existing nodes: URLs and permission
   guards stay intact; native details keeps keyboard access without a JS menu API. */
(() => {
 'use strict';
 const headers=[...document.querySelectorAll('.ui-section-header,.ui-card-header')];
 for(const header of headers){
  const actions=header.querySelector(':scope > :is(.ui-header-actions,.ui-card-actions)');
  if(!actions)continue;
  const links=[...actions.children].filter(x=>x.matches('a'));
  if(!links.length)continue;
  const markers=links.map(link=>{const marker=document.createComment('action');link.before(marker);return marker;});
  const more=document.createElement('details');more.className='ui-action-overflow';more.hidden=true;
  const summary=document.createElement('summary');summary.textContent='Xem thêm';
  const menu=document.createElement('div');menu.className='ui-action-menu';
  more.append(summary,menu);actions.append(more);
  let frame;
  const layout=()=>{
   frame=undefined;
   // Do not relocate an active control during keyboard navigation.
   if(more.open||actions.contains(document.activeElement))return;
   links.forEach((link,i)=>markers[i].after(link));more.hidden=true;
   const style=getComputedStyle(header),padding=parseFloat(style.paddingLeft)+parseFloat(style.paddingRight);
   const available=header.clientWidth-padding;
   const title=header.querySelector(':scope > :is(h2,h3,div:not(.ui-header-actions):not(.ui-card-actions))');
   const titleWidth=title?Math.min(title.scrollWidth,Math.max(available*.5,160)):0;
   const gap=parseFloat(style.columnGap)||0;
   const primary=links.filter(x=>x.matches('.ui-button--primary'));
   const secondary=links.filter(x=>!x.matches('.ui-button--primary'));
   if(primary.length>1||secondary.length>2){
    [...primary.slice(1),...secondary.slice(1)].forEach(link=>menu.append(link));more.hidden=false;
   }
   if(titleWidth+actions.scrollWidth+gap>available){
    links.forEach(link=>menu.append(link));more.hidden=false;
   }
   header.classList.toggle('ui-header--stacked',available<288);
  };
  const schedule=()=>{if(frame===undefined)frame=requestAnimationFrame(layout);};
  new ResizeObserver(schedule).observe(header);schedule();
  actions.addEventListener('focusout',schedule);
  more.addEventListener('keydown',event=>{if(event.key==='Escape'){more.open=false;summary.focus();}});
  more.addEventListener('focusout',()=>requestAnimationFrame(()=>{if(!more.contains(document.activeElement))more.open=false;}));
  document.addEventListener('click',event=>{if(!more.contains(event.target))more.open=false;});
 }
})();
