"""
🎤 Worship Vocal AI Coach
===========================

통합 Streamlit 앱 - 단일 분석 + 이중 분석(Dual-Core) 지원

사용법 (로컬에서):
    source venv/bin/activate
    streamlit run app.py
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import librosa

# 페이지 설정
st.set_page_config(
    page_title="Worship Vocal AI Coach",
    page_icon="🎤",
    layout="wide"
)

# =============================================
# Premium UI 스타일 적용
# =============================================
from components.styles import inject_custom_css
from components.charts import CHART_THEME, get_premium_layout, style_radar_chart, style_bar_chart, style_line_chart, style_histogram

inject_custom_css()

# =============================================
# P0 UX 개선: 전문 용어 번역 시스템
# =============================================
TERM_TRANSLATIONS = {
    "Spectral Centroid": "음색 밝기",
    "Dynamic Range": "강약 표현 폭",
    "Pitch Accuracy": "음정 정확도",
    "Pitch Stability": "음 안정성",
    "RMS": "평균 음량",
    "Vibrato Ratio": "떨림 정도",
    "Breath Support": "호흡 지지력",
    "High Note Stability": "고음 안정성",
    "Articulation": "발음 명료도",
    "Rhythm Offset": "리듬 정확도",
}

TERM_HELP = {
    "음색 밝기": "음색이 밝은지 따뜻한지를 나타냅니다. 낮을수록 따뜻하고, 높을수록 밝습니다.",
    "강약 표현 폭": "가장 작은 소리와 가장 큰 소리의 차이입니다. 넓을수록 표현력이 풍부합니다.",
    "음정 정확도": "목표 음정과의 차이입니다. 낮을수록 정확합니다. (단위: cents, 100 cents = 반음)",
    "음 안정성": "음을 유지할 때 얼마나 흔들리지 않는지 나타냅니다.",
    "평균 음량": "전체적인 소리 크기입니다.",
    "떨림 정도": "비브라토(의도적 떨림)의 정도입니다.",
    "호흡 지지력": "한 호흡으로 얼마나 길게 노래할 수 있는지 나타냅니다.",
    "고음 안정성": "높은 음에서 얼마나 안정적으로 소리를 유지하는지 나타냅니다.",
    "발음 명료도": "가사가 얼마나 또렷하게 전달되는지 나타냅니다.",
    "리듬 정확도": "박자에 얼마나 정확하게 맞추는지 나타냅니다.",
}

# P0 UX 개선: 백분위 기준 (통계 기반)
PERCENTILE_THRESHOLDS = {
    "pitch_accuracy_cents": [
        (0, 15, "상위 10%", "delta_good"),
        (15, 25, "상위 30%", "delta_good"),
        (25, 35, "평균", "delta_neutral"),
        (35, 100, "연습 필요", "delta_bad"),
    ],
    "high_note_stability": [
        (80, 101, "상위 10%", "delta_good"),
        (60, 80, "상위 30%", "delta_good"),
        (40, 60, "평균", "delta_neutral"),
        (0, 40, "연습 필요", "delta_bad"),
    ],
    "dynamic_range": [
        (18, 100, "상위 10%", "delta_good"),
        (14, 18, "상위 30%", "delta_good"),
        (10, 14, "평균", "delta_neutral"),
        (0, 10, "표현력 부족", "delta_bad"),
    ],
}

def get_percentile_badge(metric: str, value: float) -> tuple:
    """점수에 대한 백분위 뱃지 반환"""
    thresholds = PERCENTILE_THRESHOLDS.get(metric, [])
    for min_v, max_v, label, delta_type in thresholds:
        if min_v <= value < max_v:
            return label, delta_type
    return "", "delta_neutral"

# P0 UX 개선: 분석 진행 단계
ANALYSIS_STEPS = [
    ("🎵 오디오 로딩 중...", "파일을 읽고 있어요", 5),
    ("🎭 보컬 분리 중...", "AI가 목소리만 추출하고 있어요 (1-3분)", 25),
    ("📊 음성 분석 중...", "피치, 음량, 음색을 분석하고 있어요", 55),
    ("🧬 보컬 DNA 계산 중...", "당신의 보컬 스타일을 파악하고 있어요", 75),
    ("🤖 AI 코칭 생성 중...", "맞춤 피드백을 작성하고 있어요", 90),
    ("✅ 완료!", "분석이 끝났어요!", 100),
]

# =============================================
# 유틸리티 함수
# =============================================

def time_to_seconds(t: str) -> int:
    """시간 문자열을 초로 변환"""
    if not t:
        return None
    parts = t.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return int(t)


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """파일명으로 사용할 수 있도록 문자열 정리"""
    import re
    # 특수문자 제거 (한글, 영문, 숫자, 공백, 하이픈, 언더스코어만 허용)
    sanitized = re.sub(r'[^\w\s가-힣-]', '', title)
    # 연속 공백을 언더스코어로
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    # 길이 제한
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized or "untitled"


def extract_youtube_audio(url: str, start_time: str, end_time: str, output_name: str = None) -> tuple:
    """YouTube에서 오디오 추출 (pytubefix 사용)

    Returns:
        tuple: (오디오 파일 경로, 영상 제목)
    """
    import subprocess
    from pytubefix import YouTube

    # pytubefix로 영상 정보 가져오기
    yt = YouTube(url)
    video_title = yt.title or "untitled"

    # 영상 제목을 파일명으로 사용 (output_name이 없거나 generic한 경우)
    if not output_name or output_name in ["mission_a", "mission_b", "single", "single_analysis"]:
        safe_name = sanitize_filename(video_title)
    else:
        safe_name = output_name

    output_path = f"/tmp/{safe_name}.mp3"

    audio_stream = yt.streams.get_audio_only()

    if not audio_stream:
        raise Exception("오디오 스트림을 찾을 수 없습니다")

    downloaded_file = audio_stream.download(output_path='/tmp', filename=f"{safe_name}_full")

    # 구간 추출 (ffmpeg 사용)
    start_sec = time_to_seconds(start_time)
    end_sec = time_to_seconds(end_time) if end_time else None

    if start_sec and end_sec and end_sec > start_sec:
        duration = end_sec - start_sec
        cmd = ["ffmpeg", "-y", "-i", downloaded_file, "-ss", str(start_sec),
               "-t", str(duration), "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path]
        subprocess.run(cmd, check=True, capture_output=True)
    else:
        # 전체 파일을 mp3로 변환
        cmd = ["ffmpeg", "-y", "-i", downloaded_file, "-vn", "-acodec", "libmp3lame", "-q:a", "2", output_path]
        subprocess.run(cmd, check=True, capture_output=True)

    return output_path, video_title


def analyze_audio_features(audio_path: str, include_timeseries: bool = False) -> dict:
    """오디오 파일에서 특징 추출

    Args:
        audio_path: 오디오 파일 경로
        include_timeseries: True면 시계열 데이터도 포함 (차트용)
    """
    y, sr = librosa.load(audio_path, sr=22050)
    duration = len(y) / sr

    # 피치 추출
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=80, fmax=800, sr=sr)
    valid_f0 = f0[~np.isnan(f0)]

    # 피치 시간축
    hop_length = 512
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    # RMS (볼륨)
    rms = librosa.feature.rms(y=y)[0]
    rms_db = librosa.amplitude_to_db(rms + 1e-10)
    rms_times = librosa.times_like(rms, sr=sr, hop_length=hop_length)

    # 스펙트럼
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_times = librosa.times_like(centroid, sr=sr, hop_length=hop_length)

    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    zcr_times = librosa.times_like(zcr, sr=sr, hop_length=hop_length)

    # 템포 및 비트 추출
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)

    # 리듬 오프셋 실측 (onset-beat 동기화)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)

    # 각 onset이 가장 가까운 beat와 얼마나 떨어져 있는지 계산
    rhythm_offsets = []
    if len(beat_times) > 0 and len(onset_times) > 0:
        for onset in onset_times:
            closest_beat_idx = np.argmin(np.abs(beat_times - onset))
            offset_ms = abs(onset - beat_times[closest_beat_idx]) * 1000  # ms
            rhythm_offsets.append(offset_ms)
        rhythm_offset_ms = float(np.mean(rhythm_offsets)) if rhythm_offsets else 50.0
    else:
        rhythm_offset_ms = 50.0  # 비트/온셋 없으면 중립값

    # 피치 통계
    if len(valid_f0) > 0:
        pitch_mean = np.mean(valid_f0)
        pitch_std = np.std(valid_f0)
        pitch_min = np.min(valid_f0)
        pitch_max = np.max(valid_f0)
        pitch_range = librosa.hz_to_midi(pitch_max) - librosa.hz_to_midi(pitch_min)

        # 음정 정확도 (cents)
        midi_notes = librosa.hz_to_midi(valid_f0)
        rounded_midi = np.round(midi_notes)
        pitch_errors = (midi_notes - rounded_midi) * 100  # cents
        pitch_accuracy = np.mean(np.abs(pitch_errors))

        # 경향
        flat_ratio = np.sum(pitch_errors < -10) / len(pitch_errors)
        sharp_ratio = np.sum(pitch_errors > 10) / len(pitch_errors)

        # 고/저음 비율
        high_threshold = np.percentile(valid_f0, 75)
        high_ratio = np.sum(valid_f0 > high_threshold) / len(valid_f0)
        low_threshold = np.percentile(valid_f0, 25)
        low_ratio = np.sum(valid_f0 < low_threshold) / len(valid_f0)

        # 고음 안정성 (센트 기반 - Hz 기반보다 정확)
        high_notes = valid_f0[valid_f0 > high_threshold]
        if len(high_notes) > 10:
            # Hz를 MIDI (반음 단위)로 변환 후 표준편차 계산
            high_notes_midi = librosa.hz_to_midi(high_notes)
            high_notes_std_semitones = np.std(high_notes_midi)
            # 수정된 기준: 4.0 반음 (더 관대), 최소 20%
            # 0.5 반음 std → 87%, 1.5 반음 → 62%, 3.0 반음 → 25%, 4.0+ 반음 → 20%
            raw_stability = 1 - (high_notes_std_semitones / 4.0)
            high_note_stability = max(0.2, min(1, raw_stability))  # 최소 20% 보장
        else:
            high_note_stability = 0.6  # 데이터 부족시 중립값 (약간 높게)
    else:
        pitch_mean = 200
        pitch_std = 50
        pitch_min = 100
        pitch_max = 400
        pitch_range = 20
        pitch_accuracy = 30
        pitch_errors = np.array([0])
        flat_ratio = 0.3
        sharp_ratio = 0.3
        high_ratio = 0.2
        low_ratio = 0.2
        high_note_stability = 0.7
        high_threshold = 300
        low_threshold = 150

    # 다이나믹 레인지
    dynamic_range = np.max(rms_db) - np.percentile(rms_db, 10)

    # 다이나믹 점수 (전문가 패널 권장: 12-20dB가 최적)
    if dynamic_range < 12:
        dynamic_score = (dynamic_range / 12) * 0.5  # 0-50%
    elif dynamic_range <= 22:
        dynamic_score = 0.5 + ((dynamic_range - 12) / 10) * 0.5  # 50-100%
    else:
        dynamic_score = max(0.6, 1.0 - (dynamic_range - 22) * 0.02)  # 100에서 감소

    # 비브라토 분석 (주기성 검출로 의도적 비브라토 vs 불안정 구분)
    vibrato_rate = 0.0  # 비브라토 주파수 (Hz)
    vibrato_depth = 0.0  # 비브라토 깊이 (반음)
    vibrato_regularity = 0.0  # 비브라토 규칙성 (0-1)
    is_intentional_vibrato = False

    if len(valid_f0) > 50:
        # 피치를 센트(cents)로 변환 (음악적 단위)
        f0_cents = 1200 * np.log2(valid_f0 / (pitch_mean + 1e-6))

        # 자기상관(autocorrelation)으로 주기성 검출
        f0_centered = f0_cents - np.mean(f0_cents)
        autocorr = np.correlate(f0_centered, f0_centered, mode='full')
        autocorr = autocorr[len(autocorr)//2:]  # 양의 lag만
        autocorr = autocorr / (autocorr[0] + 1e-10)  # 정규화

        # 비브라토 주파수 범위: 4-8 Hz (일반적 비브라토 범위)
        # hop_length=512, sr=22050 → 약 43 frames/sec
        frames_per_sec = sr / hop_length
        min_lag = int(frames_per_sec / 8)  # 8 Hz
        max_lag = int(frames_per_sec / 4)  # 4 Hz

        if max_lag < len(autocorr) and min_lag > 0:
            # 비브라토 범위에서 피크 찾기
            vibrato_region = autocorr[min_lag:max_lag]
            if len(vibrato_region) > 0:
                peak_idx = np.argmax(vibrato_region)
                peak_value = vibrato_region[peak_idx]

                # 비브라토 판정: 자기상관 피크가 0.3 이상이면 주기적
                if peak_value > 0.3:
                    actual_lag = min_lag + peak_idx
                    vibrato_rate = frames_per_sec / actual_lag  # Hz
                    vibrato_depth = np.std(f0_cents) / 100  # 반음 단위
                    vibrato_regularity = float(peak_value)
                    is_intentional_vibrato = True

    # 비브라토 비율 (하위 호환성)
    if is_intentional_vibrato:
        # 의도적 비브라토: 깊이와 규칙성 기반
        vibrato_ratio = min(1.0, vibrato_depth * vibrato_regularity * 2)
    else:
        # 불안정한 피치 변동
        vibrato_ratio = pitch_std / (pitch_mean + 1e-6)
        vibrato_ratio = min(1.0, vibrato_ratio * 10)

    # 발음 선명도 개선 (spectral flux + centroid 결합)
    # Spectral flux (스펙트럼 변화율) - 발음이 또렷할수록 높음
    S = np.abs(librosa.stft(y, hop_length=hop_length))
    spectral_flux = np.mean(np.diff(S, axis=1) ** 2)
    flux_normalized = min(1.0, spectral_flux / 0.1)

    # Spectral centroid 점수 (1500-2500Hz가 최적, 너무 낮거나 높으면 감점)
    mean_centroid = np.mean(centroid)
    centroid_score = max(0, 1 - abs(mean_centroid - 2000) / 2000)

    # 결합: centroid 60% + flux 40%
    articulation_clarity = centroid_score * 0.6 + flux_normalized * 0.4

    # 프레이즈 길이 실측 (RMS 기반)
    rms_threshold = np.percentile(rms_db, 25)  # 하위 25%를 '쉬는 구간'
    phrase_lengths = []
    current_length = 0
    for db_val in rms_db:
        if db_val > rms_threshold:
            current_length += hop_length / sr
        elif current_length > 0.5:  # 0.5초 이상 유효 프레이즈
            phrase_lengths.append(current_length)
            current_length = 0
        else:
            current_length = 0
    if current_length > 0.5:
        phrase_lengths.append(current_length)
    phrase_length = np.mean(phrase_lengths) if phrase_lengths else 3.0

    # 호흡 지지 점수 (4초=50%, 8초=100%)
    breath_support_score = min(1.0, max(0, (phrase_length - 2) / 6))

    result = {
        'duration': duration,
        'avg_pitch_hz': pitch_mean,
        'pitch_min_hz': pitch_min,
        'pitch_max_hz': pitch_max,
        'pitch_std': pitch_std,
        'pitch_range_semitones': pitch_range,
        'pitch_accuracy_cents': pitch_accuracy,
        'pitch_stability': 1 - (pitch_std / (pitch_mean + 1e-6)),
        'high_note_ratio': high_ratio,
        'low_note_ratio': low_ratio,
        'high_note_stability': high_note_stability,
        'high_threshold_hz': high_threshold if len(valid_f0) > 0 else 300,
        'low_threshold_hz': low_threshold if len(valid_f0) > 0 else 150,
        'dynamic_range_db': dynamic_range,
        'dynamic_score': dynamic_score,  # 0-1, 다이나믹 점수 (최적 범위 반영)
        'rms_db_max': np.max(rms_db),
        'rms_db_mean': np.mean(rms_db),
        'energy_variance': np.std(rms),
        'climax_intensity': np.max(rms) / (np.mean(rms) + 1e-6),
        'spectral_centroid_hz': np.mean(centroid),
        'warmth_score': 1 - (np.mean(centroid) / 3000),
        'vibrato_ratio': vibrato_ratio,
        'vibrato_rate_hz': vibrato_rate,  # 비브라토 주파수 (4-8 Hz가 자연스러움)
        'vibrato_depth_semitones': vibrato_depth,  # 비브라토 깊이 (반음)
        'vibrato_regularity': vibrato_regularity,  # 규칙성 (0-1, 높을수록 의도적)
        'is_intentional_vibrato': is_intentional_vibrato,  # 의도적 비브라토 여부
        'tempo_bpm': tempo,
        'rhythm_offset_ms': rhythm_offset_ms,  # onset-beat 동기화 측정
        'breath_phrase_length': phrase_length,
        'breath_support_score': breath_support_score,  # 0-1, 호흡 지지 점수
        'articulation_clarity': articulation_clarity,
        'flat_tendency': flat_ratio,
        'sharp_tendency': sharp_ratio,
        'rms_mean': np.mean(rms),
        'voiced_ratio': len(valid_f0) / len(f0) if len(f0) > 0 else 0.7,
        'sample_rate': sr
    }

    # 시계열 데이터 (차트용)
    if include_timeseries:
        result['timeseries'] = {
            'waveform': y,
            'f0': f0,
            'f0_times': times,
            'valid_f0': valid_f0,
            'pitch_errors': pitch_errors,
            'rms': rms,
            'rms_db': rms_db,
            'rms_times': rms_times,
            'centroid': centroid,
            'centroid_times': centroid_times,
            'zcr': zcr,
            'zcr_times': zcr_times
        }

    return result


def create_radar_chart(stats: dict, title: str = "보컬 스탯 레이더") -> go.Figure:
    """5각형 레이더 차트 생성"""
    categories = list(stats.keys())
    values = list(stats.values())

    # 닫힌 다각형을 위해 첫 번째 값 추가
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(201, 169, 98, 0.2)',
        line=dict(color=CHART_THEME["colors"]["gold"], width=2.5),
        marker=dict(
            size=8,
            color=CHART_THEME["colors"]["gold"],
            line=dict(color=CHART_THEME["backgrounds"]["paper"], width=2)
        ),
        name='현재 스탯',
        hovertemplate='%{theta}: %{r:.0f}<extra></extra>'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=CHART_THEME["backgrounds"]["plot"],
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color=CHART_THEME["text"]["muted"], size=10),
                gridcolor=CHART_THEME["backgrounds"]["grid"],
                linecolor=CHART_THEME["backgrounds"]["grid"],
            ),
            angularaxis=dict(
                tickfont=dict(color=CHART_THEME["text"]["primary"], size=12),
                gridcolor=CHART_THEME["backgrounds"]["grid"],
                linecolor=CHART_THEME["backgrounds"]["grid"],
            ),
        ),
        paper_bgcolor=CHART_THEME["backgrounds"]["paper"],
        showlegend=False,
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=16, color=CHART_THEME["text"]["primary"])
        ),
        height=400,
        margin=dict(l=80, r=80, t=60, b=40)
    )

    return fig


def create_dna_chart(dna: dict) -> go.Figure:
    """6차원 DNA 차트 생성"""
    categories = list(dna.keys())
    values = list(dna.values())

    # 프리미엄 색상 팔레트
    colors = [
        CHART_THEME["colors"]["gold"],
        CHART_THEME["colors"]["purple"],
        CHART_THEME["colors"]["success"],
        CHART_THEME["colors"]["info"],
        CHART_THEME["colors"]["pink"],
        CHART_THEME["colors"]["warning"]
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{v:.0f}' for v in values],
        textposition='outside',
        textfont=dict(color=CHART_THEME["text"]["primary"], size=13)
    ))

    fig.update_layout(
        **get_premium_layout(
            title="보컬 DNA",
            yaxis=dict(range=[0, 115], title="점수")
        ),
        height=350,
        bargap=0.3
    )

    return fig


# =============================================
# 기술적 분석 시각화 함수
# =============================================

def create_waveform_chart(y: np.ndarray, sr: int) -> go.Figure:
    """파형 차트 생성"""
    # 다운샘플링 (성능을 위해)
    downsample_factor = max(1, len(y) // 5000)
    y_down = y[::downsample_factor]
    times = np.arange(len(y_down)) * downsample_factor / sr

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, y=y_down,
        mode='lines',
        line=dict(color=CHART_THEME["colors"]["cyan"], width=0.8),
        fill='tozeroy',
        fillcolor='rgba(34, 211, 238, 0.1)',
        name='Waveform'
    ))

    fig.update_layout(
        **get_premium_layout(title="Waveform"),
        xaxis_title='Time (seconds)',
        yaxis_title='Amplitude',
        height=200,
        showlegend=False
    )

    return fig


def create_pitch_tracking_chart(f0: np.ndarray, times: np.ndarray, high_thresh: float, low_thresh: float) -> go.Figure:
    """피치 트래킹 차트 (레지스터별 색상 구분)"""
    fig = go.Figure()

    # 유효한 피치만 추출
    valid_mask = ~np.isnan(f0)
    valid_times = times[valid_mask]
    valid_f0 = f0[valid_mask]

    if len(valid_f0) > 0:
        # 저음 (파랑)
        low_mask = valid_f0 < low_thresh
        if np.any(low_mask):
            fig.add_trace(go.Scatter(
                x=valid_times[low_mask], y=valid_f0[low_mask],
                mode='markers',
                marker=dict(color=CHART_THEME["colors"]["info"], size=4),
                name=f'Low (<{low_thresh:.0f}Hz)'
            ))

        # 중음 (초록)
        mid_mask = (valid_f0 >= low_thresh) & (valid_f0 <= high_thresh)
        if np.any(mid_mask):
            fig.add_trace(go.Scatter(
                x=valid_times[mid_mask], y=valid_f0[mid_mask],
                mode='markers',
                marker=dict(color=CHART_THEME["colors"]["success"], size=4),
                name='Mid'
            ))

        # 고음 (빨강)
        high_mask = valid_f0 > high_thresh
        if np.any(high_mask):
            fig.add_trace(go.Scatter(
                x=valid_times[high_mask], y=valid_f0[high_mask],
                mode='markers',
                marker=dict(color=CHART_THEME["colors"]["danger"], size=4),
                name=f'High (>{high_thresh:.0f}Hz)'
            ))

    fig.update_layout(
        **get_premium_layout(
            title="Pitch Tracking by Register",
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5
            )
        ),
        xaxis_title='Time (seconds)',
        yaxis_title='Frequency (Hz)',
        height=280
    )

    return fig


def create_dynamics_chart(rms_db: np.ndarray, times: np.ndarray) -> go.Figure:
    """다이나믹스 차트"""
    fig = go.Figure()

    # 배경 영역 (호흡 임계값)
    breath_threshold = np.percentile(rms_db, 20)

    fig.add_trace(go.Scatter(
        x=times, y=rms_db,
        fill='tozeroy',
        mode='lines',
        line=dict(color=CHART_THEME["colors"]["gold"], width=1.5),
        fillcolor='rgba(201, 169, 98, 0.2)',
        name='Loudness'
    ))

    # 호흡 임계값 라인
    fig.add_hline(y=breath_threshold, line_dash="dash",
                  line_color=CHART_THEME["colors"]["warning"],
                  annotation_text="Breath Threshold",
                  annotation_font=dict(color=CHART_THEME["text"]["secondary"]))

    fig.update_layout(
        **get_premium_layout(title="Dynamics & Breath Pattern"),
        xaxis_title='Time (seconds)',
        yaxis_title='Loudness (dB)',
        height=220,
        showlegend=False
    )

    return fig


def create_pitch_distribution_chart(valid_f0: np.ndarray) -> go.Figure:
    """피치 분포 히스토그램"""
    fig = go.Figure()

    if len(valid_f0) > 0:
        fig.add_trace(go.Histogram(
            x=valid_f0,
            nbinsx=40,
            marker=dict(
                color=CHART_THEME["colors"]["purple"],
                line=dict(color=CHART_THEME["backgrounds"]["paper"], width=1)
            ),
            name='Pitch Distribution'
        ))

        # 평균 피치 라인
        mean_pitch = np.mean(valid_f0)
        fig.add_vline(x=mean_pitch, line_dash="dash",
                      line_color=CHART_THEME["colors"]["gold"],
                      annotation_text=f"Mean: {mean_pitch:.0f}Hz",
                      annotation_font=dict(color=CHART_THEME["text"]["secondary"]))

    fig.update_layout(
        **get_premium_layout(title="Pitch Distribution"),
        xaxis_title='Frequency (Hz)',
        yaxis_title='Count',
        height=250,
        bargap=0.05,
        showlegend=False
    )

    return fig


def create_pitch_accuracy_chart(pitch_errors: np.ndarray) -> go.Figure:
    """피치 정확도 분포 (센트 단위)"""
    fig = go.Figure()

    if len(pitch_errors) > 0:
        # -50 ~ +50 cents 범위로 클리핑
        errors_clipped = np.clip(pitch_errors, -50, 50)

        fig.add_trace(go.Histogram(
            x=errors_clipped,
            nbinsx=40,
            marker=dict(
                color=CHART_THEME["colors"]["purple_light"],
                line=dict(color=CHART_THEME["backgrounds"]["paper"], width=1)
            ),
            name='Pitch Error'
        ))

        # 완벽한 피치 라인
        fig.add_vline(x=0, line_dash="solid",
                      line_color=CHART_THEME["colors"]["success"],
                      annotation_text="Perfect Pitch",
                      annotation_font=dict(color=CHART_THEME["colors"]["success"]))

        # 평균 오차
        mean_error = np.mean(pitch_errors)
        fig.add_vline(x=mean_error, line_dash="dash",
                      line_color=CHART_THEME["colors"]["warning"],
                      annotation_text=f"Mean: {mean_error:.1f}¢",
                      annotation_font=dict(color=CHART_THEME["text"]["secondary"]))

    fig.update_layout(
        **get_premium_layout(title="Pitch Accuracy Distribution"),
        xaxis_title='Pitch Error (cents)',
        yaxis_title='Count',
        height=250,
        bargap=0.05,
        showlegend=False
    )

    return fig


def create_spectral_centroid_chart(centroid: np.ndarray, times: np.ndarray) -> go.Figure:
    """스펙트럴 센트로이드 (음색 밝기) 차트"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=times, y=centroid,
        mode='lines',
        line=dict(color=CHART_THEME["colors"]["gold"], width=1.5),
        fill='tozeroy',
        fillcolor='rgba(201, 169, 98, 0.1)',
        name='Spectral Centroid'
    ))

    # Warm/Bright 경계선 (MBTI 기준 1800Hz)
    boundary = 1800
    fig.add_hline(y=boundary, line_dash="dash",
                  line_color=CHART_THEME["text"]["muted"],
                  annotation_text="Warm/Bright (1800Hz)",
                  annotation_font=dict(color=CHART_THEME["text"]["secondary"]))

    fig.update_layout(
        **get_premium_layout(title="Tonal Brightness Over Time"),
        xaxis_title='Time (seconds)',
        yaxis_title='Spectral Centroid (Hz)',
        height=220,
        showlegend=False
    )

    return fig


