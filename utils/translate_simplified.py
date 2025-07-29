"""
간소화된 번역 모듈 (캐시 제거 버전)
"""
import requests
import time
import asyncio
import aiohttp
import re
import pandas as pd
from typing import List, Optional, Dict
import streamlit as st

# 색상 번역 용어집 (한국어 -> 일본어) - 대폭 확장
COLOR_GLOSSARY: Dict[str, str] = {
    # 기본 색상
    "빨간색": "レッド", "빨강": "レッド", "레드": "レッド", "적색": "レッド",
    "파란색": "ブルー", "파랑": "ブルー", "블루": "ブルー", "청색": "ブルー",
    "노란색": "イエロー", "노랑": "イエロー", "옐로우": "イエロー", "황색": "イエロー",
    "초록색": "グリーン", "초록": "グリーン", "녹색": "グリーン", "그린": "グリーン",
    "보라색": "パープル", "보라": "パープル", "퍼플": "パープル", "자주색": "パープル",
    "주황색": "オレンジ", "주황": "オレンジ", "오렌지": "オレンジ",
    "분홍색": "ピンク", "분홍": "ピンク", "핑크": "ピンク",
    
    # 무채색
    "검은색": "ブラック", "검정": "ブラック", "블랙": "ブラック", "흑색": "ブラック",
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
    "스카이블루": "スカイブルー", "베이비핑크": "ベビーピンク", "로즈골드": "ローズゴールド",
    "파우더블루": "パウダーブルー", "모닝블루": "モーニングブルー", "틸블루": "ティールブルー",
    "샌드베이지": "サンドベージュ", "샌드그레이": "サンドグレー", "메탈그레이": "メタルグレー",
    "바샬트그레이": "バサルトグレー", "새틴그레이": "サテングレー", "빈티지그레이": "ヴィンテージグレー",
    "웜그레이": "ウォームグレー", "차콜그레이": "チャコールグレー", "연핑크": "ライトピンク",
    "인디핑크": "インディピンク", "로투ス핑크": "ロータスピンク", "올리브그린": "オリーブグリーン",
    "포레ス트그린": "フォレストグリーン", "민트그린": "ミントグリーン", "틸그린": "ティールグリーン",
    "스모키올리븴": "スモーキーオリーブ", "버터옐로우": "バターイエロー", "연노랑": "ライトイエロー",
    
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

def preprocess_text(text: str) -> str:
    """번역 전 텍스트 전처리"""
    if not text or not isinstance(text, str):
        return ""
    
    # 기본 정리
    text = text.strip()
    
    # 연속된 공백을 하나로 통합
    text = re.sub(r'\s+', ' ', text)
    
    return text

def validate_deepl_api_key(api_key: str) -> bool:
    """DeepL API 키 유효성 검증"""
    if not api_key or not api_key.strip():
        st.error("API 키가 입력되지 않았습니다.")
        return False
    
    # API 키 형식 검증 (DeepL API 키는 보통 UUID 형태)
    if len(api_key.strip()) < 20:
        st.error("API 키 형식이 올바르지 않습니다. DeepL API 키는 최소 20자 이상이어야 합니다.")
        return False
    
    # 간단한 테스트 번역으로 API 키 검증
    test_url = "https://api-free.deepl.com/v2/translate"
    test_data = {
        'auth_key': api_key.strip(),
        'text': 'test',
        'target_lang': 'JA'
    }
    
    try:
        response = requests.post(test_url, data=test_data, timeout=10)
        
        if response.status_code == 403:
            st.error("API 키가 유효하지 않거나 권한이 없습니다.")
            st.error("DeepL 계정에서 API 키를 다시 확인해주세요.")
            return False
        elif response.status_code == 456:
            st.error("API 사용량 한도를 초과했습니다.")
            return False
        elif response.status_code == 200:
            st.success("✅ API 키가 유효합니다.")
            return True
        else:
            st.warning(f"API 응답 코드: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        st.error(f"API 키 검증 중 오류 발생: {str(e)}")
        return False
    
    return False

def translate_with_deepl(text: str, api_key: str, target_lang: str = 'JA') -> Optional[str]:
    """DeepL API를 사용한 단일 텍스트 번역"""
    if not text or not text.strip():
        return ""
    
    preprocessed_text = preprocess_text(text)
    if not preprocessed_text:
        return ""
    
    url = "https://api-free.deepl.com/v2/translate"
    
    data = {
        'auth_key': api_key,
        'text': preprocessed_text,
        'target_lang': target_lang,
        'preserve_formatting': '1'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)  # 타임아웃 단축
        
        # 403 에러에 대한 간단한 처리
        if response.status_code == 403:
            print(f"번역 API 오류: 403 Forbidden - {preprocessed_text}")
            return None
        
        if response.status_code == 200:
            result = response.json()
            if 'translations' in result and result['translations']:
                return result['translations'][0]['text']
        
        print(f"번역 API 응답 코드: {response.status_code}")
        return None
        
    except requests.exceptions.Timeout:
        print(f"번역 API 타임아웃: {preprocessed_text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"번역 API 오류: {str(e)}")
        return None
    except Exception as e:
        print(f"번역 처리 오류: {str(e)}")
        return None

def translate_batch_with_deepl(texts: List[str], api_key: str, target_lang: str = 'JA', 
                              batch_size: int = 5) -> List[str]:
    """배치 번역 (동기 방식)"""
    if not texts:
        return []
    
    translated_texts = [""] * len(texts)
    
    # 진행률 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(texts), batch_size):
        batch_texts = texts[batch_idx:batch_idx + batch_size]
        batch_translations = []
        
        for text in batch_texts:
            translation = translate_with_deepl(text, api_key, target_lang)
            batch_translations.append(translation if translation else "")
            time.sleep(2.0)  # API 호출 간격 (429 에러 방지)
        
        # 결과 저장
        for i, translation in enumerate(batch_translations):
            translated_texts[batch_idx + i] = translation
        
        # 진행률 업데이트
        current_batch = (batch_idx // batch_size) + 1
        progress = current_batch / total_batches
        progress_bar.progress(progress)
        status_text.text(f"번역 진행: {current_batch}/{total_batches} 배치 완료")
    
    progress_bar.empty()
    status_text.empty()
    
    return translated_texts

async def translate_batch_async_with_deepl(texts: List[str], api_key: str, 
                                         target_lang: str = 'JA', 
                                         batch_size: int = 5) -> List[str]:
    """배치 번역 (비동기 방식) - 중복 제거 및 캐싱 최적화"""
    if not texts:
        return []
    
    from utils.translation_cache import get_translation_cache
    cache = get_translation_cache()
    
    # 1단계: 캐시에서 기존 번역 조회 및 중복 제거
    unique_texts = []
    text_to_indices = {}  # 각 고유 텍스트가 원본 리스트의 어느 위치에 있는지 매핑
    translated_texts = [""] * len(texts)
    
    for i, text in enumerate(texts):
        if not text or not text.strip():
            translated_texts[i] = text
            continue
        
        # 캐시 조회
        cached_result = cache.get(text, target_lang)
        if cached_result is not None:
            translated_texts[i] = cached_result
            continue
        
        # 중복 제거
        if text not in text_to_indices:
            text_to_indices[text] = []
            unique_texts.append(text)
        text_to_indices[text].append(i)
    
    if not unique_texts:
        return translated_texts
    
    st.info(f"🔄 중복 제거: {len(texts)}개 → {len(unique_texts)}개 (캐시 적중: {len(texts) - len(unique_texts) - sum(len(indices) for indices in text_to_indices.values())}개)")
    
    # 진행률 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async def translate_single_async(session, text: str) -> str:
        """단일 텍스트 비동기 번역"""
        if not text or not text.strip():
            return ""
        
        preprocessed_text = preprocess_text(text)
        if not preprocessed_text:
            return ""
        
        url = "https://api-free.deepl.com/v2/translate"
        data = {
            'auth_key': api_key,
            'text': preprocessed_text,
            'target_lang': target_lang,
            'preserve_formatting': '1'
        }
        
        try:
            async with session.post(url, data=data, timeout=15) as response:  # 타임아웃 증가
                if response.status == 200:
                    result = await response.json()
                    if 'translations' in result and result['translations']:
                        translated_text = result['translations'][0]['text']
                        if translated_text and translated_text.strip():
                            return translated_text
                        else:
                            print(f"빈 번역 결과: '{preprocessed_text}' -> '{translated_text}'")
                            return ""
                elif response.status == 403:
                    print(f"403 Forbidden: '{preprocessed_text}'")
                    return ""
                else:
                    print(f"API 응답 코드 {response.status}: '{preprocessed_text}'")
                    return ""
        except asyncio.TimeoutError:
            print(f"타임아웃: '{preprocessed_text}'")
            return ""
        except Exception as e:
            print(f"비동기 번역 오류 '{preprocessed_text}': {str(e)}")
            return ""
        
        return ""
    
    # 비동기 처리
    async with aiohttp.ClientSession() as session:
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for batch_idx in range(0, len(texts), batch_size):
            batch_texts = texts[batch_idx:batch_idx + batch_size]
            
            # 배치 내 비동기 처리
            tasks = [translate_single_async(session, text) for text in batch_texts]
            batch_translations = await asyncio.gather(*tasks)
            
            # 결과 저장
            for i, translation in enumerate(batch_translations):
                translated_texts[batch_idx + i] = translation
            
            # 진행률 업데이트
            current_batch = (batch_idx // batch_size) + 1
            progress = current_batch / total_batches
            progress_bar.progress(progress)
            status_text.text(f"번역 진행: {current_batch}/{total_batches} 배치 완료")
            
            # API 호출 간격 (429 에러 방지를 위해 증가)
            await asyncio.sleep(2.0)  # 2초로 증가
    
    progress_bar.empty()
    status_text.empty()
    
    return translated_texts

# 기존 함수들과의 호환성을 위한 래퍼 함수들
async def translate_product_names(df, target_column: str, api_key: str, 
                                batch_size: int = 5, use_async: bool = True):
    """상품명 번역 (기존 인터페이스 호환)"""
    texts = df[target_column].fillna("").astype(str).tolist()
    
    if use_async:
        return await translate_batch_async_with_deepl(texts, api_key, batch_size=batch_size)
    else:
        return translate_batch_with_deepl(texts, api_key, batch_size=batch_size)

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

def translate_option_colors(option_text: str, api_key: str, target_lang: str = 'JA') -> str:
    """옵션 색상 번역 (개선된 버전)"""
    if not option_text or not isinstance(option_text, str):
        return option_text
    
    # 색상{...} 형식 파싱
    match = re.match(r'색상\{([^}]+)\}', option_text)
    if not match:
        return option_text
    
    colors = match.group(1).split('|')
    translated_colors = []
    
    for color in colors:
        color = color.strip()
        if color:
            # 개선된 색상 번역 사용
            translated = translate_color_with_glossary(color, api_key, target_lang)
            translated_colors.append(translated)
    
    return f"색상{{{'|'.join(translated_colors)}}}"

def analyze_colors_in_data(df, option_columns: List[str] = None) -> Dict:
    """데이터에서 색상 분석"""
    import pandas as pd
    from collections import Counter
    
    if option_columns is None:
        option_columns = [col for col in df.columns if '옵션입력' in col]
    
    all_colors = []
    color_stats = {}
    
    for col in option_columns:
        if col not in df.columns:
            continue
            
        col_colors = []
        for option_text in df[col].fillna(""):
            if not isinstance(option_text, str):
                continue
                
            # 색상{...} 형식 파싱
            match = re.match(r'색상\{([^}]+)\}', option_text)
            if match:
                colors = [c.strip() for c in match.group(1).split('|') if c.strip()]
                col_colors.extend(colors)
                all_colors.extend(colors)
        
        color_stats[col] = Counter(col_colors)
    
    # 전체 색상 통계
    total_color_counter = Counter(all_colors)
    
    # 용어집에 있는 색상과 없는 색상 분류
    colors_in_glossary = []
    colors_not_in_glossary = []
    
    for color, count in total_color_counter.items():
        found_in_glossary = False
        color_lower = color.lower()
        
        # 정확한 매칭 우선
        if color_lower in COLOR_GLOSSARY:
            colors_in_glossary.append((color, count, COLOR_GLOSSARY[color_lower]))
            found_in_glossary = True
        else:
            # 복합 색상 매칭 (길이 순으로 정렬하여 긴 매칭 우선)
            sorted_glossary = sorted(COLOR_GLOSSARY.items(), key=lambda x: len(x[0]), reverse=True)
            
            for korean_color, japanese_color in sorted_glossary:
                korean_lower = korean_color.lower()
                
                # 정확한 단어 경계 매칭
                if korean_lower == color_lower:
                    colors_in_glossary.append((color, count, japanese_color))
                    found_in_glossary = True
                    break
                
                # 복합 색상 체크 (수식어 + 기본색상)
                modifiers = ["다크", "라이트", "딥", "소프트", "크림", "메이플", "아이스", "펄", "매트",
                            "오크", "아카시아", "월넛", "멀바우", "엘다", "고무나무", "삼나무", "참죽",
                            "내추럴", "네추럴", "워시", "빈티지", "엔틱", "우드", "애쉬", "새틴", "마블",
                            "레드파인", "진", "연", "올", "무드", "블랙", "스카이", "베이비", "로즈",
                            "파우더", "모닝", "틸", "샌드", "메탈", "바샬트", "웜", "차콜", "인디",
                            "로투스", "스모키", "버터", "순백", "유백"]
                for modifier in modifiers:
                    if (color_lower.startswith(modifier) and color_lower.endswith(korean_lower)) or \
                       (color_lower.endswith(modifier) and color_lower.startswith(korean_lower)):
                        modifier_jp = {
                            "다크": "ダーク", "라이트": "ライト", "딥": "ディープ", 
                            "소프트": "ソフト", "크림": "クリーム", "메이플": "メープル",
                            "아이스": "アイス", "펄": "パール", "매트": "マット",
                            "오크": "オーク", "아카시아": "アカシア", "월넛": "ウォルナット",
                            "멀바우": "メルバウ", "엘다": "エルダー", "고무나무": "ゴムノキ",
                            "삼나무": "スギ", "참죽": "チャンチュン", "내추럴": "ナチュラル",
                            "네추럴": "ナチュラル", "워시": "ウォッシュ", "빈티지": "ヴィンテージ",
                            "엔틱": "アンティーク", "우드": "ウッド", "애쉬": "アッシュ",
                            "새틴": "サテン", "마블": "マーブル", "레드파인": "レッドパイン",
                            "진": "ダーク", "연": "ライト", "올": "オール", "무드": "ムード",
                            "스카이": "スカイ", "베이비": "ベビー", "로즈": "ローズ",
                            "파우더": "パウダー", "모닝": "モーニング", "틸": "ティール",
                            "샌드": "サンド", "메탈": "メタル", "바샬트": "バサルト",
                            "웜": "ウォーム", "차콜": "チャコール", "인디": "インディ",
                            "로투스": "ロータス", "스모키": "スモーキー", "버터": "バター",
                            "순백": "純白", "유백": "乳白"
                        }.get(modifier, modifier)
                        
                        if color_lower.startswith(modifier):
                            predicted_translation = f"{modifier_jp}{japanese_color}"
                        else:
                            predicted_translation = f"{japanese_color}{modifier_jp}"
                            
                        colors_in_glossary.append((color, count, predicted_translation))
                        found_in_glossary = True
                        break
                
                if found_in_glossary:
                    break
        
        if not found_in_glossary:
            colors_not_in_glossary.append((color, count))
    
    return {
        'total_colors': len(total_color_counter),
        'unique_colors': list(total_color_counter.keys()),
        'color_frequency': total_color_counter,
        'colors_by_column': color_stats,
        'colors_in_glossary': colors_in_glossary,
        'colors_not_in_glossary': colors_not_in_glossary,
        'glossary_coverage': len(colors_in_glossary) / max(1, len(total_color_counter)) * 100
    }

def suggest_glossary_additions(colors_not_in_glossary: List[tuple]) -> List[str]:
    """용어집에 추가할 색상 제안"""
    suggestions = []
    
    # 자동 번역 제안 (일반적인 색상 패턴)
    auto_translations = {
        # 그레이 계열
        r'.*그레이.*|.*그레.*|.*회색.*': 'グレー',
        r'.*라이트.*그레.*|.*연.*회색.*': 'ライトグレー',
        r'.*다크.*그레.*|.*진.*회색.*': 'ダークグレー',
        
        # 베이지/크림 계열
        r'.*베이지.*': 'ベージュ',
        r'.*아이보리.*': 'アイボリー',
        r'.*크림.*': 'クリーム',
        
        # 네이비 계열
        r'.*네이비.*|.*남색.*': 'ネイビー',
        
        # 카키/올리브 계열
        r'.*카키.*': 'カーキ',
        r'.*올리브.*': 'オリーブ',
        
        # 와인/버건디 계열
        r'.*와인.*': 'ワイン',
        r'.*버건디.*': 'バーガンディ',
        
        # 메탈 계열
        r'.*골드.*|.*금색.*': 'ゴールド',
        r'.*실버.*|.*은색.*': 'シルバー',
        r'.*메탈.*': 'メタリック',
        
        # 기타
        r'.*코랄.*': 'コーラル',
        r'.*민트.*': 'ミント',
        r'.*라벤더.*': 'ラベンダー',
        r'.*터콰이즈.*': 'ターコイズ'
    }
    
    for color, count in colors_not_in_glossary:
        if count >= 2:  # 2회 이상 등장하는 색상
            suggested_translation = None
            
            # 자동 번역 패턴 매칭
            for pattern, translation in auto_translations.items():
                if re.match(pattern, color, re.IGNORECASE):
                    suggested_translation = translation
                    break
            
            if suggested_translation:
                suggestions.append(f"'{color}': '{suggested_translation}', # {count}회 등장 (자동 제안)")
            else:
                suggestions.append(f"'{color}': '(번역 필요)', # {count}회 등장")
    
    return suggestions

def export_color_analysis_to_excel(analysis_result: Dict) -> bytes:
    """색상 분석 결과를 엑셀로 내보내기"""
    import io
    import pandas as pd
    
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # 전체 색상 빈도
        if analysis_result['color_frequency']:
            freq_df = pd.DataFrame(
                list(analysis_result['color_frequency'].items()),
                columns=['색상명', '빈도']
            ).sort_values('빈도', ascending=False)
            freq_df.to_excel(writer, sheet_name='전체_색상_빈도', index=False)
        
        # 용어집에 있는 색상
        if analysis_result['colors_in_glossary']:
            glossary_df = pd.DataFrame(
                analysis_result['colors_in_glossary'],
                columns=['한국어', '빈도', '일본어']
            ).sort_values('빈도', ascending=False)
            glossary_df.to_excel(writer, sheet_name='용어집_등록_색상', index=False)
        
        # 용어집에 없는 색상
        if analysis_result['colors_not_in_glossary']:
            missing_df = pd.DataFrame(
                analysis_result['colors_not_in_glossary'],
                columns=['색상명', '빈도']
            ).sort_values('빈도', ascending=False)
            missing_df.to_excel(writer, sheet_name='용어집_미등록_색상', index=False)
        
        # 컬럼별 분석
        for col, color_counter in analysis_result['colors_by_column'].items():
            if color_counter:
                col_df = pd.DataFrame(
                    list(color_counter.items()),
                    columns=['색상명', '빈도']
                ).sort_values('빈도', ascending=False)
                sheet_name = f"컬럼_{col.replace('옵션입력', '')}"[:31]  # 엑셀 시트명 길이 제한
                col_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return buffer.getvalue()

def translate_option_column(df, column_name: str, api_key: str, target_lang: str = 'JA'):
    """옵션 컬럼 번역 (기존 인터페이스 호환)"""
    def translate_option_row(option_text):
        return translate_option_colors(option_text, api_key, target_lang)
    
    df[column_name] = df[column_name].apply(translate_option_row)
    return df

async def translate_option_column_batch_old(df, target_column: str, api_key: str, 
                                      batch_size: int = 5, use_async: bool = True):
    """옵션 컬럼 배치 번역 (상품명 번역과 동일한 방식)"""
    
    # 대폭 확장된 색상 매핑 테이블 (API 호출 최소화)
    color_map = {
        # 기본 색상
        '화이트': 'ホワイト', '블랙': 'ブラック', '그레이': 'グレー',
        '연그레이': 'ライトグレー', '진그레이': 'ダークグレー',
        '베이지': 'ベージュ', '브라운': 'ブラウン', '네이비': 'ネイビー',
        '오크': 'オーク', '메이플': 'メープル', '아카시아': 'アカシア',
        '월넛': 'ウォルナット', '멀바우': 'メルバウ', '크림': 'クリーム',
        '아이보리': 'アイボリー', '카키': 'カーキ', '올리브': 'オリーブ',
        '민트': 'ミント', '라벤더': 'ラベンダー', '골드': 'ゴールド',
        '실버': 'シルバー', '레드': 'レッド', '블루': 'ブルー',
        '그린': 'グリーン', '옐로우': 'イエロー', '핑크': 'ピンク',
        
        # 복합 색상 (로그에서 자주 나타나는 색상들)
        '오크화이트': 'オークホワイト', '크림화이트': 'クリームホワイト',
        '네추럴': 'ナチュラル', '네추럴멀바우': 'ナチュラルメルバウ',
        '네추럴피치': 'ナチュラルピーチ', '네추럴블루': 'ナチュラルブルー',
        '화이트메이플': 'ホワイトメープル', '화이트그레이': 'ホワイトグレー',
        '화이트오크': 'ホワイトオーク', '다크브라운': 'ダークブラウン',
        '라이트브라운': 'ライトブラウン', '딥브라운': 'ディープブラウン',
        
        # 자주 사용되는 복합 색상들 추가
        '그레이블랙': 'グレーブラック', '참죽': 'チャンチュン', '투톤': 'ツートン',
        '모카브라운': 'モカブラウン', '버건디': 'バーガンディ', '파우더블루': 'パウダーブルー',
        '로투스핑크': 'ロータスピンク', '네추럴화이트': 'ナチュラルホワイト',
        '아이보리메이플': 'アイボリーメープル', '워시그린': 'ウォッシュグリーン',
        '블랙아카시아': 'ブラックアカシア', '그레이메이플': 'グレーメープル',
        '커피': 'コーヒー', '베이지브라운': 'ベージュブラウン', '모카': 'モカ',
        '오렌지': 'オレンジ', '연핑크': 'ライトピンク', '라이트그레이': 'ライトグレー',
        '웜그레이': 'ウォームグレー', '샌드베이지': 'サンドベージュ', '어프리콧': 'アプリコット',
        '레몬': 'レモン', '대리석': '大理石', '투명': '透明', '엘다': 'エルダー',
        '포레스트그린': 'フォレストグリーン', '샌드그레이': 'サンドグレー',
        '새틴그레이': 'サテングレー', '바샬트그레이': 'バサルトグレー',
        '차콜그레이': 'チャコールグレー', '메탈그레이': 'メタルグレー',
        '빈티지그레이': 'ヴィンテージグレー', '페일그레이': 'ペールグレー',
        '다크그레이': 'ダークグレー', '연회색': 'ライトグレー',
        '무드블랙': 'ムードブラック', '차콜블랙': 'チャコールブラック',
        '로즈골드': 'ローズゴールド', '무광실버': 'マットシルバー',
        '유광실버': 'グロッシーシルバー', '세라믹': 'セラミック',
        '원목': '無垢材', '내추럴': 'ナチュラル', '워시': 'ウォッシュ',
        '빈티지': 'ヴィンテージ', '엔틱': 'アンティーク', '새틴': 'サテン',
        '마블': 'マーブル', '메탈': 'メタル', '우드': 'ウッド'
    }
    
    def process_option_text(option_text):
        """옵션 텍스트 처리 함수"""
        if pd.isna(option_text) or not str(option_text).strip():
            return option_text
        
        text = str(option_text).strip()
        
        # 색상{...} 형식이 아니면 원본 반환
        if not text.startswith('색상{') or not text.endswith('}'):
            return text
        
        try:
            # 색상 추출
            colors_part = text[3:-1]  # '색상{' 와 '}' 제거
            colors = [c.strip() for c in colors_part.split('|') if c.strip()]
            
            # 빈 괄호인 경우 원본 그대로 반환 (처리하지 않음)
            if not colors:
                print(f"빈 옵션 발견, 원본 유지: {text}")
                return text
            
            # 매핑 테이블에 있는 색상과 없는 색상 분리
            mapped_colors = []
            api_needed_colors = []
            color_indices = []
            
            for i, color in enumerate(colors):
                if color in color_map:
                    mapped_colors.append((i, color_map[color]))
                else:
                    api_needed_colors.append(color)
                    color_indices.append(i)
            
            return {
                'original': text,
                'colors': colors,
                'mapped_colors': mapped_colors,
                'api_needed_colors': api_needed_colors,
                'color_indices': color_indices
            }
        except Exception as e:
            print(f"옵션 처리 오류: {text}, 에러: {str(e)}")
            return text
    
    # 모든 옵션 텍스트 처리
    texts = df[target_column].fillna("").astype(str).tolist()
    processed_data = [process_option_text(text) for text in texts]
    
    # API 번역이 필요한 색상들 수집
    all_api_colors = []
    for data in processed_data:
        if isinstance(data, dict) and 'api_needed_colors' in data:
            all_api_colors.extend(data['api_needed_colors'])
    
    # 중복 제거
    unique_api_colors = list(set(all_api_colors))
    
    # API 번역 실행 (429 에러 방지를 위한 제한된 처리)
    if unique_api_colors:
        print(f"API 번역 필요한 색상 수: {len(unique_api_colors)}")
        
        # 429 에러 방지: API 번역을 제한하고 대부분 원본 유지
        api_translation_dict = {}
        
        if len(unique_api_colors) > 100:
            print(f"⚠️ API 번역 필요한 색상이 {len(unique_api_colors)}개로 너무 많습니다.")
            print("429 에러 방지를 위해 API 번역을 건너뛰고 원본 색상을 유지합니다.")
            print("매핑 테이블에 자주 사용되는 색상을 추가하는 것을 권장합니다.")
        else:
            print(f"API 번역 시도: {unique_api_colors[:10]}...")  # 처음 10개만 출력
            
            # 소량의 색상만 API 번역 시도
            if use_async:
                translated_api_colors = await translate_batch_async_with_deepl(
                    unique_api_colors, api_key, batch_size=2  # 배치 크기를 2로 줄임
                )
            else:
                translated_api_colors = translate_batch_with_deepl(
                    unique_api_colors, api_key, batch_size=2
                )
            
            # 번역 결과 분석
            successful_translations = 0
            failed_translations = 0
            
            # 번역 결과를 딕셔너리로 변환 (빈 결과 필터링)
            for original, translated in zip(unique_api_colors, translated_api_colors):
                # 번역 결과가 유효한 경우만 딕셔너리에 추가
                if translated and translated.strip():
                    api_translation_dict[original] = translated
                    successful_translations += 1
                else:
                    failed_translations += 1
                    # 실패한 색상은 로그만 출력 (너무 많아서 일부만)
                    if failed_translations <= 10:
                        print(f"번역 실패: '{original}' -> '{translated}'")
            
            print(f"번역 성공: {successful_translations}개, 실패: {failed_translations}개")
    else:
        api_translation_dict = {}
        print("API 번역이 필요한 색상이 없습니다 (모두 매핑 테이블에 있음)")
    
    # 최종 결과 조합
    final_results = []
    for data in processed_data:
        if isinstance(data, str):
            # 처리되지 않은 텍스트 (색상 형식이 아님)
            final_results.append(data)
        elif isinstance(data, dict):
            # 색상 형식 텍스트
            colors = data['colors'][:]
            
            # 매핑된 색상 적용
            for idx, translated in data['mapped_colors']:
                colors[idx] = translated
            
            # API 번역된 색상 적용 (실패 시 원본 보존)
            for i, original_idx in enumerate(data['color_indices']):
                original_color = data['api_needed_colors'][i]
                if original_color in api_translation_dict:
                    translated_color = api_translation_dict[original_color]
                    # 번역 결과가 유효한 경우만 적용, 그렇지 않으면 원본 유지
                    if translated_color and translated_color.strip():
                        colors[original_idx] = translated_color
                    else:
                        # 번역 실패 시 원본 색상 명시적으로 유지
                        colors[original_idx] = original_color
                else:
                    # API 번역 딕셔너리에 없는 경우 (건너뛴 경우) 원본 색상 유지
                    colors[original_idx] = original_color
            
            # 최종 옵션 텍스트 구성 (빈 색상 필터링)
            valid_colors = [color for color in colors if color and color.strip()]
            if valid_colors:
                final_results.append(f"색상{{{'|'.join(valid_colors)}}}")
            else:
                # 모든 색상이 빈 문자열인 경우 원본 반환
                print(f"⚠️ 모든 색상이 빈 문자열: {data['original']}")
                print(f"   원본 색상들: {data['colors']}")
                print(f"   처리된 색상들: {colors}")
                print(f"   매핑된 색상들: {data['mapped_colors']}")
                print(f"   API 필요 색상들: {data['api_needed_colors']}")
                final_results.append(data['original'])
        else:
            final_results.append(data)
    
    return final_results