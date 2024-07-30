import pandas as pd
import os
import re

# 도시 이름 설정
city = "Guilin"

# 현재 파일의 위치를 기준으로 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
travel_places_path = os.path.join(current_dir, f'{city}_travel_places_sele.csv')
cash_places_path = os.path.join(current_dir, f'{city}_travel_places_api.csv')
output_path = os.path.join(current_dir, f'{city}_combined_places.csv')

# CSV 파일 불러오기
cash_places = pd.read_csv(cash_places_path)
travel_places = pd.read_csv(travel_places_path)

# 데이터프레임 결합 및 중복 제거
combined_df = pd.concat([cash_places, travel_places], ignore_index=True)
combined_df = combined_df.drop_duplicates(subset=['name'], keep='first')

# 제외할 단어 리스트
exclude_keywords = ['hotel', 'resort', 'pub','Club', 'bar', 'Conrad','Hyatt', 'Railway Ticket', 'The Westin', 'Ritz Carlton', 'Railway Station', 'inn', 'Hilton', '인터콘티넨탈', '콘레드',  '호텔', '공항', '하얏트', '역', '호스텔', '힐튼', 'tours', '료칸', '홀리데이 인', '국제공항', '리조트', 'Night club']

# 정규 표현식을 사용하여 이름 필터링
def should_exclude(name):
    for keyword in exclude_keywords:
        if re.search(rf'\b{keyword}\b', name, re.IGNORECASE) or re.search(rf'\b{keyword}$', name, re.IGNORECASE):
            return True
    return False

# 필터링 적용
filtered_df = combined_df[~combined_df['name'].apply(should_exclude)]

# 'Popularity' 열 기준으로 내림차순 정렬
filtered_df = filtered_df.sort_values(by='popularity', ascending=False).reset_index(drop=True)
filtered_df['data id_info'] = filtered_df.index + 1

# 필요한 열 순서로 재정렬
final_df = filtered_df[['data id_info'] + [col for col in filtered_df.columns if col != 'data id_info']]

# 결과를 CSV 파일로 저장
final_df.to_csv(output_path, index=False)

print(f"Combined unique places saved to {output_path}")
