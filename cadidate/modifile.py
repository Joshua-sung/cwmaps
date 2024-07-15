import pandas as pd
import os

# 현재 스크립트의 경로를 기준으로 파일 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file_path = os.path.join(script_dir, 'input_data.csv')  # 입력 CSV 파일 이름
output_file_path = os.path.join(script_dir, 'transformed_data.csv')  # 출력 CSV 파일 이름

# CSV 파일 로드
df = pd.read_csv(input_file_path, encoding='utf-8')

# 필요한 칼럼만 남기기
df = df[['Worker ID', '작업자 닉네임', 'data id', '선택항목 1', '선택항목 2']]

# 결측값을 빈 문자열로 대체
df['선택항목 1'] = df['선택항목 1'].fillna('')
df['선택항목 2'] = df['선택항목 2'].fillna('')

# 선택항목을 각각 분리하여 개별 컬럼으로 확장
expanded_data = []

for index, row in df.iterrows():
    선택항목1 = row['선택항목 1'].split('\n')
    선택항목2 = row['선택항목 2'].split('\n')
    all_choices = 선택항목1 + 선택항목2

    new_row = {
        'Worker ID': row['Worker ID'],
        '작업자 닉네임': row['작업자 닉네임'],
        'data id': row['data id']
    }

    for i, choice in enumerate(all_choices):
        new_row[f'선택항목 {i+1}'] = choice.strip()
    
    expanded_data.append(new_row)

# 새로운 데이터프레임 생성
expanded_df = pd.DataFrame(expanded_data)

# 새로운 CSV 파일로 저장
expanded_df.to_csv(output_file_path, index=False, encoding='utf-8')

# 결과 출력
print("변환된 데이터가 'transformed_data.csv' 파일로 저장되었습니다.")
