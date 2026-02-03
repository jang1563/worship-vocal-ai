"""
💝 감성 해석 레이어 (Emotional Interpreter)
============================================

숫자와 데이터를 따뜻하고 영감을 주는 피드백으로 변환합니다.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json

# =============================================
# 1. 데이터 → 감성 번역 매핑
# =============================================

EMOTIONAL_TRANSLATIONS = {
    # ─────────────────────────────────────────
    # 음색 (Spectral Centroid) 해석
    # ─────────────────────────────────────────
    "tone": {
        "warm": {
            "range": (0, 1800),
            "poetic": "첼로처럼 깊고 따뜻한 울림",
            "technical": "저주파 대역이 풍부한 음색",
            "feedback": "당신의 따뜻한 음색이 회중의 마음을 편안하게 열어줍니다."
        },
        "balanced": {
            "range": (1800, 2200),
            "poetic": "균형 잡힌, 누구에게나 친숙한 목소리",
            "technical": "중립적인 스펙트럼 분포",
            "feedback": "어떤 곡이든 자연스럽게 소화하는 유연한 음색입니다."
        },
        "bright": {
            "range": (2200, 5000),
            "poetic": "맑고 투명한, 아침 햇살 같은 음색",
            "technical": "고주파 대역이 강조된 음색",
            "feedback": "밝은 에너지가 예배 공간을 환하게 채웁니다."
        }
    },
    
    # ─────────────────────────────────────────
    # 음정 정확도 해석
    # ─────────────────────────────────────────
    "pitch_accuracy": {
        "excellent": {
            "range": (0, 15),
            "grade": "A",
            "poetic": "흔들림 없이 정확한, 신뢰를 주는 음정",
            "feedback": "음정이 매우 안정적입니다. 회중이 편안하게 따라부를 수 있어요."
        },
        "good": {
            "range": (15, 25),
            "grade": "B",
            "poetic": "자연스럽게 흔들리는, 인간적인 따뜻함",
            "feedback": "전반적으로 좋습니다. 감정이 실린 부분에서 살짝 흔들리는 건 오히려 매력이 될 수 있어요."
        },
        "developing": {
            "range": (25, 40),
            "grade": "C",
            "poetic": "마음이 앞서가는, 열정적인 표현",
            "feedback": "진심은 충분히 느껴집니다. 피아노와 함께 연습하면 더 안정될 거예요."
        },
        "needs_work": {
            "range": (40, 100),
            "grade": "D",
            "poetic": "아직 다듬어지지 않은 원석",
            "feedback": "음정 연습이 필요해요. 하지만 걱정마세요, 누구나 처음엔 그렇습니다."
        }
    },
    
    # ─────────────────────────────────────────
    # 음정 경향 해석
    # ─────────────────────────────────────────
    "pitch_tendency": {
        "sharp": {
            "poetic": "약간 긴장되고 흥분된 상태",
            "cause": "흥분하거나 긴장할 때 음이 높아지는 경향",
            "feedback": "음정이 살짝 높게 가는 경향이 있어요. 어깨 힘을 빼고, 호흡을 낮추어 보세요.",
            "exercise": "눈을 감고 천천히 복식호흡을 한 후 시작해보세요."
        },
        "flat": {
            "poetic": "호흡이 뒤로 빠지는 느낌",
            "cause": "호흡 지지가 약해지면서 음이 내려가는 경향",
            "feedback": "음정이 살짝 낮게 가는 경향이 있어요. 배에서 소리를 밀어올려 주세요.",
            "exercise": "플랭크 자세로 발성하거나, 서서 코어에 힘을 주고 불러보세요."
        },
        "neutral": {
            "poetic": "균형 잡힌 음정 컨트롤",
            "feedback": "음정 균형이 좋습니다! 현재 상태를 유지하세요."
        }
    },
    
    # ─────────────────────────────────────────
    # 다이나믹 레인지 해석
    # ─────────────────────────────────────────
    "dynamics": {
        "narrow": {
            "range": (0, 10),
            "poetic": "일관된, 명상적인 톤",
            "feedback": "안정적인 볼륨이지만, 강약을 더 넣으면 찬양이 더 풍성해질 거예요.",
            "suggestion": "후렴에서 10% 더 밀어붙이고, 절에서 10% 더 빼보세요."
        },
        "moderate": {
            "range": (10, 18),
            "poetic": "자연스러운 숨결의 파도",
            "feedback": "적절한 강약 표현이 있습니다. 클라이맥스에서 조금 더 과감해도 좋아요.",
            "suggestion": "가장 감동적인 구간에서 볼륨을 살짝 더 높여보세요."
        },
        "wide": {
            "range": (18, 40),
            "poetic": "폭풍과 고요함을 오가는 드라마틱한 표현",
            "feedback": "강약 표현이 탁월합니다! 회중의 감정을 잘 이끌 수 있어요.",
            "suggestion": "현재 표현력을 유지하면서, 부드러운 부분의 디테일을 더해보세요."
        }
    },
    
    # ─────────────────────────────────────────
    # 호흡 관련 해석
    # ─────────────────────────────────────────
    "breath": {
        "excellent": {
            "range": (6, 100),
            "poetic": "깊은 우물에서 길어올리는 물처럼",
            "feedback": "호흡 지지가 훌륭합니다. 긴 프레이즈도 안정적으로 유지해요."
        },
        "good": {
            "range": (4, 6),
            "poetic": "대체로 안정적이지만 가끔 출렁이는",
            "feedback": "호흡이 좋은 편이에요. 긴 프레이즈 끝에서 약해지지 않도록 연습해보세요."
        },
        "developing": {
            "range": (2, 4),
            "poetic": "새처럼 가볍지만 바람에 흔들리는",
            "feedback": "프레이즈가 짧은 편이에요. 복식호흡 연습을 추천드려요.",
            "exercise": "30초 동안 천천히 '쓰' 소리를 내며 숨을 내쉬는 연습을 해보세요."
        },
        "needs_work": {
            "range": (0, 2),
            "poetic": "아직 호흡의 뿌리를 내리는 중",
            "feedback": "호흡 기초 연습이 필요해요. 하지만 이건 가장 빨리 좋아지는 부분이에요!",
            "exercise": "매일 5분씩 복식호흡 연습을 해보세요."
        }
    },
    
    # ─────────────────────────────────────────
    # 비브라토 해석
    # ─────────────────────────────────────────
    "vibrato": {
        "rich": {
            "range": (0.35, 1.0),
            "poetic": "영혼이 떨리는 듯한 풍부한 울림",
            "feedback": "비브라토가 풍부합니다. 가스펠이나 CCM에 잘 어울려요."
        },
        "moderate": {
            "range": (0.15, 0.35),
            "poetic": "적절히 흔들리는 감정의 파도",
            "feedback": "자연스러운 비브라토입니다. 균형이 좋아요."
        },
        "straight": {
            "range": (0, 0.15),
            "poetic": "고요한 수면 위의 잔잔함",
            "feedback": "스트레이트 톤 위주입니다. 의도적이라면 좋지만, 감정 구간에서는 비브라토를 추가해도 좋아요."
        }
    }
}

# =============================================
# 2. 구간별 해석 템플릿
# =============================================

SEGMENT_TEMPLATES = {
    "best_moment": {
        "template": "{time}에서 당신의 가장 아름다운 순간이 담겨 있어요. {reason}",
        "reasons": {
            "stable_high": "고음이 안정적으로 터지면서 감동을 줍니다.",
            "emotional_peak": "감정이 진정성 있게 폭발하는 구간이에요.",
            "natural_tone": "가장 편안하고 자연스러운 톤이 들립니다.",
            "dynamic_contrast": "강약의 대비가 드라마틱해요."
        }
    },
    "growth_point": {
        "template": "{time} 구간에서 {issue} - {suggestion}",
        "issues": {
            "pitch_drop": "음정이 살짝 떨어지는 부분이 있어요",
            "breath_weak": "호흡이 약해지는 느낌이에요",
            "tension": "긴장이 느껴지는 구간이에요"
        },
        "suggestions": {
            "pitch_drop": "배에서 소리를 밀어주세요.",
            "breath_weak": "이 구간 직전에 숨을 더 깊이 들이마셔 보세요.",
            "tension": "어깨를 내리고 턱을 풀어보세요."
        }
    }
}

# =============================================
# 3. LLM 프롬프트 템플릿
# =============================================

FEEDBACK_SYSTEM_PROMPT = """당신은 따뜻하고 격려적인 찬양 보컬 코치입니다.
교회 찬양팀 인도자들을 코칭하며, 기술적 정확성과 영적 깊이를 모두 중요하게 여깁니다.