def create_performance_summary_chart(features: dict, scorecard) -> go.Figure:
    """종합 성능 요약 바 차트"""
    # 음색 따뜻함은 별도 해석 필요 (40%+ = 따뜻함, 27-40% = 균형, <27% = 밝음)
    warmth_raw = features['warmth_score'] * 100
    if warmth_raw >= 40:
        warmth_label = "따뜻함"
    elif warmth_raw >= 27:
        warmth_label = "균형"
    else:
        warmth_label = "밝음"

    categories = ['Pitch\nAccuracy', 'High Note\nControl', 'Breath\nSupport', 'Dynamics', f'Tone\n({warmth_label})']

    # 점수 계산 (0-100 스케일)
    pitch_score = max(0, min(100, 100 - features['pitch_accuracy_cents'] * 2))
    high_note_score = features['high_note_stability'] * 100
    breath_score = min(100, features['breath_phrase_length'] * 15)
    dynamics_score = min(100, features['dynamic_range_db'] * 4)
    warmth_score = warmth_raw

    values = [pitch_score, high_note_score, breath_score, dynamics_score, warmth_score]
    colors = [
        CHART_THEME["colors"]["info"],
        CHART_THEME["colors"]["purple"],
        CHART_THEME["colors"]["success"],
        CHART_THEME["colors"]["warning"],
        CHART_THEME["colors"]["pink"]
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{v:.0f}' for v in values],
        textposition='outside',
        textfont=dict(color=CHART_THEME["text"]["primary"], size=13)
    ))

    # 기준선
    fig.add_hline(y=70, line_dash="dash", line_color=CHART_THEME["colors"]["success"],
                  annotation_text="Good (70)",
                  annotation_font=dict(color=CHART_THEME["text"]["secondary"]))
    fig.add_hline(y=40, line_dash="dot", line_color=CHART_THEME["colors"]["pink"],
                  annotation_text="Warm Tone (40+)",
                  annotation_font=dict(color=CHART_THEME["text"]["secondary"]))

    fig.update_layout(
        **get_premium_layout(
            title="Vocal Performance Summary",
            yaxis=dict(range=[0, 115], title='Score')
        ),
        height=320,
        bargap=0.3
    )

    return fig


def hz_to_note_name(hz: float) -> str:
    """주파수를 음이름으로 변환"""
    if hz <= 0:
        return "N/A"
    midi = librosa.hz_to_midi(hz)
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    note_idx = int(round(midi)) % 12
    octave = int(round(midi)) // 12 - 1
    return f"{note_names[note_idx]}{octave}"


def create_comparison_bar_chart(features_a: dict, features_b: dict, title_a: str, title_b: str) -> go.Figure:
    """두 곡의 특징 비교 바 차트"""
    categories = ['음역폭\n(반음)', '다이나믹\n(dB)', '고음 안정성\n(%)', '음색 밝기\n(점수)', '음정 정확도\n(점수)']

    # 정규화된 값으로 변환 (0-100 스케일)
    values_a = [
        min(100, features_a['pitch_range_semitones'] * 4),  # 25반음 = 100
        min(100, features_a['dynamic_range_db'] * 4),  # 25dB = 100
        features_a['high_note_stability'] * 100,
        (1 - features_a['warmth_score']) * 100,  # 밝기 (warmth 반전)
        max(0, 100 - features_a['pitch_accuracy_cents'] * 2)  # 정확도
    ]

    values_b = [
        min(100, features_b['pitch_range_semitones'] * 4),
        min(100, features_b['dynamic_range_db'] * 4),
        features_b['high_note_stability'] * 100,
        (1 - features_b['warmth_score']) * 100,
        max(0, 100 - features_b['pitch_accuracy_cents'] * 2)
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=title_a,
        x=categories,
        y=values_a,
        marker=dict(color=CHART_THEME["colors"]["gold"], line=dict(width=0)),
        text=[f'{v:.0f}' for v in values_a],
        textposition='outside',
        textfont=dict(color=CHART_THEME["text"]["primary"], size=12)
    ))

    fig.add_trace(go.Bar(
        name=title_b,
        x=categories,
        y=values_b,
        marker=dict(color=CHART_THEME["colors"]["purple"], line=dict(width=0)),
        text=[f'{v:.0f}' for v in values_b],
        textposition='outside',
        textfont=dict(color=CHART_THEME["text"]["primary"], size=12)
    ))

    fig.update_layout(
        **get_premium_layout(
            title="Song A vs Song B 비교",
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5
            ),
            yaxis=dict(range=[0, 115], title='Score')
        ),
        barmode='group',
        height=380,
        bargap=0.2
    )

    return fig


