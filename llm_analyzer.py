"""
🤖 LLM 기반 보컬 분석 모듈
===========================

Anthropic Claude API를 사용하여 더 정확하고 맥락을 이해하는 분석 제공
"""

import anthropic
import json
import httpx
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, List

# API 키 설정 - 환경변수에서 로드
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# 타임아웃 설정 (초)
LLM_TIMEOUT = 60  # 60초 타임아웃
LLM_MAX_RETRIES = 2  # 최대 재시도 횟수


def generate_fallback_analysis(features_a: dict, features_b: dict) -> dict:
    """
    LLM 실패 시 특징 기반 기본 분석 생성
    """
    # 특징 평균 계산
    avg_pitch = (features_a['avg_pitch_hz'] + features_b['avg_pitch_hz']) / 2
    avg_stability = (features_a.get('high_note_stability', 0.5) + features_b.get('high_note_stability', 0.5)) / 2
    avg_dynamic = (features_a['dynamic_range_db'] + features_b['dynamic_range_db']) / 2
    avg_warmth = (features_a.get('warmth_score', 0.5) + features_b.get('warmth_score', 0.5)) / 2
    avg_accuracy = (features_a['pitch_accuracy_cents'] + features_b['pitch_accuracy_cents']) / 2

    # 페르소나 결정 (특징 기반)
    if avg_warmth > 0.4 and avg_dynamic < 18:
        persona_name = "서정적 이야기꾼"
        persona_icon = "📖"
        persona_desc = "따뜻한 음색으로 가사의 의미를 전달하는 스타일입니다."
    elif avg_dynamic > 20 and avg_stability > 0.6:
        persona_name = "선포적 찬양 인도자"
        persona_icon = "🔥"
        persona_desc = "강력한 다이나믹과 안정적인 고음으로 회중을 이끄는 스타일입니다."
    elif avg_stability > 0.7:
        persona_name = "균형잡힌 목양 인도자"
        persona_icon = "⚓"
        persona_desc = "안정적인 음정과 균형잡힌 표현으로 회중을 편안하게 인도합니다."
    else:
        persona_name = "친밀한 기도 인도자"
        persona_icon = "🕊️"
        persona_desc = "부드러운 음색으로 친밀한 분위기를 만드는 스타일입니다."

    # 강점/약점 결정
    if avg_accuracy < 20:
        strength = "뛰어난 음정 정확도"
        strength_desc = "음정이 안정적이고 정확합니다."
    elif avg_warmth > 0.45:
        strength = "따뜻한 음색"
        strength_desc = "감성적인 음색으로 가사 전달력이 좋습니다."
    else:
        strength = "밝은 음색"
        strength_desc = "청명한 음색으로 찬양의 기쁨을 전달합니다."

    if avg_accuracy > 25:
        weakness = "음정 불안정"
        weakness_desc = "고음에서 음정이 흔들리는 경향이 있습니다."
    elif avg_dynamic < 12:
        weakness = "표현력 부족"
        weakness_desc = "다이나믹 변화가 적어 단조로울 수 있습니다."
    else:
        weakness = "호흡 지지"
        weakness_desc = "긴 프레이즈에서 호흡이 부족해질 수 있습니다."

    return {
        "persona_name": persona_name,
        "persona_icon": persona_icon,
        "persona_description": persona_desc,
        "signature_name": strength,
        "signature_description": strength_desc,
        "signature_evidence": {"value": f"{avg_accuracy:.1f} cents"},
        "enemy_name": weakness,
        "enemy_description": weakness_desc,
        "enemy_evidence": {"value": f"{avg_dynamic:.1f} dB"},
        "solution": "기본 연습을 꾸준히 해주세요.",
        "exercise": "호흡 연습과 음정 훈련을 병행하세요.",
        "vocal_mbti": "WL",
        "mbti_reason": "특징 기반 자동 분류",
        "overall_assessment": f"평균 음역 {avg_pitch:.0f}Hz, 다이나믹 {avg_dynamic:.1f}dB의 보컬입니다."
    }


