"""SVG 动画编码器"""

from typing import List
from pathlib import Path
import numpy as np

from ..utils.config import AnimationConfig


class SVGEncoder:
    """SVG 动画编码器

    将动画帧序列编码为 SVG 格式。
    使用位图嵌入方式，确保兼容性。
    """

    def __init__(self, cfg: AnimationConfig = None):
        self.cfg = cfg or AnimationConfig()

    def encode(self,
              frames: List[np.ndarray],
              output_path: Path,
              duration_ms: int = None) -> None:
        """编码帧序列为 SVG 动画

        Args:
            frames: numpy 图像数组列表
            output_path: 输出文件路径
            duration_ms: 每帧持续时间（毫秒）
        """
        if not frames:
            raise ValueError("No frames to encode")

        duration = duration_ms or self.cfg.duration_ms

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 获取帧尺寸
        height, width = frames[0].shape[:2]

        # 将所有帧转换为 base64 PNG
        import base64
        from io import BytesIO
        from PIL import Image

        frame_data = []
        for frame in frames:
            img = Image.fromarray(frame, mode='L')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            b64_data = base64.b64encode(buffer.getvalue()).decode('ascii')
            frame_data.append(b64_data)

        # 生成 SVG 内容
        svg_content = self._generate_svg_animated(
            frame_data, width, height, duration
        )

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

    def _generate_svg_animated(self,
                               frame_data: List[str],
                               width: int,
                               height: int,
                               duration_ms: int) -> str:
        """生成带 SMIL 动画的 SVG

        使用 <animate> 标签实现帧切换
        """
        duration_sec = duration_ms / 1000.0

        svg_header = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {width} {height}" width="{width}" height="{height}">
'''
        svg_footer = '</svg>'

        # 使用 CSS 动画方式（更兼容）
        total_duration = len(frame_data) * duration_sec
        keyframes = self._generate_keyframes(frame_data)

        svg_content = f'''{svg_header}
  <style>
    @keyframes hanzi-animation {{
      {keyframes}
    }}
    .hanzi-frame {{
      animation: hanzi-animation {total_duration:.2f}s steps(1) infinite;
    }}
  </style>
  <image class="hanji-frame" width="{width}" height="{height}" />
'''
        # 修正：使用 SMIL 动画
        svg_content = f'''{svg_header}
  <image width="{width}" height="{height}">
'''

        # 添加 SMIL 动画
        current_time = 0
        for i, data in enumerate(frame_data):
            begin = f"{current_time:.2f}s"
            current_time += duration_sec
            svg_content += f'''    <animate attributeName="xlink:href"
             to="data:image/png;base64,{data}"
             begin="{begin}"
             dur="{duration_sec:.2f}s"
             fill="freeze"
             id="frame{i}"/>
'''

        # 第一帧立即显示
        svg_content = f'''{svg_header}
  <image width="{width}" height="{height}" xlink:href="data:image/png;base64,{frame_data[0]}">
'''

        for i, data in enumerate(frame_data[1:], 1):
            begin = f"{(i-1) * duration_sec:.2f}s"
            svg_content += f'''    <animate attributeName="xlink:href"
             to="data:image/png;base64,{data}"
             begin="{begin}"
             dur="{duration_sec:.2f}s"
             fill="freeze"/>
'''

        svg_content += '  </image>\n' + svg_footer

        return svg_content

    def _generate_keyframes(self, frame_data: List[str]) -> str:
        """生成 CSS keyframes（备用方案）"""
        frames_css = []
        for i, data in enumerate(frame_data):
            percent = (i / len(frame_data)) * 100
            frames_css.append(f"      {percent:.1f}% {{ background-image: url('data:image/png;base64,{data}'); }}")
        return '\n'.join(frames_css)
