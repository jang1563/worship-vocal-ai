"""
SNS 공유용 페르소나 카드 이미지 생성 (Premium Version)
Generates shareable persona card images for social media
"""

import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Optional, Tuple
import math


# 색상 팔레트 (프리미엄 다크 테마)
COLORS = {
    "background": (13, 13, 18),        # #0D0D12
    "card_bg": (26, 26, 35),           # #1A1A23
    "card_bg_light": (35, 35, 48),     # Lighter card
    "gold": (201, 169, 98),            # #C9A962
    "gold_light": (230, 200, 130),     # Lighter gold
    "purple": (124, 92, 191),          # #7C5CBF
    "purple_light": (160, 130, 220),   # Lighter purple
    "purple_dark": (80, 60, 140),      # Darker purple
    "text_primary": (255, 255, 255),   # white
    "text_secondary": (156, 163, 175), # gray
    "text_muted": (100, 105, 115),     # muted
    "success": (74, 222, 128),         # green
    "border": (55, 55, 70),            # dark gray
    "border_light": (75, 75, 95),      # lighter border
    "glow": (124, 92, 191, 80),        # purple with alpha
}

# 아이콘 대체 문자 (이모지가 렌더링 안 될 때)
ICON_FALLBACK = {
    "🕊️": "♦",
    "🔥": "★",
    "⚓": "◆",
    "🌊": "≋",
    "📖": "◈",
    "🎉": "✦",
    "💚": "♥",
    "🌉": "⌘",
}


def create_gradient_background(width: int, height: int, color1: tuple, color2: tuple) -> Image.Image:
    """그라디언트 배경 생성"""
    img = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def add_glow_effect(img: Image.Image, center: tuple, radius: int, color: tuple) -> Image.Image:
    """글로우 효과 추가"""
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for i in range(radius, 0, -5):
        alpha = int(50 * (i / radius))
        glow_draw.ellipse(
            [center[0] - i, center[1] - i, center[0] + i, center[1] + i],
            fill=(*color[:3], alpha)
        )

    glow = glow.filter(ImageFilter.GaussianBlur(radius=20))

    # RGB로 변환하여 합성
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    return Image.alpha_composite(img, glow)


def get_fonts(scale: float = 1.0) -> dict:
    """폰트 로드 (macOS/Linux 호환)"""
    fonts = {}

    # macOS 폰트 경로들
    font_paths = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    font_path = None
    for path in font_paths:
        try:
            ImageFont.truetype(path, 32)
            font_path = path
            break
        except:
            continue

    if font_path:
        fonts["title"] = ImageFont.truetype(font_path, int(72 * scale))
        fonts["subtitle"] = ImageFont.truetype(font_path, int(36 * scale))
        fonts["body"] = ImageFont.truetype(font_path, int(32 * scale))
        fonts["small"] = ImageFont.truetype(font_path, int(28 * scale))
        fonts["tiny"] = ImageFont.truetype(font_path, int(22 * scale))
        fonts["brand"] = ImageFont.truetype(font_path, int(40 * scale))
    else:
        # Fallback
        default = ImageFont.load_default()
        fonts = {k: default for k in ["title", "subtitle", "body", "small", "tiny", "brand"]}

    return fonts


def draw_rounded_rect_with_border(draw: ImageDraw.Draw, coords: tuple,
                                   fill: tuple, border: tuple, radius: int, border_width: int = 2):
    """테두리가 있는 둥근 사각형"""
    x1, y1, x2, y2 = coords
    # 배경
    draw.rounded_rectangle(coords, radius=radius, fill=fill)
    # 테두리
    draw.rounded_rectangle(coords, radius=radius, outline=border, width=border_width)


