import pandas as pd
import streamlit as st
from typing import Iterator, Callable, Any, Optional, Dict, List
import time
from functools import wraps
import gc

class ChunkProcessor:
    """청크 단위 데이터 처리 클래스"""
    
    def __init__(self, chunk_size: int = 1000, show_progress: bool = True):
        self.chunk_size = chunk_size
        self.show_progress = show_progress
        self.processed_chunks = 0
        self.total_chunks = 0
        self.start_time = None
    
    def process_dataframe_in_chunks(
        self, 
        df: pd.DataFrame, 
        process_func: Callable[[pd.DataFrame], pd.DataFrame],
        **kwargs
    ) -> pd.DataFrame:
        """데이터프레임을 청크 단위로 처리"""
        
        if len(df) <= self.chunk_size:
            # 작은 데이터는 청크 처리 없이 바로 처리
            return process_func(df, **kwargs)
        
        self.total_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size
        self.processed_chunks = 0
        self.start_time = time.time()
        
        processed_chunks = []
        
        # Streamlit 진행률 표시
        if self.show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_text = st.empty()
        
        try:
            for i in range(0, len(df), self.chunk_size):
                chunk = df.iloc[i:i + self.chunk_size].copy()
                
                # 청크 처리
                processed_chunk = process_func(chunk, **kwargs)
                processed_chunks.append(processed_chunk)
                
                self.processed_chunks += 1
                
                # 진행률 업데이트
                if self.show_progress:
                    progress = self.processed_chunks / self.total_chunks
                    progress_bar.progress(progress)
                    
                    # 상태 텍스트 업데이트
                    status_text.text(
                        f"처리 중: {self.processed_chunks:,}/{self.total_chunks:,} 청크 "
                        f"({i + len(chunk):,}/{len(df):,} 행)"
                    )
                    
                    # 예상 완료 시간 계산
                    if self.processed_chunks > 1:
                        elapsed_time = time.time() - self.start_time
                        avg_time_per_chunk = elapsed_time / self.processed_chunks
                        remaining_chunks = self.total_chunks - self.processed_chunks
                        estimated_remaining = avg_time_per_chunk * remaining_chunks
                        
                        time_text.text(
                            f"경과 시간: {elapsed_time:.1f}초, "
                            f"예상 완료: {estimated_remaining:.1f}초 후"
                        )
                
                # 메모리 정리
                del chunk
                if i % (self.chunk_size * 5) == 0:  # 5청크마다 가비지 컬렉션
                    gc.collect()
            
            # 결과 합치기
            result_df = pd.concat(processed_chunks, ignore_index=True)
            
            if self.show_progress:
                progress_bar.progress(1.0)
                total_time = time.time() - self.start_time
                status_text.text(f"✅ 완료: {len(df):,}행 처리 완료 ({total_time:.1f}초)")
                time_text.empty()
            
            return result_df
            
        except Exception as e:
            if self.show_progress:
                st.error(f"청크 처리 중 오류 발생: {str(e)}")
            raise e
        
        finally:
            # 메모리 정리
            del processed_chunks
            gc.collect()
    
    def process_file_in_chunks(
        self,
        file_path: str,
        process_func: Callable[[pd.DataFrame], pd.DataFrame],
        output_path: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """파일을 청크 단위로 읽어서 처리"""
        
        try:
            # 파일 크기 확인
            file_size = pd.read_excel(file_path, nrows=0).shape[0]  # 헤더만 읽어서 구조 확인
            
            if self.show_progress:
                st.info(f"📁 파일 청크 처리 시작: {file_path}")
            
            processed_chunks = []
            chunk_reader = pd.read_excel(file_path, chunksize=self.chunk_size)
            
            self.processed_chunks = 0
            self.start_time = time.time()
            
            # 진행률 표시 준비
            if self.show_progress:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            for chunk_num, chunk in enumerate(chunk_reader):
                # 청크 처리
                processed_chunk = process_func(chunk, **kwargs)
                processed_chunks.append(processed_chunk)
                
                self.processed_chunks += 1
                
                # 진행률 업데이트 (정확한 총 청크 수를 모르므로 근사치 사용)
                if self.show_progress:
                    status_text.text(
                        f"처리 중: {self.processed_chunks}번째 청크 "
                        f"({len(chunk):,}행 처리)"
                    )
                
                # 메모리 정리
                del chunk
                if chunk_num % 5 == 0:
                    gc.collect()
            
            # 결과 합치기
            result_df = pd.concat(processed_chunks, ignore_index=True)
            
            if self.show_progress:
                total_time = time.time() - self.start_time
                status_text.text(f"✅ 파일 처리 완료: {len(result_df):,}행 ({total_time:.1f}초)")
            
            # 결과 저장 (선택사항)
            if output_path:
                result_df.to_excel(output_path, index=False)
                if self.show_progress:
                    st.success(f"💾 결과 저장 완료: {output_path}")
            
            return result_df
            
        except Exception as e:
            if self.show_progress:
                st.error(f"파일 청크 처리 중 오류 발생: {str(e)}")
            raise e
        
        finally:
            del processed_chunks
            gc.collect()
    
    def split_dataframe_into_chunks(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """데이터프레임을 청크 단위로 분할"""
        chunks = []
        
        for i in range(0, len(df), self.chunk_size):
            chunk = df.iloc[i:i + self.chunk_size].copy()
            chunks.append(chunk)
        
        return chunks

def chunk_processing_decorator(chunk_size: int = 1000, show_progress: bool = True):
    """청크 처리 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(df: pd.DataFrame, *args, **kwargs):
            # 청크 처리가 필요한지 확인
            if len(df) <= chunk_size:
                return func(df, *args, **kwargs)
            
            # 청크 처리 실행
            processor = ChunkProcessor(chunk_size=chunk_size, show_progress=show_progress)
            return processor.process_dataframe_in_chunks(df, func, *args, **kwargs)
        
        return wrapper
    return decorator

def estimate_processing_time(df: pd.DataFrame, sample_size: int = 100) -> Dict[str, float]:
    """처리 시간 예상"""
    if len(df) <= sample_size:
        return {'estimated_time': 0, 'sample_time': 0, 'scaling_factor': 1}
    
    # 샘플 데이터로 처리 시간 측정
    sample_df = df.head(sample_size).copy()
    
    start_time = time.time()
    # 간단한 처리 작업 (예: 데이터 복사)
    _ = sample_df.copy()
    sample_time = time.time() - start_time
    
    # 전체 데이터 처리 시간 예상
    scaling_factor = len(df) / sample_size
    estimated_time = sample_time * scaling_factor
    
    return {
        'estimated_time': estimated_time,
        'sample_time': sample_time,
        'scaling_factor': scaling_factor
    }

def recommend_chunk_size(df: pd.DataFrame, target_memory_mb: float = 50) -> int:
    """적절한 청크 크기 추천"""
    # 데이터프레임 메모리 사용량 추정
    memory_per_row = df.memory_usage(deep=True).sum() / len(df) / (1024 * 1024)  # MB per row
    
    # 목표 메모리 사용량에 맞는 청크 크기 계산
    recommended_size = int(target_memory_mb / memory_per_row)
    
    # 최소 100행, 최대 10000행으로 제한
    recommended_size = max(100, min(10000, recommended_size))
    
    return recommended_size

def display_chunk_info(df: pd.DataFrame, chunk_size: int):
    """청크 처리 정보 표시"""
    total_chunks = (len(df) + chunk_size - 1) // chunk_size
    memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
    
    st.info(
        f"📊 청크 처리 정보:\n"
        f"• 전체 데이터: {len(df):,}행\n"
        f"• 청크 크기: {chunk_size:,}행\n"
        f"• 총 청크 수: {total_chunks:,}개\n"
        f"• 메모리 사용량: {memory_usage:.1f}MB"
    )
    
    # 처리 시간 예상
    time_estimate = estimate_processing_time(df)
    if time_estimate['estimated_time'] > 0:
        st.info(
            f"⏱️ 예상 처리 시간: {time_estimate['estimated_time']:.1f}초"
        )

# 청크 처리를 위한 유틸리티 함수들
def safe_chunk_processing(func):
    """안전한 청크 처리를 위한 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MemoryError:
            st.error("❌ 메모리 부족으로 처리를 중단했습니다. 청크 크기를 줄여주세요.")
            raise
        except Exception as e:
            st.error(f"❌ 처리 중 오류 발생: {str(e)}")
            raise
    return wrapper