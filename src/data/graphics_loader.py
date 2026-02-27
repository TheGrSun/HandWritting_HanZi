"""makemeahanzi graphics.txt 数据加载器"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CharacterData:
    """字符数据结构"""
    character: str
    strokes: List[str]
    medians: List[List[List[int]]]


class GraphicsLoader:
    """makemeahanzi graphics.txt 加载器

    graphics.txt 格式:
    每行一个 JSON 对象，包含:
    - character: 汉字
    - strokes: SVG 路径数组
    - medians: 中点轨迹数组
    """

    def __init__(self, data_path: Path = None):
        self.data_path = data_path or Path("data/makemeahanzi")
        self.graphics_file = self.data_path / "graphics.txt"
        self._cache: Dict[str, CharacterData] = {}

    def load(self, force_reload: bool = False) -> Dict[str, CharacterData]:
        """加载所有字符数据"""
        if self._cache and not force_reload:
            return self._cache

        self._cache = {}

        if not self.graphics_file.exists():
            raise FileNotFoundError(
                f"graphics.txt not found at {self.graphics_file}"
            )

        with open(self.graphics_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    char_data = CharacterData(
                        character=data['character'],
                        strokes=data['strokes'],
                        medians=data.get('medians', [])
                    )
                    self._cache[data['character']] = char_data
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                    continue

        return self._cache

    def get_character(self, char: str) -> Optional[CharacterData]:
        """获取单个字符数据"""
        if not self._cache:
            self.load()

        return self._cache.get(char)

    def has_character(self, char: str) -> bool:
        """检查是否包含某字符"""
        if not self._cache:
            self.load()
        return char in self._cache

    def get_all_characters(self) -> List[str]:
        """获取所有可用字符列表"""
        if not self._cache:
            self.load()
        return list(self._cache.keys())

    def get_character_count(self) -> int:
        """获取字符总数"""
        if not self._cache:
            self.load()
        return len(self._cache)