def generate_single_fallback(features: dict) -> dict:
    """
    단일 분석 LLM 실패 시 특징 기반 기본 분석 생성
    """
    accuracy = features['pitch_accuracy_cents']
    stability = features.get('high_note_stability', 0.5)
    dynamic = features['dynamic_range_db']
    warmth = features.get('warmth_score', 0.5)

    # 강점 결정
    if accuracy < 20:
        strength = "음정이 안정적이고 정확합니다. 음악적 기초가 탄탄합니다."
    elif warmth > 0.45:
        strength = "따뜻하고 감성적인 음색이 돋보입니다. 가사 전달력이 좋습니다."
    elif dynamic > 18:
        strength = "다이나믹한 표현력이 있습니다. 감정의 기복을 잘 표현합니다."
    else:
        strength = "밝고 청명한 음색이 특징입니다."

    # 약점 결정
    if accuracy > 25:
        weakness = f"음정 정확도({accuracy:.0f} cents)를 개선하면 좋겠습니다."
    elif stability < 0.5:
        weakness = "고음에서 안정성을 높이는 연습이 필요합니다."
    elif dynamic < 12:
        weakness = "다이나믹 폭을 넓히면 표현력이 더 좋아집니다."
    else:
        weakness = "전체적으로 양호하나 꾸준한 연습이 필요합니다."

    # 팁 결정
    if accuracy > 25:
        tip = "피아노와 함께 스케일 연습을 해보세요."
    elif stability < 0.5:
        tip = "고음 발성 시 복식호흡을 의식하세요."
    else:
        tip = "다양한 장르의 곡을 연습해보세요."

    return {
        "strength": strength,
        "weakness": weakness,
        "tip": tip
    }


@dataclass
class SongRecommendation:
    """추천 곡 정보"""
    title: str
    artist: str
    reason: str
    youtube_url: str


@dataclass
class LLMAnalysisResult:
    """LLM 분석 결과"""
    persona_name: str
    persona_icon: str
    persona_description: str
    signature_name: str
    signature_description: str
    signature_evidence: dict
    enemy_name: str
    enemy_description: str
    enemy_evidence: dict
    solution: str
    exercise: str
    vocal_mbti: str
    mbti_reason: str
    overall_assessment: str
    raw_response: str
    # 추천 곡 목록
    matching_songs: List[SongRecommendation] = field(default_factory=list)
    challenge_songs: List[SongRecommendation] = field(default_factory=list)


