# Re-fetches each post in posts.csv and writes its disclosure-related page data to evidence/page-data/.
# Usage, from this video's folder: python3 tools/label_check.py
# null in the output means the field was not on the page. A labeled post (e.g. Paid partnership) has isAd true plus adAuthorization/adLabelVersion.
import csv, datetime, json, re, subprocess, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
KEEP = ['id', 'desc', 'createTime', 'isAd', 'adAuthorization', 'adLabelVersion', 'BAInfo', 'isCommerce', 'locationCreated']
LABEL = re.compile(r'brand|sponsor|promot|disclos|adLabel|adAuthor|BAInfo', re.I)

for row in csv.DictReader(open('posts.csv')):
    it = None
    for _ in range(3):
        html = subprocess.run(['curl', '-sL', '-A', UA, row['url']], capture_output=True, text=True).stdout
        m = re.search(r'id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.S)
        try:
            it = json.loads(m.group(1))['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']
            break
        except Exception:
            time.sleep(3)
    if not it:
        print(row['date'], row['url'], 'FETCH FAILED')
        continue
    rec = {k: it.get(k) for k in KEEP}
    rec['author'] = it['author']['uniqueId']
    rec['stats'] = it.get('stats')
    rec['disclosure_keys_present'] = sorted(k for k in it if LABEL.search(k))
    rec['fetched_utc'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rec['url'] = row['url']
    json.dump(rec, open(row['page_data'], 'w'), indent=2, ensure_ascii=False)
    print(row['date'], 'isAd', rec['isAd'], 'disclosure fields', rec['disclosure_keys_present'] or 'none')
    time.sleep(1)
