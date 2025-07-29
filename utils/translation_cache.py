"""
번역 캐시 시스템 - 메모리 기반 캐싱으로 중복 번역 방지
"""
from typing import Dict, Optional
import hashlib

class TranslationCache:
    """메모리 기반 번역 캐시"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._hit_count = 0
        self._miss_count = 0
    
    def _get_cache_key(self, text: str, target_lang: str = 'JA') -> str:
        """캐시 키 생성"""
        return hashlib.md5(f"{text}_{target_lang}".encode()).hexdigest()
    
    def get(self, text: str, target_lang: str = 'JA') -> Optional[str]:
        """캐시에서 번역 결과 조회"""
        if not text or not text.strip():
            return text
        
        key = self._get_cache_key(text, target_lang)
        if key in self._cache:
            self._hit_count += 1
            return self._cache[key]
        
        self._miss_count += 1
        return None
    
    def set(self, text: str, translation: str, target_lang: str = 'JA'):
        """번역 결과를 캐시에 저장"""
        if not text or not text.strip():
            return
        
        key = self._get_cache_key(text, target_lang)
        self._cache[key] = translation
    
    def get_stats(self) -> Dict[str, int]:
        """캐시 통계 반환"""
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': hit_rate
        }
    
    def clear(self):
        """캐시 초기화"""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0

# 전역 캐시 인스턴스
_global_cache = TranslationCache()

def get_translation_cache() -> TranslationCache:
    """전역 번역 캐시 반환"""
    return _global_cache