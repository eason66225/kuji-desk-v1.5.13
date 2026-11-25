import { origin, listPath, readTab } from './scan-page.js';

const alarmName = 'kuji-box-refresh';
const durationMs = 10 * 60 * 1000;
let pending = Promise.resolve();

function enqueue(task) {
  const next = pending.then(task);
  pending = next.catch(() => {});
  return next;
}

async function currentWatch() {
  return (await chrome.storage.session.get('watch')).watch;
}

async function stopWatch(state) {
  const watch = await currentWatch();
  await chrome.storage.session.remove('watch');
  await chrome.alarms.clear(alarmName);
  if (!watch) return;
  await chrome.action.setBadgeText({ tabId: watch.tabId, text: ['found', 'opened'].includes(state) ? '新' : '' }).catch(() => {});
  const titles = {
    found: '找到新箱，請在目前頁面選取箱子。',
    opened: '已開啟新箱。請在網站確認排隊。',
    blocked: '自動刷新已停止。請先查看網站畫面。',
    expired: '本次自動刷新已結束。',
  };
  await chrome.action.setTitle({ tabId: watch.tabId, title: titles[state] ?? '一番賞選箱掃描' }).catch(() => {});
}

async function scheduleRefresh(expires) {
  const nextRefresh = Date.now() + 60_000 + Math.random() * 30_000;
  await chrome.alarms.create(alarmName, { when: Math.min(nextRefresh, expires) });
}

async function startWatch(tabId, count) {
  if (!Number.isInteger(tabId) || !Number.isInteger(count) || count < 1) throw new Error('請輸入目標籤數。');
  const tab = await chrome.tabs.get(tabId);
  const url = tab.url && new URL(tab.url);
  if (tab.status !== 'complete' || !url || url.origin !== origin || url.pathname !== listPath) {
    throw new Error('請先開啟已載入的選箱列表。');
  }
  const result = await readTab(tabId, { url: url.href });
  if (!result?.boxes.length) throw new Error('請先確認頁面已顯示正常的箱子列表。');
  await stopWatch();
  const baseline = Math.max(...result.boxes.map(box => Number(box.number)));
  const expires = Date.now() + durationMs;
  await chrome.storage.session.set({ watch: { tabId, url: url.href, count, baseline, expires } });
  await scheduleRefresh(expires);
  await chrome.action.setBadgeText({ tabId, text: '看' });
  await chrome.action.setTitle({ tabId, title: '自動刷新中：每隔 60–90 秒，最多 10 分鐘。' });
}

async function inspectWatch(watch, refresh) {
  if (Date.now() >= watch.expires) {
    await stopWatch('expired');
    return;
  }
  try {
    const tab = await chrome.tabs.get(watch.tabId);
    if (tab.url !== watch.url) {
      await stopWatch('blocked');
      return;
    }
    if (tab.status !== 'complete') return;
    const result = await readTab(watch.tabId, { ...watch, refresh });
    if (!result) await stopWatch('blocked');
    else if (result.found) await stopWatch(result.opened ? 'opened' : 'found');
  } catch {
    await stopWatch('blocked');
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.tab || !['start', 'stop', 'status'].includes(message.action)) return;
  enqueue(async () => {
    if (message.action === 'start') await startWatch(message.tabId, message.count);
    if (message.action === 'stop') await stopWatch();
    return { watching: Boolean(await currentWatch()) };
  }).then(sendResponse, error => sendResponse({ error: error.message }));
  return true;
});

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name !== alarmName) return;
  enqueue(async () => {
    const watch = await currentWatch();
    if (!watch) return;
    await inspectWatch(watch, true);
    if (await currentWatch()) await scheduleRefresh(watch.expires);
  });
});
chrome.tabs.onUpdated.addListener((tabId, change) => {
  if (!change.url && change.status !== 'complete') return;
  enqueue(async () => {
    const watch = await currentWatch();
    if (watch?.tabId !== tabId) return;
    if (change.url && change.url !== watch.url) await stopWatch('blocked');
    else if (change.status === 'complete') await inspectWatch(watch, false);
  });
});
chrome.tabs.onRemoved.addListener(tabId => {
  enqueue(async () => {
    if ((await currentWatch())?.tabId === tabId) await stopWatch();
  });
});
