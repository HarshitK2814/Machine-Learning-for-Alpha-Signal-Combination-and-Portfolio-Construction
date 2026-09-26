import json, urllib.request, urllib.parse, time, difflib, re, sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
infile = sys.argv[1] if len(sys.argv) > 1 else 'refs_to_verify.txt'
outfile = sys.argv[2] if len(sys.argv) > 2 else 'crossref_results.json'

WP_HOSTS = ('ssrn', 'nber', 'working paper', 'research paper series', 'cepr', 'arxiv')

def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', (s or '').lower())

out = {}
lines = [l for l in open(infile, encoding='utf-8').read().splitlines() if l.strip()]
for line in lines:
    pid, au, yr, title = line.split('|', 3)
    q = urllib.parse.urlencode({'query.bibliographic': f'{title} {au}', 'rows': 12,
                                'select': 'DOI,title,container-title,issued,author,type,volume,issue,page'})
    try:
        req = urllib.request.Request('https://api.crossref.org/works?' + q,
                                     headers={'User-Agent': 'lit-verification-script/1.1'})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        cands = []
        for it in d['message']['items']:
            t = (it.get('title') or [''])[0]
            s = difflib.SequenceMatcher(None, norm(t), norm(title)).ratio()
            fams = [a.get('family', '') for a in it.get('author', [])]
            au_ok = any(norm(au.split()[-1]) in norm(f) for f in fams)
            cont = ((it.get('container-title') or [''])[0] or '').lower()
            y = (it.get('issued', {}).get('date-parts') or [[None]])[0][0]
            is_wp = (not cont) or any(h in cont for h in WP_HOSTS) or it.get('type') in ('posted-content', 'report')
            bonus = (0.05 if au_ok else 0) + (0.10 if not is_wp else 0) + (0.05 if (y and abs(int(yr) - y) <= 1) else 0)
            cands.append((s + bonus, s, au_ok, is_wp, y, it))
        cands.sort(key=lambda c: -c[0])
        if cands:
            tot, s, au_ok, is_wp, y, best = cands[0]
            status = 'MATCH' if (s >= 0.85 and au_ok and not is_wp and y and abs(int(yr) - y) <= 1) else \
                     ('WP_VERSION' if (s >= 0.85 and au_ok and is_wp) else 'CHECK')
            out[pid] = dict(query_title=title, query_author=au, year_expected=yr, doi=best['DOI'],
                            title=(best.get('title') or [''])[0],
                            journal=(best.get('container-title') or [''])[0], year=y,
                            vol=best.get('volume'), issue=best.get('issue'), pages=best.get('page'),
                            type=best.get('type'),
                            authors=[f"{a.get('given', '')} {a.get('family', '')}".strip() for a in best.get('author', [])][:12],
                            title_similarity=round(s, 3), author_match=au_ok, status=status)
        else:
            out[pid] = dict(query_title=title, status='NOT_FOUND')
    except Exception as e:
        out[pid] = dict(query_title=title, status='ERROR', error=str(e))
    r = out[pid]
    print(pid, r.get('status'), r.get('title_similarity'), r.get('doi'), '|', r.get('journal'), r.get('year'))
    sys.stdout.flush()
    json.dump(out, open(outfile, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    time.sleep(0.25)
print('DONE', len(out))