def create_evidence_chart(evidence: dict, title: str) -> go.Figure:
    """근거 데이터를 시각적 차트로 변환"""
    if not evidence:
        return None

    # 키-값 정리
    labels = []
    values = []
    colors = []

    for key, value in evidence.items():
        # 키 이름 정리
        display_key = key.replace('_', ' ').replace('slow', 'Song A').replace('fast', 'Song B')
        labels.append(display_key.title())

        # 값을 0-100 스케일로 변환
        if isinstance(value, (int, float)):
            if value <= 1:
                values.append(value * 100)
            else:
                values.append(min(100, value))
        else:
            values.append(50)  # 기본값

        # 색상 (값에 따라)
        if values[-1] >= 70:
            colors.append(CHART_THEME["colors"]["success"])  # 좋음
        elif values[-1] >= 40:
            colors.append(CHART_THEME["colors"]["warning"])  # 보통
        else:
            colors.append(CHART_THEME["colors"]["danger"])  # 개선필요

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{v:.0f}' for v in values],
        textposition='outside',
        textfont=dict(color=CHART_THEME["text"]["primary"], size=12)
    ))

    fig.update_layout(
        **get_premium_layout(
            title=title,
            yaxis=dict(range=[0, 115], title='Score')
        ),
        height=280,
        bargap=0.3
    )

    return fig


def render_technical_analysis(features: dict, scorecard=None, key_prefix: str = "main"):
    """기술적 분석 탭 렌더링 - 심층 보컬 분석 리포트"""
    ts = features.get('timeseries', {})

    if not ts:
        st.warning("시계열 데이터가 없습니다. 분석을 다시 실행해주세요.")
        return

    # =========================================
    # 📊 보컬 기술 분석 결과 헤더
    # =========================================
    st.markdown("## 📊 보컬 기술 분석 결과")

    # =========================================
    # 🎤 1. 음역대 (Vocal Range)
    # =========================================
    st.subheader("🎤 음역대 (Vocal Range)")

    min_hz = features['pitch_min_hz']
    max_hz = features['pitch_max_hz']
    avg_hz = features['avg_pitch_hz']
    range_semitones = features['pitch_range_semitones']
    octaves = range_semitones / 12

    # 음역대 해석
    if avg_hz < 165:  # A2 이하
        avg_interpret = "저음역 (베이스~바리톤)"
    elif avg_hz < 262:  # C4 이하
        avg_interpret = "중저음역 (바리톤~테너)"
    elif avg_hz < 392:  # G4 이하
        avg_interpret = "중고음역 (테너~알토)"
    else:
        avg_interpret = "고음역 (소프라노)"

    if octaves < 1.5:
        range_interpret = "좁은 음역 (특정 곡에 특화)"
    elif octaves < 2.0:
        range_interpret = "일반적인 대중음악 가창 범위"
    elif octaves < 2.5:
        range_interpret = "넓은 음역 (다양한 곡 소화 가능)"
    else:
        range_interpret = "매우 넓은 음역 (전문 가수급)"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        | 항목 | 값 | 해석 |
        |------|-----|------|
        | 최저음 | {} ({:.0f}Hz) | 저음역 |
        | 최고음 | {} ({:.0f}Hz) | 고음역 |
        | 평균음 | {} ({:.0f}Hz) | {} |
        | 음역폭 | {:.1f} 옥타브 | {} |
        """.format(
            hz_to_note_name(min_hz), min_hz,
            hz_to_note_name(max_hz), max_hz,
            hz_to_note_name(avg_hz), avg_hz, avg_interpret,
            octaves, range_interpret
        ))

    with col2:
        # 차트: 피치 분포
        pitch_dist_fig = create_pitch_distribution_chart(ts['valid_f0'])
        st.plotly_chart(pitch_dist_fig, use_container_width=True, key=f"{key_prefix}_pitch_dist_range")

    st.info(f"**해석**: 음역대는 {octaves:.1f}옥타브로 {range_interpret}. 평균음 {hz_to_note_name(avg_hz)}은 {avg_interpret}에 해당합니다.")

    st.markdown("---")

    # =========================================
    # 🔊 2. 다이나믹스 (강약 표현)
    # =========================================
    st.subheader("🔊 다이나믹스 (강약 표현)")

    dynamic_range = features['dynamic_range_db']
    rms_mean = features['rms_db_mean']
    rms_max = features['rms_db_max']
    climax_intensity = features['climax_intensity']

    # 다이나믹스 해석
    if dynamic_range < 10:
        dyn_interpret = "좁음 (단조로운 표현)"
        dyn_tip = "더 극적인 강약 대비를 연습해보세요"
    elif dynamic_range < 15:
        dyn_interpret = "보통 (적절한 표현)"
        dyn_tip = "좀 더 다이나믹한 표현을 추가하면 찬양이 풍성해집니다"
    elif dynamic_range < 20:
        dyn_interpret = "넓음 (풍부한 표현)"
        dyn_tip = "다이나믹 표현이 잘 되어 있습니다"
    else:
        dyn_interpret = "매우 넓음 (전문적 표현력)"
        dyn_tip = "훌륭한 다이나믹 컨트롤입니다"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 항목 | 값 | 해석 |
        |------|-----|------|
        | 다이나믹 레인지 | {dynamic_range:.1f}dB | {dyn_interpret} |
        | 평균 음량 | {rms_mean:.1f}dB | - |
        | 최대 음량 | {rms_max:.1f}dB | - |
        | 클라이맥스 강도 | {climax_intensity:.2f}x | {"강한 절정" if climax_intensity > 1.5 else "적절한 절정"} |
        """)

        with st.expander("📖 다이나믹스 이론"):
            st.markdown("""
            **다이나믹 레인지 기준:**
            - 10dB 이하: 단조로운 표현
            - 10-15dB: 보통 수준
            - 15-20dB: 풍부한 표현
            - 20dB 이상: 전문가 수준

            **개선 팁**: pp(매우 여리게) ~ ff(매우 강하게) 폭을 넓히면 극적인 찬양이 가능합니다.
            """)

    with col2:
        # 파형 차트
        waveform_fig = create_waveform_chart(ts['waveform'], features['sample_rate'])
        st.plotly_chart(waveform_fig, use_container_width=True, key=f"{key_prefix}_waveform_dynamics")

    # 다이나믹스 차트
    dynamics_fig = create_dynamics_chart(ts['rms_db'], ts['rms_times'])
    st.plotly_chart(dynamics_fig, use_container_width=True, key=f"{key_prefix}_dynamics_main")

    st.info(f"**해석**: {dyn_interpret}. {dyn_tip}")

    st.markdown("---")

    # =========================================
    # 🎨 3. 음색 (Timbre)
    # =========================================
    st.subheader("🎨 음색 (Timbre)")

    avg_centroid = features['spectral_centroid_hz']
    warmth_pct = features['warmth_score'] * 100

    if avg_centroid < 1800:
        tone_type = "따뜻하고 부드러운"
        tone_suit = "발라드, 찬양에 적합"
        tone_tip = "필요시 고음역에서 좀 더 밝은 발성을 섞으면 환하게 퍼지는 느낌을 줄 수 있어요"
    elif avg_centroid < 2200:
        tone_type = "균형 잡힌"
        tone_suit = "다양한 장르에 적합"
        tone_tip = "균형 잡힌 음색으로 다양한 곡을 소화할 수 있습니다"
    else:
        tone_type = "밝고 선명한"
        tone_suit = "업템포, CCM에 적합"
        tone_tip = "조용한 곡에서는 의도적으로 부드러운 발성을 사용해보세요"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 항목 | 값 | 해석 |
        |------|-----|------|
        | 음색 밝기 | {avg_centroid:.0f}Hz | {tone_type} 음색 |
        | 음색 따뜻함 | {warmth_pct:.0f}% | {tone_suit} |
        """)
        st.caption("💡 음색 밝기: 낮을수록 따뜻하고, 높을수록 밝은 음색입니다.")

    with col2:
        # 음색 밝기 차트
        centroid_fig = create_spectral_centroid_chart(ts['centroid'], ts['centroid_times'])
        st.plotly_chart(centroid_fig, use_container_width=True, key=f"{key_prefix}_centroid_timbre")

    st.info(f"**해석**: {tone_type} 음색으로 {tone_suit}입니다. {tone_tip}")

    st.markdown("---")

    # =========================================
    # 📈 4. 안정성 (Pitch Stability)
    # =========================================
    st.subheader("📈 안정성 (Pitch Stability)")

    pitch_std = features['pitch_std']
    pitch_stability = features.get('pitch_stability', 0.5)
    vibrato_ratio = features.get('vibrato_ratio', 0.3)

    # 안정성 해석
    stability_pct = pitch_stability * 100
    vibrato_pct = vibrato_ratio * 100

    if stability_pct >= 70:
        stability_interpret = "안정적 (좋음)"
    elif stability_pct >= 50:
        stability_interpret = "보통"
    else:
        stability_interpret = "변동이 큰 편"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 항목 | 값 | 해석 |
        |------|-----|------|
        | 피치 변동성 | {pitch_std:.1f}Hz | {"낮음 (안정적)" if pitch_std < 30 else "변동 있음"} |
        | 피치 안정성 | {stability_pct:.0f}% | {stability_interpret} |
        | 비브라토 비율 | {vibrato_pct:.0f}% | {"활발한 감정 표현" if vibrato_pct > 30 else "절제된 표현"} |
        """)

        with st.expander("📖 안정성 해석"):
            st.markdown("""
            피치 변동이 큰 경우 두 가지 가능성이 있어요:

            1. **표현력** - 의도적인 비브라토, 꾸밈음, 감정 표현
            2. **음정 불안정** - 비의도적인 피치 흔들림

            그래프를 보고 롱톤(긴 음)에서 피치가 흔들리는지 확인해보세요.
            """)

    with col2:
        # 피치 트래킹 차트
        pitch_tracking_fig = create_pitch_tracking_chart(
            ts['f0'], ts['f0_times'],
            features['high_threshold_hz'],
            features['low_threshold_hz']
        )
        st.plotly_chart(pitch_tracking_fig, use_container_width=True, key=f"{key_prefix}_pitch_tracking_stability")

    st.markdown("---")

    # =========================================
    # 🎵 5. 고음 처리 (High Note Technique)
    # =========================================
    st.subheader("🎵 고음 처리 (High Note Technique)")

    high_note_ratio = features.get('high_note_ratio', 0.15)
    high_note_stability = features.get('high_note_stability', 0.8)

    high_ratio_pct = high_note_ratio * 100
    high_stability_pct = high_note_stability * 100

    # 고음 안정성 해석
    if high_stability_pct >= 85:
        high_stability_interpret = "✅ 안정적"
    elif high_stability_pct >= 70:
        high_stability_interpret = "양호"
    else:
        high_stability_interpret = "⚠️ 흔들림 있음"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 항목 | 분석 결과 | 보컬 이론적 해석 |
        |------|----------|-----------------|
        | 최고음 | {hz_to_note_name(max_hz)} ({max_hz:.0f}Hz) | {"남성 테너 기준 적절" if max_hz < 500 else "여성/테너 고음역"} |
        | 고음역 비율 | {high_ratio_pct:.1f}% | {"고음을 적절히 활용" if high_ratio_pct > 10 else "고음 사용 적음"} |
        | 고음 안정성 | {high_stability_pct:.0f}% | {high_stability_interpret} |
        """)

        with st.expander("📖 보컬 이론 해석"):
            st.markdown("""
            **고음 안정성**이 낮은 경우:
            - **두성(Head Voice)과 흉성(Chest Voice)의 전환점(Passaggio)**에서 발생할 가능성이 높습니다
            - **믹스보이스(Mixed Voice)** 훈련으로 개선 가능

            **💡 개선 팁**: 립트릴(Lip Trill)이나 험밍으로 고음 구간을 연습하면
            성대 긴장 없이 고음을 안정적으로 유지할 수 있어요.
            """)

    with col2:
        # 성능 요약 차트
        performance_fig = create_performance_summary_chart(features, scorecard)
        st.plotly_chart(performance_fig, use_container_width=True, key=f"{key_prefix}_performance_highnote")

    st.markdown("---")

    # =========================================
    # 🌬️ 6. 호흡 분석 (Breath & Appoggio)
    # =========================================
    st.subheader("🌬️ 호흡 분석 (Breath & Appoggio)")

    breath_phrase = features.get('breath_phrase_length', 3.0)
    voiced_ratio = features.get('voiced_ratio', 0.7)

    # 호흡 해석
    if breath_phrase < 3.0:
        breath_interpret = "⚠️ 짧은 편"
        breath_tip = "복식호흡을 통한 횡격막 컨트롤이 더 필요해요"
    elif breath_phrase < 5.0:
        breath_interpret = "보통"
        breath_tip = "호흡 지지가 어느 정도 되고 있습니다"
    else:
        breath_interpret = "✅ 우수"
        breath_tip = "호흡 컨트롤이 잘 되어 있습니다"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 항목 | 분석 결과 | 해석 |
        |------|----------|------|
        | 평균 프레이즈 | {breath_phrase:.1f}초 | {breath_interpret} |
        | 발성 비율 | {voiced_ratio*100:.0f}% | {"안정적 발성" if voiced_ratio > 0.6 else "끊김 있음"} |
        """)

        with st.expander("📖 보컬 이론 해석"):
            st.markdown(f"""
            **이탈리아 벨칸토 이론의 Appoggio(호흡 지지)** 관점에서:

            - 프레이즈 {breath_phrase:.1f}초는 {breath_interpret}입니다
            - {breath_tip}

            **💡 개선 팁**: "Sustained Hissing Exercise" - 's' 소리를 일정하게 30초 이상 유지하는 연습을 통해
            횡격막 조절력을 키우면 프레이즈 길이가 늘어납니다.
            """)

    with col2:
        # 다이나믹스 차트 (호흡 패턴 확인용)
        dynamics_fig2 = create_dynamics_chart(ts['rms_db'], ts['rms_times'])
        st.plotly_chart(dynamics_fig2, use_container_width=True, key=f"{key_prefix}_dynamics_breath")

    st.markdown("---")

    # =========================================
    # 🎯 7. 음정 분석 (Intonation)
    # =========================================
    st.subheader("🎯 음정 분석 (Intonation)")

    accuracy_cents = features['pitch_accuracy_cents']
    flat_pct = features['flat_tendency'] * 100
    sharp_pct = features['sharp_tendency'] * 100
    vibrato_pct = features.get('vibrato_ratio', 0.3) * 100

    # 음정 등급
    if accuracy_cents < 10:
        accuracy_grade = "A+ (프로 수준)"
        accuracy_desc = "거의 인지 불가"
    elif accuracy_cents < 15:
        accuracy_grade = "A (매우 정확)"
        accuracy_desc = "미세하게 인지"
    elif accuracy_cents < 25:
        accuracy_grade = "B (양호)"
        accuracy_desc = "미세하게 인지 가능"
    elif accuracy_cents < 50:
        accuracy_grade = "C (보통)"
        accuracy_desc = "청중이 인지 가능"
    else:
        accuracy_grade = "D (개선 필요)"
        accuracy_desc = "명확한 음이탈"

    # 경향 분석
    if flat_pct > sharp_pct + 10:
        tendency = f"⚠️ 플랫 경향 ({flat_pct:.0f}%)"
        tendency_reason = "호흡 지지 약화 또는 후두 위치가 낮게 유지되어 발생"
    elif sharp_pct > flat_pct + 10:
        tendency = f"샤프 경향 ({sharp_pct:.0f}%)"
        tendency_reason = "긴장 또는 호흡 압력이 높아 발생"
    else:
        tendency = "균형잡힌 음정"
        tendency_reason = "안정적인 음정 컨트롤"

    # P0: 백분위 뱃지 계산
    pitch_percentile, pitch_delta_type = get_percentile_badge("pitch_accuracy_cents", accuracy_cents)
    high_note_percentile, _ = get_percentile_badge("high_note_stability", high_stability_pct)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 항목 | 결과 | 해석 |
        |------|------|------|
        | 평균 오차 | {accuracy_cents:.1f} cents | {accuracy_grade} |
        | 샤프 경향 | {sharp_pct:.0f}% | - |
        | 플랫 경향 | {flat_pct:.0f}% | {tendency} |
        | 비브라토 | {vibrato_pct:.0f}% | {"✅ 활발한 감정 표현" if vibrato_pct > 30 else "절제된 표현"} |
        """)

        # P0: 백분위 표시
        if pitch_percentile:
            badge_color = "green" if "상위" in pitch_percentile else ("orange" if "평균" in pitch_percentile else "red")
            st.markdown(f"🏅 **음정 정확도**: `{pitch_percentile}`")

        with st.expander("📖 음정 오차 기준 (Professional Standard)"):
            st.markdown("""
            | 범위 | 등급 | 설명 |
            |------|------|------|
            | 0-10 cents | 프로 수준 | 거의 인지 불가 |
            | 10-25 cents | 양호 | 미세하게 인지 |
            | 25-50 cents | 보통 | 청중이 인지 가능 |
            | 50+ cents | 개선 필요 | 명확한 음이탈 |

            **Bel Canto 전통**에서 권장하는 자연스러운 비브라토는 5-7Hz, 30-50 cents 폭입니다.
            """)

    with col2:
        # 피치 정확도 히스토그램
        pitch_accuracy_fig = create_pitch_accuracy_chart(ts['pitch_errors'])
        st.plotly_chart(pitch_accuracy_fig, use_container_width=True, key=f"{key_prefix}_pitch_accuracy_intonation")

    st.info(f"**음정 분석**: 평균 오차 {accuracy_cents:.1f}cents ({accuracy_grade}) | {tendency}\n\n*{tendency_reason}*")

    if flat_pct > sharp_pct + 10:
        st.warning("💡 **플랫 경향 교정 팁**: '높게 생각하고 노래하기' - 타겟 음보다 약간 위를 조준하는 의식적 연습. 피아노와 함께 스케일 연습 시 음정을 녹음해서 피드백 받기.")

    st.markdown("---")

    # =========================================
    # 📊 8. 종합 점수 & 피드백
    # =========================================
    st.subheader("📊 종합 점수 & 피드백")

    # 점수 계산 (높을수록 좋은 항목만)
    pitch_score = max(0, min(100, 100 - accuracy_cents * 2))
    high_note_score = high_stability_pct
    breath_score = min(100, breath_phrase * 15)
    dynamics_score = min(100, dynamic_range * 5)

    scores = {
        "음정 정확도": pitch_score,
        "고음 컨트롤": high_note_score,
        "호흡 지지": breath_score,
        "다이나믹": dynamics_score
    }

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**영역별 점수**")
        for label, score in scores.items():
            if score >= 80:
                emoji = "🟢"
            elif score >= 60:
                emoji = "🟡"
            else:
                emoji = "🔴"
            st.markdown(f"{emoji} **{label}**: {score:.0f}/100")

        # 음색 특성 (점수가 아닌 스펙트럼으로 표시)
        st.markdown("---")
        st.markdown("**🎨 음색 특성** *(높고 낮음이 아닌 특성)*")
        if warmth_pct >= 50:
            tone_char = "🔥 따뜻한 음색"
            tone_desc = "발라드, 찬양 인도에 적합"
        elif warmth_pct >= 30:
            tone_char = "⚖️ 균형 잡힌 음색"
            tone_desc = "다양한 장르에 적합"
        else:
            tone_char = "✨ 밝은 음색"
            tone_desc = "업템포, CCM에 적합"

        # 스펙트럼 바 시각화
        st.markdown(f"**{tone_char}** - {tone_desc}")
        st.markdown(f"```\n따뜻함 {'█' * int(warmth_pct / 10)}{'░' * (10 - int(warmth_pct / 10))} 밝음\n       {warmth_pct:.0f}%                {100-warmth_pct:.0f}%\n```")

    with col2:
        # 강점 & 개선점
        st.markdown("**✅ 강점 (Keep Doing)**")
        strengths = []
        if octaves >= 2.0:
            strengths.append(f"넓은 음역대 ({octaves:.1f}옥타브) - 다양한 곡 소화 가능")
        # 음색은 특성이므로 각각의 장점을 설명
        if warmth_pct >= 50:
            strengths.append("따뜻한 음색 - 발라드, 찬양 인도에 적합")
        elif warmth_pct < 30:
            strengths.append("밝은 음색 - 업템포, 밝은 찬양에 적합")
        else:
            strengths.append("균형 잡힌 음색 - 다양한 장르에 적합")
        if vibrato_pct > 30:
            strengths.append("자연스러운 비브라토 - 감정 전달력 우수")
        if pitch_score >= 70:
            strengths.append("안정적인 음정 - 정확한 피치 컨트롤")
        if breath_score >= 70:
            strengths.append("좋은 호흡 지지 - 프레이즈 유지력 우수")

        for s in strengths[:4]:
            st.markdown(f"• {s}")

    st.markdown("---")

    st.markdown("**🔧 개선점 (Work On)**")

    improvements = []
    if flat_pct > sharp_pct + 10:
        improvements.append(("플랫 경향 교정", "피아노/튜너 앱과 함께 스케일 연습, 음을 살짝 높게 조준"))
    if high_stability_pct < 80:
        improvements.append(("고음 안정성", "믹스보이스 훈련, 세미 오클루전(빨대 발성) 연습"))
    if breath_phrase < 4.0:
        improvements.append(("프레이즈 길이", "복식호흡 강화, 30초 이상 Sustained Tone 연습"))
    if dynamic_range < 15:
        improvements.append(("다이나믹 폭 확대", "pp~ff 극적 대비 연습, 감정 몰입도 향상"))
    if pitch_score < 60:
        improvements.append(("음정 정확도", "튜너 앱으로 실시간 피드백 받으며 스케일 연습"))

    if improvements:
        st.markdown("""
        | 순위 | 개선 영역 | 구체적 연습법 |
        |------|----------|-------------|""")
        for i, (area, method) in enumerate(improvements[:5], 1):
            st.markdown(f"| {i} | {area} | {method} |")
    else:
        st.success("전반적으로 우수한 보컬 능력을 보여주고 있습니다! 현재 수준을 유지하면서 다양한 곡에 도전해보세요.")


# =============================================
# 사이드바 - 모드 선택
# =============================================

st.sidebar.title("🎤 Worship Vocal AI")

analysis_mode = st.sidebar.radio(
    "분석 모드",
    ["🎵 단일 분석", "🎭 이중 분석 (Dual-Core)"],
    index=0,  # 기본값: 단일 분석
    help="이중 분석: 느린 곡 + 빠른 곡 2개를 비교 분석하여 더 입체적인 보컬 페르소나를 도출합니다."
)

st.sidebar.markdown("---")

if analysis_mode == "🎵 단일 분석":
    st.sidebar.info("💡 **Tip**: 분석 완료 후 '이중 분석' 모드로 전환하여 다른 스타일의 곡과 비교해보세요!")
else:
    st.sidebar.markdown("""
