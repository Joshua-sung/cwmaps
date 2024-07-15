import pandas as pd
import os

# 현재 스크립트의 경로를 기준으로 파일 경로 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
transformed_file_path = os.path.join(script_dir, 'transformed_data.csv')  # 변환된 입력 CSV 파일 이름
output_file_path = os.path.join(script_dir, 'graded_data.csv')  # 채점된 결과를 저장할 CSV 파일 이름

# 정답 데이터 설정
answers = {
    1: [60, 20, 80, 100, 20, 20, 60, 20, 20, 40, 100, 100, 100, 20, 80],
    2: [20, 80, 60, 20, 100, 80, 20, 20, 100, 100, 100, 100, 100, 100, 100],
    3: [60, 20, 100, 80, 20, 20, 60, 20, 20, 20, 100, 100, 100, 40, 100]
}

# CSV 파일 로드
df = pd.read_csv(transformed_file_path, encoding='utf-8')

# 결측값을 0으로 대체
df.fillna(0, inplace=True)

# 정답 범위 설정 함수
def is_correct(response, correct_answer):
    if correct_answer == 20:
        return response in {20, 40}
    elif correct_answer == 40:
        return response in {20, 40, 60}
    elif correct_answer == 60:
        return response in {40, 60, 80}
    elif correct_answer == 80:
        return response in {60, 80, 100}
    elif correct_answer == 100:
        return response in {80, 100}
    return False

# 채점 함수 정의
def grade_responses(row):
    # data id를 정수로 변환
    data_id = int(float(row['data id']))
    if data_id not in answers:
        return 0
    correct_answers = answers[data_id]
    score = 0
    for i in range(15):
        col_name = f'선택항목 {i+1}'
        if col_name in row and pd.notna(row[col_name]):
            response = int(row[col_name])
            if is_correct(response, correct_answers[i]):
                score += 1
    return score

# 점수 계산 및 새로운 데이터프레임 생성
graded_data = []

for index, row in df.iterrows():
    score = grade_responses(row)
    graded_data.append({
        'Worker ID': row['Worker ID'],
        '작업자 닉네임': row['작업자 닉네임'],
        'data id': row['data id'],
        '점수': score
    })

graded_df = pd.DataFrame(graded_data)

# 새로운 CSV 파일로 저장
graded_df.to_csv(output_file_path, index=False, encoding='utf-8')

# 결과 출력
print("채점된 데이터가 'graded_data.csv' 파일로 저장되었습니다.")
