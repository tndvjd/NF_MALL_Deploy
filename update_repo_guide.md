# 🔄 기존 저장소 업데이트 가이드 (명령줄)

## 1단계: 기존 저장소 클론

```bash
# 새 폴더에 저장소 클론
git clone https://github.com/tndvjd/nfmall.git
cd nfmall

# 현재 상태 확인
git status
git log --oneline -5
```

## 2단계: 기존 파일 정리

```bash
# 중요한 파일들 백업 (필요시)
cp README.md README_backup.md

# Git 히스토리는 유지하면서 작업 파일들만 정리
# (주의: .git 폴더는 절대 삭제하지 마세요!)

# Python 파일들 삭제
find . -name "*.py" -not -path "./.git/*" -delete

# utils 폴더 삭제 (새 버전으로 교체)
rm -rf utils/

# 기타 파일들 삭제
rm -f requirements.txt .gitignore
```

## 3단계: 새 파일들 복사

```bash
# 현재 작업 중인 프로젝트 폴더에서 파일들 복사
# (실제 경로는 상황에 맞게 수정)

# 메인 파일들
cp /path/to/current/project/app.py .
cp /path/to/current/project/requirements.txt .
cp /path/to/current/project/.gitignore .
cp /path/to/current/project/README.md .
cp /path/to/current/project/USER_GUIDE.md .
cp /path/to/current/project/deploy_guide.md .
cp /path/to/current/project/DEPLOYMENT_CHECKLIST.md .

# 폴더들
cp -r /path/to/current/project/utils/ .
cp -r /path/to/current/project/.streamlit/ .
```

## 4단계: 변경사항 확인 및 커밋

```bash
# 변경사항 확인
git status
git diff

# 새 파일들 추가
git add .

# 삭제된 파일들 확인
git add -u

# 커밋
git commit -m "Update to latest version

- 캐시 시스템 제거로 클라우드 최적화
- 번역 성능 개선 (용어집 활용으로 API 41% 절약)
- 코드 구조 간소화 및 메모리 효율성 향상
- Streamlit Cloud 배포 준비 완료
- 사용자 가이드 및 배포 문서 추가"

# 원격 저장소에 푸시
git push origin main
```

## 5단계: 배포 상태 확인

```bash
# 원격 저장소 상태 확인
git remote -v
git branch -a
git log --oneline -3

# 파일 구조 확인
tree -I '__pycache__|*.pyc|.git'
```

## 주의사항 ⚠️

1. **백업 필수**: 중요한 파일들은 미리 백업
2. **.git 폴더 보존**: 절대 삭제하지 마세요
3. **점진적 업데이트**: 한 번에 모든 파일을 바꾸지 말고 단계적으로
4. **테스트**: 로컬에서 먼저 테스트 후 푸시

## 문제 해결

### 충돌 발생 시
```bash
# 현재 변경사항 임시 저장
git stash

# 최신 상태로 업데이트
git pull origin main

# 저장된 변경사항 복원
git stash pop

# 충돌 해결 후 커밋
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### 실수로 파일 삭제 시
```bash
# 특정 파일 복원
git checkout HEAD -- filename

# 모든 변경사항 취소 (주의!)
git reset --hard HEAD
```