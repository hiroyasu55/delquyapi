import settings  # noqa: F401
import urllib.parse
from datetime import date
import re
import os
import logging
import config
from pprint import pprint
import app.lib.util as util
import app.models.Soup as Soup
import app.models.PDFReader as PDFReader
import app.models.Detail as Detail

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
# handler.setFormatter(
#    logging.Formatter()
# )
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

COUNTRIES = [
    '日本', '中国', 'アメリカ', 'フランス', 'イタリア',
    'イギリス', 'カナダ', 'オーストラリア', 'ナイジェリア',
    'ノルウェー', 'タイ', 'フィリピン', '欧州'
]


def _scrape_aichi_detail_2(start_tag):
    result = {}

    content_type = 1
    if re.match(r'^.*患者.*について$', start_tag.text):
        content_type = 2
    elif re.match(r'^.*患者.*について（県内\d+例目）$', start_tag.text):
        content_type = 2
        result['total_no'] = int(re.sub(r'^.*（県内(\d+)例目）$', r'\1', start_tag.text))

    tag = start_tag.find_next_sibling()
    term = 0
    key = ''
    while tag:
        # print(tag)
        text = tag.text.replace('\u3000', ' ').strip()
        if len(text) == 0:
            tag = tag.find_next_sibling()
            continue

        if content_type == 1 and tag.name == 'h2':
            if re.match(r'^.*概要$', text):
                term = 1
            elif re.match(r'^.*経過$', text):
                term = 2

        elif tag.name == 'p':
            if re.match(r'^.+記者発表済みです。$', text):
                result['ignore'] = True
                break

            elif re.match(r'^（\d+）概要$', text):
                term = 1
            elif re.match(r'^（\d+）経過$', text):
                term = 2
            elif re.match(r'^※.+$', text):
                result['remarks'] = result['remarks'] + '\n' if result.get('remarks') else ''
                result['remarks'] += re.sub(r'^※(\d+\s+|)', '', text)
            elif term == 1:
                if key == 'age':
                    words = re.sub(r'^(.+)（(.+)）$', r'\1 \2', text).split()
                    result['age'] = words[0]
                    if len(words) > 1:
                        if words[1] == r'外国籍':
                            result['nationality'] = words[1]
                        else:
                            result['nationality'] = re.sub(r'^(.+)国籍$', r'\1', words[1])
                else:
                    result[key] = re.sub(r'^　(.+)$', r'\1', text)
            elif term == 2:
                if 'progress' not in result:
                    result['progress'] = []
                if re.match(r'^注\d+.*$', text):
                    pass
                elif re.match(r'^\d+月\d+日 .+$', text):
                    dt, content = \
                        re.sub(r'^(\d+月\d+日) (.+)$', r'\1|\2', text).split('|')
                    month, day = \
                        re.sub(r'^(\d+)月(\d+)日.*$', r'\1 \2', dt).split()
                    result['progress'].append({
                        'date': date(year=2020, month=int(month), day=int(day)).strftime(r'%Y-%m-%d'),
                        'content': content.strip()
                    })
                else:
                    if len(result['progress']) > 0:
                        result['progress'][-1]['content'] += ('|' + text)
                    else:
                        result['progress'].append({'content': text})
            else:
                break

        elif (content_type == 1 or term == 1) and tag.name == 'h3':
            term = 1
            if re.match(r'^年代$', text):
                key = 'age'
            elif re.match(r'^性別$', text):
                key = 'sex'
            elif re.match(r'^居住地$', text):
                key = 'area'
            elif re.match(r'^主な症状(等|)$', text):
                key = 'condition'
            else:
                key = 'others'

        else:
            break

        tag = tag.find_next_sibling()

    if result.get('ignore'):
        return None

    result['remarks'] = result['remarks'].split('\n') if result.get('remarks') else []
    result['remarks'] = list(map(lambda r: r.strip(), result['remarks']))

    return result


