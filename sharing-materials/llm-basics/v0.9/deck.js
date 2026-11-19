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
    this.editable=[...document.querySelectorAll('h1,.lead,.takeaway,.text-block h3,.text-block p,.editable')];
    const toggle=document.getElementById('editToggle'), zone=document.getElementById('editHotzone');
    let hide;
    [zone,toggle].forEach(el=>{
      el.addEventListener('mouseenter',()=>{clearTimeout(hide);toggle.classList.add('show');});
      el.addEventListener('mouseleave',()=>{hide=setTimeout(()=>{if(!this.editing)toggle.classList.remove('show');},400);});
    });
    toggle.onclick=()=>this.toggleEdit();zone.onclick=()=>this.toggleEdit();
    const saved=localStorage.getItem('llm-basics-v0.9-edits');
    if(saved){const edits=JSON.parse(saved);this.editable.forEach((el,i)=>{if(typeof edits[i]==='string')el.innerHTML=edits[i];});}
    this.editable.forEach(el=>el.addEventListener('input',()=>{
      localStorage.setItem('llm-basics-v0.9-edits',JSON.stringify(this.editable.map(x=>x.innerHTML)));
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
    const a=document.createElement('a');a.href=url;a.download='llm-basics-slides-v0.9-edited.html';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);this.status('已下载 HTML；PDF 和 Markdown 讲稿需另行同步');
  }
  status(text){const el=document.getElementById('save-status');el.textContent=text;clearTimeout(this.statusTimer);this.statusTimer=setTimeout(()=>{el.textContent='';},4000);}
}
/* Offline teaching interactions. No API calls or business operations. */
const tokenExamples=JSON.parse(document.getElementById('tokenData').textContent);
function wireChoices(attr, render) {
  const buttons = [...document.querySelectorAll(`[data-${attr}]`)];
  const select = index => {
    buttons.forEach((button, i) => {
      button.classList.toggle('selected', i === index);
      button.setAttribute('aria-pressed', String(i === index));
    });
    render(index);
  };
  buttons.forEach((button, index) => button.onclick = () => select(index));
  if (buttons.length) select(0);
}
wireChoices('token',i=>{const item=tokenExamples[i];document.getElementById('tokenText').textContent=item.text;document.getElementById('tokenCount').textContent=`${item.tokens.length} 个 Token`;document.getElementById('tokenPieces').replaceChildren(...item.tokens.map(t=>{const el=document.createElement('span');el.className='token';el.textContent=t.piece.replaceAll(' ','␠');const id=document.createElement('small');id.textContent=`ID ${t.id}`;el.append(id);return el}))});
const generationSteps = [
  ['The claim is', '初始输入'],
  ['The claim is<em> pending</em>', '新增一个 Token，ID 15280，含前导空格'],
  ['The claim is pending<em>.</em>', '新增一个 Token，ID 13'],
  ['The claim is pending. <em class="generation-eos">&lt;|im_end|&gt;</em>', '结束 Token，ID 151645。推理服务停止生成。'],
];
wireChoices('generate', i => {
  document.getElementById('generationText').innerHTML = generationSteps[i][0];
  document.getElementById('generationDetail').textContent = generationSteps[i][1];
});
const chatPrompts = [...document.querySelectorAll('[data-chat-prompt]')];
wireChoices('chat', i => chatPrompts.forEach((prompt, index) => {
  prompt.hidden = index !== i;
}));
const toolExamples=[
 ['模型提出调用','模型发给应用\nconvert_currency({amount:120, base:"SGD",\n                  quote:"CNY", date:"2026-11-08"})'],
 ['应用执行并回传','工具返回给模型\n{"base":"SGD", "quote":"CNY", "rate":5.30,\n "amount":120, "converted_amount":636,\n "date":"2026-11-08", "status":"ok"}'],
 ['模型根据回执回复用户','按 1 SGD = 5.30 CNY 换算，120 SGD 等于 636 CNY。\n汇率日期为 2026-11-08。']
];
wireChoices('tool', i => {
  document.getElementById('toolTitle').textContent = toolExamples[i][0];
  document.getElementById('toolResult').textContent = toolExamples[i][1];
});
const reactExamples = [
  ['提交前要核对住宿标准和例外条件。','search_policy("住宿标准与超标审批")','§3.2 每晚 500 元。§3.3 超标须事前审批。','把 120 SGD 换算成人民币。'],
  ['合计费用需要把币种统一。','convert_currency({amount:120, base:"SGD", quote:"CNY", date:"2026-11-08"})','1 SGD = 5.30 CNY，换算结果 636 CNY。','核算费用合计和住宿超标金额。'],
  ['外币已经换算为 636 元，住宿是 560 元。','用计算工具核算 636 + 560 及 560 − 500。','费用合计 1,196 元。住宿超标 60 元。','检查是否有事前审批记录。'],
];
const approvalExamples = [
  ['住宿超标，需要确认事前审批。','检查用户随附的材料。','材料中缺少事前审批记录。','把申请保存为草稿，向用户索取审批记录。'],
  ['住宿超标，需要核验随附的审批记录。','查询审批系统，核对行程和费用。','本例的审批记录核验通过，适用于这笔住宿。','调用提交工具，等待报销系统回执。'],
];
const submissionExamples = [
  ['缺少事前审批，申请处于待补状态。','保留已核对的金额和申请草稿，请用户补件。','当前状态为待补，申请尚未提交。','收到材料后继续核验。'],
  ['审批已核验，材料符合本例的提交条件。','调用 submit_expense_claim 提交报销申请。','报销系统回执显示已提交，申请单号 DEMO-018。','把申请单号交给用户，结束本轮。'],
];
let reactStep = 0;
let approvalState = 0;
function renderReact() {
  const steps = [...reactExamples, approvalExamples[approvalState], submissionExamples[approvalState]];
  const result = steps[reactStep];
  document.getElementById('approvalChoices').hidden = reactStep < reactExamples.length;
  ['reactReason','reactAction','reactObservation','reactNext'].forEach((id, index) => {
    document.getElementById(id).textContent = result[index];
  });
}
wireChoices('react', i => {
  reactStep = i;
  renderReact();
});
wireChoices('approval', i => {
  approvalState = i;
  renderReact();
});
window.deck = new SlidePresentation();
