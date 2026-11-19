(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const stage = document.getElementById('stage');
  const notes = JSON.parse(document.getElementById('speakerNotes').textContent);
  let index = 0, editing = false;
  const panel = document.getElementById('notesPanel');
  const help = document.getElementById('helpPanel');
  const input = document.getElementById('pageInput');
  function resize() {
    const scale = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = `translate(${(innerWidth - 1920 * scale) / 2}px, ${(innerHeight - 1080 * scale) / 2}px) scale(${scale})`;
  }
  function groups() {
    return [...new Set([...slides[index].querySelectorAll('[data-step]')].map(el => Number(el.dataset.step)))].sort((a,b) => a-b);
  }
  function syncNotes() {
    document.getElementById('noteTitle').textContent = `${index + 1}. ${notes[index].title}`;
    document.getElementById('noteText').textContent = notes[index].text;
    const sources = document.getElementById('noteSources');
    sources.replaceChildren();
    notes[index].sources.forEach(source => {
      const a = document.createElement('a');
      a.href = source.href; a.textContent = source.title;
      a.target = '_blank'; a.rel = 'noopener'; sources.append(a);
    });
  }
  function go(page, expand = false) {
    index = Math.min(slides.length - 1, Math.max(0, Number(page) - 1 || 0));
    slides.forEach((slide, i) => {
      slide.classList.toggle('active', i === index);
      slide.setAttribute('aria-hidden', String(i !== index));
      slide.inert = i !== index;
    });
    if (expand) revealAll();
    input.value = index + 1;
    document.getElementById('progress').style.width = `${(index + 1) / slides.length * 100}%`;
    document.title = `${String(index+1).padStart(2,'0')} · ${notes[index].title} | 本体与 Agent`;
    history.replaceState(null, '', `#${index+1}`);
    syncNotes();
  }
  function revealAll() { slides[index].querySelectorAll('.reveal').forEach(el => el.classList.add('shown')); }
  function next() {
    const hidden = groups().find(step => [...slides[index].querySelectorAll(`[data-step="${step}"]`)].some(el => !el.classList.contains('shown')));
    if (hidden !== undefined) slides[index].querySelectorAll(`[data-step="${hidden}"]`).forEach(el => el.classList.add('shown'));
    else go(index + 2);
  }
  function prev() {
    const shown = groups().filter(step => [...slides[index].querySelectorAll(`[data-step="${step}"]`)].some(el => el.classList.contains('shown')));
    if (shown.length) slides[index].querySelectorAll(`[data-step="${shown.at(-1)}"]`).forEach(el => el.classList.remove('shown'));
    else if (index > 0) go(index, true);
  }
  function toast(text) {
    const el = document.getElementById('toast'); el.textContent = text; el.hidden = false;
    clearTimeout(toast.timer); toast.timer = setTimeout(() => {el.hidden = true;}, 2200);
  }
  function edit() {
    editing = !editing;
    document.body.classList.toggle('editing', editing);
    document.querySelectorAll('.edit-text').forEach(el => {
      el.contentEditable = String(editing); el.spellcheck = false;
    });
    document.getElementById('editButton').setAttribute('aria-pressed', String(editing));
    toast(editing ? '正文编辑已开启，Ctrl+S 下载修改后的 HTML' : '正文编辑已关闭');
  }
  function save() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelector('body').classList.remove('editing', 'capture', 'all-revealed');
    clone.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
    clone.querySelectorAll('#notesPanel,#helpPanel,#toast').forEach(el => el.setAttribute('hidden',''));
    clone.querySelector('#editButton').setAttribute('aria-pressed','false');
    const url = URL.createObjectURL(new Blob(['<!doctype html>\n' + clone.outerHTML], {type:'text/html;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'ontology-agent-edited.html'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('已下载 HTML，保存后的文字可离线打开');
  }
  async function fullscreen() {
    try { if(document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { toast('请使用浏览器菜单进入全屏'); }
  }
  document.getElementById('prevButton').onclick = prev;
  document.getElementById('nextButton').onclick = next;
  document.getElementById('contentsButton').onclick = () => go(2);
  document.getElementById('expandButton').onclick = revealAll;
  document.getElementById('notesButton').onclick = () => { panel.hidden = !panel.hidden; };
  document.getElementById('closeNotes').onclick = () => { panel.hidden = true; };
  document.getElementById('helpButton').onclick = () => { help.hidden = !help.hidden; };
  document.getElementById('closeHelp').onclick = () => { help.hidden = true; };
  document.getElementById('editButton').onclick = edit;
  document.getElementById('saveButton').onclick = save;
  document.getElementById('fullscreenButton').onclick = fullscreen;
  input.onchange = () => go(input.value);
  document.querySelectorAll('[data-go]').forEach(el => el.addEventListener('click', e => {
    if(editing && e.target.closest('.edit-text')) return;
    e.preventDefault(); go(el.dataset.go);
  }));
  const views = JSON.parse(document.getElementById('viewData').textContent);
  document.querySelectorAll('[data-view]').forEach(button => button.onclick = () => {
    const n = Number(button.dataset.view);
    document.querySelectorAll('[data-view]').forEach(el => el.setAttribute('aria-pressed',String(el === button)));
    document.querySelectorAll('#viewsGraph [data-view-node]').forEach(el => el.classList.toggle('faint', !views[n].nodes.includes(el.dataset.viewNode)));
  });
  document.querySelectorAll('[data-path]').forEach(button => button.onclick = () => {
    const choice = button.dataset.path;
    document.querySelectorAll('[data-path]').forEach(el => el.setAttribute('aria-pressed',String(el === button)));
    document.querySelectorAll('[data-path-group]').forEach(el => {
      el.classList.toggle('faint', choice !== 'all' && el.dataset.pathGroup !== choice);
    });
  });
  document.querySelectorAll('.qa details').forEach(detail => detail.addEventListener('toggle', () => {
    if(detail.id === 'maintenanceQuestion') document.getElementById('maintenanceDiagram').classList.toggle('visible',detail.open);
  }));
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {e.preventDefault(); save(); return;}
    if (e.key === 'Escape') {panel.hidden=true;help.hidden=true;if(editing) edit();return;}
    if(e.target.closest('input,textarea,[contenteditable="true"]') || editing || e.ctrlKey || e.metaKey || e.altKey) return;
    if(e.target.closest('button,summary,a') && [' ','Enter'].includes(e.key)) return;
    const key=e.key.toLowerCase();
    if(['arrowright','arrowdown',' ','pagedown'].includes(key)){e.preventDefault();next();}
    else if(['arrowleft','arrowup','pageup'].includes(key)){e.preventDefault();prev();}
    else if(key==='a') revealAll();
    else if(key==='n') panel.hidden=!panel.hidden;
    else if(key==='e') edit();
    else if(key==='f') fullscreen();
    else if(key==='g') go(2);
    else if(key==='home') go(1);
    else if(key==='end') go(slides.length,true);
    else if(key==='?') help.hidden=!help.hidden;
  });
  let touchStart;
  document.getElementById('viewport').addEventListener('touchstart', e => {
    if(!e.target.closest('button,a,summary,[contenteditable="true"]')) touchStart={x:e.changedTouches[0].clientX,y:e.changedTouches[0].clientY};
  },{passive:true});
  document.getElementById('viewport').addEventListener('touchend', e => {
    if(!touchStart) return;
    const dx=e.changedTouches[0].clientX-touchStart.x,dy=e.changedTouches[0].clientY-touchStart.y;
    if(Math.abs(dx)>60 && Math.abs(dx)>Math.abs(dy)*1.5) dx<0 ? next() : prev();
    touchStart=null;
  },{passive:true});
  addEventListener('resize',resize);
  addEventListener('hashchange',()=>go(location.hash.slice(1)));
  let printOpen=[];
  addEventListener('beforeprint',()=>{
    printOpen=[...document.querySelectorAll('details')].filter(el=>el.open);
    document.querySelectorAll('details').forEach(el=>{el.open=true;});
  });
  addEventListener('afterprint',()=>{
    document.querySelectorAll('details').forEach(el=>{el.open=printOpen.includes(el);});
  });
  window.deck={go,revealAll,next,prev,get current(){return index+1;},get count(){return slides.length;}};
  resize();go(location.hash.slice(1));
})();
