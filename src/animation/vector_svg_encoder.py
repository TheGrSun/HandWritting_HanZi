"""矢量 SVG 动画编码器 - 笔画渐进绘制法

原理：
1. 使用 stroke-dashoffset 动画让笔画沿路径"生长"
2. 蒙版中的笔画按顺序逐步绘制，逐步揭示 TTF 字体
3. 每个笔画有独立的动画延迟，形成连续书写效果

效果：白底黑字，笔画按顺序渐进绘制，TTF 字体跟随笔画逐渐显示
"""

from typing import List, Optional
from pathlib import Path
import base64
from io import BytesIO
import math

from ..utils.config import AnimationConfig
from ..data.font_manager import FontManager


class VectorSVGEncoder:
    """矢量 SVG 动画编码器（笔画渐进绘制法）

    使用 CSS stroke-dashoffset 动画实现真实的笔画书写效果。
    """

    def __init__(self, cfg: AnimationConfig = None, font_manager: FontManager = None):
        self.cfg = cfg or AnimationConfig()
        self.font_manager = font_manager

    def encode(self,
              stroke_paths: List[str],
              output_path: Path,
              character: str,
              duration_per_stroke: float = 0.6,
              stroke_width: float = 48) -> None:
        """编码笔画路径为矢量 SVG 动画

        Args:
            stroke_paths: 笔画 SVG 路径列表（来自 graphics.txt）
            output_path: 输出文件路径
            character: 要显示的汉字
            duration_per_stroke: 每个笔画的动画持续时间（秒）
            stroke_width: 蒙版中笔画的宽度
        """
        if not stroke_paths:
            raise ValueError("No stroke paths to encode")

        if not self.font_manager:
            raise ValueError("FontManager is required")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 渲染 TTF 字体字形为 base64 图片
        font_glyph_base64 = self._render_font_glyph(character)

        # 2. 生成 SVG 内容
        svg_content = self._generate_progressive_svg(
            stroke_paths,
            font_glyph_base64,
            duration_per_stroke,
            stroke_width
        )

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

    def _render_font_glyph(self, character: str) -> str:
        """渲染 TTF 字体字形为 base64 图片

        Returns:
            base64 编码的 PNG 图片 URL
        """
        from PIL import Image

        canvas_size = 1024
        font_render = self.font_manager.render_character(
            character,
            size=900,
            canvas_size=canvas_size
        )

        buffer = BytesIO()
        font_render.save(buffer, format='PNG')
        buffer.seek(0)
        base64_data = base64.b64encode(buffer.read()).decode('ascii')
        return f'data:image/png;base64,{base64_data}'

    def _estimate_path_length(self, path_data: str) -> float:
        """估算 SVG 路径长度

        使用更精确的算法解析路径命令并计算长度
        """
        import re

        # 解析路径数据，提取所有数字
        numbers = re.findall(r'-?\d+\.?\d*', path_data)
        numbers = [float(n) for n in numbers]

        if len(numbers) < 4:
            return 300  # 默认值

        # 解析路径命令
        commands = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]', path_data)

        total_length = 0
        current_x, current_y = 0, 0
        start_x, start_y = 0, 0
        num_idx = 0

        for cmd in commands:
            if cmd == 'M' and num_idx + 1 < len(numbers):
                current_x, current_y = numbers[num_idx], numbers[num_idx + 1]
                start_x, start_y = current_x, current_y
                num_idx += 2
            elif cmd == 'L' and num_idx + 1 < len(numbers):
                new_x, new_y = numbers[num_idx], numbers[num_idx + 1]
                total_length += math.sqrt((new_x - current_x)**2 + (new_y - current_y)**2)
                current_x, current_y = new_x, new_y
                num_idx += 2
            elif cmd == 'Q' and num_idx + 3 < len(numbers):
                # 二次贝塞尔曲线：近似为控制点到端点的距离
                cx, cy = numbers[num_idx], numbers[num_idx + 1]
                new_x, new_y = numbers[num_idx + 2], numbers[num_idx + 3]
                # 使用弧长近似公式
                chord = math.sqrt((new_x - current_x)**2 + (new_y - current_y)**2)
                control_dist = (math.sqrt((cx - current_x)**2 + (cy - current_y)**2) +
                               math.sqrt((new_x - cx)**2 + (new_y - cy)**2))
                total_length += (chord + control_dist) / 2
                current_x, current_y = new_x, new_y
                num_idx += 4
            elif cmd == 'C' and num_idx + 5 < len(numbers):
                # 三次贝塞尔曲线
                c1x, c1y = numbers[num_idx], numbers[num_idx + 1]
                c2x, c2y = numbers[num_idx + 2], numbers[num_idx + 3]
                new_x, new_y = numbers[num_idx + 4], numbers[num_idx + 5]
                chord = math.sqrt((new_x - current_x)**2 + (new_y - current_y)**2)
                control_dist = (math.sqrt((c1x - current_x)**2 + (c1y - current_y)**2) +
                               math.sqrt((c2x - c1x)**2 + (c2y - c1y)**2) +
                               math.sqrt((new_x - c2x)**2 + (new_y - c2y)**2))
                total_length += (chord + control_dist) / 2
                current_x, current_y = new_x, new_y
                num_idx += 6
            elif cmd == 'Z':
                total_length += math.sqrt((start_x - current_x)**2 + (start_y - current_y)**2)
                current_x, current_y = start_x, start_y

        # 确保返回合理的长度值，增加20%余量确保完全绘制
        return max(300, total_length * 1.2)

    def _generate_progressive_svg(self,
                                   stroke_paths: List[str],
                                   font_glyph_base64: str,
                                   duration_per_stroke: float,
                                   stroke_width: float) -> str:
        """生成渐进绘制 SVG 动画

        原理：
        - 使用单个 mask，包含所有笔画路径
        - 每个笔画使用 stroke-dashoffset 动画实现"绘制"效果
        - 笔画按顺序延迟启动，形成连续书写
        - TTF 字体作为被遮罩的内容，随笔画绘制逐渐显示

        SVG 结构：
        1. 背景：白色
        2. mask：包含所有笔画，每个笔画有渐进动画
        3. 字体图像：应用 mask，随笔画绘制逐渐显示
        """
        num_strokes = len(stroke_paths)
        total_duration = num_strokes * duration_per_stroke

        # mask 笔画宽度（需要足够宽以覆盖整个笔画）
        mask_stroke_width = stroke_width * 3

        # SVG 头部
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="256" height="256">
  <defs>
    <!-- 动态蒙版：笔画按顺序渐进绘制 -->
    <mask id="write-mask">
      <rect width="1024" height="1024" fill="black"/>
      <g transform="translate(62, 962) scale(1, -1)">