## 당신의 역할
- 숫자와 데이터를 시적이고 따뜻한 언어로 번역
- 비판보다 격려 중심의 피드백
- 찬양자로서의 정체성 확인과 응원
- 구체적이고 실행 가능한 연습 제안

## 주의사항
- "틀렸다"보다 "이렇게 하면 더 좋아질 거예요"
- 기술 용어는 최소화하고 비유적 표현 사용
- 찬양의 영적 의미도 함께 언급
- 롤모델과의 유사점을 찾아 자신감 부여"""

FEEDBACK_USER_TEMPLATE = """
## 분석 데이터

### 보컬 MBTI
- 타입: {vocal_type} ({vocal_type_kr})
- 설명: {type_description}

### 역량 스코어 (100점 만점)
- 음색: {tone_score}
- 리딩: {leadership_score}
- 리듬: {rhythm_score}
- 전달력: {diction_score}
- 테크닉: {technique_score}

### 상세 데이터
- 음역대: {pitch_range} 옥타브
- 평균 음정: {avg_pitch}
- 음정 정확도: {pitch_accuracy} cents (낮을수록 정확)
- 음정 경향: {pitch_tendency}
- 다이나믹 레인지: {dynamic_range} dB
- 비브라토 비율: {vibrato_ratio}%
- 평균 프레이즈 길이: {phrase_length}초
- 음색: {tone_desc}

