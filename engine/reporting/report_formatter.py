from models.statistics_data import StatisticsData

class ReportFormatter:
    """StatisticsDataを受け取り、表示専用のテキストレポートを整形するクラス。"""

    @staticmethod
    def format(data: StatisticsData) -> str:
        p = data.preset
        
        # 表示用のラベルマッピング
        display_map = {
            "favorite": "Favorite",
            "recent": "Recent",
            "play_count": "High PlayCount",
            "similarity": "Artist Similarity",
            "similarity_artist": "Artist Similarity",
            "similarity_album": "Album Similarity",
            "discovery": "Random Discovery",
            "forgotten_favorite": "Forgotten Favorite"
        }

        # 1. ヘッダーセクション
        res = [
            "==================================================",
            "=== Recommendation Report ===",
            f"Preset               : {p}",
            f"Library Total        : {data.library_total} songs",
            f"Candidate Pool       : {data.pool_count} songs",
            f"Generation Time      : {data.gen_time_ms} ms",
            "--------------------------------------------------",
            "Confidence Calculation",
            f"Strategy Selection   : {data.strat_initial_count:>2} / {data.limit}"
        ]

        # 2. Confidence Breakdown (ツリー形式)
        for k, v in data.strat_composition.items():
            if v > 0:
                label = "Nostalgic Picks" if "Forgotten" in p and k == "recent" else display_map.get(k, k.capitalize())
                res.append(f"  ├ {label:<20} {v:>2}")

        res.extend([
            f"Refill Added         : {data.refill_total:>2} (-{data.conf_refill_penalty_pct}%)",
            "",
            f"Final Confidence     : {data.confidence}%",
            "--------------------------------------------------",
            "",
            "Candidate Utilization (Strategy Selection Only)"
        ])

        # 3. 利用率セクション
        for row in data.utilization:
            res.append(f"{row.label:<20} : {row.candidates:>4} / {row.used:<3} ({row.ratio:>5.1f}%)")
        
        eff = (data.strat_initial_count / 300 * 100) if 300 > 0 else 0
        res.append(f"{'Top300 Used':<20} : {data.strat_initial_count:>3} songs ({eff:>5.1f}%)")
        res.append("")

        # 4. Rotation / Score Summary
        res.append("Rotation Summary")
        res.append(f"{'Affected Songs':<20} : {data.rotation.affected}")
        res.append(f"{'Average Penalty':<20} : {data.rotation.avg_penalty:.1f}%")
        res.append("")

        res.append("Score Statistics")
        res.append(f"{'Highest / Lowest':<20} : {data.scores.highest:.1f} / {data.scores.lowest:.1f} pt")
        res.append(f"{'Average / Median':<20} : {data.scores.average:.1f} / {data.scores.median:.1f} pt")
        res.append("")

        # 5. Refill / Diversity
        res.append("Refill Summary")
        res.append(f"{'Initial Selection':<20} : {data.strat_initial_count:>3} songs")
        res.append(f"{'Refill Added':<20} : {data.refill_total:>3} songs")
        res.append(f"{'Final Playlist':<20} : {data.final_total:>3} songs")
        res.append("")

        res.append("Playlist Diversity")
        res.append(f"{'Unique Artists':<20} : {data.diversity.unique_artists:>3} / {data.diversity.total_artists:<3} ({data.diversity.ratio_artist:>5.1f}%)")
        res.append(f"{'Unique Albums':<20} : {data.diversity.unique_albums:>3} / {data.diversity.total_albums:<3} ({data.diversity.ratio_album:>5.1f}%)")
        res.append(f"{'Assessment':<20} : {data.diversity.assessment_level} Diversity")
        res.append("")

        # 6. 最終構成比率
        res.append("Final Playlist Composition")
        for k, v in data.final_composition.items():
            if "Forgotten" in p and k == "recent":
                label = "Nostalgic Picks"
            else:
                label = display_map.get(k, k.replace("_", " ").capitalize())
            res.append(f"{label:<20} : {int(v/data.final_total*100):>3}%")
        
        if data.refill_total > 0:
            res.append(f"{'Refill System':<20} : {int(data.refill_total/data.final_total*100):>3}%")

        res.append("--------------------------------------------------")
        res.append(f"Result: {data.final_total} songs generated successfully.")
        res.append("==================================================")

        return "\n".join(res)