def draw_progress_bar(draw: ImageDraw.Draw, x: int, y: int, width: int, height: int,
                      value: float, label: str, fonts: dict):
    """프리미엄 프로그레스 바"""
    # 라벨
    draw.text((x, y), label, fill=COLORS["text_secondary"], font=fonts["small"], anchor="lt")

    bar_y = y + 35

    # 배경 바
    draw.rounded_rectangle(
        [x, bar_y, x + width, bar_y + height],
        radius=height // 2,
        fill=COLORS["border"]
    )

    # 채움 바 (그라디언트 효과)
    fill_width = max(height, int(width * value))
    if fill_width > 0:
        # 메인 바
        draw.rounded_rectangle(
            [x, bar_y, x + fill_width, bar_y + height],
            radius=height // 2,
            fill=COLORS["purple"]
        )
        # 하이라이트
        if fill_width > 10:
            draw.rounded_rectangle(
                [x + 2, bar_y + 2, x + fill_width - 2, bar_y + height // 3],
                radius=height // 4,
                fill=COLORS["purple_light"]
            )

    # 퍼센트 텍스트
    pct_text = f"{int(value * 100)}%"
    draw.text((x + width + 15, bar_y + height // 2), pct_text,
              fill=COLORS["gold"], font=fonts["small"], anchor="lm")


def create_persona_card_image(
    style_name: str,
    style_name_en: str,
    icon: str,
    description: str,
    strengths: list,
    best_fit_contexts: list,
    dimension_scores: Dict[str, float],
    width: int = 1080,
    height: int = 1920
) -> bytes:
    """
    페르소나 카드 이미지 생성 (Instagram Story 비율 9:16)
    프리미엄 디자인 버전
    """
    # 그라디언트 배경
    img = create_gradient_background(width, height, COLORS["background"], (20, 20, 30))

    # 글로우 효과 추가
    img = img.convert('RGBA')
    glow_center = (width // 2, 350)
    img = add_glow_effect(img, glow_center, 200, COLORS["purple"])

    draw = ImageDraw.Draw(img)
    fonts = get_fonts(1.0)

    y_cursor = 60
    center_x = width // 2
    padding = 60

    # 상단 카드 영역
    card_top = y_cursor
    card_height = 520
    draw_rounded_rect_with_border(
        draw,
        (padding - 20, card_top, width - padding + 20, card_top + card_height),
        fill=(*COLORS["card_bg"], 200),
        border=COLORS["border_light"],
        radius=30
    )

    y_cursor += 40

    # 브랜드 로고
    draw.text((center_x, y_cursor), "WORSHIP VOCAL AI",
              fill=COLORS["gold"], font=fonts["brand"], anchor="mt")
    y_cursor += 70

    # 아이콘 (심볼로 대체)
    icon_symbol = ICON_FALLBACK.get(icon, "★")
    draw.text((center_x, y_cursor), icon_symbol,
              fill=COLORS["gold_light"], font=fonts["title"], anchor="mt")
    y_cursor += 100

    # 스타일 이름
    draw.text((center_x, y_cursor), style_name,
              fill=COLORS["text_primary"], font=fonts["title"], anchor="mt")
    y_cursor += 80

    # 영문 이름
    draw.text((center_x, y_cursor), style_name_en,
              fill=COLORS["text_secondary"], font=fonts["subtitle"], anchor="mt")
    y_cursor += 80

    # 구분선 (골드 그라디언트)
    line_y = y_cursor
    for i, x in enumerate(range(padding + 100, width - padding - 100)):
        alpha = 1 - abs(x - center_x) / (center_x - padding - 100)
        color = tuple(int(c * alpha) for c in COLORS["gold"])
        draw.point((x, line_y), fill=color)
    y_cursor += 50

    # 설명 (카드 밖)
    desc_lines = wrap_text(description, fonts["body"], width - padding * 2 - 40)
    for line in desc_lines[:3]:
        draw.text((center_x, y_cursor), line,
                  fill=COLORS["text_secondary"], font=fonts["body"], anchor="mt")
        y_cursor += 45
    y_cursor += 40

    # 강점 섹션 카드
    section_card_top = y_cursor
    section_card_height = 180
    draw_rounded_rect_with_border(
        draw,
        (padding, section_card_top, width - padding, section_card_top + section_card_height),
        fill=(*COLORS["card_bg"], 180),
        border=COLORS["border"],
        radius=20
    )

    y_cursor += 25
    draw.text((padding + 25, y_cursor), "✦ 강점",
              fill=COLORS["gold"], font=fonts["subtitle"], anchor="lt")
    y_cursor += 50

    for i, strength in enumerate(strengths[:3]):
        x_offset = padding + 30
        draw.text((x_offset, y_cursor), f"• {strength}",
                  fill=COLORS["text_primary"], font=fonts["small"], anchor="lt")
        y_cursor += 38

    y_cursor = section_card_top + section_card_height + 20

    # 적합한 예배 섹션 카드
    section2_top = y_cursor
    section2_height = 210
    draw_rounded_rect_with_border(
        draw,
        (padding, section2_top, width - padding, section2_top + section2_height),
        fill=(*COLORS["card_bg"], 180),
        border=COLORS["border"],
        radius=20
    )

    y_cursor += 25
    draw.text((padding + 25, y_cursor), "✦ 적합한 예배",
              fill=COLORS["gold"], font=fonts["subtitle"], anchor="lt")
    y_cursor += 50

    for context in best_fit_contexts[:4]:
        draw.text((padding + 30, y_cursor), f"• {context}",
                  fill=COLORS["text_primary"], font=fonts["small"], anchor="lt")
        y_cursor += 38

    y_cursor = section2_top + section2_height + 30

    # 보컬 DNA 섹션
    draw.text((padding + 25, y_cursor), "✦ 보컬 DNA",
              fill=COLORS["gold"], font=fonts["subtitle"], anchor="lt")
    y_cursor += 55

    dimension_labels = {
        "intimacy": "친밀감",
        "dynamics": "다이나믹",
        "tone": "음색",
        "leading": "인도력",
        "sustain": "지속력",
        "expression": "표현력"
    }

    bar_width = width - padding * 2 - 180
    bar_height = 16

    for dim_key, score in dimension_scores.items():
        if hasattr(dim_key, 'value'):
            dim_name = dim_key.value
        else:
            dim_name = str(dim_key)

        label = dimension_labels.get(dim_name, dim_name)
        draw_progress_bar(draw, padding + 20, y_cursor, bar_width, bar_height, score, label, fonts)
        y_cursor += 70

    # 하단 워터마크
    footer_y = height - 120

    # 구분선
    draw.line([(padding + 100, footer_y - 30), (width - padding - 100, footer_y - 30)],
              fill=COLORS["border"], width=1)

    draw.text((center_x, footer_y), "worship-vocal.ai",
              fill=COLORS["gold"], font=fonts["small"], anchor="mt")
    draw.text((center_x, footer_y + 40), "당신의 찬양 스타일을 발견하세요",
              fill=COLORS["text_muted"], font=fonts["tiny"], anchor="mt")

    # 최종 출력
    img = img.convert('RGB')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', quality=95, optimize=True)
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """텍스트를 지정된 너비에 맞게 줄바꿈"""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        try:
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(test_line) * 20

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def get_image_download_link(img_bytes: bytes, filename: str = "persona_card.png") -> str:
    """Streamlit 다운로드 링크용 base64 인코딩"""
    b64 = base64.b64encode(img_bytes).decode()
    return f'<a href="data:image/png;base64,{b64}" download="{filename}" class="download-btn">📥 이미지 다운로드</a>'


def create_mini_card_image(
    style_name: str,
    icon: str,
    dimension_scores: Dict[str, float],
    width: int = 600,
    height: int = 600
) -> bytes:
    """
    소셜 미디어 정사각형 미니 카드 (1:1)
    프리미엄 버전
    """
    # 그라디언트 배경
    img = create_gradient_background(width, height, COLORS["background"], (25, 25, 35))
    img = img.convert('RGBA')

    # 글로우 효과
    img = add_glow_effect(img, (width // 2, height // 2), 150, COLORS["purple"])

    draw = ImageDraw.Draw(img)
    fonts = get_fonts(0.85)

    center_x = width // 2

    # 메인 카드 영역
    card_margin = 30
    draw_rounded_rect_with_border(
        draw,
        (card_margin, card_margin, width - card_margin, height - card_margin),
        fill=(*COLORS["card_bg"], 200),
        border=COLORS["border_light"],
        radius=25
    )

    # 브랜드
    draw.text((center_x, 60), "WORSHIP VOCAL AI",
              fill=COLORS["gold"], font=fonts["small"], anchor="mt")

    # 아이콘
    icon_symbol = ICON_FALLBACK.get(icon, "★")
    draw.text((center_x, 130), icon_symbol,
              fill=COLORS["gold_light"], font=fonts["title"], anchor="mt")

    # 스타일 이름
    draw.text((center_x, 230), style_name,
              fill=COLORS["text_primary"], font=fonts["subtitle"], anchor="mt")

    # 레이더 차트
    center_y = 420
    radius = 110
    draw_premium_radar_chart(draw, center_x, center_y, radius, dimension_scores, fonts)

    # 하단
    draw.text((center_x, height - 50), "worship-vocal.ai",
              fill=COLORS["text_muted"], font=fonts["tiny"], anchor="mt")

    # 출력
    img = img.convert('RGB')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', quality=95, optimize=True)
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()


def draw_premium_radar_chart(draw: ImageDraw.Draw, cx: int, cy: int, radius: int,
                              scores: Dict[str, float], fonts: dict):
    """프리미엄 레이더 차트 (라벨 포함)"""
    n = len(scores)
    if n == 0:
        return

    angles = [math.pi / 2 + 2 * math.pi * i / n for i in range(n)]

    dimension_labels = {
        "intimacy": "친밀",
        "dynamics": "다이나믹",
        "tone": "음색",
        "leading": "인도력",
        "sustain": "지속",
        "expression": "표현"
    }

    # 배경 다각형들
    for r_ratio in [1.0, 0.66, 0.33]:
        r = radius * r_ratio
        points = [
            (cx + r * math.cos(a), cy - r * math.sin(a))
            for a in angles
        ]
        draw.polygon(points, outline=COLORS["border"], fill=None, width=1)

    # 축 선
    for a in angles:
        end_x = cx + radius * math.cos(a)
        end_y = cy - radius * math.sin(a)
        draw.line([(cx, cy), (end_x, end_y)], fill=COLORS["border"], width=1)

    # 데이터 다각형
    score_values = list(scores.values())
    data_points = [
        (cx + radius * score_values[i] * math.cos(angles[i]),
         cy - radius * score_values[i] * math.sin(angles[i]))
        for i in range(n)
    ]

    # 반투명 채우기
    draw.polygon(data_points, fill=(*COLORS["purple"][:3], 100), outline=COLORS["purple"], width=2)

    # 데이터 포인트
    for point in data_points:
        draw.ellipse([point[0] - 6, point[1] - 6, point[0] + 6, point[1] + 6],
                    fill=COLORS["gold"], outline=COLORS["gold_light"], width=2)

    # 라벨
    score_keys = list(scores.keys())
    for i, a in enumerate(angles):
        label_r = radius + 30
        label_x = cx + label_r * math.cos(a)
        label_y = cy - label_r * math.sin(a)

        key = score_keys[i]
        if hasattr(key, 'value'):
            key = key.value
        label = dimension_labels.get(str(key), str(key)[:3])

        draw.text((label_x, label_y), label,
                  fill=COLORS["text_secondary"], font=fonts["tiny"], anchor="mm")
