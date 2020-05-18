import settings  # noqa: F401
import urllib.parse
import pandas as pd
from datetime import date  # noqa: F401
import re
import os
from pprint import pprint
import app.lib.log as log
import config
import app.lib.util as util
import app.models.Person as Person
import app.models.Soup as Soup
import app.models.PDFReader as PDFReader

logger = log.getLogger('get_persons')

ROWS_START_INDEX = 9
COUNTRIES = [
    '中国', 'アメリカ', 'フランス', 'イタリア',
    'イギリス', 'カナダ', 'オーストラリア', 'ナイジェリア',
    'ノルウェー', 'タイ', 'フィリピン', '欧州'
]
SPOTS = [
    '店舗', 'ライブハウス', 'スポーツジム', '合唱団'
]
GOVERNMENTS = {
    'aichi': '愛知県',
    'nagoya': '名古屋市',
    'okazaki': '岡崎市',
    'toyota': '豊田市',
    'toyohashi': '豊橋市',
}


def read_aichi_release():
    result = {}
    url = config.AICHI_SUMMARY_URL
    soup = Soup.create_soup(url)

    main_a = soup.body.select_one('#main_a')
    text_r = main_a.select_one('.text_r')
    if not re.match(r'^.*掲載日[^\d]*\d+年\d+月\d+日.*$', text_r.text):
        raise Exception('current_date not found in {}'.format(url))

    year, month, day = \
        re.sub(r'^.*掲載日[^\d]*(\d+)年(\d+)月(\d+)日.*$', r'\1 \2 \3', text_r.text).split()
    result['current_date'] = \
        date(year=int(year), month=int(month), day=int(day))
    main_a = soup.body.select_one('#main_body')
    detail_free = main_a.select_one('.detail_free')
    h2s = detail_free.select('h2')

    for h2 in h2s:
        if re.match(r'^.*愛知県内発生事例$', h2.text):
            tag = h2.find_next_sibling()
            a_s = []
            while tag.name != 'h2':
                if tag.name == 'a':
                    a_s.appenf(tag)
                else:
                    a_s.extend(tag.select('a'))

                tag = tag.find_next_sibling()

            for a in a_s:
                if re.match(r'^.*県内発生事例一覧\(\d+月\d+日現在\).*\[Excelファイル.*\]$', a.text):
                    month, day = \
                        re.sub(r'^.*\((\d+)月(\d+)日現在\).*$', r'\1 \2', a.text).split()
                    result['excel'] = {
                        'current_date': date(year=2020, month=int(month), day=int(day)),
                        'url': urllib.parse.urljoin(url, a['href'])
                    }
                # 県内発生事例一覧（5月15日現在） [PDFファイル／173KB]
                elif re.match(r'^.*県内発生事例一覧(\(|（)\d+月\d+日現在(\)|）).*\[PDFファイル.*\]$', a.text):
                    month, day = \
                        re.sub(r'^.*(\(|（)(\d+)月(\d+)日現在.*$', r'\2 \3', a.text).split()
                    result['pdf'] = {
                        'current_date': date(year=2020, month=int(month), day=int(day)),
                        'url': urllib.parse.urljoin(url, a['href'])
                    }

    return result


