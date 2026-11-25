import { origin, listPath, readTab } from './scan-page.js';

const form = document.querySelector('form');
const count = document.querySelector('#count');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const button = document.querySelector('#scan');
const watchButton = document.querySelector('#watch');
let watching = false;

function renderWatch(state) {
  watching = state.watching;
  watchButton.textContent = watching ? '停止自動刷新' : '開始自動刷新';
  watchButton.disabled = false;
}

async function scan() {
  button.disabled = true;
  results.replaceChildren();
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab?.url && new URL(tab.url);
    if (!url || url.origin !== origin || url.pathname !== listPath) {
      status.textContent = '請先在瀏覽器開啟一番賞的選箱列表。';
      return;
    }
    const result = await readTab(tab.id);
    if (!result?.boxes.length) {
      status.textContent = '目前頁面未讀到箱子。請查看網站畫面，載入選箱列表後再掃描。';
      return;
    }

    const target = count.valueAsNumber;
    localStorage.setItem('kuji-count', String(target));
    const key = result.pid && 'kuji-baseline:' + result.pid + ':' + result.page;
    const stored = key && localStorage.getItem(key);
    const baseline = stored == null ? null : Number(stored);
    const newest = result.boxes.reduce((max, box) => Math.max(max, Number(box.number)), 0);
    if (key) localStorage.setItem(key, String(Math.max(baseline ?? 0, newest)));

    const matches = result.boxes.filter(box => box.amount === target);
    matches.sort((a, b) => Number(b.number) - Number(a.number));
    for (const box of matches) {
      const row = document.createElement('li');
      const label = baseline != null && Number(box.number) > baseline ? '新箱 · ' : '';
      const waiting = box.waiting == null ? '' : ' · 等待 ' + box.waiting + ' 人';
      row.textContent = label + 'BOX-' + box.number + ' · 剩 ' + box.amount + ' 枚' + waiting;
      results.append(row);
    }
    const message = matches.length ? '符合的箱子共 ' + matches.length + ' 個。' : '目前沒有符合籤數的箱子。';
    status.textContent = key && baseline == null ? message + ' 已建立此商品頁基準。' : message;
  } catch {
    status.textContent = '讀取失敗。請回到已載入的選箱列表，再開啟擴充套件。';
  } finally {
    button.disabled = false;
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  scan();
});
const savedCount = Number(localStorage.getItem('kuji-count'));
if (Number.isInteger(savedCount) && savedCount > 0) count.value = savedCount;
scan();

watchButton.addEventListener('click', async () => {
  if (!watching && !form.reportValidity()) return;
  watchButton.disabled = true;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const state = await chrome.runtime.sendMessage({
      action: watching ? 'stop' : 'start', tabId: tab?.id, count: count.valueAsNumber,
    });
    if (state.error) throw new Error(state.error);
    if (state.watching) localStorage.setItem('kuji-count', String(count.valueAsNumber));
    renderWatch(state);
    status.textContent = state.watching
      ? '每隔 60–90 秒刷新，最多 10 分鐘。找到新箱時會嘗試開啟箱頁。'
      : '自動刷新已停止。';
  } catch (error) {
    status.textContent = error.message;
  } finally {
    watchButton.disabled = false;
  }
});
chrome.runtime.sendMessage({ action: 'status' }).then(renderWatch, () => {});
