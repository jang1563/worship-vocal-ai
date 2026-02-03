"""
Worship Vocal AI E2E Test
=========================
자동화된 E2E 테스트 스크립트
"""

import sys
import os
from datetime import datetime

# 테스트 결과 저장
RESULTS = {
    "passed": [],
    "failed": [],
    "skipped": []
}

def log_pass(test_name, detail=""):
    RESULTS["passed"].append(test_name)
    print(f"  ✅ {test_name}" + (f" - {detail}" if detail else ""))

def log_fail(test_name, error=""):
    RESULTS["failed"].append((test_name, error))
    print(f"  ❌ {test_name}" + (f" - {error}" if error else ""))

def log_skip(test_name, reason=""):
    RESULTS["skipped"].append((test_name, reason))
    print(f"  ⏭️ {test_name}" + (f" - {reason}" if reason else ""))

# =============================================
# 1. 모듈 임포트 테스트
# =============================================
print("\n" + "="*60)
print("🧪 1. 모듈 임포트 테스트")
print("="*60)

try:
    import streamlit as st
    log_pass("streamlit 임포트")
except ImportError as e:
    log_fail("streamlit 임포트", str(e))

try:
    import numpy as np
    log_pass("numpy 임포트")
except ImportError as e:
    log_fail("numpy 임포트", str(e))

try:
    import librosa
    log_pass("librosa 임포트")
except ImportError as e:
    log_fail("librosa 임포트", str(e))

try:
    import plotly.graph_objects as go
    log_pass("plotly 임포트")
except ImportError as e:
    log_fail("plotly 임포트", str(e))

try:
    from fpdf import FPDF
    log_pass("fpdf2 임포트")
except ImportError as e:
    log_fail("fpdf2 임포트", str(e))

try:
    from PIL import Image, ImageDraw, ImageFont
    log_pass("Pillow 임포트")
except ImportError as e:
    log_fail("Pillow 임포트", str(e))

# =============================================
# 2. 프로젝트 모듈 테스트
# =============================================
print("\n" + "="*60)
print("🧪 2. 프로젝트 모듈 테스트")
print("="*60)

try:
    from vocal_mbti import VocalFeatures, classify_vocal_type, VOCAL_TYPES, calculate_scorecard
    log_pass("vocal_mbti 모듈", f"VOCAL_TYPES: {len(VOCAL_TYPES)}개 유형")
except ImportError as e:
    log_fail("vocal_mbti 모듈", str(e))

try:
    from vocal_separator import auto_separate, SeparationMode, SeparationResult
    log_pass("vocal_separator 모듈")
except ImportError as e:
    log_fail("vocal_separator 모듈", str(e))

try:
    from components.pdf_report import generate_vocal_report_pdf, VocalReportPDF
    log_pass("pdf_report 모듈")
except ImportError as e:
    log_fail("pdf_report 모듈", str(e))

try:
    from components.share_image import create_persona_card_image
    log_pass("share_image 모듈")
except ImportError as e:
    log_fail("share_image 모듈", str(e))

try:
    from emotional_interpreter import generate_local_feedback
    log_pass("emotional_interpreter 모듈")
except ImportError as e:
    log_fail("emotional_interpreter 모듈", str(e))

try:
    from llm_analyzer import analyze_single_with_llm
    log_pass("llm_analyzer 모듈")
except ImportError as e:
    log_fail("llm_analyzer 모듈", str(e))

# =============================================
# 3. app.py 상수 테스트
# =============================================
print("\n" + "="*60)
print("🧪 3. app.py P0/P1/P2 상수 테스트")
print("="*60)

