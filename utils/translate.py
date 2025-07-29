import streamlit as st
import requests
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
from typing import List, Dict, Optional
from .cache_db import get_translation_cache
import urllib3
import json

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 메모리 캐시 저장소 (빠른 접근용)
_translation_cache: Dict[str, str] = {}
# SQLite 캐시 인스턴스
_db_cache = get_translation_cache()
# 용어집 캐시
_glossary_cache: Dict[str, str] = {}

# 기본 용어집 정의 (한국어 -> 일본어)
DEFAULT_GLOSSARY_ENTRIES = {
    "칸": "列",
    "3단 9칸": "3段9列",
    "참죽": "チャンチン",
    "멀바우": "メルバウ",
    "단": "段",
    "층": "段"
}

def _get_cache_key(text: str, target_lang: str) -> str:
    """캐시 키 생성"""
    return hashlib.md5(f"{text}_{target_lang}".encode()).hexdigest()

def _validate_api_key(api_key: str) -> bool:
    """DeepL API 키 형식 검증"""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # DeepL API 키는 일반적으로 UUID 형식 + ":fx" 접미사
    # 예: "12345678-1234-1234-1234-123456789abc:fx"
    parts = api_key.split(':')
    if len(parts) != 2 or parts[1] != 'fx':
        return False
    
    # UUID 부분 검증 (36자, 하이픈 포함)
    uuid_part = parts[0]
    if len(uuid_part) != 36:
        return False
    
    # 하이픈 위치 확인 (8-4-4-4-12)
    expected_hyphen_positions = [8, 13, 18, 23]
    for pos in expected_hyphen_positions:
        if uuid_part[pos] != '-':
            return False
    
    # 제공된 API 키 테스트
    test_key = "fcb562f2-0233-46ad-8d4f-2e10bf05c538:fx"
    if api_key == test_key:
        print(f"API 키 검증: {api_key} - 형식이 올바릅니다.")
    
    return True

def create_glossary(api_key: str, name: str = "Korean Terms Glossary", 
                   source_lang: str = "KO", target_lang: str = "JA", 
                   entries: Dict[str, str] = None) -> Optional[str]:
    """DeepL API를 사용하여 용어집 생성"""
    if entries is None:
        entries = DEFAULT_GLOSSARY_ENTRIES
    
    # TSV 형식으로 용어집 엔트리 변환
    tsv_entries = "\n".join([f"{source}\t{target}" for source, target in entries.items()])
    
    url = "https://api-free.deepl.com/v2/glossaries"
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": name,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "entries": tsv_entries,
        "entries_format": "tsv"
    }
    
    try:
        session = requests.Session()
        session.verify = False
        
        response = session.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        glossary_id = result.get("glossary_id")
        
        if glossary_id:
            # 용어집 ID를 캐시에 저장
            _glossary_cache[f"{source_lang}_{target_lang}"] = glossary_id
            st.success(f"용어집이 성공적으로 생성되었습니다. ID: {glossary_id}")
            return glossary_id
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            st.error(f"용어집 생성 실패 - 잘못된 요청: {str(e)}. API 키를 확인해주세요.")
        elif e.response.status_code == 401:
            st.error(f"용어집 생성 실패 - 인증 오류: {str(e)}. API 키가 유효하지 않습니다.")
        elif e.response.status_code == 403:
            st.error(f"용어집 생성 실패 - 권한 오류: {str(e)}. API 키 권한을 확인해주세요.")
        else:
            st.error(f"용어집 생성 실패 - HTTP 오류 {e.response.status_code}: {str(e)}")
        return None
    except Exception as e:
        st.warning(f"용어집 생성 중 오류 발생: {str(e)}")
        return None

