"""汉字书写动画生成器主类"""

from pathlib import Path
from typing import Optional, List
import numpy as np
from PIL import Image

from .data.graphics_loader import GraphicsLoader
from .data.font_manager import FontManager
from .core.mask_algorithm import MaskAlgorithm
from .animation.svg_encoder import SVGEncoder
from .animation.vector_svg_encoder import VectorSVGEncoder
from .utils.config import AnimationConfig


class HandwriteGenerator:
    """汉字书写动画生成器主类

    使用示例:
        generator = HandwriteGenerator()
        output_path = generator.generate("永")
        print(f"动画已保存至: {output_path}")
    """

    def __init__(self, cfg: AnimationConfig = None):
        """
        Args:
            cfg: 动画配置，如果不提供则使用默认配置
        """
        self.cfg = cfg or AnimationConfig()

        # 初始化组件
        self.graphics_loader = GraphicsLoader(self.cfg.makemeahanzi_path)
        self.font_manager = FontManager(self.cfg.font_path)
        self.algorithm = MaskAlgorithm(self.cfg)
        self.encoder = SVGEncoder(self.cfg)
        self.vector_encoder = VectorSVGEncoder(self.cfg, self.font_manager)

        # 预加载数据
        self.graphics_loader.load()

    def generate(self,
                character: str,
                output_path: Optional[Path] = None) -> Path:
        """生成汉字书写动画 SVG

        Args:
            character: 要生成动画的汉字
            output_path: 输出文件路径（默认为 output/<char>.svg）

        Returns:
            生成的 SVG 文件路径
        """
        # 1. 获取字符数据
        char_data = self.graphics_loader.get_character(character)
        if char_data is None:
            raise ValueError(
                f"字符 '{character}' 不在 graphics.txt 数据源中。"
                f"数据源包含 {self.graphics_loader.get_character_count()} 个字符。"
            )

        print(f"正在生成字符 '{character}' 的动画...")
        print(f"  - 笔画数: {len(char_data.strokes)}")

        # 2. 渲染 TTF 字体
        print(f"  - 渲染字体蒙版...")
        font_render = self.font_manager.render_character(
            character,
            size=900,
            canvas_size=self.cfg.workspace_size
        )

        # 3. 生成高分辨率动画帧（numpy 数组）
        print(f"  - 生成动画帧 (1024x1024)...")
        frames = self.algorithm.generate_frames(
            character,
            char_data.strokes,
            font_render
        )
        print(f"  - 总帧数: {len(frames)}")

        # 4. 降采样到输出尺寸
        print(f"  - 降采样到 {self.cfg.output_size}...")
        from PIL import Image
        output_frames = []
        for frame in frames:
            # frame 是 PIL Image 或 numpy 数组
            if isinstance(frame, Image.Image):
                resized = frame.resize(self.cfg.output_size, Image.Resampling.LANCZOS)
            else:
                img = Image.fromarray(frame, mode='L')
                resized = img.resize(self.cfg.output_size, Image.Resampling.LANCZOS)
            output_frames.append(np.array(resized))

        # 5. 编码 SVG
        output_path = output_path or self.cfg.output_path / f"{character}.svg"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  - 编码 SVG...")
        self.encoder.encode(output_frames, output_path)

        print(f"[OK] 动画已保存至: {output_path}")
        return output_path

    def generate_batch(self,
                      characters: str,
                      output_dir: Optional[Path] = None) -> List[Path]:
        """批量生成多个汉字的动画

        Args:
            characters: 要生成的汉字字符串
            output_dir: 输出目录（默认为配置中的 output_path）

        Returns:
            成功生成的文件路径列表
        """
        output_dir = output_dir or self.cfg.output_path
        results = []
        failed = []

        for char in characters:
            try:
                path = self.generate(char, output_dir / f"{char}.svg")
                results.append(path)
            except ValueError as e:
                print(f"[X] 跳过字符 '{char}': {e}")
                failed.append((char, str(e)))

        # 输出摘要
        print(f"\n批量生成完成:")
        print(f"  - 成功: {len(results)} 个")
        print(f"  - 失败: {len(failed)} 个")

        if failed:
            print(f"\n失败的字符:")
            for char, reason in failed:
                print(f"    - '{char}': {reason}")

        return results

    def get_available_characters(self) -> List[str]:
        """获取所有可用的字符列表"""
        return self.graphics_loader.get_all_characters()

    def has_character(self, char: str) -> bool:
        """检查是否包含某字符"""
        return self.graphics_loader.has_character(char)

    def generate_vector(self,
                        character: str,
                        output_path: Optional[Path] = None,
                        duration_per_stroke: float = 0.3) -> Path:
        """生成矢量 SVG 动画（直接使用笔画路径）

        Args:
            character: 要生成动画的汉字
            output_path: 输出文件路径（默认为 output/<char>.vector.svg）
            duration_per_stroke: 每个笔画的动画持续时间（秒）

        Returns:
            生成的矢量 SVG 文件路径

        矢量 SVG 优势:
        - 文件大小仅为位图的 1/10 - 1/100
        - 无损缩放
        - 完美抗锯齿
        - 浏览器原生渲染
        """
        # 1. 获取字符数据
        char_data = self.graphics_loader.get_character(character)
        if char_data is None:
            raise ValueError(
                f"字符 '{character}' 不在 graphics.txt 数据源中。"
                f"数据源包含 {self.graphics_loader.get_character_count()} 个字符。"
            )

        print(f"正在生成字符 '{character}' 的矢量 SVG 动画...")
        print(f"  - 笔画数: {len(char_data.strokes)}")

        # 2. 使用矢量编码器直接生成 SVG
        output_path = output_path or self.cfg.output_path / f"{character}.vector.svg"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.vector_encoder.encode(
            char_data.strokes,
            output_path,
            character=character,
            duration_per_stroke=duration_per_stroke,
            stroke_width=48  # 矢量模式下的笔画宽度（蒙版实际宽度为此值的3倍）
        )

        # 检查文件大小
        file_size = output_path.stat().st_size
        print(f"  - 文件大小: {file_size / 1024:.1f} KB")
        print(f"[OK] 矢量 SVG 已保存至: {output_path}")

        return output_path
