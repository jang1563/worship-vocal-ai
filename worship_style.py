"""
Worship Vocal Style Characterization System
찬양 예배 보컬 스타일 특성화 시스템

평가보다는 "당신의 스타일은 이렇습니다"라는 가이드 제공
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum


class StyleDimension(Enum):
    """찬양 보컬 스타일 차원"""
    INTIMACY = "intimacy"           # 친밀감 vs 선포력
    DYNAMICS = "dynamics"           # 명상적 vs 역동적
    TONE = "tone"                   # 밝은 vs 따뜻한
    LEADING = "leading"             # 자유로운 vs 구조적
    SUSTAIN = "sustain"             # 짧은 프레이즈 vs 긴 프레이즈
    EXPRESSION = "expression"       # 절제된 vs 감정적


@dataclass
class StyleAxis:
    """스타일 축 정의"""
    dimension: StyleDimension
    low_label: str          # 낮은 값의 라벨
    high_label: str         # 높은 값의 라벨
    low_icon: str
    high_icon: str
    worship_context_low: str   # 낮은 값의 예배 맥락
    worship_context_high: str  # 높은 값의 예배 맥락


# 찬양 예배 특화 스타일 축 정의
WORSHIP_STYLE_AXES = {
    StyleDimension.INTIMACY: StyleAxis(
        dimension=StyleDimension.INTIMACY,
        low_label="친밀한 기도형",
        high_label="선포적 찬양형",
        low_icon="🕊️",
        high_icon="🔥",
        worship_context_low="소그룹 예배, 기도 인도, 개인 묵상 찬양",
        worship_context_high="대규모 집회, 선포 찬양, 영적 전쟁 찬양"
    ),
    StyleDimension.DYNAMICS: StyleAxis(
        dimension=StyleDimension.DYNAMICS,
        low_label="명상적/고요한",
        high_label="역동적/파워풀",
        low_icon="🌙",
        high_icon="⚡",
        worship_context_low="묵상 시간, 성찬식, 치유 예배",
        worship_context_high="찬양 절정, 승리 선포, 축제 예배"
    ),
    StyleDimension.TONE: StyleAxis(
        dimension=StyleDimension.TONE,
        low_label="밝고 청명한",
        high_label="따뜻하고 깊은",
        low_icon="✨",
        high_icon="🎸",
        worship_context_low="새벽 예배, 부활절, 기쁨의 찬양",
        worship_context_high="저녁 예배, 성탄절, 위로의 찬양"
    ),
    StyleDimension.LEADING: StyleAxis(
        dimension=StyleDimension.LEADING,
        low_label="자유로운/즉흥적",
        high_label="구조적/안정적",
        low_icon="🌊",
        high_icon="⚓",
        worship_context_low="자유 찬양, 방언 찬양, 즉흥 인도",
        worship_context_high="정규 예배, 새신자 환영, 찬송가 인도"
    ),
    StyleDimension.SUSTAIN: StyleAxis(
        dimension=StyleDimension.SUSTAIN,
        low_label="짧고 리드미컬한",
        high_label="길고 서정적인",
        low_icon="💨",
        high_icon="🌬️",
        worship_context_low="CCM, 가스펠, 업템포 찬양",
        worship_context_high="발라드 찬양, 성가, 묵상 찬양"
    ),
    StyleDimension.EXPRESSION: StyleAxis(
        dimension=StyleDimension.EXPRESSION,
        low_label="절제된/담담한",
        high_label="감정적/열정적",
        low_icon="🪨",
        high_icon="💧",
        worship_context_low="말씀 찬양, 교리적 찬송, 송축 찬양",
        worship_context_high="고백 찬양, 헌신 찬양, 간구 찬양"
    ),
}


@dataclass
class WorshipVocalStyle:
    """예배 보컬 스타일 결과"""
    style_name: str
    style_name_en: str
    icon: str
    description: str
    strengths: List[str]
    best_fit_contexts: List[str]
    recommended_songs: List[str]
    growth_areas: List[str]
    dimension_scores: Dict[StyleDimension, float]  # 0-1


# 대표 스타일 유형 (조합 패턴)
WORSHIP_STYLE_ARCHETYPES = {
    "intimate_prayer": {
        "name": "친밀한 기도 인도자",
        "name_en": "Intimate Prayer Leader",
        "icon": "🕊️",
        "pattern": {"intimacy": "low", "dynamics": "low", "expression": "mid"},
        "description": "따뜻하고 친밀한 음색으로 회중을 하나님 앞으로 인도합니다. 개인적인 기도와 고백의 순간에 특히 빛나며, 조용히 마음을 열게 하는 힘이 있습니다.",
        "strengths": ["회중의 마음을 여는 능력", "기도 분위기 조성", "친밀한 가사 전달"],
        "best_fit": ["소그룹 예배", "기도회", "치유 집회", "새벽 예배"],
        "songs": ["주님의 사랑을 (박지현)", "아버지의 편지 (이영훈)", "그 사랑 얼마나 (김윤진)"],
        "growth": ["대규모 집회에서 존재감 키우기", "다이나믹 폭 넓히기"]
    },
    "proclamation_leader": {
        "name": "선포적 찬양 인도자",
        "name_en": "Proclamation Leader",
        "icon": "🔥",
        "pattern": {"intimacy": "high", "dynamics": "high", "expression": "high"},
        "description": "강력한 선포와 파워풀한 다이나믹으로 영적 분위기를 주도합니다. 찬양의 절정에서 회중을 하나로 묶고, 영적 선포의 순간에 앞장섭니다.",
        "strengths": ["강력한 존재감", "분위기 전환 능력", "회중 에너지 고양"],
        "best_fit": ["대규모 집회", "부흥회", "청년 예배", "축제 예배"],
        "songs": ["나의 피난처 예수 (레위지파)", "승리하신 주 (마커스)", "주 이름 높이세"],
        "growth": ["조용한 순간의 섬세함", "지속 가능한 발성 관리"]
    },
    "balanced_shepherd": {
        "name": "균형잡힌 목양 인도자",
        "name_en": "Balanced Shepherd",
        "icon": "⚓",
        "pattern": {"leading": "high", "sustain": "mid", "expression": "mid"},
        "description": "안정적이고 구조적인 인도로 회중이 편안하게 따라올 수 있게 합니다. 다양한 상황에서 유연하게 대응하며, 예배의 흐름을 자연스럽게 이끕니다.",
        "strengths": ["안정적인 인도력", "회중 친화적 발성", "다양한 장르 소화"],
        "best_fit": ["주일 예배", "새신자 환영 예배", "가정 예배", "연합 예배"],
        "songs": ["은혜 (박지민)", "내가 매일 기쁘게 (전통찬송)", "주님 다시 오실 때까지"],
        "growth": ["개성 있는 표현 개발", "즉흥 인도 능력"]
    },
    "free_flow": {
        "name": "자유로운 흐름 인도자",
        "name_en": "Free Flow Leader",
        "icon": "🌊",
        "pattern": {"leading": "low", "expression": "high", "dynamics": "mid"},
        "description": "즉흥적이고 자유로운 표현으로 예배의 흐름에 민감하게 반응합니다. 예상치 못한 은혜의 순간을 만들어내며, 회중에게 새로운 경험을 선사합니다.",
        "strengths": ["즉흥 인도 능력", "흐름 민감성", "창의적 표현"],
        "best_fit": ["자유 찬양 시간", "기도 응답 찬양", "영성 집회", "청년 수련회"],
        "songs": ["하나님의 은혜 (자유선율)", "주님 여기 (즉흥)", "기도 중 찬양 인도"],
        "growth": ["구조적 인도 연습", "일관성 있는 음정 유지"]
    },
    "lyrical_storyteller": {
        "name": "서정적 이야기꾼",
        "name_en": "Lyrical Storyteller",
        "icon": "📖",
        "pattern": {"sustain": "high", "tone": "high", "expression": "mid"},
        "description": "깊고 따뜻한 음색으로 가사의 의미를 섬세하게 전달합니다. 한 곡 한 곡을 이야기처럼 풀어내며, 회중이 가사에 집중하게 만듭니다.",
        "strengths": ["가사 전달력", "감정 몰입 유도", "서정적 분위기"],
        "best_fit": ["말씀 찬양", "간증 예배", "성가대", "묵상 시간"],
        "songs": ["나 무엇과도 (김윤희)", "주의 음성을 내가 들으니 (성가)", "사랑의 주님 (김명식)"],
        "growth": ["업템포 곡 소화력", "에너지 있는 인도"]
    },
    "joyful_celebrator": {
        "name": "기쁨의 축제 인도자",
        "name_en": "Joyful Celebrator",
        "icon": "🎉",
        "pattern": {"tone": "low", "dynamics": "high", "sustain": "low"},
        "description": "밝고 경쾌한 음색으로 기쁨과 감사의 분위기를 만듭니다. 리드미컬한 찬양에서 특히 빛나며, 회중에게 축제의 기쁨을 전합니다.",
        "strengths": ["밝은 에너지", "리드미컬한 인도", "축제 분위기 조성"],
        "best_fit": ["부활절", "감사절", "어린이 예배", "야외 예배"],
        "songs": ["기뻐하며 왕께 노래 (전통)", "축복합니다 (소원)", "주를 찬양해요"],
        "growth": ["깊은 묵상 곡 연습", "따뜻한 음색 개발"]
    },
    # 전문가 패널 권장 추가 유형
    "healing_restorer": {
        "name": "회복의 치유 인도자",
        "name_en": "Healing Restorer",
        "icon": "💚",
        "pattern": {"intimacy": "low", "tone": "high", "expression": "low"},
        "description": "따뜻하고 절제된 음색으로 상처받은 마음을 어루만집니다. 치유와 회복의 순간에 안전한 공간을 만들며, 눈물과 함께 위로를 전합니다.",
        "strengths": ["위로하는 음색", "안전한 분위기 조성", "절제된 감정 표현"],
        "best_fit": ["치유 집회", "상담 후 기도", "장례 예배", "호스피스 예배"],
        "songs": ["나 같은 죄인 살리신 (어메이징 그레이스)", "주의 사랑이 나를 (김명식)", "내 맘에 주를 품고"],
        "growth": ["기쁨의 찬양 연습", "에너지 있는 인도 경험"]
    },
    "generational_bridge": {
        "name": "세대 연결 인도자",
        "name_en": "Generational Bridge",
        "icon": "🌉",
        "pattern": {"leading": "high", "dynamics": "mid", "expression": "mid"},
        "description": "어른과 청년, 어린이 모두가 편안하게 따라올 수 있는 인도를 합니다. 전통 찬송과 현대 찬양을 자연스럽게 연결하며, 세대 간 화합을 이끕니다.",
        "strengths": ["세대 통합 능력", "다양한 장르 소화", "안정적 인도"],
        "best_fit": ["가족 예배", "주일 통합 예배", "교회 창립 예배", "세례식"],
        "songs": ["내 주를 가까이 하게 함은 (전통+현대)", "은혜 (박지민)", "주 하나님 지으신 모든 세계"],
        "growth": ["개성 있는 스타일 개발", "즉흥적 인도 연습"]
    },
}


def calculate_worship_style(features: dict) -> WorshipVocalStyle:
    """
    오디오 특징에서 예배 보컬 스타일 계산

    Args:
        features: analyze_audio_features()의 결과

    Returns:
        WorshipVocalStyle 객체
    """
    # 각 차원의 점수 계산 (0-1)
    dimension_scores = {}

    # 1. 친밀감 vs 선포력 (다이나믹 + 음색 조합)
    dynamic_score = features.get('dynamic_score', 0.5)
    warmth = features.get('warmth_score', 0.5)
    intimacy_score = 1 - (dynamic_score * 0.6 + (1 - warmth) * 0.4)
    dimension_scores[StyleDimension.INTIMACY] = intimacy_score

    # 2. 명상적 vs 역동적 (다이나믹 기반)
    dimension_scores[StyleDimension.DYNAMICS] = dynamic_score

    # 3. 밝은 vs 따뜻한 (스펙트럼 센트로이드 기반)
    dimension_scores[StyleDimension.TONE] = warmth

    # 4. 자유로운 vs 구조적 (고음 안정성 기반)
    stability = features.get('high_note_stability', 0.5)
    dimension_scores[StyleDimension.LEADING] = stability

    # 5. 짧은 vs 긴 프레이즈 (호흡 지지 기반)
    breath_support = features.get('breath_support_score', 0.5)
    dimension_scores[StyleDimension.SUSTAIN] = breath_support

    # 6. 절제된 vs 감정적 (다이나믹 변화 + 피치 변화)
    energy_var = min(1.0, features.get('energy_variance', 0.1) * 5)
    vibrato = features.get('vibrato_ratio', 0.3)
    expression_score = (energy_var * 0.6 + vibrato * 0.4)
    dimension_scores[StyleDimension.EXPRESSION] = expression_score

    # 가장 적합한 아키타입 찾기
    best_archetype = find_best_archetype(dimension_scores)
    archetype_data = WORSHIP_STYLE_ARCHETYPES[best_archetype]

    return WorshipVocalStyle(
        style_name=archetype_data["name"],
        style_name_en=archetype_data["name_en"],
        icon=archetype_data["icon"],
        description=archetype_data["description"],
        strengths=archetype_data["strengths"],
        best_fit_contexts=archetype_data["best_fit"],
        recommended_songs=archetype_data["songs"],
        growth_areas=archetype_data["growth"],
        dimension_scores=dimension_scores
    )


def find_best_archetype(scores: Dict[StyleDimension, float]) -> str:
    """점수 패턴에 가장 맞는 아키타입 찾기"""

    def score_to_level(score: float) -> str:
        if score < 0.35:
            return "low"
        elif score > 0.65:
            return "high"
        return "mid"

    best_match = "balanced_shepherd"  # 기본값
    best_score = 0

    for archetype_id, archetype in WORSHIP_STYLE_ARCHETYPES.items():
        pattern = archetype["pattern"]
        match_score = 0

        for dim_str, expected_level in pattern.items():
            # 문자열을 StyleDimension으로 변환
            dim = StyleDimension[dim_str.upper()]
            actual_level = score_to_level(scores.get(dim, 0.5))

            if actual_level == expected_level:
                match_score += 2
            elif (expected_level == "mid") or (actual_level == "mid"):
                match_score += 1  # 부분 일치

        if match_score > best_score:
            best_score = match_score
            best_match = archetype_id

    return best_match


def get_style_description_for_dimension(dim: StyleDimension, score: float) -> Tuple[str, str, str]:
    """
    차원별 스타일 설명 생성

    Returns:
        (아이콘, 라벨, 설명)
    """
    axis = WORSHIP_STYLE_AXES[dim]

    if score < 0.35:
        return (axis.low_icon, axis.low_label, axis.worship_context_low)
    elif score > 0.65:
        return (axis.high_icon, axis.high_label, axis.worship_context_high)
    else:
        # 중간 - 양쪽 특성 혼합
        return ("⚖️", f"{axis.low_label} ~ {axis.high_label}", "다양한 상황에 유연하게 적응")


def generate_style_summary(style: WorshipVocalStyle) -> str:
    """스타일 요약 텍스트 생성"""
    summary_parts = []

    # 주요 특성 2-3개 추출
    high_dims = [(dim, score) for dim, score in style.dimension_scores.items() if score > 0.65]
    low_dims = [(dim, score) for dim, score in style.dimension_scores.items() if score < 0.35]

    if high_dims:
        traits = [WORSHIP_STYLE_AXES[dim].high_label for dim, _ in high_dims[:2]]
        summary_parts.append(f"{', '.join(traits)} 성향이 강합니다")

    if low_dims:
        traits = [WORSHIP_STYLE_AXES[dim].low_label for dim, _ in low_dims[:2]]
        summary_parts.append(f"{', '.join(traits)} 특성도 있습니다")

    return ". ".join(summary_parts) if summary_parts else "균형 잡힌 스타일입니다"


# 예배 상황별 추천
WORSHIP_CONTEXT_RECOMMENDATIONS = {
    "주일 오전 예배": {
        "ideal_profile": {"leading": "high", "dynamics": "mid", "expression": "mid"},
        "description": "안정적이고 회중 친화적인 인도가 필요합니다"
    },
    "청년 예배": {
        "ideal_profile": {"dynamics": "high", "expression": "high", "leading": "mid"},
        "description": "에너지 있고 감정적 교류가 가능한 인도가 좋습니다"
    },
    "새벽 기도회": {
        "ideal_profile": {"intimacy": "low", "dynamics": "low", "sustain": "high"},
        "description": "조용하고 친밀한 분위기의 인도가 적합합니다"
    },
    "부흥 집회": {
        "ideal_profile": {"intimacy": "high", "dynamics": "high", "expression": "high"},
        "description": "선포적이고 파워풀한 인도가 필요합니다"
    },
    "치유 집회": {
        "ideal_profile": {"intimacy": "low", "tone": "high", "sustain": "high"},
        "description": "따뜻하고 위로하는 분위기의 인도가 좋습니다"
    },
    "결혼 예배": {
        "ideal_profile": {"tone": "high", "expression": "mid", "leading": "high"},
        "description": "따뜻하면서도 안정적인 인도가 적합합니다"
    },
}