# Read PDF
def read_release_pdf(filepath, debug=False):
    result = {}
    texts = PDFReader.read_textboxes(filepath)

    # 令和2年5月5日現在
    if not re.match(r'^令和\d+年\d+月\d+日現在$', texts[1]):
        raise Exception('Current date not found. {}'.format(filepath))
    result['current_date'] = \
        util.parse_japanese_date(re.sub(r'現在$', '', texts[1])).strftime(r'%Y-%m-%d')

    texts = texts[9:]
    persons = []
    i = 0
    while i < len(texts):
        person = {
            'release_date': '',
            'age': 'unknown',
            'sex': 'unknown',
            'nationality': '',
            'reason': 'unknown',
            'route': {},
            'remarks': []
        }

        # No.
        if not str.isdecimal(texts[i]):
            raise Exception('Inbalid No. {}'.format(texts[i]))
        person['no'] = int(texts[i])
        i += 1

        # date,age/sex
        words = texts[i].split()
        if len(words) == 0:
            raise Exception('Inbalid date,age/sex. {}'.format(texts[i]))
        if not re.match(r'^\d+月\d+日$', words[0]):
            raise Exception('Inbalid date. {}'.format(texts[i]))
        month, day = re.sub(r'^(\d+)月(\d+)日$', r'\1 \2', words[0]).split()
        person['release_date'] = date(2020, int(month), int(day)).strftime(r'%Y-%m-%d')

        if len(words) >= 2:
            ws = \
                re.sub(r'(\d+代|\d+歳|\d+歳代|\d+歳未満)(男性|女性)$', r'\1 \2', words[1]).split()
            if len(ws) > 0:
                if re.match(r'\d+(代|歳代|歳)$', ws[0]):
                    person['age'] = re.sub(r'(\d+)(代|歳代|歳)$', r'\1', ws[0]) + 's'
                elif re.match(r'\d+歳未満$', ws[0]):
                    person['age'] = re.sub(r'(\d+)歳未満$', r'\1', ws[0]) + 'u'
                else:
                    raise Exception('Invalid age "{}"'.format(texts[i]))

            if len(ws) > 1:
                if ws[1] == '男性':
                    person['sex'] = 'male'
                elif ws[1] == '女性':
                    person['sex'] = 'female'
                else:
                    raise Exception('Invalid sex "{}"'.format(texts[i]))
        i += 1

        # nationality
        if texts[i] in ['日本', '中国', '外国籍　']:
            person['nationality'] = texts[i]
            i += 1

        # area
        person['area'] = texts[i]
        i += 1
        if len(texts[i].split()) >= 2:
            texts[i:i + 1] = texts[i].split()
        if str.isdecimal(texts[i]):
            persons.append(person)
            continue

        # route,reason
        if re.match(r'^.+接触.+(県|市)発表(\d+|)$', texts[i]):
            texts[i:i + 1] = re.sub(r'^(.+接触)(.+発表\d+)$', r'\1 \2', texts[i]).split()

        if not re.match(r'^.+(県|市)発表(\d+|)$', texts[i]):
            person['route']['text'] = texts[i]
            rels = []

            if re.match(r'^.+(の|と)(夫|妻|娘|兄弟|姉妹|家族)$', texts[i]):
                person['reason'] = 'contact'
                words = re.sub(r'(、|、|,)', ' ', texts[i]).split()
                for word in words:
                    descs = \
                        re.sub(r'(^.+)(の|と)(夫|妻|娘|兄弟|姉妹|家族)$', r'\1 \3', word).split()
                    if len(descs) <= 2:
                        descs.append(re.sub(r'^.*(夫|妻|娘|兄弟|姉妹|家族)$', r'\1', texts[i]))
                    rels.append(
                        {'desc': descs[0],
                        'relationship': descs[1]})
            elif re.match(r'^.+と接触.*$', texts[i]):
                person['reason'] = 'contact'
                words = re.sub(r'(、|,)', ' ', texts[i]).split()
                for word in words:
                    if re.match(r'^.+と接触.+$', word):
                        desc, relationship = \
                            re.sub(r'^(.+)と接触(.+)$', r'\1 \2', word).split()
                        relationship = re.sub(r'(（|）)', '', relationship)
                        rels.append(
                            {'desc': desc,
                            'relationship': relationship})
                    elif re.match(r'^.+と接触$', word):
                        desc = re.sub(r'^(.+)と接触$', r'\1', word)
                        rels.append({'desc': desc})
                    else:
                        rels.append({'desc': word})

            if person['reason'] == 'contact':
                person['contacts'] = []

                for rel in rels:
                    descs = re.sub(r'(、|,|又は)', ' ', rel['desc']).split()

                    for desc in descs:
                        desc = re.sub(r'(No.|等)', '', desc)
                        if re.match(r'^\d+(~|～|〜)\d+$', desc):
                            start, end = re.sub(r'(~|～|〜)', ' ', desc).split()
                            for p in range(int(start), int(end) + 1):
                                if rel.get('relationship'):
                                    person['contacts'].append({
                                        'person_no': p,
                                        'relationship': rel['relationship']})
                                else:
                                    person['contacts'].append({
                                        'person_no': p})
                        elif re.match(r'^\d+$', desc):
                            if rel.get('relationship'):
                                person['contacts'].append({
                                    'person_no': int(desc),
                                    'relationship': rel['relationship']})
                            else:
                                person['contacts'].append({
                                    'person_no': int(desc)})
                        elif re.match(r'^(.+事例|.+陽性患者)$', desc):
                            person['case'] = desc
                        else:
                            raise Exception('Invalid route description "{}"'.format(texts[i]))

            elif len(texts[i]) > 0:
                if re.match(r'^(' + '|'.join(COUNTRIES) + r')$', texts[i]):
                    person['reason'] = 'abroad'
                    person['route']['country'] = texts[i]
                elif re.match(r'^.*(' + '|'.join(SPOTS) + r')$', texts[i]):
                    person['reason'] = 'contact'
                    person['spot'] = texts[i]
                elif re.match(r'^.*(都|道|府|県)$', texts[i]):
                    person['reason'] = 'other_area'
                    person['route']['area'] = texts[i]
                elif re.match(r'^再感染$', texts[i]):
                    person['reason'] = 'recurrence'
                else:
                    person['reason'] = 'other'

            i += 1
            if str.isdecimal(texts[i]):
                persons.append(person)
                continue

        # remarks, refer, remarks
        if re.match(r'^.+(県|市)発表(\d+|)$', texts[i]):
            words = re.sub(r'^(.+県|.+市)発表(\d+)$', r'\1 \2', texts[i]).split()
            words[0] = words[0].replace('本県', '愛知県')
            person['refer'] = {}
            for key, value in list(GOVERNMENTS.items()):
                if value == words[0]:
                    person['refer']['government'] = key
            if not person['refer'].get('government'):
                raise Exception('Unknown government "{}"'.format(texts[i]))

            if len(words) > 1:
                person['refer']['release_no'] = int(words[1])

        else:
            person['remarks'].append(texts[i])

        i += 1

        persons.append(person)

    result['persons'] = persons
    return result


