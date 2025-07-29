# 🔧 배포 오류 해결 가이드

## 🚨 발생한 오류
```
ModuleNotFoundError: from .cache_db import get_translation_cache
```

## 🔍 원인 분석
- `utils/option_translate.py`에서 삭제된 `translate.py` 모듈을 import
- `translate.py`에서 삭제된 `cache_db.py` 모듈을 import
- 캐시 시스템 제거 과정에서 일부 import 구문이 남아있음

## ✅ 해결 방법

### 1. utils/option_translate.py 수정
**변경 전:**
```python
from .translate import translate_batch_with_deepl
```

**변경 후:**
```python
from .translate_simplified import translate_with_deepl
```

### 2. 번역 로직 수정
**변경 전:**
```python
translated_colors = translate_batch_with_deepl(
    texts=colors_to_translate,
    api_key=api_key,
    target_lang=target_lang,
    batch_size=len(colors_to_translate),
    use_cache=True
)
```

**변경 후:**
```python
translated_colors = []
for color in colors_to_translate:
    translated_color = translate_with_deepl(color, api_key, target_lang)
    translated_colors.append(translated_color if translated_color else color)
```

### 3. 불필요한 파일 제거
다음 파일들은 배포에서 제외:
- `utils/translate.py` (캐시 기능 포함, 사용 안함)
- `utils/translation_test.py` (테스트 파일)
- `utils/__pycache__/` (Python 캐시)
- `utils/core/`, `utils/ui/` (사용하지 않는 폴더들)

## 📁 최종 파일 구조

```
nfmall-update-tool/
├── app.py
├── requirements.txt
├── README.md
├── USER_GUIDE.md
├── .streamlit/
│   └── config.toml
└── utils/
    ├── __init__.py
    ├── translate_simplified.py  # 메인 번역 모듈
    ├── analyze.py
    ├── category.py
    ├── chunk_processor.py
    ├── merge.py
    ├── option.py
    ├── option_translate.py      # 수정됨
    ├── preprocess_category.py
    ├── price.py
    ├── progress.py
    └── validation.py
```

## 🚀 재배포 단계

1. **로컬에서 수정된 파일들 복사**
2. **GitHub Desktop에서 변경사항 확인**
3. **커밋 메시지: "Fix import errors for deployment"**
4. **Push to GitHub**
5. **Streamlit Cloud에서 자동 재배포 확인**

## ✅ 배포 성공 확인

배포 성공 후 다음 사항들을 확인:
- [ ] 앱이 정상적으로 로드됨
- [ ] 모든 탭이 표시됨
- [ ] 파일 업로드 기능 작동
- [ ] 번역 기능 테스트 (API 키 입력 후)
- [ ] 오류 메시지 없음

이제 수정된 파일들을 GitHub에 업로드하면 배포 오류가 해결됩니다! 🎉