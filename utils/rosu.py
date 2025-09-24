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
    accuracy_if_fc: Optional[float]
    pp_if_ss: Optional[float]
    stars_with_mods: Optional[float]
    map_cs: Optional[float]
    map_ar: Optional[float]
    map_od: Optional[float]
    map_hp: Optional[float]
    map_bpm: Optional[float]
    map_length_sec: Optional[int]
    map_max_combo: Optional[int]


def _calculate_fc_stats(
    n300: int,
    n100: int,
    n50: int,
    misses: int,
    total_objects_for_mode: int,
    unseen_objects: int
) -> tuple[int, int, int, int, float]:
    """
    Calculate full combo hit statistics and accuracy.

    Args:
        n300 (int): Number of 300s hit.
        n100 (int): Number of 100s hit.
        n50 (int): Number of 50s hit.
        misses (int): Number of misses.
        total_objects_for_mode (int): Total hittable objects in the mode.
        unseen_objects (int): Unseen objects to convert to 300s.

    Returns:
        tuple[int, int, int, int, float]: n300_fc, n100_fc, n50_fc, misses_fc, accuracy_fc
    """
    n300_fc = n300 + unseen_objects
    
    counted_hits = total_objects_for_mode - misses
    if counted_hits <= 0 or total_objects_for_mode <= 0:
        # Treat as SS
        accuracy_fc = 100.0
        n100_fc = n100
        n50_fc = n50
        misses_fc = 0
    
    else:
        # Distribute original misses between 300s and 100s for realistic/average fc value
        redistribution_ratio = 1.0 - (n300_fc / counted_hits)
        print(f"ratio: {redistribution_ratio}")
        new_100s = int(math.ceil(max(0.0, redistribution_ratio) * misses))
        
        n300_fc += max(0, misses - new_100s)
        n100_fc = n100 + new_100s
        n50_fc = n50
        misses_fc = 0
        
        accuracy_fc = (
            (300 * n300_fc + 100 * n100_fc + 50 * n50_fc)
            / (300 * total_objects_for_mode)
            * 100.0
        )
    
    return n300_fc, n100_fc, n50_fc, misses_fc, accuracy_fc


def _calculate_fc_pp(
    beatmap,
    mods_string: str,
    lazer: bool,
    n300_fc: int,
    n100_fc: int,
    n50_fc: int,
    misses_fc: int,
    accuracy_fc: float,
    map_max_combo: Optional[int],
    n_sliders: int,
    n_small_ticks: int
) -> float:
    """
    Build performance object and calculate PP for full combo scenario.

    Args:
        beatmap (rosu.Beatmap): The beatmap.
        mods_string (str): Mods as string.
        lazer (bool): Use lazer calculations.
        n300_fc (int): 300s for FC.
        n100_fc (int): 100s for FC.
        n50_fc (int): 50s for FC.
        misses_fc (int): Misses for FC.
        accuracy_fc (float): Accuracy for FC.
        map_max_combo (Optional[int]): Map max combo.
        n_sliders (int): Number of sliders.
        n_small_ticks (int): Number of small ticks.

    Returns:
        float: PP for FC.
    """
    # Build performance calculation for FC
    performance_fc = rosu.Performance(lazer=lazer)
    performance_fc.set_mods(mods_string)
    
    if lazer:
        performance_fc.set_n300(int(n300_fc))
        performance_fc.set_n100(int(n100_fc))
        performance_fc.set_n50(int(n50_fc))
        performance_fc.set_misses(int(misses_fc))
        
        # For lazer scoring, ensure slider stuff is max
        # If score statistics has these, set them; otherwise skip.
        # Large ticks (slider ends)
        if hasattr(performance_fc, "set_slider_end_hits"):
            performance_fc.set_slider_end_hits(int(n_sliders))
        
        # Small ticks (slider ticks)
        if n_small_ticks > 0 and hasattr(performance_fc, "set_small_tick_hits"):
            performance_fc.set_small_tick_hits(n_small_ticks)  # All slider ticks hit for FC
    
    # Fallback and use accuracy + 0 misses
    else:
        performance_fc.set_accuracy(float(accuracy_fc))
        performance_fc.set_misses(0)
        performance_fc.set_combo(int(map_max_combo))

    pp_fc = float(performance_fc.calculate(beatmap).pp)
    return pp_fc


