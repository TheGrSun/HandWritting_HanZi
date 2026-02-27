"""GIF 动画编码器"""

from typing import List
from pathlib import Path
from PIL import Image
import numpy as np

from ..utils.config import AnimationConfig


class GIFEncoder:
    """GIF 动画编码器

    负责将图像帧序列编码为 GIF 动画文件。
    """

    def __init__(self, cfg: AnimationConfig = None):
        self.cfg = cfg or AnimationConfig()

    def encode(self,
              frames: List[Image.Image],
              output_path: Path,
              duration_ms: int = None,
              loop: int = None) -> None:
        """编码帧序列为 GIF

        Args:
            frames: 图像帧列表
            output_path: 输出文件路径
            duration_ms: 每帧持续时间（毫秒）
            loop: 循环次数（0=无限）
        """
        if not frames:
            raise ValueError("No frames to encode")

        duration = duration_ms or self.cfg.duration_ms
        loop_count = loop if loop is not None else self.cfg.loop

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存第一帧并附加后续帧
        first_frame = frames[0]
        first_frame.save(
            str(output_path),
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop_count,
            optimize=True,
            disposal=2  # 每帧显示后清除画布
        )

    def encode_from_numpy(self,
                         frames: List[np.ndarray],
                         output_path: Path,
                         duration_ms: int = None,
                         loop: int = None) -> None:
        """从 numpy 数组编码 GIF

        Args:
            frames: numpy 图像数组列表
            output_path: 输出文件路径
            duration_ms: 每帧持续时间（毫秒）
            loop: 循环次数（0=无限）
        """
        # 转换为 PIL Images
        pil_frames = [Image.fromarray(frame, mode='L') for frame in frames]
        self.encode(pil_frames, output_path, duration_ms, loop)