def get_or_create_glossary(api_key: str, source_lang: str = "KO", target_lang: str = "JA") -> Optional[str]:
    """기존 용어집을 가져오거나 새로 생성"""
    cache_key = f"{source_lang}_{target_lang}"
    
    # 캐시에서 확인
    if cache_key in _glossary_cache:
        return _glossary_cache[cache_key]
    
    # 기존 용어집 목록 확인
    try:
        url = "https://api-free.deepl.com/v2/glossaries"
        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
        
        session = requests.Session()
        session.verify = False
        
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        glossaries = result.get("glossaries", [])
        
        # 해당 언어 조합의 용어집 찾기
        for glossary in glossaries:
            if (glossary.get("source_lang", "").upper() == source_lang.upper() and 
                glossary.get("target_lang", "").upper() == target_lang.upper()):
                glossary_id = glossary.get("glossary_id")
                _glossary_cache[cache_key] = glossary_id
                return glossary_id
        
        # 기존 용어집이 없으면 새로 생성
        return create_glossary(api_key, source_lang=source_lang, target_lang=target_lang)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            st.error(f"용어집 조회 실패 - 잘못된 요청: {str(e)}. API 키를 확인해주세요.")
        elif e.response.status_code == 401:
            st.error(f"용어집 조회 실패 - 인증 오류: {str(e)}. API 키가 유효하지 않습니다.")
        else:
            st.error(f"용어집 조회 실패 - HTTP 오류 {e.response.status_code}: {str(e)}")
        return None
    except Exception as e:
        st.warning(f"용어집 확인 중 오류 발생: {str(e)}")
        return None

def preprocess_text_for_translation(text: str) -> str:
    """번역 전 텍스트 전처리 (용어집 보완용)"""
    if not text:
        return text
    
    # 기본 용어 매핑 (용어집이 작동하지 않을 경우 백업)
    replacements = {
        "3단9칸": "3단 9칸",  # 공백 추가로 용어집 매칭 개선
        "2단6칸": "2단 6칸",
        "4단12칸": "4단 12칸",
    }
    
    processed_text = text
    for original, replacement in replacements.items():
        processed_text = processed_text.replace(original, replacement)
    
    return processed_text

