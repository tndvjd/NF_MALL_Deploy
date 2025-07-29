import re
import streamlit as st
from typing import List, Dict, Optional
from .translate import translate_batch_with_deepl

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
    옵션 텍스트의 색상명만 번역하는 함수
    
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
        # 개별 색상명들을 번역
        colors_to_translate = extracted['colors']
        
        # DeepL API로 배치 번역 (기존 번역 함수 재사용)
        translated_colors = translate_batch_with_deepl(
            texts=colors_to_translate,
            api_key=api_key,
            target_lang=target_lang,
            batch_size=len(colors_to_translate),  # 모든 색상을 한 번에 처리
            use_cache=True
        )
        
        # 번역 실패 시 원본 반환
        if not translated_colors or len(translated_colors) != len(colors_to_translate):
            print(f"색상 번역 실패: {option_text}")
            return option_text
        
        # 번역된 색상명들로 옵션 텍스트 재구성
        result = reconstruct_option_text(extracted['prefix'], translated_colors)
        
        print(f"옵션 번역 성공: {option_text} → {result}")
        return result
        
    except Exception as e:
        print(f"옵션 번역 중 오류 발생: {option_text}, 오류: {str(e)}")
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