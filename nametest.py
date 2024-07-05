import os
from dotenv import load_dotenv
import requests
import time

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
API_KEY = os.getenv('API_KEY')

# 도시와 국가 설정
city = "Hanoi"
country = "Vietnam"

# 카테고리 목록
categories = ['Historic site']

# 하루 요청 한도 설정
DAILY_REQUEST_LIMIT = 5
request_count = 0

def get_place_ids(query, language='ko', page_token=None):
    global request_count
    if request_count >= DAILY_REQUEST_LIMIT:
        print("Daily request limit reached.")
        return None, None

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}&language={language}"
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
    
    place_ids = [(place['place_id'], place['name']) for place in places]
    return place_ids, next_page_token

for category in categories:
    print(f"Processing category: {category}")
    query = f"{city} {category}"
    next_page_token_ko = None
    next_page_token_en = None

    while request_count < DAILY_REQUEST_LIMIT:
        place_ids_ko, next_page_token_ko = get_place_ids(query, language='ko', page_token=next_page_token_ko)
        place_ids_en, next_page_token_en = get_place_ids(query, language='en', page_token=next_page_token_en)

        if not place_ids_ko or not place_ids_en:
            break

        for (place_id_ko, name_ko), (place_id_en, name_en) in zip(place_ids_ko, place_ids_en):
            if place_id_ko != place_id_en:
                continue
            print(f"Place ID: {place_id_ko}, Name (KO): {name_ko}, Name (EN): {name_en}")

        if not next_page_token_ko or not next_page_token_en:
            break
        # Google Places API에서 페이지 토큰이 유효해지기 위해 약간의 지연이 필요할 수 있습니다.
        time.sleep(2)
