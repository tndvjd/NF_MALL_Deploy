import streamlit as st
import time
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import threading
from dataclasses import dataclass
from enum import Enum

class ProgressType(Enum):
    """진행률 표시 타입"""
    BAR = "bar"
    SPINNER = "spinner"
    METRIC = "metric"
    COMBINED = "combined"

@dataclass
class ProgressState:
    """진행률 상태 정보"""
    current: int = 0
    total: int = 100
    message: str = ""
    start_time: float = 0
    estimated_remaining: float = 0
    speed: float = 0
    
class EnhancedProgressBar:
    """향상된 진행률 표시 클래스"""
    
    def __init__(self, 
                 total: int, 
                 title: str = "처리 중...",
                 progress_type: ProgressType = ProgressType.COMBINED,
                 show_eta: bool = True,
                 show_speed: bool = True,
                 update_interval: float = 0.1):
        
        self.state = ProgressState(total=total, start_time=time.time())
        self.title = title
        self.progress_type = progress_type
        self.show_eta = show_eta
        self.show_speed = show_speed
        self.update_interval = update_interval
        self.last_update = 0
        
        # Streamlit 컴포넌트 초기화
        self._init_components()
        
    def _init_components(self):
        """Streamlit 컴포넌트 초기화"""
        if self.progress_type in [ProgressType.BAR, ProgressType.COMBINED]:
            self.progress_bar = st.progress(0)
            
        if self.progress_type in [ProgressType.SPINNER, ProgressType.COMBINED]:
            self.status_container = st.empty()
            
        if self.progress_type in [ProgressType.METRIC, ProgressType.COMBINED]:
            self.metrics_container = st.empty()
            
        self.message_container = st.empty()
        
        if self.show_eta or self.show_speed:
            self.info_container = st.empty()
    
    def update(self, current: int, message: str = ""):
        """진행률 업데이트"""
        current_time = time.time()
        
        # 업데이트 간격 체크 (너무 자주 업데이트하면 성능 저하)
        if current_time - self.last_update < self.update_interval and current < self.state.total:
            return
            
        self.state.current = current
        self.state.message = message
        
        # 진행률 계산
        progress = min(current / self.state.total, 1.0) if self.state.total > 0 else 0
        
        # 속도 및 예상 완료 시간 계산
        elapsed_time = current_time - self.state.start_time
        if elapsed_time > 0 and current > 0:
            self.state.speed = current / elapsed_time
            remaining_items = self.state.total - current
            if self.state.speed > 0:
                self.state.estimated_remaining = remaining_items / self.state.speed
        
        # UI 업데이트
        self._update_ui(progress)
        self.last_update = current_time
    
    def _update_ui(self, progress: float):
        """UI 컴포넌트 업데이트"""
        # 진행률 바 업데이트
        if hasattr(self, 'progress_bar'):
            self.progress_bar.progress(progress)
        
        # 상태 메시지 업데이트
        if hasattr(self, 'status_container'):
            status_msg = f"{self.title}: {self.state.current:,}/{self.state.total:,}"
            if self.state.message:
                status_msg += f" - {self.state.message}"
            self.status_container.text(status_msg)
        
        # 메트릭 업데이트
        if hasattr(self, 'metrics_container'):
            col1, col2, col3 = self.metrics_container.columns(3)
            with col1:
                st.metric("진행률", f"{progress*100:.1f}%")
            with col2:
                st.metric("완료", f"{self.state.current:,}")
            with col3:
                st.metric("전체", f"{self.state.total:,}")
        
        # 추가 정보 업데이트
        if hasattr(self, 'info_container') and (self.show_eta or self.show_speed):
            info_parts = []
            
            if self.show_speed and self.state.speed > 0:
                if self.state.speed >= 1:
                    speed_text = f"{self.state.speed:.1f} 항목/초"
                else:
                    speed_text = f"{60/self.state.speed:.1f} 초/항목"
                info_parts.append(f"속도: {speed_text}")
            
            if self.show_eta and self.state.estimated_remaining > 0:
                eta_text = self._format_time(self.state.estimated_remaining)
                info_parts.append(f"예상 완료: {eta_text}")
            
            elapsed_text = self._format_time(time.time() - self.state.start_time)
            info_parts.append(f"경과: {elapsed_text}")
            
            if info_parts:
                self.info_container.text(" | ".join(info_parts))
    
    def _format_time(self, seconds: float) -> str:
        """시간 포맷팅"""
        if seconds < 60:
            return f"{seconds:.1f}초"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}분 {secs}초"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}시간 {minutes}분"
    
    def complete(self, message: str = "완료!"):
        """처리 완료"""
        self.update(self.state.total, message)
        
        # 완료 메시지 표시
        total_time = time.time() - self.state.start_time
        completion_msg = f"✅ {message} (총 {self._format_time(total_time)})"
        
        if hasattr(self, 'message_container'):
            self.message_container.success(completion_msg)
    
    def error(self, message: str = "오류 발생"):
        """오류 표시"""
        if hasattr(self, 'message_container'):
            self.message_container.error(f"❌ {message}")

