/* === SLIDE CONTROLLER · navigation, fixed canvas, notes and local editing === */
class SlidePresentation {
  constructor() {
    this.slides = [...document.querySelectorAll('.slide')];
    this.stage = document.getElementById('deckStage');
    this.notes = JSON.parse(document.getElementById('notesData').textContent);
    this.currentSlide = 0;
    this.editing = false;
    this.setupStageScale();
    this.setupNavigation();
    this.setupEditing();
    this.showSlide(Number(location.hash.slice(1) || 1) - 1);
  }
  setupStageScale() {
    const resize = () => {
      const factor = Math.min(innerWidth / 1920, innerHeight / 1080);
      this.stage.style.transform = `translate(${(innerWidth-1920*factor)/2}px,${(innerHeight-1080*factor)/2}px) scale(${factor})`;
    };
    addEventListener('resize', resize);
    resize();
  }
  showSlide(index) {
    this.currentSlide = Math.max(0, Math.min(Number(index) || 0, this.slides.length-1));
    this.slides.forEach((slide, i) => {
      const active = i === this.currentSlide;
      slide.classList.toggle('active', active);
      slide.classList.toggle('visible', active);
      slide.inert = !active;
      slide.setAttribute('aria-hidden', String(!active));
    });
    document.getElementById('counter').textContent = `${this.currentSlide+1} / ${this.slides.length}`;
    document.getElementById('progress').style.width = `${(this.currentSlide+1)/this.slides.length*100}%`;
    history.replaceState(null, '', `#${this.currentSlide+1}`);
    const note = this.notes[this.currentSlide];
    document.getElementById('noteTitle').textContent = `P${String(this.currentSlide+1).padStart(2,'0')} ${note.title}`;
    document.getElementById('noteText').textContent = note.text;
    const links = document.getElementById('noteSources');
    links.replaceChildren(...note.sources.map(source => {
      const p=document.createElement('p'), a=document.createElement('a');
      a.href=source.url; a.textContent=source.title; a.target='_blank'; a.rel='noopener'; p.append(a); return p;
    }));
  }
  setupNavigation() {
    const prev=()=>this.showSlide(this.currentSlide-1), next=()=>this.showSlide(this.currentSlide+1);
    document.getElementById('prev').onclick=prev;
    document.getElementById('next').onclick=next;
    document.getElementById('contents').onclick=()=>document.getElementById('contentsDialog').showModal();
    document.getElementById('notes').onclick=()=>document.getElementById('notesDialog').showModal();
    document.getElementById('fullscreen').onclick=async()=>{
      try { if(document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch { this.status('可通过浏览器菜单进入全屏'); }
    };
    document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.close).close());
    document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{
      this.showSlide(Number(b.dataset.go)-1); document.getElementById('contentsDialog').close();
    });
    document.addEventListener('keydown', e=>{
      if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();this.save();return;}
      if(e.target.isContentEditable||e.target.matches('input,textarea,select')||document.querySelector('dialog[open]'))return;
      if(e.target.closest('button,a')&&[' ','Enter'].includes(e.key))return;
      if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();next();}
      else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();prev();}
      else if(e.key==='Home')this.showSlide(0);
      else if(e.key==='End')this.showSlide(this.slides.length-1);
      else if(e.key.toLowerCase()==='n')document.getElementById('notes').click();
      else if(e.key.toLowerCase()==='g')document.getElementById('contents').click();
      else if(e.key.toLowerCase()==='f')document.getElementById('fullscreen').click();
      else if(e.key.toLowerCase()==='e')this.toggleEdit();
    });
    let start=null, lastWheel=0;
    this.stage.addEventListener('touchstart',e=>{
      if(!e.target.closest('button,a,[contenteditable=true]'))start=[e.changedTouches[0].clientX,e.changedTouches[0].clientY];
    },{passive:true});
    this.stage.addEventListener('touchend',e=>{
      if(!start)return;const dx=e.changedTouches[0].clientX-start[0],dy=e.changedTouches[0].clientY-start[1];
      if(Math.abs(dx)>45&&Math.abs(dx)>Math.abs(dy))dx<0?next():prev();start=null;
    },{passive:true});
    this.stage.addEventListener('wheel',e=>{
      if(this.editing||document.querySelector('dialog[open]'))return;
      if(Math.abs(e.deltaY)>35&&Date.now()-lastWheel>700){lastWheel=Date.now();e.deltaY>0?next():prev();}
    },{passive:true});
    addEventListener('hashchange',()=>this.showSlide(Number(location.hash.slice(1))-1));
  }
  setupEditing() {
    this.editable=[...document.querySelectorAll('h1,.lead,.takeaway,.panel h3,.panel p,.editable')];
    const toggle=document.getElementById('editToggle'), zone=document.getElementById('editHotzone');
    let hide;
    [zone,toggle].forEach(el=>{
      el.addEventListener('mouseenter',()=>{clearTimeout(hide);toggle.classList.add('show');});
      el.addEventListener('mouseleave',()=>{hide=setTimeout(()=>{if(!this.editing)toggle.classList.remove('show');},400);});
    });
    toggle.onclick=()=>this.toggleEdit();zone.onclick=()=>this.toggleEdit();
    const saved=localStorage.getItem('llm-basics-v0.1-edits');
    if(saved){const edits=JSON.parse(saved);this.editable.forEach((el,i)=>{if(typeof edits[i]==='string')el.innerHTML=edits[i];});}
    this.editable.forEach(el=>el.addEventListener('input',()=>{
      localStorage.setItem('llm-basics-v0.1-edits',JSON.stringify(this.editable.map(x=>x.innerHTML)));
    }));
  }
  toggleEdit() {
    this.editing=!this.editing;
    document.body.classList.toggle('editing',this.editing);
    this.editable.forEach(el=>el.contentEditable=String(this.editing));
    document.getElementById('editToggle').classList.toggle('active',this.editing);
    document.getElementById('editToggle').setAttribute('aria-pressed',String(this.editing));
    this.status(this.editing?'可编辑文字；Ctrl+S 下载修改后的 HTML':'已退出编辑');
  }
  save() {
    const copy=document.documentElement.cloneNode(true);
    copy.querySelectorAll('[contenteditable]').forEach(el=>el.removeAttribute('contenteditable'));
    copy.querySelectorAll('dialog').forEach(el=>el.removeAttribute('open'));
    copy.querySelector('body').classList.remove('editing');
    copy.querySelector('#save-status').textContent='';
    copy.querySelector('#editToggle').classList.remove('active','show');
    copy.querySelector('#editToggle').setAttribute('aria-pressed','false');
    const url=URL.createObjectURL(new Blob(['<!doctype html>\n'+copy.outerHTML],{type:'text/html;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='llm-basics-slides-v0.1-edited.html';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);this.status('已下载 HTML；PDF 和 Markdown 讲稿需另行同步');
  }
  status(text){const el=document.getElementById('save-status');el.textContent=text;clearTimeout(this.statusTimer);this.statusTimer=setTimeout(()=>{el.textContent='';},4000);}
}
/* === OFFLINE DEMO 1 · fixed examples computed with tiktoken cl100k_base === */
const tokenExamples=JSON.parse(document.getElementById('tokenData').textContent);
document.querySelectorAll('[data-token]').forEach(button=>button.onclick=()=>{
  document.querySelectorAll('[data-token]').forEach(b=>{const active=b===button;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});
  const item=tokenExamples[Number(button.dataset.token)];
  document.getElementById('tokenText').textContent=item.text;
  document.getElementById('tokenCount').textContent=`${item.tokens.length} 个 Token`;
  document.getElementById('tokenPieces').replaceChildren(...item.tokens.map(t=>{
    const el=document.createElement('span');el.className='token';el.textContent=t.piece.replaceAll(' ','␠');
    const small=document.createElement('small');small.textContent=`ID ${t.id}`;el.append(small);return el;
  }));
});
/* === OFFLINE DEMO 2 · authored comparison, not a live model response === */
const promptExamples=[
  ['只有一句要求','帮我整理一下会议纪要。','输出可能只有一段概括；是否提取负责人、是否补写日期，都没有说清。'],
  ['任务、约束和格式','提取决策、负责人、截止时间；缺失字段写“未提供”；只根据会议原文，按表格输出。','决策：周五前完成 VPN 升级测试；负责人：小林；截止：本周五。第二项的负责人：未提供。'],
  ['再提供公司参考资料','补充：公司事项分类只有“故障、变更、咨询”。按这个列表分类，附对应原文。','事项类型：变更；依据：“周五前完成 VPN 升级测试”。分类有了来源，缺失的具体日期仍需补充。']
];
document.querySelectorAll('[data-prompt]').forEach(button=>button.onclick=()=>{
  document.querySelectorAll('[data-prompt]').forEach(b=>{const active=b===button;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});
  const item=promptExamples[Number(button.dataset.prompt)];
  document.getElementById('promptTitle').textContent=item[0];document.getElementById('promptText').textContent=item[1];document.getElementById('promptResult').textContent=item[2];
});
/* === OFFLINE DEMO 3 · tool requests and mock results, no business API calls === */
const toolExamples=[
  ['① 查知识库','输入：“在家连不上内网”\n检索命中：《远程接入配置指南》§3\n资料说：先检查 VPN 客户端登录状态，再查询服务状态。'],
  ['② 查询服务状态','模型提出：get_vpn_status(region="示例地区")\n示例工具返回：{"status":"degraded"}\n判断：服务端异常，需要报障。'],
  ['③ 提交工单请求','用户已要求报障，所需信息已收齐。\n模型提出：create_ticket(category="VPN", summary="远程接入失败")\n运行环境按授权范围执行请求。'],
  ['④ 核对工具结果','示例工具返回：\n{"ticket_id":"IT-DEMO-042","status":"created"}\n助手回复：已创建工单 IT-DEMO-042。\n这里是离线模拟，没有创建真实工单。']
];
document.querySelectorAll('[data-tool]').forEach(button=>button.onclick=()=>{
  document.querySelectorAll('[data-tool]').forEach(b=>{const active=b===button;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});
  const item=toolExamples[Number(button.dataset.tool)];
  document.getElementById('toolTitle').textContent=item[0];document.getElementById('toolResult').textContent=item[1];
});
window.deck=new SlidePresentation();
