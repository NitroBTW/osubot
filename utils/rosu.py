"""
Script full of useful rosu calculations
"""
import math
import rosu_pp_py as rosu
from typing import Optional, Any
from dataclasses import dataclass

from utils.helpers import *

@dataclass
class ScoreMetrics:
    """
    Container for score metrics
    """
    pp: Optional[float]
    pp_if_fc: Optional[float]
    pp_if_ss: Optional[float]
    stars_with_mods: Optional[float]
    map_cs: Optional[float]
    map_ar: Optional[float]
    map_od: Optional[float]
    map_hp: Optional[float]
    map_bpm: Optional[float]
    map_length_sec: Optional[int]
    map_max_combo: Optional[int]

def calculate_score_metrics(
    beatmap_path: str,
    score: Any,
    mode: Optional[str] = None,
    lazer: bool = True,    
) -> ScoreMetrics:
    """
    Compute score metrics (PP, Map info, etc) for a beatmap at a given path.

    Args:
        beatmap_path (str): Path to the beatmap to calculate values for.
        score (Any): ossapi Score object.
        mode (Optional[str], optional): Specify which mode to calculate metrics for. Defaults to None.
        lazer (bool, optional): Use lazer calculations or not. Defaults to True.

    Returns:
        ScoreMetrics: Dataclass for score information
    """
    # Mods parsing
    mods_string = api_mods_to_string(score.mods)
    print(f"mods string: {mods_string}")
    
    # Beatmap parsing
    api_beatmap_info = score.beatmap
    print(f"api_beatmap_inf: \n{api_beatmap_info}\n\n\n")
    beatmap = rosu.Beatmap(path=beatmap_path)
    
    # Difficulty attributes
    difficulty = rosu.Difficulty(mods=mods_string, lazer=lazer)
    print(f"difficulty: \n{difficulty}\n\n\n")
    difficulty_attributes = difficulty.calculate(beatmap)
    print(f"difficulty_attributes: \n{difficulty_attributes}\n\n\n")
    stars = float(getattr(difficulty_attributes, "stars", 0.0))
    print(f"stars: {stars}")
    map_max_combo = int(getattr(difficulty_attributes, "max_combo", 0)) or None
    print(f"map_max_combo: {map_max_combo}")
    
    # Beatmap stats (raw from API if present, fallback to difficulty attributes where relevant)
    cs = getattr(api_beatmap_info, "cs", None)
    ar = getattr(api_beatmap_info, "ar", None)
    od = getattr(api_beatmap_info, "accuracy", None)  # API calls OD 'accuracy' because lazer
    hp = getattr(api_beatmap_info, "drain", None)
    bpm = getattr(api_beatmap_info, "bpm", None)
    length_sec = getattr(api_beatmap_info, "total_length", None)
    print(f"details: cs{cs}, ar{ar}, od{od}, hp{hp}, {bpm}, {length_sec}")
    
    n_circles = int(getattr(difficulty_attributes, "n_circles", 0))
    print(f"n_circles: {n_circles}")
    n_sliders = int(getattr(difficulty_attributes, "n_sliders", 0))
    print(f"n_sliders: {n_sliders}")
    n_large_ticks = int(getattr(difficulty_attributes, "n_large_ticks", 0))
    print(f"n_large_ticks: {n_large_ticks}")
    n_small_ticks = int(getattr(difficulty_attributes, "n_small_ticks", 0) or 0)
    print(f"n_small_ticks: {n_small_ticks}")
    total_objects_for_mode = n_circles + n_sliders
    print(f"Total objects for mode: {total_objects_for_mode}")
    
    # Score data from api
    n300 = int(getattr(score.statistics, "great", 0))
    print(f"n300: {n300}")
    n100 = int(getattr(score.statistics, "ok", 0))
    print(f"n100: {n100}")
    n50 = int(getattr(score.statistics, "meh", 0))
    print(f"n50: {n50}")
    misses = int(getattr(score.statistics, "miss", 0))
    print(f"misses: {misses}")
    
    # Passed objects and 'unseen' objects (if the play is a fail)
    passed_objects_count = n300 + n100 + n50 + misses
    print(f"Passed objects: {passed_objects_count}")
    unseen_objects = max(0, total_objects_for_mode - passed_objects_count)
    print(f"UNseen objects: {unseen_objects}")
    
    # Convert unseen objects into 300s
    n300_fc = n300
    print(f"n300_fc {n300_fc}")
    
    # Counted hits after removing misses
    counted_hits = total_objects_for_mode - misses
    print(f"counted_hits: {counted_hits}")
    if counted_hits <= 0 or total_objects_for_mode <= 0:
        print("Treating as SS")
        # Treat as SS
        accuracy_fc = 100.0
        print(f"Accuracy_fc: {accuracy_fc}")
        n100_fc = n100
        print(f"n100_fc {n100_fc}")
        n50_fc = n50
        print(f"n50_fc: {n50_fc}")
        misses_fc = 0
        print(f"misses_fc: {misses_fc}")
    
    else:
        print("NOT TREATING AS SS")
        # Distribute original misses between 300s and 100s for realistic/average fc value
        redistribution_ratio = 1.0 - (n300_fc / counted_hits)
        print(f"ratio: {redistribution_ratio}")
        new_100s = int(math.ceil(max(0.0, redistribution_ratio) * misses))
        print(f"new100s: {new_100s}")
        
        n300_fc += max(0, misses - new_100s)
        print(f"n300_fc: {n300_fc}")
        n100_fc = n100 + new_100s
        print(f"n100_fc {n100_fc}")
        n50_fc = n50
        print(f"n50_fc: {n50_fc}")
        misses_fc = 0
        print(f"misses_fc: {misses_fc}")
        
        accuracy_fc = (
            (300 * n300_fc + 100 * n100_fc + 50 * n50_fc)
            / (300 * total_objects_for_mode)
            * 100.0
        )
        print(f"accuracy_fc: {accuracy_fc}")
        
    # Build performance calculation for FC
    performance_fc = rosu.Performance(lazer=lazer)
    performance_fc.set_mods(mods_string)
    
    if hasattr(performance_fc, "set_n300"):
        performance_fc.set_n300(int(n300_fc))
        performance_fc.set_n100(int(n100_fc))
        performance_fc.set_n50(int(n50_fc))
        performance_fc.set_misses(int(misses_fc))
        
        # For lazer scoring, ensure slider stuff is max
        # If score statistics has these, set them; otherwise skip.
        # Large ticks (heads/tails)
        if hasattr(performance_fc, "set_slider_end_hits"):
            performance_fc.set_slider_end_hits(int(n_large_ticks))
        
        # Small ticks (slider ticks)
        if n_small_ticks and hasattr(performance_fc, "set_small_tick_hits"):
            performance_fc.set_small_tick_hits(int(n_small_ticks))
        
        # Classic mod handling
        is_classic = "CL" in mods_string or "Classic" in mods_string
        if is_classic and hasattr(performance_fc, "set_slider_tail_hits"):
            performance_fc.set_slider_tail_hits(int(n_sliders))
            
    # Fallback and use accuracy + 0 misses
    else:
        print("FALLBACK")
        performance_fc.set_accuracy(float(accuracy_fc))
        performance_fc.set_misses(0)
        print(f"performance_fc after fallback accuracy: \n{performance_fc.__getstate__}\n\n\n")

    print(accuracy_fc)
    pp_fc = float(performance_fc.calculate(beatmap).pp)
    
    # SS PP
    performance_ss = rosu.Performance(lazer=lazer)
    performance_ss.set_accuracy(100.0)
    performance_ss.set_misses(0)
    performance_ss.set_mods(mods_string)
    pp_ss = float(performance_ss.calculate(beatmap).pp)
    
    # Return
    return ScoreMetrics(
        pp=score.pp,
        pp_if_fc=pp_fc,
        pp_if_ss=pp_ss,
        stars_with_mods=stars,
        map_cs=float(cs) if cs is not None else None,
        map_ar=float(ar) if ar is not None else None,
        map_od=float(od) if od is not None else None,
        map_hp=float(hp) if hp is not None else None,
        map_bpm=float(bpm) if bpm is not None else None,
        map_length_sec=int(length_sec) if length_sec is not None else None,
        map_max_combo=map_max_combo,
    )