**이중 분석의 장점:**
- 두 스타일에서 공통되는 강점/약점 발견
- 스타일별 반전 매력 발견
- 더 정확한 보컬 페르소나 정의
""")

# =============================================
# P1: 분석 히스토리 (세션 내)
# =============================================
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []

if st.session_state.analysis_history:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 분석 기록")
    for i, record in enumerate(reversed(st.session_state.analysis_history[-5:])):
        timestamp = record.get('timestamp', '')
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%H:%M")
        mbti_type = record.get('mbti_type', '?')
        song_title = record.get('song_title', '알 수 없음')[:15]
        st.sidebar.caption(f"{i+1}. {song_title} ({mbti_type}) - {timestamp}")

# =============================================
# P2: 팀원 프로필 저장 기능
# =============================================
if 'team_profiles' not in st.session_state:
    st.session_state.team_profiles = {}

st.sidebar.markdown("---")
with st.sidebar.expander("👥 팀원 프로필 관리", expanded=False):
    # 새 팀원 저장
    if 'analysis_result' in st.session_state and st.session_state.analysis_result:
        new_member_name = st.text_input("팀원 이름", placeholder="예: 김민지", key="new_member_name")
        if st.button("현재 분석 결과 저장", key="save_profile"):
            if new_member_name:
                result = st.session_state.analysis_result
                st.session_state.team_profiles[new_member_name] = {
                    'mbti_type': result['primary_type'],
                    'vocal_type_name': result['vocal_type_info'].name_kr,
                    'scorecard': result['scorecard'],
                    'strengths': result['vocal_type_info'].strengths,
                    'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                st.success(f"✅ {new_member_name} 프로필 저장됨!")
                st.rerun()
            else:
                st.warning("팀원 이름을 입력해주세요.")

    # 저장된 팀원 목록
    if st.session_state.team_profiles:
        st.markdown("##### 저장된 팀원")
        for name, profile in st.session_state.team_profiles.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{name}** ({profile['mbti_type']})")
                st.caption(f"{profile['vocal_type_name']} - {profile['saved_at']}")
            with col2:
                if st.button("🗑️", key=f"del_{name}", help="프로필 삭제"):
                    del st.session_state.team_profiles[name]
                    st.rerun()
    else:
        st.info("저장된 팀원이 없습니다. 분석 후 '현재 분석 결과 저장'을 눌러주세요.")

    # P2: 팀원 비교 차트 (2명 이상일 때)
    if len(st.session_state.team_profiles) >= 2:
        st.markdown("---")
        st.markdown("##### 📊 팀원 비교")
        selected_members = st.multiselect(
            "비교할 팀원 선택",
            options=list(st.session_state.team_profiles.keys()),
            default=list(st.session_state.team_profiles.keys())[:3],
            key="compare_members"
        )

        if len(selected_members) >= 2:
            # 레이더 차트용 데이터 준비
            categories = ['친밀감', '다이나믹', '음색', '인도력', '지속력', '표현력']

            import plotly.graph_objects as go
            fig = go.Figure()

            colors = ['#C9A962', '#7C5CBF', '#4ADE80', '#F87171', '#60A5FA']
            for idx, name in enumerate(selected_members[:5]):  # 최대 5명
                profile = st.session_state.team_profiles[name]
                scorecard = profile.get('scorecard', {})
                values = [
                    scorecard.get('intimacy', 0.5),
                    scorecard.get('dynamics', 0.5),
                    scorecard.get('tone', 0.5),
                    scorecard.get('leading', 0.5),
                    scorecard.get('sustain', 0.5),
                    scorecard.get('expression', 0.5),
                ]
                values_pct = [v * 100 for v in values]
                values_pct.append(values_pct[0])  # 닫기

                fig.add_trace(go.Scatterpolar(
                    r=values_pct,
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=f"{name} ({profile['mbti_type']})",
                    line_color=colors[idx % len(colors)],
                    opacity=0.7
                ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100]),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300,
                margin=dict(l=30, r=30, t=30, b=50)
            )
            st.plotly_chart(fig, use_container_width=True)

            # 팀 요약
            st.caption(f"🎯 총 {len(st.session_state.team_profiles)}명의 팀원 프로필 저장됨")

# =============================================
# 메인 헤더
# =============================================

st.title("🎤 Worship Vocal AI Coach")

# =============================================
# P0: 첫 사용자 온보딩 가이드
# =============================================
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True

if st.session_state.first_visit:
    with st.expander("🎉 처음 오셨나요? 시작 가이드", expanded=True):
        st.markdown("""
### 3단계로 보컬 분석 완료!

**1️⃣ 찬양 업로드** - YouTube 링크 또는 녹음 파일
**2️⃣ 녹음 환경 선택** - 솔로? 반주와 함께?
**3️⃣ AI 분석 시작** - 1-5분 후 결과 확인!

> 💡 **팁**: '이중 분석'은 느린 곡 + 빠른 곡 2개를 비교해서 더 정확한 보컬 스타일을 알려줘요!

---

