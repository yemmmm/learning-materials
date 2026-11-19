/* === SLIDE NAVIGATION · fixed 16:9 canvas, optional incremental presentation === */
(() => {
  const slides=[...document.querySelectorAll('.slide')], stage=document.getElementById('stage');
  const notes=JSON.parse(document.getElementById('notesData').textContent);
  let index=0,stepMode=false,step=0,editing=false,wheelTime=0;
  const $=id=>document.getElementById(id);
  function resize(){const scale=Math.min(innerWidth/1920,innerHeight/1080);stage.style.transform=`translate(${(innerWidth-1920*scale)/2}px,${(innerHeight-1080*scale)/2}px) scale(${scale})`;}
  function parts(){return [...slides[index].querySelector('.slide-body').children];}
  function showParts(){parts().forEach((el,i)=>el.classList.toggle('step-hidden',stepMode&&i>step));}
  function syncNotes(){const n=notes[index];$('noteTitle').textContent=`${index+1}. ${n.title}`;$('noteText').textContent=n.text;$('noteSources').replaceChildren();for(const s of n.sources){const a=document.createElement('a');a.href=s.href;a.textContent=s.title;a.target='_blank';a.rel='noopener';$('noteSources').append(a);}}
  function go(page){index=Math.max(0,Math.min(slides.length-1,Number(page)-1||0));step=0;slides.forEach((s,i)=>{s.classList.toggle('active',i===index);s.setAttribute('aria-hidden',String(i!==index));s.inert=i!==index;});showParts();$('pageLabel').textContent=`${String(index+1).padStart(2,'0')} / ${slides.length}`;$('progressBar').style.width=`${(index+1)/slides.length*100}%`;history.replaceState(null,'',`#${index+1}`);document.title=`${index+1} · ${notes[index].title} | 本体论思想在agent中的应用 v3.6`;syncNotes();}
  function next(){if(stepMode&&step<parts().length-1){step++;showParts();}else go(index+2);}
  function prev(){if(stepMode&&step>0){step--;showParts();}else go(index);}
  function toast(s){$('toast').textContent=s;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,2300);}
  function toggleSteps(){stepMode=!stepMode;document.body.classList.toggle('stepping',stepMode);$('steps').setAttribute('aria-pressed',String(stepMode));step=0;showParts();toast(stepMode?'分步演讲：方向键逐步展示；A 展开本页':'完整阅读：当前页全部内容可见');}
  function openDialog(id){const d=$(id);if(!d.open)d.showModal();}
  async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{toast('可通过浏览器菜单进入全屏');}}
  $('prev').onclick=prev;$('next').onclick=next;$('contents').onclick=()=>openDialog('contentsDialog');$('notes').onclick=()=>openDialog('notesDialog');$('steps').onclick=toggleSteps;$('fullscreen').onclick=fullscreen;
  document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
  document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{go(b.dataset.go);$('contentsDialog').close();});
  /* === POST-DRAFT EDITING · keep changes local until explicitly saved === */
  const editable=[...document.querySelectorAll('.edit-text,.slide-body p,.slide-body h2,.slide-body h3,.faq-answer')].filter(el=>!el.closest('button')&&!el.querySelector('.edit-text'));
  function toggleEdit(){editing=!editing;document.body.classList.toggle('editing',editing);editable.forEach(el=>el.contentEditable=String(editing));$('edit').setAttribute('aria-pressed',String(editing));toast(editing?'点击正文编辑；Ctrl+S 下载修改后的 HTML':'已退出编辑');}
  function save(){const clone=document.documentElement.cloneNode(true);clone.querySelectorAll('[contenteditable]').forEach(el=>el.removeAttribute('contenteditable'));clone.querySelector('body').classList.remove('editing','stepping','capture');clone.querySelectorAll('.step-hidden').forEach(el=>el.classList.remove('step-hidden'));clone.querySelectorAll('dialog').forEach(el=>el.removeAttribute('open'));clone.querySelector('#toast').hidden=true;const u=URL.createObjectURL(new Blob(['<!doctype html>\n'+clone.outerHTML],{type:'text/html;charset=utf-8'}));const a=document.createElement('a');a.href=u;a.download='ontology-agent-slides-v3.6-edited.html';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);toast('已下载修改后的 HTML');}
  $('edit').onclick=toggleEdit;
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();save();return;}if(e.target.isContentEditable||e.target.matches('input,textarea,select'))return;if(document.querySelector('dialog[open]'))return;if(e.target.closest('button')&&[' ','Enter'].includes(e.key))return;
    if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();next();}else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();prev();}else if(e.key==='Home')go(1);else if(e.key==='End')go(slides.length);else if(e.key.toLowerCase()==='a'){step=parts().length;showParts();}else if(e.key.toLowerCase()==='g')openDialog('contentsDialog');else if(e.key.toLowerCase()==='n')openDialog('notesDialog');else if(e.key.toLowerCase()==='s')toggleSteps();else if(e.key.toLowerCase()==='e')toggleEdit();else if(e.key.toLowerCase()==='f')fullscreen();});
  let touchStart=null;stage.addEventListener('touchstart',e=>{if(!e.target.closest('button,input,[contenteditable=true]'))touchStart=[e.changedTouches[0].clientX,e.changedTouches[0].clientY];},{passive:true});stage.addEventListener('touchend',e=>{if(!touchStart)return;const dx=e.changedTouches[0].clientX-touchStart[0],dy=e.changedTouches[0].clientY-touchStart[1];if(Math.abs(dx)>50&&Math.abs(dx)>Math.abs(dy))dx<0?next():prev();touchStart=null;},{passive:true});
  stage.addEventListener('wheel',e=>{if(editing||document.querySelector('dialog[open]'))return;if(Date.now()-wheelTime>650&&Math.abs(e.deltaY)>25){wheelTime=Date.now();e.deltaY>0?next():prev();}},{passive:true});
  /* === SEMANTIC DEMONSTRATIONS · fictional case, no backend calls === */
  function select(button){button.parentElement.querySelectorAll('button').forEach(b=>{const active=b===button;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});}
  document.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',()=>{const {action,value}=b.dataset;
    if(action==='policy'){select(b);const isHead=value==='head';$('policyText').textContent=isHead?'由申请人当前所属部门的负责人审批':'对照政策：如果改为由申请人的直属主管审批';$('policyAnswer').textContent=isHead?'本例应由李敏审批。':'对照条件下，应由王强审批。';$('policyReason').textContent=isHead?'“部门负责人”与“直属主管”是两种关系。':'组织事实没有改变，政策含义改变了所走的路径。';document.querySelectorAll('[data-route]').forEach(el=>{el.classList.toggle('route-dim',el.dataset.route!==value);el.classList.toggle('route-active',el.dataset.route===value);});}
    else if(action==='ingredient'){const active=b.classList.contains('selected');select(b);$('ingredientGraph').classList.toggle('filtered',!active);if(active)b.classList.remove('selected');$('ingredientGraph').querySelectorAll('[data-kind]').forEach(el=>el.classList.toggle('highlight',el.dataset.kind.split(' ').includes(value)));}
    else if(action==='infer'){const r=$('inferenceResult');r.classList.remove('working');void r.offsetWidth;r.classList.add('working');r.querySelector('b').textContent='推导完成：李敏是员工。';}
    else if(action==='agentStep'){select(b);b.scrollIntoView({block:'nearest',inline:'nearest'});}
    else if(action==='fit'){select(b);$('fitText').textContent=value==='small'?'简单单次任务可以先用制度检索；长期复用时，再比较收益与澄清、连接、验证、维护的投入。':'多个助手跨系统、长期使用同一套业务定义时，集中澄清与维护语义更值得尝试，并用相同条件比较效果和成本。';}
    else if(action==='screenshot')openDialog('imageDialog');
  }));
  $('badFact').onchange=e=>{const r=$('consistencyResult');r.classList.toggle('error',e.target.checked);r.querySelector('b').textContent=e.target.checked?'发现矛盾：张三同时落入互斥的两类。':'当前两项陈述没有这个互斥冲突。';r.querySelector('p').textContent=e.target.checked?'“员工”和“部门”已声明互斥，这组分类断言不能同时成立。':'检查对象是给定陈述与约定；没有这个冲突不等于外部事实必然真实。';};
  $('missingHead').onchange=e=>{$('agentAnswer').textContent=e.target.checked?'已确认张三属于研发部，但缺少该部门当前负责人信息。暂无法确定审批人，需要查询或补充这一事实。':'应由李敏审批。依据为本例差旅政策与当前组织查询结果。';};
  document.querySelectorAll('button.selected').forEach(b=>b.setAttribute('aria-pressed','true'));
  window.addEventListener('beforeprint',()=>{document.querySelectorAll('.faq-list details').forEach(d=>d.open=true);});
  window.addEventListener('resize',resize);window.addEventListener('hashchange',()=>go(location.hash.slice(1)));
  window.deck={go,showAll:()=>{step=parts().length;showParts();},get index(){return index;},get count(){return slides.length;}};
  resize();go(location.hash.slice(1)||1);
})();
