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
    const saved=localStorage.getItem('llm-basics-v0.4-edits');
    if(saved){const edits=JSON.parse(saved);this.editable.forEach((el,i)=>{if(typeof edits[i]==='string')el.innerHTML=edits[i];});}
    this.editable.forEach(el=>el.addEventListener('input',()=>{
      localStorage.setItem('llm-basics-v0.4-edits',JSON.stringify(this.editable.map(x=>x.innerHTML)));
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
    const a=document.createElement('a');a.href=url;a.download='llm-basics-slides-v0.4-edited.html';a.click();
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
  ['The hotel bill was', '初始输入'],
  ['The hotel bill was<em> ¥</em>', '新增一个 Token，ID 72588，含前导空格'],
  ['The hotel bill was ¥<em>560</em>', '新增一个 Token，ID 17698'],
];
wireChoices('generate', i => {
  document.getElementById('generationText').innerHTML = generationSteps[i][0];
  document.getElementById('generationDetail').textContent = generationSteps[i][1];
});
const chatTrainingSample = [
  {role:'system', content:'住宿上限每晚 500 元，超标须事前审批。'},
  {role:'user', content:'一晚花了 560 元，能全额报销吗？'},
  {role:'assistant', content:'超出 60 元。全额报销要看事前审批记录。'}
];
document.getElementById('chatMessages').textContent =
  '[\n' + chatTrainingSample.map(({role, content}) =>
    `  {"role": ${JSON.stringify(role)},\n   "content": ${JSON.stringify(content)}}`
  ).join(',\n') + '\n]';
function renderChatPrompt(target, secondRound) {
  const messages = chatTrainingSample.slice(0, 2);
  if (secondRound) {
    messages.push(chatTrainingSample[2], {role:'user', content:'两晚共花了 1,120 元呢？'});
  }
  target.replaceChildren();
  messages.forEach(({role, content}, index) => {
    const message = document.createElement('span');
    message.textContent = '<|im_start|>' + role + '\n' + content + '<|im_end|>\n';
    if (index === 2) message.className = 'chat-added';
    target.append(message);
  });
  const generationStart = document.createElement('strong');
  generationStart.className = 'chat-added';
  generationStart.textContent = '<|im_start|>assistant';
  target.append(generationStart);
}
wireChoices('chat', i => renderChatPrompt(document.getElementById('chatRaw'), i === 1));
renderChatPrompt(document.getElementById('chatRawPrint'), true);
const toolExamples=[
 ['模型提出查询','模型 → 应用\nget_exchange_rate({base:"SGD", quote:"CNY", date:"2026-11-08"})'],
 ['应用执行并返回工具结果','应用执行查询 → 工具消息\n{"base":"SGD", "quote":"CNY", "rate":5.30,\n "date":"2026-11-08", "source":"DEMO", "status":"ok"}'],
 ['模型根据查询结果请求计算','模型 → 应用：calculate({expression:"120 * 5.30"})\n应用执行 → 工具消息：{"result":636, "status":"ok"}\n外部程序完成乘法，模型获得结果。'],
 ['模型根据工具结果回复用户','按 1 SGD = 5.30 CNY 换算，\n120 SGD 等于 636 CNY。\n汇率日期：2026-11-08。']
];
wireChoices('tool',i=>{document.getElementById('toolIndex').textContent=String(i+1).padStart(2,'0');document.getElementById('toolTitle').textContent=toolExamples[i][0];document.getElementById('toolResult').textContent=toolExamples[i][1]});
const reactExamples = [
  ['需要确定适用住宿标准和例外条件。','search_policy("住宿标准与超标审批")','§3.2 每晚 500 元。§3.3 超标须事前审批。','查取外币换算率。'],
  ['需要把 120 SGD 换算成人民币。','get_exchange_rate(SGD, CNY, "2026-11-08")','1 SGD = 5.30 CNY。','计算费用合计和住宿超出标准的金额。'],
  ['已知住宿 560 元和外币费用 120 SGD。','计算 120 × 5.30 + 560，再计算 560 − 500。','费用合计 1,196 元。住宿超标准 60 元。','检查是否提供了事前审批记录。'],
];
const approvalExamples = [
  ['已算出超标金额，需要确认例外条件。','检查用户随附的材料。','材料中没有提供事前审批记录。','交付核对说明，将审批标为待补，停止本轮。'],
  ['已算出超标金额，需要确认例外条件。','检查用户随附的材料。','材料中有一条事前审批记录，仍需核验。','查询审批系统，核验记录是否适用于本次行程与费用。'],
];
let reactStep = 0;
let approvalState = 0;
function renderReact() {
  const checkingApproval = reactStep === reactExamples.length;
  const result = checkingApproval ? approvalExamples[approvalState] : reactExamples[reactStep];
  document.getElementById('approvalChoices').hidden = !checkingApproval;
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
