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

# 사용자 정의 변수
max_data_count = 140  # 저장할 최대 데이터 개수
DAILY_REQUEST_LIMIT = 250  # 하루 요청 한도 설정
request_count = 0  # 현재 요청 횟수
city = "Kobe"  # 도시 설정
country = "Japan"  # 국가 설정
categories = [
    'Historic site', 'Theme Park', 'Activity', 'Natural Scenery','Tourist attraction','Things to do', 
    'Museums','Landmark',
    'Night View', 'Nature Reserve', 'Zoo', 'Theme Tour', 'Traditional Market', 
    'Architectural Marvel','Monument', 'Art Gallery', 'Museum of Art',  'Cultural Heritage',
    'Botanical Garden', 'Hiking Trail', 'Wildlife Sanctuary', 
    'Mountain View', 'Waterfall', 'Lake', 'Beach', 'National Park', 
    'Historical Village', 'Archaeological Site', 'Castle', 'Fort', 
    'Local Festival', 'Scenic Railway', 'Gardens', 
    'Public Park', 'Skyline View', 'Adventure Park', 
    'Botanical Park', 'Urban Park', 'Art District', 
    'Historical Building', 
]

# 모든 결과를 저장할 리스트 및 중복 확인을 위한 집합
all_results = []  # 모든 결과를 저장할 리스트
unique_place_ids = set()  # 중복 확인을 위한 집합
unique_place_urls = set()  # 중복 확인을 위한 URL 집합

# 캐시 파일 경로 생성
cache_dir = 'cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
details_cache_file = os.path.join(cache_dir, f'{city}_place_details_cache.json')

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
details_cache = load_cache(details_cache_file)

# 캐시 유효성 검사 함수
def is_cache_valid(cache_entry):
    return datetime.strptime(cache_entry['timestamp'], '%Y-%m-%d %H:%M:%S') > datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)

def get_place_ids(query, language='ko', page_token=None):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}&language={language}"
    if page_token:
        url += f"&pagetoken={page_token}"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching results for query {query}: {response.status_code}")
        return None, None

    places = response.json().get('results', [])
    next_page_token = response.json().get('next_page_token')
    if not places:
        print(f"No places found for query {query}")
        return None, None

    place_ids = [(place['place_id'], place['name']) for place in places]
    return place_ids, next_page_token

