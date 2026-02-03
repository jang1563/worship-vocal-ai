# Worship Vocal AI Coach

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> AI-powered vocal analysis and coaching platform for worship leaders
> 찬양 인도자를 위한 AI 보컬 분석 및 코칭 플랫폼

---

## Overview

Worship Vocal AI Coach is a specialized vocal analysis system designed specifically for worship music leaders and singers. It uses advanced audio processing techniques to provide personalized feedback, helping worship teams improve their vocal performance in a spiritual context.

### Key Innovations

- **Dual-Core Analysis**: Analyze two songs (slow ballad + fast upbeat) together for comprehensive vocal profiling
- **Vocal MBTI**: 6 worship-specific vocal personality types with role models
- **6D Vocal DNA**: Multi-dimensional profiling (Warmth, Power, Stability, Expression, Groove, Intimacy)
- **Emotional Translation**: Convert technical metrics into inspirational, human-readable feedback

---

## Features

### 1. Dual-Core Analysis Engine (이중 분석)
Analyze two contrasting songs to discover:
- **THE SIGNATURE**: Your consistent vocal superpower across styles
- **THE HIDDEN ENEMY**: Pattern weaknesses with specific remedies
- **Vocal Persona**: Character-based profile like "반전의 승부사" (The Reversal Ace)

### 2. Vocal MBTI Classification (보컬 MBTI)

| Type | Name | Description |
|------|------|-------------|
| **ST** | The Storyteller | 말하듯 전하는 진정성의 보컬 |
| **WL** | The Worship Leader | 회중을 안정감 있게 이끄는 리더십 |
| **PA** | The Passionate | 폭발적 감정 표현의 열정가 |
| **IN** | The Intimate | 속삭이듯 친밀한 예배 인도 |
| **JO** | The Joyful | 밝고 경쾌한 축제의 보컬 |
| **SO** | The Soulful | 깊은 영혼의 울림, 소울풀 보컬 |

### 3. Technical Analysis (기술적 분석)
- **Pitch**: Accuracy (cents), range (semitones), stability, tendency (sharp/flat)
- **Dynamics**: dB range, climax detection, energy variance
- **Timbre**: Spectral analysis (warm vs. bright)
- **Vibrato**: Rate, depth, intentionality detection
- **Rhythm**: Beat synchronization, groove feel
- **Breath**: Phrase length, support scoring

### 4. 5-Dimension Radar Chart
Visual pentagon showing:
- 감성 (Emotion) | 음색 (Timbre) | 리듬 (Rhythm) | 발성 (Technique) | 리딩 (Leadership)

### 5. Additional Features
- YouTube audio extraction with time range selection
- Vocal separation (Demucs/Spleeter) for multi-singer recordings
- Song recommendations based on vocal profile
- PDF report export & social share images
- Growth tracking across sessions

---

## Quick Start

### Prerequisites
- Python 3.9+
- FFmpeg (for audio processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/worship-vocal-ai.git
cd worship-vocal-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Ubuntu/Debian)
sudo apt install ffmpeg

# Optional: Install vocal separation
pip install demucs
```

### Run the App

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## Usage

### Single Song Analysis
1. Upload an audio file (MP3, WAV, M4A) or paste a YouTube URL
2. For YouTube: Set start/end timestamps (e.g., `24:52` - `34:26`)
3. Select recording environment (Solo / With Team)
4. Click "분석 시작" to begin analysis

### Dual-Core Analysis
1. Switch to "이중 분석" mode in the sidebar
2. Upload Mission A (slow song) + Mission B (fast song)
3. Get cross-comparison insights and unified vocal persona

---

## Project Structure

```
worship-vocal-ai/
├── app.py                      # Main Streamlit application
├── dual_core_analyzer.py       # Dual-song comparison engine
├── vocal_coach_v2.py           # MBTI + DNA + quality scoring
├── vocal_mbti.py               # 6-type vocal classification
├── emotional_interpreter.py    # Metric → language translation
├── vocal_separator.py          # Demucs/Spleeter integration
├── song_recommender.py         # Worship song recommendations
├── llm_analyzer.py             # Claude API integration (optional)
├── worship_style.py            # Style dimension framework
├── components/
│   ├── charts.py               # Plotly visualizations
│   ├── pdf_report.py           # PDF export
│   ├── share_image.py          # Social media cards
│   └── styles.py               # CSS styling
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Frontend | Streamlit |
| Audio Processing | librosa, pydub, soundfile |
| Visualization | Plotly, Matplotlib |
| Audio Extraction | yt-dlp |
| Vocal Separation | Demucs, Spleeter (optional) |
| AI Enhancement | Anthropic Claude API (optional) |
| Export | fpdf2, Pillow |

---

## Configuration

### Environment Variables (Optional)
Create a `.env` file for API keys:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### Customization
- Modify `vocal_mbti.py` to add new vocal types
- Update `song_recommender.py` with your worship song database
- Adjust thresholds in `vocal_coach_v2.py` for calibration

---

## Example Output

```
🎭 Your Vocal Type: The Storyteller (스토리텔러)
진정성 있게 말하듯 전하는 보컬. 회중의 마음을 편안하게 열어주는 따뜻한 음색.

✨ Strengths:
• 진정성 있는 전달력
• 따뜻한 중저음
• 멘트→찬양 자연스러운 연결

🎯 Growth Points:
• 음정이 살짝 낮게 가는 경향 → 배에서 소리를 밀어올려 주세요
• 호흡 프레이즈가 짧음 → 복식호흡 연습 추천

📋 Scorecard:
   음색: 72 | 리딩: 78 | 리듬: 91 | 전달력: 67 | 테크닉: 54

🎤 Role Models: 김윤진 (어노인팅), 이영훈 (어노인팅)
```

---

## Roadmap

- [ ] Real-time coaching mode (live feedback)
- [ ] Team analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Integration with worship song databases (CCLI, Ultimate Worship)
- [ ] Multilingual support (English, Chinese, Japanese)
- [ ] Expert validation & A/B testing with 50+ vocalists

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Worship leaders and teams who provided feedback and testing
- [librosa](https://librosa.org/) for audio analysis
- [Demucs](https://github.com/facebookresearch/demucs) for vocal separation
- [Streamlit](https://streamlit.io/) for the beautiful UI framework

---

<p align="center">
Made with ❤️ for Worship Leaders<br>
찬양 인도자들을 위해 사랑으로 만들었습니다
</p>
