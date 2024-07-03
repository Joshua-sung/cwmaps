import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
API_KEY = os.getenv('API_KEY')

# 하루 요청 한도 설정
DAILY_REQUEST_LIMIT = 100000
request_count = 0

# 도시와 국가 설정
city = "Sapporo"
country = "Japan"

# 카테고리 목록
categories = [
    'Historic site', 'Cultural Heritage', 'Temple', 'Landmark','Museums' ,'Nature Reserve',
    'Theme Park', 'Natural Scenery', 'National Park', 'Activity', 'Things to do',
    'Wildlife Sanctuary', 'Architectural Marvel',
    'Shrine', 'Beach', 'Waterfall', 'Lake', 'Botanical Garden', 
    'Public Park', 'Urban Park', 'Gardens', 'Night View', 
    'Theme Tour', 'Local Festival', 'Traditional Market', 'Monument', 'Castle', 
    'Fort', 'Historical Village', 'Archaeological Site', 'Historical Building', 
    'Art Gallery', 'Art District', 'Museum of Art', 
]

# 저장할 최대 데이터 개수
max_data_count = 185

# 모든 결과를 저장할 리스트 및 중복 확인을 위한 집합
all_results = []
unique_map_urls = set()

# 캐시 파일 경로
CACHE_FILE = 'place_details_cache.json'
PLACE_ID_CACHE_FILE = 'place_id_cache.json'

# 캐시 유효 기간 (30일)
CACHE_EXPIRY_DAYS = 30

# 캐시 로드 함수
def load_cache(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

# 캐시 저장 함수
def save_cache(cache, file_path):
    with open(file_path, 'w') as f:
        json.dump(cache, f)

# 캐시 초기화
details_cache = load_cache(CACHE_FILE)
place_id_cache = load_cache(PLACE_ID_CACHE_FILE)

# 캐시 유효성 검사 함수
def is_cache_valid(cache_entry):
    return datetime.strptime(cache_entry['timestamp'], '%Y-%m-%d %H:%M:%S') > datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)

def get_place_details(place_id, language='ko'):
    global request_count
    # 요청 한도 초과 여부 확인
    if request_count >= DAILY_REQUEST_LIMIT:
        print("Daily request limit reached.")
        return {}

    # 캐시에서 데이터 검색
    if place_id in details_cache and is_cache_valid(details_cache[place_id]):
        return details_cache[place_id]['data']
    
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}&language={language}&fields=name,formatted_address,rating,user_ratings_total,formatted_phone_number,international_phone_number,website,opening_hours,reviews"
    response = requests.get(url)
    request_count += 1
    if response.status_code != 200:
        print(f"Error fetching details for place_id {place_id}: {response.status_code}")
        return {}
    
    data = response.json().get('result', {})
    # 캐시에 데이터 저장
    details_cache[place_id] = {'data': data, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    save_cache(details_cache, CACHE_FILE)
    
    return data

def get_place_ids(query, page_token=None):
    global request_count
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}&fields=place_id,name"
    if page_token:
        url += f"&pagetoken={page_token}"

    response = requests.get(url)
    request_count += 1
    if response.status_code != 200:
        print(f"Error fetching results for query {query}: {response.status_code}")
        return None, None
    
    places = response.json().get('results', [])
    next_page_token = response.json().get('next_page_token')
    if not places:
        print(f"No places found for query {query}")
        return None, None
    
    place_ids = [place['place_id'] for place in places]
    return place_ids, next_page_token

def clean_unicode_escape_sequences(s):
    return s.encode('ascii', 'ignore').decode('ascii')

for category in categories:
    print(f"Processing category: {category}")
    query = f"{city} {category}"
    next_page_token = None

    while True:
        place_ids, next_page_token = get_place_ids(query, next_page_token)
        if not place_ids:
            break

        for place_id in place_ids:
            details_ko = get_place_details(place_id, language='ko')
            details_en = get_place_details(place_id, language='en')

            name_ko = details_ko.get('name', '')
            name_en = details_en.get('name', '')
            
            if name_ko and name_en:
                if name_ko == name_en:
                    name = name_en
                else:
                    name = f"{name_ko}({name_en})"
            else:
                name = name_ko or name_en

            rating = details_ko.get('rating', '0')
            reviews = details_ko.get('user_ratings_total', 0)
            if reviews < 50:
                continue  # 리뷰 수가 50개 미만인 장소는 무시

            operation_time = details_en.get('opening_hours', {}).get('weekday_text', [])
            if not operation_time:
                operation_time = ""
            else:
                # 유니코드 이스케이프 시퀀스를 제거하면서 요일 정보를 유지
                operation_time = [clean_unicode_escape_sequences(s) for s in operation_time]
                operation_time = ', '.join(operation_time)
            
            map_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            
            # 중복 확인 및 추가
            if map_url in unique_map_urls:
                continue
            unique_map_urls.add(map_url)
            
            # 연락처 정보 수집
            phone_number = details_ko.get('formatted_phone_number', '') or details_en.get('formatted_phone_number', '')
            international_phone_number = details_ko.get('international_phone_number', '') or details_en.get('international_phone_number', '')
            website = details_ko.get('website', '') or details_en.get('website', '')

            # 연락처 정보를 information 필드에 포함
            information = {
                '전화번호': phone_number,
                '국제 전화번호': international_phone_number,
                '웹사이트': website
            }
            
            # 정보를 문자열로 결합
            information_str = ', '.join([f"{key}: {value}" for key, value in information.items() if value])

            all_results.append({
                'nation': country,
                'region': city,
                'name': name,
                'operationTime': operation_time,
                'expense': '',  # 전부 빈칸으로 저장
                'infoTitle': '',
                'infoContent': '',
                'information': information_str,
                'map_url': map_url,
                'rating': rating,
                'reviews': reviews
            })

        if not next_page_token:
            break
        # Google Places API에서 페이지 토큰이 유효해지기 위해 약간의 지연이 필요할 수 있습니다.
        time.sleep(2)

# 리뷰 수를 기준으로 데이터 정렬
all_results_sorted = sorted(all_results, key=lambda x: x['reviews'], reverse=True)

# 상위 max_data_count개의 데이터만 저장
data_to_save = all_results_sorted[:min(max_data_count, len(all_results_sorted))]

# 고유 번호를 부여
for idx, item in enumerate(data_to_save, start=1):
    item['data id_info'] = idx

# 모든 결과를 DataFrame으로 변환
df = pd.DataFrame(data_to_save)

# 열 이름을 재정렬
required_columns = ['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'rating', 'reviews']
df = df[required_columns]

# CSV 파일 저장
output_file = f'{city}_travel_places.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"Data saved to {output_file}")

# 최종 요청 횟수 출력
print(f"Total API requests made: {request_count}")
