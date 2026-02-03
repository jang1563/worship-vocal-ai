"""
🎵 찬양 추천 모듈 (Song Recommender)
=====================================

보컬 분석 결과를 바탕으로:
1. 현재 실력에 어울리는 찬양 (자신감 곡)
2. 성장을 위한 연습 찬양 (도전 곡)
3. 롤모델 스타일 찬양
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

# =============================================
# 1. 찬양 데이터베이스
# =============================================

@dataclass
class Song:
    """찬양 정보"""
    title: str                  # 제목
    artist: str                 # 아티스트/팀
    key: str                    # 원키
    tempo: int                  # BPM
    difficulty: int             # 난이도 (1-5)
    vocal_range: str            # 음역대 (예: "G3-D5")
    range_semitones: int        # 음역 폭 (반음)
    style: str                  # 스타일
    characteristics: List[str]  # 특징 태그
    suitable_for: List[str]     # 적합한 보컬 타입
    practice_for: List[str]     # 연습에 좋은 보컬 타입
    youtube_url: Optional[str]  # 참고 영상
    notes: str                  # 코칭 노트


# 찬양 데이터베이스 (확장 가능)
SONG_DATABASE = [
    # =============================================
    # 발라드 / 느린 찬양
    # =============================================
    Song(
        title="나 무력할수록",
        artist="어노인팅",
        key="G",
        tempo=68,
        difficulty=2,
        vocal_range="D3-D4",
        range_semitones=12,
        style="발라드",
        characteristics=["중저음 위주", "진정성", "고백적"],
        suitable_for=["ST", "IN"],
        practice_for=["PA", "JO"],  # 파워/조이풀 타입이 절제 연습용
        youtube_url="https://www.youtube.com/watch?v=example1",
        notes="중저음에서 진정성 있게 부르는 연습에 좋습니다. 과하게 꾸미지 않고 담담하게."
    ),
    Song(
        title="주 하나님 독생자 예수",
        artist="어노인팅",
        key="D",
        tempo=72,
        difficulty=2,
        vocal_range="A2-A4",
        range_semitones=24,
        style="발라드",
        characteristics=["넓은 음역", "점진적 빌드업", "경배"],
        suitable_for=["ST", "WL"],
        practice_for=["IN"],  # 인티메이트가 음역 확장 연습
        youtube_url=None,
        notes="절에서 후렴으로 가는 빌드업이 핵심. 억지로 밀지 않고 자연스럽게."
    ),
    Song(
        title="나의 가장 낮은 곳에서",
        artist="소진영",
        key="E",
        tempo=65,
        difficulty=3,
        vocal_range="B2-E4",
        range_semitones=17,
        style="발라드",
        characteristics=["감정 표현", "클라이맥스", "간증적"],
        suitable_for=["ST", "WL", "PA"],
        practice_for=["IN", "JO"],
        youtube_url=None,
        notes="감정 폭발 구간에서 목을 조이지 않도록 주의. 호흡으로 밀어주세요."
    ),
    Song(
        title="여호와는 나의 목자시니",
        artist="마커스워십",
        key="G",
        tempo=60,
        difficulty=1,
        vocal_range="D3-D4",
        range_semitones=12,
        style="명상/기도",
        characteristics=["단순함", "반복", "평안"],
        suitable_for=["IN", "ST"],
        practice_for=["PA", "SO"],  # 절제 연습
        youtube_url=None,
        notes="단순한 멜로디를 지루하지 않게 부르는 게 핵심. 미세한 다이나믹으로 표현."
    ),
    
    # =============================================
    # 미디엄 템포
    # =============================================
    Song(
        title="예배합니다",
        artist="마커스워십",
        key="A",
        tempo=85,
        difficulty=3,
        vocal_range="E3-E5",
        range_semitones=24,
        style="경배",
        characteristics=["선포적", "넓은 음역", "리더십"],
        suitable_for=["WL", "PA"],
        practice_for=["ST", "IN"],  # 리더십/파워 연습
        youtube_url=None,
        notes="회중을 이끄는 리더십이 필요한 곡. 자신감 있게 선포하듯이."
    ),
    Song(
        title="다 드리리",
        artist="마커스워십",
        key="G",
        tempo=90,
        difficulty=3,
        vocal_range="D3-D5",
        range_semitones=24,
        style="경배/헌신",
        characteristics=["강약 대비", "고음 클라이맥스", "헌신"],
        suitable_for=["WL", "PA"],
        practice_for=["ST"],
        youtube_url=None,
        notes="절은 담담하게, 후렴은 폭발적으로. 대비가 중요합니다."
    ),
    Song(
        title="주님께 드려요",
        artist="어노인팅",
        key="F",
        tempo=88,
        difficulty=2,
        vocal_range="C3-C5",
        range_semitones=24,
        style="경배",
        characteristics=["균형잡힌", "회중 친화적", "따뜻함"],
        suitable_for=["ST", "WL"],
        practice_for=["JO", "PA"],
        youtube_url=None,
        notes="회중이 따라부르기 좋은 멜로디. 인도자가 너무 튀지 않게."
    ),
    
    # =============================================
    # 업템포 / 찬양
    # =============================================
    Song(
        title="다시 부르네",
        artist="아이자야씩스티원",
        key="E",
        tempo=130,
        difficulty=4,
        vocal_range="E3-G#5",
        range_semitones=28,
        style="가스펠/파워",
        characteristics=["폭발적 고음", "애드립", "에너지"],
        suitable_for=["PA", "SO"],
        practice_for=["WL"],  # 파워 연습
        youtube_url=None,
        notes="체력 소모가 큰 곡. 호흡 분배가 핵심. 처음부터 풀파워 금지!"
    ),
    Song(
        title="여호와 닛시",
        artist="아이자야씩스티원",
        key="F",
        tempo=125,
        difficulty=4,
        vocal_range="F3-A5",
        range_semitones=28,
        style="가스펠/선포",
        characteristics=["폭발적", "선포", "영적 전쟁"],
        suitable_for=["PA", "SO"],
        practice_for=["WL", "JO"],
        youtube_url=None,
        notes="영적 권위를 담아 선포하는 곡. 목만 쓰지 말고 온몸으로."
    ),
    Song(
        title="살아계신 주",
        artist="예수전도단",
        key="G",
        tempo=140,
        difficulty=3,
        vocal_range="D3-D5",
        range_semitones=24,
        style="찬양/축제",
        characteristics=["밝음", "경쾌함", "기쁨"],
        suitable_for=["JO", "WL"],
        practice_for=["IN", "ST"],  # 에너지 확장 연습
        youtube_url=None,
        notes="밝고 경쾌하게! 너무 무겁게 부르지 않도록."
    ),
    Song(
        title="주님 다시 오실 때까지",
        artist="마커스워십",
        key="A",
        tempo=118,
        difficulty=3,
        vocal_range="E3-E5",
        range_semitones=24,
        style="선포/행진",
        characteristics=["리더십", "결단", "선포"],
        suitable_for=["WL", "PA"],
        practice_for=["ST", "IN"],
        youtube_url=None,
        notes="행진하듯 당당하게. 비트를 타면서 선포하는 느낌으로."
    ),
    
    # =============================================
    # 소울/가스펠 스타일
    # =============================================
    Song(
        title="거친 광야 지날 때",
        artist="예수전도단",
        key="Bb",
        tempo=95,
        difficulty=4,
        vocal_range="Bb2-Bb4",
        range_semitones=24,
        style="가스펠",
        characteristics=["그루브", "비브라토", "소울"],
        suitable_for=["SO", "PA"],
        practice_for=["WL", "JO"],
        youtube_url=None,
        notes="그루브를 타면서 자연스럽게. 과한 기교보다 느낌이 중요."
    ),
    Song(
        title="은혜 (나같은 죄인 살리신)",
        artist="나윤권",
        key="G",
        tempo=70,
        difficulty=5,
        vocal_range="G2-G5",
        range_semitones=36,
        style="소울/가스펠",
        characteristics=["극한 음역", "애드립", "감정 폭발"],
        suitable_for=["SO", "PA"],
        practice_for=[],  # 고급자 전용
        youtube_url=None,
        notes="극한의 음역대와 감정 표현이 필요한 곡. 충분한 준비 후 도전."
    ),
    
    # =============================================
    # 인티메이트 / 묵상
    # =============================================
    Song(
        title="오 신실하신 주",
        artist="조셉붓소",
        key="D",
        tempo=58,
        difficulty=2,
        vocal_range="A3-D5",
        range_semitones=17,
        style="인티메이트",
        characteristics=["친밀함", "섬세함", "묵상"],
        suitable_for=["IN", "ST"],
        practice_for=["PA", "JO"],
        youtube_url=None,
        notes="속삭이듯 친밀하게. 볼륨보다 진심이 중요합니다."
    ),
    Song(
        title="나의 가장 깊은 곳에",
        artist="어노인팅",
        key="E",
        tempo=62,
        difficulty=2,
        vocal_range="B3-E5",
        range_semitones=17,
        style="묵상/기도",
        characteristics=["반복", "깊어짐", "명상"],
        suitable_for=["IN", "ST"],
        practice_for=["WL"],
        youtube_url=None,
        notes="반복되는 멜로디가 점점 깊어지도록. 지루하지 않게 미세 변화."
    ),
]


# =============================================
# 2. 추천 로직
# =============================================

class RecommendationType(Enum):
    """추천 유형"""
    CONFIDENCE = "confidence"     # 자신감 곡 (강점 활용)
    CHALLENGE = "challenge"       # 도전 곡 (성장용)
    ROLE_MODEL = "role_model"     # 롤모델 스타일


@dataclass
class SongRecommendation:
    """찬양 추천 결과"""
    song: Song
    recommendation_type: RecommendationType
    match_score: float          # 매칭 점수 (0-100)
    reason: str                 # 추천 이유
    coaching_tip: str           # 코칭 팁


def recommend_songs(
    vocal_type: str,
    vocal_features: dict,
    scorecard: dict,
    num_recommendations: int = 3
) -> Dict[str, List[SongRecommendation]]:
    """
    보컬 분석 결과를 바탕으로 찬양 추천
    
    Args:
        vocal_type: 보컬 MBTI 코드 (예: "ST")
        vocal_features: 분석된 특징들
        scorecard: 역량 스코어카드
        num_recommendations: 카테고리별 추천 수
    
    Returns:
        {
            "confidence": [...],   # 자신감 곡
            "challenge": [...],    # 도전 곡
            "role_model": [...]    # 롤모델 스타일
        }
    """
    
    recommendations = {
        "confidence": [],
        "challenge": [],
        "role_model": []
    }
    
    # 1. 자신감 곡 (suitable_for에 현재 타입이 포함)
    confidence_songs = []
    for song in SONG_DATABASE:
        if vocal_type in song.suitable_for:
            score = calculate_match_score(song, vocal_features, scorecard)
            reason = generate_confidence_reason(song, vocal_type)
            tip = song.notes
            
            confidence_songs.append(SongRecommendation(
                song=song,
                recommendation_type=RecommendationType.CONFIDENCE,
                match_score=score,
                reason=reason,
                coaching_tip=tip
            ))
    
    # 점수순 정렬
    confidence_songs.sort(key=lambda x: x.match_score, reverse=True)
    recommendations["confidence"] = confidence_songs[:num_recommendations]
    
    # 2. 도전 곡 (practice_for에 현재 타입이 포함)
    challenge_songs = []
    for song in SONG_DATABASE:
        if vocal_type in song.practice_for:
            score = calculate_challenge_score(song, vocal_features, scorecard)
            reason = generate_challenge_reason(song, vocal_type)
            tip = generate_challenge_tip(song, vocal_type, scorecard)
            
            challenge_songs.append(SongRecommendation(
                song=song,
                recommendation_type=RecommendationType.CHALLENGE,
                match_score=score,
                reason=reason,
                coaching_tip=tip
            ))
    
    challenge_songs.sort(key=lambda x: x.match_score, reverse=True)
    recommendations["challenge"] = challenge_songs[:num_recommendations]
    
    # 3. 롤모델 스타일 (롤모델 아티스트의 곡)
    role_model_artists = get_role_model_artists(vocal_type)
    role_model_songs = []
    
    for song in SONG_DATABASE:
        if any(artist.lower() in song.artist.lower() for artist in role_model_artists):
            score = 80 + (100 - song.difficulty * 10)  # 난이도 반영
            reason = f"당신의 롤모델 {song.artist}의 대표곡입니다."
            tip = song.notes
            
            role_model_songs.append(SongRecommendation(
                song=song,
                recommendation_type=RecommendationType.ROLE_MODEL,
                match_score=score,
                reason=reason,
                coaching_tip=tip
            ))
    
    role_model_songs.sort(key=lambda x: x.match_score, reverse=True)
    recommendations["role_model"] = role_model_songs[:num_recommendations]
    
    return recommendations


def calculate_match_score(song: Song, features: dict, scorecard: dict) -> float:
    """자신감 곡 매칭 점수 계산"""
    score = 70  # 기본 점수
    
    # 음역대 매칭 (사용자 음역이 곡 음역을 커버하면 +)
    user_range = features.get('pitch_range_semitones', 20)
    if user_range >= song.range_semitones:
        score += 15
    elif user_range >= song.range_semitones * 0.8:
        score += 10
    else:
        score -= 10
    
    # 난이도 매칭 (테크닉 점수와 비교)
    tech_score = scorecard.get('technique', 50)
    if tech_score >= song.difficulty * 20:
        score += 10
    elif tech_score < song.difficulty * 15:
        score -= 10
    
    # 스타일 매칭
    if "발라드" in song.style and features.get('tempo_bpm', 100) < 90:
        score += 5
    if "업템포" in song.style and features.get('tempo_bpm', 100) > 100:
        score += 5
    
    return min(100, max(0, score))


def calculate_challenge_score(song: Song, features: dict, scorecard: dict) -> float:
    """도전 곡 매칭 점수 계산 (적절한 도전 수준)"""
    score = 60
    
    # 너무 어려우면 감점, 적당히 어려우면 가점
    tech_score = scorecard.get('technique', 50)
    difficulty_gap = song.difficulty * 20 - tech_score
    
    if 10 <= difficulty_gap <= 30:  # 적절한 도전
        score += 20
    elif 0 <= difficulty_gap < 10:  # 조금 도전
        score += 15
    elif difficulty_gap > 40:  # 너무 어려움
        score -= 20
    
    return min(100, max(0, score))


def generate_confidence_reason(song: Song, vocal_type: str) -> str:
    """자신감 곡 추천 이유 생성"""
    reasons = {
        "ST": f"당신의 따뜻한 음색과 진정성이 돋보일 수 있는 곡입니다.",
        "WL": f"당신의 리더십과 안정감을 발휘할 수 있는 곡입니다.",
        "PA": f"당신의 폭발적인 에너지를 표현할 수 있는 곡입니다.",
        "IN": f"당신의 섬세함과 친밀함이 빛나는 곡입니다.",
        "JO": f"당신의 밝은 에너지가 잘 어울리는 곡입니다.",
        "SO": f"당신의 소울풀한 그루브를 표현할 수 있는 곡입니다."
    }
    return reasons.get(vocal_type, "당신의 스타일에 잘 어울리는 곡입니다.")


def generate_challenge_reason(song: Song, vocal_type: str) -> str:
    """도전 곡 추천 이유 생성"""
    reasons = {
        "ST": f"더 넓은 다이나믹과 에너지 표현을 연습할 수 있습니다.",
        "WL": f"더 강렬한 감정 표현이나 섬세한 터치를 연습할 수 있습니다.",
        "PA": f"절제와 섬세한 표현을 연습할 수 있습니다.",
        "IN": f"더 큰 볼륨과 리더십을 연습할 수 있습니다.",
        "JO": f"깊은 감정 표현과 발라드 스타일을 연습할 수 있습니다.",
        "SO": f"심플하고 절제된 표현을 연습할 수 있습니다."
    }
    return reasons.get(vocal_type, "성장을 위한 좋은 도전이 될 곡입니다.")


def generate_challenge_tip(song: Song, vocal_type: str, scorecard: dict) -> str:
    """도전 곡 코칭 팁 생성"""
    base_tip = song.notes
    
    # 타입별 추가 팁
    extra_tips = {
        "ST": "처음에는 볼륨을 낮추고 감정 표현에만 집중해보세요.",
        "WL": "기술에 집착하지 말고 감정의 흐름을 느껴보세요.",
        "PA": "일부러 50% 힘으로만 불러보세요. 절제가 핵심입니다.",
        "IN": "거울 앞에서 몸을 크게 쓰면서 연습해보세요.",
        "JO": "눈을 감고 가사의 의미에 집중하며 불러보세요.",
        "SO": "애드립 없이 원곡 그대로만 불러보세요."
    }
    
    extra = extra_tips.get(vocal_type, "")
    return f"{base_tip} {extra}".strip()


def get_role_model_artists(vocal_type: str) -> List[str]:
    """보컬 타입별 롤모델 아티스트"""
    role_models = {
        "ST": ["어노인팅", "김윤진", "이영훈"],
        "WL": ["마커스워십", "소진영", "심종호"],
        "PA": ["아이자야씩스티원", "이성진", "소향"],
        "IN": ["조셉붓소", "유은성", "다윗의장막"],
        "JO": ["예수전도단", "찬미", "디사이플스"],
        "SO": ["나윤권", "제이어스", "유진"]
    }
    return role_models.get(vocal_type, [])


# =============================================
# 3. 출력 포맷팅
# =============================================

def format_recommendations(recommendations: Dict[str, List[SongRecommendation]]) -> str:
    """추천 결과를 보기 좋게 포맷팅"""
    
    output = []
    
    # 자신감 곡
    output.append("## 🌟 자신감 곡 (당신의 강점을 살릴 수 있는 곡)")
    output.append("")
    for i, rec in enumerate(recommendations["confidence"], 1):
        output.append(f"### {i}. {rec.song.title}")
        output.append(f"- **아티스트**: {rec.song.artist}")
        output.append(f"- **난이도**: {'⭐' * rec.song.difficulty}")
        output.append(f"- **원키**: {rec.song.key} | **템포**: {rec.song.tempo} BPM")
        output.append(f"- **추천 이유**: {rec.reason}")
        output.append(f"- **코칭 팁**: {rec.coaching_tip}")
        output.append("")
    
    # 도전 곡
    output.append("## 🎯 도전 곡 (성장을 위한 연습 곡)")
    output.append("")
    for i, rec in enumerate(recommendations["challenge"], 1):
        output.append(f"### {i}. {rec.song.title}")
        output.append(f"- **아티스트**: {rec.song.artist}")
        output.append(f"- **난이도**: {'⭐' * rec.song.difficulty}")
        output.append(f"- **원키**: {rec.song.key} | **템포**: {rec.song.tempo} BPM")
        output.append(f"- **추천 이유**: {rec.reason}")
        output.append(f"- **코칭 팁**: {rec.coaching_tip}")
        output.append("")
    
    # 롤모델 곡
    if recommendations["role_model"]:
        output.append("## 🎤 롤모델 스타일 곡")
        output.append("")
        for i, rec in enumerate(recommendations["role_model"], 1):
            output.append(f"### {i}. {rec.song.title}")
            output.append(f"- **아티스트**: {rec.song.artist}")
            output.append(f"- **난이도**: {'⭐' * rec.song.difficulty}")
            output.append(f"- **추천 이유**: {rec.reason}")
            output.append(f"- **코칭 팁**: {rec.coaching_tip}")
            output.append("")
    
    return "\n".join(output)


# =============================================
# 4. 테스트
# =============================================

def test_recommendations():
    """추천 기능 테스트"""
    
    # 테스트 데이터 (Storyteller 타입)
    vocal_type = "ST"
    vocal_features = {
        'pitch_range_semitones': 28.4,
        'avg_pitch_hz': 172.5,
        'tempo_bpm': 129,
        'dynamic_range_db': 14.4
    }
    scorecard = {
        'tone': 72,
        'leadership': 78,
        'rhythm': 91,
        'diction': 67,
        'technique': 54
    }
    
    print("=" * 60)
    print("🎵 찬양 추천 결과")
    print(f"   보컬 타입: The Storyteller (스토리텔러)")
    print("=" * 60)
    print()
    
    recommendations = recommend_songs(vocal_type, vocal_features, scorecard)
    formatted = format_recommendations(recommendations)
    print(formatted)
    
    return recommendations


if __name__ == "__main__":
    test_recommendations()
