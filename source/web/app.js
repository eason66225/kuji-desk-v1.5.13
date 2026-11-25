'use strict';
const $ = selector => document.querySelector(selector);
const token = location.hash.slice(1) || sessionStorage.getItem('kujiSession') || '';
if(token)sessionStorage.setItem('kujiSession',token);
history.replaceState(null, '', location.pathname);
let state = [], audio, pendingReset, pendingRequeue, toastTimer, polling = false;
const busy = new Set(), notified = new Set();
const colors = {A:'#8bb9ff', B:'#d7f896', C:'#ffbe84'};
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = value => value ? new Date(value).toLocaleTimeString('zh-TW',{hour12:false}) : '—';
const duration = value => value == null ? '—' : `${value} ms`;
function config(){return Object.fromEntries(['url','count','minSeconds','maxSeconds'].map(k=>[k,k==='url'?$('#'+k).value:Number($('#'+k).value)]));}
function toast(message){$('#toast').textContent=message;$('#toast').style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').style.display='none',6000);}
async function api(path, data){
  const response=await fetch('/api/'+path,{method:data?'POST':'GET',headers:{Authorization:'Bearer '+token,...(data?{'Content-Type':'application/json'}:{})},body:data?JSON.stringify(data):undefined});
  const text=await response.text();let result;
  try{result=JSON.parse(text);}catch{throw new Error(response.status===401?'連線憑證已失效，請使用程式視窗列出的完整網址重新開啟。':'無法連接本機程式。');}
  if(!response.ok)throw new Error(result.error||'操作失敗');return result;
}
function beep(id){
  if(!audio||audio.state!=='running')return;
  const frequency={A:660,B:880,C:1100}[id];
  for(let i=0;i<3;i++){const o=audio.createOscillator(),g=audio.createGain();o.connect(g);g.connect(audio.destination);o.frequency.value=frequency;g.gain.value=.12;const t=audio.currentTime+i*.38;o.start(t);o.stop(t+.2);}
}
$('#sound').onclick=async()=>{try{audio||=new AudioContext();await audio.resume();beep('B');$('#soundState').textContent='已啟用 · A/B/C 使用不同音高';for(const a of state)if(a.phase==='ready')beep(a.id);}catch(e){toast(e.message);}};
function inventoryPanel(a){
  const stock=a.inventory||{};
  const isApi = stock.source === 'api';
  return `<section class="inventory-panel"><div class="inventory-heading"><span>剩餘籤數</span><strong class="inventory-amount">${stock.remaining??'—'}<small>${stock.total ? ' / ' + stock.total + ' 枚' : ''}</small></strong></div><div class="prize-grid">${(stock.prizes||[]).map(p=>`<div class="prize ${p.remaining===0?'sold':''}"><span>${esc(p.label)}</span><strong>${p.remaining}<small> / ${p.total}</small></strong></div>`).join('')||'<p>進入箱子後，讀取網站各賞剩餘數量。</p>'}</div>${stock.lastOneListed?'<div class="last-one">Last One：網站有列出，未提供數量</div>':''}<div class="stock-foot"><small>${stock.readAt?(isApi?'已更新 '+fmt(stock.readAt):'頁面讀取 '+fmt(stock.readAt)):'尚未讀取箱子資訊'}<br>每 3 分鐘自動更新；鍵盤按下 F5 亦可重新整理。</small></div></section>`;
}
function card(a){
  const m=a.metrics||{}, active=busy.has(a.id);
  return `<article class="account" data-id="${a.id}" data-phase="${esc(a.phase)}"><div class="account-top"><div class="account-name"><span class="avatar">${a.id}</span><div><strong>${esc(a.label)}</strong><small>獨立 Chrome 設定檔 · ${a.id}${a.hasSession ? (a.opened ? ' · 已連線' : ' · Session 有效') : ''}</small></div></div><span class="badge ${esc(a.phase)}">${esc(a.phaseLabel)}</span></div><div class="box-area"><div><small>目前鎖定箱子</small><span class="box-id">${a.target?'BOX-'+(a.target.seq!=null?String(a.target.seq).padStart(5,'0'):esc((a.target.id||'').slice(0,5))):'等待新箱'}</span></div><div class="rank"><small>${a.queueAhead!=null?'前方還有':'網站順位'}</small><strong>${a.phase==='ready'?'輪到你！':(a.queueAhead!=null?a.queueAhead+' 人':a.queueNo??'—')}</strong></div></div><p class="note">${esc(a.note)}</p>${inventoryPanel(a)}<div class="timings"><div>最近資料檢查<b>${fmt(m.lastCheckedAt)}</b></div><div>最近請求耗時<b>${duration(m.requestMs)}</b></div><div>發現 → 觸發排隊<b>${duration(m.submittedAt&&m.foundAt?m.submittedAt-m.foundAt:null)}</b></div><div>最後順位變更<b>${fmt(m.lastQueueAt)}</b></div></div><div class="actions"><button data-action="open" ${active?'disabled':''}>${a.opened?'切回專用視窗 ↗':(a.hasSession?'開啟視窗 ↗':'開啟視窗／登入 ↗')}</button><button class="primary" data-action="start" ${!a.canStart||active?'disabled':''}>開始監看</button><button data-action="navigate" ${!a.canStart||active?'disabled':''}>開啟選箱列表</button><button class="subtle" data-action="stop" ${!a.canStop||active?'disabled':''}>停止監看</button></div><div class="actions"><button data-action="inspect" ${!a.opened||active?'disabled':''}>重新查看／修復狀態</button><button data-action="restart" ${active?'disabled':''}>重啟此帳號視窗</button></div><button class="requeue" data-action="requeue" ${!a.canRequeue||active?'disabled':''}>離開本箱並重新監看 ↻</button><div class="minor-actions"><button data-action="label" ${active?'disabled':''}>編輯帳號名稱</button><button data-action="reset" ${!a.canReset||active?'disabled':''}>結束本次任務</button></div><div class="event-list">${a.events.length?a.events.slice(-2).map(e=>`<div><time>${fmt(e.at)}</time>${esc(e.message)}</div>`).join(''):'<div>尚未開始。先開啟此帳號的專用視窗。</div>'}</div></article>`;
}
function render(){
  $('#accounts').innerHTML=state.map(card).join('');
  $('#watchCount').textContent=state.filter(a=>a.phase==='watching').length;
  $('#queueCount').textContent=state.filter(a=>a.phase==='waiting').length;
  const ready=state.filter(a=>a.phase==='ready');$('#readyCount').textContent=ready.length;
  document.title=ready.length?`🔔 ${ready.map(a=>a.label).join('、')} 輪到了｜Kuji Desk`:'Kuji Desk · 三帳號總控';
  $('#startAll').disabled=!state.some(a=>a.canStart&&!busy.has(a.id));
  $('#stopAll').disabled=!state.some(a=>a.canStop&&!busy.has(a.id));
  for(const a of ready){const key=a.id+':'+a.metrics.readyAt;if(!notified.has(key)){notified.add(key);beep(a.id);toast(`${a.label} 輪到你了！請切回專用視窗。`);}}
}
async function refresh(){if(polling)return;polling=true;try{const result=await api('state');state=result.accounts;render();$('#connection').textContent='本機總控已連線';$('#connectionDot').style.background='var(--lime)';$('#footerState').textContent='v'+result.version+' · 最新狀態 '+fmt(Date.now());}catch(e){$('#connection').textContent='本機程式已離線';$('#connectionDot').style.background='#ffbe84';$('#footerState').textContent=e.message;$('#startAll').disabled=true;$('#stopAll').disabled=true;for(const b of document.querySelectorAll('[data-action]'))b.disabled=true;}finally{polling=false;}}
async function action(id, command, extra={}){
  if(busy.has(id))return;busy.add(id);render();
  try{
    if(command==='api_inventory'){
      try{
        await api('action',{id,action:'api_inventory',...config(),...extra});
      }catch(err){
        await api('action',{id,action:'inventory',...config(),...extra});
      }
    }else{
      await api('action',{id,action:command,...config(),...extra});
    }
  }catch(e){toast(`${state.find(a=>a.id===id)?.label||id}：${e.message}`);}
  finally{busy.delete(id);await refresh();}
}
$('#accounts').onclick=event=>{const b=event.target.closest('[data-action]');if(!b||b.disabled)return;const id=b.closest('[data-id]').dataset.id, command=b.dataset.action;
  if(command==='label'){const value=prompt('這個帳號要顯示什麼名稱？',state.find(a=>a.id===id).label);if(value!==null)action(id,'label',{label:value});}
  else if(command==='restart'){if(confirm('重啟此帳號視窗可能中斷此帳號隊伍，登入資料保留，另外兩個帳號不變。繼續？'))action(id,command,{confirmed:true});}
  else if(command==='requeue'){pendingRequeue=id;$('#requeueDialog').showModal();}
  else if(command==='reset'){pendingReset=id;$('#resetDialog').showModal();}
  else action(id,command);
};
$('#cancelRequeue').onclick=()=>$('#requeueDialog').close();
$('#confirmRequeue').onclick=()=>{$('#requeueDialog').close();action(pendingRequeue,'requeue',{confirmed:true});};
$('#cancelReset').onclick=()=>$('#resetDialog').close();
$('#confirmReset').onclick=()=>{$('#resetDialog').close();action(pendingReset,'reset',{confirmed:true});};
$('#startAll').onclick=()=>Promise.all(state.filter(a=>a.canStart).map(a=>action(a.id,'start')));
$('#stopAll').onclick=()=>Promise.all(state.filter(a=>a.canStop).map(a=>action(a.id,'stop')));
for(const key of ['url','count','minSeconds','maxSeconds']){
  const saved=localStorage.getItem('kuji-setting-'+key);if(saved!==null)$('#'+key).value=saved;
  $('#'+key).addEventListener('change',()=>localStorage.setItem('kuji-setting-'+key,$('#'+key).value));
}
setInterval(()=>$('#time').textContent=fmt(Date.now()),1000);
setInterval(refresh,1000);refresh();
