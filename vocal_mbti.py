"""
🎤 Worship Vocal MBTI 분류 시스템
=====================================

이 모듈은 오디오 분석 데이터를 기반으로 보컬 타입을 분류합니다.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# =============================================
# 1. 보컬 MBTI 타입 정의
# =============================================

@dataclass
class VocalType:
    """보컬 타입 정의"""
    code: str           # 타입 코드 (예: "ST")
    name_en: str        # 영문 이름
    name_kr: str        # 한글 이름
    description: str    # 설명
    strengths: List[str]    # 강점
    weaknesses: List[str]   # 약점
    role_models: List[str]  # 롤모델
    practice_focus: List[str]  # 연습 포인트

# 6가지 보컬 타입 정의
VOCAL_TYPES = {
    "ST": VocalType(
        code="ST",
        name_en="The Storyteller",
        name_kr="스토리텔러",
        description="말하듯 전하는 진정성의 보컬. 회중의 마음을 편안하게 열어주는 따뜻한 음색.",
        strengths=["진정성 있는 전달력", "따뜻한 중저음", "멘트→찬양 자연스러운 연결"],
        weaknesses=["고음역 파워 부족 가능", "때로 에너지 부족"],
        role_models=["김윤진 (어노인팅)", "이영훈 (어노인팅)"],
        practice_focus=["고음 지지력 강화", "다이나믹 레인지 확대"]
    ),
    "WL": VocalType(
        code="WL",
        name_en="The Worship Leader",
        name_kr="워십 리더",
        description="회중을 안정감 있게 이끄는 리더십의 보컬. 균형 잡힌 테크닉과 영적 권위.",
        strengths=["안정적인 음정", "넓은 음역대 활용", "회중 리딩 능력"],
        weaknesses=["때로 기계적으로 느껴질 수 있음"],
        role_models=["소진영 (마커스)", "심종호 (어노인팅)"],
        practice_focus=["감정 표현 다양화", "즉흥적 변주"]
    ),
    "PA": VocalType(
        code="PA",
        name_en="The Passionate",
        name_kr="열정가",
        description="폭발적 감정 표현의 보컬. 클라이맥스에서 회중을 압도하는 파워.",
        strengths=["강렬한 고음", "다이나믹한 표현", "에너지 전달력"],
        weaknesses=["저음역 약할 수 있음", "과한 표현 주의"],
        role_models=["이성진 (아이자야씩스티원)", "소향"],
        practice_focus=["저음역 안정화", "섬세한 표현 추가"]
    ),
    "IN": VocalType(
        code="IN",
        name_en="The Intimate",
        name_kr="인티메이트",
        description="속삭이듯 친밀하게 다가오는 보컬. 개인 예배와 묵상에 적합한 섬세함.",
        strengths=["섬세한 감정 표현", "부드러운 톤", "친밀감"],
        weaknesses=["파워 부족", "큰 공간에서 전달력 약함"],
        role_models=["유은성 (다윗의장막)", "조셉붓소"],
        practice_focus=["복식호흡 강화", "성량 확대"]
    ),
    "JO": VocalType(
        code="JO",
        name_en="The Joyful",
        name_kr="조이풀",
        description="밝고 경쾌한 축제의 보컬. 찬양의 기쁨을 온몸으로 표현하는 에너지.",
        strengths=["밝은 음색", "리듬감", "긍정적 에너지"],
        weaknesses=["깊은 감정 표현 부족", "발라드 약할 수 있음"],
        role_models=["찬미 (예수전도단)", "천관웅 (다윗의장막)"],
        practice_focus=["감정 깊이 추가", "발라드 표현력"]
    ),
    "SO": VocalType(
        code="SO",
        name_en="The Soulful",
        name_kr="소울풀",
        description="깊은 영혼의 울림을 가진 보컬. 가스펠 특유의 그루브와 애드립.",
        strengths=["풍부한 비브라토", "애드립 능력", "그루브"],
        weaknesses=["때로 과한 기교", "심플한 곡에서 어색"],
        role_models=["나윤권", "이끼 (Eki)"],
        practice_focus=["절제된 표현", "심플한 곡 연습"]
    )
}

# =============================================
# 2. 분류 기준 정의 (Feature → Type 매핑)
# =============================================

"""
분류에 사용하는 오디오 특성들:

1. 음역대 관련
   - pitch_range: 음역 폭 (반음 단위)
   - avg_pitch: 평균 음정 (Hz)
   - high_note_ratio: 고음역 비율 (%)
   
2. 다이나믹 관련
   - dynamic_range: 다이나믹 레인지 (dB)
   - energy_variance: 에너지 변화량
   - climax_intensity: 클라이맥스 강도
   
3. 음색 관련
   - spectral_centroid: 스펙트럼 센트로이드 (Hz) - 밝기
   - warmth_score: 따뜻함 점수 (저주파 비율)
   
4. 표현력 관련
   - vibrato_ratio: 비브라토 비율 (%)
   - pitch_stability: 음정 안정성 (%)
   - pitch_accuracy: 음정 정확도 (cents)
   
5. 리듬 관련
   - tempo: 템포 (BPM)
   - rhythm_consistency: 박자 일관성
"""

@dataclass
class VocalFeatures:
    """분석된 보컬 특성"""
    # 음역대
    pitch_range_semitones: float  # 음역 폭 (반음)
    avg_pitch_hz: float           # 평균 음정
    high_note_ratio: float        # 고음역 비율 (0-1)
    low_note_ratio: float         # 저음역 비율 (0-1)
    
    # 다이나믹
    dynamic_range_db: float       # 다이나믹 레인지
    energy_variance: float        # 에너지 변화량
    climax_intensity: float       # 클라이맥스 강도 (0-1)
    
    # 음색
    spectral_centroid_hz: float   # 밝기
    warmth_score: float           # 따뜻함 (0-1)
    
    # 표현력
    vibrato_ratio: float          # 비브라토 비율 (0-1)
    pitch_stability: float        # 음정 안정성 (0-1)
    pitch_accuracy_cents: float   # 음정 오차 (cents)
    
    # 리듬
    tempo_bpm: float              # 템포
    
    # 추가 특성
    breath_phrase_length: float   # 평균 프레이즈 길이 (초)
    flat_tendency: float          # 플랫 경향 (0-1)
    sharp_tendency: float         # 샤프 경향 (0-1)


def classify_vocal_type(features: VocalFeatures) -> Tuple[str, Dict[str, float]]:
    """
    보컬 특성을 기반으로 MBTI 타입 분류
    
    Returns:
        (primary_type_code, scores_dict)
    """
    scores = {code: 0.0 for code in VOCAL_TYPES.keys()}
    
    # =============================================
    # 분류 규칙 (가중치 기반 점수)
    # =============================================
    
    # 1. 음색 기반 분류
    # 따뜻한 음색 (낮은 spectral centroid)
    if features.spectral_centroid_hz < 1800:
        scores["ST"] += 25  # 스토리텔러
        scores["IN"] += 20  # 인티메이트
    elif features.spectral_centroid_hz < 2200:
        scores["WL"] += 20  # 워십리더 (균형)
        scores["SO"] += 15  # 소울풀
    else:
        scores["JO"] += 25  # 조이풀 (밝음)
        scores["PA"] += 15  # 열정가
    
    # 2. 다이나믹 기반 분류
    if features.dynamic_range_db > 18:
        scores["PA"] += 25  # 열정가 (극적인 강약)
        scores["SO"] += 15
    elif features.dynamic_range_db > 12:
        scores["WL"] += 20  # 워십리더 (적절한 강약)
        scores["ST"] += 15
    else:
        scores["IN"] += 25  # 인티메이트 (일정한 톤)
        scores["ST"] += 10
    
    # 3. 고음 비율 기반 분류
    if features.high_note_ratio > 0.25:
        scores["PA"] += 20  # 열정가 (고음 많음)
        scores["JO"] += 15
    elif features.high_note_ratio < 0.10:
        scores["ST"] += 15  # 스토리텔러 (중저음 위주)
        scores["IN"] += 15
    else:
        scores["WL"] += 15  # 워십리더 (균형)
    
    # 4. 비브라토 기반 분류
    if features.vibrato_ratio > 0.35:
        scores["SO"] += 25  # 소울풀 (풍부한 비브라토)
        scores["PA"] += 10
    elif features.vibrato_ratio > 0.20:
        scores["WL"] += 15
        scores["ST"] += 10
    else:
        scores["IN"] += 15  # 인티메이트 (스트레이트 톤)
        scores["JO"] += 10
    
    # 5. 음정 안정성 기반 분류
    if features.pitch_stability > 0.85:
        scores["WL"] += 20  # 워십리더 (안정적)
        scores["IN"] += 15
    elif features.pitch_stability < 0.70:
        scores["SO"] += 15  # 소울풀 (표현적 변화)
        scores["PA"] += 10
    
    # 6. 템포/에너지 기반 분류
    if features.tempo_bpm > 120:
        scores["JO"] += 20  # 조이풀 (빠른 템포)
        scores["PA"] += 10
    elif features.tempo_bpm < 80:
        scores["IN"] += 20  # 인티메이트 (느린 템포)
        scores["ST"] += 15
    else:
        scores["WL"] += 15
        scores["ST"] += 10
    
    # 7. 프레이즈 길이 기반
    if features.breath_phrase_length > 6:
        scores["WL"] += 10  # 좋은 호흡 = 리더십
        scores["PA"] += 10
    elif features.breath_phrase_length < 3:
        scores["IN"] += 10  # 짧은 프레이즈 = 친밀함
    
    # 8. 클라이맥스 강도
    if features.climax_intensity > 0.8:
        scores["PA"] += 15
        scores["SO"] += 10
    elif features.climax_intensity < 0.5:
        scores["IN"] += 15
        scores["ST"] += 10
    
    # 정규화 (0-100 스케일)
    max_score = max(scores.values())
    if max_score > 0:
        scores = {k: round(v / max_score * 100, 1) for k, v in scores.items()}
    
    # 1위 타입 결정
    primary_type = max(scores, key=scores.get)
    
    return primary_type, scores


def get_secondary_type(scores: Dict[str, float], primary: str) -> Optional[str]:
    """2순위 타입 반환"""
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for code, score in sorted_scores:
        if code != primary and score > 50:  # 50점 이상만
            return code
    return None


# =============================================
# 3. 역량 스코어카드 계산
# =============================================

@dataclass
class ScoreCard:
    """역량 평가표"""
    tone: int           # 음색 (0-100)
    leadership: int     # 리딩 (0-100)
    rhythm: int         # 리듬 (0-100)
    diction: int        # 전달력 (0-100)
    technique: int      # 테크닉 (0-100)
    
    @property
    def total(self) -> int:
        return round((self.tone + self.leadership + self.rhythm + 
                     self.diction + self.technique) / 5)


def calculate_scorecard(features: VocalFeatures) -> ScoreCard:
    """특성 기반 스코어카드 계산"""
    
    # 음색: 따뜻함 + 안정성
    tone = min(100, int(
        features.warmth_score * 50 + 
        features.pitch_stability * 50
    ))
    
    # 리딩: 다이나믹 + 음역대 + 안정성
    leadership = min(100, int(
        (features.dynamic_range_db / 20) * 30 +
        (features.pitch_range_semitones / 30) * 30 +
        features.pitch_stability * 40
    ))
    
    # 리듬: 템포 일관성 (임시로 안정성 활용)
    rhythm = min(100, int(
        70 + features.pitch_stability * 30
    ))
    
    # 전달력: 다이나믹 + 고음 비율
    diction = min(100, int(
        (features.dynamic_range_db / 20) * 40 +
        (1 - features.flat_tendency) * 30 +
        features.climax_intensity * 30
    ))
    
    # 테크닉: 음정 정확도 + 호흡 + 비브라토 컨트롤
    technique = min(100, int(
        max(0, 100 - features.pitch_accuracy_cents * 2) * 0.4 +
        min(100, features.breath_phrase_length * 10) * 0.3 +
        min(100, features.pitch_stability * 100) * 0.3
    ))
    
    return ScoreCard(
        tone=tone,
        leadership=leadership,
        rhythm=rhythm,
        diction=diction,
        technique=technique
    )


# =============================================
# 4. 테스트 함수
# =============================================

def test_classification():
    """분류 로직 테스트 (아까 분석한 데이터 기반)"""
    
    # 아까 분석한 찬양 인도자 데이터
    test_features = VocalFeatures(
        pitch_range_semitones=28.4,    # 2.4 옥타브
        avg_pitch_hz=172.5,            # F3
        high_note_ratio=0.158,         # 15.8%
        low_note_ratio=0.248,          # 24.8%
        dynamic_range_db=14.4,
        energy_variance=0.3,
        climax_intensity=0.7,
        spectral_centroid_hz=1777,     # 따뜻한 음색
        warmth_score=0.75,
        vibrato_ratio=0.406,           # 40.6% 비브라토
        pitch_stability=0.70,          # 30.4% 변동 → 70% 안정
        pitch_accuracy_cents=20.3,
        tempo_bpm=129,
        breath_phrase_length=3.1,
        flat_tendency=0.406,
        sharp_tendency=0.287
    )
    
    # 분류 실행
    primary_type, scores = classify_vocal_type(test_features)
    secondary_type = get_secondary_type(scores, primary_type)
    scorecard = calculate_scorecard(test_features)
    
    print("=" * 60)
    print("🎤 보컬 MBTI 분류 결과")
    print("=" * 60)
    
    print(f"\n📌 주요 타입: {VOCAL_TYPES[primary_type].name_en}")
    print(f"   ({VOCAL_TYPES[primary_type].name_kr})")
    print(f"\n   {VOCAL_TYPES[primary_type].description}")
    
    if secondary_type:
        print(f"\n📌 보조 타입: {VOCAL_TYPES[secondary_type].name_en}")
        print(f"   ({VOCAL_TYPES[secondary_type].name_kr})")
    
    print(f"\n📊 타입별 점수:")
    for code, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        print(f"   {VOCAL_TYPES[code].name_kr:8} {bar} {score:.1f}")
    
    print(f"\n📋 역량 스코어카드:")
    print(f"   음색 (Tone):      {scorecard.tone}")
    print(f"   리딩 (Leadership): {scorecard.leadership}")
    print(f"   리듬 (Rhythm):     {scorecard.rhythm}")
    print(f"   전달력 (Diction):  {scorecard.diction}")
    print(f"   테크닉 (Tech):     {scorecard.technique}")
    print(f"   ─────────────────────")
    print(f"   종합:              {scorecard.total}")
    
    vocal_type = VOCAL_TYPES[primary_type]
    print(f"\n✅ 강점:")
    for s in vocal_type.strengths:
        print(f"   • {s}")
    
    print(f"\n⚠️ 보완점:")
    for w in vocal_type.weaknesses:
        print(f"   • {w}")
    
    print(f"\n🎯 롤모델:")
    for r in vocal_type.role_models:
        print(f"   • {r}")
    
    print(f"\n📝 연습 포인트:")
    for p in vocal_type.practice_focus:
        print(f"   • {p}")
    
    return primary_type, scores, scorecard


if __name__ == "__main__":
    test_classification()