def scrape_release_details(url):
    results = []

    soup = Soup.create_soup(url)
    pdf_a = list(filter(
        lambda a: re.match(r'^新型コロナウイルス感染症患者.*$', a.text),
        soup.body.select('a')
    ))
    if len(pdf_a) > 0:
        pdf_url = urllib.parse.urljoin(config.AICHI_PRESS_RELEASE_URL, pdf_a[0]['href'])
        filename = re.sub(r'^.*\/([^\/]+)$', r'\1', pdf_url)
        filepath = os.path.join(config.DATA_DIR, 'aichi', filename)
        if not os.path.exists(filepath):
            util.download_file(pdf_url, filepath=filepath)

        pdf_results = read_release_pdf(filepath)
        for result in pdf_results:
            result.update({
                'url': url,
                'pdf_url': pdf_url,
            })
            results.append(result)
        return results

    detail_free = soup.body.select('.detail_free')
    if detail_free is None:
        raise('class "detail_free" not found.')

    # <h2>1　患者Ａについて</h2>
    # <h2>1　患者Ａについて（県内xx例目）</h2>
    headers = []
    header = detail_free[0].find('h2', text=re.compile(r'^.*患者概要$'))
    if header:
        headers = [header]
    else:
        # headers = detail_free[0].find_all('h2', text=re.compile(r'^.*患者.*について.*$'))
        headers = list(filter(lambda h2: re.match(r'^\d+\s+患者.*について.*$', h2.text), detail_free[0].find_all('h2')))

    results = list(map(lambda tag: _scrape_aichi_detail_2(tag), headers))
    results = list(filter(lambda r: r is not None, results))

    if len(results) == 0:
        results.append({'url': url})

    return results


def _scrape_aichi_press_releases():
    results = []

    soup = Soup.create_soup(config.AICHI_PRESS_RELEASE_URL)

    detail_free = soup.body.select('.detail_free')[0]
    ps = detail_free.select('p')
    for p in ps:
        result = {}
        if re.match(r'^\d+年\d+月\d+日更新.*$', p.text) is None:
            continue
        year, month, day = \
            re.sub(r'^(\d+)年(\d+)月(\d+)日.*$', r'\1 \2 \3', p.text).split()
        result['date'] = \
            date(year=int(year), month=int(month), day=int(day)).strftime(r'%Y-%m-%d')

        a = p.select('a')[0]
        if re.match(r'^新型コロナウイルス感染症患者の発生について.*$', a.text) is None:
            # print(a.text)
            continue
        result['text'] = a.text
        result['url'] = urllib.parse.urljoin(config.AICHI_PRESS_RELEASE_URL, a['href'])

        results.append(result)

    return list(reversed(results))


def _parse_pdf_key_values(word):
    key = None
    value = None
    if re.match(r'県内.*\d+例目$', word):
        key = 'total_no'
        value = int(re.sub(r'^[^\d]*(\d+)例目$', r'\1', word))
    elif word == r'年代':
        key = 'age'
    elif word == r'症状':
        key = 'condition'
    elif word == r'性別':
        key = 'sex'
    elif word == r'国籍':
        key = 'nationality'
    elif word == r'居住地':
        key = 'area'
    elif re.match(r'^発症日$', word):
        key = 'onset_date'
    elif word == r'陽性確定日':
        key = 'confirmed_date'
    elif re.match(r'^海外渡航歴.*$', word):
        key = 'abroad_history'
        words = word.split(' ')
        if len(words) >= 2:
            value = ''.join(words[1:])
    elif re.match(r'^特記事項.*$', word):
        key = 'remarks'
        words = word.split('|')
        if len(words) >= 2:
            value = ''.join(words[1:])

    return key, value


def parse_pdf_key_values(text):
    key, value = _parse_pdf_key_values(text)
    if key:
        return [{'key': key, 'value': value}]

    words = text.split('|')
    if len(words) == 1:
        return [{'key': None, 'value': text}]

    keys = []
    for word in text.split('|'):
        key, value = _parse_pdf_key_values(word)
        if not key:
            keys.append({'key': None, 'value': word})
        else:
            keys.append({'key': key, 'value': value})

    return keys