def get_place_details(place_id):
    global request_count
    if request_count >= DAILY_REQUEST_LIMIT:
        print("Daily request limit reached.")
        return {}

    # 캐시에서 데이터 검색
    if place_id in details_cache and is_cache_valid(details_cache[place_id]):
        return details_cache[place_id]['data']

    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}&fields=name,formatted_address,rating,user_ratings_total,formatted_phone_number,international_phone_number,website,opening_hours,reviews"
    response = requests.get(url)
    request_count += 1
    if response.status_code != 200:
        print(f"Error fetching details for place_id {place_id}: {response.status_code}")
        return {}

    data = response.json().get('result', {})
    # 캐시에 데이터 저장
    details_cache[place_id] = {'data': data, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    save_cache(details_cache, details_cache_file)

    return data

def clean_unicode_escape_sequences(s):
    return s.encode('ascii', 'ignore').decode('ascii')

def convert_to_24_hour(time_str):
    """시간 문자열을 24시간 형식으로 변환"""
    try:
        # 12시간 형식 변환 시도
        in_time = datetime.strptime(time_str, "%I:%M %p")
        return in_time.strftime("%H:%M")
    except ValueError:
        try:
            # 24시간 형식 변환 시도
            in_time = datetime.strptime(time_str, "%H:%M")
            return in_time.strftime("%H:%M")
        except ValueError:
            raise ValueError(f"time data '{time_str}' does not match format '%I:%M %p' or '%H:%M'")

def parse_opening_hours(opening_hours):
    if not opening_hours:
        return ""

    weekday_text = opening_hours.get('weekday_text', [])
    if not weekday_text:
        return ""

    # 영어 요일을 한글로 변환하는 딕셔너리
    weekday_translation = {
        'Monday': '월',
        'Tuesday': '화',
        'Wednesday': '수',
        'Thursday': '목',
        'Friday': '금',
        'Saturday': '토',
        'Sunday': '일',
        'Closed': '휴무'
    }

    # 연중무휴 24시간 운영 처리
    if len(set(weekday_text)) == 1 and "Open 24 hours" in weekday_text[0]:
        return "연중무휴"

    hours_dict = {}
    for entry in weekday_text:
        day, hours = entry.split(": ", 1)
        if "Closed" in hours:
            hours = "휴무"
        day = weekday_translation.get(day, day)  # 요일을 한글로 변환
        if hours in hours_dict:
            hours_dict[hours].append(day)
        else:
            hours_dict[hours] = [day]

    formatted_hours = []
    for hours, days in hours_dict.items():
        formatted_days = ", ".join(days)
        try:
            if "AM" in hours or "PM" in hours:
                start_time, end_time = hours.split(" – ")
                start_time_24 = convert_to_24_hour(start_time.strip())
                end_time_24 = convert_to_24_hour(end_time.strip())
                hours = f"{start_time_24}~{end_time_24}"
            formatted_hours.append(f"{formatted_days}: {hours}")
        except ValueError:
            formatted_hours.append(f"{formatted_days}: {hours} (unparsed)")

    return "; ".join(formatted_hours)

for category in categories:
    print(f"Processing category: {category}")
    query = f"{city} {category}"
    next_page_token_ko = None
    next_page_token_en = None

    while True:
        place_ids_ko, next_page_token_ko = get_place_ids(query, language='ko', page_token=next_page_token_ko)
        place_ids_en, next_page_token_en = get_place_ids(query, language='en', page_token=next_page_token_en)

        if not place_ids_ko or not place_ids_en:
            break

        for (place_id_ko, name_ko), (place_id_en, name_en) in zip(place_ids_ko, place_ids_en):
            if place_id_ko != place_id_en:
                continue

            if place_id_en in unique_place_ids:
                continue  # 이미 처리된 장소는 무시

            unique_place_ids.add(place_id_en)

            # 한글 및 영어 이름 가져오기
            if name_ko and name_en:
                if name_ko == name_en:
                    place_name = name_en
                else:
                    place_name = f"{name_ko}({name_en})"
            else:
                place_name = name_en

            details = get_place_details(place_id_en)
            rating = details.get('rating', '0')
            popularity = details.get('user_ratings_total', 0)
            if popularity < 0:
                continue  # 리뷰 수가 0개 미만인 장소는 무시

            operation_time = parse_opening_hours(details.get('opening_hours', {}))

            map_url = f"https://www.google.com/maps/place/?q=place_id:{place_id_en}"

            # 중복 확인 및 추가
            if map_url in unique_place_urls:
                continue
            unique_place_urls.add(map_url)

            # 연락처 정보 수집
            international_phone_number = details.get('international_phone_number', '')
            website = details.get('website', '')

            # 연락처 정보를 information 필드에 포함
            information = {
                '국제전화번호': international_phone_number,
                '홈페이지': website
            }

            # 정보를 문자열로 결합
            information_str = ' '.join([f"{key}: {value}" for key, value in information.items() if value])

            all_results.append({
                'nation': country,
                'region': city,
                'name': place_name,
                'operationTime': operation_time,
                'expense': '',  # 전부 빈칸으로 저장
                'infoTitle': '',
                'infoContent': '',
                'information': information_str,
                'map_url': map_url,
                'rating': rating,
                'popularity': popularity
            })

        if not next_page_token_ko or not next_page_token_en:
            break
        # Google Places API에서 페이지 토큰이 유효해지기 위해 약간의 지연이 필요할 수 있습니다.
        time.sleep(2)

# 리뷰 수를 기준으로 데이터 정렬
all_results_sorted = sorted(all_results, key=lambda x: x['popularity'], reverse=True)

# 상위 max_data_count개의 데이터만 저장
data_to_save = all_results_sorted[:min(max_data_count, len(all_results_sorted))]

# 고유 번호를 부여
for idx, item in enumerate(data_to_save, start=1):
    item['data id_info'] = idx

# 모든 결과를 DataFrame으로 변환
df = pd.DataFrame(data_to_save)

# 열 이름을 재정렬
required_columns = ['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'popularity','rating' ]
df = df[required_columns]

# CSV 파일 저장
output_file = f'{city}_travel_places_api.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"Data saved to {output_file}")

# 최종 요청 횟수 출력
print(f"Total API requests made: {request_count}")