'''

        # 为每个笔画添加渐进绘制动画（直接内联路径）
        for i, path_data in enumerate(stroke_paths):
            path_length = self._estimate_path_length(path_data)
            delay = i * duration_per_stroke

            # stroke-dasharray 实现渐进绘制效果
            # 动画：从完全隐藏（offset=length）到完全显示（offset=0）
            svg += f'''        <path d="{path_data}"
             class="mask-stroke"
             stroke="white"
             stroke-width="{mask_stroke_width}"
             stroke-linecap="round"
             stroke-linejoin="round"
             fill="none"
             style="--length: {path_length}; --delay: {delay:.3f}s; --duration: {duration_per_stroke:.3f}s;"/>
'''

        svg += '''      </g>
    </mask>
'''

        # CSS 动画定义 - 使用百分比关键帧实现真正的循环
        # 时间分配：绘制40% + 停留50% + 重置10%
        hold_duration = total_duration * 1.5  # 停留时间为绘制时间的1.5倍
        full_loop = total_duration + hold_duration + 0.5  # 总循环时间

        draw_end = (total_duration / full_loop) * 100  # 绘制结束点
        hold_end = ((total_duration + hold_duration) / full_loop) * 100  # 停留结束点

        svg += f'''
    <style>
      .mask-stroke {{
        stroke-dasharray: var(--length);
        stroke-dashoffset: var(--length);
        animation: draw-stroke {full_loop:.2f}s ease-out infinite;
        animation-delay: var(--delay);
      }}

      @keyframes draw-stroke {{
        0% {{
          stroke-dashoffset: var(--length);
        }}
        {draw_end:.1f}% {{
          stroke-dashoffset: 0;
        }}
        {hold_end:.1f}% {{
          stroke-dashoffset: 0;
        }}
        {hold_end + 3:.1f}%, 100% {{
          stroke-dashoffset: var(--length);
        }}
      }}
    </style>
  </defs>

  <!-- 白色背景 -->
  <rect width="1024" height="1024" fill="white"/>

  <!-- TTF 字体图像，通过蒙版渐进显示 -->
  <image x="0" y="0" width="1024" height="1024"
         href="{font_glyph_base64}" mask="url(#write-mask)"/>

</svg>'''

        return svg
