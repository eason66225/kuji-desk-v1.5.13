"""Detect an interstitial so callers can stop automatic website activity."""


def requires_cloudflare_verification(text='', headers=None):
    if any(key.lower() == 'cf-mitigated' and value.lower() == 'challenge'
           for key, value in (headers or {}).items()):
        return True
    content = ' '.join(text.casefold().split())
    return 'cloudflare' in content and any(marker in content for marker in (
        '正在執行安全驗證',
        '驗證您是人類',
        'verify you are human',
        'verifying you are human',
    ))


if __name__ == '__main__':
    assert requires_cloudflare_verification('正在執行安全驗證\n驗證您是人類\nCloudflare')
    assert requires_cloudflare_verification(headers={'CF-Mitigated': 'challenge'})
    assert not requires_cloudflare_verification('一時的に入場いただける人数を制限しております。')
    assert not requires_cloudflare_verification(headers={'Server': 'cloudflare'})
