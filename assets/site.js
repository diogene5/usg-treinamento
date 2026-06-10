(function(){
  'use strict';
  var d=document;

  /* ---------- storage helpers ---------- */
  function load(key,fallback){
    try{var v=localStorage.getItem(key);return v?JSON.parse(v):fallback}catch(e){return fallback}
  }
  function save(key,val){
    try{localStorage.setItem(key,JSON.stringify(val))}catch(e){}
  }

  /* ---------- progresso da trilha ---------- */
  var mods=Array.prototype.slice.call(d.querySelectorAll('details.module'));
  var total=mods.length;
  var done={};
  load('pocusV3.done',[]).forEach(function(id){done[id]=true});

  function doneCount(list){
    var n=0;list.forEach(function(m){if(done[m.id])n++});return n;
  }
  function renderProgress(){
    var n=doneCount(mods);
    var label=d.getElementById('progress-label');
    var fill=d.getElementById('progress-fill');
    if(label)label.textContent=n+'/'+total+' módulos';
    if(fill)fill.style.width=(total?Math.round(n/total*100):0)+'%';
    mods.forEach(function(m){
      m.classList.toggle('is-done',!!done[m.id]);
      var b=m.querySelector('.complete-btn');
      if(b){
        b.setAttribute('aria-pressed',done[m.id]?'true':'false');
        var lb=b.querySelector('.cb-label');
        if(lb)lb.textContent=done[m.id]?'Módulo concluído':'Marcar como concluído';
      }
    });
    Array.prototype.slice.call(d.querySelectorAll('.stage')).forEach(function(stage){
      var list=Array.prototype.slice.call(stage.querySelectorAll('details.module'));
      var out=stage.querySelector('[data-stage-count]');
      if(out)out.textContent=doneCount(list)+'/'+list.length;
    });
    var mLabel=d.getElementById('mnav-progress-label');
    if(mLabel)mLabel.textContent=n+'/'+total+' módulos concluídos';
    Array.prototype.slice.call(d.querySelectorAll('[data-mnav]')).forEach(function(a){
      a.classList.toggle('is-done',!!done[a.getAttribute('data-mnav')]);
    });
    var panel=d.getElementById('trilha-concluida');
    if(panel)panel.hidden=(n!==total);
  }
  d.addEventListener('click',function(e){
    var b=e.target.closest?e.target.closest('.complete-btn'):null;
    if(!b)return;
    var id=b.getAttribute('data-complete');
    if(done[id]){delete done[id]}else{done[id]=true}
    save('pocusV3.done',Object.keys(done));
    renderProgress();
  });
  var resetTrail=d.getElementById('reset-trail');
  if(resetTrail)resetTrail.addEventListener('click',function(){
    done={};save('pocusV3.done',[]);renderProgress();
    var top=d.getElementById('topo');
    if(top&&top.scrollIntoView)top.scrollIntoView();
  });
  renderProgress();

  /* ---------- checklists persistidos ---------- */
  var checks=load('pocusV3.checks',{});
  var boxes=Array.prototype.slice.call(d.querySelectorAll('.checklist input[type="checkbox"]'));
  function renderCounts(){
    Array.prototype.slice.call(d.querySelectorAll('.chk-count')).forEach(function(out){
      var g=out.getAttribute('data-count');
      var list=d.querySelector('.checklist[data-group="'+g+'"]');
      if(!list)return;
      var inputs=list.querySelectorAll('input[type="checkbox"]');
      var n=0;
      Array.prototype.slice.call(inputs).forEach(function(i){if(i.checked)n++});
      out.textContent='· '+n+'/'+inputs.length;
    });
  }
  boxes.forEach(function(box){
    var k=box.getAttribute('data-key');
    if(checks[k])box.checked=true;
    box.addEventListener('change',function(){
      if(box.checked){checks[k]=true}else{delete checks[k]}
      save('pocusV3.checks',checks);
      renderCounts();
    });
  });
  Array.prototype.slice.call(d.querySelectorAll('.chk-clear')).forEach(function(btn){
    btn.addEventListener('click',function(){
      var g=btn.getAttribute('data-clear');
      var list=d.querySelector('.checklist[data-group="'+g+'"]');
      if(!list)return;
      Array.prototype.slice.call(list.querySelectorAll('input[type="checkbox"]')).forEach(function(i){
        i.checked=false;delete checks[i.getAttribute('data-key')];
      });
      save('pocusV3.checks',checks);
      renderCounts();
    });
  });
  renderCounts();

  /* ---------- flashcards ---------- */
  Array.prototype.slice.call(d.querySelectorAll('.flashcard')).forEach(function(card){
    card.addEventListener('click',function(){
      var flipped=card.getAttribute('aria-pressed')==='true';
      card.setAttribute('aria-pressed',flipped?'false':'true');
    });
  });

  /* ---------- quiz ---------- */
  var quiz=d.getElementById('quiz');
  if(quiz){
    var questions=Array.prototype.slice.call(quiz.querySelectorAll('.quiz-q'));
    var answered=0,right=0;
    var result=d.getElementById('quiz-result');
    var score=d.getElementById('quiz-score');
    questions.forEach(function(q){
      var opts=Array.prototype.slice.call(q.querySelectorAll('.q-opt'));
      var fb=q.querySelector('.q-feedback');
      opts.forEach(function(opt){
        opt.addEventListener('click',function(){
          if(q.getAttribute('data-answered')==='1')return;
          q.setAttribute('data-answered','1');
          var ok=opt.getAttribute('data-correct')==='true';
          opts.forEach(function(o){
            o.disabled=true;
            if(o.getAttribute('data-correct')==='true')o.classList.add('is-right');
          });
          if(!ok)opt.classList.add('is-wrong');
          if(fb){
            fb.hidden=false;
            fb.classList.toggle('ok',ok);
            fb.textContent=(ok?'Correto. ':'Não exatamente. ')+(q.getAttribute('data-explain')||'');
          }
          answered++;if(ok)right++;
          if(answered===questions.length&&result&&score){
            score.textContent=right+' de '+questions.length+' corretas.';
            result.hidden=false;
          }
        });
      });
    });
    var resetQuiz=d.getElementById('quiz-reset');
    if(resetQuiz)resetQuiz.addEventListener('click',function(){
      answered=0;right=0;
      questions.forEach(function(q){
        q.removeAttribute('data-answered');
        Array.prototype.slice.call(q.querySelectorAll('.q-opt')).forEach(function(o){
          o.disabled=false;o.classList.remove('is-right','is-wrong');
        });
        var fb=q.querySelector('.q-feedback');
        if(fb){fb.hidden=true;fb.textContent='';fb.classList.remove('ok')}
      });
      if(result)result.hidden=true;
      var first=questions[0];
      if(first&&first.scrollIntoView)first.scrollIntoView();
    });
  }

  /* ---------- abrir módulo via âncora ---------- */
  function openFromHash(){
    var h=location.hash;
    if(!h||h.length<2)return;
    var el=d.getElementById(h.slice(1));
    if(!el)return;
    if(el.tagName==='DIALOG'){
      if(typeof el.showModal==='function'&&!el.open){
        el.showModal();
        d.body.classList.add('modal-open');
      }
      return;
    }
    if(el.tagName==='DETAILS')el.open=true;
    var parent=el.closest?el.closest('details.module'):null;
    if(parent)parent.open=true;
  }
  window.addEventListener('hashchange',openFromHash);
  openFromHash();

  /* ---------- V3.1 · tema claro/escuro/auto ---------- */
  var root=d.documentElement;
  var themeMeta=d.getElementById('meta-theme');
  var themeBtn=d.getElementById('theme-toggle');
  var themeLabels={auto:'automático',light:'claro',dark:'escuro'};
  var mqDark=null;
  try{mqDark=window.matchMedia('(prefers-color-scheme: dark)')}catch(e){}
  function currentTheme(){
    var t=root.getAttribute('data-theme');
    return (t==='light'||t==='dark')?t:'auto';
  }
  function themeIsDark(t){return t==='dark'||(t==='auto'&&!!(mqDark&&mqDark.matches))}
  function applyTheme(t){
    root.setAttribute('data-theme',t);
    try{localStorage.setItem('pocusV31.theme',t)}catch(e){}
    if(themeMeta)themeMeta.setAttribute('content',themeIsDark(t)?'#121a17':'#faf7f1');
    if(themeBtn)themeBtn.setAttribute('aria-label','Tema: '+themeLabels[t]+' (tocar para mudar)');
  }
  if(themeBtn){
    themeBtn.addEventListener('click',function(){
      var cur=currentTheme();
      applyTheme(cur==='auto'?'light':(cur==='light'?'dark':'auto'));
    });
  }
  function onSchemeChange(){applyTheme(currentTheme())}
  if(mqDark){
    if(mqDark.addEventListener)mqDark.addEventListener('change',onSchemeChange);
    else if(mqDark.addListener)mqDark.addListener(onSchemeChange);
  }
  applyTheme(currentTheme());

  /* ---------- V3.1 · painel plantão (dialog) ---------- */
  var plantao=d.getElementById('plantao');
  var plantaoBtn=d.getElementById('plantao-btn');
  var supportsDialog=!!(plantao&&typeof plantao.showModal==='function');
  if(plantao&&!supportsDialog)root.classList.add('no-dialog');
  if(plantao&&supportsDialog){
    plantao.addEventListener('close',function(){d.body.classList.remove('modal-open')});
    if(plantaoBtn){
      plantaoBtn.addEventListener('click',function(e){
        e.preventDefault();
        if(!plantao.open)plantao.showModal();
        d.body.classList.add('modal-open');
      });
    }
    var plantaoClose=plantao.querySelector('.plantao-close');
    if(plantaoClose)plantaoClose.addEventListener('click',function(){plantao.close()});
    Array.prototype.slice.call(plantao.querySelectorAll('a[href^="#"]')).forEach(function(a){
      a.addEventListener('click',function(){if(plantao.open)plantao.close()});
    });
  }

  /* ---------- V3.1 · copiar credencial ---------- */
  function legacyCopy(text){
    var ta=d.createElement('textarea');
    ta.value=text;
    ta.setAttribute('readonly','');
    ta.style.position='fixed';
    ta.style.left='-9999px';
    d.body.appendChild(ta);
    ta.select();
    try{d.execCommand('copy')}catch(e){}
    d.body.removeChild(ta);
  }
  Array.prototype.slice.call(d.querySelectorAll('.copy-btn')).forEach(function(btn){
    btn.addEventListener('click',function(){
      var text=btn.getAttribute('data-copy')||'';
      var flash=function(){
        btn.classList.add('copied');
        var lbl=btn.querySelector('.copy-label');
        if(lbl)lbl.textContent='copiado!';
        var status=btn.parentNode?btn.parentNode.querySelector('[data-copy-status]'):null;
        if(status)status.textContent='Senha copiada para a área de transferência.';
        setTimeout(function(){
          btn.classList.remove('copied');
          if(lbl)lbl.textContent='copiar senha';
          if(status)status.textContent='';
        },1800);
      };
      if(navigator.clipboard&&navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(flash,function(){legacyCopy(text);flash()});
      }else{
        legacyCopy(text);flash();
      }
    });
  });

  /* ---------- V3.1 · busca de módulos ---------- */
  var searchInput=d.getElementById('search-input');
  var searchClear=d.getElementById('search-clear');
  var searchCount=d.getElementById('search-count');
  var searchToggle=d.getElementById('search-toggle');
  var topbar=d.querySelector('.topbar');
  if(searchToggle&&topbar){
    searchToggle.addEventListener('click',function(){
      var open=topbar.classList.toggle('search-open');
      searchToggle.setAttribute('aria-expanded',open?'true':'false');
      if(open&&searchInput)searchInput.focus();
    });
  }
  function fold(s){
    return s.normalize?s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase():s.toLowerCase();
  }
  function clearMarks(scope){
    Array.prototype.slice.call(scope.querySelectorAll('mark.srch')).forEach(function(m){
      var parent=m.parentNode;
      if(!parent)return;
      parent.replaceChild(d.createTextNode(m.textContent),m);
      parent.normalize();
    });
  }
  /* destaca só em nós de texto, mapeando índices entre o texto normalizado (sem acento) e o original */
  function markNode(node,foldedQuery){
    var text=node.nodeValue;
    var folded='',map=[];
    for(var i=0;i<text.length;i++){
      var f=fold(text.charAt(i));
      for(var j=0;j<f.length;j++){folded+=f.charAt(j);map.push(i)}
    }
    var hits=[],pos=folded.indexOf(foldedQuery);
    while(pos!==-1){hits.push(pos);pos=folded.indexOf(foldedQuery,pos+foldedQuery.length)}
    if(!hits.length)return 0;
    var frag=d.createDocumentFragment(),last=0,made=0;
    hits.forEach(function(hp){
      var start=map[hp];
      var end=map[hp+foldedQuery.length-1]+1;
      if(start<last)return;
      frag.appendChild(d.createTextNode(text.slice(last,start)));
      var mk=d.createElement('mark');
      mk.className='srch';
      mk.textContent=text.slice(start,end);
      frag.appendChild(mk);
      last=end;made++;
    });
    frag.appendChild(d.createTextNode(text.slice(last)));
    node.parentNode.replaceChild(frag,node);
    return made;
  }
  function markIn(el,foldedQuery){
    var walker=d.createTreeWalker(el,NodeFilter.SHOW_TEXT,null,false);
    var nodes=[],n;
    while((n=walker.nextNode()))nodes.push(n);
    var count=0;
    nodes.forEach(function(node){
      var p=node.parentNode;
      if(!p)return;
      var tag=p.nodeName;
      if(tag==='SCRIPT'||tag==='STYLE'||tag==='MARK')return;
      count+=markNode(node,foldedQuery);
    });
    return count;
  }
  var searchState=null;
  function startSearchState(){
    if(searchState)return;
    searchState={open:{}};
    mods.forEach(function(m){searchState.open[m.id]=m.open});
  }
  function endSearch(){
    mods.forEach(function(m){
      clearMarks(m);
      m.hidden=false;
      if(searchState)m.open=!!searchState.open[m.id];
    });
    Array.prototype.slice.call(d.querySelectorAll('.stage')).forEach(function(s){s.hidden=false});
    searchState=null;
    d.body.classList.remove('searching');
    if(searchCount){searchCount.hidden=true;searchCount.textContent=''}
    if(searchClear)searchClear.hidden=true;
  }
  function runSearch(){
    var q=searchInput.value.trim();
    if(q.length<2){endSearch();return}
    startSearchState();
    var fq=fold(q),found=0;
    mods.forEach(function(m){
      clearMarks(m);
      var hits=markIn(m,fq);
      if(hits>0){m.hidden=false;m.open=true;found++}
      else{m.hidden=true}
    });
    Array.prototype.slice.call(d.querySelectorAll('.stage')).forEach(function(s){
      s.hidden=(s.querySelectorAll('details.module:not([hidden])').length===0);
    });
    d.body.classList.add('searching');
    if(searchCount){
      searchCount.hidden=false;
      searchCount.textContent=found===0?'Nenhum módulo encontrado':(found===1?'1 módulo encontrado':found+' módulos encontrados');
    }
    if(searchClear)searchClear.hidden=false;
  }
  if(searchInput){
    var searchTimer=null;
    searchInput.addEventListener('input',function(){
      clearTimeout(searchTimer);
      searchTimer=setTimeout(runSearch,160);
    });
    searchInput.addEventListener('keydown',function(e){
      if(e.key==='Escape'){searchInput.value='';endSearch()}
    });
  }
  if(searchClear)searchClear.addEventListener('click',function(){
    if(searchInput){searchInput.value='';searchInput.focus()}
    endSearch();
  });

  /* ---------- V3.1 · menu mobile ---------- */
  var mnav=d.getElementById('mnav');
  if(mnav){
    mnav.addEventListener('toggle',function(){
      d.body.classList.toggle('mnav-open',mnav.open);
    });
    Array.prototype.slice.call(mnav.querySelectorAll('a[href^="#"]')).forEach(function(a){
      a.addEventListener('click',function(){mnav.open=false});
    });
    d.addEventListener('keydown',function(e){
      if(e.key==='Escape'&&mnav.open)mnav.open=false;
    });
  }

  /* ---------- reveals (a classe só existe com JS; nada fica oculto sem JS) ---------- */
  var canReveal='IntersectionObserver' in window;
  var reduced=false;
  try{reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches}catch(e){}
  if(canReveal&&!reduced){
    var targets=Array.prototype.slice.call(d.querySelectorAll('.stage-head, details.module, .hero-figure, .done-inner'));
    targets.forEach(function(t){t.classList.add('reveal')});
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}
      });
    },{rootMargin:'0px 0px -7% 0px',threshold:.05});
    targets.forEach(function(t){io.observe(t)});
  }
})();