**결과에서 확인할 수 있는 것:**
- 🎭 **보컬 MBTI** - 8가지 유형 중 당신의 스타일
- 📊 **기술 분석** - 음정, 음색, 다이나믹 등 상세 분석
- 🎵 **추천 찬양** - 당신에게 어울리는 찬양 리스트
- 📥 **PDF/이미지** - 분석 결과 저장 및 공유
        """)
        if st.button("알겠어요, 시작할게요!", type="primary"):
            st.session_state.first_visit = False
            st.rerun()

if analysis_mode == "🎭 이중 분석 (Dual-Core)":
    st.markdown("""
    **이중 분석 모드**: 서로 다른 스타일의 2곡을 비교 분석하여 **입체적인 보컬 페르소나**를 도출합니다.
    """)
else:
    st.markdown("당신의 찬양을 분석하고, **보컬 MBTI**와 **맞춤 코칭**을 제공합니다.")


# =============================================
# 이중 분석 모드
# =============================================

if analysis_mode == "🎭 이중 분석 (Dual-Core)":

    # 세션 상태 초기화
    if 'mission_a_path' not in st.session_state:
        st.session_state.mission_a_path = None
    if 'mission_b_path' not in st.session_state:
        st.session_state.mission_b_path = None
    if 'dual_result' not in st.session_state:
        st.session_state.dual_result = None

    # 녹음 환경 설정 (이중 분석용)
    st.subheader("🎤 녹음 환경")
    dual_recording_type = st.selectbox(
        "녹음 상황을 선택하세요",
        [
            "🎤 솔로 녹음 (나만 녹음됨)",
            "🎹 반주와 함께 (MR + 내 목소리)",
            "👥 찬양팀과 함께 (내가 메인 인도자)"
        ],
        key="dual_recording_type"
    )
    dual_need_separation = dual_recording_type != "🎤 솔로 녹음 (나만 녹음됨)"

    if dual_need_separation:
        st.info("🔧 AI가 자동으로 보컬을 분리하여 분석합니다.")

    st.markdown("---")

    # Song A 입력
    st.header("🎵 Song A: 첫 번째 곡")

    col_a1, col_a2 = st.columns([2, 1])

    with col_a1:
        input_method_a = st.radio(
            "입력 방식 (Mission A)",
            ["🔗 YouTube 링크", "📁 파일 업로드"],
            horizontal=True,
            key="input_a"
        )

    with col_a2:
        song_title_a = st.text_input("곡 제목 (Song A)", placeholder="예: 나 무력할수록", key="title_a")

    if input_method_a == "🔗 YouTube 링크":
        url_a = st.text_input("YouTube URL (Mission A)", placeholder="https://www.youtube.com/watch?v=...", key="url_a")

        st.caption("✂️ 분석할 구간 (MM:SS 형식)")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_a = st.text_input("⏱️ 시작", "0:00", key="start_a")
        with col2:
            end_a = st.text_input("⏱️ 종료", "", key="end_a", help="비워두면 끝까지")
        with col3:
            if start_a and end_a:
                try:
                    s = time_to_seconds(start_a) or 0
                    e = time_to_seconds(end_a)
                    if e and e > s:
                        d = e - s
                        st.metric("길이", f"{d//60}:{d%60:02d}")
                except:
                    pass

        if st.button("🎵 Mission A 추출", key="extract_a"):
            if url_a:
                with st.spinner("Mission A 오디오 추출 중..."):
                    try:
                        path, title = extract_youtube_audio(url_a, start_a, end_a, "mission_a")
                        st.session_state.mission_a_path = path
                        st.session_state.mission_a_title = title
                        st.success(f"✅ Mission A 추출 완료! ({title})")
                        st.audio(path)
                    except Exception as e:
                        st.error(f"추출 실패: {e}")
    else:
        uploaded_a = st.file_uploader("오디오 파일 (Mission A)", type=['mp3', 'wav', 'm4a'], key="file_a")
        if uploaded_a:
            temp_path = f"/tmp/mission_a_{uploaded_a.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_a.getbuffer())
            st.session_state.mission_a_path = temp_path
            st.audio(uploaded_a)

    st.markdown("---")

    # Song B 입력
    st.header("🎵 Song B: 두 번째 곡")

    col_b1, col_b2 = st.columns([2, 1])

    with col_b1:
        input_method_b = st.radio(
            "입력 방식 (Mission B)",
            ["🔗 YouTube 링크", "📁 파일 업로드"],
            horizontal=True,
            key="input_b"
        )

    with col_b2:
        song_title_b = st.text_input("곡 제목 (Mission B)", placeholder="예: 살아계신 주", key="title_b")

    if input_method_b == "🔗 YouTube 링크":
        url_b = st.text_input("YouTube URL (Mission B)", placeholder="https://www.youtube.com/watch?v=...", key="url_b")

        st.caption("✂️ 분석할 구간 (MM:SS 형식)")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_b = st.text_input("⏱️ 시작", "0:00", key="start_b")
        with col2:
            end_b = st.text_input("⏱️ 종료", "", key="end_b", help="비워두면 끝까지")
        with col3:
            if start_b and end_b:
                try:
                    s = time_to_seconds(start_b) or 0
                    e = time_to_seconds(end_b)
                    if e and e > s:
                        d = e - s
                        st.metric("길이", f"{d//60}:{d%60:02d}")
                except:
                    pass

        if st.button("🎵 Mission B 추출", key="extract_b"):
            if url_b:
                with st.spinner("Mission B 오디오 추출 중..."):
                    try:
                        path, title = extract_youtube_audio(url_b, start_b, end_b, "mission_b")
                        st.session_state.mission_b_path = path
                        st.session_state.mission_b_title = title
                        st.success(f"✅ Mission B 추출 완료! ({title})")
                        st.audio(path)
                    except Exception as e:
                        st.error(f"추출 실패: {e}")
    else:
        uploaded_b = st.file_uploader("오디오 파일 (Mission B)", type=['mp3', 'wav', 'm4a'], key="file_b")
        if uploaded_b:
            temp_path = f"/tmp/mission_b_{uploaded_b.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_b.getbuffer())
            st.session_state.mission_b_path = temp_path
            st.audio(uploaded_b)

    st.markdown("---")

    # 세션 상태 초기화 (분리 결과 저장용)
    if 'separated_vocals_a' not in st.session_state:
        st.session_state.separated_vocals_a = None
    if 'separated_vocals_b' not in st.session_state:
        st.session_state.separated_vocals_b = None
    if 'separated_instrumental_a' not in st.session_state:
        st.session_state.separated_instrumental_a = None
    if 'separated_instrumental_b' not in st.session_state:
        st.session_state.separated_instrumental_b = None

    # 이중 분석 실행 (2단계 분리)
    if st.session_state.mission_a_path and st.session_state.mission_b_path:

        # ========== STEP 1: 보컬 분리 ==========
        if dual_need_separation and not st.session_state.separated_vocals_a:
            st.subheader("📌 Step 1: 보컬 분리")

            if st.button("🎭 보컬 분리 시작", type="primary", key="step1_separate"):
                progress = st.progress(0)
                status = st.empty()

                try:
                    from vocal_separator import auto_separate, SeparationMode

                    audio_path_a = st.session_state.mission_a_path
                    audio_path_b = st.session_state.mission_b_path

                    # 파일 크기 확인
                    size_a = os.path.getsize(audio_path_a) / (1024 * 1024)
                    size_b = os.path.getsize(audio_path_b) / (1024 * 1024)
                    total_size = size_a + size_b
                    if total_size > 50:
                        est_time = int((total_size * 18 + 300) / 60)
                        st.warning(f"⏱️ 파일 크기가 큽니다 (총 {total_size:.0f}MB). 보컬 분리에 약 {est_time}분 소요될 수 있습니다.")

                    status.text(f"🎭 Song A 보컬 분리 중... ({size_a:.0f}MB)")
                    sep_result_a = auto_separate(audio_path_a, "/tmp/separated_a", mode=SeparationMode.VOCALS_ONLY)
                    progress.progress(40)

                    status.text(f"🎭 Song B 보컬 분리 중... ({size_b:.0f}MB)")
                    sep_result_b = auto_separate(audio_path_b, "/tmp/separated_b", mode=SeparationMode.VOCALS_ONLY)
                    progress.progress(80)

                    # 결과 저장
                    if sep_result_a.success and sep_result_a.lead_vocals_path:
                        st.session_state.separated_vocals_a = sep_result_a.lead_vocals_path
                        st.session_state.separated_instrumental_a = sep_result_a.instrumental_path
                    if sep_result_b.success and sep_result_b.lead_vocals_path:
                        st.session_state.separated_vocals_b = sep_result_b.lead_vocals_path
                        st.session_state.separated_instrumental_b = sep_result_b.instrumental_path

                    progress.progress(100)
                    status.text("✅ 보컬 분리 완료!")
                    st.rerun()

                except Exception as e:
                    st.error(f"분리 중 오류: {e}")

        # ========== 분리 완료 후: 미리듣기 & 다운로드 ==========
        if st.session_state.separated_vocals_a and st.session_state.separated_vocals_b:
            st.success("✅ 보컬 분리 완료! 아래에서 미리 듣거나 다운로드할 수 있습니다.")

            # 미리듣기 섹션
            st.subheader("🎧 분리된 보컬 미리듣기 & 다운로드")
            col_prev1, col_prev2 = st.columns(2)

            with col_prev1:
                st.markdown(f"**🎵 {song_title_a or 'Song A'} - 보컬**")
                if os.path.exists(st.session_state.separated_vocals_a):
                    st.audio(st.session_state.separated_vocals_a, format='audio/wav')
                    with open(st.session_state.separated_vocals_a, 'rb') as f:
                        st.download_button("⬇️ 보컬 다운로드", f, f"{song_title_a or 'SongA'}_vocals.wav", "audio/wav", key="dl_voc_a")
                if st.session_state.separated_instrumental_a and os.path.exists(st.session_state.separated_instrumental_a):
                    st.markdown("**🎸 MR (반주)**")
                    st.audio(st.session_state.separated_instrumental_a, format='audio/wav')
                    with open(st.session_state.separated_instrumental_a, 'rb') as f:
                        st.download_button("⬇️ MR 다운로드", f, f"{song_title_a or 'SongA'}_mr.wav", "audio/wav", key="dl_mr_a")

            with col_prev2:
                st.markdown(f"**🎵 {song_title_b or 'Song B'} - 보컬**")
                if os.path.exists(st.session_state.separated_vocals_b):
                    st.audio(st.session_state.separated_vocals_b, format='audio/wav')
                    with open(st.session_state.separated_vocals_b, 'rb') as f:
                        st.download_button("⬇️ 보컬 다운로드", f, f"{song_title_b or 'SongB'}_vocals.wav", "audio/wav", key="dl_voc_b")
                if st.session_state.separated_instrumental_b and os.path.exists(st.session_state.separated_instrumental_b):
                    st.markdown("**🎸 MR (반주)**")
                    st.audio(st.session_state.separated_instrumental_b, format='audio/wav')
                    with open(st.session_state.separated_instrumental_b, 'rb') as f:
                        st.download_button("⬇️ MR 다운로드", f, f"{song_title_b or 'SongB'}_mr.wav", "audio/wav", key="dl_mr_b")

            st.markdown("---")

            # ========== STEP 2: 피치 분석 ==========
            st.subheader("📌 Step 2: 보컬 분석")
            st.caption("분리된 보컬을 분석하여 기술 점수, 스타일, MBTI 등을 계산합니다.")

            if st.button("🔍 분석 계속하기", type="primary", key="step2_analyze"):
                progress = st.progress(0)
                status = st.empty()

                try:
                    audio_path_a = st.session_state.separated_vocals_a
                    audio_path_b = st.session_state.separated_vocals_b

                    # Song A 분석 (시계열 포함)
                    status.text("📊 Song A 분석 중...")
                    features_a = analyze_audio_features(audio_path_a, include_timeseries=True)
                    progress.progress(30)

                    # Song B 분석 (시계열 포함)
                    status.text("📊 Song B 분석 중...")
                    features_b = analyze_audio_features(audio_path_b, include_timeseries=True)
                    progress.progress(60)

                    # LLM 기반 분석 사용
                    status.text("🤖 AI(Claude) 분석 중...")

                    from llm_analyzer import analyze_with_llm

                    llm_result = analyze_with_llm(
                        features_a,
                        features_b,
                        song_title_a or "Song A",
                        song_title_b or "Song B"
                    )

                    progress.progress(85)

                    # 레이더 차트 및 DNA 계산 (개선된 점수 시스템)
                    avg_dynamic_score = (features_a['dynamic_score'] + features_b['dynamic_score']) / 2
                    avg_breath_score = (features_a['breath_support_score'] + features_b['breath_support_score']) / 2
                    avg_centroid = (features_a['spectral_centroid_hz'] + features_b['spectral_centroid_hz']) / 2
                    avg_stability = (features_a['high_note_stability'] + features_b['high_note_stability']) / 2
                    avg_clarity = (features_a['articulation_clarity'] + features_b['articulation_clarity']) / 2
                    avg_rhythm = (features_a['rhythm_offset_ms'] + features_b['rhythm_offset_ms']) / 2

                    radar_stats = {
                        "감성": avg_dynamic_score * 100,  # 개선: 최적 범위 반영
                        "음색": min(100, 100 - abs(avg_centroid - 1800) / 20),
                        "리듬": min(100, 100 - avg_rhythm),
                        "발성": avg_stability * 100,
                        "리딩": avg_clarity * 100
                    }

                    vocal_dna = {
                        "따뜻함": max(0, min(100, (3000 - avg_centroid) / 15)),
                        "파워": avg_dynamic_score * 100,  # 개선: 최적 범위 반영
                        "안정성": avg_stability * 100,
                        "표현력": avg_dynamic_score * 80 + avg_breath_score * 20,  # 다이나믹 + 호흡
                        "그루브": max(0, min(100, 100 - avg_rhythm)),
                        "친밀감": avg_breath_score * 100  # 개선: 호흡 지지 기반
                    }

                    # 결과 객체 생성 (LLM 결과 + 계산된 차트 데이터)
                    class LLMDualResult:
                        pass

                    result = LLMDualResult()
                    result.persona_name = llm_result.persona_name
                    result.persona_icon = llm_result.persona_icon
                    result.persona_description = llm_result.persona_description
                    result.signature_name = llm_result.signature_name
                    result.signature_description = llm_result.signature_description
                    result.signature_evidence = llm_result.signature_evidence
                    result.enemy_name = llm_result.enemy_name
                    result.enemy_description = llm_result.enemy_description
                    result.enemy_evidence = llm_result.enemy_evidence
                    result.solution = llm_result.solution
                    result.exercise = llm_result.exercise
                    result.vocal_mbti = llm_result.vocal_mbti
                    result.mbti_reason = llm_result.mbti_reason
                    result.overall_assessment = llm_result.overall_assessment
                    result.matching_songs = llm_result.matching_songs
                    result.challenge_songs = llm_result.challenge_songs
                    result.radar_stats = radar_stats
                    result.vocal_dna = vocal_dna

                    # 곡 정보 (표시용)
                    class SongInfo:
                        pass
                    result.slow_song = SongInfo()
                    result.slow_song.song_title = song_title_a or "Song A"
                    result.fast_song = SongInfo()
                    result.fast_song.song_title = song_title_b or "Song B"

                    progress.progress(90)

                    # 결과 저장
                    st.session_state.dual_result = {
                        'result': result,
                        'features_a': features_a,
                        'features_b': features_b
                    }

                    # 보컬 분리 결과 저장 (다운로드용) - 이미 세션에 저장됨
                    st.session_state.dual_separation_result = {
                        'song_a': {
                            'vocals_path': st.session_state.separated_vocals_a,
                            'instrumental_path': st.session_state.separated_instrumental_a,
                            'confidence': 0.9,
                            'title': song_title_a or "Song A"
                        },
                        'song_b': {
                            'vocals_path': st.session_state.separated_vocals_b,
                            'instrumental_path': st.session_state.separated_instrumental_b,
                            'confidence': 0.9,
                            'title': song_title_b or "Song B"
                        }
                    }

                    progress.progress(100)
                    status.text("✅ 이중 분석 완료!")

                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        # ========== 분리 필요 없는 경우: 바로 분석 ==========
        elif not dual_need_separation:
            st.subheader("📌 보컬 분석")
            st.caption("파일에서 직접 보컬을 분석합니다.")

            if st.button("🔍 분석 시작", type="primary", key="direct_analyze"):
                progress = st.progress(0)
                status = st.empty()

                try:
                    audio_path_a = st.session_state.mission_a_path
                    audio_path_b = st.session_state.mission_b_path

                    # Song A 분석 (시계열 포함)
                    status.text("📊 Song A 분석 중...")
                    features_a = analyze_audio_features(audio_path_a, include_timeseries=True)
                    progress.progress(30)

                    # Song B 분석 (시계열 포함)
                    status.text("📊 Song B 분석 중...")
                    features_b = analyze_audio_features(audio_path_b, include_timeseries=True)
                    progress.progress(60)

                    # LLM 기반 분석 사용
                    status.text("🤖 AI(Claude) 분석 중...")

                    from llm_analyzer import analyze_with_llm

                    llm_result = analyze_with_llm(
                        features_a,
                        features_b,
                        song_title_a or "Song A",
                        song_title_b or "Song B"
                    )

                    progress.progress(85)

                    # 레이더 차트 및 DNA 계산
                    avg_dynamic_score = (features_a['dynamic_score'] + features_b['dynamic_score']) / 2
                    avg_breath_score = (features_a['breath_support_score'] + features_b['breath_support_score']) / 2
                    avg_centroid = (features_a['spectral_centroid_hz'] + features_b['spectral_centroid_hz']) / 2
                    avg_stability = (features_a['high_note_stability'] + features_b['high_note_stability']) / 2
                    avg_clarity = (features_a['articulation_clarity'] + features_b['articulation_clarity']) / 2
                    avg_rhythm = (features_a['rhythm_offset_ms'] + features_b['rhythm_offset_ms']) / 2

                    radar_stats = {
                        "감성": avg_dynamic_score * 100,
                        "음색": min(100, 100 - abs(avg_centroid - 1800) / 20),
                        "리듬": min(100, 100 - avg_rhythm),
                        "발성": avg_stability * 100,
                        "리딩": avg_clarity * 100
                    }

                    vocal_dna = {
                        "따뜻함": max(0, min(100, (3000 - avg_centroid) / 15)),
                        "파워": avg_dynamic_score * 100,
                        "안정성": avg_stability * 100,
                        "표현력": avg_dynamic_score * 80 + avg_breath_score * 20,
                        "그루브": max(0, min(100, 100 - avg_rhythm)),
                        "친밀감": avg_breath_score * 100
                    }

                    class LLMDualResult:
                        pass

                    result = LLMDualResult()
                    result.persona_name = llm_result.persona_name
                    result.persona_icon = llm_result.persona_icon
                    result.persona_description = llm_result.persona_description
                    result.signature_name = llm_result.signature_name
                    result.signature_description = llm_result.signature_description
                    result.signature_evidence = llm_result.signature_evidence
                    result.enemy_name = llm_result.enemy_name
                    result.enemy_description = llm_result.enemy_description
                    result.enemy_evidence = llm_result.enemy_evidence
                    result.solution = llm_result.solution
                    result.exercise = llm_result.exercise
                    result.vocal_mbti = llm_result.vocal_mbti
                    result.mbti_reason = llm_result.mbti_reason
                    result.overall_assessment = llm_result.overall_assessment
                    result.matching_songs = llm_result.matching_songs
                    result.challenge_songs = llm_result.challenge_songs
                    result.radar_stats = radar_stats
                    result.vocal_dna = vocal_dna

                    class SongInfo:
                        pass
                    result.slow_song = SongInfo()
                    result.slow_song.song_title = song_title_a or "Song A"
                    result.fast_song = SongInfo()
                    result.fast_song.song_title = song_title_b or "Song B"

                    # 결과 저장
                    st.session_state.dual_result = {
                        'result': result,
                        'features_a': features_a,
                        'features_b': features_b
                    }
                    st.session_state.dual_separation_result = None

                    progress.progress(100)
                    status.text("✅ 분석 완료!")

                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # 결과 표시
    if st.session_state.dual_result:
        result = st.session_state.dual_result['result']
        features_a = st.session_state.dual_result['features_a']
        features_b = st.session_state.dual_result['features_b']

        st.markdown("---")
        st.header("🎭 이중 분석 결과")

        # 탭 인터페이스
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🎭 보컬 코칭", "📊 Song A 기술 분석", "📊 Song B 기술 분석", "🎵 추천 찬양", "📋 보컬 MBTI 유형", "📥 오디오 다운로드"])

        with tab1:
            # 페르소나 카드
            st.subheader(f"{result.persona_icon} THE PERSONA: {result.persona_name}")
            st.info(result.persona_description)

            # 2열 레이아웃 (SIGNATURE / HIDDEN ENEMY)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### ⭐ YOUR SIGNATURE")
                st.markdown(f"**{result.signature_name}**")
                st.write(result.signature_description)
                if result.signature_evidence:
                    # JSON 대신 테이블로 표시
                    st.markdown("**📊 근거:**")
                    for key, value in result.signature_evidence.items():
                        display_key = key.replace('_', ' ').replace('song a', 'Song A').replace('song b', 'Song B')
                        st.write(f"- {display_key}: **{value}**")

            with col2:
                st.markdown("### 🎯 HIDDEN ENEMY")
                st.markdown(f"**{result.enemy_name}**")
                st.write(result.enemy_description)
                if result.enemy_evidence:
                    st.markdown("**📊 근거:**")
                    for key, value in result.enemy_evidence.items():
                        display_key = key.replace('_', ' ').replace('song a', 'Song A').replace('song b', 'Song B')
                        if isinstance(value, float):
                            st.write(f"- {display_key}: **{value:.1f}**")
                        else:
                            st.write(f"- {display_key}: **{value}**")

            st.markdown("---")

            # VOCAL IDENTITY (상세화 - LLM 이유 포함)
            from vocal_mbti import VOCAL_TYPES
            st.markdown("### 🧬 VOCAL IDENTITY")

            id_col1, id_col2 = st.columns([1, 2])

            with id_col1:
                st.metric("MBTI 타입", result.vocal_mbti)

            with id_col2:
                if result.vocal_mbti in VOCAL_TYPES:
                    vtype = VOCAL_TYPES[result.vocal_mbti]
                    st.markdown(f"**{vtype.name_en}** ({vtype.name_kr})")
                    st.write(vtype.description)
                    st.markdown("**롤모델:** " + ", ".join(vtype.role_models))

                # LLM이 분석한 이유 표시
                if hasattr(result, 'mbti_reason') and result.mbti_reason:
                    st.info(f"**AI 분석:** {result.mbti_reason}")

            st.markdown("---")

            # 찬양 예배 스타일 (평가보다 스타일 안내)
            st.markdown("### ⛪ 찬양 예배 스타일")
            from worship_style import calculate_worship_style, WORSHIP_STYLE_AXES, StyleDimension

            # 두 곡의 평균 특성으로 스타일 계산
            avg_features = {
                'dynamic_score': (features_a.get('dynamic_score', 0.5) + features_b.get('dynamic_score', 0.5)) / 2,
                'warmth_score': (features_a.get('warmth_score', 0.5) + features_b.get('warmth_score', 0.5)) / 2,
                'high_note_stability': (features_a.get('high_note_stability', 0.5) + features_b.get('high_note_stability', 0.5)) / 2,
                'breath_support_score': (features_a.get('breath_support_score', 0.5) + features_b.get('breath_support_score', 0.5)) / 2,
                'energy_variance': (features_a.get('energy_variance', 0.1) + features_b.get('energy_variance', 0.1)) / 2,
                'vibrato_ratio': (features_a.get('vibrato_ratio', 0.3) + features_b.get('vibrato_ratio', 0.3)) / 2,
            }
            worship_style = calculate_worship_style(avg_features)

            # 스타일 이름과 설명
            st.success(f"{worship_style.icon} **{worship_style.style_name}** ({worship_style.style_name_en})")
            st.write(worship_style.description)

            # 스타일 차원 시각화
            style_col1, style_col2 = st.columns(2)

            with style_col1:
                st.markdown("**✨ 강점:**")
                for strength in worship_style.strengths:
                    st.write(f"• {strength}")

            with style_col2:
                st.markdown("**⛪ 어울리는 예배:**")
                for context in worship_style.best_fit_contexts:
                    st.write(f"• {context}")

            # 스타일 축 표시 (expander)
            with st.expander("📊 스타일 상세 분석"):
                for dim, score in worship_style.dimension_scores.items():
                    axis = WORSHIP_STYLE_AXES[dim]
                    # 스타일 바 표시
                    st.write(f"**{axis.low_icon} {axis.low_label}** ← → **{axis.high_label} {axis.high_icon}**")
                    st.progress(float(score))
                    if score < 0.35:
                        st.caption(f"→ {axis.worship_context_low}")
                    elif score > 0.65:
                        st.caption(f"→ {axis.worship_context_high}")
                    else:
                        st.caption("→ 다양한 상황에 유연하게 적응")

            # 📱 SNS 공유 이미지 생성
            with st.expander("📱 SNS 공유 이미지 다운로드"):
                st.caption("페르소나 카드를 이미지로 저장하여 SNS에 공유하세요!")
                share_col1, share_col2 = st.columns(2)

                with share_col1:
                    if st.button("📥 스토리용 (9:16)", key="share_story_dual"):
                        try:
                            from components.share_image import create_persona_card_image

                            dim_scores_str = {
                                dim.value if hasattr(dim, 'value') else str(dim): score
                                for dim, score in worship_style.dimension_scores.items()
                            }

                            img_bytes = create_persona_card_image(
                                style_name=worship_style.style_name,
                                style_name_en=worship_style.style_name_en,
                                icon=worship_style.icon,
                                description=worship_style.description,
                                strengths=worship_style.strengths,
                                best_fit_contexts=worship_style.best_fit_contexts,
                                dimension_scores=dim_scores_str
                            )

                            st.download_button(
                                label="💾 이미지 저장",
                                data=img_bytes,
                                file_name="worship_vocal_persona.png",
                                mime="image/png",
                                key="download_story_dual"
                            )
                            st.success("이미지가 생성되었습니다!")
                        except Exception as e:
                            st.error(f"이미지 생성 실패: {e}")

                with share_col2:
                    if st.button("📥 정사각형 (1:1)", key="share_square_dual"):
                        try:
                            from components.share_image import create_mini_card_image

                            dim_scores_str = {
                                dim.value if hasattr(dim, 'value') else str(dim): score
                                for dim, score in worship_style.dimension_scores.items()
                            }

                            img_bytes = create_mini_card_image(
                                style_name=worship_style.style_name,
                                icon=worship_style.icon,
                                dimension_scores=dim_scores_str
                            )

                            st.download_button(
                                label="💾 이미지 저장",
                                data=img_bytes,
                                file_name="worship_vocal_mini.png",
                                mime="image/png",
                                key="download_square_dual"
                            )
                            st.success("이미지가 생성되었습니다!")
                        except Exception as e:
                            st.error(f"이미지 생성 실패: {e}")

            # 📄 PDF 리포트 다운로드 (이중 분석)
            with st.expander("📄 PDF 리포트 다운로드"):
                st.caption("이중 분석 결과를 PDF 파일로 저장하여 보관하거나 공유하세요!")

                if st.button("📄 PDF 리포트 생성", key="generate_pdf_dual"):
                    try:
                        from components.pdf_report import generate_vocal_report_pdf

                        # 차원 점수 변환
                        dim_scores_dict = {
                            dim.value if hasattr(dim, 'value') else str(dim): score
                            for dim, score in worship_style.dimension_scores.items()
                        }

                        # 평균 features 계산
                        avg_features = {
                            'pitch_accuracy_cents': (features_a.get('pitch_accuracy_cents', 0) + features_b.get('pitch_accuracy_cents', 0)) / 2,
                            'high_note_stability': (features_a.get('high_note_stability', 0) + features_b.get('high_note_stability', 0)) / 2,
                            'dynamic_range_db': (features_a.get('dynamic_range_db', 0) + features_b.get('dynamic_range_db', 0)) / 2,
                            'pitch_mean': (features_a.get('pitch_mean', 0) + features_b.get('pitch_mean', 0)) / 2,
                            'avg_phrase_length': (features_a.get('avg_phrase_length', 0) + features_b.get('avg_phrase_length', 0)) / 2,
                            'vibrato_ratio': (features_a.get('vibrato_ratio', 0) + features_b.get('vibrato_ratio', 0)) / 2,
                            'rhythm_offset_ms': (features_a.get('rhythm_offset_ms', 0) + features_b.get('rhythm_offset_ms', 0)) / 2,
                        }

                        coaching_text = f"이중 분석 결과: {result.slow_song.song_title} + {result.fast_song.song_title}"

                        pdf_bytes = generate_vocal_report_pdf(
                            style_name=worship_style.style_name,
                            style_name_en=worship_style.style_name_en,
                            icon=worship_style.icon,
                            description=worship_style.description,
                            strengths=worship_style.strengths,
                            best_fit=worship_style.best_fit_contexts,
                            scorecard=dim_scores_dict,
                            features=avg_features,
                            coaching_text=coaching_text,
                            matching_songs=[],
                            challenge_songs=[]
                        )

                        if pdf_bytes[:4] == b'%PDF':
                            file_ext = "pdf"
                            mime_type = "application/pdf"
                        else:
                            file_ext = "txt"
                            mime_type = "text/plain"

                        st.download_button(
                            label=f"💾 리포트 저장 (.{file_ext})",
                            data=pdf_bytes,
                            file_name=f"vocal_report_dual_{datetime.now().strftime('%Y%m%d')}.{file_ext}",
                            mime=mime_type,
                            key="download_pdf_dual"
                        )
                        st.success("리포트가 생성되었습니다!")

                    except Exception as e:
                        st.error(f"PDF 생성 실패: {e}")
                        st.info("💡 PDF 생성을 위해 `pip install fpdf2` 설치가 필요할 수 있습니다.")

            st.markdown("---")

            # 레이더 차트 + DNA 차트
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                radar_fig = create_radar_chart(result.radar_stats, "📊 VOCAL STAT RADAR")
                st.plotly_chart(radar_fig, use_container_width=True, key="dual_radar")

            with col_chart2:
                dna_fig = create_dna_chart(result.vocal_dna)
                st.plotly_chart(dna_fig, use_container_width=True, key="dual_dna")

            # 곡별 비교 차트
            st.subheader("📀 곡별 비교")

            comparison_fig = create_comparison_bar_chart(
                features_a, features_b,
                result.slow_song.song_title,
                result.fast_song.song_title
            )
            st.plotly_chart(comparison_fig, use_container_width=True, key="dual_comparison")

            # 상세 비교 테이블
            comp_col1, comp_col2 = st.columns(2)

            with comp_col1:
                st.markdown(f"**🎵 {result.slow_song.song_title}**")
                st.write(f"- 평균 음역: {features_a['avg_pitch_hz']:.1f} Hz ({hz_to_note_name(features_a['avg_pitch_hz'])})")
                st.write(f"- 음역폭: {features_a['pitch_range_semitones']:.1f} 반음")
                st.write(f"- 다이나믹 레인지: {features_a['dynamic_range_db']:.1f} dB")
                st.write(f"- 음정 정확도: {features_a['pitch_accuracy_cents']:.1f} cents")
                st.write(f"- 고음 안정성: {features_a['high_note_stability']*100:.0f}%")

            with comp_col2:
                st.markdown(f"**🎵 {result.fast_song.song_title}**")
                st.write(f"- 평균 음역: {features_b['avg_pitch_hz']:.1f} Hz ({hz_to_note_name(features_b['avg_pitch_hz'])})")
                st.write(f"- 음역폭: {features_b['pitch_range_semitones']:.1f} 반음")
                st.write(f"- 다이나믹 레인지: {features_b['dynamic_range_db']:.1f} dB")
                st.write(f"- 음정 정확도: {features_b['pitch_accuracy_cents']:.1f} cents")
                st.write(f"- 고음 안정성: {features_b['high_note_stability']*100:.0f}%")

            # 처방전 (LLM 기반)
            if hasattr(result, 'solution') and result.solution:
                st.subheader("💊 처방전")
                st.warning(f"**문제**: {result.enemy_description}")
                st.success(f"**해결책**: {result.solution}")
                st.info(f"**오늘의 연습**: {result.exercise}")

            # 전체 평가 (LLM)
            if hasattr(result, 'overall_assessment') and result.overall_assessment:
                st.subheader("💬 AI 코치의 한마디")
                st.success(result.overall_assessment)

        with tab2:
            # Song A 기술적 분석
            st.subheader(f"🎵 Song A: {result.slow_song.song_title}")
            render_technical_analysis(features_a, key_prefix="song_a")

        with tab3:
            # Song B 기술적 분석
            st.subheader(f"🎵 Song B: {result.fast_song.song_title}")
            render_technical_analysis(features_b, key_prefix="song_b")

        with tab4:
            # 추천 찬양 탭
            st.subheader("🎵 추천 찬양")
            st.markdown("AI가 당신의 보컬 스타일을 분석하여 추천하는 찬양입니다.")

            # 어울리는 찬양
            st.markdown("### 💚 어울리는 찬양")
            st.info("현재 보컬 스타일과 잘 맞는 곡들입니다. 강점을 살려 자신감 있게 불러보세요!")

            if hasattr(result, 'matching_songs') and result.matching_songs:
                for i, song in enumerate(result.matching_songs, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{i}. {song.title}** - {song.artist}")
                            st.write(f"📝 {song.reason}")
                        with col2:
                            if song.youtube_url:
                                st.link_button("▶️ YouTube", song.youtube_url)
                        st.markdown("---")
            else:
                st.warning("추천 곡 데이터가 없습니다. 분석을 다시 실행해주세요.")

            st.markdown("---")

            # 도전해볼 찬양
            st.markdown("### 🔥 도전해볼 찬양")
            st.warning("약점을 극복하고 성장하는 데 도움이 되는 곡들입니다. 연습용으로 도전해보세요!")

            if hasattr(result, 'challenge_songs') and result.challenge_songs:
                for i, song in enumerate(result.challenge_songs, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{i}. {song.title}** - {song.artist}")
                            st.write(f"📝 {song.reason}")
                        with col2:
                            if song.youtube_url:
                                st.link_button("▶️ YouTube", song.youtube_url)
                        st.markdown("---")
            else:
                st.warning("추천 곡 데이터가 없습니다. 분석을 다시 실행해주세요.")

            # 추천 기준 설명
            with st.expander("ℹ️ 추천 기준"):
                st.markdown("""
                **어울리는 찬양 선정 기준:**
                - 현재 음역대에 맞는 곡
                - 음색과 어울리는 장르/분위기
                - 강점을 살릴 수 있는 테크닉 요구사항

                **도전 찬양 선정 기준:**
                - 약점 영역을 연습할 수 있는 곡
                - 적절히 도전적이면서 불가능하지 않은 난이도
                - 성장에 도움이 되는 특정 기술 요구
                """)

        with tab5:
            # MBTI 전체 타입 탭
            st.subheader("📋 보컬 MBTI 전체 유형")
            st.markdown("6가지 보컬 MBTI 유형을 확인하고, 당신의 타입과 비교해보세요.")

            current_type = result.vocal_mbti
            st.info(f"🎯 **당신의 타입: {current_type}**")

            st.markdown("---")

            from vocal_mbti import VOCAL_TYPES
            for code, vtype in VOCAL_TYPES.items():
                is_current = code == current_type
                icon = "✅ " if is_current else ""

                st.markdown(f"### {icon}{code}: {vtype.name_en}")
                st.markdown(f"**{vtype.name_kr}**")
                st.write(vtype.description)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**✨ 강점:**")
                    for s in vtype.strengths:
                        st.write(f"• {s}")
                with col2:
                    st.markdown("**🎤 롤모델:**")
                    for r in vtype.role_models:
                        st.write(f"• {r}")

                st.markdown("---")

        with tab6:
            # 오디오 다운로드 탭 (이중 분석용)
            st.subheader("📥 분리된 오디오 다운로드")

            if hasattr(st.session_state, 'dual_separation_result') and st.session_state.dual_separation_result:
                sep_data = st.session_state.dual_separation_result

                # Song A 다운로드
                st.markdown(f"### 🎵 {sep_data['song_a']['title']}")
                st.success(f"✅ 보컬 분리 완료! (신뢰도: {sep_data['song_a']['confidence'] * 100:.0f}%)")

                col_a1, col_a2 = st.columns(2)

                with col_a1:
                    st.markdown("**🎤 보컬 트랙**")
                    if sep_data['song_a']['vocals_path'] and os.path.exists(sep_data['song_a']['vocals_path']):
                        with open(sep_data['song_a']['vocals_path'], 'rb') as f:
                            vocals_data_a = f.read()
                        st.audio(vocals_data_a, format='audio/wav')
                        st.download_button(
                            label="📥 보컬 다운로드 (WAV)",
                            data=vocals_data_a,
                            file_name=f"vocals_{sep_data['song_a']['title']}.wav",
                            mime="audio/wav",
                            key="download_vocals_a"
                        )
                    else:
                        st.warning("보컬 파일을 찾을 수 없습니다.")

                with col_a2:
                    st.markdown("**🎹 반주 트랙**")
                    if sep_data['song_a']['instrumental_path'] and os.path.exists(sep_data['song_a']['instrumental_path']):
                        with open(sep_data['song_a']['instrumental_path'], 'rb') as f:
                            instrumental_data_a = f.read()
                        st.audio(instrumental_data_a, format='audio/wav')
                        st.download_button(
                            label="📥 반주 다운로드 (WAV)",
                            data=instrumental_data_a,
                            file_name=f"instrumental_{sep_data['song_a']['title']}.wav",
                            mime="audio/wav",
                            key="download_instrumental_a"
                        )
                    else:
                        st.warning("반주 파일을 찾을 수 없습니다.")

                st.markdown("---")

                # Song B 다운로드
                st.markdown(f"### 🎵 {sep_data['song_b']['title']}")
                st.success(f"✅ 보컬 분리 완료! (신뢰도: {sep_data['song_b']['confidence'] * 100:.0f}%)")

                col_b1, col_b2 = st.columns(2)

                with col_b1:
                    st.markdown("**🎤 보컬 트랙**")
                    if sep_data['song_b']['vocals_path'] and os.path.exists(sep_data['song_b']['vocals_path']):
                        with open(sep_data['song_b']['vocals_path'], 'rb') as f:
                            vocals_data_b = f.read()
                        st.audio(vocals_data_b, format='audio/wav')
                        st.download_button(
                            label="📥 보컬 다운로드 (WAV)",
                            data=vocals_data_b,
                            file_name=f"vocals_{sep_data['song_b']['title']}.wav",
                            mime="audio/wav",
                            key="download_vocals_b"
                        )
                    else:
                        st.warning("보컬 파일을 찾을 수 없습니다.")

                with col_b2:
                    st.markdown("**🎹 반주 트랙**")
                    if sep_data['song_b']['instrumental_path'] and os.path.exists(sep_data['song_b']['instrumental_path']):
                        with open(sep_data['song_b']['instrumental_path'], 'rb') as f:
                            instrumental_data_b = f.read()
                        st.audio(instrumental_data_b, format='audio/wav')
                        st.download_button(
                            label="📥 반주 다운로드 (WAV)",
                            data=instrumental_data_b,
                            file_name=f"instrumental_{sep_data['song_b']['title']}.wav",
                            mime="audio/wav",
                            key="download_instrumental_b"
                        )
                    else:
                        st.warning("반주 파일을 찾을 수 없습니다.")

                st.markdown("---")
                st.info("💡 **활용 팁:** 분리된 보컬로 음정 연습을, 반주로 MR 연습을 할 수 있습니다!")

            else:
                st.info("🎤 보컬 분리를 사용하지 않았습니다.")
                st.write("'반주와 함께' 또는 '찬양팀과 함께' 옵션으로 분석하면 분리된 오디오를 다운로드할 수 있습니다.")


# =============================================
# 단일 분석 모드 (기존 로직)
# =============================================

else:
    # 세션 상태 초기화
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'separation_result' not in st.session_state:
        st.session_state.separation_result = None

    st.header("1️⃣ 찬양 업로드")

    input_method = st.radio(
        "입력 방식을 선택하세요",
        ["🔗 YouTube 링크", "📁 파일 업로드"],
        horizontal=True
    )

    audio_path = None

    if input_method == "🔗 YouTube 링크":
        url = st.text_input("YouTube URL을 입력하세요", placeholder="https://www.youtube.com/watch?v=...")

        # 구간 선택 UI 개선
        st.markdown("##### ✂️ 구간 선택")
        st.caption("분석할 구간을 지정하세요. 비워두면 전체 영상을 분석합니다.")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_time = st.text_input("⏱️ 시작", "0:00", help="형식: MM:SS 또는 HH:MM:SS")
        with col2:
            end_time = st.text_input("⏱️ 종료", "", help="비워두면 끝까지 추출")
        with col3:
            # 예상 길이 표시
            if start_time and end_time:
                try:
                    start_sec = time_to_seconds(start_time) or 0
                    end_sec = time_to_seconds(end_time)
                    if end_sec and end_sec > start_sec:
                        duration = end_sec - start_sec
                        st.metric("길이", f"{duration//60}:{duration%60:02d}")
                except:
                    pass

        # 빠른 구간 선택 버튼
        st.caption("💡 빠른 선택:")
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)
        with qcol1:
            if st.button("1분", key="q1"):
                st.session_state.quick_duration = 60
        with qcol2:
            if st.button("2분", key="q2"):
                st.session_state.quick_duration = 120
        with qcol3:
            if st.button("3분", key="q3"):
                st.session_state.quick_duration = 180
        with qcol4:
            if st.button("전체", key="qall"):
                st.session_state.quick_duration = None

        if st.button("🎵 오디오 추출", type="primary") and url:
            with st.spinner("YouTube에서 오디오 추출 중..."):
                try:
                    audio_path, video_title = extract_youtube_audio(url, start_time, end_time, "single_analysis")
                    st.session_state.single_audio_path = audio_path
                    st.session_state.single_video_title = video_title
                    st.success(f"✅ 추출 완료! ({video_title})")
                    st.audio(audio_path)
                except Exception as e:
                    st.error(f"추출 실패: {e}")

    elif input_method == "📁 파일 업로드":
        uploaded_file = st.file_uploader(
            "오디오 파일을 선택하세요",
            type=['mp3', 'wav', 'm4a', 'ogg']
        )

        if uploaded_file:
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            audio_path = temp_path
            st.session_state.single_audio_path = audio_path
            # P1: 파일명 저장 (히스토리용)
            st.session_state.uploaded_file_name = uploaded_file.name.rsplit('.', 1)[0]
            st.audio(uploaded_file)

    # 이전에 추출한 오디오 사용
    if 'single_audio_path' in st.session_state:
        audio_path = st.session_state.single_audio_path

    # 녹음 환경 설정
    if audio_path:
        st.header("2️⃣ 녹음 환경")

        recording_type = st.selectbox(
            "녹음 상황을 선택하세요",
            [
                "🎤 솔로 녹음 (나만 녹음됨)",
                "🎹 반주와 함께 (MR + 내 목소리)",
                "👥 찬양팀과 함께 (내가 메인 인도자)",
                "🎵 여러 싱어 중 하나 (하모니 파트)"
            ],
            help="녹음 환경에 따라 AI 보컬 분리 여부가 결정됩니다. 정확한 분석을 위해 실제 녹음 상황을 선택해주세요."
        )

        # P1: 옵션별 상세 설명
        with st.expander("ℹ️ 녹음 환경 설명", expanded=False):
            st.markdown("""
