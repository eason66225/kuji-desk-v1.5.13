export const origin = 'https://on-line.1kuji.com';
export const listPath = '/Form/Product/SelectBox.aspx';

export function readBoxList(expectedOrigin, expectedPath, watch) {
  if (location.origin !== expectedOrigin || location.pathname !== expectedPath) return null;
  if (watch && (location.href !== watch.url || document.readyState !== 'complete'
      || (watch.expires != null && Date.now() >= watch.expires))) return null;

  const text = document.body?.innerText ?? '';
  if (/一時的に入場いただける人数を\s*制限|順番待ちを抜ける|あなたの番です|verify you are human|verifying you are human|正在執行安全驗證/i.test(text)
      || /^(just a moment|請稍候|しばらくお待ち)/i.test(document.title)
      || document.querySelector('input[type="password"], [id$="_lbExitQueue"], [id^="cf-chl-"]')) return null;

  const boxes = [];
  const matches = [];
  for (const item of document.querySelectorAll('.selectbox__box-list-item')) {
    if (!item.getClientRects().length) continue;
    const link = item.querySelector('a[class*="BOX-"]');
    if (!link?.getClientRects().length) continue;
    const number = link.className.match(/(?:^|\s)BOX-(\d+)(?:\s|$)/)?.[1];
    const amount = item.querySelector('.selectbox__text--product-amount')
      ?.textContent.match(/残\s*(\d+)\s*枚/)?.[1];
    const waiting = item.querySelector('.selectbox__text--product-waiting')
      ?.textContent.match(/(\d+)\s*人/)?.[1];
    if (!number || !amount) continue;
    const box = { number, amount: Number(amount), waiting };
    boxes.push(box);
    if (watch && Number(number) > watch.baseline && box.amount === watch.count) {
      matches.push({ link, box });
    }
  }
  const params = new URLSearchParams(location.search);
  const pid = params.get('pid');
  if (watch && (!pid || !boxes.length)) return null;
  const match = matches.sort((a, b) => Number(b.box.number) - Number(a.box.number))[0];
  let opened = false;
  if (match) {
    const destination = new URL(match.link.href, location.href);
    const boxId = destination.searchParams.get('lbdid');
    const linkBoxId = match.link.className.match(/(?:^|\s)([0-9A-F]{16})(?:\s|$)/i)?.[1];
    if (destination.origin === expectedOrigin && !destination.username && !destination.password
        && destination.pathname === '/Form/Product/SelectBoxDetail.aspx'
        && [...destination.searchParams.keys()].every(key => ['shop', 'pid', 'lbdid', 'sort', 'fil', 'udns', 'pno'].includes(key))
        && destination.searchParams.getAll('pid').length === 1 && destination.searchParams.getAll('lbdid').length === 1
        && destination.searchParams.get('pid') === pid && /^[0-9A-F]{16}$/i.test(boxId ?? '')
        && (!linkBoxId || linkBoxId.toUpperCase() === boxId.toUpperCase())) {
      opened = true;
      location.assign(destination.href);
    }
  } else if (watch?.refresh) {
    location.reload();
  }
  return { boxes, pid, page: params.get('pno') || '1', found: match?.box.number, opened };
}

export async function readTab(tabId, watch) {
  const [{ result }] = await chrome.scripting.executeScript({
    target: { tabId },
    func: readBoxList,
    args: [origin, listPath, watch ?? null],
  });
  return result;
}
