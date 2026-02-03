"""
🎤 Worship Vocal AI - Dual-Core Analysis Engine
================================================

핵심 컨셉: 두 곡(느린 곡 + 빠른 곡) 비교 분석으로
더 입체적인 보컬 페르소나 도출

기존 단일 분석의 한계:
- "이 곡에서 음정이 틀렸다" (일회성)
- 유저의 전체적인 스타일 파악 불가

개선된 이중 분석:
- 두 스타일에서 공통되는 강점/약점 발견
- 스타일별 반전 매력 발견
- 더 정확한 보컬 페르소나 정의
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np

# =============================================
# 1. 데이터 구조
# =============================================

class SongStyle(Enum):
    """곡 스타일"""
    SLOW = "slow"      # Mission A: 느린 고백 찬양
    FAST = "fast"      # Mission B: 빠른 리듬 찬양


@dataclass
class SongFeatures:
    """단일 곡 분석 결과"""
    style: SongStyle
    song_title: str

    # 기본 특징
    avg_pitch_hz: float           # 평균 음역대
    pitch_range_semitones: float  # 음역 폭
    rhythm_offset_ms: float       # 박자 밀림/당김 (ms)
    spectral_centroid: float      # 음색 밝기
    dynamic_range_db: float       # 감정 표현폭

    # 추가 특징
    high_note_stability: float    # 고음 안정성 (0-1)
    vibrato_regularity: float     # 비브라토 규칙성 (0-1)
    breath_phrase_length: float   # 평균 프레이즈 길이 (초)
    articulation_clarity: float   # 발음 선명도 (0-1)

    # 음정 관련 (새로 추가)
    pitch_accuracy_cents: float = 30.0  # 음정 정확도 (cents, 낮을수록 좋음)
    pitch_stability: float = 0.7        # 음정 안정성 (0-1)

    # 구간별 데이터
    problem_sections: List[dict] = field(default_factory=list)  # 문제 구간
    highlight_sections: List[dict] = field(default_factory=list)  # 하이라이트 구간


@dataclass
class DualAnalysisResult:
    """이중 분석 결과"""
    
    # 입력
    slow_song: SongFeatures      # Mission A 결과
    fast_song: SongFeatures      # Mission B 결과
    
    # The Persona (보컬 정체성)
    persona_name: str            # 예: "반전의 승부사"
    persona_description: str     # 상세 설명
    persona_icon: str            # 이모지
    
    # The Signature (고유 강점)
    signature_name: str          # 예: "Magical Bridge"
    signature_description: str
    signature_evidence: dict     # 근거 데이터
    
    # The Hidden Enemy (공통 약점)
    enemy_name: str              # 예: "High-Note Squeeze"
    enemy_description: str
    enemy_evidence: dict
    
    # Vocal Stat Radar (5각형)
    radar_stats: dict            # {감성, 음색, 리듬, 발성, 리딩}
    
    # 기존 MBTI와 연동
    vocal_mbti: str              # ST, WL, PA, IN, JO, SO
    vocal_dna: dict              # 6차원 DNA


# =============================================
# 2. 페르소나 매핑 테이블
# =============================================

# (Slow 특성, Fast 특성) → 페르소나
PERSONA_MAPPING = {
    # 느린 곡에서 감성적 + 빠른 곡에서 리듬감
    ("emotional", "rhythmic"): {
        "name": "반전의 승부사",
        "icon": "🎭",
        "description": "발라드에선 첼로 같은 깊이를, 빠른 곡에선 타악기 같은 리듬감을 가졌어요!",
        "strength": "상황에 따라 완전히 다른 매력을 보여줄 수 있어요.",
        "mbti_tendency": "SO"  # Soulful
    },
    
    # 느린 곡에서 안정적 + 빠른 곡에서도 안정적
    ("stable", "stable"): {
        "name": "흔들림 없는 닻",
        "icon": "⚓",
        "description": "어떤 템포에서도 중심을 잃지 않는 안정감의 대명사!",
        "strength": "회중이 믿고 따라올 수 있는 리더십이 있어요.",
        "mbti_tendency": "WL"  # Worship Leader
    },
    
    # 느린 곡에서 친밀 + 빠른 곡에서 폭발
    ("intimate", "explosive"): {
        "name": "감정의 스펙트럼",
        "icon": "🌈",
        "description": "속삭임부터 폭발까지, 감정의 전 영역을 아우르는 표현력!",
        "strength": "찬양의 드라마틱한 전개를 이끌 수 있어요.",
        "mbti_tendency": "PA"  # Passionate
    },
    
    # 느린 곡에서 스토리텔링 + 빠른 곡에서도 전달력
    ("narrative", "narrative"): {
        "name": "말씀의 전달자",
        "icon": "📖",
        "description": "빠르든 느리든, 가사의 의미를 명확하게 전달하는 능력!",
        "strength": "회중이 가사에 집중하게 만드는 힘이 있어요.",
        "mbti_tendency": "ST"  # Storyteller
    },
    
    # 느린 곡에서 부드러움 + 빠른 곡에서 밝음
    ("soft", "bright"): {
        "name": "햇살 같은 위로자",
        "icon": "☀️",
        "description": "느린 곡에선 부드럽게 감싸고, 빠른 곡에선 밝게 이끌어요!",
        "strength": "분위기를 환하게 바꾸는 긍정 에너지가 있어요.",
        "mbti_tendency": "JO"  # Joyful
    },
    
    # 느린 곡에서 깊음 + 빠른 곡에서 그루브
    ("deep", "groovy"): {
        "name": "소울의 연금술사",
        "icon": "🎷",
        "description": "깊은 울림과 그루브를 동시에 가진 소울풀한 보컬!",
        "strength": "독특한 색깔로 찬양에 깊이를 더해요.",
        "mbti_tendency": "SO"  # Soulful
    },
    
    # 느린 곡에서 친밀 + 빠른 곡에서도 친밀
    ("intimate", "intimate"): {
        "name": "친밀함의 수호자",
        "icon": "🕯️",
        "description": "어떤 템포에서도 하나님과의 친밀함을 유지하는 보컬!",
        "strength": "기도 분위기를 이끄는 데 탁월해요.",
        "mbti_tendency": "IN"  # Intimate
    },
    
    # 기본 폴백
    ("default", "default"): {
        "name": "균형 잡힌 워십퍼",
        "icon": "⭐",
        "description": "다양한 스타일을 균형 있게 소화하는 올라운더!",
        "strength": "어떤 상황에서도 안정적으로 찬양을 이끌 수 있어요.",
        "mbti_tendency": "WL"
    }
}


# =============================================
# 3. 시그니처(강점) 패턴
# =============================================

SIGNATURE_PATTERNS = {
    "magical_bridge": {
        "name": "Magical Bridge (마법의 연결고리)",
        "description": "어떤 빠르기의 곡이든 멘트에서 찬양으로 넘어가는 호흡이 완벽해요.",
        "detection": "transition_smoothness > 0.8 in both songs",
        "icon": "🌉"
    },
    "emotional_consistency": {
        "name": "Emotional Anchor (감정의 닻)",
        "description": "곡 전체에서 감정의 흐름이 일관되게 유지돼요.",
        "detection": "dynamic_variance < 0.2 in both songs",
        "icon": "⚓"
    },
    "pitch_precision": {
        "name": "Pitch Sniper (음정 저격수)",
        "description": "느린 곡이든 빠른 곡이든 음정 정확도가 뛰어나요.",
        "detection": "pitch_accuracy > 0.85 in both songs",
        "icon": "🎯"
    },
    "breath_master": {
        "name": "Breath Architect (호흡의 건축가)",
        "description": "긴 프레이즈도 짧은 프레이즈도 자연스럽게 소화해요.",
        "detection": "breath_control > 0.8 in both songs",
        "icon": "🌬️"
    },
    "dynamic_storyteller": {
        "name": "Dynamic Painter (다이내믹 화가)",
        "description": "볼륨 변화로 곡의 스토리를 입체적으로 그려내요.",
        "detection": "dynamic_range > 15dB in both songs",
        "icon": "🎨"
    },
    "rhythm_keeper": {
        "name": "Rhythm Guardian (리듬의 수호자)",
        "description": "템포가 바뀌어도 정확한 박자감을 유지해요.",
        "detection": "rhythm_accuracy > 0.85 in both songs",
        "icon": "🥁"
    },
    "tone_consistency": {
        "name": "Tone Identity (음색 정체성)",
        "description": "어떤 곡에서든 '나'라는 걸 알 수 있는 일관된 음색이 있어요.",
        "detection": "spectral_similarity > 0.7 between songs",
        "icon": "🎵"
    }
}


# =============================================
# 4. 히든 에너미(약점) 패턴
# =============================================

ENEMY_PATTERNS = {
    "high_note_squeeze": {
        "name": "High-Note Squeeze (고음 조임)",
        "description": "느린 곡이든 빠른 곡이든, 특정 음역 이상에서 후두가 올라가고 소리가 얇아져요.",
        "detection": "high_note_stability < 0.6 in both songs",
        "solution": "고음에서 후두를 내리는 연습이 필요해요. 하품하듯 열린 목 상태를 유지해보세요.",
        "exercise": "립 트릴로 고음까지 올라가기 (매일 2분)",
        "icon": "😣"
    },
    "breath_shortage": {
        "name": "Breath Thief (호흡 도둑)",
        "description": "프레이즈 끝에서 호흡이 부족해지는 경향이 있어요.",
        "detection": "phrase_end_stability < 0.6 in both songs",
        "solution": "복식호흡 훈련과 프레이즈 계획이 필요해요.",
        "exercise": "숨 참기 운동 + 긴 'S' 소리 내기 (30초 목표)",
        "icon": "💨"
    },
    "rhythm_drift": {
        "name": "Rhythm Wanderer (리듬 방랑자)",
        "description": "특히 빠른 곡에서 박자가 밀리거나 당겨지는 경향이 있어요.",
        "detection": "rhythm_offset > 50ms in both songs",
        "solution": "메트로놈과 함께 연습하면서 정박 감각을 키워보세요.",
        "exercise": "메트로놈 80-120 BPM에서 박수 치기 (매일 3분)",
        "icon": "⏱️"
    },
    "dynamic_flatness": {
        "name": "Flat Liner (평평한 표현)",
        "description": "볼륨 변화가 적어서 곡이 단조롭게 느껴질 수 있어요.",
        "detection": "dynamic_range < 8dB in both songs",
        "solution": "의도적으로 크레센도/디크레센도를 넣어보세요.",
        "exercise": "한 프레이즈를 pp→ff→pp로 부르기",
        "icon": "📊"
    },
    "articulation_blur": {
        "name": "Word Fog (가사 안개)",
        "description": "특히 빠른 곡에서 가사 전달이 뭉개지는 경향이 있어요.",
        "detection": "articulation_clarity < 0.6 in fast song",
        "solution": "자음을 더 명확하게 발음하는 연습이 필요해요.",
        "exercise": "빠른 곡 가사를 또박또박 읽기 → 점점 빠르게",
        "icon": "🌫️"
    },
    "vibrato_inconsistency": {
        "name": "Shaky Vibrato (불안정한 떨림)",
        "description": "비브라토가 불규칙하거나 과도하게 들어가요.",
        "detection": "vibrato_regularity < 0.5 in both songs",
        "solution": "자연스러운 비브라토를 위해 횡격막 조절 연습이 필요해요.",
        "exercise": "일정한 박자로 '아~아~아~' 비브라토 연습",
        "icon": "〰️"
    }
}


# =============================================
# 5. 이중 분석 엔진
# =============================================

class DualCoreAnalyzer:
    """이중 분석 엔진"""
    
    def __init__(self):
        self.persona_map = PERSONA_MAPPING
        self.signature_patterns = SIGNATURE_PATTERNS
        self.enemy_patterns = ENEMY_PATTERNS
    
    def analyze(self, slow_features: SongFeatures, fast_features: SongFeatures) -> DualAnalysisResult:
        """두 곡 비교 분석 실행"""
        
        # 1. 각 곡의 특성 분류
        slow_trait = self._classify_trait(slow_features)
        fast_trait = self._classify_trait(fast_features)
        
        # 2. 페르소나 결정
        persona = self._determine_persona(slow_trait, fast_trait)
        
        # 3. 시그니처 (공통 강점) 발견
        signature = self._find_signature(slow_features, fast_features)
        
        # 4. 히든 에너미 (공통 약점) 발견
        enemy = self._find_enemy(slow_features, fast_features)
        
        # 5. 레이더 차트 스탯 계산
        radar_stats = self._calculate_radar(slow_features, fast_features)
        
        # 6. 기존 MBTI/DNA 연동
        vocal_mbti = persona["mbti_tendency"]
        vocal_dna = self._calculate_dna(slow_features, fast_features)
        
        return DualAnalysisResult(
            slow_song=slow_features,
            fast_song=fast_features,
            persona_name=persona["name"],
            persona_description=persona["description"],
            persona_icon=persona["icon"],
            signature_name=signature["name"],
            signature_description=signature["description"],
            signature_evidence=signature["evidence"],
            enemy_name=enemy["name"],
            enemy_description=enemy["description"],
            enemy_evidence=enemy["evidence"],
            radar_stats=radar_stats,
            vocal_mbti=vocal_mbti,
            vocal_dna=vocal_dna
        )
    
    def _classify_trait(self, features: SongFeatures) -> str:
        """곡의 주요 특성 분류"""
        
        traits = {
            "emotional": features.dynamic_range_db > 15,
            "stable": features.high_note_stability > 0.8,
            "intimate": features.spectral_centroid < 1800 and features.dynamic_range_db < 12,
            "explosive": features.dynamic_range_db > 20,
            "narrative": features.articulation_clarity > 0.8,
            "soft": features.spectral_centroid < 1600,
            "bright": features.spectral_centroid > 2200,
            "deep": features.spectral_centroid < 1500,
            "groovy": features.rhythm_offset_ms < 30,
            "rhythmic": features.rhythm_offset_ms < 25
        }
        
        # 가장 강한 특성 반환
        for trait, condition in traits.items():
            if condition:
                return trait
        
        return "default"
    
    def _determine_persona(self, slow_trait: str, fast_trait: str) -> dict:
        """페르소나 결정"""
        
        key = (slow_trait, fast_trait)
        
        if key in self.persona_map:
            return self.persona_map[key]
        
        # 순서 바꿔서 찾기
        key_reversed = (fast_trait, slow_trait)
        if key_reversed in self.persona_map:
            return self.persona_map[key_reversed]
        
        # 기본값
        return self.persona_map[("default", "default")]
    
    def _find_signature(self, slow: SongFeatures, fast: SongFeatures) -> dict:
        """공통 강점 발견"""
        
        signatures_found = []
        
        # 각 패턴 검사
        if slow.articulation_clarity > 0.7 and fast.articulation_clarity > 0.7:
            signatures_found.append({
                **self.signature_patterns["magical_bridge"],
                "evidence": {
                    "slow_clarity": slow.articulation_clarity,
                    "fast_clarity": fast.articulation_clarity
                }
            })
        
        # 음정 정확도 체크 (cents가 낮을수록 좋음, 15 이하면 매우 정확)
        if slow.pitch_accuracy_cents < 20 and fast.pitch_accuracy_cents < 20:
            signatures_found.append({
                **self.signature_patterns["pitch_precision"],
                "evidence": {
                    "song_a_accuracy": f"{slow.pitch_accuracy_cents:.1f} cents",
                    "song_b_accuracy": f"{fast.pitch_accuracy_cents:.1f} cents",
                    "판정": "매우 정확 (20 cents 미만)"
                }
            })

        # 고음 안정성 체크 (별도 시그니처)
        if slow.high_note_stability > 0.8 and fast.high_note_stability > 0.8:
            signatures_found.append({
                "name": "High Note Master (고음 마스터)",
                "description": "어떤 곡에서든 고음 구간이 흔들림 없이 안정적이에요.",
                "icon": "🎤",
                "evidence": {
                    "song_a_stability": f"{slow.high_note_stability*100:.0f}%",
                    "song_b_stability": f"{fast.high_note_stability*100:.0f}%"
                }
            })
        
        if slow.dynamic_range_db > 12 and fast.dynamic_range_db > 12:
            signatures_found.append({
                **self.signature_patterns["dynamic_storyteller"],
                "evidence": {
                    "slow_dynamic": slow.dynamic_range_db,
                    "fast_dynamic": fast.dynamic_range_db
                }
            })
        
        if slow.breath_phrase_length > 6 and fast.breath_phrase_length > 4:
            signatures_found.append({
                **self.signature_patterns["breath_master"],
                "evidence": {
                    "slow_phrase": slow.breath_phrase_length,
                    "fast_phrase": fast.breath_phrase_length
                }
            })
        
        # 가장 강한 시그니처 반환
        if signatures_found:
            return signatures_found[0]
        
        # 기본 시그니처
        return {
            "name": "Hidden Gem (숨겨진 보석)",
            "description": "아직 발견되지 않은 당신만의 강점이 있어요. 더 많은 곡을 분석해보세요!",
            "icon": "💎",
            "evidence": {}
        }
    
    def _find_enemy(self, slow: SongFeatures, fast: SongFeatures) -> dict:
        """공통 약점 발견"""
        
        enemies_found = []
        
        # 각 패턴 검사
        if slow.high_note_stability < 0.6 and fast.high_note_stability < 0.6:
            enemies_found.append({
                **self.enemy_patterns["high_note_squeeze"],
                "evidence": {
                    "slow_stability": slow.high_note_stability,
                    "fast_stability": fast.high_note_stability
                }
            })
        
        if slow.breath_phrase_length < 4 and fast.breath_phrase_length < 3:
            enemies_found.append({
                **self.enemy_patterns["breath_shortage"],
                "evidence": {
                    "slow_phrase": slow.breath_phrase_length,
                    "fast_phrase": fast.breath_phrase_length
                }
            })
        
        if slow.rhythm_offset_ms > 50 or fast.rhythm_offset_ms > 50:
            enemies_found.append({
                **self.enemy_patterns["rhythm_drift"],
                "evidence": {
                    "slow_offset": slow.rhythm_offset_ms,
                    "fast_offset": fast.rhythm_offset_ms
                }
            })
        
        if slow.dynamic_range_db < 8 and fast.dynamic_range_db < 8:
            enemies_found.append({
                **self.enemy_patterns["dynamic_flatness"],
                "evidence": {
                    "slow_dynamic": slow.dynamic_range_db,
                    "fast_dynamic": fast.dynamic_range_db
                }
            })
        
        if fast.articulation_clarity < 0.6:
            enemies_found.append({
                **self.enemy_patterns["articulation_blur"],
                "evidence": {
                    "fast_clarity": fast.articulation_clarity
                }
            })
        
        # 가장 심각한 약점 반환
        if enemies_found:
            return enemies_found[0]
        
        # 약점 없음
        return {
            "name": "No Major Enemy (큰 약점 없음)",
            "description": "두 곡에서 공통되는 큰 약점이 발견되지 않았어요! 하지만 항상 개선할 점은 있답니다.",
            "icon": "✨",
            "evidence": {}
        }
    
    def _calculate_radar(self, slow: SongFeatures, fast: SongFeatures) -> dict:
        """5각형 레이더 스탯 계산"""
        
        # 두 곡의 평균으로 계산
        return {
            "감성": min(100, (slow.dynamic_range_db + fast.dynamic_range_db) / 2 * 4),
            "음색": min(100, 100 - abs(slow.spectral_centroid - 1800) / 20),
            "리듬": min(100, 100 - (slow.rhythm_offset_ms + fast.rhythm_offset_ms) / 2),
            "발성": min(100, (slow.high_note_stability + fast.high_note_stability) / 2 * 100),
            "리딩": min(100, (slow.articulation_clarity + fast.articulation_clarity) / 2 * 100)
        }
    
    def _calculate_dna(self, slow: SongFeatures, fast: SongFeatures) -> dict:
        """6차원 보컬 DNA 계산"""
        
        avg_centroid = (slow.spectral_centroid + fast.spectral_centroid) / 2
        avg_dynamic = (slow.dynamic_range_db + fast.dynamic_range_db) / 2
        avg_stability = (slow.high_note_stability + fast.high_note_stability) / 2
        
        return {
            "따뜻함": max(0, min(100, (3000 - avg_centroid) / 15)),
            "파워": max(0, min(100, avg_dynamic * 4)),
            "안정성": avg_stability * 100,
            "표현력": max(0, min(100, avg_dynamic * 3)),
            "그루브": max(0, min(100, 100 - (slow.rhythm_offset_ms + fast.rhythm_offset_ms) / 2)),
            "친밀감": max(0, min(100, 100 - avg_dynamic * 2))
        }


# =============================================
# 6. 출력 포맷팅
# =============================================

def format_dual_analysis_report(result: DualAnalysisResult) -> str:
    """이중 분석 리포트 포맷팅"""
    
    output = []
    
    # 헤더
    output.append("=" * 60)
    output.append("🎤 WORSHIP VOCAL AI - 종합 보컬 프로파일")
    output.append("=" * 60)
    output.append("")
    
    # 분석 곡 정보
    output.append(f"📀 분석 곡")
    output.append(f"   Mission A (느린 곡): {result.slow_song.song_title}")
    output.append(f"   Mission B (빠른 곡): {result.fast_song.song_title}")
    output.append("")
    
    # The Persona
    output.append("─" * 60)
    output.append(f"{result.persona_icon} THE PERSONA: {result.persona_name}")
    output.append("─" * 60)
    output.append(f"   {result.persona_description}")
    output.append("")
    
    # The Signature
    output.append("─" * 60)
    output.append(f"⭐ YOUR SIGNATURE: {result.signature_name}")
    output.append("─" * 60)
    output.append(f"   {result.signature_description}")
    if result.signature_evidence:
        output.append(f"   📊 근거: {result.signature_evidence}")
    output.append("")
    
    # The Hidden Enemy
    output.append("─" * 60)
    output.append(f"🎯 HIDDEN ENEMY: {result.enemy_name}")
    output.append("─" * 60)
    output.append(f"   {result.enemy_description}")
    if result.enemy_evidence:
        output.append(f"   📊 근거: {result.enemy_evidence}")
    output.append("")
    
    # Radar Stats
    output.append("─" * 60)
    output.append("📊 VOCAL STAT RADAR")
    output.append("─" * 60)
    for stat, value in result.radar_stats.items():
        bar = "█" * int(value / 5) + "░" * (20 - int(value / 5))
        output.append(f"   {stat:6} {bar} {value:.0f}")
    output.append("")
    
    # MBTI & DNA
    output.append("─" * 60)
    output.append(f"🧬 VOCAL IDENTITY")
    output.append("─" * 60)
    output.append(f"   MBTI 타입: {result.vocal_mbti}")
    output.append(f"   DNA: {result.vocal_dna}")
    output.append("")
    
    output.append("=" * 60)
    
    return "\n".join(output)


# =============================================
# 7. 테스트
# =============================================

def test_dual_core_analysis():
    """이중 분석 테스트"""
    
    print("🎤 Dual-Core Analysis Engine 테스트")
    print("=" * 60)
    
    # 테스트 데이터: Mission A (느린 곡)
    slow_song = SongFeatures(
        style=SongStyle.SLOW,
        song_title="나 무력할수록",
        avg_pitch_hz=175.0,
        pitch_range_semitones=18.5,
        rhythm_offset_ms=25.0,
        spectral_centroid=1650.0,
        dynamic_range_db=14.5,
        high_note_stability=0.72,
        vibrato_regularity=0.65,
        breath_phrase_length=7.2,
        articulation_clarity=0.78
    )
    
    # 테스트 데이터: Mission B (빠른 곡)
    fast_song = SongFeatures(
        style=SongStyle.FAST,
        song_title="살아계신 주",
        avg_pitch_hz=195.0,
        pitch_range_semitones=22.0,
        rhythm_offset_ms=35.0,
        spectral_centroid=2100.0,
        dynamic_range_db=18.2,
        high_note_stability=0.58,
        vibrato_regularity=0.45,
        breath_phrase_length=4.5,
        articulation_clarity=0.65
    )
    
    # 분석 실행
    analyzer = DualCoreAnalyzer()
    result = analyzer.analyze(slow_song, fast_song)
    
    # 결과 출력
    report = format_dual_analysis_report(result)
    print(report)
    
    return result


if __name__ == "__main__":
    test_dual_core_analysis()
