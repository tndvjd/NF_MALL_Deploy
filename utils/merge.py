import pandas as pd
import numpy as np

def merge_files(product_db_df, template_df):
    """상품DB와 양식 파일을 병합하는 함수"""
    try:
        # 1단계: 기본 병합
        # 빈 데이터프레임 생성 (template의 모든 컬럼 포함)
        result_df = pd.DataFrame(columns=template_df.columns)
        
        # product_db의 데이터 복사
        for col in product_db_df.columns:
            if col in result_df.columns:
                result_df[col] = product_db_df[col]
        
        # 인덱스 재설정
        result_df = result_df.reindex(range(len(product_db_df)))
        
        # 2단계: 양식 재검사 및 적용
        # template의 첫 행을 기준으로 모든 컬럼의 형식 확인
        template_row = template_df.iloc[0]
        for col in template_df.columns:
            if col not in result_df.columns:
                result_df[col] = template_row[col]
            elif result_df[col].isna().all():  # 컬럼이 모두 비어있는 경우
                result_df[col] = template_row[col]
        
        # 3단계: 필수 값 설정
        # 빈 값으로 설정할 컬럼들
        empty_columns = [
            "상품코드", "모바일 상품 상세설명 설정", "원산지",
            "상품배송유형 코드", "검색엔진최적화(SEO) 검색엔진 노출 설정", 
            "배송비입력", "스토어픽업 설정", "배송비 구분", "배송기간", 
            "배송방법", "국내/해외배송", "추가입력옵션", "옵션 표시방식"
        ]
        for col in empty_columns:
            if col in result_df.columns:
                result_df[col] = ''

        # 특정 값으로 통일할 컬럼들
        value_mappings = {
            "과세구분": "B",
            "품목 구성방식": "F",
            "배송정보": "F",
            "필수여부": "T",
            "유효기간 사용여부": "N",
            "배송지역": "서울/경기",
            "진열상태": "Y",
            "판매상태": "Y",
            "상품분류 추천상품영역": "N,N",
            "상품 전체중량(kg)": "1",
            "판매가 대체문구 사용": "N",
            "최소 주문수량(이상)": "1",
            "적립금": "10",
            "적립금 구분": "P",
            "공통이벤트 정보": "Y",
            "성인인증": "N",
            "옵션사용": "Y"
        }
        for col, value in value_mappings.items():
            if col in result_df.columns:
                result_df[col] = value

        # 4단계: 이미지 처리
        image_columns = ["이미지등록(목록)", "이미지등록(작은목록)", "이미지등록(축소)"]
        if "이미지등록(상세)" in result_df.columns:
            detail_image = result_df["이미지등록(상세)"]
            for col in image_columns:
                if col in result_df.columns:
                    result_df[col] = detail_image.where(detail_image.notna(), result_df[col])
        
        # 5단계: 최종 정리
        # NaN 값을 빈 문자열로 변환
        result_df = result_df.replace({np.nan: ''})
        
        # 컬럼 순서를 template와 동일하게 맞추기
        result_df = result_df.reindex(columns=template_df.columns)
        
        return result_df
        
    except Exception as e:
        print(f"병합 중 오류 발생: {str(e)}")
        return None 