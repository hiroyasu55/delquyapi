import settings  # noqa: F401
import urllib.parse as parse
from datetime import date  # noqa: F401
import re
import os  # noqa: F401
import logging
from pprint import pprint  # noqa: F401
import config
import app.lib.util as util
import app.models.Soup as Soup
import app.models.PDFReader as PDFReader
import app.models.Detail as Detail


logger = logging.getLogger('nagoya')
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        r'%(name)s [%(levelname)s] %(message)s',
        config.LOG_TIME_FORMAT
    )
)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


CONSTANT_CHARS = {
    2: [
        '接触', '患者', '未満',
    ],
    3: ['コロナ', '起こす', 'に引き'],
    4: [],
}
AFTER_CHARS = [
    'での'
]
CONSTANTS_PAIRS = [
    ['コロナ', 'ウイルス'],
    ['いただく', 'よう'],
    ['実施', 'する'],
]


def word_to_age(word):
    age = None
    if re.match(r'^\d+(代|歳|歳代|歳未満)$', word):
        if re.match(r'\d+(代|歳代)$', word):
            age = re.sub(r'(\d+)(代|歳代)$', r'\1', word) + 's'
        elif re.match(r'\d+歳$', word):
            age = re.sub(r'(\d+)歳$', r'\1', word) + 's'
        elif re.match(r'\d+歳未満$', word):
            age = re.sub(r'(\d+)歳未満$', r'\1', word) + 'u'
        elif word == '不明':
            age = 'unknown'
        else:
            raise Exception('Age "{}" not defined'.format(word))
    return age


def word_to_sex(word):
    sex = None

    if word in ['男性', '男']:
        sex = 'male'
    elif word in ['女性', '女']:
        sex = 'female'
    elif word == '不明':
        sex = 'unknown'
    else:
        raise Exception('Sex "{}" not defined'.format(word))

    return sex


def scrape_nagoya_press_releases():
    releases = []

    soup = Soup.create_soup(config.NAGOYA_PRESS_RELEASE_URL)
    # fileblock = soup.body.select_one('.mol_attachfileblock')
    mol_contents = soup.body.select_one('#mol_contents')
    h2 = list(filter(lambda h2: re.match(r'^名古屋市記者発表資料.*$', h2.text), mol_contents.select('h2')))[0]
    block = list(filter(lambda e: 'mol_attachfileblock' in e.get('class'), h2.next_siblings))[0]
    # lis = list(filter(lambda li: re.match(r'^新型コロナウイルス患者の発生について.*$', li.text), block.select('li')))
    lis = list(filter(lambda li: re.match(r'^新型コロナウイルス患者の発生について（令和\d+年\d+月\d+日）.*$', li.text), block.select('li')))

    for li in lis:
        a = li.select_one('a')
        pdf_url = parse.urljoin(
            re.sub(r'.\/[^\/]+$', '', config.NAGOYA_PRESS_RELEASE_URL),
            a['href'])

        filename = re.sub(r'^.*\/([^\/]+)$', r'\1', pdf_url)
        filepath = os.path.join(config.DATA_DIR, 'nagoya', filename)
        if not os.path.exists(filepath):
            util.download_file(pdf_url, filepath=filepath)

        releases.append({
            'date': util.parse_japanese_date(
                re.sub(r'^.+（(令和\d+年\d+月\d+日)）.*$', r'\1', li.text)).strftime(r'%Y-%m-%d'),
            'title': li.text,
            'pdf_url': pdf_url
        })

    releases = list(reversed(releases))

    return releases


