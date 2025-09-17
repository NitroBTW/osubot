"""
Script full of useful rosu calculations
"""
import rosu_pp_py as rosu
from typing import Optional, Any

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
    mods_string = api_mods_to_string
    
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
    od = getattr(api_beatmap_info, "accuracy", None)  # API calls OD 'accuracy' because lazer
    hp = getattr(api_beatmap_info, "drain", None)
    bpm = getattr(api_beatmap_info, "bpm", None)
    length_sec = getattr(api_beatmap_info, "total_length", None)

    # Score data from api
    accuracy_percent = float(score.accuracy) * 100.0
    misses = int(getattr(score.statistics, "count_miss", 0))
    performance = rosu.Performance(lazer=lazer)
    performance.set_accuracy(accuracy_percent)
    performance.set_misses(misses)
    performance.set_mods(mods_string)
    if getattr(score, "max_combo", None) is not None:
        performance.set_combo(int(score.max_combo))
    pp = score.pp
    
    # If-FC PP
    performance_fc = rosu.Performance(lazer=lazer)
    performance_fc.set_accuracy(accuracy_percent)
    performance_fc.set_misses(0)
    performance_fc.set_mods(mods_string)
    pp_fc = float(performance_fc.calculate(beatmap).pp)
    
    # SS PP
    performance_ss = rosu.Performance(lazer=lazer)
    performance_ss.set_accuracy(100.0)
    performance_ss.set_misses(0)
    performance_ss.set_mods(mods_string)
    pp_ss = float(performance_ss.calculate(beatmap).pp)
    
    # Return
    return ScoreMetrics(
        pp_actual=pp,
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