#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 시스템 테스트 스크립트

이 스크립트는 새로 구현된 용어집 기능과 전처리 기능을 테스트합니다.
- "칸", "참죽", "멀바우" 등의 용어가 올바르게 번역되는지 확인
- DeepL 용어집 기능 활용
- 캐싱 시스템 동작 확인
"""

import asyncio
import os
from translate import (
    translate_batch_with_deepl,
    translate_product_name,
    translate_product_names_async,
    translate_product_names_optimized,
    create_glossary,
    get_or_create_glossary,
    preprocess_text_for_translation,
    DEFAULT_GLOSSARY_ENTRIES
)

# 테스트용 API 키 (실제 사용 시 환경변수나 설정 파일에서 가져오세요)
API_KEY = os.getenv('DEEPL_API_KEY', 'your-deepl-api-key-here')

# 테스트 데이터
TEST_TEXTS = [
    "3단 9칸 책장",
    "참죽 원목 테이블",
    "멀바우 마루판",
    "2단 6칸 서랍장",
    "4단 12칸 수납함",
    "참죽나무 의자",
    "멀바우 원목 침대",
    "칸막이 선반",
    "단층 침대",
    "층층이 쌓인 책들"
]

def test_preprocessing():
    """전처리 기능 테스트"""
    print("=== 전처리 기능 테스트 ===")
    
    test_cases = [
        "3단9칸",
        "2단6칸", 
        "4단12칸"
    ]
    
    for text in test_cases:
        processed = preprocess_text_for_translation(text)
        print(f"원본: '{text}' -> 전처리: '{processed}'")
    print()

def test_glossary_creation():
    """용어집 생성 테스트"""
    print("=== 용어집 생성 테스트 ===")
    
    if API_KEY == 'your-deepl-api-key-here':
        print("⚠️  실제 API 키가 설정되지 않았습니다. 용어집 테스트를 건너뜁니다.")
        return False
    
    print("기본 용어집 엔트리:")
    for ko, ja in DEFAULT_GLOSSARY_ENTRIES.items():
        print(f"  {ko} -> {ja}")
    
    # 용어집 생성 또는 가져오기
    glossary_id = get_or_create_glossary(API_KEY)
    if glossary_id:
        print(f"✅ 용어집 ID: {glossary_id}")
        return True
    else:
        print("❌ 용어집 생성/가져오기 실패")
        return False
    print()

def test_single_translation():
    """단일 번역 테스트"""
    print("=== 단일 번역 테스트 ===")
    
    if API_KEY == 'your-deepl-api-key-here':
        print("⚠️  실제 API 키가 설정되지 않았습니다. 번역 테스트를 건너뜁니다.")
        return
    
    test_text = "3단 9칸 참죽 책장"
    print(f"번역할 텍스트: '{test_text}'")
    
    result = translate_product_name(test_text, API_KEY)
    print(f"번역 결과: '{result}'")
    print()

def test_batch_translation():
    """배치 번역 테스트"""
    print("=== 배치 번역 테스트 ===")
    
    if API_KEY == 'your-deepl-api-key-here':
        print("⚠️  실제 API 키가 설정되지 않았습니다. 번역 테스트를 건너뜁니다.")
        return
    
    print("번역할 텍스트 목록:")
    for i, text in enumerate(TEST_TEXTS, 1):
        print(f"  {i}. {text}")
    
    print("\n번역 중...")
    results = translate_batch_with_deepl(TEST_TEXTS, API_KEY, batch_size=3)
    
    print("\n번역 결과:")
    for original, translated in zip(TEST_TEXTS, results):
        print(f"  {original} -> {translated}")
    print()

async def test_async_translation():
    """비동기 번역 테스트"""
    print("=== 비동기 번역 테스트 ===")
    
    if API_KEY == 'your-deepl-api-key-here':
        print("⚠️  실제 API 키가 설정되지 않았습니다. 번역 테스트를 건너뜁니다.")
        return
    
    print("비동기 번역 중...")
    results = await translate_product_names_async(TEST_TEXTS, API_KEY, batch_size=3)
    
    print("\n비동기 번역 결과:")
    for original, translated in zip(TEST_TEXTS, results):
        print(f"  {original} -> {translated}")
    print()

def test_cache_performance():
    """캐시 성능 테스트"""
    print("=== 캐시 성능 테스트 ===")
    
    if API_KEY == 'your-deepl-api-key-here':
        print("⚠️  실제 API 키가 설정되지 않았습니다. 캐시 테스트를 건너뜁니다.")
        return
    
    import time
    
    # 첫 번째 번역 (API 호출)
    start_time = time.time()
    result1 = translate_product_name("3단 9칸 참죽 책장", API_KEY)
    first_time = time.time() - start_time
    
    # 두 번째 번역 (캐시 사용)
    start_time = time.time()
    result2 = translate_product_name("3단 9칸 참죽 책장", API_KEY)
    second_time = time.time() - start_time
    
    print(f"첫 번째 번역 (API): {first_time:.3f}초 -> '{result1}'")
    print(f"두 번째 번역 (캐시): {second_time:.3f}초 -> '{result2}'")
    print(f"캐시 성능 향상: {first_time/second_time:.1f}배 빠름")
    print()

async def main():
    """메인 테스트 함수"""
    print("🚀 DeepL 번역 시스템 테스트 시작\n")
    
    # 1. 전처리 테스트
    test_preprocessing()
    
    # 2. 용어집 테스트
    glossary_available = test_glossary_creation()
    
    # 3. 단일 번역 테스트
    test_single_translation()
    
    # 4. 배치 번역 테스트
    test_batch_translation()
    
    # 5. 비동기 번역 테스트
    await test_async_translation()
    
    # 6. 캐시 성능 테스트
    test_cache_performance()
    
    print("✅ 모든 테스트 완료!")
    
    if not glossary_available:
        print("\n💡 팁: 실제 DeepL API 키를 설정하면 용어집 기능을 테스트할 수 있습니다.")
        print("   환경변수 DEEPL_API_KEY에 API 키를 설정하거나")
        print("   이 스크립트의 API_KEY 변수를 수정하세요.")

if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(main())