def analyze_with_llm(features_a: dict, features_b: dict, song_title_a: str, song_title_b: str) -> LLMAnalysisResult:
    """
    LLM을 사용하여 두 곡의 보컬 특징을 분석하고 인사이트 도출
    """

    # API 키 확인
    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. fallback 분석을 사용합니다.")
        fallback = generate_fallback_analysis(features_a, features_b)
        return LLMAnalysisResult(
            persona_name=fallback["persona_name"] + " (자동 분석)",
            persona_icon=fallback["persona_icon"],
            persona_description=fallback["persona_description"],
            signature_name=fallback["signature_name"],
            signature_description=fallback["signature_description"],
            signature_evidence=fallback["signature_evidence"],
            enemy_name=fallback["enemy_name"],
            enemy_description=fallback["enemy_description"],
            enemy_evidence=fallback["enemy_evidence"],
            solution=fallback["solution"],
            exercise=fallback["exercise"],
            vocal_mbti=fallback["vocal_mbti"],
            mbti_reason=fallback["mbti_reason"],
            overall_assessment=fallback["overall_assessment"],
            raw_response="No API key - using fallback analysis"
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # 분석 데이터 준비
    analysis_data = {
        "song_a": {
            "title": song_title_a,
            "avg_pitch_hz": round(float(features_a['avg_pitch_hz']), 1),
            "pitch_min_hz": round(float(features_a['pitch_min_hz']), 1),
            "pitch_max_hz": round(float(features_a['pitch_max_hz']), 1),
            "pitch_range_semitones": round(float(features_a['pitch_range_semitones']), 1),
            "pitch_accuracy_cents": round(float(features_a['pitch_accuracy_cents']), 1),
            "pitch_stability": round(float(features_a['pitch_stability']), 2),
            "high_note_stability": round(float(features_a['high_note_stability']), 2),
            "dynamic_range_db": round(float(features_a['dynamic_range_db']), 1),
            "spectral_centroid_hz": round(float(features_a['spectral_centroid_hz']), 0),
            "warmth_score": round(float(features_a['warmth_score']), 2),
            "articulation_clarity": round(float(features_a['articulation_clarity']), 2),
            "flat_tendency": round(float(features_a['flat_tendency']), 2),
            "sharp_tendency": round(float(features_a['sharp_tendency']), 2),
            "tempo_bpm": round(float(features_a['tempo_bpm']), 0)
        },
        "song_b": {
            "title": song_title_b,
            "avg_pitch_hz": round(float(features_b['avg_pitch_hz']), 1),
            "pitch_min_hz": round(float(features_b['pitch_min_hz']), 1),
            "pitch_max_hz": round(float(features_b['pitch_max_hz']), 1),
            "pitch_range_semitones": round(float(features_b['pitch_range_semitones']), 1),
            "pitch_accuracy_cents": round(float(features_b['pitch_accuracy_cents']), 1),
            "pitch_stability": round(float(features_b['pitch_stability']), 2),
            "high_note_stability": round(float(features_b['high_note_stability']), 2),
            "dynamic_range_db": round(float(features_b['dynamic_range_db']), 1),
            "spectral_centroid_hz": round(float(features_b['spectral_centroid_hz']), 0),
            "warmth_score": round(float(features_b['warmth_score']), 2),
            "articulation_clarity": round(float(features_b['articulation_clarity']), 2),
            "flat_tendency": round(float(features_b['flat_tendency']), 2),
            "sharp_tendency": round(float(features_b['sharp_tendency']), 2),
            "tempo_bpm": round(float(features_b['tempo_bpm']), 0)
        }
    }

    prompt = f"""당신은 전문 보컬 코치입니다. 아래 두 곡의 보컬 분석 데이터를 바탕으로 이 가수의 특성을 분석해주세요.

## 분석 데이터

### Song A: {song_title_a}
{json.dumps(analysis_data['song_a'], indent=2, ensure_ascii=False)}

### Song B: {song_title_b}
{json.dumps(analysis_data['song_b'], indent=2, ensure_ascii=False)}

## 데이터 해석 가이드
- pitch_accuracy_cents: 음정 정확도 (낮을수록 좋음, 15 이하=매우 정확, 15-25=양호, 25 이상=개선 필요)
- high_note_stability: 고음 안정성 (0-1, 0.8 이상=안정적)
- dynamic_range_db: 다이나믹 레인지 (15dB 이상=표현력 풍부)
- spectral_centroid_hz: 음색 밝기 (1500 이하=따뜻함, 2500 이상=밝음)
- warmth_score: 음색 따뜻함 (0.40 이상=따뜻한 음색, 0.27-0.40=중립적, 0.27 미만=밝은 음색). 이 점수가 0.40 미만이면 "따뜻하다"고 표현하면 안됨!
- flat_tendency/sharp_tendency: 음정이 낮아지는/높아지는 경향 (0.3 이상이면 경향 있음)
- articulation_clarity: 발음 선명도 (0-1, 0.7 이상=선명)

## 응답 형식 (반드시 이 JSON 형식으로만 응답)
```json
{{
    "persona_name": "페르소나 이름 (한글, 예: 감성의 스토리텔러)",
    "persona_icon": "이모지 1개",
    "persona_description": "이 가수의 전체적인 보컬 정체성을 2-3문장으로 설명",

    "signature_name": "강점 이름 (한글+영어, 예: Dynamic Painter (다이나믹 화가))",
    "signature_description": "두 곡에서 공통적으로 발견되는 강점을 구체적인 수치와 함께 설명",
    "signature_evidence": {{
        "song_a_data": "Song A에서의 근거 수치",
        "song_b_data": "Song B에서의 근거 수치",
        "interpretation": "이 수치가 의미하는 바"
    }},

    "enemy_name": "약점 이름 (한글+영어, 예: Pitch Wanderer (음정 방랑자))",
    "enemy_description": "두 곡에서 공통적으로 발견되는 약점을 구체적인 수치와 함께 설명",
    "enemy_evidence": {{
        "song_a_data": "Song A에서의 근거 수치",
        "song_b_data": "Song B에서의 근거 수치",
        "interpretation": "이 수치가 의미하는 바"
    }},
    "solution": "약점을 극복하기 위한 구체적인 방법",
    "exercise": "오늘 바로 할 수 있는 5분 연습법",

    "vocal_mbti": "ST/WL/PA/IN/JO/SO 중 하나",
    "mbti_reason": "왜 이 타입인지 설명",

    "overall_assessment": "전체적인 평가와 격려의 말 (2-3문장)",

    "matching_songs": [
        {{
            "title": "곡 제목",
            "artist": "아티스트명",
            "reason": "이 가수의 현재 스타일과 잘 어울리는 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "곡 제목 2",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "곡 제목 3",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }}
    ],
    "challenge_songs": [
        {{
            "title": "도전곡 제목",
            "artist": "아티스트명",
            "reason": "이 곡이 약점 극복에 도움이 되는 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "도전곡 제목 2",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "도전곡 제목 3",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }}
    ]
}}
```

MBTI 타입 참고:
- ST (Storyteller): 말하듯 전하는 진정성, 따뜻한 중저음
- WL (Worship Leader): 안정적 리딩, 균형 잡힌 테크닉
- PA (Passionate): 폭발적 감정 표현, 강렬한 고음
- IN (Intimate): 속삭이듯 친밀함, 섬세한 표현
- JO (Joyful): 밝고 경쾌함, 리듬감
- SO (Soulful): 깊은 울림, 그루브와 애드립

중요:
1. 실제 데이터 수치를 근거로 분석해주세요
2. 수치가 좋지 않으면 솔직하게 약점으로 지적해주세요
3. JSON 형식만 출력하세요 (다른 텍스트 없이)

추천 곡 가이드:
- matching_songs: 이 가수의 현재 보컬 스타일에 잘 어울리는 한국 CCM/찬양 곡 3개
  - 강점을 살릴 수 있는 곡들을 추천
  - 음역대, 음색, 다이나믹 특성에 맞는 곡 선정
- challenge_songs: 약점을 극복하는 데 도움이 될 도전적인 곡 3개
  - 약점 영역을 연습할 수 있는 곡들
  - 너무 어렵지 않으면서 성장에 도움이 되는 곡 선정
- youtube_url: 유튜브 검색 URL 형식으로 작성 (예: https://www.youtube.com/results?search_query=곡제목+아티스트명)
  - 곡 제목과 아티스트를 +로 연결하고 공백은 +로 대체
"""

    try:
        # 타임아웃 적용
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            timeout=httpx.Timeout(LLM_TIMEOUT, connect=10.0),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # JSON 파싱
        # ```json ... ``` 형식이면 추출
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result_data = json.loads(json_str)

        # 추천 곡 파싱
        matching_songs = []
        for song in result_data.get("matching_songs", []):
            matching_songs.append(SongRecommendation(
                title=song.get("title", ""),
                artist=song.get("artist", ""),
                reason=song.get("reason", ""),
                youtube_url=song.get("youtube_url", "")
            ))

        challenge_songs = []
        for song in result_data.get("challenge_songs", []):
            challenge_songs.append(SongRecommendation(
                title=song.get("title", ""),
                artist=song.get("artist", ""),
                reason=song.get("reason", ""),
                youtube_url=song.get("youtube_url", "")
            ))

        return LLMAnalysisResult(
            persona_name=result_data.get("persona_name", "분석 중"),
            persona_icon=result_data.get("persona_icon", "🎤"),
            persona_description=result_data.get("persona_description", ""),
            signature_name=result_data.get("signature_name", "분석 중"),
            signature_description=result_data.get("signature_description", ""),
            signature_evidence=result_data.get("signature_evidence", {}),
            enemy_name=result_data.get("enemy_name", "분석 중"),
            enemy_description=result_data.get("enemy_description", ""),
            enemy_evidence=result_data.get("enemy_evidence", {}),
            solution=result_data.get("solution", ""),
            exercise=result_data.get("exercise", ""),
            vocal_mbti=result_data.get("vocal_mbti", "WL"),
            mbti_reason=result_data.get("mbti_reason", ""),
            overall_assessment=result_data.get("overall_assessment", ""),
            raw_response=response_text,
            matching_songs=matching_songs,
            challenge_songs=challenge_songs
        )

    except httpx.TimeoutException as e:
        # 타임아웃 시 fallback 분석 사용
        print(f"⚠️ LLM 타임아웃 ({LLM_TIMEOUT}초): fallback 분석 사용")
        fallback = generate_fallback_analysis(features_a, features_b)
        return LLMAnalysisResult(
            persona_name=fallback["persona_name"] + " (자동 분석)",
            persona_icon=fallback["persona_icon"],
            persona_description=fallback["persona_description"],
            signature_name=fallback["signature_name"],
            signature_description=fallback["signature_description"],
            signature_evidence=fallback["signature_evidence"],
            enemy_name=fallback["enemy_name"],
            enemy_description=fallback["enemy_description"],
            enemy_evidence=fallback["enemy_evidence"],
            solution=fallback["solution"],
            exercise=fallback["exercise"],
            vocal_mbti=fallback["vocal_mbti"],
            mbti_reason=fallback["mbti_reason"],
            overall_assessment=fallback["overall_assessment"],
            raw_response=f"Timeout after {LLM_TIMEOUT}s - using fallback analysis"
        )

    except anthropic.APIError as e:
        # API 오류 시 fallback 분석 사용
        print(f"⚠️ LLM API 오류: {e}")
        fallback = generate_fallback_analysis(features_a, features_b)
        return LLMAnalysisResult(
            persona_name=fallback["persona_name"] + " (자동 분석)",
            persona_icon=fallback["persona_icon"],
            persona_description=fallback["persona_description"],
            signature_name=fallback["signature_name"],
            signature_description=fallback["signature_description"],
            signature_evidence=fallback["signature_evidence"],
            enemy_name=fallback["enemy_name"],
            enemy_description=fallback["enemy_description"],
            enemy_evidence=fallback["enemy_evidence"],
            solution=fallback["solution"],
            exercise=fallback["exercise"],
            vocal_mbti=fallback["vocal_mbti"],
            mbti_reason=fallback["mbti_reason"],
            overall_assessment=fallback["overall_assessment"],
            raw_response=f"API Error: {str(e)}"
        )

    except Exception as e:
        # 기타 오류 시 fallback 분석 사용
        print(f"⚠️ LLM 오류: {e}")
        fallback = generate_fallback_analysis(features_a, features_b)
        return LLMAnalysisResult(
            persona_name=fallback["persona_name"] + " (자동 분석)",
            persona_icon=fallback["persona_icon"],
            persona_description=fallback["persona_description"],
            signature_name=fallback["signature_name"],
            signature_description=fallback["signature_description"],
            signature_evidence=fallback["signature_evidence"],
            enemy_name=fallback["enemy_name"],
            enemy_description=fallback["enemy_description"],
            enemy_evidence=fallback["enemy_evidence"],
            solution=fallback["solution"],
            exercise=fallback["exercise"],
            vocal_mbti=fallback["vocal_mbti"],
            mbti_reason=fallback["mbti_reason"],
            overall_assessment=fallback["overall_assessment"],
            raw_response=f"Error: {str(e)}"
        )


@dataclass
class SingleAnalysisResult:
    """단일 곡 LLM 분석 결과"""
    strength: str
    weakness: str
    tip: str
    matching_songs: List[SongRecommendation]
    challenge_songs: List[SongRecommendation]


def analyze_single_with_llm(features: dict, song_title: str) -> SingleAnalysisResult:
    """
    단일 곡 LLM 분석 (추천곡 포함)
    """

    # API 키 확인
    if not ANTHROPIC_API_KEY:
        print("⚠️ ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. fallback 분석을 사용합니다.")
        fallback = generate_single_fallback(features)
        return SingleAnalysisResult(
            strength=fallback["strength"] + " (자동 분석)",
            weakness=fallback["weakness"],
            tip=fallback["tip"],
            matching_songs=[],
            challenge_songs=[]
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    analysis_data = {
        "title": song_title,
        "avg_pitch_hz": round(float(features['avg_pitch_hz']), 1),
        "pitch_range_semitones": round(float(features['pitch_range_semitones']), 1),
        "pitch_accuracy_cents": round(float(features['pitch_accuracy_cents']), 1),
        "high_note_stability": round(float(features['high_note_stability']), 2),
        "dynamic_range_db": round(float(features['dynamic_range_db']), 1),
        "spectral_centroid_hz": round(float(features['spectral_centroid_hz']), 0),
        "warmth_score": round(float(features['warmth_score']), 2),
        "flat_tendency": round(float(features['flat_tendency']), 2),
        "sharp_tendency": round(float(features['sharp_tendency']), 2)
    }

    prompt = f"""보컬 분석 데이터를 바탕으로 피드백과 추천 곡을 제공해주세요.

## 데이터
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

## 해석 가이드
- pitch_accuracy_cents: 음정 정확도 (낮을수록 좋음, 15 이하=매우 정확, 25 이상=개선 필요)
- high_note_stability: 고음 안정성 (0.8 이상=안정적)
- dynamic_range_db: 다이나믹 레인지 (15dB 이상=표현력 풍부)
- spectral_centroid_hz: 음색 밝기 (1500 이하=따뜻함, 2500 이상=밝음)
- warmth_score: 음색 따뜻함 (0.40 이상=따뜻한 음색, 0.27-0.40=중립, 0.27 미만=밝은 음색). 이 점수가 0.40 미만이면 따뜻하다고 하면 안됨!

## 응답 (JSON만)
```json
{{
    "strength": "이 녹음에서 발견된 강점 (1-2문장)",
    "weakness": "개선이 필요한 부분 (1-2문장)",
    "tip": "바로 적용할 수 있는 팁 (1문장)",
    "matching_songs": [
        {{
            "title": "곡 제목",
            "artist": "아티스트명",
            "reason": "이 가수의 현재 스타일과 잘 어울리는 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "곡 제목 2",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "곡 제목 3",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }}
    ],
    "challenge_songs": [
        {{
            "title": "도전곡 제목",
            "artist": "아티스트명",
            "reason": "이 곡이 약점 극복에 도움이 되는 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "도전곡 제목 2",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }},
        {{
            "title": "도전곡 제목 3",
            "artist": "아티스트명",
            "reason": "추천 이유",
            "youtube_url": "https://www.youtube.com/results?search_query=곡제목+아티스트"
        }}
    ]
}}
```

추천 곡 가이드:
- matching_songs: 현재 보컬 스타일에 잘 어울리는 한국 CCM/찬양 곡 3개
- challenge_songs: 약점을 극복하는 데 도움이 될 도전적인 곡 3개
- youtube_url: 유튜브 검색 URL 형식으로 작성 (예: https://www.youtube.com/results?search_query=곡제목+아티스트명)
  - 곡 제목과 아티스트를 +로 연결하고 URL 인코딩된 형식으로 작성
"""

    try:
        # 타임아웃 적용
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            timeout=httpx.Timeout(LLM_TIMEOUT, connect=10.0),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result_data = json.loads(json_str)

        # 추천 곡 파싱
        matching_songs = []
        for song in result_data.get("matching_songs", []):
            matching_songs.append(SongRecommendation(
                title=song.get("title", ""),
                artist=song.get("artist", ""),
                reason=song.get("reason", ""),
                youtube_url=song.get("youtube_url", "")
            ))

        challenge_songs = []
        for song in result_data.get("challenge_songs", []):
            challenge_songs.append(SongRecommendation(
                title=song.get("title", ""),
                artist=song.get("artist", ""),
                reason=song.get("reason", ""),
                youtube_url=song.get("youtube_url", "")
            ))

        return SingleAnalysisResult(
            strength=result_data.get("strength", ""),
            weakness=result_data.get("weakness", ""),
            tip=result_data.get("tip", ""),
            matching_songs=matching_songs,
            challenge_songs=challenge_songs
        )

    except (httpx.TimeoutException, anthropic.APIError) as e:
        # 타임아웃 또는 API 오류 시 fallback 분석 사용
        print(f"⚠️ 단일 분석 LLM 오류: {e} - fallback 사용")
        fallback = generate_single_fallback(features)
        return SingleAnalysisResult(
            strength=fallback["strength"] + " (자동 분석)",
            weakness=fallback["weakness"],
            tip=fallback["tip"],
            matching_songs=[],  # fallback에서는 추천곡 제공 안함
            challenge_songs=[]
        )

    except Exception as e:
        # 기타 오류 시 fallback 분석 사용
        print(f"⚠️ 단일 분석 오류: {e} - fallback 사용")
        fallback = generate_single_fallback(features)
        return SingleAnalysisResult(
            strength=fallback["strength"] + " (자동 분석)",
            weakness=fallback["weakness"],
            tip=fallback["tip"],
            matching_songs=[],
            challenge_songs=[]
        )


# 테스트
if __name__ == "__main__":
    # 테스트 데이터
    test_features_a = {
        'avg_pitch_hz': 175.0,
        'pitch_min_hz': 120.0,
        'pitch_max_hz': 350.0,
        'pitch_range_semitones': 18.5,
        'pitch_accuracy_cents': 28.5,
        'pitch_stability': 0.65,
        'high_note_stability': 0.55,
        'dynamic_range_db': 14.5,
        'spectral_centroid_hz': 1650.0,
        'warmth_score': 0.45,
        'articulation_clarity': 0.72,
        'flat_tendency': 0.35,
        'sharp_tendency': 0.15,
        'tempo_bpm': 72
    }

    test_features_b = {
        'avg_pitch_hz': 195.0,
        'pitch_min_hz': 130.0,
        'pitch_max_hz': 400.0,
        'pitch_range_semitones': 22.0,
        'pitch_accuracy_cents': 32.0,
        'pitch_stability': 0.58,
        'high_note_stability': 0.48,
        'dynamic_range_db': 18.2,
        'spectral_centroid_hz': 2100.0,
        'warmth_score': 0.30,
        'articulation_clarity': 0.65,
        'flat_tendency': 0.40,
        'sharp_tendency': 0.12,
        'tempo_bpm': 128
    }

    print("🎤 LLM 분석 테스트 중...")
    result = analyze_with_llm(test_features_a, test_features_b, "나 무력할수록", "살아계신 주")

    print(f"\n페르소나: {result.persona_icon} {result.persona_name}")
    print(f"설명: {result.persona_description}")
    print(f"\n강점: {result.signature_name}")
    print(f"설명: {result.signature_description}")
    print(f"\n약점: {result.enemy_name}")
    print(f"설명: {result.enemy_description}")
    print(f"\nMBTI: {result.vocal_mbti}")
    print(f"이유: {result.mbti_reason}")
