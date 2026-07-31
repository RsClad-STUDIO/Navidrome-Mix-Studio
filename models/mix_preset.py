"""Mix生成パラメータのプリセットを管理するモデル。"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict


@dataclass
class MixPreset:
    """Mix生成用プリセットモデル。"""

    name: str
    limit: int = 25
    mix_type: str = "Recent"
    favorite_priority: str = "Medium"  # Low, Medium, High
    album_diversity: str = "Normal"  # Low, Normal, High
    artist_diversity: str = "Normal"
    suppress_instrumental: bool = True
    suppress_live: bool = False
    suppress_remix: bool = False
    suppress_demo: bool = False
    suppress_acoustic: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書型データに変換します。"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MixPreset":
        """辞書データからMixPresetインスタンスを復元します。"""
        return cls(
            name=data.get("name", "Untitled Preset"),
            limit=data.get("limit", 25),
            mix_type=data.get("mix_type", "Recent"),
            favorite_priority=data.get("favorite_priority", "Medium"),
            album_diversity=data.get("album_diversity", "Normal"),
            artist_diversity=data.get("artist_diversity", "Normal"),
            suppress_instrumental=data.get("suppress_instrumental", True),
            suppress_live=data.get("suppress_live", False),
            suppress_remix=data.get("suppress_remix", False),
            suppress_demo=data.get("suppress_demo", False),
            suppress_acoustic=data.get("suppress_acoustic", False),
            extra_params=data.get("extra_params", {}),
        )