try:
    # app.py 파일 읽기
    with open("app.py", "r") as f:
        app_content = f.read()

    # P0 상수 확인
    if "TERM_TRANSLATIONS" in app_content:
        log_pass("P0: TERM_TRANSLATIONS 정의됨")
    else:
        log_fail("P0: TERM_TRANSLATIONS 없음")

    if "TERM_HELP" in app_content:
        log_pass("P0: TERM_HELP 정의됨")
    else:
        log_fail("P0: TERM_HELP 없음")

    if "PERCENTILE_THRESHOLDS" in app_content:
        log_pass("P0: PERCENTILE_THRESHOLDS 정의됨")
    else:
        log_fail("P0: PERCENTILE_THRESHOLDS 없음")

    if "ANALYSIS_STEPS" in app_content:
        log_pass("P0: ANALYSIS_STEPS 정의됨")
    else:
        log_fail("P0: ANALYSIS_STEPS 없음")

    if "first_visit" in app_content:
        log_pass("P0: 온보딩 가이드 (first_visit)")
    else:
        log_fail("P0: 온보딩 가이드 없음")

    # P1 상수 확인
    if "analysis_history" in app_content:
        log_pass("P1: 분석 히스토리")
    else:
        log_fail("P1: 분석 히스토리 없음")

    if "다음에 해볼 것" in app_content:
        log_pass("P1: 다음에 해볼 것 가이드")
    else:
        log_fail("P1: 다음에 해볼 것 가이드 없음")

    if "녹음 환경 설명" in app_content:
        log_pass("P1: 옵션 설명 강화")
    else:
        log_fail("P1: 옵션 설명 강화 없음")

    # P2 상수 확인
    if "team_profiles" in app_content:
        log_pass("P2: 팀원 프로필 관리")
    else:
        log_fail("P2: 팀원 프로필 관리 없음")

    if "팀원 비교" in app_content:
        log_pass("P2: 팀원 비교 차트")
    else:
        log_fail("P2: 팀원 비교 차트 없음")

except Exception as e:
    log_fail("app.py 읽기 실패", str(e))

# =============================================
# 4. 알고리즘 테스트
# =============================================
print("\n" + "="*60)
print("🧪 4. 알고리즘 테스트")
print("="*60)

try:
    with open("app.py", "r") as f:
        app_content = f.read()

    # 리듬 오프셋 실측
    if "onset_env = librosa.onset.onset_strength" in app_content:
        log_pass("알고리즘: 리듬 오프셋 실측 (onset-beat)")
    else:
        log_fail("알고리즘: 리듬 오프셋 실측 없음")

    # 발음 명료도
    if "spectral_flux" in app_content and "articulation_clarity" in app_content:
        log_pass("알고리즘: 발음 명료도 (spectral flux)")
    else:
        log_fail("알고리즘: 발음 명료도 없음")

    # 비브라토 분석
    if "vibrato_rate" in app_content and "is_intentional_vibrato" in app_content:
        log_pass("알고리즘: 비브라토 분석")
    else:
        log_fail("알고리즘: 비브라토 분석 없음")

    # 고음 안정성 (수정된 기준)
    if "4.0" in app_content and "high_notes_std_semitones" in app_content:
        log_pass("알고리즘: 고음 안정성 (4.0 반음 기준)")
    else:
        log_fail("알고리즘: 고음 안정성 기준 미수정")

except Exception as e:
    log_fail("알고리즘 테스트 실패", str(e))

# =============================================
# 5. vocal_separator.py 타임아웃 테스트
# =============================================
print("\n" + "="*60)
print("🧪 5. Demucs 타임아웃 설정 테스트")
print("="*60)

try:
    with open("vocal_separator.py", "r") as f:
        sep_content = f.read()

    if "librosa.get_duration" in sep_content:
        log_pass("타임아웃: 오디오 길이 기반 (librosa)")
    else:
        log_fail("타임아웃: 오디오 길이 기반 없음")

    if "duration_seconds * 3 + 300" in sep_content:
        log_pass("타임아웃: 공식 (길이*3 + 5분)")
    else:
        log_fail("타임아웃: 공식 미적용")

    if "max(timeout_seconds, 900)" in sep_content:
        log_pass("타임아웃: 최소 15분")
    else:
        log_fail("타임아웃: 최소값 미설정")

    if "min(timeout_seconds, 5400)" in sep_content:
        log_pass("타임아웃: 최대 90분")
    else:
        log_fail("타임아웃: 최대값 미설정")

except Exception as e:
    log_fail("vocal_separator.py 테스트 실패", str(e))

# =============================================
# 6. PDF 리포트 기능 테스트
# =============================================
print("\n" + "="*60)
print("🧪 6. PDF 리포트 기능 테스트")
print("="*60)

