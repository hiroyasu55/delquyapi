import settings  # noqa: F401
import urllib.parse as parse
from datetime import date  # noqa: F401
import re
import os  # noqa: F401
from pprint import pprint  # noqa: F401
import config
import app.lib.log as log
import app.lib.util as util
import app.models.Soup as Soup
import app.models.PDFReader as PDFReader
import app.models.Detail as Detail


logger = log.getLogger('scrape_nagoya')


def _scrape_nagoya_press_releases():
    results = []

    soup = Soup.create_soup(config.NAGOYA_PRESS_RELEASE_URL)

    fileblock = soup.body.select_one('.mol_attachfileblock')
    lis = list(filter(lambda li: re.match(r'^新型コロナウイルス患者の発生について.*$', li.text), fileblock.select('li')))

    for li in lis:
        a = li.select_one('a')
        pdf_url = parse.urljoin(
            re.sub(r'.\/[^\/]+$', '', config.NAGOYA_PRESS_RELEASE_URL),
            a['href'])

        filename = re.sub(r'^.*\/([^\/]+)$', r'\1', pdf_url)
        filepath = os.path.join(config.DATA_DIR, 'nagoya', filename)
        if not os.path.exists(filepath):
            util.download_file(pdf_url, filepath=filepath)

        result = {
            'title': li.text,
            'pdf_url': pdf_url
        }
        results.append(result)

    results = list(reversed(results))

    return results


