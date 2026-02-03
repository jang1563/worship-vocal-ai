"""
🎭 보컬 분리 모듈 (Vocal Separator)
====================================

여러 싱어가 섞여 있거나 반주와 함께 녹음된 경우,
분석 대상 보컬만 추출하는 기능입니다.

지원 기술:
1. Demucs (Meta AI) - 로컬 실행, 고품질
2. Spleeter (Deezer) - 빠르고 가벼움
3. LALAL.AI API - 리드/백보컬 분리 (유료)
"""

import os
import sys
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

class SeparationMode(Enum):
    """분리 모드"""
    NONE = "none"               # 분리 안함 (솔로 녹음)
    VOCALS_ONLY = "vocals"      # 보컬 vs 반주
    LEAD_VOCALS = "lead"        # 리드 vs 백보컬 vs 반주
    MULTI_SINGER = "multi"      # 개별 싱어 분리 시도

class SeparationMethod(Enum):
    """분리 방법"""
    DEMUCS = "demucs"           # Meta AI (로컬, 고품질)
    SPLEETER = "spleeter"       # Deezer (로컬, 빠름)
    LALAL_API = "lalal"         # LALAL.AI (API, 리드/백 분리)

@dataclass
class SeparationResult:
    """분리 결과"""
    success: bool
    lead_vocals_path: Optional[str]     # 리드 보컬 파일 경로
    back_vocals_path: Optional[str]     # 백 보컬 파일 경로
    instrumental_path: Optional[str]    # 반주 파일 경로
    confidence: float                   # 분리 품질 신뢰도 (0-1)
    method_used: str                    # 사용된 방법
    message: str                        # 상태 메시지


# =============================================
# 1. Demucs 기반 분리 (권장)
# =============================================