def read_release_excel(filepath):
    results = []

    df = pd.read_excel(filepath)

    datecols = list(filter(lambda col: re.match(r'^令和\d+年\d+月\d+日現在$', str(col)), df.loc[0]))
    if len(datecols) == 0:
        raise Exception('Release date not found. %s', filepath)
    current_date = util.parse_japanese_date(re.sub(r'現在$', '', str(datecols[0]))).strftime(r'%Y-%m-%d')

    for index, row in df.iterrows():
        if index < 2:
            continue

        for i in [2, 3, 4, 5, 6]:
            row[i] = '' if row[i] == 0 else row[i]

        result = {
            'no': int(row[0]),
            'current_date': current_date,
            'release_date': util.excel_num_to_date(row[1]).strftime(r'%Y-%m-%d'),
            'nationality': row[3] if len(row[3]) > 0 else '',
            'area': row[4],
            'reason': 'unknown',
            'route': {
            },
            'remarks': []
        }
        if len(row[5]) > 0:
            result['route']['text'] = row[5]

        # age, sex
        if str(row[2]) != 'nan':
            words = \
                re.sub(r'(\d+代|\d+歳|\d+歳代|\d+歳未満)(男性|女性)$', r'\1 \2', row[2]).split()
            if len(words) > 0:
                if re.match(r'\d+(代|歳代)$', words[0]):
                    result['age'] = re.sub(r'(\d+)(代|歳代|歳)$', r'\1', words[0]) + 's'
                elif re.match(r'\d+歳$', words[0]):
                    result['age'] = re.sub(r'(\d+)歳$', r'\1', words[0]) + 's'
                elif re.match(r'\d+歳未満$', words[0]):
                    result['age'] = re.sub(r'(\d+)歳未満$', r'\1', words[0]) + 'u'
                else:
                    raise Exception('Age "{}" not defined'.format(words[0]))
            else:
                result['age'] = 'unknown'
            if len(words) > 1:
                if words[1] == '男性':
                    result['sex'] = 'male'
                elif words[1] == '女性':
                    result['sex'] = 'female'
                else:
                    raise Exception('Sex "{}" not defined'.format(words[1]))
            else:
                result['sex'] = 'unknown'
        else:
            result['age'] = 'unknown'
            result['sex'] = 'unknown'

        # route
        desc = None
        relationship = None
        rels = []
        if re.match(r'^.+(の|と)(夫|妻|娘|兄弟|姉妹|家族)$', row[5]):
            result['reason'] = 'contact'
            words = re.sub(r'(、|、|,)', ' ', row[5]).split()
            for word in words:
                descs = \
                    re.sub(r'(^.+)(の|と)(夫|妻|娘|兄弟|姉妹|家族)$', r'\1 \3', word).split()
                if len(descs) <= 2:
                    descs.append(re.sub(r'^.*(夫|妻|娘|兄弟|姉妹|家族)$', r'\1', row[5]))
                rels.append(
                    {'desc': descs[0],
                     'relationship': descs[1]})
        elif re.match(r'^.+と接触.*$', row[5]):
            result['reason'] = 'contact'
            words = re.sub(r'(、|,)', ' ', row[5]).split()
            for word in words:
                if re.match(r'^.+と接触.+$', word):
                    desc, relationship = \
                        re.sub(r'^(.+)と接触(.+)$', r'\1 \2', word).split()
                    relationship = re.sub(r'(（|）)', '', relationship)
                    rels.append(
                        {'desc': desc,
                         'relationship': relationship})
                elif re.match(r'^.+と接触$', word):
                    desc = re.sub(r'^(.+)と接触$', r'\1', word)
                    rels.append({'desc': desc})
                else:
                    rels.append(
                        {'desc': word})

        if result['reason'] == 'contact':
            result['contacts'] = []

            for rel in rels:
                descs = re.sub(r'(、|,|又は)', ' ', rel['desc']).split()

                for desc in descs:
                    desc = re.sub(r'(No.|等)', '', desc)
                    if re.match(r'^\d+(~|～|〜)\d+$', desc):
                        start, end = re.sub(r'(~|～|〜)', ' ', desc).split()
                        for p in range(int(start), int(end) + 1):
                            if rel.get('relationship'):
                                result['contacts'].append({
                                    'person_no': p,
                                    'relationship': rel['relationship']})
                            else:
                                result['contacts'].append({
                                    'person_no': p})
                    elif re.match(r'^\d+$', desc):
                        if rel.get('relationship'):
                            result['contacts'].append({
                                'person_no': int(desc),
                                'relationship': rel['relationship']})
                        else:
                            result['contacts'].append({
                                'person_no': int(desc)})
                    elif re.match(r'^(.+事例|.+陽性患者)$', desc):
                        result['case'] = desc
                    else:
                        raise Exception('Invalid description %s', row[5])

        elif len(row[5]) > 0:
            if re.match(r'^(' + '|'.join(COUNTRIES) + r')$', row[5]):
                result['reason'] = 'abroad'
                result['route']['country'] = row[5]
            elif re.match(r'^.*(' + '|'.join(SPOTS) + r')$', row[5]):
                result['reason'] = 'contact'
                result['spot'] = row[5]
            elif re.match(r'^.*(都|道|府|県)$', row[5]):
                result['reason'] = 'other_area'
                result['route']['area'] = row[5]
            elif re.match(r'^再感染$', row[5]):
                result['reason'] = 'recurrence'
            else:
                result['reason'] = 'other'

        # refer, remarks
        if re.match(r'^.+(県|市)発表(\d+|)$', row[6]):
            words = re.sub(r'^(.+県|.+市)発表(\d+)$', r'\1 \2', row[6]).split()
            words[0] = words[0].replace('本県', '愛知県')
            result['refer'] = {}
            for key, value in list(GOVERNMENTS.items()):
                if value == words[0]:
                    result['refer']['government'] = key
            if not result['refer'].get('government'):
                raise Exception('Unknown government %s', row[6])

            if len(words) > 1:
                result['refer']['release_no'] = int(words[1])

        else:
            result['remarks'].append(row[6])

        results.append(result)

    return {'current_date': current_date, 'persons': results}


