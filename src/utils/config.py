"""配置管理模块"""

from dataclasses import dataclass
from typing import Tuple
from pathlib import Path


@dataclass
class AnimationConfig:
    """动画生成配置"""

    # 尺寸配置
    workspace_size: int = 2048      # 中间处理分辨率（提升以保留更多细节）
    output_size: Tuple[int, int] = (256, 256)  # 输出分辨率（提升以减少降采样损失）

    # 笔画配置
    stroke_width_ratio: float = 0.08  # 笔刷宽度占字号比例（降低使笔画变细）
    stroke_steps: int = 16             # 每笔画分解帧数（提升使动画更平滑）

    # 动画配置
    fps: int = 20                     # 帧率
    loop: int = 0                     # 循环次数 (0=无限)
    duration_ms: int = 80             # 每帧持续时间（毫秒）

    # 墨迹效果配置
    blur_radius: float = 0.5          # 高斯模糊半径（降低以减少模糊）
    binarize_threshold: int = 128     # 二值化阈值

    # 对齐配置
    use_center_of_mass: bool = True   # 是否使用重心对齐
    padding_ratio: float = 0.1        # 内边距比例

    # 路径配置
    makemeahanzi_path: Path = Path(
        "E:/360MoveData/Users/Lenovo/Desktop/handwrite/makemeahanzi"
    )
    font_path: Path = Path(
        "E:/360MoveData/Users/Lenovo/Desktop/handwrite/hanzi-animator/data/fonts/龚帆手写笔记体.ttf"
    )
    output_path: Path = Path("output")


# 全局配置实例
config = AnimationConfig()