def translate_batch_with_deepl(texts, api_key, target_lang='JA', batch_size=5, use_cache=True):
    """DeepL API를 사용하여 텍스트 배치를 번역하는 함수 (SQLite + 메모리 캐싱 지원)"""
    if not texts or not api_key:
        return []
    
    # API 키 형식 검증
    if not _validate_api_key(api_key):
        st.error("잘못된 DeepL API 키 형식입니다. 올바른 형식: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx'")
        return [str(text) if text else "" for text in texts]
    
    url = "https://api-free.deepl.com/v2/translate"
    translated_texts = []
    texts_to_translate = []
    cache_indices = []
    
    # 캐시 확인 및 번역 필요한 텍스트 분리
    for i, text in enumerate(texts):
        text_str = str(text) if text and str(text).strip() else ""
        
        if not text_str:
            translated_texts.append("")
            continue
        
        # 텍스트 전처리 적용
        preprocessed_text = preprocess_text_for_translation(text_str)
        cache_key = _get_cache_key(preprocessed_text, target_lang)
        cached_result = None
        
        if use_cache:
            # 1단계: 메모리 캐시 확인 (가장 빠름)
            if cache_key in _translation_cache:
                cached_result = _translation_cache[cache_key]
            else:
                # 2단계: SQLite 캐시 확인
                cached_result = _db_cache.get_translation(preprocessed_text, target_lang)
                if cached_result:
                    # SQLite에서 찾은 결과를 메모리 캐시에도 저장
                    _translation_cache[cache_key] = cached_result
        
        if cached_result:
            translated_texts.append(cached_result)
        else:
            texts_to_translate.append(preprocessed_text)
            cache_indices.append((i, cache_key, preprocessed_text))
            translated_texts.append(None)  # 나중에 채울 자리 표시
    
    # 번역이 필요한 텍스트만 처리
    if texts_to_translate:
        batch_results = []
        
        for i in range(0, len(texts_to_translate), batch_size):
            batch = texts_to_translate[i:i+batch_size]
            
            headers = {
                "Authorization": f"DeepL-Auth-Key {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text": batch,
                "target_lang": target_lang,
                "preserve_formatting": True
            }
            
            # 소스 언어 자동 감지 (이미 번역된 텍스트 처리)
            if target_lang == 'JA':
                # 모든 텍스트를 검사하여 일본어 여부 확인
                all_text = ' '.join(batch)
                japanese_chars = sum(1 for char in all_text if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF')
                total_meaningful_chars = len([c for c in all_text if c.isalpha() or '\u3040' <= c <= '\u9FAF' or '\u4E00' <= c <= '\u9FAF'])
                
                # 일본어 문자가 30% 이상이거나, 히라가나/가타카나가 포함된 경우
                has_hiragana = any('\u3040' <= char <= '\u309F' for char in all_text)
                has_katakana = any('\u30A0' <= char <= '\u30FF' for char in all_text)
                
                if (total_meaningful_chars > 0 and japanese_chars / total_meaningful_chars > 0.3) or has_hiragana or has_katakana:
                     print(f"이미 일본어로 번역된 텍스트를 감지했습니다. 번역을 건너뜁니다.")
                     print(f"감지된 텍스트: {batch[:2]}...")  # 처음 2개만 출력
                     translated_texts.extend(batch)  # 원본 텍스트 그대로 반환
                     continue
            
            # 용어집 적용 (오류 처리 강화)
            try:
                glossary_id = get_or_create_glossary(api_key, "KO", target_lang)
                if glossary_id and glossary_id.strip():  # 유효한 용어집 ID인지 확인
                    data["glossary_id"] = glossary_id
                    data["source_lang"] = "KO"  # glossary 사용 시 source_lang 필수
            except Exception as e:
                print(f"용어집 처리 중 오류 발생: {str(e)}")
                # 용어집 오류가 있어도 번역은 계속 진행 (용어집 없이)
            
            # 재시도 로직 추가
            max_retries = 3
            success = False
            
            for attempt in range(max_retries):
                try:
                    # SSL 검증 비활성화 및 세션 설정
                    session = requests.Session()
                    session.verify = False  # SSL 검증 비활성화
                    
                    response = session.post(
                        url, 
                        headers=headers, 
                        json=data, 
                        timeout=60
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    batch_translations = [t["text"] for t in result["translations"]]
                    batch_results.extend(batch_translations)
                    success = True
                    
                    # API 호출 제한을 위한 대기
                    time.sleep(0.1)
                    break
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 400:
                        print(f"번역 요청 실패 - 잘못된 요청 (400): {str(e)}")
                        print(f"요청 데이터: {data}")
                        if hasattr(e.response, 'text'):
                            print(f"응답 내용: {e.response.text}")
                    elif e.response.status_code == 401:
                        print(f"번역 요청 실패 - 인증 오류 (401): {str(e)}")
                    elif e.response.status_code == 403:
                        print(f"번역 요청 실패 - 권한 오류 (403): {str(e)}")
                    else:
                        print(f"번역 요청 실패 - HTTP 오류 {e.response.status_code}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # 지수 백오프
                        continue
                    else:
                        st.error(f"DeepL API HTTP 오류. 최대 재시도 횟수 초과: {str(e)}")
                        batch_results.extend(batch)  # 오류 시 원본 반환
                        
                except (requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
                    print(f"연결 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # 지수 백오프
                        continue
                    else:
                        st.error(f"DeepL API 연결 실패. 최대 재시도 횟수 초과: {str(e)}")
                        batch_results.extend(batch)  # 오류 시 원본 반환
                        
                except Exception as e:
                    print(f"배치 번역 중 오류 발생 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        st.error(f"배치 번역 중 오류 발생: {str(e)}")
                        batch_results.extend(batch)  # 오류 시 원본 반환
        
        # 결과를 원래 위치에 배치하고 캐시에 저장
        result_idx = 0
        for original_idx, cache_key, preprocessed_text in cache_indices:
            if result_idx < len(batch_results):
                translation = batch_results[result_idx]
                translated_texts[original_idx] = translation
                
                # 캐시에 저장 (메모리 + SQLite) - 전처리된 텍스트를 키로 사용
                if use_cache:
                    _translation_cache[cache_key] = translation
                    _db_cache.save_translation(preprocessed_text, target_lang, translation)
                    
                result_idx += 1
    
    return [t for t in translated_texts if t is not None]

async def translate_product_names(df, target_column, api_key, batch_size=5, use_async=False):
    """상품명들을 배치로 처리하여 번역"""
    total_items = len(df)
    processed_items = 0
    start_time = time.time()
    
    # 프로그레스 바와 상태 표시 초기화
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        current_batch = st.empty()
        translation_preview = st.empty()
        time_text = st.empty()
    
    # 번역할 텍스트 준비
    texts_to_translate = df[target_column].astype(str).tolist()
    translated_texts = []
    
    # 배치 처리
    for i in range(0, len(texts_to_translate), batch_size):
        batch = texts_to_translate[i:i + batch_size]
        
        # 현재 배치 정보 표시
        current_batch.markdown(f"""
        #### 현재 처리 중인 배치 ({i//batch_size + 1}/{(total_items + batch_size - 1)//batch_size})
        """)
        
        # 배치 번역
        if use_async:
            translated_batch = await translate_batch_async_with_deepl(batch, api_key)
        else:
            translated_batch = translate_batch_with_deepl(batch, api_key)
        translated_texts.extend(translated_batch)
        
        # 번역 미리보기 표시
        preview_text = "### 번역 미리보기\n"
        for orig, trans in zip(batch, translated_batch):
            preview_text += f"- 원본: {orig}\n  → 번역: {trans}\n"
        translation_preview.markdown(preview_text)
        
        # 진행률 업데이트
        processed_items = min(i + batch_size, total_items)
        progress = processed_items / total_items
        progress_bar.progress(progress)
        
        # 상태 텍스트 업데이트
        status_text.markdown(f"""
        ### 진행 상황
        - 처리된 항목: {processed_items:,}/{total_items:,}
        - 진행률: {progress*100:.1f}%
        """)
        
        # 남은 시간 예측
        elapsed_time = time.time() - start_time
        if processed_items > 0:
            items_per_second = processed_items / elapsed_time
            remaining_items = total_items - processed_items
            estimated_remaining_time = remaining_items / items_per_second
            eta = datetime.now() + timedelta(seconds=estimated_remaining_time)
            time_text.markdown(f"""
            ### 예상 시간
            - 남은 시간: {timedelta(seconds=int(estimated_remaining_time))}
            - 완료 예상: {eta.strftime('%H:%M:%S')}
            - 처리 속도: {items_per_second:.1f} 항목/초
            """)
        
        # API 호출 제한 고려
        time.sleep(0.1)  # 100ms 대기
    
    return translated_texts

async def _fetch_translation_async(session, url, headers, text_batch, target_lang, api_key=None, max_retries=3):
    """aiohttp를 사용하여 단일 배치 번역을 비동기로 요청하는 내부 함수 (재시도 로직 포함)"""
    data = {
        "text": text_batch,
        "target_lang": target_lang,
        "preserve_formatting": True
    }
    
    # 소스 언어 자동 감지 (이미 번역된 텍스트 처리)
    # 일본어 텍스트를 일본어로 번역하려는 경우 방지
    if target_lang == 'JA':
        # 모든 텍스트를 검사하여 일본어 여부 확인
        all_text = ' '.join(text_batch)
        japanese_chars = sum(1 for char in all_text if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF')
        total_meaningful_chars = len([c for c in all_text if c.isalpha() or '\u3040' <= c <= '\u9FAF' or '\u4E00' <= c <= '\u9FAF'])
        
        # 일본어 문자가 30% 이상이거나, 히라가나/가타카나가 포함된 경우
        has_hiragana = any('\u3040' <= char <= '\u309F' for char in all_text)
        has_katakana = any('\u30A0' <= char <= '\u30FF' for char in all_text)
        
        if (total_meaningful_chars > 0 and japanese_chars / total_meaningful_chars > 0.3) or has_hiragana or has_katakana:
            print(f"이미 일본어로 번역된 텍스트를 감지했습니다. 번역을 건너뜁니다.")
            print(f"감지된 텍스트: {text_batch[:2]}...")  # 처음 2개만 출력
            return text_batch
    
    # 용어집 적용 (오류 처리 강화)
    if api_key:
        try:
            glossary_id = get_or_create_glossary(api_key, "KO", target_lang)
            if glossary_id and glossary_id.strip():  # 유효한 용어집 ID인지 확인
                data["glossary_id"] = glossary_id
                data["source_lang"] = "KO"  # glossary 사용 시 source_lang 필수
        except Exception as e:
            print(f"용어집 처리 중 오류 발생: {str(e)}")
            # 용어집 오류가 있어도 번역은 계속 진행 (용어집 없이)
    
    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            
            async with session.post(
                url, 
                headers=headers, 
                json=data, 
                timeout=timeout
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return [t["text"] for t in result["translations"]]
                
        except (aiohttp.ClientConnectorError, aiohttp.ClientSSLError) as e:
            print(f"연결 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 지수 백오프
                continue
            else:
                print(f"최대 재시도 횟수 초과. 원본 텍스트 반환.")
                return text_batch
                
        except aiohttp.ClientResponseError as e:
            print(f"비동기 배치 번역 HTTP 오류 (시도 {attempt + 1}/{max_retries}): 상태코드 {e.status}")
            print(f"요청 데이터: {data}")
            if hasattr(e, 'message'):
                print(f"오류 메시지: {e.message}")
            try:
                response_text = await e.response.text() if e.response else "응답 없음"
                print(f"응답 내용: {response_text}")
            except:
                print("응답 내용을 읽을 수 없음")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            else:
                return text_batch
        except Exception as e:
            print(f"비동기 배치 번역 중 오류 발생 (시도 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            else:
                return text_batch  # 오류 시 원본 반환

async def translate_batch_async_with_deepl(texts, api_key, target_lang='JA', batch_size=50, use_cache=True):
    """DeepL API를 사용하여 텍스트 배치를 비동기로 번역하는 함수 (캐싱 지원)"""
    if not texts or not api_key:
        return []
    
    # API 키 형식 검증
    if not _validate_api_key(api_key):
        st.error("잘못된 DeepL API 키 형식입니다. 올바른 형식: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx'")
        return [str(text) if text else "" for text in texts]

    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json"
    }

    translated_texts = [None] * len(texts)
    texts_to_translate = []
    indices_to_translate = []

    # 1. 캐시 확인
    for i, text in enumerate(texts):
        text_str = str(text).strip() if text else ""
        if not text_str:
            translated_texts[i] = ""
            continue

        # 텍스트 전처리
        preprocessed_text = preprocess_text_for_translation(text_str)
        cache_key = _get_cache_key(preprocessed_text, target_lang)
        cached_result = None

        if use_cache:
            if cache_key in _translation_cache:
                cached_result = _translation_cache[cache_key]
            else:
                cached_result = _db_cache.get_translation(preprocessed_text, target_lang)
                if cached_result:
                    _translation_cache[cache_key] = cached_result
        
        if cached_result:
            translated_texts[i] = cached_result
        else:
            texts_to_translate.append(preprocessed_text)
            indices_to_translate.append(i)

    # 2. 번역 필요한 텍스트만 비동기 처리
    if texts_to_translate:
        # SSL 검증 비활성화된 커넥터 생성
        connector = aiohttp.TCPConnector(
            ssl=False,
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=120, connect=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for i in range(0, len(texts_to_translate), batch_size):
                batch = texts_to_translate[i:i+batch_size]
                tasks.append(_fetch_translation_async(session, url, headers, batch, target_lang, api_key))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 3. 결과 통합 및 캐시 저장
            flat_results = [item for sublist in batch_results for item in sublist]
            
            for i, translation in enumerate(flat_results):
                original_index = indices_to_translate[i]
                preprocessed_text = texts_to_translate[i]
                
                translated_texts[original_index] = translation
                
                if use_cache:
                    cache_key = _get_cache_key(preprocessed_text, target_lang)
                    _translation_cache[cache_key] = translation
                    _db_cache.save_translation(preprocessed_text, target_lang, translation)

    return [t if t is not None else "" for t in translated_texts]


async def translate_product_names_optimized(texts, api_key, target_lang='JA', batch_size=5, use_cache=True):
    """최적화된 제품명 번역 함수 (전처리 및 용어집 지원)"""
    if not texts or not api_key:
        return []
    
    # API 키 형식 검증
    if not _validate_api_key(api_key):
        st.error("잘못된 DeepL API 키 형식입니다. 올바른 형식: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx'")
        return [str(text) if text else "" for text in texts]

    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json"
    }
    translated_texts = [None] * len(texts)
    texts_to_translate_map = {}

    # 캐시 확인 및 번역 필요한 텍스트 분리
    for i, text in enumerate(texts):
        text_str = str(text).strip() if text and str(text).strip() else ""
        if not text_str:
            translated_texts[i] = ""
            continue
        
        # 텍스트 전처리
        preprocessed_text = preprocess_text_for_translation(text_str)

        if use_cache:
            cache_key = _get_cache_key(preprocessed_text, target_lang)
            cached_result = _translation_cache.get(cache_key) or _db_cache.get_translation(preprocessed_text, target_lang)
            if cached_result:
                translated_texts[i] = cached_result
                if cache_key not in _translation_cache:
                    _translation_cache[cache_key] = cached_result
            else:
                if preprocessed_text not in texts_to_translate_map:
                    texts_to_translate_map[preprocessed_text] = []
                texts_to_translate_map[preprocessed_text].append(i)
        else:
            if preprocessed_text not in texts_to_translate_map:
                texts_to_translate_map[preprocessed_text] = []
            texts_to_translate_map[preprocessed_text].append(i)

    unique_texts_to_translate = list(texts_to_translate_map.keys())

    if unique_texts_to_translate:
        # SSL 검증 비활성화된 커넥터 생성
        connector = aiohttp.TCPConnector(
            ssl=False,
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=120, connect=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for i in range(0, len(unique_texts_to_translate), batch_size):
                batch = unique_texts_to_translate[i:i+batch_size]
                tasks.append(_fetch_translation_async(session, url, headers, batch, target_lang, api_key))
            
            batch_results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 취합 및 캐시 저장
            result_idx = 0
            for batch_translations in batch_results_list:
                if isinstance(batch_translations, Exception):
                    # 오류 발생 시 빈 문자열로 처리
                    batch_translations = ["" for _ in range(min(batch_size, len(unique_texts_to_translate) - result_idx))]
                
                for original_text, translation in zip(unique_texts_to_translate[result_idx:result_idx+len(batch_translations)], batch_translations):
                    for original_idx in texts_to_translate_map[original_text]:
                        translated_texts[original_idx] = translation
                    if use_cache:
                        cache_key = _get_cache_key(original_text, target_lang)
                        _translation_cache[cache_key] = translation
                        _db_cache.save_translation(original_text, target_lang, translation)
                result_idx += len(batch_translations)

    return [t if t is not None else "" for t in translated_texts]


def translate_product_name(text, api_key, target_lang='JA'):
    """단일 상품명 번역 (전처리 및 용어집 지원)"""
    if not text or not api_key:
        return ""
    
    # 전처리 적용
    preprocessed_text = preprocess_text_for_translation(str(text).strip())
    
    # 캐시 확인
    cache_key = _get_cache_key(preprocessed_text, target_lang)
    cached_result = _translation_cache.get(cache_key) or _db_cache.get_translation(preprocessed_text, target_lang)
    
    if cached_result:
        if cache_key not in _translation_cache:
            _translation_cache[cache_key] = cached_result
        return cached_result
    
    # 배치 번역 사용
    result = translate_batch_with_deepl([preprocessed_text], api_key, target_lang)
    return result[0] if result else ""