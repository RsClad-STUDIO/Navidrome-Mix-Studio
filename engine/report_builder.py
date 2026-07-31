import logging
from typing import Dict, Any

class ReportBuilder:
    """Phase 12.6: 統計の正確性と分析性を重視したレポートフォーマッタ"""

    @staticmethod
    def build_report(stats: Dict[str, Any]) -> str:
        preset = stats.get("preset", "Unknown Mix")
        limit = stats.get("limit", 25)
        
        # --- 1. 基本数値の整理 ---
        total = stats.get("final_total", 0)
        strat_init = stats.get("strat_initial_count", 0) # Refill前の純粋な選出数
        refill_total = stats.get("refill_total", 0)
        
        lib_art = stats.get("lib_artists", 1) or 1
        lib_alb = stats.get("lib_albums", 1) or 1
        mix_art = stats.get("mix_artists", 0)
        mix_alb = stats.get("mix_albums", 0)

        # --- 2. 信頼度 (Recommendation Confidence) の計算 ---
        # Strategyが本来の構成をどれだけ維持できたか
        # 100% - (Refill依存率 * 50) - (Random依存率 * 20)
        refill_rate = (refill_total / limit) if limit > 0 else 0
        random_rate = (stats.get("final_src_discovery", 0) / limit) if limit > 0 else 0
        conf_score = 100 - (refill_rate * 50) - (random_rate * 20)
        confidence = max(0, min(100, int(conf_score)))

        # --- 3. 多様性アセスメント ---
        art_ratio = (mix_art / lib_art * 100)
        if art_ratio < 15:
            div_level, div_msg = "Low", "Artist repetition is high. Consider increasing diversity settings."
        elif art_ratio < 30:
            div_level, div_msg = "Moderate", "Album repetition is well balanced."
        elif art_ratio < 50:
            div_level, div_msg = "High", "Good variety of artists and albums."
        else:
            div_level, div_msg = "Excellent", "Excellent diversity. Wide range of artists selected."

        # --- 4. レポート組み立て ---
        report = [
            "==================================================",
            "=== Recommendation Report ===",
            f"Preset               : {preset}",
            f"Library Total        : {stats.get('library_total', 0)} songs",
            f"Candidate Pool       : {stats.get('pool_count', 0)} songs",
            f"Generation Time      : {stats.get('gen_time_ms', 0)} ms",
            "--------------------------------------------------",
            f"Recommendation Confidence : {confidence}%",
            "",
            "Candidate Utilization (Strategy Selection Only)"
        ]

        # 100%を超えない正確な利用率表示
        for label, c_key, u_key in [
            ("Favorite", "can_fav", "strat_fav"),
            ("Recent", "can_recent", "strat_recent"),
            ("High PlayCount", "can_pc", "strat_pc"),
            ("Album Candidates", "can_album", "strat_album"),
            ("Artist Candidates", "can_artist", "strat_artist")
        ]:
            cand = stats.get(c_key, 0)
            used = stats.get(u_key, 0) # Strategyが選んだ数 (Refillを含まない)
            util = (used / cand * 100) if cand > 0 else 0.0
            report.append(f"{label:<20} : {cand:>4} / {used:<3} ({util:>5.1f}%)")
        
        # Pool Efficiency
        eff = (strat_init / 300 * 100) if 300 > 0 else 0
        report.append(f"{'Top300 Used':<20} : {strat_init:>3} songs ({eff:>5.1f}%)")
        report.append("")

        report.append("Rotation Summary")
        report.append(f"{'Affected Songs':<20} : {stats.get('rotation_count', 0)}")
        report.append(f"{'Average Penalty':<20} : {stats.get('avg_penalty', 0.0):.1f}%")
        if stats.get("rotation_exempt", 0) > 0:
            report.append(f"{'Top Favorite Exempt':<20} : {stats.get('rotation_exempt', 0)}")
        report.append("")

        if "score_high" in stats:
            report.append("Score Statistics")
            report.append(f"{'Highest / Lowest':<20} : {stats.get('score_high', 0):.1f} / {stats.get('score_low', 0):.1f} pt")
            report.append(f"{'Average / Median':<20} : {stats.get('score_avg', 0):.1f} / {stats.get('score_median', 0):.1f} pt")
            report.append("")

        report.append("Refill Summary")
        report.append(f"{'Initial Selection':<20} : {strat_init:>3} songs")
        report.append(f"{'Refill Added':<20} : {refill_total:>3} songs")
        report.append(f"{'Final Playlist':<20} : {total:>3} songs")
        
        if refill_total > 0:
            r_sources = stats.get("refill_sources", {})
            report.append("Refill Sources:")
            for src_name, count in r_sources.items():
                if count > 0:
                    report.append(f"  {src_name.capitalize():<18} : {count}")
        report.append("")

        # Strategy Composition (Forgottenの名称改善対応)
        report.append("Strategy Composition")
        if "Discovery Mix" in preset:
            report.append(f"{'Discovery Layer':<20} : Scanned {stats.get('disc_scanned', 0)}, Inserted {stats.get('disc_inserted', 0)}")

        comp_items = [
            ("strat_fav_selected", "Favorite"),
            ("strat_src_recent", "Nostalgic Picks" if "Forgotten" in preset else "Recent"),
            ("strat_src_playcount", "High PlayCount"),
            ("strat_src_sim_artist", "Artist Similarity"),
            ("strat_src_sim_album", "Album Similarity"),
            ("strat_src_discovery", "Random Discovery")
        ]
        for key, label in comp_items:
            val = stats.get(key, 0)
            if val > 0 or (label == "Favorite" and "Forgotten" not in preset):
                report.append(f"{label:<20} : {val:>2} ({int(val/strat_init*100 if strat_init > 0 else 0):>3}%)")
        report.append("")

        report.append("Playlist Diversity")
        report.append(f"{'Unique Artists':<20} : {mix_art:>3} / {lib_art:<3} ({mix_art/lib_art*100:>5.1f}%)")
        report.append(f"{'Unique Albums':<20} : {mix_alb:>3} / {lib_alb:<3} ({mix_alb/lib_alb*100:>5.1f}%)")
        report.append(f"{'Assessment':<20} : {div_level} Diversity")
        report.append(f"  {div_msg}")
        report.append("")

        report.append("Final Playlist Composition")
        for key, label in [
            ("final_fav_selected", "Favorite"),
            ("final_src_recent", "Nostalgic Picks" if "Forgotten" in preset else "Recent"),
            ("final_src_playcount", "High PlayCount"),
            ("final_src_sim_artist", "Artist Similarity"),
            ("final_src_sim_album", "Album Similarity"),
            ("final_src_discovery", "Random Discovery"),
            ("refill_total", "Refill System")
        ]:
            val = stats.get(key, 0)
            if val > 0:
                report.append(f"{label:<20} : {int(val/total*100):>3}%")

        report.extend([
            "--------------------------------------------------",
            f"Result: {total} songs generated successfully.",
            "=================================================="
        ])

        return "\n".join(report)