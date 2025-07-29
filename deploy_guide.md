# 🚀 Streamlit Cloud 배포 가이드

## 현재 디렉토리에서 GitHub에 업로드하는 방법

### 방법 1: GitHub Desktop 사용 (초보자 추천)

1. **GitHub Desktop 다운로드**
   - https://desktop.github.com/ 에서 다운로드
   - 설치 후 GitHub 계정으로 로그인

2. **저장소 클론**
   - GitHub Desktop에서 "Clone a repository from the Internet"
   - 방금 만든 저장소 URL 입력하여 클론

3. **파일 복사**
   - 현재 프로젝트의 모든 파일을 클론된 폴더로 복사
   - 다음 파일들은 제외:
     - `*.xlsx` (엑셀 파일들)
     - `*.db` (데이터베이스 파일들)
     - `__pycache__/` 폴더
     - `.git/` 폴더 (이미 있는 경우)

4. **커밋 및 푸시**
   - GitHub Desktop에서 변경사항 확인
   - Commit message: "Initial commit - 뉴퍼스트몰 업데이트 도구"
   - "Commit to main" 클릭
   - "Push origin" 클릭

### 방법 2: 명령줄 사용 (개발자용)

```bash
# 현재 디렉토리에서 실행
git init
git add .
git commit -m "Initial commit - 뉴퍼스트몰 업데이트 도구"
git branch -M main
git remote add origin https://github.com/[사용자명]/[저장소명].git
git push -u origin main
```

## 필수 파일 체크리스트 ✅

배포 전 다음 파일들이 있는지 확인:

- ✅ `app.py` (메인 앱 파일)
- ✅ `requirements.txt` (의존성 목록)
- ✅ `README.md` (프로젝트 설명)
- ✅ `utils/` 폴더 (유틸리티 모듈들)
- ✅ `.streamlit/config.toml` (Streamlit 설정)
- ✅ `.gitignore` (불필요한 파일 제외)

## 제외해야 할 파일들 ❌

다음 파일들은 GitHub에 업로드하지 마세요:

- ❌ `*.xlsx` (엑셀 데이터 파일들)
- ❌ `*.db` (데이터베이스 파일들)
- ❌ `__pycache__/` (Python 캐시)
- ❌ `.env` (환경변수 파일)
- ❌ 개인 API 키가 포함된 파일들

## 다음 단계

파일 업로드가 완료되면 Streamlit Cloud 배포 단계로 진행하세요!