# Read PDF
def read_release_pdf(filepath, debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)

    data = []
    for text in PDFReader.read_textboxes(filepath)[1:]:
        text = text.strip().replace('\n', '|')
        if len(text) == 0:
            continue

        # print('<{}>'.format(text))
        results = parse_pdf_key_values(text)
        data.extend(results)

    results = []
    items = []
    stocks = []
    current_key = None
    for d in data:
        logger.debug('{}'.format(d))
        item = None
        if d['key']:
            if d['key'] == 'age' and current_key:
                if len(stocks) > 0:
                    raise Exception('Undefined values {}'.format(','.join(stocks)))
                result = {}
                for _item in items:
                    result[_item['key']] = _item['value']
                results.append(result)
                logger.debug('--------')
                items = []

            if d['value']:
                item = {'key': d['key'], 'value': d['value']}
                logger.debug('A> {}'.format(item))

            elif d['key'] in ['onset_date', 'confirmed_date']:
                for s in list(filter(lambda s: re.match(r'^\d+月\d+日$', s), stocks)):
                    item = {'key': d['key'], 'value': s}
                    logger.debug('P> {}'.format(item))
                    stocks.remove(s)
                    break

            elif d['key'] in ['condition']:
                t = ''
                while len(stocks) > 0:
                    s = stocks[0]
                    if re.match(r'^\d+月\d+日$', s):
                        break
                    t += s
                    stocks.remove(s)
                if len(t) > 0:
                    item = {'key': d['key'], 'value': t}
                    logger.debug('P> %s', item)

            elif len(stocks) > 0:
                s = stocks.pop(0)
                item = {'key': d['key'], 'value': s}
                logger.debug('P> {}'.format(item))

            if not item:
                item = {'key': d['key'], 'value': '' if d['key'] == 'remarks' else None}
                logger.debug('N> {}'.format(item))

            items.append(item)
            current_key = d['key']

        elif re.match(r'^.+(歳|歳代|歳未満)$', d['value']):
            for _item in list(filter(lambda _item: _item['key'] == 'age', items)):
                item = _item
                item['value'] = d['value']
                logger.debug('U> {}'.format(item))
                break

        elif re.match(r'^(男|女)性$', d['value']):
            for _item in list(filter(lambda _item: _item['key'] == 'sex', items)):
                item = _item
                item['value'] = d['value']
                logger.debug('U> {}'.format(item))
                break

        elif d['value'] in COUNTRIES:
            for _item in list(filter(lambda _item: _item['key'] == 'nationality', items)):
                item = _item
                item['value'] = d['value']
                logger.debug('U> {}'.format(item))
                break

        elif re.match(r'^.+(都|道|府|県|市|町|村)$', d['value']):
            for _item in list(filter(lambda _item: _item['key'] == 'area', items)):
                item = _item
                item['value'] = d['value']
                logger.debug('U> {}'.format(item))
                break

        elif re.match(r'^\d+月\d+日$', d['value']):
            for _item in list(filter(lambda _item: _item['key'] in ['onset_date', 'confirmed_date'], items)):
                if _item['value']:
                    continue
                item = _item
                item['value'] = d['value']
                logger.debug('U> {}'.format(item))
                break

        elif re.match(r'^・.+$', d['value']):
            for _item in list(filter(lambda _item: _item['key'] == 'remarks', items)):
                item = _item
                item['value'] = d['value']
                logger.debug('U> {}'.format(item))
                current_key = 'remarks'
                break

        elif current_key == 'condition':
            for _item in list(filter(lambda _item: _item['key'] == 'condition', items)):
                item = _item
                item['value'] = (item.get('value') or '') + d['value']
                logger.debug('+> {}'.format(item))
                break

        elif current_key == 'remarks':
            for _item in list(filter(lambda _item: _item['key'] == 'remarks', items)):
                item = _item
                item['value'] = (item.get('value') or '') + d['value']
                logger.debug('+> {}'.format(item))
                break

        if not item:
            for _item in list(filter(lambda r: r['value'] is None, items)):
                if re.match(r'^\d+月\d+日$', d['value']):
                    if _item['key'] not in ['onset_date', 'confirmed_date']:
                        continue
                item = _item
                break
            if item:
                item['value'] = d['value']
                logger.debug('O> {}'.format(item))
            else:
                if not current_key:
                    logger.debug('I> %s', d['value'])
                    continue

                stocks.append(d['value'])
                logger.debug('S> %s', d['value'])

    if len(items) > 0:
        result = {}
        for item in items:
            result[item['key']] = item['value']
        results.append(result)

    for result in results:
        for key in result:
            if not result[key]:
                result[key] = '' if key == 'remarks' else 'unknown'
            if key in ['onset_date', 'confirmed_date']:
                if result[key] == '－':
                    result[key] = ''
                elif re.match(r'^\d+月\d+日$', result[key]):
                    result[key] = util.parse_japanese_date('令和2年' + result[key]).strftime(r'%Y-%m-%d')

        result['progress'] = result.get('progress') or []
        result['remarks'] = result['remarks'].split('\n') if result.get('remarks') else []
        result['remarks'] = list(map(lambda r: re.sub(r'^・', '', r), result['remarks']))

    return results


