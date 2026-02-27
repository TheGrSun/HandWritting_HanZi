"""TTF 字体管理器"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import platform


class FontManager:
    """TTF 字体管理器

    负责加载 TrueType 字体文件并渲染字符到画布上。
    当主字体不包含某个字符时，自动使用系统字体作为后备。
    """

    # 系统后备字体配置（根据操作系统）
    FALLBACK_FONTS = {
        'Windows': ['msyh.ttc', 'simsun.ttc', 'simhei.ttf'],
        'Darwin': ['PingFang.ttc', 'STHeiti.ttc', 'Arial Unicode.ttf'],
        'Linux': ['wqy-zenhei.ttc', 'noto.ttf', 'DejaVuSans.ttf']
    }

    def __init__(self, font_path: Path = None):
        self.font_path = font_path or Path("data/fonts/default.ttf")
        self._font_cache = {}
        self._fallback_font = None
        self._using_fallback = set()  # 记录使用后备字体的字符

        # 验证字体文件存在
        if not self.font_path.exists():
            raise FileNotFoundError(f"Font file not found: {self.font_path}")

    def _get_fallback_font(self, size: int) -> Optional[ImageFont.FreeTypeFont]:
        """获取系统后备字体"""
        if self._fallback_font is not None:
            return self._fallback_font

        system = platform.system()
        font_names = self.FALLBACK_FONTS.get(system, self.FALLBACK_FONTS['Linux'])

        # 尝试加载系统字体
        for font_name in font_names:
            try:
                self._fallback_font = ImageFont.truetype(font_name, size)
                return self._fallback_font
            except OSError:
                continue

        # 如果系统字体都失败，使用默认字体
        try:
            self._fallback_font = ImageFont.load_default()
            return self._fallback_font
        except Exception:
            return None

    def get_font(self, size: int, use_fallback: bool = False) -> ImageFont.FreeTypeFont:
        """获取指定大小的字体对象

        Args:
            size: 字体大小
            use_fallback: 是否使用后备字体
        """
        if use_fallback:
            fallback = self._get_fallback_font(size)
            if fallback:
                return fallback

        if size not in self._font_cache:
            self._font_cache[size] = ImageFont.truetype(
                str(self.font_path),
                size=size
            )
        return self._font_cache[size]

    def _has_character(self, font: ImageFont.FreeTypeFont, char: str) -> bool:
        """检查字体是否包含指定字符

        通过检查字符边界框来判断。如果字体不包含该字符，
        getbbox 会返回高度或宽度为 0 的边界框。
        """
        try:
            left, top, right, bottom = font.getbbox(char)
            width = right - left
            height = bottom - top
            # 如果高度或宽度为 0 或负数，字符不存在于字体中
            return width > 0 and height > 0
        except Exception:
            return False

    def render_character(self,
                        char: str,
                        size: int = 900,
                        canvas_size: int = 1024) -> Image.Image:
        """渲染单个字符到画布中心

        当主字体不包含该字符时，自动使用系统字体作为后备。

        Args:
            char: 要渲染的字符
            size: 字体大小（默认 900 以匹配 makemeahanzi 坐标系）
            canvas_size: 画布大小（默认 1024）

        Returns:
            L 模式的灰度图像，白色为笔画，黑色为背景
        """
        # 创建白色画布（255表示白色）
        img = Image.new('L', (canvas_size, canvas_size), 255)
        draw = ImageDraw.Draw(img)

        # 获取主字体
        font = self.get_font(size)

        # 检查主字体是否包含该字符
        if not self._has_character(font, char):
            # 尝试使用后备字体
            fallback_font = self._get_fallback_font(size)
            if fallback_font and self._has_character(fallback_font, char):
                font = fallback_font
                self._using_fallback.add(char)
                print(f"  [注意] 字符 '{char}' 不在手写字体中，使用系统字体")
            else:
                print(f"  [警告] 字符 '{char}' 在所有字体中均不可用")

        # 使用 anchor='mm' 自动居中（mm = middle-middle）
        # 这会自动处理不同字符的基线差异，无需手动计算 getbbox()
        draw.text((canvas_size / 2, canvas_size / 2), char, font=font, fill=0, anchor='mm')

        return img

    def get_fallback_characters(self) -> set:
        """获取使用后备字体的字符集合"""
        return self._using_fallback.copy()