# Read PDF lines
def read_pdf_lines(filepath, debug=False):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    texts = PDFReader.read_textboxes(filepath)
    _texts = []
    for text in texts:
        _texts.extend(text.split('\n'))
    texts = _texts

    _texts = []
    for text in texts:

        while re.match(r'^.*[^\d+]\s+\d+\s+[^\d+].*$', text):
            text = re.sub(r'^(.*[^\d+])\s+(\d+)\s+([^\d+].*)$', r'\1\2\3', text)
        while re.match(r'^\d+\s+[^\d+]$', text):
            text = re.sub(r'^(.*\d+)\s+([^\d+].*)$', r'\1\2', text)

        while re.match(r'^(未満)\d+$', text):
            text = re.sub(r'^(未満)(\d+)$', r'\1 \2', text)
            logger.debug('!"{}"'.format(text))

        # text = text.strip().replace('  ', '^').replace(' ', '').replace('^', ' ')
        if re.match(r'^\d+月\d+日 [^\s]+検査$', text):
            pass
        else:
            text = text.strip().replace('  ', ' ').replace(' ', '|')

        if len(text) == 0:
            continue
        _texts.extend(text.split('|'))

    texts = _texts

    lines = []
    for i, text in enumerate(texts):
        text = text.strip()

        # check = False
        # while re.match(r'^.*\d+\s+(例目).*$', text):
        #     text = re.sub(r'^(.*\d+)\s+([^\s+].*)$', r'\1\2', text)
        #     check = True
        # if check:
        #     logger.debug('>"{}"'.format(text))

        logger.debug('"{}"'.format(text))

        if i >= 1:
            if re.match(r'^.*(\(|（)[^\)）]*$', lines[-1]):
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue

            # if re.match(r'^[^（]*）.*$', text):
            #     if re.match(r'^.*（[^）]*$', lines[-1]):
            #         lines[-1] += text
            #         logger.debug('->"{}"'.format(lines[-1]))
            #         exit()
            #         continue
            #     else:
            #         raise Exception('"（）" not paring. "{}","{}"'.format(lines[-1], text))

            if re.match(r'^.*\d+$', lines[-1]) and not re.match(r'^\d+.*$', text):
                if re.match(r'^(男|女|軽症|中等症|重症|―).*$', text):
                    pass
                elif re.match(r'^(本市|愛知).*$', text):
                    pass
                elif re.match(r'^(調査中)$', text):
                    pass
                elif re.match(r'^(種類|例目).*$', text):
                    lines[-1] += text
                    logger.debug('->"{}"'.format(lines[-1]))
                    continue
                else:
                    raise Exception('??? "{}","{}"'.format(lines[-1], text))

            if re.match(r'^(※)$', lines[-1]):
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue

            if re.match(r'^.*(～)$', lines[-1]):
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue

            if lines[-1][-1] + text[0] in CONSTANT_CHARS[2]:
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue
            # if len(lines) >= 2 and lines[-2][-1] + text[0] in CONSTANT_CHARS[2]:
            #     lines[-2] += text
            #     logger.debug('-->"{}"'.format(lines[-1]))
            #     exit()
            #     continue
            if lines[-1][-1:] + text[:2] in CONSTANT_CHARS[3] or \
                    lines[-1][-2:] + text[:1] in CONSTANT_CHARS[3]:
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue
            if lines[-1][-1:] + text[:3] in CONSTANT_CHARS[4] or \
                    lines[-1][-2:] + text[:2] in CONSTANT_CHARS[4] or \
                    lines[-1][-3:] + text[:1] in CONSTANT_CHARS[4]:
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue

            if re.match(r'^('+'|'.join(AFTER_CHARS)+').*$', text):
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue

            if re.match(r'^(に|へ|の|と|へ|は)、.*$', text):
                lines[-1] += text
                logger.debug('->"{}"'.format(lines[-1]))
                continue

            if len(lines[-1]) == 1:
                if re.match(r'^\d+$', lines[-1]) and not re.match(r'^\d+.*$', text):
                    lines[-1] += '|' + text
                    logger.debug('->"{}"'.format(lines[-1]))
                    exit()
                    continue

            # if re.match(r'^.+(に|へ|の|と|へ)$', lines[-1]) and \
            #         re.match(r'('+'|'.join(['|'.join(CONSTANT_CHARS[2]), '|'.join(CONSTANT_CHARS[3])])+r').*$', text):
            #     lines[-1] += text
            #     logger.debug('->"{}"'.format(lines[-1]))
            #     exit()
            #     continue
            # if re.match(
            #         r'^(に|へ|の|と|へ|な)('+'|'.join(['|'.join(CONSTANT_CHARS[2]), '|'.join(CONSTANT_CHARS[3])])+r').*$',
            #         text):
            #     lines[-1] += text
            #     logger.debug('->"{}"'.format(lines[-1]))
            #     continue

            # pair = None
            # for p in CONSTANTS_PAIRS:
            #     if re.match(r'^.*'+p[0]+r'$', lines[-1]) and re.match(r'^'+p[1]+r'.*$', text):
            #         pair = p
            #         break
            #     if pair:
            #         lines[-1] += text
            #         logger.debug('->"{}"'.format(lines[-1]))
            #         exit()
            #         continue

        lines.append(text)

    # for text in texts:
    #     _texts.extend(text.split('\n'))
    # texts = _texts
    # i = 0
    # while i < len(_lines):
    #     line = _lines[i]
    #     print(i, line, len(_lines))
    #     if i < len(_lines) and len(line) == 1 and len(_lines[i + 1]) > 0:
    #         if re.match(r'^\d+$', line) and not re.match(r'^\d+.*$', _lines[i + 1]):
    #             line += '|'
    #         line += _lines[i + 1]
    #         i += 1

    #     line = line.strip().replace('  ', '|').replace(' ', '').replace('|', ' ')
    #     if len(line) > 0:
    #         lines.append(line)

    #     i += 1
    return lines


def read_nagoya_pdf_1(lines, debug=False, release_date=None, current_no=None):
    results = []
    patient = None
    term = None
    progress_date = None
    result = None
    stocks = []

    for line in lines:
        logger.debug('{}:{} > {}'.format(patient, term, line))

        # if re.match(r'^（令和\d+年\d+月\d+日.*）.*$', line):
        #     release_date = util.parse_japanese_date(
        #         re.sub(r'^（(令和\d+年\d+月\d+日).*）.*$', r'\1', line)
        #     ).strftime(r'%Y-%m-%d')
        #     if re.match(r'^.*(\(|（)本市公表\d+～\d+例目(\)|）)$', line):
        #         current_no = int(re.sub(r'.*本市公表(\d+)～.*$', r'\1', line))
        #     elif re.match(r'^.*(\(|（)本市公表\d+例目(\)|）)$', line):
        #         current_no = int(re.sub(r'.*本市公表(\d+)例目.*$', r'\1', line))

        if re.match(r'^(\d+|)(\s|)患者.*について.*$', line) and not re.match(r'^.*発生.*$', line):
            if result:
                results.append(result)
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

        elif re.match(r'^患者・御家族等の人権尊重・個人情報保護にご理解とご配慮をお願いします。.*$', line):
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
                        # if re.match(r'\d+(代|歳代)$', word):
                        #     result['age'] = re.sub(r'(\d+)(代|歳代)$', r'\1', word) + 's'
                        # elif re.match(r'\d+歳$', word):
                        #     result['age'] = re.sub(r'(\d+)歳$', r'\1', word) + 's'
                        # elif re.match(r'\d+歳未満$', word):
                        #     result['age'] = re.sub(r'(\d+)歳未満$', r'\1', word) + 'u'
                        # elif word == '不明':
                        #     result['age'] = 'unknown'
                        # else:
                        #     raise Exception('Age "{}" not defined'.format(word))
                        result['age'] = word_to_age(word)
                        if not result['age']:
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
                result['condition'] = re.sub(r'^主な症状：(.+)$', r'\1', line)

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
            if re.match(r'^\d+月\d+日\(.+\).*$', line.replace(' ', '')):
                line = line.replace(' ', '')
                if re.match(r'^\d+月\d+日\(.+\).+$', line):
                    progress_date, txt = re.sub(r'^(\d+月\d+日)\(.+\)(.*)$', r'\1 \2', line).split()
                    stocks.append(txt)
                else:
                    progress_date = re.sub(r'^(\d+月\d+日)\(.+\)$', r'\1', line)

                progress_date = util.parse_japanese_date('令和2年' + progress_date).strftime(r'%Y-%m-%d')

                if len(stocks) > 0:
                    progress = {
                        'date': progress_date,
                        'content': ''.join(stocks),
                    }
                    result['progress'].append(progress)
                    stocks = []
                    # progress_date = None

            elif progress_date:
                if re.match(r'^\d+$', line):
                    pass
                else:
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

            # elif len(stocks) == 0:
            #     stocks.append(line)

            else:
                stocks.append(line)
                # raise Exception('Illegal line "{}" file={}'.format(line, filepath))

        elif not term:
            continue

        else:
            raise Exception('Illegal line "{}"'.format(line))

    if result:
        results.append(result)

    return results


