# -*- coding: utf-8 -*-
"""AI 교육 1~8차 패들렛(공개 보드)에서 '수강생이 올린 결과물'만 모아 edu_results.json 으로 저장한다.
   강사(보드 주인) 글은 강의 자료라 빼고, 수강생 글만 남긴다(닉네임·링크·첨부 이미지·한 줄 설명).
   python tools/padlet_results.py  → edu_results.json (대시보드 「AI 교육 다시보기」가 읽음)"""
import json, os, re, sys, time, urllib.request, urllib.parse, html

BOARDS = {   # 회차: 패들렛 주소(대시보드 EDU.doc 단축 링크가 가리키는 곳)
    1: 'https://padlet.com/hamsterthemerciless/260619_-ai-_-_1-a70yapbeunhyjhrm',
    2: 'https://padlet.com/hamsterthemerciless/260626_-ai-_-_2-v3hgsnqzughwlmeg',
    3: 'https://padlet.com/hamsterthemerciless/260703_-ai-_-_3-wnl44xm62ldp9eds',
    4: 'https://padlet.com/hamsterthemerciless/260710_-ai-_-_4-zy87eyrrdzqc29qq',
    5: 'https://padlet.com/hamsterthemerciless/260724_-ai-_-_5-iwf9ke2u1p3s5zwe',
    6: 'https://padlet.com/hamsterthemerciless/260731_-ai-_-_6-y8d4v6t7yaro7996',
    7: 'https://padlet.com/hamsterthemerciless/260807_-ai-_-_7-nhjci3rukt4ya48s',
    8: 'https://padlet.com/hamsterthemerciless/260821_-ai-_-_8-eik1cfr4z8vdv1dh',
}
UA = {'User-Agent': 'Mozilla/5.0'}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'edu_results.json')


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode('utf-8')


def text(s):
    s = re.sub(r'<br\s*/?>|</p>|</div>', '\n', s or '')
    return re.sub(r'\n{2,}', '\n', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()


KIND = {'pdf': 'PDF', 'pptx': 'PPT', 'ppt': 'PPT', 'docx': '워드', 'doc': '워드', 'hwp': '한글', 'hwpx': '한글', 'xlsx': '엑셀', 'xls': '엑셀',
        'csv': 'CSV', 'html': 'HTML', 'zip': 'ZIP', 'png': '이미지', 'jpg': '이미지', 'jpeg': '이미지', 'gif': '이미지', 'webp': '이미지',
        'mp4': '영상', 'mov': '영상', 'md': '문서', 'txt': '문서'}


def board(n, url):
    page = get(url)
    hid = re.search(r'hashid=board_([A-Za-z0-9]+)', page).group(1)
    wishes = json.loads(get(f'https://padlet.com/api/10/wishes?wall_hashid={hid}&wallHashid={hid}'))
    if isinstance(wishes, dict):
        wishes = wishes.get('data') or []
    posts = [w.get('attributes', w) for w in wishes]
    # 강사(보드를 만든 사람)는 강의 자료를 가장 많이 올린 사람 — 그 글은 빼고 수강생 글만 남긴다
    from collections import Counter
    owner = Counter(a.get('author_id') for a in posts).most_common(1)[0][0]
    rows = []
    for a in posts:
        if a.get('author_id') == owner:
            continue
        wc = a.get('wish_content') or {}
        att = ((wc.get('attachment_props') or {}).get('url')) or a.get('attachment') or ''
        body = text(a.get('body') or wc.get('body'))
        web = ''
        if att.startswith('http') and 'padletusercontent' not in att:
            web = att
        else:
            m = re.search(r'https?://[^\s<>"]+', body)
            web = m.group(0) if m else ''
        kind, fname = '', ''
        if 'padletusercontent' in att:
            path = urllib.parse.unquote(att.split('?')[0].rsplit('/', 1)[-1])
            ext = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
            kind, fname = KIND.get(ext, ext.upper() or '파일'), re.sub(r'[_]+', ' ', path.rsplit('.', 1)[0])[:70]
        elif web:
            kind = 'GitHub' if 'github' in web else '웹'
        elif body:
            kind = '글'
        note = re.sub(r'https?://\S+', '', body).strip()
        note = re.sub(r'(배포\s*)?(URL|주소|링크)\s*[:：]?\s*$', '', note, flags=re.I).strip(' :：-')   # 링크를 뺀 뒤 남는 꼬리 정리
        rows.append({'who': (a.get('subject') or '').strip()[:30], 'kind': kind, 'file': fname,
                     'note': note[:90], 'web': web,
                     'post': a.get('permalink') or '', 'at': (a.get('created_at') or '')[:10]})
    rows.sort(key=lambda r: (r['at'], r['who']))
    return {'n': n, 'board': url, 'count': len(rows), 'items': rows}


if __name__ == '__main__':
    data = {'updated': time.strftime('%Y-%m-%d %H:%M'), 'sessions': []}
    for n, url in BOARDS.items():
        b = board(n, url); data['sessions'].append(b)
        print(n, '결과물', b['count'], '건', file=sys.stderr)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(OUT)
