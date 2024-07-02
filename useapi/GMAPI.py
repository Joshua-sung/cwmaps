import os
from dotenv import load_dotenv
import requests
import pandas as pd
import time

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
API_KEY = os.getenv('API_KEY')

# 도시와 국가 설정
city = "Osaka"
country = "Japan"

# 카테고리 목록
categories = [
    'Historic site', 'Theme Park', 'Activity', 'Natural Scenery', 'Things to do', 
    'Museums'
    , 'Night View', 'Nature Reserve', 'Zoo', 'Theme Tour', 
    'Monument', 'Art Gallery', 'Museum of Art', 'Landmark', 'Cultural Heritage',
    'Botanical Garden', 'Hiking Trail', 'Wildlife Sanctuary', 
    'Mountain View', 'Waterfall', 'Lake', 'Beach', 'National Park', 
    'Historical Village', 'Archaeological Site', 'Castle', 'Fort', 
    'Traditional Market', 'Local Festival', 'Scenic Railway', 'Gardens', 
    'Public Park', 'Skyline View', 'Adventure Park', 
    'Botanical Park', 'Urban Park', 'Art District', 
    'Historical Building', 'Architectural Marvel'
]

# 저장할 최대 데이터 개수
max_data_count = 213

# 모든 결과를 저장할 리스트 및 중복 확인을 위한 집합
all_results = []
unique_place_ids = set()

def get_place_details(place_id, language='ko'):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}&language={language}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching details for place_id {place_id}: {response.status_code}")
        return {}
    return response.json().get('result', {})

def clean_unicode_escape_sequences(s):
    return s.encode('ascii', 'ignore').decode('ascii')

for category in categories:
    print(f"Processing category: {category}")
    query = f"{city} {category}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}&language=ko"
    
    while True:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching results for query {query}: {response.status_code}")
            break
        places = response.json().get('results', [])
        
        if not places:
            print(f"No places found for query {query}")
            break
        
        for place in places:
            place_id = place['place_id']
            
            if place_id in unique_place_ids:
                continue  # 이미 처리된 장소는 무시
            
            unique_place_ids.add(place_id)
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

        # 다음 페이지 결과 확인
        next_page_token = response.json().get('next_page_token')
        if next_page_token:
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?pagetoken={next_page_token}&key={API_KEY}&language=ko"
            # 페이지 토큰 적용을 위한 지연
            time.sleep(2)
        else:
            break

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