def separate_with_demucs(
    audio_path: str,
    output_dir: str,
    mode: SeparationMode = SeparationMode.VOCALS_ONLY,
    model: str = "htdemucs"
) -> SeparationResult:
    """
    Demucs를 사용한 보컬 분리
    
    Models:
    - htdemucs: 기본 모델 (vocals, drums, bass, other)
    - htdemucs_ft: Fine-tuned 버전 (더 정확)
    - htdemucs_6s: 6-stem (vocals, drums, bass, guitar, piano, other)
    
    Installation:
        pip install demucs
    
    Usage:
        # 터미널에서
        demucs -n htdemucs --two-stems=vocals input.mp3
        
        # 파이썬에서
        import demucs.separate
        demucs.separate.main(["--two-stems", "vocals", "-n", "htdemucs", audio_path])
    """

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 캐시 확인: 이미 분리된 파일이 있으면 재사용
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    expected_vocals = os.path.join(output_dir, model, audio_name, "vocals.wav")
    expected_instrumental = os.path.join(output_dir, model, audio_name, "no_vocals.wav")

    if os.path.exists(expected_vocals) and os.path.exists(expected_instrumental):
        # 파일 크기 확인 (최소 1MB 이상이면 유효한 파일로 간주)
        if os.path.getsize(expected_vocals) > 1024 * 1024:
            print(f"✅ 캐시 사용: {audio_name} (이미 분리된 파일 존재)")
            return SeparationResult(
                success=True,
                lead_vocals_path=expected_vocals,
                back_vocals_path=None,
                instrumental_path=expected_instrumental,
                confidence=0.90,  # 캐시 사용 시 약간 낮은 신뢰도
                method_used="demucs (cached)",
                message="캐시된 분리 파일 사용"
            )

    try:
        # Conda 환경 Python 경로 (ARM64 최적화)
        conda_python = "/Users/jak4013/miniconda3-arm64/envs/worship_vocal/bin/python"

        # MPS(Metal GPU) 사용 가능 여부 확인
        import torch
        device = "mps" if torch.backends.mps.is_available() else "cpu"

        # Demucs 실행 (Conda 환경 + MPS 가속)
        if mode == SeparationMode.VOCALS_ONLY:
            # 보컬 vs 반주만 분리 (더 빠름)
            cmd = [
                conda_python, "-m", "demucs",
                "--two-stems=vocals",
                "-d", device,  # MPS 또는 CPU
                "-n", model,
                "-o", output_dir,
                audio_path
            ]
        else:
            # 전체 stem 분리
            cmd = [
                conda_python, "-m", "demucs",
                "-d", device,
                "-n", model,
                "-o", output_dir,
                audio_path
            ]

        # 오디오 길이 기반 타임아웃 동적 설정
        # MPS에서 처리 시간 ≈ 오디오 길이의 2-3배 + 모델 로딩 시간(5분)
        import librosa
        try:
            duration_seconds = librosa.get_duration(path=audio_path)
        except:
            # 추정: 128kbps MP3 기준
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            duration_seconds = (file_size_mb * 1024 * 1024 * 8) / (128 * 1000)

        # 타임아웃: 오디오 길이의 3배 + 5분 (모델 로딩/시스템 부하 여유)
        timeout_seconds = int(duration_seconds * 3 + 300)
        timeout_seconds = max(timeout_seconds, 900)   # 최소 15분
        timeout_seconds = min(timeout_seconds, 5400)  # 최대 90분

        print(f"🎭 Demucs 분리 중... (모델: {model}, 디바이스: {device})")
        print(f"   Python: {conda_python}")
        print(f"   오디오 길이: {duration_seconds/60:.1f}분, 예상 타임아웃: {timeout_seconds//60}분")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        
        if result.returncode != 0:
            return SeparationResult(
                success=False,
                lead_vocals_path=None,
                back_vocals_path=None,
                instrumental_path=None,
                confidence=0.0,
                method_used="demucs",
                message=f"Demucs 오류: {result.stderr}"
            )
        
        # 출력 파일 경로 찾기
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        stem_dir = os.path.join(output_dir, model, audio_name)
        
        vocals_path = os.path.join(stem_dir, "vocals.wav")
        no_vocals_path = os.path.join(stem_dir, "no_vocals.wav")
        
        return SeparationResult(
            success=True,
            lead_vocals_path=vocals_path if os.path.exists(vocals_path) else None,
            back_vocals_path=None,  # Demucs 기본은 리드/백 분리 안됨
            instrumental_path=no_vocals_path if os.path.exists(no_vocals_path) else None,
            confidence=0.85,  # Demucs 평균 품질
            method_used="demucs",
            message="✅ 보컬 분리 완료!"
        )
        
    except FileNotFoundError:
        return SeparationResult(
            success=False,
            lead_vocals_path=None,
            back_vocals_path=None,
            instrumental_path=None,
            confidence=0.0,
            method_used="demucs",
            message="❌ Demucs가 설치되지 않았습니다. 'pip install demucs'를 실행해주세요."
        )


# =============================================
# 2. Spleeter 기반 분리 (빠름)
# =============================================

def separate_with_spleeter(
    audio_path: str,
    output_dir: str,
    stems: int = 2
) -> SeparationResult:
    """
    Spleeter를 사용한 보컬 분리
    
    Stems:
    - 2: vocals + accompaniment
    - 4: vocals + drums + bass + other
    - 5: vocals + drums + bass + piano + other
    
    Installation:
        pip install spleeter
    
    Usage:
        spleeter separate -p spleeter:2stems -o output input.mp3
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        cmd = [
            "spleeter", "separate",
            "-p", f"spleeter:{stems}stems",
            "-o", output_dir,
            audio_path
        ]
        
        print(f"🎭 Spleeter 분리 중... ({stems}stems)")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return SeparationResult(
                success=False,
                lead_vocals_path=None,
                back_vocals_path=None,
                instrumental_path=None,
                confidence=0.0,
                method_used="spleeter",
                message=f"Spleeter 오류: {result.stderr}"
            )
        
        # 출력 파일 경로
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        stem_dir = os.path.join(output_dir, audio_name)
        
        vocals_path = os.path.join(stem_dir, "vocals.wav")
        accompaniment_path = os.path.join(stem_dir, "accompaniment.wav")
        
        return SeparationResult(
            success=True,
            lead_vocals_path=vocals_path if os.path.exists(vocals_path) else None,
            back_vocals_path=None,
            instrumental_path=accompaniment_path if os.path.exists(accompaniment_path) else None,
            confidence=0.75,  # Spleeter는 Demucs보다 약간 낮음
            method_used="spleeter",
            message="✅ 보컬 분리 완료!"
        )
        
    except FileNotFoundError:
        return SeparationResult(
            success=False,
            lead_vocals_path=None,
            back_vocals_path=None,
            instrumental_path=None,
            confidence=0.0,
            method_used="spleeter",
            message="❌ Spleeter가 설치되지 않았습니다. 'pip install spleeter'를 실행해주세요."
        )


# =============================================
# 3. 리드/백보컬 분리 (고급)
# =============================================

"""
리드 보컬과 백 보컬을 분리하려면:

방법 1: LALAL.AI API (권장)
- https://www.lalal.ai/lead-back-vocals-remover/
- 유료이지만 가장 정확
- API 호출로 자동화 가능

방법 2: 2단계 Demucs
1. 먼저 보컬 전체 분리
2. 분리된 보컬에서 다시 처리 (실험적)

방법 3: Medley Vox (실험적)
- https://mvsep.com/en
- 여러 싱어 분리 전용
- 아직 품질이 일정하지 않음
"""

def separate_lead_and_back_vocals(
    audio_path: str,
    output_dir: str,
    method: str = "demucs_two_stage"
) -> SeparationResult:
    """
    리드 보컬과 백 보컬 분리 시도 (실험적)
    
    이 기능은 완벽하지 않습니다.
    가장 좋은 방법은 솔로 녹음을 따로 받는 것입니다.
    """
    
    if method == "lalal_api":
        # LALAL.AI API 사용 (별도 구현 필요)
        return SeparationResult(
            success=False,
            lead_vocals_path=None,
            back_vocals_path=None,
            instrumental_path=None,
            confidence=0.0,
            method_used="lalal_api",
            message="LALAL.AI API 연동이 필요합니다. API 키를 설정해주세요."
        )
    
    # 2단계 Demucs (실험적)
    print("⚠️ 리드/백보컬 분리는 실험적 기능입니다.")
    print("   정확도가 낮을 수 있으며, 솔로 녹음을 권장합니다.")
    
    # 1단계: 보컬 분리
    stage1_result = separate_with_demucs(
        audio_path, 
        os.path.join(output_dir, "stage1"),
        mode=SeparationMode.VOCALS_ONLY
    )
    
    if not stage1_result.success:
        return stage1_result
    
    # 분리된 보컬 파일 반환 (리드/백 구분은 수동으로)
    return SeparationResult(
        success=True,
        lead_vocals_path=stage1_result.lead_vocals_path,
        back_vocals_path=None,  # 자동 분리 어려움
        instrumental_path=stage1_result.instrumental_path,
        confidence=0.6,  # 신뢰도 낮음 표시
        method_used="demucs_two_stage",
        message="⚠️ 보컬은 분리되었지만, 리드/백 구분은 수동 확인이 필요합니다."
    )


# =============================================
# 4. 통합 인터페이스
# =============================================

def auto_separate(
    audio_path: str,
    output_dir: str,
    mode: SeparationMode = SeparationMode.VOCALS_ONLY,
    preferred_method: SeparationMethod = SeparationMethod.DEMUCS
) -> SeparationResult:
    """
    상황에 맞는 최적의 분리 방법 자동 선택
    
    Args:
        audio_path: 입력 오디오 파일
        output_dir: 출력 디렉토리
        mode: 분리 모드
        preferred_method: 선호하는 방법
    
    Returns:
        SeparationResult
    """
    
    print(f"🎵 입력: {audio_path}")
    print(f"📁 출력: {output_dir}")
    print(f"🎯 모드: {mode.value}")
    
    # 분리 안함 모드
    if mode == SeparationMode.NONE:
        return SeparationResult(
            success=True,
            lead_vocals_path=audio_path,
            back_vocals_path=None,
            instrumental_path=None,
            confidence=1.0,
            method_used="none",
            message="솔로 녹음 - 분리 없이 진행"
        )
    
    # 리드/백 분리 모드
    if mode == SeparationMode.LEAD_VOCALS:
        return separate_lead_and_back_vocals(audio_path, output_dir)
    
    # 보컬 분리 모드
    if preferred_method == SeparationMethod.DEMUCS:
        result = separate_with_demucs(audio_path, output_dir, mode)
        if result.success:
            return result
        # 실패시 Spleeter로 폴백
        print("⚠️ Demucs 실패, Spleeter로 시도...")
        return separate_with_spleeter(audio_path, output_dir)
    
    elif preferred_method == SeparationMethod.SPLEETER:
        result = separate_with_spleeter(audio_path, output_dir)
        if result.success:
            return result
        # 실패시 Demucs로 폴백
        print("⚠️ Spleeter 실패, Demucs로 시도...")
        return separate_with_demucs(audio_path, output_dir, mode)
    
    return SeparationResult(
        success=False,
        lead_vocals_path=None,
        back_vocals_path=None,
        instrumental_path=None,
        confidence=0.0,
        method_used="none",
        message="❌ 지원되지 않는 분리 방법입니다."
    )


# =============================================
# 5. 사용자 가이드
# =============================================

USER_GUIDE = """
🎭 보컬 분리 가이드
==================

