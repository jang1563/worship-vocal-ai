"""
보컬 분석 PDF 리포트 생성
Generates PDF report for vocal analysis results
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional

# reportlab 대신 간단한 HTML -> PDF 변환 사용
# fpdf2 사용 (한글 지원)
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


def sanitize_emoji(text: str) -> str:
    """이모지를 PDF에서 안전한 심볼로 대체"""
    emoji_map = {
        '🕊️': '[dove]',
        '🔥': '[fire]',
        '🎤': '[mic]',
        '🌊': '[wave]',
        '⚡': '[bolt]',
        '💫': '[star]',
        '🎵': '[note]',
        '🎶': '[notes]',
        '✨': '*',
        '🎯': '[target]',
        '📊': '[chart]',
        '🧬': '[DNA]',
        '🤖': '[AI]',
        '♪': '[note]',
        '◆': '-',
        '█': '#',
        '░': '-',
        '•': '-',
    }
    result = text
    for emoji, replacement in emoji_map.items():
        result = result.replace(emoji, replacement)
    return result


class VocalReportPDF:
    """보컬 분석 리포트 PDF 생성기"""

    def __init__(self):
        if not HAS_FPDF:
            raise ImportError("fpdf2가 필요합니다. pip install fpdf2")

        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)

        # 한글 폰트 설정 - TTF 파일 우선 사용 (TTC는 fpdf2에서 불안정)
        self.font_name = 'Helvetica'  # 기본값

        # 폰트 경로 우선순위
        font_paths = [
            # NanumGothic TTF (가장 안정적)
            ('/Library/Fonts/NanumGothic-Regular.ttf', '/Library/Fonts/NanumGothic-Bold.ttf'),
            # 사용자 폰트 디렉토리
            ('~/Library/Fonts/NanumGothic-Regular.ttf', '~/Library/Fonts/NanumGothic-Bold.ttf'),
        ]

        import os
        for regular_path, bold_path in font_paths:
            regular_path = os.path.expanduser(regular_path)
            bold_path = os.path.expanduser(bold_path)

            if os.path.exists(regular_path):
                try:
                    self.pdf.add_font('KoreanFont', '', regular_path, uni=True)
                    if os.path.exists(bold_path):
                        self.pdf.add_font('KoreanFont', 'B', bold_path, uni=True)
                    else:
                        self.pdf.add_font('KoreanFont', 'B', regular_path, uni=True)
                    self.font_name = 'KoreanFont'
                    break
                except Exception as e:
                    print(f"폰트 로딩 실패 ({regular_path}): {e}")
                    continue

    def add_title_page(self, title: str, subtitle: str = ""):
        """타이틀 페이지 추가"""
        self.pdf.add_page()
        self.pdf.set_font(self.font_name, 'B', 32)
        self.pdf.set_text_color(201, 169, 98)  # Gold

        # 중앙 정렬 타이틀
        self.pdf.ln(60)
        self.pdf.cell(0, 20, title, align='C', ln=True)

        if subtitle:
            self.pdf.set_font(self.font_name, '', 16)
            self.pdf.set_text_color(156, 163, 175)  # Gray
            self.pdf.cell(0, 10, subtitle, align='C', ln=True)

        # 날짜
        self.pdf.ln(20)
        self.pdf.set_font(self.font_name, '', 12)
        self.pdf.set_text_color(100, 105, 115)
        date_str = datetime.now().strftime("%Y년 %m월 %d일")
        self.pdf.cell(0, 10, f"분석일: {date_str}", align='C', ln=True)

        # 브랜드
        self.pdf.ln(40)
        self.pdf.set_font(self.font_name, '', 14)
        self.pdf.set_text_color(124, 92, 191)  # Purple
        self.pdf.cell(0, 10, "Worship Vocal AI Coach", align='C', ln=True)

    def add_persona_section(self, style_name: str, style_name_en: str,
                            icon: str, description: str,
                            strengths: list, best_fit: list):
        """페르소나 섹션 추가"""
        self.pdf.add_page()

        # 섹션 헤더
        self._add_section_header("보컬 페르소나")

        # 스타일 이름 (이모지 sanitize)
        self.pdf.set_font(self.font_name, 'B', 24)
        self.pdf.set_text_color(255, 255, 255)
        safe_icon = sanitize_emoji(icon) if icon else ""
        self.pdf.cell(0, 15, f"{safe_icon} {style_name}", ln=True)

        self.pdf.set_font(self.font_name, '', 14)
        self.pdf.set_text_color(156, 163, 175)
        self.pdf.cell(0, 10, style_name_en, ln=True)

        self.pdf.ln(10)

        # 설명
        self.pdf.set_font(self.font_name, '', 12)
        self.pdf.set_text_color(200, 200, 200)
        self.pdf.multi_cell(0, 7, description)

        self.pdf.ln(10)

        # 강점
        self._add_subsection("강점")
        for strength in strengths[:5]:
            self.pdf.set_font(self.font_name, '', 11)
            self.pdf.set_text_color(255, 255, 255)
            self.pdf.cell(0, 7, f"  • {strength}", ln=True)

        self.pdf.ln(5)

        # 적합한 예배
        self._add_subsection("적합한 예배 상황")
        for context in best_fit[:5]:
            self.pdf.set_font(self.font_name, '', 11)
            self.pdf.set_text_color(255, 255, 255)
            self.pdf.cell(0, 7, f"  • {context}", ln=True)

    def add_scorecard_section(self, scorecard: Dict[str, float]):
        """점수표 섹션 추가"""
        self.pdf.add_page()
        self._add_section_header("보컬 DNA 점수표")

        dimension_labels = {
            "intimacy": "친밀감",
            "dynamics": "다이나믹",
            "tone": "음색",
            "leading": "인도력",
            "sustain": "지속력",
            "expression": "표현력"
        }

        for key, value in scorecard.items():
            label = dimension_labels.get(key, key)
            pct = int(value * 100)

            self.pdf.set_font(self.font_name, '', 12)
            self.pdf.set_text_color(156, 163, 175)
            self.pdf.cell(60, 10, label)

            # 프로그레스 바 (텍스트로 표현)
            bar_filled = int(pct / 5)
            bar_empty = 20 - bar_filled
            bar_text = "█" * bar_filled + "░" * bar_empty

            self.pdf.set_font(self.font_name, '', 10)
            self.pdf.set_text_color(124, 92, 191)
            self.pdf.cell(80, 10, bar_text)

            self.pdf.set_font(self.font_name, 'B', 12)
            self.pdf.set_text_color(201, 169, 98)
            self.pdf.cell(30, 10, f"{pct}%", ln=True)

    def add_technical_section(self, features: Dict[str, Any]):
        """기술적 분석 섹션 추가"""
        self.pdf.add_page()
        self._add_section_header("기술적 분석")

        metrics = [
            ("음정 정확도", f"{features.get('pitch_accuracy_cents', 0):.1f} cents",
             "목표 음정과의 차이 (낮을수록 좋음)"),
            ("고음 안정성", f"{features.get('high_note_stability', 0)*100:.0f}%",
             "고음에서의 음정 유지력"),
            ("다이나믹 레인지", f"{features.get('dynamic_range_db', 0):.1f} dB",
             "강약 표현의 폭"),
            ("평균 음높이", f"{features.get('pitch_mean', 0):.0f} Hz",
             "전체적인 음역대"),
            ("프레이즈 길이", f"{features.get('avg_phrase_length', 0):.1f}초",
             "평균 한 호흡 길이"),
            ("비브라토", f"{features.get('vibrato_ratio', 0)*100:.0f}%",
             "떨림 표현 정도"),
            ("리듬 정확도", f"{features.get('rhythm_offset_ms', 0):.0f}ms",
             "박자 정확도 (낮을수록 좋음)"),
        ]

        for label, value, description in metrics:
            self.pdf.set_font(self.font_name, 'B', 11)
            self.pdf.set_text_color(201, 169, 98)
            self.pdf.cell(70, 8, label)

            self.pdf.set_font(self.font_name, '', 11)
            self.pdf.set_text_color(255, 255, 255)
            self.pdf.cell(50, 8, value)

            self.pdf.set_font(self.font_name, '', 9)
            self.pdf.set_text_color(100, 105, 115)
            self.pdf.cell(0, 8, description, ln=True)

            self.pdf.ln(2)

    def add_coaching_section(self, coaching_text: str):
        """AI 코칭 섹션 추가"""
        self.pdf.add_page()
        self._add_section_header("AI 코칭 피드백")

        self.pdf.set_font(self.font_name, '', 11)
        self.pdf.set_text_color(200, 200, 200)
        self.pdf.multi_cell(0, 7, coaching_text)

    def add_recommendations_section(self, matching_songs: list, challenge_songs: list):
        """추천 찬양 섹션 추가"""
        self.pdf.add_page()
        self._add_section_header("추천 찬양")

        # 어울리는 찬양
        self._add_subsection("어울리는 찬양")
        if matching_songs:
            for song in matching_songs[:5]:
                name = song.get('name', song) if isinstance(song, dict) else str(song)
                self.pdf.set_font(self.font_name, '', 11)
                self.pdf.set_text_color(74, 222, 128)  # Green
                self.pdf.cell(0, 7, f"  ♪ {name}", ln=True)
        else:
            self.pdf.set_font(self.font_name, '', 11)
            self.pdf.set_text_color(156, 163, 175)
            self.pdf.cell(0, 7, "  추천 정보 없음", ln=True)

        self.pdf.ln(10)

        # 도전할 찬양
        self._add_subsection("도전해볼 찬양")
        if challenge_songs:
            for song in challenge_songs[:5]:
                name = song.get('name', song) if isinstance(song, dict) else str(song)
                self.pdf.set_font(self.font_name, '', 11)
                self.pdf.set_text_color(251, 191, 36)  # Yellow/Warning
                self.pdf.cell(0, 7, f"  ♪ {name}", ln=True)
        else:
            self.pdf.set_font(self.font_name, '', 11)
            self.pdf.set_text_color(156, 163, 175)
            self.pdf.cell(0, 7, "  추천 정보 없음", ln=True)

    def _add_section_header(self, title: str):
        """섹션 헤더 추가"""
        self.pdf.set_font(self.font_name, 'B', 18)
        self.pdf.set_text_color(201, 169, 98)  # Gold
        self.pdf.cell(0, 15, title, ln=True)
        self.pdf.ln(5)

    def _add_subsection(self, title: str):
        """서브섹션 헤더 추가"""
        self.pdf.set_font(self.font_name, 'B', 13)
        self.pdf.set_text_color(124, 92, 191)  # Purple
        self.pdf.cell(0, 10, f"◆ {title}", ln=True)

    def generate(self) -> bytes:
        """PDF 바이트 생성"""
        return bytes(self.pdf.output())


def generate_vocal_report_pdf(
    style_name: str,
    style_name_en: str,
    icon: str,
    description: str,
    strengths: list,
    best_fit: list,
    scorecard: Dict[str, float],
    features: Dict[str, Any],
    coaching_text: str = "",
    matching_songs: list = None,
    challenge_songs: list = None
) -> bytes:
    """
    보컬 분석 PDF 리포트 생성

    Returns:
        PDF 파일 바이트 데이터
    """
    if not HAS_FPDF:
        # fpdf2가 없으면 간단한 텍스트 파일 반환
        return generate_text_report(
            style_name, style_name_en, icon, description,
            strengths, best_fit, scorecard, features,
            coaching_text, matching_songs, challenge_songs
        )

    report = VocalReportPDF()

    # 타이틀 페이지
    report.add_title_page(
        "보컬 분석 리포트",
        f"{style_name} ({style_name_en})"
    )

    # 페르소나 섹션
    report.add_persona_section(
        style_name, style_name_en, icon,
        description, strengths, best_fit
    )

    # 점수표 섹션
    report.add_scorecard_section(scorecard)

    # 기술적 분석 섹션
    report.add_technical_section(features)

    # AI 코칭 섹션 (있는 경우)
    if coaching_text:
        report.add_coaching_section(coaching_text)

    # 추천 찬양 섹션
    report.add_recommendations_section(
        matching_songs or [],
        challenge_songs or []
    )

    return report.generate()


def generate_text_report(
    style_name: str,
    style_name_en: str,
    icon: str,
    description: str,
    strengths: list,
    best_fit: list,
    scorecard: Dict[str, float],
    features: Dict[str, Any],
    coaching_text: str = "",
    matching_songs: list = None,
    challenge_songs: list = None
) -> bytes:
    """
    텍스트 형식 리포트 생성 (fpdf2 없을 때 fallback)
    """
    lines = [
        "=" * 60,
        "          WORSHIP VOCAL AI - 보컬 분석 리포트",
        "=" * 60,
        "",
        f"분석일: {datetime.now().strftime('%Y년 %m월 %d일')}",
        "",
        "-" * 60,
        "[ 보컬 페르소나 ]",
        "-" * 60,
        f"{icon} {style_name} ({style_name_en})",
        "",
        description,
        "",
        "강점:",
    ]

    for s in strengths[:5]:
        lines.append(f"  • {s}")

    lines.extend([
        "",
        "적합한 예배:",
    ])

    for b in best_fit[:5]:
        lines.append(f"  • {b}")

    lines.extend([
        "",
        "-" * 60,
        "[ 보컬 DNA 점수 ]",
        "-" * 60,
    ])

    dimension_labels = {
        "intimacy": "친밀감",
        "dynamics": "다이나믹",
        "tone": "음색",
        "leading": "인도력",
        "sustain": "지속력",
        "expression": "표현력"
    }

    for key, value in scorecard.items():
        label = dimension_labels.get(key, key)
        pct = int(value * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        lines.append(f"{label:10s} {bar} {pct}%")

    lines.extend([
        "",
        "-" * 60,
        "[ 기술적 분석 ]",
        "-" * 60,
        f"음정 정확도: {features.get('pitch_accuracy_cents', 0):.1f} cents",
        f"고음 안정성: {features.get('high_note_stability', 0)*100:.0f}%",
        f"다이나믹 레인지: {features.get('dynamic_range_db', 0):.1f} dB",
        f"평균 음높이: {features.get('pitch_mean', 0):.0f} Hz",
        f"프레이즈 길이: {features.get('avg_phrase_length', 0):.1f}초",
        "",
        "=" * 60,
        "          Powered by Worship Vocal AI Coach",
        "=" * 60,
    ])

    return "\n".join(lines).encode('utf-8')