try:
    from components.pdf_report import generate_vocal_report_pdf

    # 테스트 데이터
    test_scorecard = {
        "intimacy": 0.7,
        "dynamics": 0.6,
        "tone": 0.8,
        "leading": 0.5,
        "sustain": 0.65,
        "expression": 0.75
    }
    test_features = {
        "pitch_accuracy_cents": 18.5,
        "high_note_stability": 0.72,
        "dynamic_range_db": 15.2,
        "pitch_mean": 220,
        "avg_phrase_length": 4.2,
        "vibrato_ratio": 0.35,
        "rhythm_offset_ms": 32
    }

    pdf_bytes = generate_vocal_report_pdf(
        style_name="친밀한 기도 인도자",
        style_name_en="Intimate Prayer Leader",
        icon="🕊️",
        description="따뜻하고 친밀한 음색으로 회중을 인도합니다.",
        strengths=["회중의 마음을 여는 능력", "기도 분위기 조성"],
        best_fit=["소그룹 예배", "기도회"],
        scorecard=test_scorecard,
        features=test_features,
        coaching_text="테스트 코칭 피드백입니다.",
        matching_songs=["테스트 찬양 1", "테스트 찬양 2"],
        challenge_songs=["도전 찬양 1"]
    )

    if pdf_bytes and len(pdf_bytes) > 100:
        log_pass("PDF 생성", f"{len(pdf_bytes)} bytes")
    else:
        log_fail("PDF 생성", "빈 파일 또는 너무 작음")

except Exception as e:
    log_fail("PDF 리포트 테스트", str(e))

# =============================================
# 7. SNS 이미지 생성 테스트
# =============================================
print("\n" + "="*60)
print("🧪 7. SNS 이미지 생성 테스트")
print("="*60)

try:
    from components.share_image import create_persona_card_image

    test_dimension_scores = {
        "intimacy": 0.7,
        "dynamics": 0.6,
        "tone": 0.8,
        "leading": 0.5,
        "sustain": 0.65,
        "expression": 0.75
    }

    img_bytes = create_persona_card_image(
        style_name="친밀한 기도 인도자",
        style_name_en="Intimate Prayer Leader",
        icon="P",  # 심볼로 대체
        description="따뜻하고 친밀한 음색으로 회중을 인도합니다.",
        strengths=["회중의 마음을 여는 능력", "기도 분위기 조성"],
        best_fit_contexts=["소그룹 예배", "기도회"],
        dimension_scores=test_dimension_scores
    )

    if img_bytes and len(img_bytes) > 1000:
        log_pass("SNS 이미지 생성", f"{len(img_bytes)} bytes")
    else:
        log_fail("SNS 이미지 생성", "빈 파일 또는 너무 작음")

except Exception as e:
    log_fail("SNS 이미지 테스트", str(e))

# =============================================
# 8. VOCAL_TYPES 구조 테스트
# =============================================
print("\n" + "="*60)
print("🧪 8. VOCAL_TYPES 구조 테스트")
print("="*60)

try:
    from vocal_mbti import VOCAL_TYPES

    # 실제 VocalType 필드: code, name_en, name_kr, description, strengths, weaknesses, role_models, practice_focus
    required_fields = ['name_kr', 'name_en', 'description', 'strengths', 'weaknesses', 'role_models', 'practice_focus']

    for type_code, type_info in VOCAL_TYPES.items():
        missing = [f for f in required_fields if not hasattr(type_info, f)]
        if missing:
            log_fail(f"VOCAL_TYPES[{type_code}]", f"누락 필드: {missing}")
        else:
            log_pass(f"VOCAL_TYPES[{type_code}]", type_info.name_kr)

except Exception as e:
    log_fail("VOCAL_TYPES 구조 테스트", str(e))

# =============================================
# 결과 요약
# =============================================
print("\n" + "="*60)
print("📊 테스트 결과 요약")
print("="*60)

total = len(RESULTS["passed"]) + len(RESULTS["failed"]) + len(RESULTS["skipped"])
passed = len(RESULTS["passed"])
failed = len(RESULTS["failed"])
skipped = len(RESULTS["skipped"])

print(f"\n총 {total}개 테스트")
print(f"  ✅ 통과: {passed}")
print(f"  ❌ 실패: {failed}")
print(f"  ⏭️ 스킵: {skipped}")

if failed > 0:
    print("\n❌ 실패한 테스트:")
    for test_name, error in RESULTS["failed"]:
        print(f"  - {test_name}: {error}")

success_rate = (passed / total * 100) if total > 0 else 0
print(f"\n🎯 성공률: {success_rate:.1f}%")

if success_rate >= 90:
    print("\n🎉 E2E 테스트 통과!")
elif success_rate >= 70:
    print("\n⚠️ 일부 테스트 실패 - 확인 필요")
else:
    print("\n🚨 주요 테스트 실패 - 수정 필요")

# 종료 코드
sys.exit(0 if failed == 0 else 1)