def scrape_releases():
    releases = _scrape_aichi_press_releases()
    results = []

    no = 2
    for i, release in enumerate(releases):
        logger.info('detail {}/{}'.format(i + 1, len(releases)))
        details = scrape_release_details(release['url'])
        for detail in details:
            if detail.get('total_no') == 285:
                no = 100
            elif detail.get('total_no') == 328:
                no = 118
            else:
                no += 1
            detail.update({
                'no': no,
                'release_date': release['date'],
                'government': 'aichi',
                'url': release['url']
            })

            if not detail.get('age'):
                pprint(detail)
                raise Exception('age')
            if re.match(r'\d+(代|歳代)$', detail['age']):
                detail['age'] = re.sub(r'(\d+)(代|歳代|歳)$', r'\1', detail['age']) + 's'
            elif re.match(r'\d+歳(児|)$', detail['age']):
                detail['age'] = re.sub(r'(\d+)歳.*$', r'\1', detail['age']) + 's'
            elif re.match(r'\d+歳未満(（小学生）|)$', detail['age']):
                detail['age'] = re.sub(r'(\d+)歳未満.*$', r'\1', detail['age']) + 'u'
            elif detail['age'] == 'unknown':
                pass
            else:
                raise Exception('Age "{}" not defined'.format(detail['age']))

            if detail['sex'] == '男性':
                detail['sex'] = 'male'
            elif detail['sex'] == '女性':
                detail['sex'] = 'female'
            elif detail['sex'] == 'unknown':
                pass
            else:
                raise Exception('Sex "{}" not defined'.format(detail['sex']))

            if detail['release_date'] == '2020-04-11':
                detail['release_date'].append(
                    '◎検査誤りの可能性あり（https://www.pref.aichi.jp/site/covid19-aichi/pressrelease-ncov200412.html）'
                )

        results.extend(details)

    return results


def revise_detail(detail):
    if len(detail['progress']) > 0:
        # onset date
        restr = r'^.*(' + '|'.join(config.CONDITIONS) + ').*$'
        p0 = detail['progress'][0]
        if re.match(restr, p0['content']):
            detail['onset_date'] = p0['date']
        else:
            ps = list(filter(lambda p: re.match(restr, p['content']), detail['progress']))
            if len(ps) > 0:
                detail['onset_date'] = ps[0]['date']

        # hospitalization date
        ps = list(filter(lambda p: re.match('^.*入院.*$', p['content']) and not re.match('^.*入院予定.*$', p['content']), detail['progress']))  # noqa E501
        if len(ps) > 0:
            detail['hospitalization_date'] = ps[0]['date']

        # confirmed date
        ps = list(filter(lambda p: re.match('^.*陽性.*$', p['content']), detail['progress']))
        if len(ps) > 0:
            detail['confirmed_date'] = ps[0]['date']

    return detail


# Main
if __name__ == '__main__':

    current_details = Detail.find(order=['-release_date'], limit=1)
    current_date = current_details[0]['release_date']

    details = scrape_releases()
    details = list(filter(lambda d: d['release_date'] > current_date, details))
    details = list(map(lambda d: revise_detail(d), details))

    for detail in details:
        pprint(detail)
        Detail.insert(detail)
        logger.info('Add Aichi detail [%s]', detail['no'])

    exit()
