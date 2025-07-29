import re
import streamlit as st
from typing import List, Dict, Optional
from .translate_simplified import translate_with_deepl
import asyncio
import aiohttp
import time
import pandas as pd

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
        
        # 용어집 우선 번역 (개선된 번역 함수 사용)
        from .translate_simplified import translate_color_with_glossary
        
        translated_colors = []
        for color in colors_to_translate:
            translated_color = translate_color_with_glossary(color, api_key, target_lang)
            translated_colors.append(translated_color if translated_color else color)
        
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

# 색상 번역 용어집 (한국어 -> 일본어) - 대폭 확장
COLOR_GLOSSARY: Dict[str, str] = {
    # 기본 색상
    "빨간색": "レッド", "빨강": "レッド", "레드": "レッド", "적색": "レッド",
    "파란색": "ブルー", "파랑": "ブルー", "블루": "ブルー", "청색": "ブルー",
    "노란색": "イエロー", "노랑": "イエロー", "옐로우": "イエ로ー", "황색": "イエ로ー",
    "초록색": "グリーン", "초록": "グリーン", "녹색": "グリーン", "그린": "グリーン",
    "보라색": "パープル", "보라": "パープル", "퍼플": "パープル", "자주색": "パープル",
    "주황색": "オレンジ", "주황": "オレンジ", "오렌지": "オレンジ",
    "분홍색": "ピンク", "분홍": "ピンク", "핑크": "ピンク",
    
    # 무채색
    "검은색": "ブラック", "검정": "ブラック", "블랑": "ブラック", "흑색": "ブラック",
    "하얀색": "ホワイト", "하양": "ホワイト", "화이트": "ホワイト", "백색": "ホワイト",
    "회색": "グレー", "그레이": "グレー", "회백색": "グレー",
    
    # 고급 색상
    "베이지": "ベージュ", "아이보리": "アイボリー", "크림": "クリーム",
    "네이비": "ネイビー", "남색": "ネイビー", "감청색": "ネイビー",
    "카키": "カーキ", "올리브": "オリーブ", "민트": "ミント",
    "라벤더": "ラベンダー", "바이올렛": "バイオレット",
    "마젠타": "マゼンタ", "시안": "シアン", "터콰이즈": "ターコイズ",
    
    # 브라운 계열
    "갈색": "ブラウン", "브라운": "ブラウン", "밤색": "ブラウン",
    "초콜릿": "チョコレート", "커피": "コーヒー", "모카": "モカ",
    "카멜": "キャメル", "타바코": "タバコ",
    
    # 골드/실버 계열
    "금색": "ゴールド", "골드": "ゴールド", "황금색": "ゴールド",
    "은색": "シルバー", "실버": "シルバー", "백금색": "プラチナ",
    
    # 목재/가구 색상 (분석 결과 기반 추가)
    "오크": "オーク", "메이플": "メープル", "아카시아": "アカシア",
    "월넛": "ウォルナット", "멀바우": "メルバウ", "엘다": "エルダー",
    "고무나무": "ゴムノキ", "삼나무": "スギ", "참죽": "チャンチュン",
    "내추럴": "ナチュラル", "네추럴": "ナチュラル", "워시": "ウォッシュ",
    "빈티지": "ヴィンテージ", "엔틱": "アンティーク", "우드": "ウッド",
    "애쉬": "アッシュ", "새틴": "サテン", "마블": "マーブル",
    "세라믹": "セラミック", "편백": "ヒノキ", "자작나무": "シラカバ",
    
    # 색상 수식어
    "연그레이": "ライトグレー", "진그레이": "ダークグレー", "무드블랙": "ムードブラック",
    "스카이블루": "スカイブルー", "베이비핑크": "ベビーピンク", "로즈골드": "로ーズゴールド",
    "파우더블루": "パウダーブルー", "모닝블루": "モーニングブルー", "틸블루": "ティールブルー",
    "샌드베이지": "サンドベージュ", "샌드그레이": "サンドグレー", "메탈그레이": "メタルグレー",
    "바샬트그레이": "バサルトグレー", "새틴그레이": "サテングレー", "빈티지그레이": "ヴィンテージグレー",
    "웜그레이": "ウォームグレー", "차콜그레이": "チャコールグレー", "연핑크": "ライトピンク",
    "인디핑크": "インディピンク", "로투스핑크": "ロータスピンク", "올리브그린": "オリーブグリーン",
    "포레스트그린": "フォレストグリーン", "민트그린": "ミントグリーン", "틸그린": "ティールグリーン",
    "스모키올리브": "スモーキーオリーブ", "버터옐로우": "バターイエロー", "연노랑": "ライトイエロー",
    
    # 복합 색상 (고빈도)
    "순백색": "純白", "유백": "乳白", "버터": "バター", "캐럿": "キャロット",
    "어프리콧": "アプリコット", "피치": "ピーチ", "코랄": "コーラル", "와인": "ワイン",
    "버건디": "バーガンディ", "머스타드": "マスタード", "바닐라": "バニラ",
    "레몬": "レモン", "청록": "ターコイズ", "스카이": "スカイ", "블루베리": "ブルーベリー",
    
    # 특수 색상
    "투명": "透明", "클리어": "クリア", "매트": "マット", "메탈": "メタル",
    "글로시": "グロッシー", "메탈릭": "メタリック", "새틴": "サテン",
    "대리석": "大理石", "원목": "無垢材", "투톤": "ツートン",
    
    # 패턴/질감
    "무늬": "柄", "패턴": "パターン", "스트라이프": "ストライプ",
    "체크": "チェック", "도트": "ドット", "플라워": "フラワー",
    
    # 자주 사용되는 복합 색상들 추가 (미번역 문제 해결용)
    "오크화이트": "オークホワイト", "크림화이트": "クリームホワイト",
    "네추럴피치": "ナチュラルピーチ", "네추럴블루": "ナチュラルブルー",
    "네추럴멀바우": "ナチュラルメルバウ", "네추럴화이트": "ナチュラルホワイト",
    "화이트메이플": "ホワイトメープル", "화이트그레이": "ホワイトグレー",
    "화이트오크": "ホワイトオーク", "다크브라운": "ダークブラウン",
    "라이트브라운": "ライトブラウン", "딥브라운": "ディープブラウン",
    "그레이블랙": "グレーブラック", "모카브라운": "モカブラウン",
    "아이보리메이플": "アイボリーメープル", "워시그린": "ウォッシュグリーン",
    "블랙아카시아": "ブラックアカシア", "그레이메이플": "グレーメープル",
    "베이지브라운": "ベージュブラウン", "라이트그레이": "ライトグレー",
    "페일그레이": "ペールグレー", "다크그레이": "ダークグレー",
    "연회색": "ライトグレー", "차콜블랙": "チャコールブラック",
    "무광실버": "マットシルバー", "유광실버": "グロッシーシルバー"
}

def translate_color_with_glossary(color: str, api_key: str, target_lang: str = 'JA') -> str:
    """용어집을 활용한 색상 번역 (간소화된 버전)"""
    if not color or not color.strip():
        return color
    
    color = color.strip()
    color_lower = color.lower()
    
    # 1단계: 정확한 매칭 우선
    if color_lower in COLOR_GLOSSARY:
        return COLOR_GLOSSARY[color_lower]
    
    # 2단계: 부분 매칭 (간소화)
    for korean, japanese in COLOR_GLOSSARY.items():
        if korean.lower() in color_lower:
            return japanese
    
    # 3단계: DeepL API 사용 (용어집에 없는 경우만)
    try:
        translated = translate_with_deepl(color, api_key, target_lang)
        return translated if translated else color
    except:
        return color

async def translate_option_column_batch(df: pd.DataFrame, api_key: str, batch_size: int = 5) -> pd.DataFrame:
    """옵션 컬럼 배치 번역 (비동기)"""
    option_columns = [col for col in df.columns if '옵션입력' in col]
    for col in option_columns:
        texts = df[col].fillna("").astype(str).tolist()
        translated_texts = await translate_batch_async_with_deepl(texts, api_key, batch_size=batch_size)
        df[col] = translated_texts
    return df

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