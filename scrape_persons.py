import settings  # noqa: F401
import urllib.parse
from datetime import date  # noqa: F401
import calendar  # noqa: F401
import re
import os
from pprint import pprint  # noqa: F401
import logging
# import app.lib.log as log
import config
import app.lib.util as util
import app.models.Person as Person
import app.models.Soup as Soup
import app.models.PDFReader as PDFReader
import json  # noqa: F401

# logger = log.getLogger('get_persons')
logger = logging.getLogger('persons')
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

ROWS_START_INDEX = 9
COUNTRIES = [
    '中国', 'アメリカ', 'フランス', 'イタリア',
    'イギリス', 'カナダ', 'オーストラリア', 'ナイジェリア',
    'ノルウェー', 'タイ', 'フィリピン', 'パキスタン',
    '韓国', 'ベトナム', '欧州'
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


def read_aichi_release(last_date=None):
    results = []
    url = config.AICHI_SUMMARY_URL
    soup = Soup.create_soup(url)

    main_a = soup.body.select_one('#main_a')
    text_r = main_a.select_one('.text_r')
    if not re.match(r'^.*掲載日[^\d]*\d+年\d+月\d+日.*$', text_r.text):
        raise Exception('current_date not found in {}'.format(url))

    year, month, day = \
        re.sub(r'^.*掲載日[^\d]*(\d+)年(\d+)月(\d+)日.*$', r'\1 \2 \3', text_r.text).split()
    current_date = date(year=int(year), month=int(month), day=int(day)).strftime(r'%Y-%m-%d')
    main_a = soup.body.select_one('#main_body')
    detail_free = main_a.select_one('.detail_free')
    ps = list(filter(lambda p: re.match(r'^.*愛知県内の発生事例', p.text), detail_free.select('p')))
    if len(ps) == 0:
        raise Exception('header "愛知県内の発生事例" not found in {}'.format(url))

    for a in list(filter(lambda a: re.match(r'^\d+月.*PDFファイル', a.text), ps[0].select('a'))):
        month = int(re.sub(r'^(\d+)月.*$', r'\1', a.text))
        d = date(year=2020, month=month, day=calendar.monthrange(2020, month)[1]).strftime(r'%Y-%m-%d')
        if last_date and last_date < d:
            result = {
                'current_date': current_date,
                'last_date': d,
                'pdf': {
                    'url': urllib.parse.urljoin(url, a['href'])
                }
            }
            results.append(result)

    results = sorted(results, key=lambda r: r['last_date'])
    return results


# Read PDF
def read_release_pdf(filepath, debug=False):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    result = {}
    lines = PDFReader.read_textboxes(filepath)

    # 令和2年5月5日現在
    if not re.match(r'^令和\d+年\d+月\d+日現在$', lines[1]):
        raise Exception('Current date not found. {}'.format(filepath))
    result['current_date'] = \
        util.parse_japanese_date(re.sub(r'現在$', '', lines[1])).strftime(r'%Y-%m-%d')
    lines = lines[2:]

    # for i, text in enumerate(texts):
    #     if text == '備考':
    #         break
    # if i >= len(texts):
    #     raise Exception('"備考" not found. {}'.format(filepath))
    # texts = texts[i+1:]

    HEADERS = ['No', '発表日', '年代・性別', '国籍', '住居地', '接触状況', '備考']
    texts = []
    i = 0
    while i < len(lines):
        print(i, lines[i])
        if len(lines[i].split()) >= 2:
            lines[i:i+1] = lines[i].split()
            continue
        if len(lines[i]) == 0:
            i += 1
            continue
        if lines[i:i+7] == HEADERS:
            i += 7
            continue

        line = lines[i]
        if line == '調査中調査中性':
            texts.extend(['調査中', '調査中'])
        elif re.match(r'^.+未満代.*$', line):
            texts.append(re.sub(r'未満代', '未満', line))
        elif re.match(r'^.+性性$', line):
            texts.append(re.sub(r'性性', '性', line))
        else:
            texts.append(line)
        i += 1

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
        logger.debug('{} no:{}'.format(i, texts[i]))
        if not str.isdecimal(texts[i]):
            print(texts[i-2:i+3])
            raise Exception('Invalid No. {}'.format(texts[i]))
        person['no'] = int(texts[i])
        i += 1

        # release date
        if len(texts[i].split()) > 0:
            texts[i:i+1] = texts[i].split()

        if not re.match(r'^\d+月\d+日$', texts[i]):
            raise Exception('Inbalid date. {}'.format(texts[i]))
        logger.debug('{} release_date:{}'.format(i, texts[i]))
        # month, day = re.sub(r'^(\d+)月(\d+)日$', r'\1 \2', words[0]).split()
        # person['release_date'] = date(2020, int(month), int(day)).strftime(r'%Y-%m-%d')
        person['release_date'] = util.parse_japanese_date('令和2年' + texts[i]).strftime(r'%Y-%m-%d')
        i += 1

        # age/sex
        # if texts[i] == '調査中調査中性':
        #     texts[i] = '調査中調査中'
        # elif re.match(r'^.+未満代.*$', texts[i]):
        #     texts[i] = re.sub(r'未満代', '未満', texts[i])
        # elif re.match(r'^.+性性$', texts[i]):
        #     texts[i] = re.sub(r'性性', '性', texts[i])

        if not re.match(r'^.+(男性|女性|調査中)$', texts[i]):
            raise Exception('Invalid age/sex "{}"'.format(texts[i]))
        logger.debug('{} age/sex:{}'.format(i, texts[i]))

        age, sex = \
            re.sub(r'^(.+)(男性|女性|調査中)$', r'\1 \2', texts[i]).split()
        if re.match(r'^\d+(代|歳代|歳)$', age):
            person['age'] = re.sub(r'(\d+)(代|歳代|歳)$', r'\1', age) + 's'
        elif re.match(r'^\d+歳未満$', age):
            person['age'] = re.sub(r'(\d+)歳未満$', r'\1', age) + 'u'
        elif re.match(r'^高齢者(代|)$', age):
            person['age'] = 'elderly'
        elif re.match(r'^調査中$', age):
            person['age'] = 'unknown'
        else:
            raise Exception('Invalid age "{}"'.format(texts[i]))

        if sex == '男性':
            person['sex'] = 'male'
        elif sex == '女性':
            person['sex'] = 'female'
        elif sex == '調査中':
            person['sex'] = 'unknown'
        else:
            raise Exception('Invalid sex "{}"'.format(texts[i]))

        i += 1
        if len(texts[i].split()) >= 2 and len(texts[i].split(', ')) < 2:
            texts[i:i+1] = texts[i].split()

        # nationality
        if texts[i] in COUNTRIES or texts[i] in ['日本', '外国籍', '調査中']:
            logger.debug('{} nationality:{}'.format(i, texts[i]))
            person['nationality'] = texts[i]
            i += 1

        # area
        person['area'] = texts[i]
        logger.debug('{} area:{}'.format(i, texts[i]))
        i += 1

        if len(texts[i].split()) >= 2 and len(texts[i].split(', ')) < 2:
            texts[i:i+1] = texts[i].split()

        # discharged date/death date
        if re.match(r'^\d+月\d+日$', texts[i]):
            logger.debug('{} discharged_date:{}'.format(i, texts[i]))
            person['discharged_date'] = util.parse_japanese_date('令和2年' + texts[i]).strftime(r'%Y-%m-%d')
            person['status'] = 'discharged'
            i += 1
        elif re.match(r'^済$', texts[i]):
            logger.debug('{} status(discharged):{}'.format(i, texts[i]))
            person['status'] = 'discharged'
            i += 1
        elif re.match(r'^\d+\/\d+死亡$', texts[i]):
            logger.debug('{} discharged_date:{}'.format(i, texts[i]))
            month, day = re.sub(r'^(\d+)\/(\d+)死亡$', r'\1 \2', texts[i]).split()
            person['death_date'] = date(2020, int(month), int(day)).strftime(r'%Y-%m-%d')
            person['status'] = 'dead'
            i += 1

        if str.isdecimal(texts[i]):
            persons.append(person)
            continue

        # route,reason
        if re.match(r'^.+接触 .+(県|市)発表(\d+|)$', texts[i]):
            texts[i:i+1] = re.sub(r'^(.+接触) (.+発表\d+)$', r'\1|\2', texts[i]).split('|')
        elif re.match(r'^.+接触.+(県|市)発表(\d+|)$', texts[i]):
            texts[i:i+1] = re.sub(r'^(.+接触)(.+発表\d+)$', r'\1 \2', texts[i]).split()

        if not re.match(r'^.+(県|市)発表(\d+|)$', texts[i]):
            person['route']['text'] = texts[i]
            logger.debug('{} route.text:{}'.format(i, texts[i]))

            texts[i] = re.sub(r'No,(\d+)', r'No.\1', texts[i])
            words = re.sub(r'(、|、|,|又は|及び)', ' ', texts[i]).split()
            # texts[i] = re.sub(r'No,(\d+)', r'No.\1', texts[i])
            nos = []
            for word in words:
                if re.match(r'^(No\.|)(\d+).*$', word) and re.match(r'^.*(\d+)(等|例目|)(と接触|接触|)$', word):
                    desc = re.sub(r'^No\.', '', word)
                    desc = re.sub(r'(と接触|接触)$', '', desc)
                    desc = re.sub(r'(等|例目)$', '', desc)
                    person['reason'] = 'contact'

                    if re.match(r'^\d+$', desc):
                        nos.append(int(desc))
                    elif re.match(r'^\d+(~|～|〜)\d+$', desc):
                        start, end = re.sub(r'(~|～|〜)', ' ', desc).split()
                        for p in range(int(start), int(end) + 1):
                            nos.append(p)
                    else:
                        raise Exception('Invalid route(contact) "{}" no:{}'.format(texts[i], person.get('no')))

                elif re.match(r'^空港検疫.+(と接触|)$', word):
                    person['reason'] = 'other_area'
                    person['route']['area'] = \
                        (',' if person['route'].get('area') else '') + '空港検疫'

                elif re.match(r'^.+(都|道|府|県)(No\.|)\d+(と接触|)$', word):
                    person['reason'] = 'other_area'
                    person['route']['area'] = \
                        re.sub(r'^(.+)(都|道|府|県)(No\.|)\d+(と接触|)$', r'\1\2', word)

                elif re.match(r'^(.+事例|.+発生例|.+陽性患者).*(と接触|)$', word):
                    if re.match(r'^(名古屋市|市内|愛知県|県内).*$', word):
                        person['reason'] = 'contact'
                    elif re.match(r'^.+(都|道|府|県|市).*$', word):
                        person['reason'] = 'other_area'
                        person['route']['area'] = \
                            (',' if person['route'].get('area') else '') + \
                            re.sub(r'^(.+)(都|道|府|県|市).*$', r'\1\2', word)
                    elif re.match(r'^岐阜.*$', word):
                        person['reason'] = 'other_area'
                        person['route']['area'] = \
                            (',' if person['route'].get('area') else '') + '岐阜県'
                    elif re.match(r'^市外事例.*$', word):
                        person['reason'] = 'contact'
                    else:
                        raise Exception('Invalid route(case) "{}" no:{}'.format(texts[i], person.get('no')))
                    person['case'] = word

                elif re.match(r'^.+と接触$', word):
                    person['reason'] = 'contact'

                elif re.match(r'^(' + '|'.join(COUNTRIES) + r')$', word):
                    person['reason'] = 'abroad'
                    person['route']['country'] = word

                elif re.match(r'^.*(' + '|'.join(SPOTS) + r')$', word):
                    if re.match(r'^(名古屋市|市内|愛知県|県内).*$', word):
                        person['reason'] = 'contact'
                    elif re.match(r'^.+(都|道|府|県|市).*$', word):
                        person['reason'] = 'other_area'
                        person['route']['area'] = \
                            (',' if person['route'].get('area') else '') + \
                            re.sub(r'^(.+)(都|道|府|県|市).*$', r'\1\2', word)
                    else:
                        raise Exception('Invalid route(spot) "{}" no:{}'.format(texts[i], person.get('no')))
                    person['spot'] = word

                elif re.match(r'^(.+都|.+道|.+府|.+県|関東)(に|)(滞在|)$', word):
                    if person['reason'] == 'unknown':
                        person['reason'] = 'other_area'
                    person['route']['area'] = \
                        (',' if person['route'].get('area') else '') + re.sub(r'(に|)滞在$', '', word)

                elif re.match(r'^再感染.*$', word):
                    person['reason'] = 'recurrence'
                    if re.match(r'^再感染（(No\.|)\d+）$', word):
                        person['former_no'] = int(re.sub(r'^再感染（(No\.|)(\d+)）$', r'\2', word))

                else:
                    print(texts[i-5:i+5])
                    raise Exception('Invalid route "{}" no:{}'.format(texts[i], person.get('no')))

            if len(nos) > 0:
                person['contacts'] = [{'person_no': no} for no in nos]

            i += 1
            if str.isdecimal(texts[i]):
                persons.append(person)
                continue

        # refer, remarks
        if re.match(r'^.+(県|市)発表(\d+|)$', texts[i]):
            logger.debug('{} refer:{}'.format(i, texts[i]))
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
            logger.debug('{} remarks:{}'.format(i, texts[i]))
            person['remarks'].append(texts[i])

        i += 1
        persons.append(person)

    result['persons'] = persons

    # if len(persons) >= 552:
    #     p552 = persons[551]
    #     p552.update({
    #         'age': '20s',
    #         'area': '名古屋市',
    #         'cluster_no': 9,
    #         'contacts': [{'person_no': 537}],
    #         'nationality': '',
    #         'no': 552,
    #         'reason': 'contact',
    #         'refer': {'government': 'nagoya', 'release_no': 303},
    #         'release_date': '2020-07-15',
    #         'remarks': [],
    #         'route': {'text': 'No.537と接触'},
    #         'sex': 'female',
    #     })
    # if len(persons) >= 553:
    #     p553 = persons[552]
    #     p553.update({
    #         'age': '30s',
    #         'area': '名古屋市',
    #         'nationality': '',
    #         'no': 553,
    #         'reason': 'other_area',
    #         'refer': {'government': 'nagoya', 'release_no': 304},
    #         'release_date': '2020-07-15',
    #         'remarks': [],
    #         'route': {'area': '東京都', 'text': '東京都'},
    #         'sex': 'female',
    #     })
    # if len(persons) >= 554:
    #     p554 = persons[553]
    #     p554.update({
    #         'age': '40s',
    #         'area': '名古屋市',
    #         'nationality': '',
    #         'no': 554,
    #         'reason': 'other_area',
    #         'refer': {'government': 'nagoya', 'release_no': 305},
    #         'release_date': '2020-07-15',
    #         'remarks': [],
    #         'route': {'area': '東京都', 'text': '東京都'},
    #         'sex': 'female',
    #     })

    return result


# Main
if __name__ == '__main__':

    last_date = None
    last_no = 0
    current_persons = Person.find(order=['-no'], limit=1)
    if len(current_persons) > 0:
        last_date = current_persons[-1]['release_date']
        last_no = current_persons[-1]['no']

    releases = read_aichi_release(last_date=last_date)
    for release in releases:
        # filepath = os.path.join(
        #     config.DATA_DIR, 'aichi/releases',
        #     'aichi_release_{}.pdf'.format(release['pdf']['current_date'].strftime(r'%Y%m%d')))
        filepath = os.path.join(
            config.DATA_DIR, 'aichi/releases',
            'aichi_release_{}.pdf'.format(re.sub(r'^.*\/(\d+)\.pdf$', r'\1', release['pdf']['url'])))
        if not os.path.exists(filepath):
            logger.info('Download PDF file %s', filepath)
            util.download_file(release['pdf']['url'], filepath=filepath)
        else:
            logger.info('File %s already exists.', filepath)
        release['pdf']['filepath'] = filepath

        result = read_release_pdf(release['pdf']['filepath'], debug=True)
        persons = list(filter(lambda p: p['no'] > last_no, result['persons']))

        logger.info('Add %s persons', len(persons))
        for person in persons:
            print(person)
            Person.insert(person)

    exit()