| 옵션 | 설명 | AI 보컬 분리 |
|------|------|-------------|
| **🎤 솔로 녹음** | 목소리만 녹음된 파일 (아카펠라, 보이스메모 등) | ❌ 불필요 |
| **🎹 반주와 함께** | MR + 내 목소리가 함께 녹음됨 | ✅ 자동 분리 |
| **👥 찬양팀과 함께** | 내가 메인이고 배경에 다른 싱어가 있음 | ✅ 자동 분리 |
| **🎵 하모니 파트** | 여러 명이 함께 부르고 내가 그 중 하나 | ⚠️ 정확도 낮음 |
            """)

        need_separation = recording_type != "🎤 솔로 녹음 (나만 녹음됨)"

        if need_separation:
            st.info("🔧 AI가 자동으로 보컬을 분리하여 분석합니다. 파일 길이에 따라 1-5분 소요될 수 있습니다.")
            if recording_type == "🎵 여러 싱어 중 하나 (하모니 파트)":
                st.warning("⚠️ 하모니 중 특정 파트 분리는 정확도가 낮을 수 있습니다. 가능하면 솔로 녹음을 권장합니다.")

    # 분석 실행
    if audio_path and st.button("🔍 AI 분석 시작", type="primary"):

        # P0: 로딩 단계 상세 표시
        progress = st.progress(0)
        status_container = st.container()
        with status_container:
            status = st.empty()
            detail = st.empty()

        try:
            # 보컬 분리 (필요시)
            if need_separation:
                status.markdown("### 🎭 보컬 분리 중...")
                detail.caption("AI가 목소리만 추출하고 있어요. 파일 길이에 따라 1-5분 정도 소요됩니다.")
                from vocal_separator import auto_separate, SeparationMode

                sep_result = auto_separate(
                    audio_path,
                    "/tmp/separated",
                    mode=SeparationMode.VOCALS_ONLY
                )

                if sep_result.success and sep_result.lead_vocals_path:
                    audio_path = sep_result.lead_vocals_path
                    st.info(f"✅ 보컬 분리 완료! (신뢰도: {sep_result.confidence * 100:.0f}%)")
                    # 분리 결과 저장 (다운로드용)
                    st.session_state.separation_result = {
                        'vocals_path': sep_result.lead_vocals_path,
                        'instrumental_path': sep_result.instrumental_path,
                        'confidence': sep_result.confidence
                    }
                progress.progress(25)

            # 특징 추출 (시계열 데이터 포함)
            status.markdown("### 📊 음성 분석 중...")
            detail.caption("피치, 음량, 음색을 분석하고 있어요.")
            features = analyze_audio_features(audio_path, include_timeseries=True)
            progress.progress(50)

            # MBTI 분류
            status.markdown("### 🧬 보컬 DNA 계산 중...")
            detail.caption("당신의 보컬 스타일을 파악하고 있어요.")

            from vocal_mbti import VocalFeatures, classify_vocal_type, VOCAL_TYPES, calculate_scorecard

            vocal_features = VocalFeatures(
                pitch_range_semitones=features['pitch_range_semitones'],
                avg_pitch_hz=features['avg_pitch_hz'],
                high_note_ratio=features['high_note_ratio'],
                low_note_ratio=features['low_note_ratio'],
                dynamic_range_db=features['dynamic_range_db'],
                energy_variance=features['energy_variance'],
                climax_intensity=features['climax_intensity'],
                spectral_centroid_hz=features['spectral_centroid_hz'],
                warmth_score=features['warmth_score'],
                vibrato_ratio=features['vibrato_ratio'],
                pitch_stability=features['pitch_stability'],
                pitch_accuracy_cents=features['pitch_accuracy_cents'],
                tempo_bpm=features['tempo_bpm'],
                breath_phrase_length=features['breath_phrase_length'],
                flat_tendency=features['flat_tendency'],
                sharp_tendency=features['sharp_tendency']
            )

            primary_type, scores = classify_vocal_type(vocal_features)
            vocal_type_info = VOCAL_TYPES[primary_type]
            scorecard = calculate_scorecard(vocal_features)
            progress.progress(75)

            # 감성 해석
            status.markdown("### 💝 피드백 생성 중...")
            detail.caption("맞춤 피드백을 작성하고 있어요.")
            from emotional_interpreter import generate_local_feedback
            feedback = generate_local_feedback(vocal_features, vocal_type_info, scorecard)
            progress.progress(85)

            # LLM 기반 추천곡 분석
            status.markdown("### 🤖 AI 코칭 생성 중...")
            detail.caption("Claude AI가 맞춤 코칭과 추천곡을 준비하고 있어요.")
            from llm_analyzer import analyze_single_with_llm
            llm_single_result = analyze_single_with_llm(features, "분석된 곡")
            progress.progress(100)

            status.markdown("### ✅ 분석 완료!")
            detail.caption("결과를 확인해보세요!")

            # 결과 저장
            st.session_state.analysis_result = {
                'features': vocal_features,
                'raw_features': features,
                'primary_type': primary_type,
                'scores': scores,
                'vocal_type_info': vocal_type_info,
                'scorecard': scorecard,
                'feedback': feedback,
                'llm_result': llm_single_result
            }

            # P1: 히스토리에 추가
            song_title = st.session_state.get('single_video_title', st.session_state.get('uploaded_file_name', '분석된 곡'))
            st.session_state.analysis_history.append({
                'timestamp': datetime.now(),
                'song_title': song_title,
                'mbti_type': primary_type,
            })

        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
            import traceback
            st.code(traceback.format_exc())

    # 결과 표시
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result

        st.header("3️⃣ 분석 결과")

        # 탭 인터페이스
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎭 보컬 코칭", "📊 기술적 분석", "🎵 추천 찬양", "📋 보컬 MBTI 유형", "📥 오디오 다운로드"])

        with tab1:
            # 🧬 VOCAL IDENTITY 섹션 (이중분석 스타일)
            st.markdown("### 🧬 VOCAL IDENTITY")

            id_col1, id_col2 = st.columns([1, 2])

            with id_col1:
                st.metric("MBTI 타입", result['primary_type'])
                st.markdown(f"**{result['vocal_type_info'].name_en}**")

            with id_col2:
                st.markdown(f"**{result['vocal_type_info'].name_kr}**")
                st.write(result['vocal_type_info'].description)
                st.markdown("**🎤 롤모델:** " + ", ".join(result['vocal_type_info'].role_models))

            st.markdown("---")

            # ⭐ YOUR SIGNATURE / 🎯 GROWTH POINT (2열)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### ⭐ YOUR SIGNATURE")
                st.success("**당신의 강점**")
                for s in result['vocal_type_info'].strengths:
                    st.write(f"✅ {s}")

            with col2:
                st.markdown("### 🎯 GROWTH POINT")
                st.warning("**성장 포인트**")
                for w in result['vocal_type_info'].weaknesses:
                    st.write(f"📌 {w}")

            st.markdown("---")

            # ⛪ 찬양 예배 스타일
            st.markdown("### ⛪ 찬양 예배 스타일")
            from worship_style import calculate_worship_style, WORSHIP_STYLE_AXES, StyleDimension

            features = result['raw_features']
            worship_style = calculate_worship_style(features)

            st.success(f"{worship_style.icon} **{worship_style.style_name}** ({worship_style.style_name_en})")
            st.write(worship_style.description)

            style_col1, style_col2 = st.columns(2)
            with style_col1:
                st.markdown("**✨ 강점:**")
                for strength in worship_style.strengths:
                    st.write(f"• {strength}")
            with style_col2:
                st.markdown("**⛪ 어울리는 예배:**")
                for context in worship_style.best_fit_contexts:
                    st.write(f"• {context}")

            with st.expander("📊 스타일 상세 분석"):
                for dim, score in worship_style.dimension_scores.items():
                    axis = WORSHIP_STYLE_AXES[dim]
                    st.write(f"**{axis.low_icon} {axis.low_label}** ← → **{axis.high_label} {axis.high_icon}**")
                    st.progress(float(score))
                    if score < 0.35:
                        st.caption(f"→ {axis.worship_context_low}")
                    elif score > 0.65:
                        st.caption(f"→ {axis.worship_context_high}")
                    else:
                        st.caption("→ 다양한 상황에 유연하게 적응")

            # 📱 SNS 공유 이미지 생성
            with st.expander("📱 SNS 공유 이미지 다운로드"):
                st.caption("페르소나 카드를 이미지로 저장하여 SNS에 공유하세요!")
                share_col1, share_col2 = st.columns(2)

                with share_col1:
                    if st.button("📥 스토리용 (9:16)", key="share_story_single"):
                        try:
                            from components.share_image import create_persona_card_image

                            # dimension_scores를 문자열 키로 변환
                            dim_scores_str = {
                                dim.value if hasattr(dim, 'value') else str(dim): score
                                for dim, score in worship_style.dimension_scores.items()
                            }

                            img_bytes = create_persona_card_image(
                                style_name=worship_style.style_name,
                                style_name_en=worship_style.style_name_en,
                                icon=worship_style.icon,
                                description=worship_style.description,
                                strengths=worship_style.strengths,
                                best_fit_contexts=worship_style.best_fit_contexts,
                                dimension_scores=dim_scores_str
                            )

                            st.download_button(
                                label="💾 이미지 저장",
                                data=img_bytes,
                                file_name="worship_vocal_persona.png",
                                mime="image/png",
                                key="download_story_single"
                            )
                            st.success("이미지가 생성되었습니다!")
                        except Exception as e:
                            st.error(f"이미지 생성 실패: {e}")

                with share_col2:
                    if st.button("📥 정사각형 (1:1)", key="share_square_single"):
                        try:
                            from components.share_image import create_mini_card_image

                            dim_scores_str = {
                                dim.value if hasattr(dim, 'value') else str(dim): score
                                for dim, score in worship_style.dimension_scores.items()
                            }

                            img_bytes = create_mini_card_image(
                                style_name=worship_style.style_name,
                                icon=worship_style.icon,
                                dimension_scores=dim_scores_str
                            )

                            st.download_button(
                                label="💾 이미지 저장",
                                data=img_bytes,
                                file_name="worship_vocal_mini.png",
                                mime="image/png",
                                key="download_square_single"
                            )
                            st.success("이미지가 생성되었습니다!")
                        except Exception as e:
                            st.error(f"이미지 생성 실패: {e}")

            # 📄 PDF 리포트 다운로드
            with st.expander("📄 PDF 리포트 다운로드"):
                st.caption("분석 결과를 PDF 파일로 저장하여 보관하거나 공유하세요!")

                if st.button("📄 PDF 리포트 생성", key="generate_pdf_single"):
                    try:
                        from components.pdf_report import generate_vocal_report_pdf

                        # 차원 점수 변환
                        dim_scores_dict = {
                            dim.value if hasattr(dim, 'value') else str(dim): score
                            for dim, score in worship_style.dimension_scores.items()
                        }

                        # LLM 결과에서 추천 곡 추출
                        llm_result = result.get('llm_result')
                        matching = []
                        challenge = []
                        coaching_text = ""

                        if llm_result:
                            if hasattr(llm_result, 'matching_songs'):
                                matching = [s.name if hasattr(s, 'name') else str(s) for s in llm_result.matching_songs[:5]]
                            if hasattr(llm_result, 'challenge_songs'):
                                challenge = [s.name if hasattr(s, 'name') else str(s) for s in llm_result.challenge_songs[:5]]
                            if hasattr(llm_result, 'coaching_summary'):
                                coaching_text = llm_result.coaching_summary

                        pdf_bytes = generate_vocal_report_pdf(
                            style_name=worship_style.style_name,
                            style_name_en=worship_style.style_name_en,
                            icon=worship_style.icon,
                            description=worship_style.description,
                            strengths=worship_style.strengths,
                            best_fit=worship_style.best_fit_contexts,
                            scorecard=dim_scores_dict,
                            features=result['raw_features'],
                            coaching_text=coaching_text,
                            matching_songs=matching,
                            challenge_songs=challenge
                        )

                        # PDF인지 텍스트인지 확인
                        if pdf_bytes[:4] == b'%PDF':
                            file_ext = "pdf"
                            mime_type = "application/pdf"
                        else:
                            file_ext = "txt"
                            mime_type = "text/plain"

                        st.download_button(
                            label=f"💾 리포트 저장 (.{file_ext})",
                            data=pdf_bytes,
                            file_name=f"vocal_report_{datetime.now().strftime('%Y%m%d')}.{file_ext}",
                            mime=mime_type,
                            key="download_pdf_single"
                        )
                        st.success("리포트가 생성되었습니다!")

                    except Exception as e:
                        st.error(f"PDF 생성 실패: {e}")
                        st.info("💡 PDF 생성을 위해 `pip install fpdf2` 설치가 필요할 수 있습니다.")

            st.markdown("---")

            # 📊 레이더 차트 + 스코어카드 (2열)
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # 레이더 차트 생성 (features에서)
                features = result['raw_features']
                radar_stats = {
                    "음정": max(0, min(100, 100 - features['pitch_accuracy_cents'] * 2)),
                    "고음": features.get('high_note_stability', 0.8) * 100,
                    "호흡": min(100, features.get('breath_phrase_length', 3) * 15),
                    "다이나믹": min(100, features['dynamic_range_db'] * 5),
                    "안정성": features.get('pitch_stability', 0.7) * 100
                }
                radar_fig = create_radar_chart(radar_stats, "📊 VOCAL STAT RADAR")
                st.plotly_chart(radar_fig, use_container_width=True, key="single_radar")

            with chart_col2:
                # 스코어카드 (시각적으로 개선)
                st.markdown("### 📋 역량 스코어카드")
                sc = result['scorecard']

                score_items = [
                    ("🎵 음색+안정", sc.tone),
                    ("👑 리딩", sc.leadership),
                    ("🥁 리듬", sc.rhythm),
                    ("💬 전달력", sc.diction),
                    ("🔧 테크닉", sc.technique)
                ]

                for label, score in score_items:
                    emoji = "🟢" if score >= 4 else "🟡" if score >= 3 else "🔴"
                    st.markdown(f"{emoji} **{label}**: {score}/5")

                st.metric("📊 종합", f"{sc.total}/100")

            st.markdown("---")

            # 💊 처방전 스타일 피드백
            st.markdown("### 💊 AI 코칭 처방전")

            # 피드백 요약
            st.success(f"**💬 AI 코치의 한마디**\n\n{result['feedback'].summary}")

            with st.expander("📝 상세 분석 보기"):
                st.markdown(result['feedback'].detailed_feedback)

            st.markdown("---")

            # 🎯 오늘의 연습 (시각적으로 개선)
            st.markdown("### 🎯 오늘의 5분 연습")

            for i, ex in enumerate(result['feedback'].exercises, 1):
                with st.container():
                    st.info(f"**{i}. {ex['name']}** ({ex['duration']})\n\n{ex['description']}")

            st.markdown("---")

            # 📊 타입별 매칭 점수 (접히는 섹션으로)
            with st.expander("📊 타입별 매칭 점수 보기"):
                import pandas as pd
                from vocal_mbti import VOCAL_TYPES

                score_df = pd.DataFrame([
                    {"타입": VOCAL_TYPES[code].name_kr, "점수": score}
                    for code, score in sorted(result['scores'].items(), key=lambda x: x[1], reverse=True)
                ])
                st.bar_chart(score_df.set_index("타입"))

        with tab2:
            # 기술적 분석 탭
            render_technical_analysis(result['raw_features'], result['scorecard'])

        with tab3:
            # 추천 찬양 탭
            st.subheader("🎵 추천 찬양")
            st.markdown("AI가 당신의 보컬 스타일을 분석하여 추천하는 찬양입니다.")

            llm_result = result.get('llm_result')

            # 어울리는 찬양
            st.markdown("### 💚 어울리는 찬양")
            st.info("현재 보컬 스타일과 잘 맞는 곡들입니다. 강점을 살려 자신감 있게 불러보세요!")

            if llm_result and hasattr(llm_result, 'matching_songs') and llm_result.matching_songs:
                for i, song in enumerate(llm_result.matching_songs, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{i}. {song.title}** - {song.artist}")
                            st.write(f"📝 {song.reason}")
                        with col2:
                            if song.youtube_url:
                                st.link_button("▶️ YouTube", song.youtube_url)
                        st.markdown("---")
            else:
                st.warning("추천 곡 데이터가 없습니다. 분석을 다시 실행해주세요.")

            st.markdown("---")

            # 도전해볼 찬양
            st.markdown("### 🔥 도전해볼 찬양")
            st.warning("약점을 극복하고 성장하는 데 도움이 되는 곡들입니다. 연습용으로 도전해보세요!")

            if llm_result and hasattr(llm_result, 'challenge_songs') and llm_result.challenge_songs:
                for i, song in enumerate(llm_result.challenge_songs, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{i}. {song.title}** - {song.artist}")
                            st.write(f"📝 {song.reason}")
                        with col2:
                            if song.youtube_url:
                                st.link_button("▶️ YouTube", song.youtube_url)
                        st.markdown("---")
            else:
                st.warning("추천 곡 데이터가 없습니다. 분석을 다시 실행해주세요.")

            # 추천 기준 설명
            with st.expander("ℹ️ 추천 기준"):
                st.markdown("""
                **어울리는 찬양 선정 기준:**
                - 현재 음역대에 맞는 곡
                - 음색과 어울리는 장르/분위기
                - 강점을 살릴 수 있는 테크닉 요구사항

                **도전 찬양 선정 기준:**
                - 약점 영역을 연습할 수 있는 곡
                - 적절히 도전적이면서 불가능하지 않은 난이도
                - 성장에 도움이 되는 특정 기술 요구
                """)

        with tab4:
            # MBTI 전체 타입 탭
            st.subheader("📋 보컬 MBTI 전체 유형")
            st.markdown("6가지 보컬 MBTI 유형을 확인하고, 당신의 타입과 비교해보세요.")

            current_type = result['primary_type']
            st.info(f"🎯 **당신의 타입: {current_type}**")

            st.markdown("---")

            from vocal_mbti import VOCAL_TYPES
            for code, vtype in VOCAL_TYPES.items():
                is_current = code == current_type
                icon = "✅ " if is_current else ""
                bg_color = "background-color: #e8f5e9;" if is_current else ""

                st.markdown(f"### {icon}{code}: {vtype.name_en}")
                st.markdown(f"**{vtype.name_kr}**")
                st.write(vtype.description)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**✨ 강점:**")
                    for s in vtype.strengths:
                        st.write(f"• {s}")
                with col2:
                    st.markdown("**🎤 롤모델:**")
                    for r in vtype.role_models:
                        st.write(f"• {r}")

                st.markdown("---")

        with tab5:
            # 오디오 다운로드 탭
            st.subheader("📥 분리된 오디오 다운로드")

            if hasattr(st.session_state, 'separation_result') and st.session_state.separation_result:
                sep = st.session_state.separation_result
                st.success(f"✅ 보컬 분리 완료! (신뢰도: {sep['confidence'] * 100:.0f}%)")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 🎤 보컬 트랙")
                    st.write("반주가 제거된 순수 보컬 음성입니다.")
                    if sep['vocals_path'] and os.path.exists(sep['vocals_path']):
                        with open(sep['vocals_path'], 'rb') as f:
                            vocals_data = f.read()
                        st.audio(vocals_data, format='audio/wav')
                        st.download_button(
                            label="📥 보컬 다운로드 (WAV)",
                            data=vocals_data,
                            file_name="vocals_separated.wav",
                            mime="audio/wav",
                            key="download_vocals"
                        )
                    else:
                        st.warning("보컬 파일을 찾을 수 없습니다.")

                with col2:
                    st.markdown("### 🎹 반주 트랙")
                    st.write("보컬이 제거된 반주(MR) 음성입니다.")
                    if sep['instrumental_path'] and os.path.exists(sep['instrumental_path']):
                        with open(sep['instrumental_path'], 'rb') as f:
                            instrumental_data = f.read()
                        st.audio(instrumental_data, format='audio/wav')
                        st.download_button(
                            label="📥 반주 다운로드 (WAV)",
                            data=instrumental_data,
                            file_name="instrumental_separated.wav",
                            mime="audio/wav",
                            key="download_instrumental"
                        )
                    else:
                        st.warning("반주 파일을 찾을 수 없습니다.")

                st.markdown("---")
                st.info("💡 **활용 팁:** 분리된 보컬로 음정 연습을, 반주로 MR 연습을 할 수 있습니다!")

            else:
                st.info("🎤 보컬 분리를 사용하지 않았습니다.")
                st.write("'반주와 함께' 또는 '찬양팀과 함께' 옵션으로 분석하면 분리된 오디오를 다운로드할 수 있습니다.")

        # P1: 다음에 해볼 것 가이드
        st.markdown("---")
        with st.expander("🚀 다음에 해볼 것", expanded=False):
            st.markdown("""
