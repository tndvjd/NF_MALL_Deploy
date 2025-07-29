import numpy as np
import pandas as pd
from functools import wraps
import time

def measure_time(func):
    """함수 실행 시간을 측정하는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 실행 시간: {end-start:.4f}초")
        return result
    return wrapper

@measure_time
def calculate_prices(df, random_seed=42):
    """가격 정보를 처리하는 함수 (성능 최적화 버전)"""
    if '소비자가' not in df.columns:
        return df
    
    # 데이터 복사본 생성
    result_df = df.copy()
    
    # 1. 소비자가의 값을 공급가, 판매가로 적용 (벡터화 연산)
    result_df['공급가'] = result_df['소비자가']
    result_df['판매가'] = result_df['소비자가']
    
    # 2. 공급가에서 부가세를 제외한 금액을 상품가로 설정 (벡터화 연산)
    result_df['상품가'] = (result_df['공급가'] / 1.1).round().astype('int32')
    
    # 3. 재현 가능한 랜덤 마진 적용 (벡터화 연산)
    np.random.seed(random_seed)
    margin_rates = np.random.uniform(0.15, 0.30, len(result_df))
    result_df['소비자가'] = ((result_df['공급가'] * (1 + margin_rates)) // 100 * 100).astype('int32')
    
    return result_df

def calculate_prices_optimized(df, random_seed=42):
    """메모리 효율적인 가격 계산 함수"""
    if '소비자가' not in df.columns:
        return df
    
    # 필요한 컬럼만 처리하여 메모리 절약
    price_columns = ['소비자가', '공급가', '판매가', '상품가']
    
    # 소비자가 컬럼을 기준으로 계산
    consumer_price = df['소비자가'].astype('float32')  # 메모리 절약을 위해 float32 사용
    
    # 벡터화된 계산
    df['공급가'] = consumer_price.astype('int32')
    df['판매가'] = consumer_price.astype('int32')
    df['상품가'] = (consumer_price / 1.1).round().astype('int32')
    
    # 재현 가능한 랜덤 마진
    np.random.seed(random_seed)
    margin_rates = np.random.uniform(0.15, 0.30, len(df))
    df['소비자가'] = ((consumer_price * (1 + margin_rates)) // 100 * 100).astype('int32')
    
    return df