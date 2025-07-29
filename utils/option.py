import pandas as pd
from .option_translate import translate_option_colors, is_option_format

def convert_option_format(value):
    """옵션 형식을 변환하는 함수"""
    if pd.isna(value):
        return value
    # 문자열이 아닌 경우 문자열로 변환
    value = str(value)
    # 이미 변환된 형식인 경우 건너뛰기
    if value.startswith('색상{') and value.endswith('}'):
        return value
    # 콤마나 파이프로 구분된 옵션들을 분리하고 공백 제거
    if '|' in value:
        options = [opt.strip() for opt in value.split('|')]
    else:
        options = [opt.strip() for opt in value.split(',')]
    # 중복 제거 및 빈 문자열 제거
    options = list(filter(None, dict.fromkeys(options)))
    # 새로운 형식으로 변환
    return '색상{' + '|'.join(options) + '}'

def translate_option_column(df, column_name, api_key, target_lang='JA'):
    """
    데이터프레임의 옵션 컬럼을 번역하는 함수
    
    Args:
        df: 데이터프레임
        column_name: 번역할 옵션 컬럼명
        api_key: DeepL API 키
        target_lang: 번역 대상 언어
    
    Returns:
        번역된 데이터프레임
    """
    if column_name not in df.columns:
        print(f"컬럼을 찾을 수 없습니다: {column_name}")
        return df
    
    # 복사본 생성
    result_df = df.copy()
    
    # 옵션 형식인 행들만 필터링
    option_mask = result_df[column_name].apply(lambda x: is_option_format(str(x)) if pd.notna(x) else False)
    option_rows = result_df[option_mask]
    
    if len(option_rows) == 0:
        print(f"번역할 옵션 형식 데이터가 없습니다: {column_name}")
        return result_df
    
    print(f"번역할 옵션 데이터 {len(option_rows)}개 발견")
    
    # 옵션 번역 수행
    translated_options = []
    for idx, row in option_rows.iterrows():
        original_option = str(row[column_name])
        translated_option = translate_option_colors(original_option, api_key, target_lang)
        translated_options.append((idx, translated_option))
    
    # 번역 결과를 데이터프레임에 적용
    for idx, translated_option in translated_options:
        result_df.at[idx, column_name] = translated_option
    
    print(f"옵션 번역 완료: {len(translated_options)}개")
    return result_df