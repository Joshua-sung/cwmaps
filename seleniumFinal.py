# 필요한 패키지 임포트
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re

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

# 국가 정보
country = "China"

# 도시 목록
cities = [
    "Yanbian",
]

# 카테고리 목록 (영어로 변경)
categories = [
    'Historic site', 'Theme Park', 'Activity', 'Natural Scenery','Tourist attraction','Things to do', 
    'Museums','Landmark',
    'Night View', 'Nature Reserve', 'Zoo', 'Theme Tour', 'Traditional Market', 
    'Architectural Marvel','Monument', 'Art Gallery', 'Museum of Art', 'Cultural Heritage',
    'Botanical Garden', 'Hiking Trail', 'Wildlife Sanctuary', 
    'Mountain View', 'Waterfall', 'Lake', 'Beach', 'National Park', 
    'Historical Village', 'Archaeological Site', 'Castle', 'Fort', 
    'Local Festival', 'Scenic Railway', 'Gardens', 
    'Public Park', 'Skyline View', 'Adventure Park', 
    'Botanical Park', 'Urban Park', 'Art District', 
    'Historical Building'
]

# 중복 URL을 확인하기 위한 집합
unique_urls = set()

def get_places(driver):
    return driver.find_elements(By.CLASS_NAME, 'Nv2PK')

for city in cities:
    all_results = []  # 각 도시마다 결과 리스트를 초기화
    for category in categories:
        query = f"{city} {category}"
        # Google Maps 접속
        maps_url = f"https://www.google.com/maps/place/{country},+{city}/"
        driver.get(maps_url)
        
        # 페이지 로드 대기
        wait = WebDriverWait(driver, 8)
        search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
        
        # 검색창에 카테고리 검색어 입력
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        # 페이지 로드 대기
        time.sleep(5)
        
        # 스크롤을 5번만 수행하도록 설정
        scroll_attempts = 0
        max_scrolls = 5
        endliststrings = ["You've reached the end of the list.", "마지막 항목입니다."]

        while scroll_attempts < max_scrolls:
            search_results = driver.find_elements(By.CLASS_NAME, 'hfpxzc')
            if search_results:
                driver.execute_script("return arguments[0].scrollIntoView();", search_results[-1])
            time.sleep(1)
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            if any(endliststring in page_text for endliststring in endliststrings):
                break
            scroll_attempts += 1
        
        # 여행지 정보 추출
        places = get_places(driver)

        for place in places:
            try:
                # 기본 정보 추출
                name = place.find_element(By.CLASS_NAME, 'qBF1Pd').text
                rating = place.find_element(By.CLASS_NAME, 'MW4etd').text if place.find_elements(By.CLASS_NAME, 'MW4etd') else '0'
                map_url = place.find_element(By.TAG_NAME, 'a').get_attribute('href')
                if map_url in unique_urls:
                    continue  # 이미 처리된 URL은 무시
                
                unique_urls.add(map_url)
                
                popularity = place.find_element(By.CLASS_NAME, 'UY7F9').text if place.find_elements(By.CLASS_NAME, 'UY7F9') else '0'
                popularity = re.sub(r'[^\d]', '', popularity)  # 숫자가 아닌 문자 제거
                popularity = int(popularity) if popularity else 0  # 빈 문자열을 0으로 처리
                if popularity < 0:
                    continue  # 리뷰 수가 0 미만인 경우 무시

                info_content = None
                expense = None

                # 상세 페이지로 이동하여 추가 정보 추출
                place.find_element(By.TAG_NAME, 'a').click()
                time.sleep(3)  # 페이지 로드 대기
                
                info_title = driver.find_element(By.CLASS_NAME, 'PYvSYb').text if driver.find_elements(By.CLASS_NAME, 'PYvSYb') else ""            
                operation_time = driver.find_element(By.XPATH, "//div[@data-section-id='hours']/div/div[1]").text if driver.find_elements(By.XPATH, "//div[@data-section-id='hours']/div/div[1]") else ""
                information = place.find_element(By.CLASS_NAME, 'rogA2c ITvuef').text if place.find_elements(By.CLASS_NAME, 'rogA2c ITvuef') else ""
                
                all_results.append({
                    'nation': country,  # 국가 추가
                    'region': city,  # 도시 이름 추가
                    'name': name,
                    'operationTime': operation_time,
                    'expense': expense,
                    'infoTitle': info_title,
                    'infoContent': info_content,
                    'information': information,
                    'map_url': map_url,
                    'popularity': popularity,  # 열 이름 변경
                    'rating': rating,
                })
                
                driver.back()
                time.sleep(3)
            except Exception as e:
                print(f"Error occurred: {e}")
                continue

    # 모든 결과를 DataFrame으로 변환
    df = pd.DataFrame(all_results)

    # 열 이름 확인
    print(df.columns)

    # 'Popularity' 열이 존재하는지 확인하고 없으면 예외 처리
    if 'popularity' not in df.columns:
        print("Error: 'popularity' column not found in the DataFrame.")
        df['popularity'] = 0  # 기본값 0으로 'popularity' 열 추가

    # 리뷰 수 기준으로 내림차순 정렬
    df = df.sort_values(by='popularity', ascending=False)

    # data id_info 번호 부여
    df.insert(0, 'data id_info', range(1, len(df) + 1))

    # 열 이름을 재정렬 (실제 열 이름 확인 후 필요 시 수정)
    required_columns = ['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'popularity', 'rating']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''  # 없는 열은 빈 값으로 채움

    # 결과 출력 (포맷에 맞게 재정렬)
    df = df[required_columns]

    # 도시별 CSV 파일로 저장
    df.to_csv(f'{city}_travel_places_sele.csv', index=False, encoding='utf-8-sig')

# 포맷 정보 저장
format_info = {
    'class(kr)': ['data id_info', '국가', '지역', '이름', '영업시간', '가격', '여행지 정보(간략)', '여행지 정보(상세)', '문의처', '구글지도 링크', '인기', '평점'],
    'class(en)': ['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'popularity', 'rating'],
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
