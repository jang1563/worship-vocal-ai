# CLAUDE.md

## 프로젝트
Worship Vocal AI Coach - 찬양 인도자를 위한 AI 보컬 코칭

## 핵심 컨셉
**이중 분석 엔진 (Dual-Core Analysis)**
- 느린 곡(Mission A) + 빠른 곡(Mission B) 2개를 비교 분석
- 입체적인 보컬 페르소나 도출
- 두 스타일에서 공통되는 강점/약점 발견

## 핵심 기능
1. **이중 분석 모드**: Mission A/B 교차 비교
2. **보컬 페르소나**: "반전의 승부사", "흔들림 없는 닻" 등 캐릭터 부여
3. **The Signature**: 두 곡에서 공통 발견되는 강점 (필살기)
4. **The Hidden Enemy**: 스타일 관통 약점 + 처방전
5. **5각형 레이더**: 감성/음색/리듬/발성/리딩
6. **6차원 DNA**: 따뜻함/파워/안정성/표현력/그루브/친밀감
7. **보컬 MBTI**: 6가지 타입 (ST, WL, PA, IN, JO, SO)

## 핵심 파일
- `app.py`: Streamlit 메인 앱 (단일 + 이중 분석 모드)
- `dual_core_analyzer.py`: 이중 분석 엔진
- `vocal_coach_v2.py`: 보컬 DNA + 신뢰도 시스템
- `vocal_mbti.py`: 6가지 보컬 MBTI 분류
- `song_recommender.py`: 찬양 추천
- `emotional_interpreter.py`: 감성 언어 번역
- `vocal_separator.py`: 보컬 분리 (Demucs/Spleeter)

## 실행
```bash
source venv/bin/activate
streamlit run app.py
```

## 테스트
```bash
python dual_core_analyzer.py
python vocal_coach_v2.py
python vocal_mbti.py
```

## 의존성
- streamlit, librosa, numpy, pandas
- plotly (레이더/DNA 차트)
- yt-dlp (YouTube 추출)
- demucs/spleeter (보컬 분리, 선택)

## 스타일
- 한국어 주석/문서
- 타입 힌트 사용
- dataclass 활용