@contextmanager
def progress_context(total: int, 
                    title: str = "처리 중...",
                    progress_type: ProgressType = ProgressType.COMBINED,
                    **kwargs):
    """진행률 표시 컨텍스트 매니저"""
    progress = EnhancedProgressBar(total, title, progress_type, **kwargs)
    try:
        yield progress
        progress.complete()
    except Exception as e:
        progress.error(f"처리 중 오류: {str(e)}")
        raise

class MultiStepProgress:
    """다단계 진행률 표시 클래스"""
    
    def __init__(self, steps: List[Dict[str, Any]]):
        """
        steps: [{'name': '단계명', 'weight': 가중치}, ...]
        """
        self.steps = steps
        self.current_step = 0
        self.total_weight = sum(step.get('weight', 1) for step in steps)
        self.step_progress = 0
        
        # UI 컴포넌트
        self.overall_progress = st.progress(0)
        self.step_progress_bar = st.progress(0)
        self.status_container = st.empty()
        self.step_container = st.empty()
        
        self._update_display()
    
    def start_step(self, step_index: int):
        """단계 시작"""
        self.current_step = step_index
        self.step_progress = 0
        self._update_display()
    
    def update_step(self, progress: float, message: str = ""):
        """현재 단계 진행률 업데이트"""
        self.step_progress = min(progress, 1.0)
        
        # 전체 진행률 계산
        completed_weight = sum(
            self.steps[i].get('weight', 1) 
            for i in range(self.current_step)
        )
        current_weight = self.steps[self.current_step].get('weight', 1) * self.step_progress
        overall_progress = (completed_weight + current_weight) / self.total_weight
        
        # UI 업데이트
        self.overall_progress.progress(overall_progress)
        self.step_progress_bar.progress(self.step_progress)
        
        step_name = self.steps[self.current_step]['name']
        status_text = f"단계 {self.current_step + 1}/{len(self.steps)}: {step_name}"
        if message:
            status_text += f" - {message}"
        
        self.status_container.text(status_text)
        
        # 단계별 상태 표시
        self._update_step_display()
    
    def _update_display(self):
        """전체 디스플레이 업데이트"""
        self.update_step(self.step_progress)
    
    def _update_step_display(self):
        """단계별 상태 표시"""
        step_status = []
        for i, step in enumerate(self.steps):
            if i < self.current_step:
                status = "✅"
            elif i == self.current_step:
                status = f"🔄 ({self.step_progress*100:.0f}%)"
            else:
                status = "⏳"
            
            step_status.append(f"{status} {step['name']}")
        
        self.step_container.text(" → ".join(step_status))
    
    def complete_step(self):
        """현재 단계 완료"""
        self.update_step(1.0, "완료")
    
    def complete_all(self, message: str = "모든 단계 완료!"):
        """모든 단계 완료"""
        self.overall_progress.progress(1.0)
        self.step_progress_bar.progress(1.0)
        self.status_container.success(f"✅ {message}")

def create_processing_steps(operations: List[str]) -> List[Dict[str, Any]]:
    """처리 단계 생성 헬퍼 함수"""
    return [{'name': op, 'weight': 1} for op in operations]

# 자주 사용되는 진행률 표시 패턴들
def show_file_processing_progress(total_files: int):
    """파일 처리 진행률 표시"""
    return EnhancedProgressBar(
        total=total_files,
        title="파일 처리",
        progress_type=ProgressType.COMBINED,
        show_eta=True,
        show_speed=True
    )

def show_data_processing_progress(total_rows: int):
    """데이터 처리 진행률 표시"""
    return EnhancedProgressBar(
        total=total_rows,
        title="데이터 처리",
        progress_type=ProgressType.BAR,
        show_eta=True,
        show_speed=True
    )

def show_translation_progress(total_items: int):
    """번역 진행률 표시"""
    return EnhancedProgressBar(
        total=total_items,
        title="번역 처리",
        progress_type=ProgressType.COMBINED,
        show_eta=True,
        show_speed=False  # 번역은 속도가 일정하지 않음
    )

# 진행률 표시 유틸리티 함수들
def estimate_completion_time(current: int, total: int, start_time: float) -> Optional[float]:
    """완료 예상 시간 계산"""
    if current <= 0:
        return None
    
    elapsed = time.time() - start_time
    rate = current / elapsed
    remaining = total - current
    
    return remaining / rate if rate > 0 else None

def format_progress_message(current: int, total: int, item_name: str = "항목") -> str:
    """진행률 메시지 포맷팅"""
    percentage = (current / total * 100) if total > 0 else 0
    return f"{current:,}/{total:,} {item_name} ({percentage:.1f}%)"

def show_memory_usage_progress(current_mb: float, max_mb: float = 1000):
    """메모리 사용량 진행률 표시"""
    percentage = min(current_mb / max_mb, 1.0)
    
    # 색상 결정
    if percentage < 0.7:
        color = "normal"
    elif percentage < 0.9:
        color = "warning"
    else:
        color = "error"
    
    st.metric(
        "메모리 사용량",
        f"{current_mb:.1f}MB",
        f"{percentage*100:.1f}% 사용 중"
    )
    
    if color == "warning":
        st.warning("⚠️ 메모리 사용량이 높습니다.")
    elif color == "error":
        st.error("🚨 메모리 사용량이 위험 수준입니다!")