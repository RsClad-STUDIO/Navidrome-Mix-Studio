import re
from typing import Dict

class TitleNormalizer:
    # 判定ルール：前後がアルファベットでない独立した単語として判定
    RULES = {
        "live": [r"live", r"concert", r"ライブ", r"コンサート", r"録画", r"完全版", r"公演"],
        "instrumental": [
            r"instrumental", r"inst\b", r"off vocal", r"backing track", 
            r"伴奏", r"カラオケ", r"ピアノメドレー", r"without vocal",
            r"piano ver", r"violin ver", r"music box", r"orgel", r"オルゴール"],
        "remix": [r"remix", r"re-mix", r"arrange", r"アレンジ", r"edit"],
        "demo": [r"demo", r"デモ", r"試作"],
        "acoustic": [r"acoustic", r"unplugged", r"アコースティック"],
        "version": [r"ver\.", r"version", r"short ver", r"tv size"]
    }

    @staticmethod
    def detect_versions(text: str) -> Dict[str, bool]:
        if not text:
            return {k: False for k in TitleNormalizer.RULES.keys()}

        text_lower = text.lower()
        results = {}

        for category, keywords in TitleNormalizer.RULES.items():
            found = False
            for kw in keywords:
                # 根本対策：前後がアルファベット(a-z)でない場合のみマッチ
                # これにより "Come Alive" はスルーし、"スターレイルLIVE" や "(Inst.)" は検知する
                pattern = fr"(?i)(?<![a-z]){kw}(?![a-z])"
                if re.search(pattern, text_lower):
                    found = True
                    break
            results[category] = found
        return results

    @staticmethod
    def normalize(title: str) -> str:
        """比較用の純粋なタイトルを生成 (DiversityEngineで使用)"""
        if not title: return ""
        # カッコ内を除去
        n = re.sub(r"[\(\[（［].*?[\)\]）］]", "", title.lower())
        # 記号をスペースに
        n = re.sub(r"[:：\-－_＿/／]", " ", n)
        return " ".join(n.split()).strip()