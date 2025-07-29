import pandas as pd
import streamlit as st
from typing import List, Dict, Optional, Tuple
import os
from pathlib import Path

class DataValidator:
    """데이터 검증 클래스"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_excel_file(self, file_path: str) -> bool:
        """Excel 파일 기본 검증"""
        try:
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                self.errors.append(f"파일이 존재하지 않습니다: {file_path}")
                return False
            
            # 파일 확장자 확인
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                self.errors.append(f"지원하지 않는 파일 형식입니다. Excel 파일(.xlsx, .xls)만 지원합니다.")
                return False
            
            # 파일 크기 확인 (100MB 제한)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            if file_size > 100:
                self.warnings.append(f"파일 크기가 큽니다 ({file_size:.1f}MB). 처리 시간이 오래 걸릴 수 있습니다.")
            
            return True
            
        except Exception as e:
            self.errors.append(f"파일 검증 중 오류 발생: {str(e)}")
            return False
    
    def validate_dataframe_structure(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """데이터프레임 구조 검증"""
        try:
            # 빈 데이터프레임 확인
            if df.empty:
                self.errors.append("데이터가 비어있습니다.")
                return False
            
            # 필수 컬럼 존재 여부 확인
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.errors.append(f"필수 컬럼이 없습니다: {', '.join(missing_columns)}")
                return False
            
            # 데이터 행 수 확인
            if len(df) > 50000:
                self.warnings.append(f"데이터 행 수가 많습니다 ({len(df):,}행). 청크 처리를 권장합니다.")
            
            return True
            
        except Exception as e:
            self.errors.append(f"데이터 구조 검증 중 오류 발생: {str(e)}")
            return False
    
    def validate_price_data(self, df: pd.DataFrame, price_columns: List[str] = None) -> 'DataValidator':
        """가격 데이터 검증"""
        validator = DataValidator()
        
        try:
            if price_columns is None:
                price_columns = ['소비자가']
            
            for col in price_columns:
                if col not in df.columns:
                    continue  # 가격 컬럼이 없으면 검증 생략
                
                # 가격 데이터 타입 확인
                price_column = df[col]
                
                # 숫자가 아닌 값 확인
                non_numeric = price_column[pd.to_numeric(price_column, errors='coerce').isna()]
                if not non_numeric.empty:
                    validator.warnings.append(f"{col}: 숫자가 아닌 가격 데이터가 {len(non_numeric)}개 있습니다.")
                
                # 음수 또는 0 값 확인
                numeric_prices = pd.to_numeric(price_column, errors='coerce')
                invalid_prices = numeric_prices[numeric_prices <= 0]
                if not invalid_prices.empty:
                    validator.warnings.append(f"{col}: 유효하지 않은 가격 데이터가 {len(invalid_prices)}개 있습니다 (0 이하).")
                
                # 비정상적으로 높은 가격 확인 (1억원 이상)
                high_prices = numeric_prices[numeric_prices > 100000000]
                if not high_prices.empty:
                    validator.warnings.append(f"{col}: 비정상적으로 높은 가격이 {len(high_prices)}개 있습니다 (1억원 이상).")
            
            validator.is_valid = len(validator.errors) == 0
            return validator
            
        except Exception as e:
            validator.errors.append(f"가격 데이터 검증 중 오류 발생: {str(e)}")
            validator.is_valid = False
            return validator
    
    def validate_translation_data(self, df: pd.DataFrame, target_column: str) -> bool:
        """번역 대상 데이터 검증"""
        try:
            if target_column not in df.columns:
                self.errors.append(f"번역 대상 컬럼이 없습니다: {target_column}")
                return False
            
            # 빈 값 확인
            empty_values = df[target_column].isna() | (df[target_column] == '')
            if empty_values.sum() > 0:
                self.warnings.append(f"빈 값이 {empty_values.sum()}개 있습니다. 번역에서 제외됩니다.")
            
            # 번역할 텍스트 길이 확인
            text_lengths = df[target_column].astype(str).str.len()
            long_texts = text_lengths[text_lengths > 500]
            if not long_texts.empty:
                self.warnings.append(f"긴 텍스트가 {len(long_texts)}개 있습니다 (500자 이상). 번역 비용이 높을 수 있습니다.")
            
            return True
            
        except Exception as e:
            self.errors.append(f"번역 데이터 검증 중 오류 발생: {str(e)}")
            return False
    
    def validate_api_key(self, api_key: str, api_type: str = "DeepL") -> 'DataValidator':
        """API 키 검증"""
        validator = DataValidator()
        
        try:
            if not api_key or api_key.strip() == "":
                validator.errors.append(f"{api_type} API 키가 입력되지 않았습니다.")
                validator.is_valid = False
                return validator
            
            # DeepL API 키 형식 확인 (기본적인 형식 검증)
            if api_type == "DeepL":
                if not api_key.endswith(":fx"):
                    validator.warnings.append("DeepL API 키 형식이 일반적이지 않습니다. 무료 계정 키는 ':fx'로 끝납니다.")
            
            validator.is_valid = len(validator.errors) == 0
            return validator
            
        except Exception as e:
            validator.errors.append(f"API 키 검증 중 오류 발생: {str(e)}")
            validator.is_valid = False
            return validator
    
    def get_validation_summary(self) -> Dict[str, List[str]]:
        """검증 결과 요약 반환"""
        return {
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def display_validation_results(self):
        """Streamlit에서 검증 결과 표시"""
        if self.errors:
            st.error("❌ 오류가 발견되었습니다:")
            for error in self.errors:
                st.error(f"• {error}")
        
        if self.warnings:
            st.warning("⚠️ 주의사항:")
            for warning in self.warnings:
                st.warning(f"• {warning}")
        
        if not self.errors and not self.warnings:
            st.success("✅ 모든 검증을 통과했습니다!")
    
    def clear_results(self):
        """검증 결과 초기화"""
        self.errors.clear()
        self.warnings.clear()

def validate_file_upload(uploaded_file, required_columns: List[str]) -> Tuple[bool, pd.DataFrame, DataValidator]:
    """파일 업로드 통합 검증 함수"""
    validator = DataValidator()
    
    try:
        # 파일이 업로드되었는지 확인
        if uploaded_file is None:
            validator.errors.append("파일이 업로드되지 않았습니다.")
            return False, pd.DataFrame(), validator
        
        # 임시 파일로 저장하여 검증
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 파일 검증
        if not validator.validate_excel_file(temp_path):
            os.remove(temp_path)
            return False, pd.DataFrame(), validator
        
        # 데이터 읽기
        df = pd.read_excel(temp_path)
        os.remove(temp_path)
        
        # 데이터 구조 검증
        if not validator.validate_dataframe_structure(df, required_columns):
            return False, df, validator
        
        return True, df, validator
        
    except Exception as e:
        validator.errors.append(f"파일 처리 중 오류 발생: {str(e)}")
        return False, pd.DataFrame(), validator

# 각 기능별 필수 컬럼 정의
REQUIRED_COLUMNS = {
    'merge': ['상품명'],
    'price': ['소비자가'],
    'category': ['카테고리'],
    'option': ['옵션'],
    'translate': ['상품명']
}

def get_required_columns(feature: str) -> List[str]:
    """기능별 필수 컬럼 반환"""
    return REQUIRED_COLUMNS.get(feature, [])

def display_validation_results(validators: List[DataValidator]):
    """여러 검증 결과를 Streamlit에서 표시"""
    all_errors = []
    all_warnings = []
    
    for validator in validators:
        all_errors.extend(validator.errors)
        all_warnings.extend(validator.warnings)
    
    if all_errors:
        st.error("❌ 오류가 발견되었습니다:")
        for error in all_errors:
            st.error(f"• {error}")
    
    if all_warnings:
        st.warning("⚠️ 주의사항:")
        for warning in all_warnings:
            st.warning(f"• {warning}")
    
    if not all_errors and not all_warnings:
        st.success("✅ 모든 검증을 통과했습니다!")