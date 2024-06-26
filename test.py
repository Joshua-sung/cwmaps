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

# 도시와 국가 정보
city = "Tokyo"
country = "Japan"

# 카테고리 목록 (영어로 변경)
categories = {
    'Historic site': f'{city} Historic site',
    'Theme Park': f'{city} Theme Park',
    'Activity': f'{city} Activity',
    'Natural Scenery': f'{city} Natural Scenery',
    'Things to do': f'{city} Things to do',
    'Museums': f'{city} Museums',
    'Night View': f'{city} Night View',
    'Nature Reserve': f'{city} Nature Reserve',
    'Zoo': f'{city} Zoo',
    'Theme Tour': f'{city} Theme Tour',
    'Monument': f'{city} Monument',
    'Art Gallery': f'{city} Art Gallery',
    'Museum of Art': f'{city} Museum of Art'
}

# 모든 결과를 저장할 리스트
all_results = []

# 중복 URL을 확인하기 위한 집합
unique_urls = set()

# 고유 번호를 위한 초기값
id_counter = 1

def scroll_to_load_more(driver, scroll_pause_time=2, max_scrolls=5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0

    while scroll_attempts < max_scrolls:
        scroll_attempts += 1
        scroll_panel = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]')
        driver.execute_script('arguments[0].scrollBy(0, 5000);', scroll_panel)
        time.sleep(scroll_pause_time)

        new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_panel)
        if new_height == last_height:
            break
        last_height = new_height

def get_places(driver, min_places=20):
    places = driver.find_elements(By.CLASS_NAME, 'Nv2PK')
    scroll_attempts = 0
    while len(places) < min_places and scroll_attempts < 5:
        scroll_to_load_more(driver)
        places = driver.find_elements(By.CLASS_NAME, 'Nv2PK')
        scroll_attempts += 1
    return places

# 각 카테고리에 대해 데이터 추출
for category, query in categories.items():
    # Google Maps 접속
    maps_url = f"https://www.google.com/maps/place/{city},+{country}/"
    driver.get(maps_url)
    
    # 페이지 로드 대기
    wait = WebDriverWait(driver, 5)
    search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
    
    # 검색창에 카테고리 검색어 입력
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    
    # 페이지 로드 대기
    time.sleep(5)
    
    # 여행지 정보 추출
    places = get_places(driver)

    for place in places:
        try:
            # 기본 정보 추출
            name = place.find_element(By.CLASS_NAME, 'qBF1Pd').text
            try:
                rating = place.find_element(By.CLASS_NAME, 'MW4etd').text
            except:
                rating = '0'  # 평점이 없는 경우 기본값 설정
            map_url = place.find_element(By.TAG_NAME, 'a').get_attribute('href')
            if map_url in unique_urls:
                continue  # 이미 처리된 URL은 무시
            
            unique_urls.add(map_url)
            
            try:
                reviews = place.find_element(By.CLASS_NAME, 'UY7F9').text
            except:
                reviews = '0'  # 리뷰가 없는 경우 기본값 설정

            try:
                info_title =driver.find_element(By.XPATH,'//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]/div[3]/div/div[2]/div[4]/div[1]/div/div/div[2]/div[4]/div[1]/span[1]').text
            except:
                info_title = None
            
            info_content = None
            expense = None

            # 상세 페이지로 이동하여 추가 정보 추출
            place.find_element(By.TAG_NAME, 'a').click()
            time.sleep(3)  # 페이지 로드 대기
            
            try:
                operation_time = driver.find_element(By.XPATH, "//div[@data-section-id='hours']/div/div[1]").text
            except:
                operation_time = None
   
            
            try:  
                information = place.find_element(By.CLASS_NAME, 'Io6YTe fontBodyMedium kR99db ').text
            except:
                information = None
            
            all_results.append({
                'data id_info': id_counter,
                'nation': country,  # 국가 추가
                'region': city,  # 도시 이름 추가
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

# 열 이름 확인
print(df.columns)

# 열 이름을 재정렬 (실제 열 이름 확인 후 필요 시 수정)
required_columns = ['data id_info', 'nation', 'region', 'name', 'operationTime', 'expense', 'infoTitle', 'infoContent', 'information', 'map_url', 'rating', 'reviews']
for col in required_columns:
    if col not in df.columns:
        df[col] = ''  # 없는 열은 빈 값으로 채움

# 결과 출력 (포맷에 맞게 재정렬)
df = df[required_columns]

# CSV 파일로 저장
df.to_csv(f'{city}_travel_places.csv', index=False, encoding='utf-8-sig')

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