def parse_pdf_key_values(word):
    data = []
    key = None
    words = word.split(' ')

    if words[0] == r'本市公表':
        key = 'no'
    elif words[0] == r'年代':
        key = 'age'
    elif words[0] == r'症状':
        key = 'condition'
    elif words[0] == r'性別':
        key = 'sex'
    elif words[0] == r'国籍':
        key = 'nationality'
    elif words[0] == r'居住地':
        key = 'area'
    elif words[0] == r'発症日':
        key = 'onset_date'
    elif words[0] == r'陽性確定日':
        key = 'confirmed_date'
    elif words[0] == r'海外渡航歴':
        key = 'abroad_history'
    elif words[0] == r'特記事項':
        key = 'remarks'

    if key:
        if len(words) <= 1:
            data.append({'key': key})
        else:
            data.append({'key': key, 'value': words[1]})
            if len(words) >= 2:
                data.extend([{'value': w} for w in words[2:]])
    else:
        data.extend([{'value': w} for w in words])

    return data


# Read PDF (2020/7/20〜7/23)
def read_nagoya_pdf_2(lines, debug=False, release_date=None):
    if debug:
        logger.setLevel(logging.DEBUG)

    data = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^海外渡航歴.+$', line):
            lines[i], line_r = re.sub(r'^(海外渡航歴)(.+)$', r'\1|\2', line).split('|')
            lines[i+1:i+1] = [line_r]
            if re.match(r'^.+本市公表\d+例目.*$', lines[i+1]):
                lines[i+1], line_r = re.sub(r'^(.+)(本市公表\d+例目.*)$', r'\1|\2', lines[i+1]).split('|')
                lines[i+2:i+2] = [line_r]
                # logger.debug('"{}"->"{}","{}","{}"'.format(line, lines[i], lines[i+1], line_r))
            # else:
            #     logger.debug('"{}"->"{}","{}"'.format(line, lines[i], line_r))

        elif re.match(r'^―.+$', line):
            lines[i], line_r = re.sub(r'^(―)(.+)$', r'\1|\2', lines[i]).split('|')
            # logger.debug('"{}"->"{}","{}"'.format(line, lines[i], line_r))
            lines[i+1:i+1] = [line_r]
        i += 1

    for i, line in enumerate(lines):

        line = line.strip().replace('\n', '|')
        if len(line) == 0:
            continue

        results = parse_pdf_key_values(line)
        data.extend(results)

    results = []
    key = None
    result = None
    remarks = False

    for d in data:
        logger.debug('{}'.format(d))

        if d.get('value') and re.match(r'^.*人権尊重・個人情報保護にご理解とご配慮をお願いします。$', d.get('value')):
            results.append(result)
            logger.debug('========')
            break

        if d.get('key') == 'age' and result:
            results.append(result)
            logger.debug('--------')
            result = None
            remarks = False

        if d.get('key'):
            if not result:
                result = {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'progress': [],
                    'remarks': []
                }

            key = d['key']
            if key == 'remarks':
                remarks = True

        if not key:
            if not d.get('value'):
                raise Exception('No value')

            if remarks:
                if len(result['remarks']) == 0:
                    result['remarks'].append(d['value'])
                else:
                    result['remarks'][-1] += d['value']
                logger.debug('A> remarks:{}'.format(result['remarks'][-1]))
            else:
                logger.debug('I> %s', d['value'])
            continue

        if not d.get('value'):
            logger.debug('N> {}'.format(key))
            continue

        if key == 'no':
            if not re.match(r'^\d+例目$', d['value']):
                raise Exception('Invalid No "{}"'.format(d['value']))
            result[key] = int(re.sub(r'^(\d+)例目$', r'\1', d['value']))
            logger.debug('U> {}:{}'.format(key, result[key]))

        elif key == 'age':
            result[key] = word_to_age(d['value'])
            logger.debug('U> {}:{}'.format(key, result[key]))

        elif key == 'sex':
            if d['value'] == '男性':
                result[key] = 'male'
            elif d['value'] == '女性':
                result[key] = 'female'
            elif d['value'] == '不明':
                result[key] = 'unknown'
            else:
                raise Exception('Sex "{}" not defined'.format(d['value']))
            logger.debug('U> {}:{}'.format(key, result[key]))

        elif key in ['area', 'condition', 'abroad_history']:
            result[key] = d['value']
            logger.debug('U> {}:{}'.format(key, result[key]))

        elif key in ['onset_date', 'confirmed_date']:
            if d['value'] in [r'―', r'調査中']:
                result[key] = 'unknown'
            else:
                if not re.match(r'^\d+月\d+日$', d['value']):
                    raise Exception('Invalid {} value "{}"'.format(key, d['value']))
                result[key] = util.parse_japanese_date(r'令和2年' + d['value']).strftime(r'%Y-%m-%d')
            logger.debug('U> {}:{}'.format(key, result[key]))

        else:
            raise Exception('Unknown value key:{} value:"{}"'.format(key, d['value']))

        key = None
        if result.get('remarks'):
            remarks = False

    return results


