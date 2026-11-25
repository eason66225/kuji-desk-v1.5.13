"""Parse the visible Japanese detail page without confusing total waiters with yours."""
import re
import unicodedata


def parse_detail_text(text):
    text = unicodedata.normalize('NFKC', text or '')
    ahead = re.search(r'あと\s*([\d,]+)\s*人であなたの番です', text)
    remaining = re.search(r'残りくじ\s*([\d,]+)\s*枚', text)
    prizes = {}
    for match in re.finditer(r'(ラストワン賞|[A-Z]{1,8}賞|\d+賞)\s*(?:残数\s*[:：]?\s*)?([\d,]+)\s*/\s*([\d,]+)', text):
        label, left, total = match.groups()
        left, total = int(left.replace(',','')), int(total.replace(',',''))
        if 0 <= left <= total:
            # The compact award summary appears before the expanded descriptions.
            # Keep it when both sections are present.
            prizes.setdefault(label, {'label':label, 'remaining':left, 'total':total})
    # Last One is an extra award, not another ticket. Never infer its stock.
    footer = re.search(r'(?:^|\n)残数\s*(\d+)\s*/\s*(\d+)\s*(?:\n|$)', text)
    return {
        'ahead':int(ahead[1].replace(',','')) if ahead else None,
        'remaining':int(remaining[1].replace(',','')) if remaining else None,
        'total':int(footer[2]) if footer else None,
        'prizes':list(prizes.values()),
        'lastOneListed':'ラストワン賞' in text,
    }


READ_DETAIL = r'''() => {
  const visible = e => !!e && e.getClientRects().length > 0;
  const alert = document.querySelector('#customAlert');
  const waiting = document.querySelector('#waitingNo');
  const exit = document.querySelector('[id$="_lbExitQueue"]');
  const refresh = [...document.querySelectorAll('button, input[type="button"], a')]
    .find(e => visible(e) && (e.textContent.trim() === '在庫情報を更新' || e.value === '在庫情報を更新'));
  const alertText=visible(alert)?alert.innerText:'';
  return {url:location.href, paymentTimeout:alertText.includes('タイムアウト') && /制限時間内に決済が完了しなかったため/.test(alertText.replace(/\s/g,'')) && alertText.includes('キャンセル'), soldOut:alertText.includes('順番待ち中のくじ箱が在庫切れ'), ready:visible(alert) && alert.textContent.includes('あなたの番です'),
    number:visible(waiting) && /^\d+$/.test(waiting.textContent.trim()) ? Number(waiting.textContent.trim()) : null,
    text:document.body.innerText, exitVisible:visible(exit),
    refreshEnabled:!!refresh && !refresh.disabled && refresh.getAttribute('aria-disabled') !== 'true'};
}'''


def parse_detail_html(html):
    """Parse the full or partial detail page HTML directly from an HTTP response."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html or '', 'html.parser')
    remain_cnt = None
    total_cnt = 0
    remain_tag = soup.find(class_=re.compile(r'selectbox-lottery-modal__heading-container'))
    if remain_tag:
        m = re.search(r'残りくじ\s*([\d,]+)\s*枚', unicodedata.normalize('NFKC', remain_tag.get_text()))
        if m:
            remain_cnt = int(m.group(1).replace(',', ''))

    prizes = []
    stock_list = soup.find(class_=re.compile(r'selectbox-lottery-modal__variation-stock-list'))
    if stock_list:
        for item in stock_list.find_all('li'):
            name_tag = item.find(class_=re.compile(r'variation-stock-prize-name'))
            num_tag = item.find(class_=re.compile(r'variation-stock-prize-number'))
            if name_tag and num_tag:
                name = unicodedata.normalize('NFKC', name_tag.get_text(strip=True))
                nums = re.search(r'([\d,]+)\s*/\s*([\d,]+)', unicodedata.normalize('NFKC', num_tag.get_text()))
                if nums:
                    left = int(nums.group(1).replace(',', ''))
                    tot = int(nums.group(2).replace(',', ''))
                    total_cnt += tot
                    prizes.append({'label': name, 'remaining': left, 'total': tot})

    if remain_cnt is None and prizes:
        remain_cnt = sum(p['remaining'] for p in prizes if 'ラストワン' not in p['label'])

    text = unicodedata.normalize('NFKC', soup.get_text())
    fallback = parse_detail_text(soup.get_text('\n'))
    if remain_cnt is None:
        remain_cnt = fallback['remaining']
    if not prizes:
        prizes = fallback['prizes']
        total_cnt = sum(p['total'] for p in prizes if 'ラストワン' not in p['label'])
    ahead = re.search(r'あと\s*([\d,]+)\s*人であなたの番です', text)
    return {
        'ahead': int(ahead.group(1).replace(',', '')) if ahead else None,
        'remaining': remain_cnt,
        'total': total_cnt if total_cnt else None,
        'prizes': prizes,
        'lastOneListed': any('ラストワン' in p['label'] for p in prizes),
    }
