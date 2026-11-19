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
    const saved=localStorage.getItem('llm-basics-v0.2-edits');
    if(saved){const edits=JSON.parse(saved);this.editable.forEach((el,i)=>{if(typeof edits[i]==='string')el.innerHTML=edits[i];});}
    this.editable.forEach(el=>el.addEventListener('input',()=>{
      localStorage.setItem('llm-basics-v0.2-edits',JSON.stringify(this.editable.map(x=>x.innerHTML)));
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
    const a=document.createElement('a');a.href=url;a.download='llm-basics-slides-v0.2-edited.html';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);this.status('已下载 HTML；PDF 和 Markdown 讲稿需另行同步');
  }
  status(text){const el=document.getElementById('save-status');el.textContent=text;clearTimeout(this.statusTimer);this.statusTimer=setTimeout(()=>{el.textContent='';},4000);}
}
/* Offline teaching interactions. No API calls or business operations. */
const tokenExamples=JSON.parse(document.getElementById('tokenData').textContent);
function wireChoices(attr,render){const buttons=[...document.querySelectorAll(`[data-${attr}]`)];buttons.forEach(button=>button.onclick=()=>{buttons.forEach(b=>{const active=b===button;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active))});render(Number(button.dataset[attr]))});if(buttons.length)render(0)}
wireChoices('token',i=>{const item=tokenExamples[i];document.getElementById('tokenText').textContent=item.text;document.getElementById('tokenCount').textContent=`${item.tokens.length} 个 Token`;document.getElementById('tokenPieces').replaceChildren(...item.tokens.map(t=>{const el=document.createElement('span');el.className='token';el.textContent=t.piece.replaceAll(' ','␠');const id=document.createElement('small');id.textContent=`ID ${t.id}`;el.append(id);return el}))});
wireChoices('generate',i=>{document.getElementById('generationText').innerHTML=['今天的天气','今天的天气<em>很好</em>','今天的天气很好<em>，适合出门。</em>'][i]});
wireChoices('chat',i=>{const messages=[{role:'system',content:'按提供的制度回答。'},{role:'user',content:'住宿上限每晚 500 元？'}];if(i)messages.push({role:'assistant',content:'按提供制度，是的。'},{role:'user',content:'那两晚呢？'});document.getElementById('chatMessages').textContent='[\n'+messages.map(m=>'  '+JSON.stringify(m)).join(',\n')+'\n]';document.getElementById('chatRaw').textContent=messages.map(m=>`<|im_start|>${m.role}\n${m.content}<|im_end|>`).join('\n')+'\n<|im_start|>assistant\n'});
const toolExamples=[
 ['模型提出查询','模型 → 应用\nget_exchange_rate({base:"SGD", quote:"CNY", date:"2026-11-01"})\n\n此时只产生调用请求，尚未取得查询结果。'],
 ['应用执行并返回工具结果','应用执行查询 → 工具消息\n{"base":"SGD", "quote":"CNY", "rate":5.30,\n "date":"2026-11-01", "source":"DEMO", "status":"ok"}\n这是预设教学响应，不是实时汇率。'],
 ['模型根据查询结果请求计算','模型 → 应用：calculate({expression:"120 * 5.30"})\n应用执行 → 工具消息：{"result":636, "status":"ok"}\n外部程序完成乘法，模型获得结果。'],
 ['模型根据工具结果回复用户','按示例汇率 1 SGD = 5.30 CNY，\n120 SGD 换算为 636 CNY。\n汇率日期：2026-11-01；来源：教学数据 DEMO。']
];
wireChoices('tool',i=>{document.getElementById('toolIndex').textContent=String(i+1).padStart(2,'0');document.getElementById('toolTitle').textContent=toolExamples[i][0];document.getElementById('toolResult').textContent=toolExamples[i][1]});
const reactExamples=[
 ['需要确定适用住宿标准与例外条件。','search_policy("住宿标准与超标审批")','§3.2：500 元/晚；§3.3：超标需事前审批。','继续取得外币换算率，并检查审批材料是否提供。'],
 ['需要把 120 SGD 换算成人民币。','get_exchange_rate(SGD, CNY, "2026-11-01")','DEMO：1 SGD = 5.30 CNY。','调用计算工具汇总费用并计算超标金额。'],
 ['已知住宿 560 CNY，另有 120 SGD 的费用。','calculate("120 * 5.30 + 560")','费用合计 1,196 CNY；住宿超标准 60 CNY。','检查审批记录；没有记录就标明待补充。'],
 ['材料中没有提供事前审批，不能推定全额获批。','按报告模板整理结论、依据和缺口。','合计 1,196 CNY；住宿超标 60 CNY；审批记录待补。','交付核对说明。待补事项保留为未完成，停止本轮。']
];
wireChoices('react',i=>{['reactReason','reactAction','reactObservation','reactNext'].forEach((id,j)=>document.getElementById(id).textContent=reactExamples[i][j])});
document.querySelector('[data-chat="1"]').click();
window.deck=new SlidePresentation();
