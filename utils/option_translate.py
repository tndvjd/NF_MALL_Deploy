"""
옵션 번역 모듈 - 개선된 배치 번역 방식

주요 변경사항:
- 복잡한 용어집 매칭 로직 제거
- 상품명 번역과 동일한 DeepL 배치 번역 방식 적용
- 개별 색상명을 추출하여 배치로 번역 후 재구성
- 구조 안정성과 번역 품질 향상
"""

import re
import streamlit as st
from typing import List, Dict, Optional
import pandas as pd
import io

def extract_option_colors(option_text: str) -> Optional[Dict[str, any]]:
    """
    옵션 텍스트에서 색상 정보를 추출하는 함수
    
    Args:
        option_text: '색상{화이트|진그레이|오크화이트}' 형식의 텍스트
    
    Returns:
        {
            'prefix': '색상',
            'colors': ['화이트', '진그레이', '오크화이트'],
            'original': '색상{화이트|진그레이|오크화이트}'
        }
        또는 패턴이 맞지 않으면 None
    """
    if not option_text or not isinstance(option_text, str):
        return None
    
    # 색상{내용} 패턴 매칭
    pattern = r'^(색상)\{([^}]+)\}$'
    match = re.match(pattern, option_text.strip())
    
    if not match:
        return None
    
    prefix = match.group(1)  # '색상'
    colors_text = match.group(2)  # '화이트|진그레이|오크화이트'
    
    # 파이프로 분리하여 개별 색상명 추출
    colors = [color.strip() for color in colors_text.split('|') if color.strip()]
    
    if not colors:
        return None
    
    return {
        'prefix': prefix,
        'colors': colors,
        'original': option_text
    }

def reconstruct_option_text(prefix: str, translated_colors: List[str]) -> str:
    """
    번역된 색상명들을 다시 옵션 형식으로 조합하는 함수
    
    Args:
        prefix: '색상'
        translated_colors: ['ホワイト', 'ダークグレー', 'オークホワイト']
    
    Returns:
        '색상{ホワイト|ダークグレー|オークホワイト}'
    """
    if not translated_colors:
        return ''
    
    return prefix + "{" + "|".join(translated_colors) + "}"

def translate_option_colors(option_text: str, api_key: str, target_lang: str = 'JA') -> str:
    """
    옵션 텍스트의 색상명을 배치 번역하는 함수 (상품명 번역과 동일한 방식)
    
    Args:
        option_text: '색상{화이트|진그레이|오크화이트}' 형식의 텍스트
        api_key: DeepL API 키
        target_lang: 번역 대상 언어 (기본값: 'JA')
    
    Returns:
        번역된 옵션 텍스트 또는 원본 텍스트 (오류 시)
    """
    if not option_text or not api_key:
        return option_text or ''
    
    # 옵션 형식이 아닌 경우 원본 반환
    extracted = extract_option_colors(option_text)
    if not extracted:
        return option_text
    
    try:
        # 개별 색상명들을 추출
        colors_to_translate = extracted['colors']
        
        # 상품명 번역과 동일한 방식으로 배치 번역
        from .translate_simplified import translate_batch_with_deepl
        translated_colors = translate_batch_with_deepl(colors_to_translate, api_key, target_lang, batch_size=5)
        
        # 번역 실패 시 원본 반환
        if not translated_colors or len(translated_colors) != len(colors_to_translate):
            st.error(f"색상 번역 실패: {option_text}")
            return option_text
        
        # 번역된 색상명들로 옵션 텍스트 재구성
        result = reconstruct_option_text(extracted['prefix'], translated_colors)
        
        return result
        
    except Exception as e:
        st.error(f"옵션 번역 중 오류 발생: {option_text}, 오류: {str(e)}")
        return option_text

def translate_option_batch(option_texts: List[str], api_key: str, target_lang: str = 'JA') -> List[str]:
    """
    여러 옵션 텍스트를 배치로 번역하는 함수
    
    Args:
        option_texts: 옵션 텍스트 리스트
        api_key: DeepL API 키
        target_lang: 번역 대상 언어
    
    Returns:
        번역된 옵션 텍스트 리스트
    """
    if not option_texts or not api_key:
        return option_texts or []
    
    translated_options = []
    
    for option_text in option_texts:
        translated_option = translate_option_colors(option_text, api_key, target_lang)
        translated_options.append(translated_option)
    
    return translated_options

