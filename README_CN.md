# 汉字动画生成器

生成逼真的汉字书写动画，支持笔画顺序渲染。

[English](./README.md)

## 效果展示

| 一 | 永 | 中 | 爱 | 把 |
|:---:|:---:|:---:|:---:|:---:|
| ![一](./output/一.vector.svg) | ![永](./output/永.vector.svg) | ![中](./output/中.vector.svg) | ![爱](./output/爱.vector.svg) | ![把](./output/把.vector.svg) |

> 在浏览器中打开SVG文件查看动画效果。

## 特性

- **矢量SVG动画** - 无限缩放，文件极小（每字8-40KB）
- **真实笔画顺序** - 基于makemeahanzi官方笔画数据
- **流畅动画** - CSS笔画绘制效果，timing合理
- **可自定义** - 支持自定义TTF字体和动画参数
- **9000+汉字** - 覆盖绝大多数常用汉字

## 已知问题

由于**骨架笔画数据与TTF字体的对齐程度不高**，动画可能存在以下问题：

- **位置偏移**：笔画蒙版可能无法完美对齐字体字形
- **覆盖缺失**：字体的某些部分可能无法被笔画蒙版完全揭示
- **视觉瑕疵**：复杂字符中出现重叠或缺失区域

**根本原因**：makemeahanzi骨架使用固定的1024x1024坐标系，而TTF字体根据每个字符的形状有可变的边界框。当前实现使用字体自身的边界框进行居中，这与骨架期望的定位不匹配。

**可能的解决方案**（欢迎贡献）：
- 使用与makemeahanzi骨架风格匹配的TTF字体
- 实现动态坐标变换
- 直接从TTF字体生成骨架数据

## 安装

```bash
pip install -r requirements.txt
```

依赖：
- Python 3.10+
- Pillow
- numpy

## 快速开始

```python
from src import HandwriteGenerator

# 初始化生成器
generator = HandwriteGenerator()

# 生成矢量SVG动画
generator.generate_vector("永")

# 批量生成
for char in "中国人":
    generator.generate_vector(char)
```

输出文件保存在 `output/` 目录。

## 动画模式

### 矢量SVG（推荐）

```python
generator.generate_vector("永")
```

- 文件格式：SVG
- 文件大小：8-40 KB/字
- 可缩放：是
- 动画原理：CSS stroke-dashoffset

### GIF动画

```python
generator.generate("永")
```

- 文件格式：GIF
- 文件大小：50-200 KB/字
- 可缩放：否（位图）
- 动画原理：帧动画

## 配置

```python
from src import HandwriteGenerator, AnimationConfig

config = AnimationConfig(
    workspace_size=1024,       # 处理分辨率
    output_size=(64, 64),      # 输出分辨率（仅GIF）
    fps=20,                    # 帧率（仅GIF）
)

generator = HandwriteGenerator(cfg=config)
```

## 项目结构

```
hanzi-animator/
├── src/
│   ├── data/
│   │   ├── graphics_loader.py    # 笔画数据加载器
│   │   └── font_manager.py       # TTF字体管理器
│   ├── animation/
│   │   ├── vector_svg_encoder.py # 矢量SVG编码器
│   │   ├── svg_encoder.py        # SVG编码器
│   │   └── gif_encoder.py        # GIF编码器
│   ├── utils/
│   │   └── config.py             # 配置管理
│   └── generator.py              # 主入口
├── data/
│   ├── makemeahanzi/             # 笔画数据（graphics.txt）
│   └── fonts/                    # TTF字体
├── output/                       # 生成的动画
├── examples/
│   └── demo.py                   # 使用示例
├── pyproject.toml
├── requirements.txt
├── README.md
└── README_CN.md
```

## 数据来源

- **笔画数据**：[makemeahanzi](https://github.com/skishore/makemeahanzi) - 9000+汉字SVG笔画路径
- **字体**：自定义TTF手写字体（放置在 `data/fonts/`）

## API参考

### HandwriteGenerator

| 方法 | 说明 |
|------|------|
| `generate_vector(char)` | 生成矢量SVG动画 |
| `generate(char)` | 生成GIF动画 |
| `generate_batch(chars)` | 批量生成多个汉字 |
| `has_character(char)` | 检查是否支持某汉字 |

### AnimationConfig

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `workspace_size` | 1024 | 处理分辨率 |
| `output_size` | (64, 64) | 输出分辨率 |
| `fps` | 20 | 帧率 |
| `font_path` | 自动 | TTF字体路径 |

## 技术原理

### 矢量SVG动画

使用CSS `stroke-dashoffset` 创建"绘制"效果：

1. **蒙版层**：makemeahanzi笔画数据的SVG路径
2. **内容层**：TTF字体渲染为base64 PNG
3. **动画**：CSS关键帧动画，`stroke-dashoffset`从全长变为0

动画时序：
- 绘制阶段：约30%循环时间
- 停留阶段：约45%循环时间
- 重置阶段：约25%循环时间

## 参与贡献

欢迎贡献代码！以下领域需要改进：

1. **坐标对齐** - 更好地匹配骨架和TTF字体
2. **字体兼容性** - 支持与makemeahanzi风格匹配的字体
3. **动画平滑** - 更自然的笔画绘制效果
4. **性能优化** - 批量生成优化

## 许可证

MIT License - 详见[LICENSE](./LICENSE)文件。

## 致谢

- [makemeahanzi](https://github.com/skishore/makemeahanzi) 提供笔画数据
- 所有贡献者和用户