### 구간별 분석
{segment_analysis}

## 요청
위 데이터를 바탕으로 다음 형식의 피드백을 작성해주세요:

1. **첫인상** (2-3문장): 따뜻한 인사와 전체적인 느낌
2. **당신의 보컬 아이덴티티**: MBTI 타입의 의미를 시적으로 설명
3. **빛나는 순간들**: 가장 좋았던 2-3 구간, 왜 좋았는지
4. **성장 포인트**: 개선점 2-3가지, 부드럽게 제안
5. **오늘의 연습**: 구체적인 5분 루틴 (3가지)
6. **마무리 격려**: 찬양자로서의 정체성 확인
"""

# =============================================
# 4. 해석 함수들
# =============================================

def interpret_tone(spectral_centroid: float) -> dict:
    """음색 해석"""
    for level, data in EMOTIONAL_TRANSLATIONS["tone"].items():
        if data["range"][0] <= spectral_centroid < data["range"][1]:
            return {
                "level": level,
                "poetic": data["poetic"],
                "technical": data["technical"],
                "feedback": data["feedback"]
            }
    return EMOTIONAL_TRANSLATIONS["tone"]["balanced"]


def interpret_pitch_accuracy(cents: float) -> dict:
    """음정 정확도 해석"""
    for level, data in EMOTIONAL_TRANSLATIONS["pitch_accuracy"].items():
        if data["range"][0] <= cents < data["range"][1]:
            return {
                "level": level,
                "grade": data["grade"],
                "poetic": data["poetic"],
                "feedback": data["feedback"]
            }
    return EMOTIONAL_TRANSLATIONS["pitch_accuracy"]["needs_work"]


def interpret_pitch_tendency(flat_ratio: float, sharp_ratio: float) -> dict:
    """음정 경향 해석"""
    if flat_ratio > sharp_ratio + 0.1:
        return EMOTIONAL_TRANSLATIONS["pitch_tendency"]["flat"]
    elif sharp_ratio > flat_ratio + 0.1:
        return EMOTIONAL_TRANSLATIONS["pitch_tendency"]["sharp"]
    else:
        return EMOTIONAL_TRANSLATIONS["pitch_tendency"]["neutral"]


def interpret_dynamics(dynamic_range: float) -> dict:
    """다이나믹 해석"""
    for level, data in EMOTIONAL_TRANSLATIONS["dynamics"].items():
        if data["range"][0] <= dynamic_range < data["range"][1]:
            return {
                "level": level,
                "poetic": data["poetic"],
                "feedback": data["feedback"],
                "suggestion": data.get("suggestion", "")
            }
    return EMOTIONAL_TRANSLATIONS["dynamics"]["moderate"]


def interpret_breath(phrase_length: float) -> dict:
    """호흡 해석"""
    for level, data in EMOTIONAL_TRANSLATIONS["breath"].items():
        if data["range"][0] <= phrase_length < data["range"][1]:
            return {
                "level": level,
                "poetic": data["poetic"],
                "feedback": data["feedback"],
                "exercise": data.get("exercise", "")
            }
    return EMOTIONAL_TRANSLATIONS["breath"]["developing"]


def interpret_vibrato(vibrato_ratio: float) -> dict:
    """비브라토 해석"""
    for level, data in EMOTIONAL_TRANSLATIONS["vibrato"].items():
        if data["range"][0] <= vibrato_ratio <= data["range"][1]:
            return {
                "level": level,
                "poetic": data["poetic"],
                "feedback": data["feedback"]
            }
    return EMOTIONAL_TRANSLATIONS["vibrato"]["moderate"]


# =============================================
# 5. 종합 해석 생성
# =============================================

@dataclass
class EmotionalFeedback:
    """감성 피드백 결과"""
    # 해석된 개별 요소들
    tone_interpretation: dict
    pitch_interpretation: dict
    tendency_interpretation: dict
    dynamics_interpretation: dict
    breath_interpretation: dict
    vibrato_interpretation: dict
    
    # 종합 피드백 텍스트
    summary: str
    detailed_feedback: str
    exercises: List[dict]


def generate_local_feedback(features, vocal_type_info, scorecard) -> EmotionalFeedback:
    """
    LLM 없이 로컬에서 피드백 생성 (템플릿 기반)
    """
    # 개별 해석
    tone_interp = interpret_tone(features.spectral_centroid_hz)
    pitch_interp = interpret_pitch_accuracy(features.pitch_accuracy_cents)
    tendency_interp = interpret_pitch_tendency(features.flat_tendency, features.sharp_tendency)
    dynamics_interp = interpret_dynamics(features.dynamic_range_db)
    breath_interp = interpret_breath(features.breath_phrase_length)
    vibrato_interp = interpret_vibrato(features.vibrato_ratio)
    
    # 요약 생성
    summary_parts = [
        f"🎭 당신은 **{vocal_type_info.name_kr}** 타입입니다!",
        f"\n{vocal_type_info.description}",
        f"\n\n✨ 음색: {tone_interp['poetic']}",
        f"\n{tone_interp['feedback']}",
    ]
    
    # 강점 추가
    summary_parts.append(f"\n\n💪 **강점**")
    for s in vocal_type_info.strengths[:2]:
        summary_parts.append(f"\n• {s}")
    
    # 성장 포인트 추가
    summary_parts.append(f"\n\n🎯 **성장 포인트**")
    
    # 음정 관련
    if pitch_interp['level'] in ['developing', 'needs_work']:
        summary_parts.append(f"\n• 음정: {pitch_interp['feedback']}")
    
    # 음정 경향 관련
    if tendency_interp.get('cause'):
        summary_parts.append(f"\n• {tendency_interp['feedback']}")
    
    # 호흡 관련
    if breath_interp['level'] in ['developing', 'needs_work']:
        summary_parts.append(f"\n• 호흡: {breath_interp['feedback']}")
    
    summary = "".join(summary_parts)
    
    # 상세 피드백
    detailed_parts = [
        f"## 📊 상세 분석\n",
        f"\n### 음색 분석",
        f"\n{tone_interp['poetic']}",
        f"\n{tone_interp['feedback']}",
        
        f"\n\n### 음정 분석",
        f"\n등급: {pitch_interp['grade']} ({pitch_interp['poetic']})",
        f"\n{pitch_interp['feedback']}",
        
        f"\n\n### 다이나믹 분석",
        f"\n{dynamics_interp['poetic']}",
        f"\n{dynamics_interp['feedback']}",
        
        f"\n\n### 호흡 분석",
        f"\n{breath_interp['poetic']}",
        f"\n{breath_interp['feedback']}",
        
        f"\n\n### 비브라토 분석",
        f"\n{vibrato_interp['poetic']}",
        f"\n{vibrato_interp['feedback']}",
    ]
    
    detailed = "".join(detailed_parts)
    
    # 연습 처방
    exercises = []
    
    # 1. 음정 경향에 따른 연습
    if tendency_interp.get('exercise'):
        exercises.append({
            "name": "호흡 안정화",
            "duration": "1분",
            "description": tendency_interp['exercise']
        })
    
    # 2. 호흡 연습
    if breath_interp.get('exercise'):
        exercises.append({
            "name": "호흡 지지력 강화",
            "duration": "2분",
            "description": breath_interp['exercise']
        })
    else:
        exercises.append({
            "name": "호흡 유지",
            "duration": "2분",
            "description": "'스' 소리를 20초 동안 일정하게 유지하기 × 3회"
        })
    
    # 3. 타입별 맞춤 연습
    for focus in vocal_type_info.practice_focus[:2]:
        if "고음" in focus:
            exercises.append({
                "name": "고음 안정화",
                "duration": "2분",
                "description": "립 트릴로 스케일 올리기. 목에 힘을 빼고 입술 떨림에 집중하세요."
            })
        elif "다이나믹" in focus or "강약" in focus:
            exercises.append({
                "name": "다이나믹 확장",
                "duration": "2분",
                "description": "같은 음을 pp에서 시작해 ff까지 크레센도, 다시 pp로 디크레센도."
            })
        elif "감정" in focus:
            exercises.append({
                "name": "감정 표현",
                "duration": "2분",
                "description": "좋아하는 가사 한 줄을 3가지 감정으로 불러보기 (기쁨, 간절함, 평안)"
            })
    
    return EmotionalFeedback(
        tone_interpretation=tone_interp,
        pitch_interpretation=pitch_interp,
        tendency_interpretation=tendency_interp,
        dynamics_interpretation=dynamics_interp,
        breath_interpretation=breath_interp,
        vibrato_interpretation=vibrato_interp,
        summary=summary,
        detailed_feedback=detailed,
        exercises=exercises[:5]  # 최대 5개
    )


# =============================================
# 6. 테스트
# =============================================

def test_emotional_interpretation():
    """감성 해석 테스트"""
    
    from vocal_mbti import VocalFeatures, classify_vocal_type, VOCAL_TYPES, calculate_scorecard
    
    # 아까 분석한 데이터
    test_features = VocalFeatures(
        pitch_range_semitones=28.4,
        avg_pitch_hz=172.5,
        high_note_ratio=0.158,
        low_note_ratio=0.248,
        dynamic_range_db=14.4,
        energy_variance=0.3,
        climax_intensity=0.7,
        spectral_centroid_hz=1777,
        warmth_score=0.75,
        vibrato_ratio=0.406,
        pitch_stability=0.70,
        pitch_accuracy_cents=20.3,
        tempo_bpm=129,
        breath_phrase_length=3.1,
        flat_tendency=0.406,
        sharp_tendency=0.287
    )
    
    # 분류
    primary_type, scores = classify_vocal_type(test_features)
    vocal_type_info = VOCAL_TYPES[primary_type]
    scorecard = calculate_scorecard(test_features)
    
    # 감성 해석
    feedback = generate_local_feedback(test_features, vocal_type_info, scorecard)
    
    print("=" * 60)
    print("💝 감성 해석 피드백")
    print("=" * 60)
    
    print("\n📋 요약:")
    print(feedback.summary)
    
    print("\n" + "─" * 60)
    print("\n📝 상세 분석:")
    print(feedback.detailed_feedback)
    
    print("\n" + "─" * 60)
    print("\n🎯 오늘의 연습 (5분 루틴):")
    for i, ex in enumerate(feedback.exercises, 1):
        print(f"\n{i}. {ex['name']} ({ex['duration']})")
        print(f"   {ex['description']}")
    
    return feedback


if __name__ == "__main__":
    test_emotional_interpretation()