# Read PDF
def read_nagoya_pdf(filepath, debug=False):
    results = []
    texts = PDFReader.read_textboxes(filepath)
    _lines = []

    for text in texts:
        _lines.extend(text.split('\n'))
    i = 0
    lines = []
    while i < len(_lines):
        line = _lines[i]
        if i < len(_lines) and len(line) == 1 and len(_lines[i + 1]) > 0:
            if re.match(r'^\d+$', line) and not re.match(r'^\d+.*$', _lines[i + 1]):
                line += '|'
            line += _lines[i + 1]
            i += 1

        line = line.strip().replace('  ', '|').replace(' ', '').replace('|', ' ')
        if len(line) > 0:
            lines.append(line)

        i += 1

    release_date = None
    patient = None
    term = None
    progress_date = None
    result = None
    stocks = []
    current_no = None

    for i, line in enumerate(lines):
        if debug:
            print('{}:{} > {}'.format(patient, term, line))

        if re.match(r'^（令和\d+年\d+月\d+日.*）.*$', line):
            release_date = util.parse_japanese_date(
                re.sub(r'^（(令和\d+年\d+月\d+日).*）.*$', r'\1', line)
            ).strftime(r'%Y-%m-%d')
            if re.match(r'^.*(\(|（)本市公表\d+～\d+例目(\)|）)$', line):
                current_no = int(re.sub(r'.*本市公表(\d+)～.*$', r'\1', line))
            elif re.match(r'^.*(\(|（)本市公表\d+例目(\)|）)$', line):
                current_no = int(re.sub(r'.*本市公表(\d+)例目.*$', r'\1', line))

        elif re.match(r'^(\d+|)(\s|)患者.*について.*$', line) and not re.match(r'^.*発生.*$', line):
            if result:
                results.append(result)
                # pprint(result)
            patient = re.sub(r'^.*(患者.*)について.*$', r'\1', line).replace(' ', '')
            term = None
            result = {
                'release_date': release_date,
                'patient_name': patient,
                'government': 'nagoya',
                'progress': [],
                'remarks': []
            }
            if current_no:
                result['no'] = current_no
                current_no += 1

        elif re.match(r'^以上\d+名の.+$', line) \
                or re.match(r'^\d+\s*.*新型コロナウイルスとは.*$', line) \
                or re.match(r'^\d+\s*.*新型コロナウイルスに関連した肺炎について.*$', line):
            if result:
                results.append(result)
                # pprint(result)
            result = None
            patient = None
            term = None

        elif not patient:
            continue

        elif re.match(r'^（.+）概要.*$', line):
            term = 'digest'

        elif re.match(r'^（.+）行動・症状等.*$', line):
            term = 'progress'
            progress_date = None

        elif line in ['患者・御家族等の人権尊重・個人情報保護にご理解とご配慮をお願いします。', 'また、行動歴、濃厚接触者については、現在調査中です。']:
            term = None

        elif re.match(r'^（.+）.+$', line):
            term = None

        # （１）概要
        elif term == 'digest':
            #  50歳代 男性 市内在住
            if not result.get('age'):
                words = line.split()
                for word in words:
                    if re.match(r'^\d+(代|歳|歳代|歳未満)$', word):
                        if re.match(r'\d+(代|歳代)$', word):
                            result['age'] = re.sub(r'(\d+)(代|歳代)$', r'\1', word) + 's'
                        elif re.match(r'\d+歳$', word):
                            result['age'] = re.sub(r'(\d+)歳$', r'\1', word) + 's'
                        elif re.match(r'\d+歳未満$', word):
                            result['age'] = re.sub(r'(\d+)歳未満$', r'\1', word) + 'u'
                        elif word == '不明':
                            result['age'] = 'unknown'
                        else:
                            raise Exception('Age "{}" not defined'.format(word))
                    elif re.match(r'^(男|女)性$', word):
                        if word == '男性':
                            result['sex'] = 'male'
                        elif word == '女性':
                            result['sex'] = 'female'
                        elif word == '不明':
                            result['sex'] = 'unknown'
                        else:
                            raise Exception('Sex "{}" not defined'.format(word))
                    elif re.match(r'^.+在住$', word):
                        if word == '市内在住':
                            result['area'] = '名古屋市'
                        else:
                            result['area'] = re.sub(r'在住$', r'', word)
                    elif re.match(r'^.+国籍$', word):
                        result['nationality'] = re.sub(r'国籍$', '', word)
                    else:
                        raise Exception('Illegal line ', line)

            # 主な症状：発熱、呼吸困難、咽頭痛、倦怠感、肺炎
            elif re.match(r'^主な症状：.+$', line):
                result['condition'] = re.sub(r'^主な症状：(.+)$', '\\1', line)

            # ※昨日までの本市公表事例の方との接触は、現時点においては確認できておりません。
            # elif re.match(r'^※.+$', line):
            else:
                remark = re.sub(r'^※', '', line)
                if len(result['remarks']) == 0:
                    result['remarks'].append(remark)
                else:
                    result['remarks'][-1] += remark

        # （２）行動・症状等
        elif term == 'progress':
            # 4月10日(金)
            # 発熱、咽頭痛
            if re.match(r'^\d+月\d+日.*$', line):
                progress_date = re.sub(r'^(\d+月\d+日).*$', '令和2年\\1', line)
                progress_date = util.parse_japanese_date(progress_date).strftime(r'%Y-%m-%d')

                if len(stocks) > 0:
                    progress = {
                        'date': progress_date,
                        'content': stocks[0],
                    }
                    result['progress'].append(progress)
                    stocks = []
                    progress_date = None

            elif progress_date:
                progress = {}
                if len(result['progress']) > 0 and result['progress'][-1]['date'] == progress_date:
                    progress = result['progress'][-1]
                else:
                    progress = {
                        'date': progress_date,
                        'content': '',
                    }
                    result['progress'].append(progress)

                progress['content'] += line

            elif len(stocks) == 0:
                stocks.append(line)

            else:
                raise Exception('Illegal line ' + line)

        elif not term:
            continue

        else:
            raise Exception('Illegal line ' + line)

    if result:
        results.append(result)

    return results


def scrape_releases():
    releases = _scrape_nagoya_press_releases()
    results = []
    no = 0

    for i, release in enumerate(releases):
        filename = re.sub(r'^.*\/([^\/]+)$', '\\1', release['pdf_url'])
        filepath = os.path.join(config.DATA_DIR, 'nagoya', filename)
        _results = read_nagoya_pdf(filepath)
        logger.debug('read PDF {}/{}'.format(i + 1, len(releases)))
        for r in _results:
            if r['release_date'] == '2020-04-30' and r.get('no') == 272:
                continue

            no += 1
            if no in [2, 56, 81]:
                no += 1

            if not r.get('no'):
                r['no'] = no

            r['url'] = release['pdf_url']
            results.append(r)

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
    details = scrape_releases()

    current_details = Detail.find_by_government('nagoya', order=['-no'], limit=1)
    last_no = 0 if len(current_details) == 0 else current_details[0]['no']
    details = list(filter(lambda d: d['no'] > last_no, details))
    details = list(map(lambda d: revise_detail(d), details))

    for detail in details:
        pprint(detail)
        Detail.insert(detail)
        logger.info('Add Nagoya detail [%s]', detail['no'])

    exit()
