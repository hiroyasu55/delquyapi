import os
import logging

DEBUG = False

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.join(BASE_DIR, 'app')
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_NAME = r'delquy'
LOG_FORMAT = r"%(asctime)s [%(levelname)s] %(name)s %(message)s"
LOG_TIME_FORMAT = r'%Y-%m-%d %H:%M:%S'
LOG_LEVEL = logging.INFO
USER_AGENT = \
    r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113"  # noqa: E501
WTF_CSRF_SECRET_KEY = "sefh30itgmp2fnp^ih26vb;fkga"

AGE = {
  '0s': '0歳',
  '10u': '10歳未満',
  '10s': '10代',
  '20s': '20代',
  '30s': '30代',
  '40s': '40代',
  '50s': '50代',
  '60s': '60代',
  '70s': '70代',
  '80s': '80代',
  '90s': '90代',
  '100o': '100歳以上',
  'unknown': '不明',
}

SEX = {
  'male': '男性',
  'female': '女性',
  'unknown': '不明',
}

REASON = {
  'contact': '対人接触',
  'abroad': '国外',
  'other_area': '県外',
  'recurrence': '再感染',
  'other': 'その他',
  'unknown': '不明',
}

GOVERNMENT = {
  'aichi': '愛知県',
  'nagoya': '名古屋市',
  'okazaki': '岡崎市',
  'toyota': '豊田市',
  'toyohashi': '豊橋市',
  'mhlw': '厚生労働省',
}

CONDITIONS = [
  '発熱', '微熱', '倦怠感', '味覚', '嗅覚', '咳', '肺炎', '脱力感', '感冒',
  '咽頭痛', 'のどの痛み', '呼吸苦', '背中の痛み', '関節痛', '胸痛', '食欲低下']


AICHI_SUMMARY_URL = \
    'https://www.pref.aichi.jp/site/covid19-aichi/kansensya-kensa.html'
AICHI_PRESS_RELEASE_URL = \
    'https://www.pref.aichi.jp/site/covid19-aichi/corona-kisya.html'
NAGOYA_PRESS_RELEASE_URL = \
    'http://www.city.nagoya.jp/kenkofukushi/page/0000126920.html'

DEBUG = False

if os.getenv('FLASK_ENV') == 'development':
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    FLASK_PORT = 5001
