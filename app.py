import streamlit as st
import pandas as pd
import numpy as np
import io
import time
import gc
import asyncio
from utils import (
    analyze_product_names,
    convert_option_format,
    is_option_format,
    calculate_prices,
    calculate_prices_optimized,
    convert_categories,
    merge_files,
    preprocess_categories
)
from utils.translate_simplified import (
    translate_product_names,
    translate_option_column,
    translate_option_colors,
    analyze_colors_in_data,
    suggest_glossary_additions,
    export_color_analysis_to_excel
)
# from utils.validation import DataValidator, display_validation_results  # 제거됨
from utils.chunk_processor import ChunkProcessor, display_chunk_info, recommend_chunk_size
from utils.progress import (
    progress_context, MultiStepProgress, create_processing_steps,
    show_data_processing_progress, show_translation_progress
)

st.set_page_config(
    page_title="뉴퍼스트몰 업데이트 도구",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# UI 헬퍼 함수들
def show_progress_message(message, type="info"):
    """진행 상태를 시각적으로 표시하는 함수"""
    if type == "success":
        st.success(f"✅ {message}")
    elif type == "error":
        st.error(f"❌ {message}")
    elif type == "warning":
        st.warning(f"⚠️ {message}")
    else:
        st.info(f"ℹ️ {message}")

def show_file_uploader(label, key, help_text=None):
    """향상된 파일 업로드 컴포넌트"""
    col1, col2 = st.columns([3, 1])
    with col1:
        file = st.file_uploader(
            label,
            type=['xlsx'],
            key=key,
            help=help_text
        )
    with col2:
        if file:
            st.success("✅ 파일 준비 완료")
    return file

def show_data_preview(df, num_rows=5):
    """데이터 미리보기를 표시하는 함수"""
    with st.expander("📊 데이터 미리보기"):
        st.dataframe(df.head(num_rows), use_container_width=True)

def process_with_progress(func, df, message="처리 중..."):
    """진행 상태 표시와 함께 처리하는 함수"""
    start_time = time.time()
    with st.spinner(message):
        result = func(df)
        end_time = time.time()
        processing_time = end_time - start_time
        show_progress_message(f"처리 완료! (소요시간: {processing_time:.2f}초)", "success")
    return result

# 세션 상태 초기화
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'last_processed_file' not in st.session_state:
    st.session_state.last_processed_file = None
# if 'validation_enabled' not in st.session_state:  # 제거됨
#     st.session_state.validation_enabled = True
if 'chunk_size' not in st.session_state:
    st.session_state.chunk_size = 1000

# 모든 세션 상태 변수 초기화
if 'chunk_size' not in st.session_state:
    st.session_state.chunk_size = 1000

def save_processed_data(df, step):
    """처리된 데이터를 저장하고 버퍼를 반환하는 함수"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    st.session_state.processed_data = df
    st.session_state.last_processed_file = f"step_{step}_result.xlsx"
    
    return buffer

# 탭 생성
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📚 사용설명서",
    "1️⃣ 엑셀 파일 업로드",
    "2️⃣ 가격 정보 처리",
    "3️⃣ 카테고리 전처리",
    "4️⃣ 카테고리 변환",
    "5️⃣ 옵션 형식 변환",
    "6️⃣ 상품명 번역",
    "7️⃣ 옵션 번역",
    "8️⃣ 청크 다운로드",
    "🔍 색상 분석"
])

# 사용설명서 탭
with tab0:
    st.markdown("## 뉴퍼스트몰 업데이트 도구 사용설명서")
    
    st.markdown("""
    ### 🎯 도구 소개
    이 도구는 뉴퍼스트몰의 상품 데이터를 효율적으로 관리하고 업데이트하기 위한 도구입니다.
    엑셀 파일 병합부터 상품명 번역까지 모든 과정을 자동화하여 처리할 수 있습니다.
    
    ### 📝 주요 기능
    1. **엑셀 파일 병합**: 상품DB와 양식 파일을 병합
    2. **가격 정보 처리**: 공급가, 판매가, 상품가 자동 계산
    3. **카테고리 전처리**: 상품 카테고리 정리 및 표준화
    4. **카테고리 변환**: 카테고리 코드 자동 매핑
    5. **옵션 형식 변환**: 옵션 정보 표준 형식으로 변환
    6. **상품명 번역**: 한글 상품명을 일본어로 자동 번역
    7. **옵션 번역**: 색상 옵션을 일본어로 자동 번역 (용어집 활용)
    8. **청크 다운로드**: 대용량 파일 분할 다운로드
    
    ### 💡 사용 순서
    1. 각 단계는 순차적으로 진행하는 것을 권장합니다.
    2. 각 단계에서 생성된 파일은 다음 단계의 입력 파일로 사용됩니다.
    3. 모든 단계는 독립적으로도 실행 가능합니다.
    
    ### ⚠️ 주의사항
    - 파일 업로드 시 엑셀(.xlsx) 형식만 지원됩니다.
    - 번역 기능 사용 시 DeepL API 키가 필요합니다.
    - 대용량 파일 처리 시 시간이 소요될 수 있습니다.
    
    ### 🔍 각 단계별 상세 설명
    
    #### 1단계: 엑셀 파일 병합
    - 상품DB와 양식 파일의 공통 컬럼을 매핑하여 병합
    - 필수 정보 자동 채우기 (상품코드, 배송정보 등)
    
    #### 2단계: 가격 정보 처리
    - 소비자가 기준으로 공급가, 판매가 자동 계산
    - 부가세 처리 및 마진율 자동 적용
    
    #### 3단계: 카테고리 전처리
    - 상품 카테고리 정리 및 표준화
    - 잘못된 카테고리 자동 수정
    
    #### 4단계: 카테고리 변환
    - 표준화된 카테고리를 코드로 변환
    - 카테고리 분포 분석 기능 제공
    
    #### 5단계: 옵션 형식 변환
    - 쉼표로 구분된 옵션을 표준 형식으로 변환
    - 중복 옵션 자동 제거
    
    #### 6단계: 상품명 번역
    - DeepL API를 활용한 자동 번역
    - 모델번호, 규격 정보 보존
    - 배치 처리로 빠른 번역 처리
    - 간소화된 시스템으로 안정적인 처리
    
    #### 7단계: 옵션 번역
    - 색상 옵션을 일본어로 자동 번역
    - 옵션 형식 구조 보존 (색상{...} 형태 유지)
    - 100+ 색상 용어집 활용으로 정확한 번역
    - DeepL API와 용어집의 하이브리드 번역 (41% API 절약)
    
    #### 8단계: 청크 다운로드
    - 쇼핑몰에 업로드 가능한 단위로 분할
    - 각 청크별 개별 다운로드 지원
    """)

# 1단계: 엑셀 파일 업로드 탭
with tab1:
    st.header("엑셀 파일 업로드")
    st.markdown("""
    ### 사용 방법
    1. 상품 DB 엑셀 파일을 업로드하세요
    2. 템플릿 엑셀 파일을 업로드하세요
    3. '파일 병합 시작' 버튼을 클릭하세요
    """)
    
    # 설정 옵션
    chunk_size = st.slider(
        "청크 크기",
        min_value=100,
        max_value=5000,
        value=st.session_state.chunk_size,
        step=100,
        help="한 번에 처리할 데이터 행 수"
    )
    st.session_state.chunk_size = chunk_size
    
    product_db = st.file_uploader(
        "상품 DB 엑셀 파일을 업로드하세요",
        type=['xlsx'],
        key="product_db_1",
        help="상품 정보가 포함된 엑셀 파일을 선택하세요"
    )
    
    if product_db:
        st.success("✅ 상품 DB 파일 준비 완료")
        
    template_file = st.file_uploader(
        "템플릿 엑셀 파일을 업로드하세요",
        type=['xlsx'],
        key="template_1",
        help="뉴퍼스트몰 양식 파일을 선택하세요"
    )
    
    if template_file:
        st.success("✅ 템플릿 파일 준비 완료")
    
    if product_db and template_file:
        if st.button("파일 병합 시작", key="merge_start_1", use_container_width=True):
            try:
                with st.spinner("파일 읽는 중..."):
                    # 파일 읽기
                    product_db_df = pd.read_excel(product_db, engine='openpyxl')
                    template_df = pd.read_excel(template_file, engine='openpyxl')
                
                # 데이터 검증 기능 제거됨 (사용자 요청)
                
                # 청크 처리 정보 표시
                recommended_chunk_size = recommend_chunk_size(product_db_df)
                if chunk_size != recommended_chunk_size:
                    st.info(
                        f"💡 권장 청크 크기: {recommended_chunk_size:,}행 "
                        f"(현재: {chunk_size:,}행)"
                    )
                
                display_chunk_info(product_db_df, chunk_size)
                
                # 데이터 미리보기
                with st.expander("📊 데이터 미리보기"):
                    st.write("상품 DB 미리보기")
                    st.dataframe(product_db_df.head(), use_container_width=True)
                
                # 청크 프로세서를 사용한 병합
                chunk_processor = ChunkProcessor(
                    chunk_size=chunk_size,
                    show_progress=True
                )
                
                with st.spinner("파일 병합 중..."):
                    # 파일 병합
                    merged_df = merge_files(product_db_df, template_df)
                    
                    # 결과 저장
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        merged_df.to_excel(writer, index=False)
                    
                    # 세션 상태 업데이트
                    st.session_state.processed_data = merged_df
                    st.session_state.last_processed_file = "step_1_result.xlsx"
                    
                    # 메모리 정리
                    gc.collect()
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.download_button(
                        label="📥 병합된 파일 다운로드",
                        data=buffer.getvalue(),
                        file_name="merged_file.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_1",
                        use_container_width=True
                    )
                with col2:
                    st.success("✅ 병합 완료!")
                
            except Exception as e:
                st.error(f"❌ 파일 처리 중 오류가 발생했습니다: {str(e)}")

# 2단계: 가격 정보 처리 탭
with tab2:
    st.header("가격 정보 처리")
    st.markdown("""
    ### 사용 방법
    1. 엑셀 파일을 업로드하세요
    2. '가격 정보 처리 시작' 버튼을 클릭하세요
    3. 처리가 완료되면 결과를 다운로드하세요
    """)
    
    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_1_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="price_processor_2")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
    
    if 'df' in locals():
        # 데이터 검증 기능 제거됨 (사용자 요청)
        
        if st.button("가격 정보 처리 시작", key="price_process_2"):
            # 다단계 진행률 표시
            steps = create_processing_steps(["가격 처리", "결과 정리"])
            multi_progress = MultiStepProgress(steps)
            
            try:
                multi_progress.start_step(0)
                
                # 청크 프로세서를 사용한 가격 처리
                chunk_processor = ChunkProcessor(
                    chunk_size=st.session_state.chunk_size,
                    show_progress=True
                )
                
                def process_price_chunk(chunk_df):
                    return calculate_prices_optimized(chunk_df)
                
                processed_df = chunk_processor.process_dataframe_in_chunks(
                    df.copy(), 
                    process_price_chunk
                )
                
                multi_progress.complete_step()
                multi_progress.start_step(1)
                
                # 결과 저장
                buffer = save_processed_data(processed_df, 2)
                
                # 메모리 정리
                gc.collect()
                multi_progress.complete_step()
                multi_progress.complete_all("가격 정보 처리가 완료되었습니다!")
                    
                st.download_button(
                    label="처리된 파일 다운로드",
                    data=buffer.getvalue(),
                    file_name="price_processed.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_2"
                )
                
                # 처리 결과 미리보기
                st.subheader("처리 결과 미리보기")
                st.dataframe(processed_df.head(10))
                    
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

# 3단계: 카테고리 전처리 탭
with tab3:
    st.header("카테고리 전처리")
    st.markdown("""
    ### 사용 방법
    1. 엑셀 파일을 업로드하세요
    2. '카테고리 전처리 시작' 버튼을 클릭하세요
    3. 처리가 완료되면 결과를 다운로드하세요
    """)
    
    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_2_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="preprocess_category_3")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
    
    if 'df' in locals():
        if st.button("카테고리 전처리 시작", key="preprocess_category_start_3"):
            with st.spinner("카테고리 전처리 중..."):
                try:
                    # 전처리 실행
                    processed_df = preprocess_categories(df)
                    
                    # 결과 저장
                    buffer = save_processed_data(processed_df, 3)
                    
                    st.download_button(
                        label="전처리된 파일 다운로드",
                        data=buffer.getvalue(),
                        file_name="category_preprocessed.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_3"
                    )
                    
                    st.success("카테고리 전처리가 완료되었습니다!")
                    
                except Exception as e:
                    st.error(f"전처리 중 오류가 발생했습니다: {str(e)}")

# 4단계: 카테고리 변환 탭
with tab4:
    st.header("카테고리 변환")
    st.markdown("""
    ### 사용 방법
    1. 변환할 엑셀 파일을 업로드하세요
    2. '카테고리 변환 시작' 버튼을 클릭하세요
    3. 변환된 파일을 다운로드하세요
    """)
    
    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_3_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="category_converter_4")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
    
    if 'df' in locals():
        if st.button("카테고리 변환 시작", key="category_convert_4"):
            with st.spinner("카테고리 변환 중..."):
                try:
                    # 카테고리 변환 적용
                    df, success = convert_categories(df)
                    
                    if success:
                        # 결과 저장
                        buffer = save_processed_data(df, 4)
                        
                        st.download_button(
                            label="변환된 파일 다운로드",
                            data=buffer.getvalue(),
                            file_name="category_converted.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_4"
                        )
                        
                        st.success("카테고리 변환이 완료되었습니다!")
                        
                    else:
                        st.error("필요한 컬럼(상품분류 번호, 상품분류 신상품영역)을 찾을 수 없습니다.")
                        
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

# 5단계: 옵션 형식 변환 탭
with tab5:
    st.header("옵션 형식 변환")
    st.markdown("""
    ### 사용 방법
    1. 변환할 엑셀 파일을 업로드하세요
    2. '옵션 형식 변환 시작' 버튼을 클릭하세요
    3. 변환된 파일을 다운로드하세요
    
    ### 변환 예시
    - 변환 전: "화이트,블랙,브라운"
    - 변환 후: "색상{화이트|블랙|브라운}"
    """)

    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_4_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="option_converter_5")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

    if 'df' in locals():
        option_columns = [col for col in df.columns if '옵션입력' in col]
        if option_columns:
            if st.button("옵션 형식 변환 시작", key="option_convert_5"):
                with st.spinner("옵션 형식 변환 중..."):
                    try:
                        progress_bar = st.progress(0)
                        total_cols = len(option_columns)

                        for idx, col in enumerate(option_columns):
                            df[col] = df[col].apply(convert_option_format)
                            progress_bar.progress((idx + 1) / total_cols)

                        # 결과 저장
                        buffer = save_processed_data(df, 5)
                        
                        # 결과 미리보기
                        st.subheader("변환 결과 미리보기")
                        st.write(df[option_columns].head())

                        st.download_button(
                            label="변환된 파일 다운로드",
                            data=buffer.getvalue(),
                            file_name="option_converted.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_5"
                        )

                        st.success("옵션 형식 변환이 완료되었습니다!")
                        
                    except Exception as e:
                        st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("옵션 관련 컬럼을 찾을 수 없습니다.")

# 6단계: 상품명 번역 탭
with tab6:
    st.header("상품명 번역")
    st.markdown("""
    ### 📝 사용 방법
    1. 번역할 엑셀 파일을 업로드하세요
    2. DeepL API 키를 입력하세요 ([API 키 발급받기](https://www.deepl.com/ko/pro-api))
    3. 배치 크기를 선택하세요 (기본값: 5)
    4. '번역 시작' 버튼을 클릭하세요
    
    ### 번역 예시
    - 번역 전: "삼성 갤럭시 스마트폰 케이스"
    - 번역 후: "サムスン ギャラクシー スマートフォン ケース"
    
    ### ⚠️ 주의사항
    - DeepL API는 월 50만 자까지 무료로 사용 가능합니다
    - 대량의 상품명 번역 시 API 사용량을 고려해주세요
    - 배치 크기를 조절하여 번역 속도와 안정성을 최적화할 수 있습니다
    - 간소화된 시스템으로 안정적인 번역 처리
    """)

    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_5_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="translator_6")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

    if 'df' in locals():
        auth_key = st.text_input("DeepL API 키를 입력하세요", type="password", key="deepl_key_6")
        
        # 상품명 컬럼 확인
        if "상품명" not in df.columns:
            st.error("상품명 컬럼을 찾을 수 없습니다.")
            st.stop()

        batch_size = st.select_slider(
            "배치 크기를 선택하세요 (큰 값 = 빠른 처리, 작은 값 = 안정적인 처리)",
            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            value=5,
            key="batch_size_6"
        )

        if st.button("번역 시작", key="translation_start_6"):
            if not auth_key:
                st.warning("⚠️ DeepL API 키를 입력해주세요.")
            else:
                # API 키 검증 기능 제거됨 (사용자 요청)
                
                # 다단계 진행률 표시
                steps = create_processing_steps(["번역 처리", "결과 정리"])
                multi_progress = MultiStepProgress(steps)
                
                try:
                    multi_progress.start_step(0)
                    
                    # 상품명 번역 실행 (비동기)
                    translated_texts = asyncio.run(translate_product_names(
                        df=df,
                        target_column="상품명",
                        api_key=auth_key,
                        batch_size=batch_size,
                        use_async=True
                    ))
                    df["상품명"] = translated_texts
                    
                    multi_progress.complete_step()
                    multi_progress.start_step(1)
                    
                    # 결과 저장
                    buffer = save_processed_data(df, 6)
                    
                    # 메모리 정리
                    gc.collect()
                    multi_progress.complete_step()
                    multi_progress.complete_all("번역이 완료되었습니다!")
                        
                    # 결과 미리보기
                    st.subheader("번역 결과 미리보기")
                    st.dataframe(df["상품명"].head(), use_container_width=True)

                    st.download_button(
                        label="📥 번역 완료 파일 다운로드",
                        data=buffer.getvalue(),
                        file_name="translated_products.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_6"
                    )
                        
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

# 7단계: 옵션 번역 탭
with tab7:
    st.header("옵션 번역")
    
    st.markdown("""
    ### 📝 사용 방법
    1. 옵션 형식이 변환된 엑셀 파일을 업로드하세요
    2. DeepL API 키를 입력하세요 ([API 키 발급받기](https://www.deepl.com/ko/pro-api))
    3. 번역할 옵션 컬럼을 선택하세요
    4. '옵션 번역 시작' 버튼을 클릭하세요
    
    ### 번역 예시
    - 번역 전: "색상{화이트|블랙|브라운}"
    - 번역 후: "색상{ホワイト|ブラック|ブラウン}"
    
    ### 🎯 개선된 번역 시스템
    - **용어집 우선**: 100+ 색상 용어를 정확하게 번역
    - **복합 색상 지원**: "크림화이트" → "クリームホワイト"
    - **목재 색상 완벽 지원**: "오크", "메이플", "아카시아" 등
    - **API 절약**: 용어집 매칭 시 API 사용 안함 (41% 절약)
    
    ### ⚠️ 주의사항
    - 옵션 형식(색상{...})으로 변환된 데이터만 번역됩니다
    - DeepL API 키가 필요합니다 (용어집에 없는 색상만)
    - 용어집에 없는 특수 색상은 DeepL로 번역됩니다
    """)

    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_6_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="option_translator_7")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

    if 'df' in locals():
        # API 키 입력
        api_key = st.text_input("DeepL API 키를 입력하세요", type="password", key="deepl_api_key_7")
        
        if api_key:
            # 옵션 컬럼 찾기
            option_columns = [col for col in df.columns if '옵션입력' in col]
            
            if option_columns:
                # 옵션 형식 데이터 확인
                option_data_count = 0
                for col in option_columns:
                    option_mask = df[col].apply(lambda x: is_option_format(str(x)) if pd.notna(x) else False)
                    option_data_count += option_mask.sum()
                
                st.info(f"번역 가능한 옵션 데이터: {option_data_count}개")
                
                # 컬럼 선택
                selected_columns = st.multiselect(
                    "번역할 옵션 컬럼을 선택하세요",
                    option_columns,
                    default=option_columns,
                    key="option_columns_7"
                )
                
                if selected_columns and st.button("옵션 번역 시작", key="option_translate_7"):
                    with st.spinner("옵션 번역 중..."):
                        try:
                            progress_bar = st.progress(0)
                            total_cols = len(selected_columns)
                            
                            for idx, col in enumerate(selected_columns):
                                st.write(f"번역 중: {col}")
                                df = translate_option_column(df, col, api_key, target_lang='JA')
                                progress_bar.progress((idx + 1) / total_cols)
                            
                            # 결과 저장
                            buffer = save_processed_data(df, 7)
                            
                            # 결과 미리보기
                            st.subheader("번역 결과 미리보기")
                            preview_df = df[selected_columns].head()
                            st.write(preview_df)
                            
                            st.download_button(
                                label="번역된 파일 다운로드",
                                data=buffer.getvalue(),
                                file_name="option_translated.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_7"
                            )
                            
                            st.success("옵션 번역이 완료되었습니다!")
                            
                        except Exception as e:
                            st.error(f"번역 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("옵션 관련 컬럼을 찾을 수 없습니다.")
        else:
            st.warning("DeepL API 키를 입력해주세요.")

# 8단계: 청크 다운로드 탭
with tab8:
    st.header("청크 다운로드")
    st.markdown("""
    ### 사용 방법
    1. 변환된 엑셀 파일을 업로드하세요
    2. 파일이 1000행 단위로 나뉘어 다운로드됩니다
    3. 원하는 청크 파일을 선택하여 다운로드하세요
    """)

    # 이전 단계 결과 파일 자동 로드
    if st.session_state.processed_data is not None and st.session_state.last_processed_file == "step_7_result.xlsx":
        st.info("이전 단계의 결과 파일이 자동으로 로드되었습니다.")
        df = st.session_state.processed_data
    else:
        uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=['xlsx'], key="chunk_downloader_8")
        if uploaded_file:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

    if 'df' in locals():
        try:
            chunk_size_download = st.slider(
                "다운로드 청크 크기",
                min_value=500,
                max_value=5000,
                value=1000,
                step=100,
                help="각 파일에 포함될 행 수"
            )
            
            total_rows = len(df)
            num_chunks = (total_rows + chunk_size_download - 1) // chunk_size_download

            if num_chunks > 1:
                st.write(f"총 {total_rows:,}개 행을 {num_chunks}개의 파일로 나눕니다.")
                
                # 청크 정보 표시
                display_chunk_info(df, chunk_size_download)

                # 청크 프로세서를 사용한 분할
                chunk_processor = ChunkProcessor(
                    chunk_size=chunk_size_download,
                    show_progress=True
                )
                
                chunks = chunk_processor.split_dataframe_into_chunks(df)
                
                for i, chunk_df in enumerate(chunks):
                    start_idx = i * chunk_size_download
                    end_idx = min((i + 1) * chunk_size_download, total_rows)

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        chunk_df.to_excel(writer, index=False)

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.download_button(
                            label=f"청크 {i+1} 다운로드 ({start_idx+1:,}~{end_idx:,}행)",
                            data=buffer.getvalue(),
                            file_name=f"chunk_{i+1}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"chunk_{i}_8"
                        )
                    with col2:
                        st.write(f"{end_idx-start_idx:,}행")

                st.success("모든 청크 파일이 준비되었습니다!")
                
                # 메모리 정리
                gc.collect()

        except Exception as e:
            st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

# 색상 분석 탭 (임시 기능)
with tab9:
    st.header("🔍 색상 데이터 분석")
    st.markdown("""
    ### 📝 사용 방법
    1. 옵션 형식이 변환된 엑셀 파일을 업로드하세요
    2. '색상 분석 실행' 버튼을 클릭하세요
    3. 분석 결과를 확인하고 용어집 개선에 활용하세요
    
    ### 💡 분석 내용
    - 전체 색상 종류 및 빈도 분석
    - 용어집 커버리지 확인
    - 미등록 색상에 대한 번역 제안
    - 컬럼별 색상 분포 분석
    """)
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "색상 분석할 엑셀 파일을 업로드하세요", 
        type=['xlsx'], 
        key="color_analysis_file"
    )
    
    if uploaded_file:
        try:
            df_analysis = pd.read_excel(uploaded_file, engine='openpyxl')
            st.success(f"✅ 파일 로드 완료: {len(df_analysis):,}행")
            
            # 옵션 컬럼 확인
            option_columns = [col for col in df_analysis.columns if '옵션입력' in col]
            if option_columns:
                st.info(f"발견된 옵션 컬럼: {', '.join(option_columns)}")
                
                # 색상 분석 실행
                if st.button("🔍 색상 분석 실행", key="analyze_colors_main", use_container_width=True):
                    with st.spinner("색상 데이터 분석 중..."):
                        try:
                            analysis_result = analyze_colors_in_data(df_analysis, option_columns)
                            
                            # 분석 결과 요약
                            st.subheader("📊 분석 결과 요약")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("총 색상 종류", f"{analysis_result['total_colors']}개")
                            with col2:
                                st.metric("용어집 커버리지", f"{analysis_result['glossary_coverage']:.1f}%")
                            with col3:
                                st.metric("등록된 색상", f"{len(analysis_result['colors_in_glossary'])}개")
                            with col4:
                                st.metric("미등록 색상", f"{len(analysis_result['colors_not_in_glossary'])}개")
                            
                            # 용어집에 있는 색상
                            if analysis_result['colors_in_glossary']:
                                st.subheader("✅ 용어집에 등록된 색상")
                                glossary_df = pd.DataFrame(
                                    analysis_result['colors_in_glossary'],
                                    columns=['한국어', '빈도', '일본어']
                                ).sort_values('빈도', ascending=False)
                                st.dataframe(glossary_df, use_container_width=True)
                            
                            # 용어집에 없는 색상
                            if analysis_result['colors_not_in_glossary']:
                                st.subheader("⚠️ 용어집에 없는 색상")
                                missing_df = pd.DataFrame(
                                    analysis_result['colors_not_in_glossary'],
                                    columns=['색상명', '빈도']
                                ).sort_values('빈도', ascending=False)
                                st.dataframe(missing_df, use_container_width=True)
                                
                                # 용어집 추가 제안
                                suggestions = suggest_glossary_additions(analysis_result['colors_not_in_glossary'])
                                if suggestions:
                                    st.subheader("💡 용어집 추가 제안")
                                    st.info("다음 색상들을 용어집에 추가하는 것을 권장합니다:")
                                    
                                    # 상위 10개 표시
                                    for suggestion in suggestions[:10]:
                                        st.code(suggestion)
                                    
                                    # 전체 제안 보기
                                    if len(suggestions) > 10:
                                        with st.expander(f"전체 제안 보기 ({len(suggestions)}개)"):
                                            for suggestion in suggestions:
                                                st.code(suggestion)
                            
                            # 컬럼별 색상 분포
                            st.subheader("📊 컬럼별 색상 분포")
                            for col, color_counter in analysis_result['colors_by_column'].items():
                                if color_counter:
                                    with st.expander(f"{col} ({len(color_counter)}개 색상)"):
                                        top_colors = color_counter.most_common(10)
                                        col_df = pd.DataFrame(top_colors, columns=['색상명', '빈도'])
                                        st.dataframe(col_df, use_container_width=True)
                            
                            # 분석 결과 엑셀 다운로드
                            st.subheader("📥 분석 결과 다운로드")
                            try:
                                excel_data = export_color_analysis_to_excel(analysis_result)
                                st.download_button(
                                    label="📊 색상 분석 결과 엑셀 다운로드",
                                    data=excel_data,
                                    file_name="color_analysis_result.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="download_color_analysis_main",
                                    use_container_width=True
                                )
                                st.success("✅ 엑셀 파일이 준비되었습니다!")
                            except Exception as e:
                                st.error(f"엑셀 생성 중 오류: {str(e)}")
                                
                        except Exception as e:
                            st.error(f"색상 분석 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("⚠️ 옵션 관련 컬럼을 찾을 수 없습니다. 옵션 형식 변환을 먼저 진행해주세요.")
                
        except Exception as e:
            st.error(f"파일 읽기 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("👆 분석할 엑셀 파일을 업로드해주세요.")