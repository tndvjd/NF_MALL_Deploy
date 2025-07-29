"""
병렬 번역 처리 모듈
"""
import asyncio
import streamlit as st
from typing import List, Dict, Tuple
import pandas as pd
from utils.translate_simplified import translate_batch_async_with_deepl
from utils.option_translate import translate_option_column_batch

class ParallelTranslationManager:
    """병렬 번역 관리자"""
    
    def __init__(self, api_key: str, batch_size: int = 5):
        self.api_key = api_key
        self.batch_size = batch_size
    
    async def translate_product_and_options_parallel(self, df: pd.DataFrame) -> pd.DataFrame:
        """상품명과 옵션을 병렬로 번역"""
        
        # 번역할 컬럼들 식별
        product_column = "상품명" if "상품명" in df.columns else None
        option_columns = [col for col in df.columns if '옵션입력' in col]
        
        if not product_column and not option_columns:
            st.warning("번역할 컬럼이 없습니다.")
            return df
        
        # 병렬 작업 준비
        tasks = []
        task_info = []
        
        # 상품명 번역 태스크
        if product_column:
            product_texts = df[product_column].fillna("").astype(str).tolist()
            task = translate_batch_async_with_deepl(
                product_texts, self.api_key, batch_size=self.batch_size
            )
            tasks.append(task)
            task_info.append(("product", product_column))
        
        # 옵션 번역 태스크들
        for col in option_columns:
            task = translate_option_column_batch(
                df, col, self.api_key, batch_size=self.batch_size, use_async=True
            )
            tasks.append(task)
            task_info.append(("option", col))
        
        # 병렬 실행
        st.info(f"🚀 병렬 번역 시작: {len(tasks)}개 작업")
        
        try:
            results = await asyncio.gather(*tasks)
            
            # 결과 적용
            df_result = df.copy()
            for i, (task_type, column) in enumerate(task_info):
                if task_type == "product":
                    df_result[column] = results[i]
                elif task_type == "option":
                    df_result[column] = results[i]
            
            st.success(f"✅ 병렬 번역 완료: {len(tasks)}개 작업")
            return df_result
            
        except Exception as e:
            st.error(f"병렬 번역 중 오류: {str(e)}")
            return df
    
    async def translate_multiple_option_columns_parallel(self, df: pd.DataFrame, 
                                                       option_columns: List[str]) -> pd.DataFrame:
        """여러 옵션 컬럼을 병렬로 번역"""
        
        if not option_columns:
            return df
        
        # 각 컬럼별 번역 태스크 생성
        tasks = []
        for col in option_columns:
            task = translate_option_column_batch(
                df, col, self.api_key, batch_size=self.batch_size, use_async=True
            )
            tasks.append(task)
        
        st.info(f"🔄 옵션 컬럼 병렬 번역: {len(option_columns)}개 컬럼")
        
        try:
            # 병렬 실행
            results = await asyncio.gather(*tasks)
            
            # 결과 적용
            df_result = df.copy()
            for i, col in enumerate(option_columns):
                df_result[col] = results[i]
            
            return df_result
            
        except Exception as e:
            st.error(f"옵션 병렬 번역 중 오류: {str(e)}")
            return df

def estimate_translation_time(text_count: int, batch_size: int = 5) -> Dict[str, float]:
    """번역 소요 시간 추정"""
    
    # 경험적 수치 (초 단위)
    api_call_time = 3.0  # API 호출당 평균 시간
    batch_delay = 2.0    # 배치 간 대기 시간
    
    total_batches = (text_count + batch_size - 1) // batch_size
    estimated_time = (total_batches * api_call_time) + ((total_batches - 1) * batch_delay)
    
    return {
        'total_texts': text_count,
        'total_batches': total_batches,
        'estimated_seconds': estimated_time,
        'estimated_minutes': estimated_time / 60,
        'batch_size': batch_size
    }

def estimate_api_usage(text_count: int, avg_chars_per_text: int = 20) -> Dict[str, int]:
    """API 사용량 추정"""
    
    total_chars = text_count * avg_chars_per_text
    
    return {
        'total_texts': text_count,
        'avg_chars_per_text': avg_chars_per_text,
        'estimated_total_chars': total_chars,
        'deepl_free_limit': 500000,  # 50만자
        'usage_percentage': (total_chars / 500000) * 100
    }