# 🎤 Vocal Analysis Algorithm - Expert Panel Review

## 패널 구성
- **Dr. Kim** - 음향 공학 박사, 신호 처리 전문가
- **Prof. Park** - 성악과 교수, 보컬 테크닉 전문가
- **Coach Lee** - 실용음악 보컬 트레이너, 15년 경력

---

## 1. 고음 안정성 (High Note Stability)

### 현재 알고리즘
```python
high_notes_midi = librosa.hz_to_midi(high_notes)
high_notes_std_semitones = np.std(high_notes_midi)
high_note_stability = max(0, min(1, 1 - (high_notes_std_semitones / 1.5)))
```

### 패널 리뷰

**Dr. Kim (음향 공학):**
> "1.5 반음을 기준으로 사용하는 것은 너무 엄격합니다. 프로 가수도 비브라토나 표현적 요소로 인해 0.5-1.0 반음의 자연스러운 변동이 있습니다. 2.5-3.0 반음을 기준으로 사용하면 더 현실적입니다."

**Prof. Park (성악):**
> "고음에서의 안정성은 단순 편차만으로 측정하기 어렵습니다. 비브라토와 불안정한 흔들림을 구분해야 합니다. 그러나 현재 수준에서는 편차 기준을 완화하는 것이 합리적입니다."

**Coach Lee (실용음악):**
> "일반인 기준으로 2.0 반음 이내면 '안정적', 3.0 반음 이내면 '보통', 그 이상이면 '불안정'으로 보는 게 맞습니다."

### 권장 수정
```python
# 기준을 2.5 반음으로 완화
high_note_stability = max(0, min(1, 1 - (high_notes_std_semitones / 2.5)))
```

### 예상 점수 변화
| 표준편차 (반음) | 이전 점수 | 수정 후 점수 | 해석 |
|----------------|----------|-------------|------|
| 0.3 | 80% | 88% | 매우 안정 |
| 0.5 | 67% | 80% | 안정 |
| 1.0 | 33% | 60% | 보통 |
| 1.5 | 0% | 40% | 약간 불안정 |
| 2.0 | 0% | 20% | 불안정 |
| 2.5+ | 0% | 0% | 매우 불안정 |

---

## 2. 다이나믹 레인지 (Dynamic Range)

### 현재 알고리즘
```python
dynamic_range = np.max(rms_db) - np.percentile(rms_db, 10)
# 레이더 차트: avg_dynamic * 4
# 예: 25dB → 100점
```

### 패널 리뷰

**Dr. Kim (음향 공학):**
> "일반적인 보컬의 다이나믹 레인지는 15-35dB입니다. 현재 공식은 25dB 이상이면 무조건 100점이 됩니다. 이는 구분력이 없습니다."

**Prof. Park (성악):**
> "다이나믹 레인지가 넓다고 무조건 좋은 것은 아닙니다. 너무 넓으면 컨트롤이 안 되는 것일 수 있고, 너무 좁으면 표현력이 부족한 것입니다. 15-25dB가 이상적인 범위입니다."

**Coach Lee (실용음악):**
> "찬양의 경우 12-20dB가 적절합니다. 너무 큰 다이나믹은 PA 시스템에서 다루기 어렵습니다."

### 권장 수정
```python
# 12dB = 0점, 20dB = 100점, 그 이상은 서서히 감소 (과도한 다이나믹은 컨트롤 문제)
if dynamic_range < 12:
    dynamic_score = (dynamic_range / 12) * 50  # 0-50점
elif dynamic_range <= 20:
    dynamic_score = 50 + ((dynamic_range - 12) / 8) * 50  # 50-100점
else:
    dynamic_score = max(60, 100 - (dynamic_range - 20) * 2)  # 100에서 감소
```

### 예상 점수 변화
| 다이나믹 (dB) | 이전 점수 | 수정 후 점수 | 해석 |
|--------------|----------|-------------|------|
| 8 | 32% | 33% | 표현력 부족 |
| 12 | 48% | 50% | 보통 |
| 16 | 64% | 75% | 좋음 |
| 20 | 80% | 100% | 최적 |
| 25 | 100% | 90% | 약간 과도 |
| 30 | 100% | 80% | 컨트롤 필요 |

---

## 3. 호흡/프레이즈 길이 (Breath Phrase Length)

### 현재 알고리즘
```python
phrase_length = 4.0 + (dynamic_range / 10)
# 문제: 실제 호흡이 아닌 다이나믹의 함수
```

### 패널 리뷰

**Dr. Kim (음향 공학):**
> "호흡 길이는 무음 구간(silence detection)을 기반으로 측정해야 합니다. 현재는 다이나믹 레인지의 파생 값으로 의미가 없습니다."

**Prof. Park (성악):**
> "실제 프레이즈 길이는 RMS가 특정 threshold 이하로 떨어지는 구간을 찾아 측정해야 합니다."