# Read PDF (2020-07-24〜)
def read_nagoya_pdf_3(filepath, debug=False, release_date=None):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    lines = read_pdf_lines(filepath, debug)

    results = []
    ii = -1
    HEADERS = {
        'no': '本市公表',
        'age': '年代',
        'sex': '性別',
        'area': '居住地',
        'abroad_history': '海外渡航歴',
        'onset_date': '発症日',
        'confirmed_date': '陽性確定日',
        'condition_level': '重症度',
        'remarks': '特記事項',
    }

    for i, line in enumerate(lines):
        if re.match(r'^本市公表', line):
            ii = i
            break
    if ii < 0:
        raise Exception('Cannot find start word "本市公表" file:{}'.format(filepath))
    lines = lines[ii:]

    i = 0
    ii = 0
    headers = list(HEADERS.values())

    while ii < len(headers) and re.match(r'^'+headers[ii], lines[i]):
        line = lines[i]
        while len(line) > 0:
            line = re.sub(r'^'+headers[ii], '', line)
            ii += 1
        i += 1
    lines = lines[i:]

    i = 0
    ii = 0
    keys = list(HEADERS.keys())
    result = None
    lastkey = None

    while i < len(lines):

        # if (result or {}).get('no', 0) > 3741:
        #     exit()

        key = keys[ii]

        # if ((result or {}).get('no') or 0) >= 2458:
        #     exit()

        line = lines[i]
        if re.match(r'^\d+(調査中)(男|女)$', line):
            words = re.sub(r'^(\d+)(調査中)(男|女)$', r'\1 \2 \3', line).split()
            logger.debug('"{}"->{}'.format(line, words))
            lines[i:i+1] = words
        elif re.match(r'^(男|女).+(都|道|府|県|市|町|村)$', line):
            words = re.sub(r'^(男|女)(.+)(都|道|府|県|市|町|村)$', r'\1 \2\3', line).split()
            logger.debug('"{}"->{}'.format(line, words))
            lines[i:i+1] = words
        elif re.match(r'^(男|女)(なし)$', line):
            words = re.sub(r'^(男|女)(.+)$', r'\1 \2', line).split()
            logger.debug('"{}"->{}'.format(line, words))
            lines[i:i+1] = words
        elif re.match(r'^(軽症|中等症|重症).+$', line):
            words = re.sub(r'^(軽症|中等症|重症)(.+)$', r'\1 \2', line).split()
            logger.debug('"{}"->{}'.format(line, words))
            lines[i:i+1] = words
        elif re.match(r'^(-|―|－|−).+$', line):
            words = re.sub(r'^(-|―|－|−)(.+)$', r'- \2', line).split()
            logger.debug('"{}"->{}'.format(line, words))
            lines[i:i+1] = words
        elif re.match(r'^.+[^、]本市公表\d+例目.*$', line):
            words = re.sub(r'^(.+)(本市公表\d+例目.*)$', r'\1 \2', line).split()
            logger.debug('"{}"->{}'.format(line, words))
            lines[i:i+1] = words

        line = lines[i]
        logger.debug('{} - {}'.format(key, line))

        if key == 'no' and re.match(r'^\d+$', line):
            if len(results) > 0 and not results[-1].get('age'):
                if not re.match(r'^(\d{1,2}0)(歳|)$', line):
                    raise Exception('Invalid text for age, "{}" file:{}'.format(line, filepath))
                lastkey = 'age'
                results[-1]['age'] = re.sub(r'歳$', '', line) + 's'
                logger.debug('({}) age*:{}'.format(results[-1]['no'], results[-1]['age']))
                i += 1
                continue

            elif (result or {}).get('no'):
                if not result.get('age') and re.match(r'^(\d{1,2}0)(歳|)$', line):
                    lastkey = 'age'
                    result['age'] = line + 's'
                    logger.debug('age:{}'.format(result['age']))
                    i += 1
                    continue
                else:
                    results.append(result)
                    logger.debug('-----')
                    result = None
                    continue

            elif len(results) == 0 or (len(results) > 0 and int(line) == results[-1]['no'] + 1):
                lastkey = 'no'
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['no'] = int(line)
                logger.debug('no:{}'.format(result['no']))
                ii = 0

            elif not (result or {}).get('age'):
                if not re.match(r'^(\d{1,2}0)(歳|)$', line):
                    raise Exception('Invalid text for no/age, "{}" file:{}'.format(line, filepath))
                lastkey = 'age'
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['age'] = line + 's'
                logger.debug('age:{}'.format(result['age']))
                i += 1
                continue

            else:
                raise Exception('Invalid text for no, "{}" file:{}'.format(line, filepath))
                # logger.debug('->pass')
                # ii = (ii + 1) % len(keys)
                # continue

        elif key == 'age':
            if (result or {}).get('age'):
                logger.debug('age:->pass')
                ii = (ii + 1) % len(keys)
                continue
            elif re.match(r'^([1-9]0|100)(歳|)$', line):
                lastkey = 'age'
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['age'] = re.sub(r'^(\d+).*$', r'\1', line) + 's'
                logger.debug('age:{}'.format(result['age']))
            elif line in ['調査中', '―', '－']:
                lastkey = 'age'
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['age'] = 'unknown'
                logger.debug('age:{}'.format(result['age']))
            else:
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue

        elif re.match(r'^([1-9]0|100)(歳|)(未満|)$', line):
            lastkey = 'age'
            if len(results) > 0 and not results[-1].get('age'):
                results[-1]['age'] = re.sub(r'^(\d+).*$', r'\1', line)
                results[-1]['age'] += 'u' if re.match(r'^.+未満$', line) else 's'
                logger.debug('({}) age:{}'.format(results[-1]['no'], results[-1]['age']))
            elif not (result or {}).get('age'):
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['age'] = re.sub(r'^(\d+).*$', r'\1', line)
                result['age'] += 'u' if re.match(r'^.+未満$', line) else 's'
                logger.debug('age:{}'.format(result['age']))
            elif result and result.get('no'):
                results.append(result)
                logger.debug('-----')
                result = None
                ii = 0
                continue
            else:
                raise Exception('Invalid text for age, "{}" file:{}'.format(line, filepath))
            i += 1
            continue

        elif re.match(r'^10歳未満$', line):
            lastkey = 'age'
            if len(results) > 0 and not results[-1].get('age'):
                results[-1]['age'] = '10u'
                logger.debug('({}) age:{}'.format(results[-1]['no'], results[-1]['age']))
            elif not (result or {}).get('age'):
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['age'] = '10u'
                logger.debug('age:{}'.format(result['age']))
            elif result and result.get('no'):
                results.append(result)
                logger.debug('-----')
                result = None
                ii = 0
                continue
            else:
                raise Exception('Invalid text for age, "{}" file:{}'.format(line, filepath))
            i += 1
            continue

        elif line == '未満':
            lastkey = 'age'
            if (result or {}).get('age'):
                result['age'] = re.sub(r's$', 'u', result['age'])
                logger.debug('age*:{}'.format(result['age']))
            elif len(results) > 0 and results[-1].get('age'):
                results[-1]['age'] = re.sub(r's$', 'u', results[-1]['age'])
                logger.debug('({}) age*:{}'.format(results[-1]['no'], results[-1]['age']))
            else:
                raise Exception('Invalid text for age, "{}" file:{}'.format(line, filepath))
            i += 1
            continue

        # elif line == '満':
        #     lastkey = 'age'
        #     if re.match(r'^\d+u$', (result or {}).get('age') or ''):
        #         logger.debug('age*:{}'.format(result['age']))
        #     elif len(results) > 0 and re.match(r'^\d+u$', results[-1].get('age') or ''):
        #         logger.debug('({}) age*:{}'.format(results[-1]['no'], results[-1]['age']))
        #     else:
        #         raise Exception('Invalid text for age, "{}" file:{}'.format(line, filepath))
        #     i += 1
        #     continue

        elif not (result or {}).get('no') and re.match(r'^\d+$', line):
            lastkey = 'no'
            if not result:
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['no'] = int(line)
                logger.debug('no:{}'.format(result['no']))
                ii = 0
            else:
                result['no'] = int(line)
                logger.debug('no:{}'.format(result['no']))
                i += 1
                continue

        elif key == 'sex':
            lastkey = 'sex'
            if (result or {}).get('sex'):
                logger.debug('sex:->pass')
                # results.append(result)
                # logger.debug('-----')
                # result = {
                #     'release_date': release_date,
                #     'remarks': []
                # }
            elif re.match(r'^(男|女)$', line):
                result['sex'] = word_to_sex(line)
                logger.debug('sex:{}'.format(result['sex']))
            elif line in ['調査中', '―', '－']:
                result['sex'] = 'unknown'
                logger.debug('area:{}'.format(result['sex']))
            else:
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue

        elif re.match(r'^(男|女)$', line):
            if (result or {}).get('sex'):
                # raise Exception('Invalid text for sex, "{}" file:{}'.format(line, filepath))
                results.append(result)
                logger.debug('-----')
                result = None
                ii = 0
                continue

            lastkey = 'sex'
            result = result or {
                'release_date': release_date,
                'government': 'nagoya',
                'remarks': []
            }
            result['sex'] = word_to_sex(line)
            logger.debug('sex:{}'.format(result['sex']))
            i += 1
            continue

        elif key == 'area':
            lastkey = 'area'
            if (result or {}).get('area'):
                logger.debug('area:->pass')
                ii = (ii + 1) % len(keys)
                continue
            elif re.match(r'^.+(都|道|府|県|市|町|村)$', line):
                result['area'] = line
                logger.debug('area:{}'.format(result['area']))
            elif line in ['調査中', '―', '－']:
                result['area'] = 'unknown'
                logger.debug('area:{}'.format(result['area']))
            elif re.match(r'^(なし)$', line):
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue
            else:
                raise Exception('Invalid text for {}, "{}" file:{}'.format(key, line, filepath))

        elif re.match(r'^.+(都|道|府|県|市|町|村)$', line):
            lastkey = 'area'
            if (result or {}).get('area'):
                raise Exception('Invalid text for area, "{}" file:{}'.format(line, filepath))
            result['area'] = line
            logger.debug('area:{}'.format(result['area']))

        elif key == 'abroad_history':
            if re.match(r'^\d+月\d+日$', line):
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue
            lastkey = 'abroad_history'
            if line in ['調査中', '―', '－']:
                result['abroad_history'] = 'unknown'
            else:
                result['abroad_history'] = line
            logger.debug('abroad_history:{}'.format(result['abroad_history']))

        elif key == 'onset_date':
            if re.match(r'^\d+月\d+日$', line):
                if result.get(key):
                    logger.debug('{}:->pass({})'.format(key, result[key]))
                    ii = (ii + 1) % len(keys)
                    continue
                else:
                    lastkey = 'onset_date'
                    result[key] = util.parse_japanese_date('令和2年'+line).strftime(r'%Y-%m-%d')
                    logger.debug('{}:{}'.format(key, result[key]))
            elif line in ['-', '―', '－', '調査中']:
                lastkey = 'onset_date'
                result[key] = 'unknown'
                logger.debug('{}:{}'.format(key, result[key]))
            elif result.get('no') == 1639 and re.match(r'^\d+月月\d+日$', line):
                lastkey = 'onset_date'
                result[key] = util.parse_japanese_date('令和2年'+line.replace('月月', '月')).strftime(r'%Y-%m-%d')
                logger.debug('{}:*{}'.format(key, result[key]))
            else:
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue

        elif key == 'confirmed_date':
            if re.match(r'^\d+月\d+日$', line):
                if result.get(key):
                    logger.debug('{}:->pass({})'.format(key, result[key]))
                    ii = (ii + 1) % len(keys)
                    continue
                else:
                    lastkey = 'confirmed_date'
                    result[key] = util.parse_japanese_date('令和2年'+line).strftime(r'%Y-%m-%d')
                    logger.debug('{}:{}'.format(key, result[key]))
            elif line in ['-', '―', '－', '調査中']:
                lastkey = 'onset_date'
                result[key] = 'unknown'
                logger.debug('{}:{}'.format(key, result[key]))
            else:
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue

        elif re.match(r'^\d+月\d+日$', line):
            # if not result:
            #     raise Exception('Invalid text for date, "{}" file:{}'.format(line, filepath))
            result = result or {
                'release_date': release_date,
                'government': 'nagoya',
                'remarks': []
            }
            if not result.get('onset_date'):
                lastkey = 'onset_date'
                result['onset_date'] = util.parse_japanese_date('令和2年'+line).strftime(r'%Y-%m-%d')
                logger.debug('onset_date:{}'.format(result['onset_date']))
                i += 1
                continue
            elif not result.get('confirmed_date'):
                lastkey = 'confirmed_date'
                result['confirmed_date'] = util.parse_japanese_date('令和2年'+line).strftime(r'%Y-%m-%d')
                logger.debug('confirmed_date:{}'.format(result['confirmed_date']))
                i += 1
                continue
            else:
                # raise Exception('Invalid text for date, "{}" file:{}'.format(line, filepath))
                results.append(result)
                logger.debug('-----')
                result = None
                ii = 0
                continue

        elif key == 'condition_level':
            if (result or {}).get('condition_level'):
                logger.debug('condition_level:->pass')
                ii = (ii + 1) % len(keys)
                continue
            elif line in ['なし', '軽症', '中等症', '重症', '調査中']:
                lastkey = 'condition_level'
                result['condition_level'] = line
                logger.debug('condition_level:{}'.format(result['condition_level']))
                if result.get('remarks'):
                    results.append(result)
                    logger.debug('-----')
                    result = None
            elif line in ['-', '―', '－']:
                lastkey = 'condition_level'
                result[key] = 'unknown'
                logger.debug('{}:{}'.format(key, result[key]))
                if result.get('remarks'):
                    results.append(result)
                    logger.debug('-----')
                    result = None
            else:
                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue

        elif line in ['軽症', '中等症', '重症']:
            if not result.get('condition_level'):
                lastkey = 'condition_level'
                result['condition_level'] = line
                logger.debug('condition_level:{}'.format(result['condition_level']))
            else:
                raise Exception('Invalid text for condition_level, "{}" file:{}'.format(line, filepath))
            i += 1
            continue

        elif line in ['なし', '調査中']:
            if not result.get('abroad_history'):
                lastkey = 'abroad_history'
                result['abroad_history'] = line
                logger.debug('abroad_history:{}'.format(result['abroad_history']))
            elif not result.get('condition_level'):
                lastkey = 'condition_level'
                result['condition_level'] = line
                logger.debug('condition_level:{}'.format(result['condition_level']))
            else:
                raise Exception('Invalid text for abroad_history/condition_level, "{}" file:{}'.format(line, filepath))
            i += 1
            continue

        elif key == 'remarks':
            if re.match(r'^\d+$', line) or re.match(r'^([1-9]0|100|[1-9]0歳|100歳|調査中)$', line):
                if result:
                    if result.get('onset_date') and not result.get('confirmed_date'):
                        result['confirmed_date'] = result['onset_date']
                        result['onset_date'] = 'unknown'
                        logger.debug('onset_date*:{}'.format(result['onset_date']))
                        logger.debug('confirmed_date*:{}'.format(result['confirmed_date']))
                    # results.append(result)
                    # logger.debug('-----')
                    # result = None

                logger.debug('->pass')
                ii = (ii + 1) % len(keys)
                continue

            elif re.match(r'^(県内\d+例目|県内公表\d+例目|本市公表\d+例目|市内\d+例目|.+県\d+例目).*$', line) or re.match(r'^.+滞在$', line):
                if result and len(result['remarks']) == 0:
                    result['remarks'].append(line)
                    logger.debug('remarks:{}'.format('|'.join(result['remarks'])))

                    if result.get('no'):
                        if result.get('onset_date') and not result.get('confirmed_date'):
                            result['confirmed_date'] = result['onset_date']
                            result['onset_date'] = 'unknown'
                            logger.debug('onset_date:*{}'.format(result['onset_date']))
                            logger.debug('confirmed_date:*{}'.format(result['confirmed_date']))
                        # results.append(result)
                        # logger.debug('-----')
                        # result = None

                elif result and re.match(r'^.*(及び|・)$', result['remarks'][-1]):
                    result['remarks'][-1] += line
                    logger.debug('+remarks:{}'.format('|'.join(result['remarks'])))

                elif len(results) > 0 and len(results[-1]['remarks']) == 0:
                    results[-1]['remarks'].append(line)
                    logger.debug('({}) remarks:{}'.format(results[-1]['no'], '|'.join(results[-1]['remarks'])))

                elif len(results) > 0 and re.match(r'^.*(及び|・)$', '|'.join(results[-1]['remarks'])):
                    results[-1]['remarks'][-1] += line
                    logger.debug('({}) +remarks:{}'.format(results[-1]['no'], '|'.join(results[-1]['remarks'])))

                elif not result:
                    result = {
                        'release_date': release_date,
                        'government': 'nagoya',
                        'remarks': [line]
                    }
                    logger.debug('remarks:{}'.format('|'.join(result['remarks'])))

                else:
                    raise Exception('Invalid text for remarks, "{}" file:{}'.format(line, filepath))

            elif re.match(r'^.+と接触$', line):
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['remarks'].append(line)
                logger.debug('remarks:{}'.format('|'.join(result['remarks'])))

            elif re.match(r'^.+から検査$', line):
                if result and re.match(r'^\d+月\d+.+から検査$', line):
                    result['remarks'].append(line)
                    logger.debug('remarks:{}'.format('|'.join(result['remarks'])))
                elif result and len(result['remarks']) > 0:
                    result['remarks'][-1] += line
                    logger.debug('remarks*:{}'.format('|'.join(result['remarks'])))
                elif len(results) > 0 and len(results[-1]['remarks']) > 0:
                    results[-1]['remarks'][-1] += line
                    logger.debug('({}) remarks*:{}'.format(results[-1]['no'], '|'.join(results[-1]['remarks'])))
                elif result and len(result.get('remarks', [])) == 0:
                    result['remarks'].append(line)
                else:
                    raise Exception('Invalid text for remarks, "{}" file:{}'.format(line, filepath))

            elif result and len(result['remarks']) > 0:
                result['remarks'].append(line)
                logger.debug('remarks:{}'.format('|'.join(result['remarks'])))

                if result.get('no'):
                    if result.get('onset_date') and not result.get('confirmed_date'):
                        result['confirmed_date'] = result['onset_date']
                        result['onset_date'] = 'unknown'
                        logger.debug('onset_date:*{}'.format(result['onset_date']))
                        logger.debug('confirmed_date:*{}'.format(result['confirmed_date']))
                    results.append(result)
                    logger.debug('-----')

                    # if result['no'] >= 1520:
                    #     pprint(results[-3:])
                    #     exit()
                    result = None

            elif len(results) > 0 and len(results[-1]['remarks']) > 0:
                results[-1]['remarks'][-1] += line
                logger.debug('({}) remarks+:{}'.format(results[-1]['no'], '|'.join(results[-1]['remarks'])))

            else:
                result = result or {
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                result['remarks'].append(line)
                logger.debug('remarks:{}'.format('|'.join(result['remarks'])))
            lastkey = 'remarks'

        elif re.match(r'^\d+$', line):
            lastkey = 'no'
            if not result:
                result = {
                    'no': int(line),
                    'release_date': release_date,
                    'government': 'nagoya',
                    'remarks': []
                }
                logger.debug('no:{}'.format(result['no']))
                ii = 0
            elif not result.get('no'):
                result['no'] = int(line)
                logger.debug('no:{}'.format(result['no']))
                i += 1
                continue
            else:
                raise Exception('Invalid text for no, "{}" file:{}'.format(line, filepath))

        elif re.match(r'^(県内\d+例目|本市公表\d+例目|市内\d+例目|岐阜県\d+例目).*$', line) or \
                re.match(r'^.+(滞在|検査)$', line):
            if result and len(result['remarks']) > 0:
                if lastkey == 'remarks':
                    result['remarks'].append(line)
                    logger.debug('remarks+:{}'.format('|'.join(result['remarks'])))
                elif result.get('no'):
                    if result.get('onset_date') and not result.get('confirmed_date'):
                        result['confirmed_date'] = result['onset_date']
                        result['onset_date'] = 'unknown'
                        logger.debug('onset_date*:{}'.format(result['onset_date']))
                        logger.debug('confirmed_date*:{}'.format(result['confirmed_date']))
                else:
                    raise Exception('Invalid text for remarks, "{}" file:{}'.format(line, filepath))
            elif len(results) > 0 and len(results[-1]['remarks']) == 0:
                results[-1]['remarks'].append(line)
                logger.debug('({}) remarks:{}'.format(results[-1]['no'], '|'.join(results[-1]['remarks'])))
            elif result:
                result['remarks'].append(line)
                logger.debug('remarks:{}'.format('|'.join(result['remarks'])))
                if result.get('no'):
                    if result.get('onset_date') and not result.get('confirmed_date'):
                        result['confirmed_date'] = result['onset_date']
                        result['onset_date'] = 'unknown'
                        logger.debug('onset_date*:{}'.format(result['onset_date']))
                        logger.debug('confirmed_date*:{}'.format(result['confirmed_date']))
                    results.append(result)
                    logger.debug('-----')
                    result = None
            else:
                result = {
                    'release_date': release_date,
                    'remarks': []
                }
                result['remarks'].append(line)
                logger.debug('remarks:{}'.format('|'.join(result['remarks'])))
            i += 1
            continue

        elif result and result.get('no'):
            if len(result['remarks']) > 0:
                if lastkey == 'remarks':
                    if re.match(r'^.*(及び|、|・)$', result['remarks'][-1]) or re.match(r'^(及び|の|男|女).+$', line):
                        result['remarks'][-1] += line
                        logger.debug('remarks*:{}'.format('|'.join(result['remarks'])))
                    else:
                        result['remarks'].append(line)
                        logger.debug('remarks+:{}'.format('|'.join(result['remarks'])))
                    i += 1
                    continue
                else:
                    raise Exception('Invalid text for remarks, "{}" file:{}'.format(line, filepath))

            lastkey = 'remarks'
            result['remarks'].append(line)
            logger.debug('remarks:{}'.format('|'.join(result['remarks'])))
            if result.get('onset_date') and not result.get('confirmed_date'):
                result['confirmed_date'] = result['onset_date']
                result['onset_date'] = 'unknown'
                logger.debug('onset_date*:{}'.format(result['onset_date']))
                logger.debug('confirmed_date*:{}'.format(result['confirmed_date']))
            results.append(result)
            logger.debug('-----')
            result = None
            i += 1
            continue

        elif lastkey == 'remarks':
            if result and len(result['remarks']) > 0:
                if re.match(r'^.*(及び|、|・|・)$', result['remarks'][-1]) or re.match(r'^(及び|の|男|女).+$', line):
                    result['remarks'][-1] += line
                    logger.debug('remarks*:{}'.format('|'.join(result['remarks'])))
                else:
                    result['remarks'].append(line)
                    logger.debug('remarks+:{}'.format('|'.join(result['remarks'])))
            elif len(results) > 0 and len(results[-1]['remarks'][-1]) > 0:
                results[-1]['remarks'][-1] += line
                logger.debug('({}) remarks*:{}'.format(results[-1]['no'], '|'.join(results[-1]['remarks'])))
            else:
                raise Exception('Invalid text for remarks, "{}" file:{}'.format(line, filepath))
            i += 1
            continue

        elif result and len(result['remarks']) > 0:
            lastkey = 'remarks'
            result['remarks'][-1] += line
            logger.debug('+remarks:{}'.format('|'.join(result['remarks'])))
            i += 1
            continue

        # elif len(results) > 0:
        #     lastkey = 'remarks'
        #     if len(results[-1]['remarks'][-1]) == 0:
        #         results[-1]['remarks'].append(line)
        #         logger.debug('({}) remarks:{}'.format(results[-1]['no'], results[-1]['remarks'][-1]))
        #     else:
        #         results[-1]['remarks'][-1] += line
        #         logger.debug('({}) +remarks:{}'.format(results[-1]['no'], results[-1]['remarks'][-1]))
        #     i += 1
        #     continue

        else:
            raise Exception('Invalid text "{}" file:{}'.format(line, filepath))

        ii = (ii + 1) % len(keys)
        i += 1

    if result:
        if result.get('onset_date') and not result.get('confirmed_date'):
            result['confirmed_date'] = result['onset_date']
            result['onset_date'] = 'unknown'
            logger.debug('onset_date:*{}'.format(result['onset_date']))
            logger.debug('confirmed_date:*{}'.format(result['confirmed_date']))
        results.append(result)

    return results


# Read PDF
def read_nagoya_pdf(filepath, debug=False, release_date=None, last_release_date=None):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    results = []

    if re.match(r'^(|.*\/)R20214kisya\.pdf$', filepath):
        release_date = '2020-02-14'
        if last_release_date and release_date <= last_release_date:
            logger.info('Pass to read PDF: release_date={}'.format(release_date))
            return None

        logger.warning('Invalid PDF file {}'.format(filepath))
        results.append({
            'release_date': release_date,
            'government': 'nagoya',
            'no': 1
        })
        return results

    lines = read_pdf_lines(filepath, debug)

    header_index = None
    for i, line in enumerate(lines):
        if re.match(r'^（令和\d+年\d+月\d+日.*）.*$', line):
            header_index = i
            break

    if not header_index:
        raise Exception('Cannot find release date from file:{}'.format(filepath))

    if not release_date:
        release_date = util.parse_japanese_date(
            re.sub(r'^（(令和\d+年\d+月\d+日).*）.*$', r'\1', lines[header_index])
        ).strftime(r'%Y-%m-%d')

    if last_release_date and release_date <= last_release_date:
        logger.info('Pass to read PDF: release_date={}'.format(release_date))
        return None

    current_no = None
    if re.match(r'^.*(\(|（)本市公表\d+～\d+例目(\)|）)$', lines[header_index]):
        current_no = int(re.sub(r'.*本市公表(\d+)～.*$', r'\1', lines[header_index]))
        no_s = re.sub(r'.*本市公表(\d+)～(\d+)例目.*$', r'\1 \2', lines[header_index]).split()
        current_no = int(no_s[0])
        logger.debug('[{} No.{}〜{}]'.format(release_date, no_s[0], no_s[1]))
    elif re.match(r'^.*(\(|（)本市公表\d+例目(\)|）)$', lines[header_index]):
        current_no = int(re.sub(r'.*本市公表(\d+)例目.*$', r'\1', lines[header_index]))
        logger.debug('[{} No.{}]'.format(release_date, current_no))
    else:
        logger.debug('[{}]'.format(release_date))

    lines = lines[header_index+1:]

    if release_date <= '2020-07-19':
        try:
            results = read_nagoya_pdf_1(lines, release_date=release_date, current_no=current_no)
        except Exception as e:
            raise Exception('{} / file:{}'.format(e, filepath))
    elif release_date <= '2020-07-23':
        try:
            results = read_nagoya_pdf_2(lines, release_date=release_date)
        except Exception as e:
            raise Exception('{} / file:{}'.format(e, filepath))
    else:
        results = read_nagoya_pdf_3(filepath, release_date=release_date, debug=debug)

    return results


def scrape_releases(last_release_date=None, debug=False):
    releases = scrape_nagoya_press_releases()
    results = []
    no = 0

    for i, release in enumerate(releases):
        filename = re.sub(r'^.*\/([^\/]+)$', r'\1', release['pdf_url'])
        filepath = os.path.join(config.DATA_DIR, 'nagoya', filename)

        if last_release_date and release['date'] <= last_release_date:
            continue

        if release['date'] <= '2020-07-23':
            _results = read_nagoya_pdf(filepath, release_date=release['date'], last_release_date=last_release_date, debug=debug)
        else:
            _results = read_nagoya_pdf_3(filepath, release_date=release['date'], debug=debug)
            logger.info(filepath)

        if not _results:
            continue

        logger.debug('read PDF {}/{}'.format(i + 1, len(releases)))
        for r in _results:
            if r['release_date'] == '2020-04-30' and r.get('no') == 272:
                print('(pass)', r)
                continue

            no += 1
            if no in [2, 56, 81]:
                no += 1

            if not r.get('no'):
                r['no'] = no

            r.update({
                'government': 'nagoya',
                'url': release['pdf_url']
            })
            r['progress'] = r.get('progress') or []
            r['remarks'] = r.get('remarks') or []

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

    # releases = scrape_nagoya_press_releases()
    # pprint(releases)
    # results = read_nagoya_pdf('data/nagoya/R21110kisyahappyou2.pdf', debug=True)
    # exit()

    last_release_date = None
    current_details = Detail.find_by_government('nagoya', order=['-no'], limit=1)
    if len(current_details) > 0:
        last_release_date = current_details[0]['release_date']

    details = scrape_releases(last_release_date=last_release_date)
    details = list(map(lambda d: revise_detail(d), details))

    for detail in details:
        pprint(detail)
        Detail.insert(detail)
        logger.info('Add Nagoya detail [%s]', detail['no'])

    exit()
