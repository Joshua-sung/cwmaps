import json
import os

def recover_json(file_path):
    """
    손상된 JSON 파일을 복구합니다.
    """
    recovered_data = {}
    try:
        with open(file_path, 'r') as file:
            # 한 줄씩 읽어가면서 유효한 JSON 객체를 추출
            for line in file:
                try:
                    data = json.loads(line.strip())
                    recovered_data.update(data)
                except json.JSONDecodeError:
                    # 유효하지 않은 JSON 객체를 무시
                    continue
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    
    return recovered_data

def save_recovered_json(data, output_file):
    """
    복구된 데이터를 JSON 파일로 저장합니다.
    """
    try:
        with open(output_file, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"Recovered data saved to {output_file}")
    except Exception as e:
        print(f"Error saving file {output_file}: {e}")

# 현재 스크립트의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))

# 손상된 JSON 파일 경로
place_id_cache_file = os.path.join(current_dir, 'place_id_cache.json')
place_details_cache_file = os.path.join(current_dir, 'place_details_cache.json')

# 복구된 데이터 저장 경로
recovered_place_id_cache_file = os.path.join(current_dir, 'recovered_place_id_cache.json')
recovered_place_details_cache_file = os.path.join(current_dir, 'recovered_place_details_cache.json')

# JSON 파일 복구
recovered_place_id_cache = recover_json(place_id_cache_file)
recovered_place_details_cache = recover_json(place_details_cache_file)

# 복구된 데이터 저장
save_recovered_json(recovered_place_id_cache, recovered_place_id_cache_file)
save_recovered_json(recovered_place_details_cache, recovered_place_details_cache_file)