**Coach Lee (실용음악):**
> "찬양에서 평균 프레이즈는 3-6초입니다. 8초 이상 한 호흡으로 유지하면 '호흡 지지가 좋다'고 평가합니다."

### 권장 수정
```python
# RMS 기반 실제 프레이즈 길이 측정
rms_threshold = np.percentile(rms_db, 20)  # 하위 20%를 '쉬는 구간'으로
silence_frames = rms_db < rms_threshold
# 연속 발성 구간의 평균 길이 계산
phrase_lengths = []
current_length = 0
for is_silent in silence_frames:
    if not is_silent:
        current_length += hop_length / sr
    elif current_length > 0.5:  # 0.5초 이상만 유효한 프레이즈
        phrase_lengths.append(current_length)
        current_length = 0
avg_phrase_length = np.mean(phrase_lengths) if phrase_lengths else 3.0

# 점수화: 4초=50점, 8초=100점
breath_support_score = min(100, max(0, (avg_phrase_length - 2) / 6 * 100))
```

---

## 4. 리듬 오프셋 (Rhythm Offset)

### 현재 알고리즘
```python
rhythm_offset_ms = 30  # 임시값 (하드코딩)
```

### 패널 리뷰

**Dr. Kim (음향 공학):**
> "임시값은 분석에서 제외하거나, 실제 비트 추출 후 onset과의 오차를 측정해야 합니다."

**Coach Lee (실용음악):**
> "리듬감은 템포 변화의 일관성으로도 측정할 수 있습니다. 일정한 템포를 유지하면 리듬감이 좋은 것입니다."

### 권장 수정
```python
# 비트 추출 후 onset과의 동기화 정도 측정
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)
beat_times = librosa.frames_to_time(beats, sr=sr)

# 각 onset이 가장 가까운 beat와 얼마나 떨어져 있는지 계산
offsets = []
for onset in onset_times:
    closest_beat = beat_times[np.argmin(np.abs(beat_times - onset))]
    offsets.append(abs(onset - closest_beat) * 1000)  # ms
rhythm_offset_ms = np.mean(offsets) if offsets else 50

# 점수화: 20ms 이내 = 100점, 80ms = 50점, 150ms+ = 0점
rhythm_score = max(0, min(100, 100 - (rhythm_offset_ms - 20) * 0.77))
```

---

## 5. 발음 명료도 (Articulation Clarity)

### 현재 알고리즘
```python
articulation_clarity = min(1.0, np.mean(centroid) / 3000)
# 문제: 단순히 밝기(brightness)를 측정
```

### 패널 리뷰

**Dr. Kim (음향 공학):**
> "발음 명료도는 스펙트럼 centroid만으로는 불충분합니다. 자음의 존재(고주파 burst)와 spectral flux(스펙트럼 변화율)를 함께 봐야 합니다."

**Prof. Park (성악):**
> "명료도가 높으면 자음이 또렷하고, spectral flux가 적절히 높습니다. 너무 높으면 딱딱하게 들리고, 너무 낮으면 뭉개집니다."

### 권장 수정
```python
# Spectral flux (스펙트럼 변화율)
S = np.abs(librosa.stft(y))
spectral_flux = np.mean(np.diff(S, axis=1) ** 2)
flux_normalized = min(1.0, spectral_flux / 0.1)

# Spectral centroid 정규화 (1500-2500Hz가 최적)
centroid_score = 1 - abs(np.mean(centroid) - 2000) / 2000

# 결합
articulation_clarity = (centroid_score * 0.6 + flux_normalized * 0.4)
```

---

## 6. 종합 개선 제안

### 현재 문제점 요약
1. **고음 안정성**: 기준이 너무 엄격 (1.5반음 → 2.5반음으로 완화)
2. **다이나믹**: 무조건 높을수록 좋음 → 최적 범위(15-22dB) 설정
3. **호흡 지지**: 실제 측정 없음 → RMS 기반 프레이즈 길이 측정
4. **리듬**: 하드코딩 → onset-beat 동기화 측정
5. **명료도**: 단순 밝기 → spectral flux 결합

### 점수 분포 목표 (일반인 기준)
| 점수 범위 | 비율 | 의미 |
|----------|-----|------|
| 90-100 | 5% | 탁월함 |
| 70-89 | 25% | 우수함 |
| 50-69 | 45% | 평균 |
| 30-49 | 20% | 개선 필요 |
| 0-29 | 5% | 집중 훈련 필요 |

---

## 적용 우선순위

1. **즉시 적용** (간단한 수정)
   - 고음 안정성 기준 완화 (1.5 → 2.5)
   - 다이나믹 점수 곡선 조정

2. **단기 적용** (알고리즘 추가)
   - 실제 프레이즈 길이 측정
   - 리듬 오프셋 실제 측정

3. **중기 적용** (고급 분석)
   - 비브라토 검출 및 분리
   - 발음 명료도 개선

---

*Last Updated: 2026-01-31*
*Reviewed by: Simulated Expert Panel*