def _calculate_actual_pp(
    beatmap,
    mods_string: str,
    lazer: bool,
    n300: int,
    n100: int,
    n50: int,
    misses: int,
    actual_slider_end_hits: int,
    actual_small_tick_hits: int,
    score_max_combo: Optional[int],
    score_accuracy: Any
) -> float:
    """
    Build performance object and calculate actual PP from score.

    Args:
        beatmap (rosu.Beatmap): The beatmap.
        mods_string (str): Mods as string.
        lazer (bool): Use lazer calculations.
        n300 (int): Actual 300s.
        n100 (int): Actual 100s.
        n50 (int): Actual 50s.
        misses (int): Actual misses.
        actual_slider_end_hits (int): Actual slider end hits.
        actual_small_tick_hits (int): Actual small tick hits.
        score_max_combo (Optional[int]): Score max combo.
        score_accuracy (Any): Score accuracy for stable.

    Returns:
        float: Actual PP.
    """
    # Actual PP
    performance_actual = rosu.Performance(lazer=lazer)
    performance_actual.set_mods(mods_string)
    
    if lazer:
        performance_actual.set_n300(int(n300))
        performance_actual.set_n100(int(n100))
        performance_actual.set_n50(int(n50))
        performance_actual.set_misses(int(misses))

        # Set actual slider hits from score statistics
        if hasattr(performance_actual, "set_slider_end_hits"):
            performance_actual.set_slider_end_hits(actual_slider_end_hits)
        
        # Set actual small ticks if available
        if hasattr(performance_actual, "set_small_tick_hits"):
            performance_actual.set_small_tick_hits(actual_small_tick_hits)
        
        # Set combo
        if score_max_combo is not None:
            performance_actual.set_combo(int(score_max_combo))
    else:
        accuracy_percent = float(score_accuracy) * 100.0
        performance_actual.set_accuracy(accuracy_percent)
        performance_actual.set_misses(int(misses))
        if score_max_combo is not None:
            performance_actual.set_combo(int(score_max_combo))
    
    actual_pp = performance_actual.calculate(beatmap).pp
    return actual_pp


def _calculate_ss_pp(
    beatmap,
    mods_string: str,
    lazer: bool
) -> float:
    """
    Calculate PP for SS score.

    Args:
        beatmap (rosu.Beatmap): The beatmap.
        mods_string (str): Mods as string.
        lazer (bool): Use lazer calculations.

    Returns:
        float: SS PP.
    """
    # SS PP
    performance_ss = rosu.Performance(lazer=lazer)
    performance_ss.set_accuracy(100.0)
    performance_ss.set_misses(0)
    performance_ss.set_mods(mods_string)
    pp_ss = float(performance_ss.calculate(beatmap).pp)
    return pp_ss


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
    
    # Beatmap parsing
    api_beatmap_info = score.beatmap
    beatmap = rosu.Beatmap(path=beatmap_path)
    
    # Difficulty attributes
    difficulty = rosu.Difficulty(mods=mods_string, lazer=lazer)
    difficulty_attributes = difficulty.calculate(beatmap)
    stars = float(getattr(difficulty_attributes, "stars", 0.0))
    map_max_combo = int(getattr(difficulty_attributes, "max_combo", 0)) or None
    
    # Beatmap stats (raw from API if present, fallback to difficulty attributes where relevant)
    cs = getattr(api_beatmap_info, "cs", None)
    ar = getattr(api_beatmap_info, "ar", None)
    od = getattr(api_beatmap_info, "accuracy", None) # API calls OD 'accuracy' because lazer
    hp = getattr(api_beatmap_info, "drain", None)
    bpm = getattr(api_beatmap_info, "bpm", None)
    length_sec = getattr(api_beatmap_info, "total_length", None)
    
    n_circles = int(getattr(difficulty_attributes, "n_circles", 0) or 0)
    n_sliders = int(getattr(difficulty_attributes, "n_sliders", 0) or 0)
    n_large_ticks = int(getattr(difficulty_attributes, "n_large_ticks", 0) or 0)
    n_small_ticks = int(getattr(difficulty_attributes, "n_small_ticks", 0) or 0)
    total_objects_for_mode = n_circles + n_sliders
    
    # Score data from api
    n300 = int(getattr(score.statistics, "great", 0) or 0)
    n100 = int(getattr(score.statistics, "ok", 0) or 0)
    n50 = int(getattr(score.statistics, "meh", 0) or 0)
    misses = int(getattr(score.statistics, "miss", 0) or 0)
    
    # Passed objects and 'unseen' objects (if the play is a fail)
    passed_objects_count = n300 + n100 + n50 + misses
    unseen_objects = max(0, total_objects_for_mode - passed_objects_count)
    
    # Calculate FC stats
    n300_fc, n100_fc, n50_fc, misses_fc, accuracy_fc = _calculate_fc_stats(
        n300, n100, n50, misses, total_objects_for_mode, unseen_objects
    )
    
    # Calculate FC PP
    pp_fc = _calculate_fc_pp(
        beatmap, mods_string, lazer, n300_fc, n100_fc, n50_fc, misses_fc,
        accuracy_fc, map_max_combo, n_sliders, n_small_ticks
    )
    
    # Actual slider hits
    actual_slider_end_hits = int(getattr(score.statistics, "slider_tail_hit", 0) or 0)
    actual_small_tick_hits = int(getattr(score.statistics, "small_tick_hit", 0) or 0)
    
    # Score combo and accuracy
    score_max_combo = getattr(score, "max_combo", None)
    
    # Calculate actual PP
    actual_pp = _calculate_actual_pp(
        beatmap, mods_string, lazer, n300, n100, n50, misses,
        actual_slider_end_hits, actual_small_tick_hits, score_max_combo, score.accuracy
    )
    
    # Calculate SS PP
    pp_ss = _calculate_ss_pp(beatmap, mods_string, lazer)
    
    # Return
    return ScoreMetrics(
        pp=actual_pp,
        pp_if_fc=pp_fc,
        accuracy_if_fc=accuracy_fc,
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