### 분석 결과를 활용하는 방법

**1️⃣ 이중 분석으로 더 깊이 알아보기**
- 사이드바에서 '이중 분석' 모드를 선택하세요
- 느린 곡 + 빠른 곡을 함께 분석하면 더 입체적인 보컬 페르소나를 알 수 있어요

**2️⃣ 추천 찬양 연습하기**
- '추천 찬양' 탭에서 당신에게 어울리는 찬양을 확인하세요
- YouTube에서 MR을 찾아 연습해보세요

**3️⃣ 성장 포인트 연습**
- '보컬 코칭' 탭의 GROWTH POINT를 확인하세요
- 각 항목에 대한 연습 방법을 따라해보세요

**4️⃣ 결과 공유하기**
- SNS 이미지를 다운로드하여 친구들과 공유하세요
- PDF 리포트로 저장하여 나중에 다시 확인할 수 있어요

**5️⃣ 주기적으로 분석하기**
- 연습 후 다시 분석하여 성장을 확인해보세요
- 같은 곡을 시간 간격을 두고 분석하면 발전 정도를 알 수 있어요
            """)


# =============================================
# 푸터
# =============================================

st.markdown("---")
st.markdown("Made with ❤️ for Worship Leaders | Dual-Core Analysis Engine v3.0")
