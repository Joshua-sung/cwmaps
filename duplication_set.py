import pandas as pd
import os

# 도시 이름 설정
city = "Dalian"

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

# 'Popularity' 열 기준으로 내림차순 정렬
combined_df = combined_df.sort_values(by='Popularity', ascending=False).reset_index(drop=True)
combined_df['data id_info'] = combined_df.index + 1

# 필요한 열 순서로 재정렬
final_df = combined_df[['data id_info'] + [col for col in combined_df.columns if col != 'data id_info']]

# 결과를 CSV 파일로 저장
final_df.to_csv(output_path, index=False)

print(f"Combined unique places saved to {output_path}")
