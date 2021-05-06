import settings  # noqa: F401
import urllib.parse
from urllib.error import HTTPError
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
import app.models.Person as Person

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

CUSTOM_DETAILS = [
    {
        'filename': '341215.pdf',
        'release_date': '2020-07-18',
        'results': [
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 231,
                'total_no': 599,
                'age': '20s',
                'sex': 'male',
                'nationality': '日本',
                'area': '瀬戸市',
                'abroad_history': '14日以内なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-17',
                'condition': 'なし',
                'remarks': [
                    '県内545例目（20歳代女性・7月15日本件発表）の知人（濃厚接触者）'
                ],
                'contacts': [
                    {'person_no': 545, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 231,
                'total_no': 600,
                'age': '20s',
                'sex': 'female',
                'nationality': '日本',
                'area': 'あま市',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-11',
                'confirmed_date': '2020-07-17',
                'condition': '【軽症】発熱、咳、鼻汁、咽頭痛、頭痛、関節痛、味覚・嗅覚障害',
                'remarks': [
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 232,
                'total_no': 601,
                'age': '20s',
                'sex': 'femali',
                'nationality': '日本',
                'area': '半田市',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-13',
                'confirmed_date': '2020-07-17',
                'condition': '【軽症】発熱、頭痛',
                'remarks': [
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 233,
                'total_no': 602,
                'age': '40s',
                'sex': 'male',
                'nationality': '日本',
                'area': '知多郡武豊町',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-03',
                'confirmed_date': '2020-07-17',
                'condition': '【中等症】発熱、肺炎、倦怠感',
                'remarks': [
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 234,
                'total_no': 603,
                'age': '20s',
                'sex': 'male',
                'nationality': '日本',
                'area': '春日井市',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-11',
                'confirmed_date': '2020-07-17',
                'condition': '【軽症】発熱',
                'remarks': [
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 235,
                'total_no': 604,
                'age': '40s',
                'sex': 'male',
                'nationality': '日本',
                'area': '小牧市',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-14',
                'confirmed_date': '2020-07-18',
                'condition': '【軽症】発熱、咳、関節筋肉痛',
                'remarks': [
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 236,
                'total_no': 605,
                'age': '10s',
                'sex': 'female',
                'nationality': '日本',
                'area': '海部郡大治町',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-12',
                'confirmed_date': '2020-07-18',
                'condition': '【軽症】発熱、咳、咽頭痛、頭痛、味覚・嗅覚障害',
                'remarks': [
                    '県内537例目（20歳代・7月14日本県発表）の知人（濃厚接触者）'
                ],
                'contacts': [
                    {'person_no': 537, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-18',
                'government': 'aichi',
                'no': 237,
                'total_no': 606,
                'age': '30s',
                'sex': 'male',
                'nationality': '日本',
                'area': '刈谷市',
                'abroad_history': '14日以内なし',
                'onset_date': '2020-07-14',
                'confirmed_date': '2020-07-18',
                'condition': '【軽症】発熱、咳',
                'remarks': [
                ]
            },
        ]
    },
    {
        'filename': '341590.pdf',
        'release_date': '2020-07-25',
        'results': [
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1020,
                'age': '40s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1021,
                'age': '70s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': ['県内882例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 882, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1022,
                'age': '30s',
                'sex': 'male',
                'area': '瀬戸市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-19',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1023,
                'age': '20s',
                'sex': 'male',
                'area': '日進市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-18',
                'confirmed_date': '2020-07-25',
                'condition': '中等症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1024,
                'age': '30s',
                'sex': 'male',
                'area': '北名古屋市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-17',
                'confirmed_date': '2020-07-25',
                'condition': '中等症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'no': 1025,
                'age': '20s',
                'sex': 'female',
                'area': '清須市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-16',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': ['県内824例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 824, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1026,
                'age': '20s',
                'sex': 'male',
                'area': '清須市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-19',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'no': 1027,
                'age': '50s',
                'sex': 'female',
                'area': '清須市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': ['県内1026例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1026, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1028,
                'age': '30s',
                'sex': 'male',
                'area': '北名古屋市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-23',
                'confirmed_date': '2020-07-25',
                'condition': '中等症',
                'remarks': ['県内1024例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1024, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1029,
                'age': '70s',
                'sex': 'male',
                'area': '北名古屋市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-25',
                'condition': '中等症',
                'remarks': ['県内1024例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1024, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1030,
                'age': '10s',
                'sex': 'female',
                'area': '北名古屋市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': ['県内956例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 956, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1031,
                'age': '20s',
                'sex': 'male',
                'area': '津島市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-20',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1032,
                'age': '20s',
                'sex': 'male',
                'area': 'あま市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1033,
                'age': '40s',
                'sex': 'male',
                'area': 'あま市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1034,
                'age': '20s',
                'sex': 'male',
                'area': '大治町',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1035,
                'age': '10s',
                'sex': 'male',
                'area': '東浦町',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-25',
                'condition': 'なし',
                'remarks': ['県内871例目の濃厚接触者'],
                'contacts': [
                    {'person_no': 871}
                ]
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1036,
                'age': '70s',
                'sex': 'female',
                'area': '東海市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'no': 1037,
                'age': '10s',
                'sex': 'female',
                'area': '知多市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-19',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1038,
                'age': '50s',
                'sex': 'male',
                'area': '知多市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-16',
                'confirmed_date': '2020-07-25',
                'condition': '中等症',
                'remarks': ['7月11日〜12日兵庫県に滞在']
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1039,
                'age': '30s',
                'sex': 'male',
                'area': '東海市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-23',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1040,
                'age': '20s',
                'sex': 'male',
                'area': '高浜市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1041,
                'age': '20s',
                'sex': 'male',
                'area': 'みよし市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-25',
                'condition': 'なし',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1042,
                'age': '40s',
                'sex': 'male',
                'area': 'みよし市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-25',
                'condition': 'なし',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1043,
                'age': '20s',
                'sex': 'female',
                'area': '西尾市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1044,
                'age': '20s',
                'sex': 'female',
                'area': '西尾市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-25',
                'condition': 'なし',
                'remarks': []
            },
            {
                'release_date': '2020-07-25',
                'government': 'aichi',
                'total_no': 1045,
                'age': '10s',
                'sex': 'male',
                'area': '蒲郡市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-25',
                'condition': '軽症',
                'remarks': ['県内810例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 810, 'relationship': '知人'}
                ]
            },
        ]
    },
    {
        'filename': '342171.pdf',
        'release_date': '2020-07-30',
        'results': [
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1453,
                'age': '30s',
                'sex': 'female',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内762例目の濃厚接触者'],
                'contacts': [
                    {'person_no': 762}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1454,
                'age': '40s',
                'sex': 'female',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-27',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1179例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1179, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1455,
                'age': '20s',
                'sex': 'male',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-27',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1179例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1179, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1456,
                'age': '10u',
                'sex': 'male',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-25',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1179例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1179, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1457,
                'age': '20s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-29',
                'condition': 'なし',
                'remarks': ['県内1129例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1129, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1458,
                'age': '30s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-29',
                'condition': 'なし',
                'remarks': ['県内1129例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1129, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1459,
                'age': '50s',
                'sex': 'male',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-19',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1460,
                'age': '20s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-19',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1182例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1182, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1461,
                'age': '50s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-26',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1462,
                'age': '20s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-29',
                'condition': 'なし',
                'remarks': ['県内1183例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1183, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1463,
                'age': '10s',
                'sex': 'female',
                'area': '長久手市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-22',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1129例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1129, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1464,
                'age': '20s',
                'sex': 'female',
                'area': '豊明市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-26',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内980例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 980, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1465,
                'age': '10s',
                'sex': 'female',
                'area': '東郷町',
                'abroad_history': 'なし',
                'onset_date': '2020-07-28',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1296例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1296, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1466,
                'age': '50s',
                'sex': 'male',
                'area': '瀬戸市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1467,
                'age': '60s',
                'sex': 'male',
                'area': '春日井市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-28',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1468,
                'age': '20s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-29',
                'condition': 'なし',
                'remarks': ['県内1099例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1099, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1469,
                'age': '60s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-28',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1190例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1190, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1470,
                'age': '40s',
                'sex': 'male',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-26',
                'confirmed_date': '2020-07-28',
                'condition': '中等症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1471,
                'age': '20s',
                'sex': 'female',
                'area': '清須市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内904例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 904, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1472,
                'age': '20s',
                'sex': 'male',
                'area': '北名古屋市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-29',
                'confirmed_date': '2020-07-29',
                'condition': '中等症',
                'remarks': ['県内708例目の同僚'],
                'contacts': [
                    {'person_no': 708, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1473,
                'age': '20s',
                'sex': 'male',
                'area': '弥富市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内708例目の同僚'],
                'contacts': [
                    {'person_no': 708, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1474,
                'age': '50s',
                'sex': 'male',
                'area': '愛西市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-29',
                'condition': 'なし',
                'remarks': ['県内1280例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1280, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1475,
                'age': '50s',
                'sex': 'male',
                'area': '南知多町',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1476,
                'age': '70s',
                'sex': 'female',
                'area': '南知多町',
                'abroad_history': 'なし',
                'onset_date': '2020-07-27',
                'confirmed_date': '2020-07-29',
                'condition': '中等症',
                'remarks': ['県内1475例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1475, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1477,
                'age': '50s',
                'sex': 'male',
                'area': '東海市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-24',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1478,
                'age': '20s',
                'sex': 'female',
                'area': '大府市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-27',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1322例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1322, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1479,
                'age': '20s',
                'sex': 'male',
                'area': '大府市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-27',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1480,
                'age': '20s',
                'sex': 'female',
                'area': '知立市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-16',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1481,
                'age': '30s',
                'sex': 'male',
                'area': '刈谷市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-28',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1482,
                'age': '40s',
                'sex': 'male',
                'area': '安城市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-25',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1483,
                'age': '50s',
                'sex': 'male',
                'area': '安城市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-25',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1338例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1338, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1484,
                'age': '40s',
                'sex': 'female',
                'area': '安城市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-28',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1338例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1338, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1485,
                'age': '20s',
                'sex': 'male',
                'area': '知立市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-19',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1486,
                'age': '20s',
                'sex': 'female',
                'area': '西尾市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-23',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1487,
                'age': '20s',
                'sex': 'male',
                'area': '西尾市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-21',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': ['県内1063例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1063, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1488,
                'age': '20s',
                'sex': 'female',
                'area': '西尾市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-25',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1489,
                'age': '40s',
                'sex': 'female',
                'area': '新城市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-07-29',
                'condition': 'なし',
                'remarks': ['県内1343例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 1343, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-07-30',
                'government': 'aichi',
                'total_no': 1490,
                'age': '20s',
                'sex': 'male',
                'area': '蒲郡市',
                'abroad_history': 'なし',
                'onset_date': '2020-07-28',
                'confirmed_date': '2020-07-29',
                'condition': '軽症',
                'remarks': []
            },
        ]
    },
    {
        'filename': '346128.pdf',
        'release_date': '2020-09-13',
        'results': [
            {
                'release_date': '2020-09-13',
                'government': 'aichi',
                'total_no': 4877,
                'age': '50s',
                'sex': 'male',
                'area': '長久手市',
                'abroad_history': 'なし',
                'onset_date': '2020-09-09',
                'confirmed_date': '2020-09-12',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-09-13',
                'government': 'aichi',
                'total_no': 4878,
                'age': '50s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-09-06',
                'confirmed_date': '2020-09-11',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-09-13',
                'government': 'aichi',
                'total_no': 4879,
                'age': '10s',
                'sex': 'male',
                'area': '大治町',
                'abroad_history': 'なし',
                'onset_date': '2020-09-10',
                'confirmed_date': '2020-09-12',
                'condition': '軽症',
                'remarks': ['県内4755例目の接触者'],
                'contacts': [
                    {'person_no': 4755}
                ]
            },
            {
                'release_date': '2020-09-13',
                'government': 'aichi',
                'total_no': 4880,
                'age': '10s',
                'sex': 'male',
                'area': '東浦町',
                'abroad_history': 'なし',
                'onset_date': '2020-09-11',
                'confirmed_date': '2020-09-12',
                'condition': '軽症',
                'remarks': ['県内4738例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 4738, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-09-13',
                'government': 'aichi',
                'total_no': 4881,
                'age': '50s',
                'sex': 'female',
                'area': '蒲郡市',
                'abroad_history': 'なし',
                'onset_date': '2020-09-07',
                'confirmed_date': '2020-09-12',
                'condition': '軽症',
                'remarks': ['県内4907例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 4907, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-09-13',
                'government': 'aichi',
                'total_no': 4882,
                'age': '50s',
                'sex': 'male',
                'area': '蒲郡市',
                'abroad_history': 'なし',
                'onset_date': '2020-09-10',
                'confirmed_date': '2020-09-12',
                'condition': '軽症',
                'remarks': ['県内4907例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 4907, 'relationship': '家族'}
                ]
            },
         ]
    },
    {
        'filename': '350721.pdf',
        'release_date': '2020-10-24',
        'results': [
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5824,
                'age': '50s',
                'sex': 'male',
                'area': '長久手市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-17',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5825,
                'age': '30s',
                'sex': 'female',
                'area': '日進市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-20',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5826,
                'age': '40s',
                'sex': 'male',
                'area': '東郷町',
                'abroad_history': 'なし',
                'onset_date': '2020-10-18',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5827,
                'age': '10s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-21',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5791例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5791, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5828,
                'age': '10s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-20',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5791例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5791, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5829,
                'age': '10s',
                'sex': 'male',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-20',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5791例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5791, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5830,
                'age': '40s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-19',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5791例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5791, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5831,
                'age': '30s',
                'sex': 'male',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-10-23',
                'condition': 'なし',
                'remarks': ['県内5786例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5786, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5832,
                'age': '40s',
                'sex': 'male',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-20',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5730例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5730, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5833,
                'age': '40s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-19',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5730例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5730, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5834,
                'age': '60s',
                'sex': 'male',
                'area': '犬山市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-22',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5793例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5793, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5835,
                'age': '70s',
                'sex': 'male',
                'area': '江南市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-23',
                'confirmed_date': '2020-10-23',
                'condition': '中等症',
                'remarks': ['県内5595例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5595, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5836,
                'age': '60s',
                'sex': 'male',
                'area': '弥富市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-10-23',
                'condition': 'なし',
                'remarks': ['県内5797例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5797, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5837,
                'age': '30s',
                'sex': 'male',
                'area': '常滑市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-19',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': ['県内5769例目の同僚（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5769, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5838,
                'age': '40s',
                'sex': 'male',
                'area': '知多市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-20',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5839,
                'age': '30s',
                'sex': 'male',
                'area': 'みよし市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-20',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5840,
                'age': '50s',
                'sex': 'female',
                'area': '高浜市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-14',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5841,
                'age': '30s',
                'sex': 'male',
                'area': 'みよし市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-19',
                'confirmed_date': '2020-10-23',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-10-24',
                'government': 'aichi',
                'total_no': 5842,
                'age': '70s',
                'sex': 'female',
                'area': '豊川市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-10-23',
                'condition': 'なし',
                'remarks': ['県内5801例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 5801, 'relationship': '家族'}
                ]
            },
         ]
    },
    {
        'filename': '351614.pdf',
        'release_date': '2020-11-04',
        'results': [
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6417,
                'age': '50s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-29',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6418,
                'age': '50s',
                'sex': 'male',
                'area': '一宮市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-28',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6419,
                'age': '60s',
                'sex': 'female',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': '2020-11-03',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6335例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6335, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6420,
                'age': '20s',
                'sex': 'male',
                'area': '稲沢市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6335例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6335, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6421,
                'age': '30s',
                'sex': 'female',
                'area': '東郷町',
                'abroad_history': 'なし',
                'onset_date': '2020-11-01',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6340例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6340, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6422,
                'age': '10s',
                'sex': 'male',
                'area': '春日井市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6342例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6342, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6423,
                'age': '10s',
                'sex': 'female',
                'area': '春日井市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-30',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6342例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6342, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6424,
                'age': '10s',
                'sex': 'female',
                'area': '春日井市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6344例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6344, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6425,
                'age': '30s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-11-02',
                'confirmed_date': '2020-11-02',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6426,
                'age': '40s',
                'sex': 'female',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-29',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6169例目の同僚（接触者）'],
                'contacts': [
                    {'person_no': 6169, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6427,
                'age': '80s',
                'sex': 'male',
                'area': '小牧市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6292例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6292, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6428,
                'age': '10s',
                'sex': 'male',
                'area': '岩倉市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6169例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6169, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6429,
                'age': '20s',
                'sex': 'female',
                'area': '北名古屋市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-29',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6430,
                'age': '70s',
                'sex': 'male',
                'area': '津島市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6354例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6354, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6431,
                'age': '70s',
                'sex': 'female',
                'area': '津島市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-24',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6354例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6354, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6432,
                'age': '60s',
                'sex': 'female',
                'area': '津島市',
                'abroad_history': 'なし',
                'onset_date': 'unknown',
                'confirmed_date': '2020-11-03',
                'condition': 'なし',
                'remarks': ['県内6355例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6355, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6433,
                'age': '70s',
                'sex': 'female',
                'area': '津島市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-27',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6354例目の知人（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6354, 'relationship': '知人'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6434,
                'age': '20s',
                'sex': 'male',
                'area': '美浜町',
                'abroad_history': 'なし',
                'onset_date': '2020-11-03',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6435,
                'age': '20s',
                'sex': 'male',
                'area': '武豊町',
                'abroad_history': 'なし',
                'onset_date': '2020-10-31',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6399例目の同僚（接触者）'],
                'contacts': [
                    {'person_no': 6399, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6436,
                'age': '10u',
                'sex': 'male',
                'area': '刈谷市',
                'abroad_history': 'なし',
                'onset_date': '2020-10-31',
                'confirmed_date': '2020-11-02',
                'condition': '軽症',
                'remarks': []
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6437,
                'age': '90s',
                'sex': 'female',
                'area': '新城市',
                'abroad_history': 'なし',
                'onset_date': '2020-11-03',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6360例目の家族（濃厚接触者）'],
                'contacts': [
                    {'person_no': 6360, 'relationship': '家族'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6438,
                'age': '30s',
                'sex': 'male',
                'area': '豊川市',
                'abroad_history': 'なし',
                'onset_date': '2020-11-01',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': ['県内6263例目の同僚（接触者）'],
                'contacts': [
                    {'person_no': 6263, 'relationship': '同僚'}
                ]
            },
            {
                'release_date': '2020-11-04',
                'government': 'aichi',
                'total_no': 6439,
                'age': '10u',
                'sex': 'male',
                'area': '豊川市',
                'abroad_history': 'なし',
                'onset_date': '2020-11-01',
                'confirmed_date': '2020-11-03',
                'condition': '軽症',
                'remarks': []
            }
        ]
    }
]


def _revise_detail(detail):
    if not detail.get('age'):
        raise Exception('age not defined. {}'.format(detail))
    elif re.match(r'\d+(代|歳代)$', detail['age']):
        detail['age'] = re.sub(r'(\d+)(代|歳代|歳)$', r'\1', detail['age']) + 's'
    elif re.match(r'\d+歳(児|)$', detail['age']):
        detail['age'] = re.sub(r'(\d+)歳.*$', r'\1', detail['age']) + 's'
    elif re.match(r'\d+歳未満(（小学生）|)$', detail['age']):
        detail['age'] = re.sub(r'(\d+)歳未満.*$', r'\1', detail['age']) + 'u'
    elif detail['age'] == 'unknown':
        pass
    else:
        raise Exception('Age "{}" is invalid.'.format(detail['age']))

    if detail['sex'] == '男性':
        detail['sex'] = 'male'
    elif detail['sex'] == '女性':
        detail['sex'] = 'female'
    elif detail['sex'] == 'unknown':
        pass
    else:
        raise Exception('Sex "{}" is invalid.'.format(detail['sex']))

    if len(detail['progress']) > 0:
        # onset date
        if not detail.get('onset_date'):
            restr = r'^.*(' + '|'.join(config.CONDITIONS) + ').*$'
            p0 = detail['progress'][0]
            if re.match(restr, p0['content']):
                detail['onset_date'] = p0['date']
            else:
                ps = list(filter(lambda p: re.match(restr, p['content']), detail['progress']))
                if len(ps) > 0:
                    detail['onset_date'] = ps[0]['date']

        # hospitalization date
        if not detail.get('hospitalization_date'):
            ps = list(filter(lambda p: re.match('^.*入院.*$', p['content']) and not re.match('^.*入院予定.*$', p['content']), detail['progress']))  # noqa E501
            if len(ps) > 0:
                detail['hospitalization_date'] = ps[0]['date']

        # confirmed date
        if not detail.get('confirmed_date'):
            ps = list(filter(lambda p: re.match('^.*陽性.*$', p['content']), detail['progress']))
            if len(ps) > 0:
                detail['confirmed_date'] = ps[0]['date']

    for remark in (detail['remarks'] or []):
        if re.match(r'^県内\d+例目.*の.+（濃厚接触者）$', remark):
            person_no, relationship = \
                re.sub(r'^県内(\d+)例目.*の(.+)（濃厚接触者）$', r'\1 \2', remark).split()
            detail['contacts'] = detail.get('contacts', [])
            detail['contacts'].append({'person_no': int(person_no), 'relationship': relationship})

    return True


def _scrape_aichi_detail_2(start_tag):
    result = {
        'progress': [],
    }

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

    result['remarks'] = result.get('remarks', '').split('\n')
    result['remarks'] = list(map(lambda r: r.strip(), result['remarks']))
    _revise_detail(result)

    return result


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


# Read PDF(<=2020-07-23)
def read_release_pdf_1(filepath, release_date):

    data = []
    texts = PDFReader.read_textboxes(filepath)

    if len(texts) == 0:
        return None

    # if re.match(r'^(|.*\/)R20214kisya\.pdf$', filepath):
    #     release_date = '2020-02-14'
    #     if last_release_date and release_date <= last_release_date:
    #         logger.info('Pass to read PDF: release_date={}'.format(release_date))
    #         return None

    #     logger.warning('Invalid PDF file {}'.format(filepath))
    #     results.append({
    #         'release_date': release_date,
    #         'government': 'nagoya',
    #         'no': 1
    #     })
    #     return results

    for i, text in enumerate(texts):
        text = text.strip().replace('\n', '|')
        if len(text) == 0:
            continue
        elif i == 0 and text == r'別紙':
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
                    raise Exception('Unknown values {} in {}'.format(','.join(stocks), filepath))
                result = {}
                for _item in items:
                    result[_item['key']] = _item['value']
                results.append(result)
                logger.debug('--------')
                items = []

            if d['value']:
                if d['key'] == 'remarks':
                    d['value'] = re.sub(r'^・', '', d['value'])
                item = {
                    'key': d['key'],
                    'value': d['value']
                }
                logger.debug('A> {}'.format(item))

            elif re.match(r'^.+_date$', d['key']):
                for s in list(filter(lambda s: re.match(r'^(\d+月\d+日|－|−)$', s), stocks)):
                    v = 'unknown' if s in ['－', '−'] else util.parse_japanese_date('令和2年'+s).strftime(r'%Y-%m-%d')
                    item = {
                        'key': d['key'],
                        'value': v
                    }
                    logger.debug('P> {}'.format(item))
                    stocks.remove(s)
                    break

            elif d['key'] in ['condition', 'abroad_history', 'nationality']:
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
            for _item in list(filter(lambda _item: _item['key'] == 'nationality' and not _item.get('value'), items)):
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
            for _item in list(filter(lambda _item: re.match(r'^.+_date$', _item['key']), items)):
                if _item['value'] or _item['value'] == '':
                    continue
                item = _item
                item['value'] = util.parse_japanese_date('令和2年' + d['value']).strftime(r'%Y-%m-%d')
                logger.debug('U> {}'.format(item))
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
                item['value'] = item.get('value', '') + d['value']
                logger.debug('+> {}'.format(item))
                break

        elif re.match(r'^・.+$', d['value']):
            for _item in list(filter(lambda _item: _item['key'] == 'remarks', items)):
                item = _item
                item['value'] = re.sub(r'^・', '', d['value'])
                logger.debug('U> {}'.format(item))
                current_key = 'remarks'
                break

        if not item:
            _items = list(filter(lambda r: r['value'] is None, items))
            if len(_items) > 0:
                item = _items[0]
                if re.match(r'^.+_date$', item['key']):
                    if re.match(r'^\d+月\d+日$', d['value']):
                        item['value'] = util.parse_japanese_date('令和2年' + d['value']).strftime(r'%Y-%m-%d')
                    else:
                        item['value'] = ''
                else:
                    item['value'] = d['value']
                logger.debug('O> {}'.format(item))

            else:
                if not current_key:
                    logger.debug('I> %s', d['value'])
                    continue
                elif re.match(r'^\d+$', d['value']):
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
        result['progress'] = result.get('progress') or []
        result['remarks'] = result['remarks'].split('\n') if result.get('remarks') else []

        _revise_detail(result)

    return results


# Read PDF(>=2020-07-24)
def read_release_pdf_2(filepath, release_date):
    results = []

    if re.match(r'^(.+\/|)(341590|342171)\.pdf$', filepath):
        logger.warning('PDF file {}({}) not adopted.'.format(filepath, release_date))
        return None

    HEADERS = {
        'total_no': '症例番号',
        'age': '年代',
        'sex': '性別',
        'area': '居住地',
        'abroad_history': '海外渡航歴',
        'onset_date': '発症日',
        'confirmed_date': '陽性確定日',
        'condition': '症状等',
        'remarks': '特記事項'
    }
    # headers = [
    #     'no', 'age', 'sex', 'area', 'abroad_history',
    #     'onset_date', 'confirmed_date',
    #     'condition', 'remarks'
    # ]

    lines = PDFReader.read_textboxes(filepath)

    if len(lines) == 0:
        return None

    texts = []
    for line in lines:
        text = line.strip().replace('\n', '')
        if len(text) == 0:
            continue
        if re.match(r'^(‐|-|−|―|－){2}$', text):
            texts.extend(['-', '-'])
        else:
            texts.extend(text.split())

    # i = 0
    # while i < len(texts):
    #     texts[i] = texts[i].strip().replace('\n', '')
    #     text = texts[i]
    #     words = text.split()
    #     if len(words) >= 2:
    #         texts[i:i+1] = words
    #         text = texts[i]
    #     elif re.match(r'^(‐|-|−|―|－){2}$', text):
    #         texts[i:i+1] = ['-', '-']
    #         text = texts[i]
    #     i += 1

    i = 0
    ii = 0
    result = None
    while i < len(texts):
        text = texts[i]
        if text in HEADERS.values():
            # logger.debug('({})'.format(text))
            i += 1
            continue
        elif re.match(r'^\d{1}$', text):
            i += 1
            continue

        key = list(HEADERS.keys())[ii]
        logger.debug('{}-[{}]'.format(key, text))

        if key == 'total_no' and re.match(r'^\d+$', text):
            result = result or {}
            if result.get('total_no'):
                if not result or result['total_no'] + 1:
                    results.append(result)
                    logger.debug('------')
                    result = None
                    continue
                elif not result.get('age') and re.match(r'^\d{1,2}0$', text):
                    result['age'] = text + 's'
                    logger.debug('-age:{}'.format(result['age']))
                    i += 1
                    continue
                else:
                    raise Exception('Invalid total_no "{}"'.format(text))

            elif len(results) > 0 and int(text) == results[-1]['total_no'] + 1:
                result['total_no'] = int(text)
                logger.debug('total_no:{}'.format(result['total_no']))
            elif not result.get('age') and re.match(r'^\d{1,2}0$', text):
                result['age'] = text + 's'
                logger.debug('-age:{}'.format(result['age']))
                i += 1
                continue
            elif len(results) == 0:
                result['total_no'] = int(text)
                logger.debug('total_no:{}'.format(result['total_no']))
            else:
                raise Exception('Invalid total_no "{}"'.format(text))

        elif key == 'age' and re.match(r'^\d{1,2}0(未満|)$', text):
            result = result or {}
            if result.get('age'):
                results.append(result)
                logger.debug('------')
                result = None
                continue
            result['age'] = re.sub(r'^(\d+)(未満|)$', r'\1', text) + ('u' if re.match(r'^\d+未満$', text) else 's')
            logger.debug('age:{}'.format(result['age']))

        elif re.match(r'^\d+未満$', text):
            result = result or {}
            if result.get('age'):
                results.append(result)
                logger.debug('------')
                result = None
                continue
            else:
                result['age'] = re.sub(r'^(\d+)未満$', r'\1', text) + 'u'
                logger.debug('-age:{}'.format(result['age']))
                i += 1
                continue

        elif re.match(r'^\d+$', text):
            result = result or {}
            if result.get('total_no'):
                if not result.get('age') and re.match(r'^\d{1,2}0$', text):
                    result['age'] = text + 's'
                    logger.debug('-age:{}'.format(result['age']))
                elif int(text) == result['total_no'] + 1:
                    results.append(result)
                    logger.debug('------')
                    result = None
                    ii = 0
                    continue
            elif len(results) > 0 and int(text) == results[-1]['total_no'] + 1:
                result['total_no'] = int(text)
                logger.debug('+no:{}'.format(result['total_no']))
            elif not result.get('age') and re.match(r'^\d{1,2}0$', text):
                result['age'] = text + 's'
                logger.debug('-age:{}'.format(result['age']))

            else:
                raise Exception('Invalid number "{}"'.format(text))

            i += 1
            continue

        elif key == 'sex' and text in ['男', '女']:
            result = result or {}
            if result.get('sex'):
                raise Exception('Multiple sex "{}"'.format(text))
            result['sex'] = 'male' if text == '男' else 'female'
            logger.debug('sex:{}'.format(result['sex']))

        elif text in ['男', '女']:
            result = result or {}
            if result.get('sex'):
                raise Exception('Multiple sex "{}"'.format(text))
            result['sex'] = 'male' if text == '男' else 'female'
            logger.debug('-sex:{}'.format(result['sex']))
            i += 1
            continue

        elif key == 'area' and re.match(r'^.+(都|道|府|県|市|町|村)$', text):
            if result and result.get('area'):
                raise Exception('Multiple area "{}"'.format(text))
            result = result or {}
            result['area'] = text
            logger.debug('area:{}'.format(result['area']))

        elif re.match(r'^.+(都|道|府|県|市|町|村)$', text):
            result = result or {}
            if result.get('area'):
                raise Exception('Multiple area "{}"'.format(text))
            result['area'] = text
            logger.debug('-area:{}'.format(result['area']))
            i += 1
            continue

        elif key == 'abroad_history':
            if re.match(r'^なし$', text):
                result = result or {}
                result['abroad_history'] = text
                logger.debug('abroad_history:{}'.format(result['abroad_history']))
            else:
                logger.debug('->pass')
                ii = (ii+1) % len(HEADERS)
                continue

        elif key == 'onset_date' and re.match(r'^(\d+月\d+日|‐|-|−|―|－|調査中)$', text):
            result = result or {}
            if re.match(r'^\d+月\d+日$', text):
                result['onset_date'] = util.parse_japanese_date('令和2年' + text).strftime(r'%Y-%m-%d')
            else:
                result['onset_date'] = 'unknown'
            logger.debug('onset_date:{}'.format(result['onset_date']))

        elif key == 'confirmed_date' and re.match(r'^(\d+月\d+日)$', text):
            result = result or {}
            result['confirmed_date'] = util.parse_japanese_date('令和2年' + text).strftime(r'%Y-%m-%d')
            logger.debug('confirmed_date:{}'.format(result['confirmed_date']))

        elif re.match(r'^\d+月\d+日$', text):
            result = result or {}
            if not result.get('onset_date'):
                result['onset_date'] = util.parse_japanese_date('令和2年' + text).strftime(r'%Y-%m-%d')
                logger.debug('-onset_date:{}'.format(result['onset_date']))
            elif not result.get('confirmed_date'):
                result['confirmed_date'] = util.parse_japanese_date('令和2年' + text).strftime(r'%Y-%m-%d')
                logger.debug('-confirmed_date:{}'.format(result['confirmed_date']))
            elif result['onset_date'] == 'unknown' and result.get('confirmed_date') and not result.get('remarks'):
                result['onset_date'] = result['confirmed_date']
                logger.debug('*onset_date:{}'.format(result['onset_date']))
                result['confirmed_date'] = util.parse_japanese_date('令和2年' + text).strftime(r'%Y-%m-%d')
                logger.debug('*confirmed_date:{}'.format(result['confirmed_date']))
                result['remarks'] = ['-']
                logger.debug('*remarks:{}'.format(result['remarks'][0]))
            else:
                raise Exception('Invalid date text "{}"'.format(text))
            i = i + 1
            continue

        elif key == 'condition' and text in ['なし', '軽症', '中等症', '重症', '調査中']:
            result = result or {}
            if result.get('condition'):
                if result['condition'] == '調査中' and result.get('onset_date') == 'unknown':
                    result['condition'] = text
                    logger.debug('*condition:{}'.format(result['condition']))
                else:
                    raise Exception('Multiple condition "{}"'.format(text))
            else:
                result['condition'] = text
                logger.debug('condition:{}'.format(result['condition']))

        elif text in ['軽症', '中等症', '重症']:
            result = result or {}
            if result.get('condition'):
                raise Exception('Multiple condition "{}"'.format(text))
            result['condition'] = text
            logger.debug('-condition:{}'.format(result['condition']))
            i = i + 1
            continue

        elif re.match(r'^なし$', text):
            result = result or {}
            if not result.get('abroad_history'):
                result['abroad_history'] = text
                logger.debug('-abroad_history:{}'.format(result['abroad_history']))
            elif not result.get('condition'):
                result['condition'] = text
                logger.debug('-condition:{}'.format(result['condition']))
            else:
                raise Exception('Invalid date text "{}"'.format(text))
            i += 1
            continue

        elif text == '調査中':
            result = result or {}
            if not result.get('onset_date'):
                result['onset_date'] = 'unknown'
                logger.debug('-onset_date:{}'.format(result['onset_date']))
            elif result['onset_date'] == 'unknown' and not result.get('remarks'):
                result['remarks'] = ['-']
                logger.debug('*remarks:{}'.format(result['remarks'][0]))
            if not result.get('condition'):
                result['condition'] = text
                logger.debug('-condition:{}'.format(result['condition']))
            else:
                raise Exception('Invalid date text "{}"'.format(text))
            i = i + 1
            continue

        elif key == 'remarks':
            result = result or {}
            if result.get('remarks'):
                results.append(result)
                logger.debug('------')
                result = None
                continue
            elif text in ['‐', '-', '−', '―', '－']:
                if len(results) > 0 and not results[-1].get('remarks'):
                    results[-1]['remarks'] = ['-']
                    logger.debug('({}) remarks:{}'.format(results[-1]['total_no'], results[-1]['remarks'][0]))
                else:
                    result['remarks'] = ['-']
                    logger.debug('remarks:{}'.format(result['remarks'][0]))
            else:
                result['remarks'] = [text]
                logger.debug('remarks:{}'.format(result['remarks'][0]))

        elif re.match(r'^(県内|.+都|.+道|.+府|.+県|.+市)\d+例目.*の.+$', text) or \
                re.match(r'^.+(都|道|府|県|市)事例の.+$', text) or \
                re.match(r'^.+に滞在$', text):
            result = result or {}
            if result.get('remarks'):
                results.append(result)
                logger.debug('------')
                result = None
                continue
            else:
                result['remarks'] = [text]
                logger.debug('-remarks:{}'.format(result['remarks'][0]))
            i += 1
            continue

        elif text in ['-', '−', '－']:
            if result:
                if not result.get('onset_date'):
                    result['onset_date'] = 'unknown'
                    logger.debug('-onset_date:{}'.format(result['onset_date']))
                elif not result.get('remarks'):
                    result['remarks'] = ['-']
                    logger.debug('-remarks:{}'.format(result['remarks'][0]))
                elif result.get('total_no'):
                    results.append(result)
                    logger.debug('------')
                    result = None
                    continue
                else:
                    print(texts[i-5:i+3])
                    raise Exception('Invalid text "{}"'.format(text))
            else:
                result = {
                    'remarks': ['-']
                }
                logger.debug('+remarks:{}'.format(result['remarks'][0]))
            i += 1
            continue

        else:
            print(texts[i-2:i+3])
            raise Exception('Invalid text "{}"'.format(text))

        ii = (ii+1) % len(HEADERS)
        i += 1
        # if i > 80:
        #     break

    if result:
        results.append(result)
        logger.debug('------')

    for result in results:
        if result.get('remarks'):
            remark = result['remarks'][0]
            if remark == '-':
                result['remarks'] = []
            elif re.match(r'^県内\d+例目.*の.+（濃厚接触者）$', remark):
                person_no, relationship = \
                    re.sub(r'^県内(\d+)例目.*の(.+)（濃厚接触者）$', r'\1 \2', remark).split()
                result['contacts'] = result.get('contacts') or []
                result['contacts'].append({'person_no': int(person_no), 'relationship': relationship})

    return results


# Read PDF
def read_release_pdf(filepath, release_date, debug=False):

    if debug:
        logger.setLevel(logging.DEBUG)

    results = None

    try:
        if release_date <= '2020-07-23':
            results = read_release_pdf_1(filepath, release_date)
        else:
            results = read_release_pdf_2(filepath, release_date)

        if results is None:
            filename = re.sub(r'^(|.*\/)([^\/]+\.pdf)$', r'\2', filepath)
            cd = list(filter(lambda d: d['filename'] == filename, CUSTOM_DETAILS))
            if len(cd) == 0:
                raise Exception('Cannot read PDF file:{}'.format(filepath))

            logger.warning('PDF file {} is not valid format, so add custom data.'.format(filename))
            results = cd[0]['results']

        return results

    except Exception as e:
        raise Exception('{} / file:{}'.format(e, filepath))
        return None


def scrape_release_details(url, release_date, debug=False):
    results = []

    try:
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
            pdf_results = read_release_pdf(filepath, release_date, debug=debug)
            for result in pdf_results:
                result.update({
                    'url': url,
                    'pdf_url': pdf_url,
                })
                results.append(result)

        else:
            detail_free = soup.body.select('.detail_free')
            if detail_free is None:
                raise Exception('class "detail_free" not found.')

            # <h2>1　患者Ａについて</h2>
            # <h2>1　患者Ａについて（県内xx例目）</h2>
            headers = []
            header = detail_free[0].find('h2', text=re.compile(r'^.*患者概要$'))
            if header:
                headers = [header]
            else:
                # headers = detail_free[0].find_all('h2', text=re.compile(r'^.*患者.*について.*$'))
                headers = list(filter(
                    lambda h2: re.match(r'^\d+\s+患者.*について.*$', h2.text), detail_free[0].find_all('h2')))

            results = list(map(lambda tag: _scrape_aichi_detail_2(tag), headers))
            results = list(filter(lambda r: r is not None, results))

            if len(results) == 0:
                results.append({'url': url})

        return results

    except HTTPError as err:
        if err.code == 404:
            logger.warning('HTTP Error [%s]%s url=%s', err.code, err.reason, url)
            return None

        raise err


# def _scrape_aichi_press_releases(last_release_date=None):
#     results = []

#     soup = Soup.create_soup(config.AICHI_PRESS_RELEASE_URL)

#     detail_free = soup.body.select('.detail_free')[0]
#     ps = detail_free.select('p')
#     for p in ps:
#         result = {}
#         if re.match(r'^\d+年\d+月\d+日更新.*$', p.text) is None:
#             continue
#         year, month, day = \
#             re.sub(r'^(\d+)年(\d+)月(\d+)日.*$', r'\1 \2 \3', p.text).split()

#         result['date'] = \
#             date(year=int(year), month=int(month), day=int(day)).strftime(r'%Y-%m-%d')
#         if last_release_date and result['date'] <= last_release_date:
#             continue

#         a = p.select('a')[0]
#         if not re.match(r'^新型コロナウ(イ|ィ)ルス感染症患者の発生について.*$', a.text):
#             continue
#         result['text'] = a.text
#         result['url'] = urllib.parse.urljoin(config.AICHI_PRESS_RELEASE_URL, a['href'])

#         results.append(result)

#     return list(reversed(results))

def _scrape_aichi_press_releases(last_release_date=None):
    results = []

    soup = Soup.create_soup(config.AICHI_PRESS_RELEASE_URL)

    main_body = soup.body.select_one('#main_body')
    for li in main_body.select_one('ul').select('li'):
        result = {}
        if re.match(r'^\d+年\d+月\d+日更新.*$', li.text) is None:
            continue
        year, month, day = \
            re.sub(r'^(\d+)年(\d+)月(\d+)日.*$', r'\1 \2 \3', li.text).split()
        result['date'] = \
            date(year=int(year), month=int(month), day=int(day)).strftime(r'%Y-%m-%d')
        if last_release_date and result['date'] <= last_release_date:
            continue

        a = li.select_one('a')
        if not re.match(r'^新型コロナウ(イ|ィ)ルス感染症患者の発生について.*$', a.text):
            continue
        result['text'] = a.text
        result['url'] = urllib.parse.urljoin(config.AICHI_PRESS_RELEASE_URL, a['href'])

        results.append(result)

    return list(reversed(results))


def scrape_releases(last_release_date=None, start_no=None, debug=False):

    releases = _scrape_aichi_press_releases(last_release_date=last_release_date)
    results = []

    # release = list(filter(lambda r: r['date'] == '2020-07-17', releases))[0]

    no = start_no or 2
    for i, release in enumerate(releases):
        # if last_release_date and release['date'] <= last_release_date:
        #     logger.info('detail {}/{} {} - pass'.format(i + 1, len(releases), release['date']))
        #     continue
        details = scrape_release_details(release['url'], release['date'], debug=debug)
        if not details:
            logger.info('detail {}/{} {} - nodata'.format(i + 1, len(releases), release['date']))
            continue

        for detail in details:

            if detail.get('total_no') == 285:
                no = 100
            elif detail.get('total_no') == 328:
                no = 118

            detail.update({
                'no': no,
                'release_date': release['date'],
                'government': 'aichi',
                'url': release['url']
            })

            no += 1

        logger.info(
            'detail {}/{} {} {}-{}'.format(i+1, len(releases), release['date'], details[0]['no'], details[-1]['no']))

        results.extend(details)

    if last_release_date:
        results = list(filter(lambda r: r['release_date'] > last_release_date, results))
    return results


# Main
if __name__ == '__main__':

    # details = read_release_pdf('data/aichi/351514.pdf', '2020-12-01', debug=True)
    # exit()

    last_release_date, start_no = None, None
    current_details = Detail.find_by_government('aichi', order=['-no'], limit=1)
    if len(current_details) > 0:
        last_release_date = current_details[0]['release_date']
        start_no = current_details[0]['no'] + 1

    details = scrape_releases(last_release_date=last_release_date, start_no=start_no)

    for detail in details:
        pprint(detail)
        Detail.insert(detail)
        logger.info('Add Aichi detail [%s]', detail['no'])

        if detail.get('total_no'):
            person = Person.find_by_no(detail['total_no'])
            if not person:
                logger.warn('Person[{}] not exists.'.format(detail['total_no']))
                continue

            updated = False
            for d_contact in detail.get('contacts', []):
                cs = list(filter(
                    lambda c: c['person_no'] == d_contact['person_no'] and d_contact.get('relationship'),
                    person.get('contacts', [])))
                for contact in cs:
                    contact['relationship'] = contact.get('relationship', d_contact['relationship'])
                    updated = True

            if updated:
                pprint(person)
                Person.update(person)
                logger.info('Update Person [%s]', person['no'])

    exit()
