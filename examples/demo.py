"""汉字书写动画生成器演示脚本

使用示例:
    python examples/demo.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import HandwriteGenerator, AnimationConfig


def main():
    """演示如何生成汉字书写动画"""

    # 1. 使用默认配置
    print("=" * 50)
    print("汉字书写动画生成器 - 演示")
    print("=" * 50)

    # 可选：自定义配置
    config = AnimationConfig(
        workspace_size=1024,       # 中间处理分辨率
        output_size=(64, 64),      # 输出分辨率
        stroke_width_ratio=0.18,   # 笔刷宽度
        stroke_steps=15,           # 每笔画帧数
        fps=20,                    # 帧率
        blur_radius=1.5,           # 模糊半径
    )

    # 2. 初始化生成器
    generator = HandwriteGenerator(cfg=config)

    # 3. 生成单个汉字
    print("\n--- 生成单个汉字 ---")
    test_chars = ["一", "二", "三", "永", "中"]

    for char in test_chars:
        try:
            output_path = generator.generate(char)
            print(f"  成功: {char} -> {output_path}")
        except ValueError as e:
            print(f"  跳过: {char} - {e}")

    # 4. 批量生成
    print("\n--- 批量生成 ---")
    batch_chars = "天地玄黄宇宙洪荒"
    generator.generate_batch(batch_chars)

    print("\n" + "=" * 50)
    print("演示完成！请查看 output 目录中的 GIF 文件")
    print("=" * 50)


if __name__ == "__main__":
    main()