# Main
if __name__ == '__main__':

    release = read_aichi_release()

    if release.get('excel'):

        filepath = os.path.join(
            config.DATA_DIR, 'aichi/releases',
            'aichi_release_{}.xlsx'.format(release['excel']['current_date'].strftime(r'%Y%m%d')))

        util.download_file(release['excel']['url'], filepath=filepath)
        if not os.path.exists(filepath):
            logger.info('Download excel file %s', filepath)
        else:
            logger.info('File %s already exists.', filepath)
        release['excel']['filepath'] = filepath

        result = read_release_excel(release['excel']['filepath'])

    elif release.get('pdf'):
        filepath = os.path.join(
            config.DATA_DIR, 'aichi/releases',
            'aichi_release_{}.pdf'.format(release['pdf']['current_date'].strftime(r'%Y%m%d')))
        util.download_file(release['pdf']['url'], filepath=filepath)
        if not os.path.exists(filepath):
            logger.info('Download PDF file %s', filepath)
        else:
            logger.info('File %s already exists.', filepath)
        release['pdf']['filepath'] = filepath

        result = read_release_pdf(release['pdf']['filepath'])

    else:
        raise Exception('No result.')

    last_no = Person.get_last_no()
    persons = list(filter(lambda p: p['no'] > last_no, result['persons']))

    logger.info('Add %s persons', len(persons))
    for person in persons:
        print(person)
        Person.insert(person)

    exit()
