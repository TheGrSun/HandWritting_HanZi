"""蒙版法核心算法实现"""

from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ..data.svg_parser import SVGPathParser, Point
from ..utils.config import AnimationConfig


class MaskAlgorithm:
    """蒙版法核心算法实现

    直接使用笔画数据生成动画，不依赖字体蒙版。
    """

    def __init__(self, cfg: AnimationConfig = None):
        self.cfg = cfg or AnimationConfig()
        self.parser = SVGPathParser()

    def generate_frames(self,
                       character: str,
                       stroke_paths: List[str],
                       font_render: Image.Image = None) -> List[np.ndarray]:
        """生成完整动画帧序列

        Args:
            character: 目标汉字
            stroke_paths: 笔画 SVG 路径列表（来自 graphics.txt）
            font_render: 忽略，直接使用笔画数据

        Returns:
            高分辨率动画帧列表（numpy 数组）
        """
        frames = []
        workspace_size = self.cfg.workspace_size

        # 预解析所有笔画路径
        all_stroke_points = []
        for path_data in stroke_paths:
            commands = self.parser.parse(path_data)
            points = self.parser.commands_to_points(commands)
            all_stroke_points.append(points)

        # 如果有字体渲染，用于调整笔画位置
        offset_x, offset_y = 0, 0
        if font_render is not None:
            # 计算字体的重心
            font_array = np.array(font_render, dtype=np.uint8)
            non_zero = np.argwhere(font_array > 0)
            if len(non_zero) > 0:
                font_center_x = non_zero[:, 1].mean()
                font_center_y = non_zero[:, 0].mean()

                # 计算笔画数据的重心
                all_points = []
                for points in all_stroke_points:
                    all_points.extend(points)
                if all_points:
                    stroke_center_x = np.mean([p.x for p in all_points])
                    stroke_center_y = np.mean([p.y for p in all_points])

                    # 计算偏移
                    offset_x = font_center_x - stroke_center_x
                    offset_y = font_center_y - stroke_center_y

        # 生成累积动画帧
        accumulated_skeleton = np.zeros((workspace_size, workspace_size), dtype=np.uint8)

        for stroke_idx, stroke_points in enumerate(all_stroke_points):
            if len(stroke_points) < 2:
                continue

            # 应用偏移（如果有）
            if offset_x != 0 or offset_y != 0:
                adjusted_points = [Point(p.x + offset_x, p.y + offset_y) for p in stroke_points]
            else:
                adjusted_points = stroke_points

            # 分割当前笔画
            segments = self.parser.split_path_by_length(adjusted_points, self.cfg.stroke_steps)

            # 为当前笔画生成渐进帧
            for segment_idx, segment in enumerate(segments):
                if not segment or len(segment) < 2:
                    continue

                # 绘制当前笔画到当前进度
                current_stroke_skeleton = self._draw_skeleton(segment)

                # 累积：已完成笔画 + 当前笔画进度
                combined_skeleton = np.maximum(accumulated_skeleton, current_stroke_skeleton)

                frames.append(combined_skeleton.copy())

            # 当前笔画完成，更新累积骨架
            complete_stroke = self._draw_skeleton(adjusted_points)
            accumulated_skeleton = np.maximum(accumulated_skeleton, complete_stroke)

            # 笔画完成后添加一帧保留状态
            frames.append(accumulated_skeleton.copy())

        # 最终帧保留更长时间
        if frames:
            final_frame = frames[-1]
            hold_frames = 10
            for _ in range(hold_frames):
                frames.append(final_frame.copy())

        return frames

    def _draw_skeleton(self, points: List[Point]) -> np.ndarray:
        """绘制骨架 - 带超采样抗锯齿"""
        size = self.cfg.workspace_size

        if len(points) < 2:
            return np.zeros((size, size), dtype=np.uint8)

        # 超采样抗锯齿：使用 2 倍分辨率绘制后降采样
        super_sample_size = size * 2
        stroke_width = int(900 * self.cfg.stroke_width_ratio * 2)

        # 在 2 倍分辨率画布上绘制
        img = Image.new('L', (super_sample_size, super_sample_size), 0)
        draw = ImageDraw.Draw(img)

        # 使用浮点坐标并映射到超采样空间（保留精度）
        coords = [(max(0, min(p.x * 2, super_sample_size - 1)),
                   max(0, min(p.y * 2, super_sample_size - 1))) for p in points]

        # 绘制平滑线条
        if len(coords) >= 2:
            draw.line(coords, fill=255, width=stroke_width)

            # 端点圆滑处理
            x, y = coords[0]
            draw.ellipse(
                [x - stroke_width // 2, y - stroke_width // 2,
                 x + stroke_width // 2, y + stroke_width // 2],
                fill=255
            )
            x, y = coords[-1]
            draw.ellipse(
                [x - stroke_width // 2, y - stroke_width // 2,
                 x + stroke_width // 2, y + stroke_width // 2],
                fill=255
            )

        # 降采样回原始尺寸（LANCZOS 抗锯齿效果）
        resized = img.resize((size, size), Image.Resampling.LANCZOS)

        # 应用轻微模糊处理，进一步柔化边缘
        final = resized.filter(ImageFilter.GaussianBlur(radius=0.5))

        return np.array(final, dtype=np.uint8)

    def downsample(self,
                   image: Image.Image,
                   output_size: Tuple[int, int] = None) -> Image.Image:
        """降采样到输出尺寸"""
        size = output_size or self.cfg.output_size
        return image.resize(size, Image.Resampling.LANCZOS)