📌 녹음 상황별 권장 설정:

┌─────────────────────────────────────────────────────────────────┐
│ 상황                        │ 권장 모드      │ 정확도          │
├─────────────────────────────────────────────────────────────────┤
│ 🎤 솔로 녹음 (나만 녹음됨)    │ NONE          │ ⭐⭐⭐⭐⭐ 100%   │
│ 🎹 반주 + 내 목소리           │ VOCALS_ONLY   │ ⭐⭐⭐⭐ 85%     │
│ 👥 찬양팀과 함께 (내가 메인)   │ VOCALS_ONLY   │ ⭐⭐⭐⭐ 80%     │
│ 🎵 여러 싱어 중 하나          │ LEAD_VOCALS   │ ⭐⭐⭐ 60%       │
│ 🎼 전체 밴드 녹음             │ VOCALS_ONLY   │ ⭐⭐⭐ 70%       │
└─────────────────────────────────────────────────────────────────┘

💡 팁:
1. 가장 좋은 방법은 "솔로 녹음"을 따로 받는 것입니다.
2. 찬양팀 녹음이라면, 가능하면 메인 인도자 마이크 트랙을 따로 받으세요.
3. 보컬 분리 후 품질이 낮다면, 신뢰도를 확인하고 결과 해석에 참고하세요.
4. 분리된 보컬에 잡음이 많으면 분석 정확도가 떨어질 수 있습니다.

🔧 설치 방법:

# Demucs (권장)
pip install demucs

# Spleeter
pip install spleeter

# 둘 다 설치 권장 (폴백용)
pip install demucs spleeter
"""


# =============================================
# 6. 테스트
# =============================================

def test_separation_info():
    """분리 기능 정보 출력"""
    print(USER_GUIDE)
    
    print("\n🔍 설치 상태 확인...")
    
    # Demucs 확인
    try:
        result = subprocess.run(["demucs", "--help"], capture_output=True)
        print("✅ Demucs: 설치됨")
    except FileNotFoundError:
        print("❌ Demucs: 설치 안됨 (pip install demucs)")
    
    # Spleeter 확인
    try:
        result = subprocess.run(["spleeter", "--help"], capture_output=True)
        print("✅ Spleeter: 설치됨")
    except FileNotFoundError:
        print("❌ Spleeter: 설치 안됨 (pip install spleeter)")


if __name__ == "__main__":
    test_separation_info()
