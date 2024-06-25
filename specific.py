# 필요한 패키지 임포트
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")   
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# options.add_argument('--blink-settings=imagesEnabled=false') #이미지 안보이게 하기

# ChromeDriver 설정 및 초기화
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Google Maps 상세 페이지 열기
driver.get('https://www.google.com/maps/place/MR+Kukrit+Pramoj+House/@13.749861,100.4890016,15z/data=!4m10!1m2!2m1!1z67Cp7L2VIGhpc3JvdGljIHNpdGU!3m6!1s0x30e29f324b498891:0x1d05a92888b79876!8m2!3d13.7203062!4d100.5335999!15sChTrsKnsvZUgaGlzdG9yaWMgc2l0ZVoWIhTrsKnsvZUgaGlzdG9yaWMgc2l0ZZIBF2hpc3RvcmljYWxfcGxhY2VfbXVzZXVtmgEjQ2haRFNVaE5NRzluUzBWSlEwRm5TVU5qYW1OTFRFSjNFQUXgAQA!16s%2Fm%2F043mdbd?entry=ttu')

# 페이지가 로드될 때까지 대기
time.sleep(5)

# 정보 추출
try:
    name = driver.find_element(By.CLASS_NAME, 'qBF1Pd').text
except:
    name = None

try:
    rating = driver.find_element(By.CLASS_NAME, 'MW4etd').text
except:
    rating = '0'  # 평점이 없는 경우 기본값 설정

try:
    reviews = driver.find_element(By.CLASS_NAME, 'UY7F9').text
except:
    reviews = '0'  # 리뷰가 없는 경우 기본값 설정

try:
    category = driver.find_element(By.CLASS_NAME, 'DkEaL').text
except:
    category = None

try:
    hours = driver.find_element(By.CLASS_NAME, 'f5Mkv').text
except:
    hours = None

try:
    website_element = driver.find_element(By.XPATH, '//a[@data-item-id="authority"]')
    website = website_element.get_attribute('href')
except:
    website = None

try:
    phone_element = driver.find_element(By.XPATH, '//button[@data-item-id="phone"]')
    phone = phone_element.get_attribute('aria-label')
except:
    phone = None

# 브라우저 닫기
driver.quit()

# 결과를 CSV 파일로 저장
csv_file_path = 'place_details.csv'
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['name', 'rating', 'reviews', 'category', 'hours', 'website', 'phone'])
    writer.writeheader()
    writer.writerow({
        'name': name,
        'rating': rating,
        'reviews': reviews,
        'category': category,
        'hours': hours,
        'website': website,
        'phone': phone
    })

print(f"Data has been saved to {csv_file_path}")
