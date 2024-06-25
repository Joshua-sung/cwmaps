# 필요한 패키지 임포트
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# ChromeDriver 설정 및 초기화
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 카테고리 목록 (영어로 변경)
categories = {
    'Historic site': 'Khao Lak Historic site',
    'Theme Park': 'Khao Lak Theme Park',
    'Activity': 'Khao Lak Activity',
    'Natural Scenery': 'Khao Lak Natural Scenery',
    'Things to do': 'Khao Lak Things to do',
    'Museums': 'Khao Lak Museums'
}

# 모든 결과를 저장할 리스트
all_results = []

# 고유 번호를 위한 초기값
id_counter = 1

# 각 카테고리에 대해 데이터 추출
for category, query in categories.items():
    # Google Maps 접속
    driver.get("https://www.google.com/maps")
    
    # 검색창에 카테고리 검색어 입력
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    
    # 페이지 로드 대기
    time.sleep(5)
    
    # 여행지 정보 추출
    places = driver.find_elements(By.CLASS_NAME, 'Nv2PK')
    
    for place in places:
        try:
            # 기본 정보 추출
            name = place.find_element(By.CLASS_NAME, 'qBF1Pd').text
            try:
                rating = place.find_element(By.CLASS_NAME, 'MW4etd').text
            except:
                rating = '0'  # 평점이 없는 경우 기본값 설정
            map_url = place.find_element(By.TAG_NAME, 'a').get_attribute('href')
            try:
                reviews = place.find_element(By.CLASS_NAME, 'UY7F9').text
            except:
                reviews = '0'  # 리뷰가 없는 경우 기본값 설정

            # 상세 페이지로 이동하여 추가 정보 추출
            place.find_element(By.TAG_NAME, 'a').click()
            time.sleep(3)  # 페이지 로드 대기
            
            operation_time = ""
            expense = ""
            info_title = ""
            info_content = ""
            information = ""
            
            try:
                operation_time = driver.find_element(By.XPATH, "//div[@data-section-id='hours']/div/div[1]").text
            except:
                pass
            
            try:
                expense = driver.find_element(By.XPATH, "//div[@data-section-id='price']/div/span[1]").text
            except:
                pass
            
            try:
                info_title = driver.find_element(By.CLASS_NAME, 'section-summary-title').text
                info_content = driver.find_element(By.CLASS_NAME, 'section-summary-text').text
            except:
                pass
            
            try:
                information = driver.find_element(By.XPATH, "//div[@data-section-id='phone']/div/span[1]").text
            except:
                pass
            
            all_results.append({
                'data id_info': id_counter,
                'nation': 'Thailand',  # 국가 추가
                'region': 'Khao Lak',  # 도시 이름 추가
                'name': name,
                'operationTime': operation_time,
                'expense': expense,
                'infoTitle': info_title,
                'infoContent': info_content,
                'information': information,
                'map_url': map_url,
                'rating': rating,
                'reviews': reviews
            })
            
            id_counter += 1  # 고유 번호 증가
            
            driver.back()
            time.sleep(3)
        except Exception as e:
            print(f"Error occurred: {e}")
            continue

# 모든 결과를 DataFrame으로 변환
df = pd.DataFrame(all_results)

# rating을 float으로 변환 (예외 발생 시 0으로 설정)
if 'rating' in df.columns:
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)

# reviews에서 쉼표 제거하고 숫자로 변환 (예외 발생 시 0으로 설정)
if 'reviews' in df.columns:
    df['reviews'] = df['reviews'].str.replace(',', '').astype(int, errors='ignore').fillna(0)

# 중복 데이터 제거 (map_url 기준)
df.drop_duplicates(subset=['map_url'], inplace=True)

# 고유 번호 재부여
df.reset_index(drop=True, inplace=True)
df['data id_info'] = df.index + 1

# 결과 출력 (포맷에 맞게 재정렬)
df = df[['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'rating', 'reviews']]

# CSV 파일로 저장
df.to_csv('khaolak_travel_places.csv', index=False, encoding='utf-8-sig')

# 포맷 정보 저장
format_info = {
    'class(kr)': ['data id_info', '국가', '지역', '이름', '영업시간', '가격', '여행지 정보(간략)', '여행지 정보(상세)', '문의처', '구글지도 링크', '평점', '리뷰 수'],
    'class(en)': ['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'rating', 'reviews'],
    'type': ['num', 'string', 'string', 'string', 'string', 'string', 'string', 'string', 'string', 'url', 'num', 'num']
}

# 각 배열의 길이를 동일하게 맞추기 위해 동일한 길이의 배열로 변환
max_len = max(len(format_info['class(kr)']), len(format_info['class(en)']), len(format_info['type']))

for key in format_info:
    if len(format_info[key]) < max_len:
        format_info[key].extend([''] * (max_len - len(format_info[key])))

format_df = pd.DataFrame(format_info)
format_df.to_csv('format_info.csv', index=False, encoding='utf-8-sig')

# 브라우저 닫기
driver.quit()