def is_option_format(text: str) -> bool:
    """
    텍스트가 옵션 형식인지 확인하는 함수
    
    Args:
        text: 확인할 텍스트
    
    Returns:
        True if 옵션 형식, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    pattern = r'^색상\{[^}]+\}$'
    return bool(re.match(pattern, text.strip()))

def validate_option_translation(original: str, translated: str) -> bool:
    """
    옵션 번역 결과를 검증하는 함수
    
    Args:
        original: 원본 옵션 텍스트
        translated: 번역된 옵션 텍스트
    
    Returns:
        True if 번역이 올바름, False otherwise
    """
    original_extracted = extract_option_colors(original)
    translated_extracted = extract_option_colors(translated)
    
    if not original_extracted or not translated_extracted:
        return False
    
    # 색상 개수가 같은지 확인
    return len(original_extracted['colors']) == len(translated_extracted['colors'])

# 사용 예시 및 테스트 함수
def test_option_translation():
    """
    옵션 번역 기능 테스트 함수
    """
    test_cases = [
        '색상{화이트|진그레이|오크화이트}',
        '색상{화이트|아카시아|네이비}',
        '색상{네추럴멀바우|네추럴피치|네추럴블루}',
        '색상{화이트|화이트메이플|화이트그레이|메이플|그레이}',
        '색상{화이크|오크}',
        '색상{연그레이|진그레이|오크화이트|화이트}'
    ]
    
    print("=== 옵션 번역 테스트 ===")
    
    for test_case in test_cases:
        extracted = extract_option_colors(test_case)
        if extracted:
            print(f"원본: {test_case}")
            print(f"추출된 색상: {extracted['colors']}")
            print(f"형식 검증: {is_option_format(test_case)}")
            print("-" * 50)
        else:
            print(f"패턴 매칭 실패: {test_case}")

if __name__ == "__main__":
    test_option_translation()

# 용어집 기반 번역 제거 - DeepL 배치 번역으로 대체
# 필요시 후처리에서 명확한 오역만 수정

# 용어집 기반 번역은 제거하고 DeepL 배치 번역만 사용
# 필요시 후처리에서 명확한 오역만 수정하는 방식으로 변경

async def translate_option_column_batch(df: pd.DataFrame, target_column: str, api_key: str, 
                                      batch_size: int = 5, use_async: bool = True) -> List[str]:
    """
    옵션 컬럼 배치 번역 (상품명 번역과 동일한 방식 적용) - 세분화된 진행률 표시
    
    Args:
        df: 데이터프레임
        target_column: 번역할 컬럼명
        api_key: DeepL API 키
        batch_size: 배치 크기
        use_async: 비동기 사용 여부
    
    Returns:
        번역된 텍스트 리스트
    """
    if target_column not in df.columns:
        st.error(f"컬럼 '{target_column}'이 존재하지 않습니다.")
        return []
    
    texts = df[target_column].fillna("").astype(str).tolist()
    total_rows = len(texts)
    
    # 진행률 표시를 위한 컨테이너 생성
    progress_container = st.container()
    with progress_container:
        st.write(f"📊 **옵션 번역 진행상황** - 컬럼: `{target_column}`")
        
        # 전체 진행률 바
        overall_progress = st.progress(0)
        overall_status = st.empty()
        
        # 세부 진행률 정보
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        with detail_col1:
            parsing_status = st.empty()
        with detail_col2:
            translation_status = st.empty()
        with detail_col3:
            reconstruction_status = st.empty()
    
    # 1단계: 옵션 형식 파싱 및 분석
    overall_status.text("1/3 단계: 옵션 형식 분석 중...")
    parsing_status.text("🔍 파싱 중...")
    
    option_texts = []
    option_indices = []
    result_texts = [""] * len(texts)
    option_count = 0
    non_option_count = 0
    
    for i, text in enumerate(texts):
        if is_option_format(text):
            # 옵션 형식인 경우: 색상명들만 추출하여 번역 대상에 추가
            extracted = extract_option_colors(text)
            if extracted:
                option_texts.extend(extracted['colors'])
                option_indices.append((i, len(extracted['colors']), extracted['prefix']))
                option_count += 1
            else:
                result_texts[i] = text  # 파싱 실패시 원본 유지
                non_option_count += 1
        else:
            result_texts[i] = text  # 옵션 형식이 아니면 원본 유지
            non_option_count += 1
        
        # 파싱 진행률 업데이트 (10%씩)
        if (i + 1) % max(1, total_rows // 10) == 0 or i == total_rows - 1:
            progress = (i + 1) / total_rows * 0.2  # 전체의 20%
            overall_progress.progress(progress)
            parsing_status.text(f"🔍 파싱: {i + 1}/{total_rows}")
    
    # 파싱 결과 요약
    unique_colors = len(set(option_texts))
    parsing_status.text(f"✅ 파싱 완료: 옵션 {option_count}개, 일반 {non_option_count}개")
    
    # 2단계: 색상명 배치 번역
    if option_texts:
        overall_status.text(f"2/3 단계: 색상명 번역 중... ({len(option_texts)}개 색상, {unique_colors}개 고유)")
        translation_status.text(f"🌐 번역 대기: {len(option_texts)}개")
        
        try:
            import asyncio
            from .translate_simplified import translate_batch_async_with_deepl, translate_batch_with_deepl
            
            # 번역 시작 전 진행률 업데이트
            overall_progress.progress(0.3)
            translation_status.text(f"🌐 번역 시작: {len(option_texts)}개 색상")
            
            if use_async:
                # 단순하게 기존 함수 사용 (중복 메시지 방지)
                translated_colors = await translate_batch_async_with_deepl(
                    option_texts, api_key, batch_size=batch_size
                )
                
            else:
                # 동기 방식은 기존과 동일
                translated_colors = translate_batch_with_deepl(
                    option_texts, api_key, batch_size=batch_size
                )
            
            # 번역 완료 후 진행률 업데이트
            overall_progress.progress(0.7)
            translation_status.text(f"✅ 번역 완료: {len(translated_colors)}/{len(option_texts)}")
            
            # 3단계: 옵션 형식으로 재구성
            overall_status.text("3/3 단계: 옵션 형식 재구성 중...")
            reconstruction_status.text("🔧 재구성 중...")
            
            color_index = 0
            success_count = 0
            fail_count = 0
            
            for idx, (original_index, color_count, prefix) in enumerate(option_indices):
                try:
                    # 해당 옵션의 번역된 색상들 추출
                    translated_option_colors = translated_colors[color_index:color_index + color_count]
                    color_index += color_count
                    
                    # 옵션 텍스트 재구성
                    if len(translated_option_colors) == color_count:
                        result_texts[original_index] = reconstruct_option_text(prefix, translated_option_colors)
                        success_count += 1
                    else:
                        # 번역 실패시 원본 유지
                        result_texts[original_index] = texts[original_index]
                        fail_count += 1
                        if fail_count <= 3:  # 처음 3개만 경고 표시
                            st.warning(f"옵션 번역 불완전 (행 {original_index + 1}): 원본 유지")
                        
                except Exception as e:
                    result_texts[original_index] = texts[original_index]
                    fail_count += 1
                    if fail_count <= 3:  # 처음 3개만 에러 표시
                        st.error(f"옵션 재구성 오류 (행 {original_index + 1}): {str(e)}")
                
                # 재구성 진행률 업데이트
                if (idx + 1) % max(1, len(option_indices) // 5) == 0 or idx == len(option_indices) - 1:
                    progress = 0.7 + (idx + 1) / len(option_indices) * 0.3
                    overall_progress.progress(progress)
                    reconstruction_status.text(f"🔧 재구성: {idx + 1}/{len(option_indices)}")
            
            # 최종 결과 표시
            overall_progress.progress(1.0)
            overall_status.text("✅ 번역 완료!")
            reconstruction_status.text(f"✅ 성공: {success_count}개, 실패: {fail_count}개")
            
            # 실패가 많은 경우 추가 정보 표시
            if fail_count > 3:
                st.info(f"총 {fail_count}개 옵션에서 번역 문제가 발생했습니다. (처음 3개만 표시)")
                    
        except Exception as e:
            overall_progress.progress(0.3)
            st.error(f"배치 번역 오류: {str(e)}")
            translation_status.text("❌ 번역 실패")
            reconstruction_status.text("⏭️ 원본 유지")
            
            # 전체 번역 실패시 원본 텍스트들로 복원
            for original_index, _, _ in option_indices:
                result_texts[original_index] = texts[original_index]
    else:
        # 번역할 옵션이 없는 경우
        overall_progress.progress(1.0)
        overall_status.text("✅ 완료 (번역할 옵션 없음)")
        translation_status.text("⏭️ 번역 불필요")
        reconstruction_status.text("⏭️ 재구성 불필요")
    
    return result_texts

def analyze_colors_in_data(df: pd.DataFrame) -> Dict[str, any]:
    """
    데이터프레임에서 색상 정보를 분석하는 함수
    
    Args:
        df: 분석할 데이터프레임
    
    Returns:
        색상 분석 결과 딕셔너리
    """
    if df is None or df.empty:
        return {"total_colors": 0, "unique_colors": [], "color_frequency": {}}
    
    option_columns = [col for col in df.columns if '옵션' in col or 'option' in col.lower()]
    all_colors = []
    
    for col in option_columns:
        for value in df[col].fillna("").astype(str):
            if is_option_format(value):
                extracted = extract_option_colors(value)
                if extracted:
                    all_colors.extend(extracted['colors'])
    
    # 색상 빈도 계산
    color_frequency = {}
    for color in all_colors:
        color_frequency[color] = color_frequency.get(color, 0) + 1
    
    return {
        "total_colors": len(all_colors),
        "unique_colors": list(set(all_colors)),
        "color_frequency": color_frequency,
        "most_common": sorted(color_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    }

def suggest_glossary_additions(color_analysis: Dict[str, any]) -> List[str]:
    """
    색상 분석 결과를 바탕으로 번역 검토 제안 (용어집 대신 후처리용)
    
    Args:
        color_analysis: analyze_colors_in_data 결과
    
    Returns:
        번역 검토가 필요한 색상명 리스트
    """
    if not color_analysis or not color_analysis.get("unique_colors"):
        return []
    
    # 빈도가 높은 색상들을 우선적으로 검토 제안
    most_common = color_analysis.get("most_common", [])
    suggestions = [color for color, freq in most_common if freq >= 5]  # 5회 이상 등장하는 색상
    
    return suggestions[:20]  # 상위 20개만 제안

def export_color_analysis_to_excel(color_analysis: Dict[str, any], filename: str = "color_analysis.xlsx") -> bytes:
    """
    색상 분석 결과를 엑셀 파일로 내보내기
    
    Args:
        color_analysis: 색상 분석 결과
        filename: 파일명
    
    Returns:
        엑셀 파일 바이트 데이터
    """
    if not color_analysis:
        return b""
    
    # 엑셀 파일 생성
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 색상 빈도 시트
        if color_analysis.get("color_frequency"):
            freq_df = pd.DataFrame(
                list(color_analysis["color_frequency"].items()),
                columns=["색상명", "빈도"]
            ).sort_values("빈도", ascending=False)
            freq_df.to_excel(writer, sheet_name="색상빈도", index=False)
        
        # 고유 색상 시트
        if color_analysis.get("unique_colors"):
            unique_df = pd.DataFrame(
                color_analysis["unique_colors"],
                columns=["고유색상"]
            )
            unique_df.to_excel(writer, sheet_name="고유색상", index=False)
        
        # 요약 정보 시트
        summary_df = pd.DataFrame([
            ["총 색상 수", color_analysis.get("total_colors", 0)],
            ["고유 색상 수", len(color_analysis.get("unique_colors", []))]
        ], columns=["항목", "값"])
        summary_df.to_excel(writer, sheet_name="요약", index=False)
    
    output.seek(0)
    return output.getvalue()

# 사용 예시 및 테스트 함수
def test_option_translation():
    """
    옵션 번역 기능 테스트 함수
    """
    test_cases = [
        '색상{화이트|진그레이|오크화이트}',
        '색상{화이트|아카시아|네이비}',
        '색상{네추럴멀바우|네추럴피치|네추럴블루}',
        '색상{화이트|화이트메이플|화이트그레이|메이플|그레이}',
        '색상{화이크|오크}',
        '색상{연그레이|진그레이|오크화이트|화이트}'
    ]
    
    print("=== 옵션 번역 테스트 ===")
    
    for test_case in test_cases:
        extracted = extract_option_colors(test_case)
        if extracted:
            print(f"원본: {test_case}")
            print(f"추출된 색상: {extracted['colors']}")
            print(f"형식 검증: {is_option_format(test_case)}")
            print("-" * 50)
        else:
            print(f"패턴 매칭 실패: {test_case}")

if __name__ == "__main__":
    test_option_translation()