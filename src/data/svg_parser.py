"""SVG 路径解析器"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Point:
    x: float
    y: float


@dataclass
class PathCommand:
    type: str  # M, L, Q, C, Z
    params: List[float]


class SVGPathParser:
    """SVG 路径解析器

    makemeahanzi 坐标系特点:
    - viewBox: 0 0 1024 1024
    - 使用 transform="scale(1, -1) translate(0, -900)" 进行坐标系转换
    - Y 轴向下递减（与常规 SVG 相反）
    """

    # makemeahanzi 坐标系转换参数
    Y_OFFSET = 900
    SCALE_Y = -1

    @staticmethod
    def parse(path_data: str) -> List[PathCommand]:
        """解析 SVG 路径字符串为命令列表

        示例输入: "M 100 100 Q 150 150 200 100 L 300 100"
        """
        path_data = path_data.strip()

        # 正则匹配路径命令和参数
        # 匹配模式: 命令字母 + 后续非命令字符
        tokens = re.findall(r'([MLQCTZHVAmllqctzhv])([^MLQCTZHVAmllqctzhv]*)', path_data)

        commands = []
        for cmd_type, params_str in tokens:
            params = []
            for x in params_str.strip().split():
                if x:
                    try:
                        params.append(float(x))
                    except ValueError:
                        pass  # 忽略无效数字
            commands.append(PathCommand(cmd_type, params))

        return commands

    @staticmethod
    def transform_point(x: float, y: float) -> Point:
        """应用 makemeahanzi 坐标系变换

        makemeahanzi 使用 transform="scale(1, -1) translate(0, -900)"
        SVG 变换从右向左应用：先 translate(0, -900)，再 scale(1, -1)

        转换公式:
        x_new = x
        y_new = -(y - 900) = 900 - y

        这与 makemeahanzi 的 SVG 结构一致
        """
        return Point(
            x=x,
            y=900 - y
        )

    @staticmethod
    def commands_to_points(commands: List[PathCommand],
                          resolution: int = 1024) -> List[Point]:
        """将路径命令转换为点序列

        支持的命令:
        - M/m: Move to
        - L/l: Line to
        - Q/q: Quadratic Bezier curve
        - C/c: Cubic Bezier curve
        - Z/z: Close path
        """
        points = []
        current_pos = Point(0, 0)
        start_pos = Point(0, 0)  # 当前子路径的起点

        for cmd in commands:
            cmd_type = cmd.type.upper()
            params = cmd.params

            if cmd_type == 'M':  # Move to
                current_pos = SVGPathParser.transform_point(params[0], params[1])
                start_pos = current_pos
                points.append(current_pos)
                # 处理多对参数的情况（隐含 Line to）
                for i in range(2, len(params), 2):
                    current_pos = SVGPathParser.transform_point(params[i], params[i + 1])
                    points.append(current_pos)

            elif cmd_type == 'L':  # Line to
                for i in range(0, len(params), 2):
                    current_pos = SVGPathParser.transform_point(params[i], params[i + 1])
                    points.append(current_pos)

            elif cmd_type == 'Q':  # Quadratic Bezier
                for i in range(0, len(params), 4):
                    ctrl = SVGPathParser.transform_point(params[i], params[i + 1])
                    end = SVGPathParser.transform_point(params[i + 2], params[i + 3])
                    # 插值生成贝塞尔曲线上的点
                    curve_points = SVGPathParser._quadratic_bezier_points(
                        current_pos, ctrl, end, steps=10
                    )
                    points.extend(curve_points)
                    current_pos = end

            elif cmd_type == 'C':  # Cubic Bezier
                for i in range(0, len(params), 6):
                    ctrl1 = SVGPathParser.transform_point(params[i], params[i + 1])
                    ctrl2 = SVGPathParser.transform_point(params[i + 2], params[i + 3])
                    end = SVGPathParser.transform_point(params[i + 4], params[i + 5])
                    # 插值生成贝塞尔曲线上的点
                    curve_points = SVGPathParser._cubic_bezier_points(
                        current_pos, ctrl1, ctrl2, end, steps=10
                    )
                    points.extend(curve_points)
                    current_pos = end

            elif cmd_type == 'Z':  # Close path
                current_pos = start_pos
                # 闭合路径，添加起点（如果还没闭合）
                if points and (points[-1].x != start_pos.x or points[-1].y != start_pos.y):
                    points.append(start_pos)

        return points

    @staticmethod
    def _quadratic_bezier_points(p0: Point, p1: Point, p2: Point, steps: int = 10) -> List[Point]:
        """生成二次贝塞尔曲线上的点"""
        points = []
        for i in range(1, steps + 1):
            t = i / steps
            # B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
            x = (1 - t) ** 2 * p0.x + 2 * (1 - t) * t * p1.x + t ** 2 * p2.x
            y = (1 - t) ** 2 * p0.y + 2 * (1 - t) * t * p1.y + t ** 2 * p2.y
            points.append(Point(x, y))
        return points

    @staticmethod
    def _cubic_bezier_points(p0: Point, p1: Point, p2: Point, p3: Point, steps: int = 10) -> List[Point]:
        """生成三次贝塞尔曲线上的点"""
        points = []
        for i in range(1, steps + 1):
            t = i / steps
            # B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            x = ((1 - t) ** 3 * p0.x +
                 3 * (1 - t) ** 2 * t * p1.x +
                 3 * (1 - t) * t ** 2 * p2.x +
                 t ** 3 * p3.x)
            y = ((1 - t) ** 3 * p0.y +
                 3 * (1 - t) ** 2 * t * p1.y +
                 3 * (1 - t) * t ** 2 * p2.y +
                 t ** 3 * p3.y)
            points.append(Point(x, y))
        return points

    @staticmethod
    def calculate_path_length(points: List[Point]) -> float:
        """计算路径总长度"""
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            length += (dx ** 2 + dy ** 2) ** 0.5
        return length

    @staticmethod
    def split_path_by_length(points: List[Point], num_segments: int) -> List[List[Point]]:
        """按长度将路径分割为多段

        Returns:
            包含 num_segments 个路径段的列表，每段是一个点列表
        """
        if len(points) < 2:
            return [points.copy() for _ in range(num_segments)]

        total_length = SVGPathParser.calculate_path_length(points)
        segment_length = total_length / num_segments

        segments = []
        current_segment = [points[0]]
        current_length = 0.0
        target_length = segment_length

        for i in range(1, len(points)):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            segment_len = (dx ** 2 + dy ** 2) ** 0.5

            # 检查当前段是否需要被分割
            while current_length + segment_len >= target_length and len(segments) < num_segments:
                # 计算部分点
                remaining = target_length - current_length
                ratio = remaining / segment_len if segment_len > 0 else 0
                partial_x = points[i - 1].x + dx * ratio
                partial_y = points[i - 1].y + dy * ratio
                current_segment.append(Point(partial_x, partial_y))

                # 保存当前段
                segments.append(current_segment)

                # 开始新段
                current_segment = [Point(partial_x, partial_y)]
                current_length = 0
                target_length = segment_length

                # 更新剩余长度
                segment_len *= (1 - ratio)

            # 添加当前点
            current_segment.append(points[i])
            current_length += segment_len

        # 添加最后剩余的点
        while len(segments) < num_segments:
            if current_segment:
                segments.append(current_segment.copy())
                current_segment = [current_segment[-1]] if current_segment else []
            else:
                segments.append(points[-1:] if points else [])

        return segments
