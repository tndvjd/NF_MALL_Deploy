# ⚡ 빠른 저장소 업데이트 체크리스트

## 📋 업데이트 전 준비

- [ ] 기존 저장소 백업 (중요한 파일들)
- [ ] 현재 작업 중인 코드 최종 테스트 완료
- [ ] 업데이트할 파일 목록 확인

## 🔄 핵심 파일 업데이트 (필수)

### Python 파일들
- [ ] `app.py` - 메인 애플리케이션 (893줄)
- [ ] `utils/__init__.py` - 모듈 초기화
- [ ] `utils/translate_simplified.py` - 간소화된 번역 모듈
- [ ] `utils/chunk_processor.py` - 청크 처리
- [ ] `utils/progress.py` - 진행률 표시
- [ ] 기타 utils/ 폴더 내 모든 .py 파일들

### 설정 파일들
- [ ] `requirements.txt` - 의존성 목록
- [ ] `.gitignore` - Git 제외 설정
- [ ] `.streamlit/config.toml` - Streamlit 설정

## 📚 문서 파일 업데이트

- [ ] `README.md` - 프로젝트 메인 설명서
- [ ] `USER_GUIDE.md` - 사용자 가이드
- [ ] `deploy_guide.md` - 배포 가이드
- [ ] `DEPLOYMENT_CHECKLIST.md` - 배포 체크리스트

## 🗑️ 제거해야 할 파일들

### 캐시 관련 (더 이상 사용 안함)
- [ ] `utils/cache_db.py` - 삭제됨
- [ ] `fix_translation_issues.py` - 삭제됨
- [ ] `번역_문제_해결_가이드.md` - 삭제됨
- [ ] `translation_cache.db` - 삭제됨

### 데이터 파일들 (배포에서 제외)
- [ ] `*.xlsx` 파일들
- [ ] `*.db` 파일들
- [ ] `__pycache__/` 폴더들

## ✅ 업데이트 후 확인사항

### 파일 구조 확인
```
nfmall/
├── app.py
├── requirements.txt
├── README.md
├── USER_GUIDE.md
├── deploy_guide.md
├── DEPLOYMENT_CHECKLIST.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── utils/
    ├── __init__.py
    ├── translate_simplified.py
    ├── chunk_processor.py
    ├── progress.py
    └── [기타 유틸리티 파일들]
```

### 기능 테스트
- [ ] 로컬에서 `streamlit run app.py` 실행 테스트
- [ ] 모든 탭이 정상 작동하는지 확인
- [ ] import 오류 없는지 확인
- [ ] 파일 업로드 기능 테스트

### Git 상태 확인
- [ ] `git status`로 변경사항 확인
- [ ] 불필요한 파일이 추가되지 않았는지 확인
- [ ] 커밋 메시지 작성 및 푸시

## 🚀 Streamlit Cloud 재배포

업데이트 완료 후:
- [ ] GitHub 푸시 완료 확인
- [ ] Streamlit Cloud에서 자동 재배포 확인 (2-3분 소요)
- [ ] 배포된 앱에서 정상 작동 확인
- [ ] 오류 로그 확인

## 📞 문제 발생 시

1. **Import 오류**: requirements.txt 확인
2. **파일 없음 오류**: 파일 경로 및 이름 확인  
3. **배포 실패**: Streamlit Cloud 로그 확인
4. **기능 오류**: 로컬에서 먼저 테스트

모든 항목을 체크한 후 업데이트를 완료하세요! ✨