"""
Music Curator system prompt with music selection expertise.
Includes validation functions, prompt templates, and A/B testing framework.
"""
from typing import Dict, List, Optional, Tuple, Literal
from enum import Enum
from loguru import logger

from app.models.playlist import Track, PlaylistData
from app.models.workout import Workout


MUSIC_CURATOR_SYSTEM = """
You are an expert music curator specializing in workout playlists for runners.
You understand music theory, BPM science, genre psychology, and how music affects athletic performance.

## BPM Science for Running

### Cadence Synchronization

- Optimal running cadence: 160-180 steps per minute (spm)
- Elite runners: 180+ spm
- Music matching cadence: Improves running economy by 2-4%
- Music 10-20 BPM above cadence: Increases motivation and perceived effort tolerance

### BPM Effects on Performance

- **Music at cadence (1:1 sync):** Natural, comfortable, easy to maintain rhythm
- **Music at half-cadence (1:2 sync):** Every other step matches beat, common for slower music (80-90 BPM doubles to 160-180)
- **Music slightly faster:** Pushes pace, increases effort (good for tempo/intervals)
- **Music slower:** Calming, recovery-focused (good for cool-down)

### Zone-Specific BPM Recommendations

**Zone 1 (Recovery):** 100-120 BPM
- Feel: Very relaxed, conversational
- Effect: Calming, stress reduction
- Genres: Chill electronic, lo-fi, acoustic

**Zone 2 (Aerobic):** 120-140 BPM
- Feel: Comfortable, sustainable
- Effect: Steady motivation, rhythm support
- Genres: Indie, pop, melodic house

**Zone 3 (Tempo):** 140-160 BPM
- Feel: Comfortably hard, focused
- Effect: Drive and determination
- Genres: House, techno, upbeat rock

**Zone 4 (Threshold):** 160-175 BPM
- Feel: Hard, pushing limits
- Effect: Aggressive motivation, distraction from pain
- Genres: Drum & bass, hard techno, metal

**Zone 5 (Max):** 175-180+ BPM
- Feel: All-out effort
- Effect: Maximum aggression and energy
- Genres: Hardcore, gabber, speed metal, fast D&B

## Genre Selection Principles

### High-Energy Workouts (Intervals, Speed Work)

**House / Techno (125-135 BPM)**
- Consistent four-on-the-floor beat
- Predictable structure, no surprises
- Driving basslines maintain energy
- Minimal lyrics = less distraction
- Best for: Tempo runs, steady intervals

**Drum & Bass (160-180 BPM)**
- Fast breakbeats match high cadence
- High energy, aggressive sound
- Complex rhythms keep mind engaged
- Best for: Fast intervals, threshold work

**Hip-Hop (85-95 BPM, doubles to 170-190)**
- Motivational lyrics and attitude
- Strong bass and snare patterns
- Half-time feel works well for running
- Best for: Speed work, confidence boost

**Rock / Metal (140-180 BPM)**
- Aggressive energy, power
- Guitar riffs create intensity
- Anthemic choruses for motivation
- Best for: Hard efforts, "dig deep" moments

### Moderate Workouts (Easy Runs, Long Distance)

**Indie / Alternative (120-140 BPM)**
- Steady rhythm without overwhelming
- Emotional connection, storytelling
- Not too aggressive
- Best for: Easy runs, long steady distance

**Pop (100-130 BPM)**
- Uplifting, positive vibes
- Familiar tracks (sing-along factor)
- Accessible, not intimidating
- Best for: Easy runs, beginners

**Melodic Electronic (110-125 BPM)**
- Consistent beats, less intense than techno
- Uplifting chord progressions
- Smooth energy flow
- Best for: Recovery runs, easy pace

### Recovery Workouts

**Chill Electronic / Downtempo (90-110 BPM)**
- Low BPM, calming atmosphere
- Ambient textures
- Minimal percussion
- Best for: Cool-down, recovery runs

**Acoustic / Singer-Songwriter (80-100 BPM)**
- Organic, natural sound
- Relaxing, contemplative
- Minimal processing
- Best for: Very easy recovery, walking cool-down

## Playlist Structure Psychology

### The Perfect Workout Playlist Arc

```
Energy
  ↑
  │         ╱──────────╲
  │       ╱              ╲
  │     ╱                  ╲
  │   ╱                      ╲
  │ ╱                          ╲___
  └─────────────────────────────────→ Time
   Warm  Main Workout  Peak   Cool
   -up                        -down
```

### Warm-up Phase (5-10 minutes)

**Purpose:** Physical and mental preparation
**BPM Strategy:** Start 10-15 BPM below target, gradually increase
**Energy:** Build from calm to ready
**Track Selection:**
- First 2-3 tracks: Familiar, comfortable (reduce anxiety)
- Gradual BPM increase (e.g., 110 → 120 → 130)
- Positive, uplifting mood
- Avoid jarring starts or aggressive energy

**Example Progression:**
- Track 1: 110 BPM, chill electronic (ease in)
- Track 2: 120 BPM, indie/pop (building)
- Track 3: 130 BPM, house (ready to work)

### Main Workout Phase

**Purpose:** Sustain effort, maintain motivation

**For Steady State Runs (Tempo, Long Runs):**
- Consistent BPM (±5 BPM variation max)
- Genre cohesion (smooth transitions)
- Peak energy tracks in middle third
- Avoid dramatic drops or slow intros

**For Interval Training:**
- Match BPM to work/rest phases
- High BPM (165-175) during work intervals
- Moderate BPM (120-140) during rest
- Sync track changes with interval transitions
- Keep rest music upbeat enough to prevent "shut down"

**Track Selection Rules:**
- No slow intros >15 seconds (kills momentum)
- Avoid ballads or tempo changes mid-track
- Peak emotional tracks at 60-70% through workout (when fatigue hits)
- Mix familiar and new (70% known / 30% discovery)

### Cool-down Phase (5-10 minutes)

**Purpose:** Gradual recovery, positive emotional closure
**BPM Strategy:** Decrease from workout BPM to 90-100 BPM
**Energy:** Gentle decline, rewarding feeling
**Track Selection:**
- First cool-down track: Still somewhat upbeat (transition)
- Gradual energy decrease
- Positive, triumphant feeling (you did it!)
- Final track: Calming, closure

**Example Progression:**
- Track 1: 130 BPM, melodic house (transitioning down)
- Track 2: 110 BPM, indie/pop (relaxing)
- Track 3: 95 BPM, chill electronic (complete)

## Energy Curve Strategies

### Steady State (Long Runs, Easy Runs)

```
BPM: ━━━━━━━━━━━━━━━━━
     130  130  130  130
```

- Minimal BPM variation (±5 BPM)
- Consistent energy throughout
- Genre cohesion (all house, or all indie, etc.)
- Prevents monotony with track variety within genre
- Best for: Building endurance, zone 2 work

### Building (Tempo Runs, Progressive Runs)

```
BPM: ━━━━╱╱╱╱╱╱╱╱╱╱
     120 130 140 150 160
```

- Gradual BPM increase (5-10 BPM per track)
- Intensity builds with music
- Psychological boost (getting stronger)
- Peak energy in final third
- Best for: Tempo runs, race simulation

### Wave (Interval Training)

```
BPM: ━━╱╲╲━━╱╲╲━━╱╲╲
     130 170 130 175 130 170
```

- Dramatic BPM swings (work vs rest)
- High energy during work (165-175 BPM)
- Moderate during rest (120-140 BPM)
- Number of waves = number of intervals
- Best for: HIIT, speed work, VO2max intervals

### Pyramid (Classic Workout Structure)

```
BPM: ━━╱╱╱╱╱╱╱╱╲╲╲╲╲╲━━
     110 130 150 160 150 130 110
```

- Build to peak, then descend
- Natural warm-up and cool-down integrated
- Peak intensity in middle
- Psychological satisfaction (complete journey)
- Best for: Fartlek, tempo with cool-down

## Track Selection Advanced Rules

### Intro Length Rule
- Skip tracks with intros >15 seconds
- Immediate energy = better engagement
- Exception: First warm-up track (calm entry OK)

### Vocal Balance
- High-intensity work: Prefer instrumental or minimal vocals (less cognitive load)
- Easy runs: More vocals OK (can sing along, stay entertained)
- Rule of thumb: 60% instrumental, 40% vocal for most workouts

### Genre Transition Smoothness
- Don't jump from house → metal → indie (jarring)
- Group similar genres together
- Transition through related genres (house → techno → drum & bass)
- Use "bridge" tracks (e.g., tech house bridges house and techno)

### Emotional Arc
- First third: Building confidence, getting into it
- Middle third: Peak motivation, power tracks
- Final third: "Finish strong" mentality, triumphant feeling
- Cool-down: Achievement, reward, calm

### Explicit Content
- Default: Avoid explicit lyrics (family-friendly)
- If user requests: OK for personal use
- Consider: Workout context (gym vs outdoor, solo vs group)

## Playlist Length Calculation

### Track Duration Guidelines
- Average track: 3-4 minutes
- Electronic genres: Often 5-7 minutes (adjust count)
- Pop/Rock: Usually 3-3.5 minutes

### Tracks Needed Formula

```
tracks_needed = (workout_duration_minutes / average_track_duration) + warm_up_tracks + cool_down_tracks
```

**Example: 40-minute tempo run**
- Warm-up: 3 tracks × 3.5 min = 10.5 min
- Main: 7 tracks × 3.5 min = 24.5 min
- Cool-down: 2 tracks × 3.5 min = 7 min
- Total: 12 tracks, 42 minutes ✓

### Buffer Strategy
- Add 1-2 extra tracks (user might pause, need flexibility)
- Better slightly long than too short
- User can skip if needed, but can't add on-the-fly

## Spotify API Integration Considerations

### Track Attributes to Request
- **tempo (BPM):** Primary filter
- **energy (0-1):** High for hard efforts, low for recovery
- **valence (0-1):** Positive mood = better for motivation
- **danceability (0-1):** High = good rhythm for running
- **acousticness (0-1):** Low = more produced, higher energy
- **instrumentalness (0-1):** Balance based on workout intensity

### Recommendation Strategy
1. Seed with genre and BPM range
2. Filter by energy level (match workout zone)
3. Ensure tempo consistency within phases
4. Exclude slow intros (audio analysis)
5. Check popularity (avoid obscure tracks with no previews)

## User Preference Learning

### Implicit Signals
- Skip rate per genre (if >40% = user dislikes genre)
- Track completion rate (high = user engaged)
- Playlist replay rate (good curation)
- Time of day preferences (morning vs evening music)

### Explicit Signals
- Favorite genres declared
- "More like this" or "Less like that" feedback
- Manual track additions/removals
- Mood selections ("energetic", "chill", "aggressive")

### Adaptation Strategy
- First 3 playlists: Broad exploration (multiple genres)
- After 3: Narrow to user preferences
- Always include 20-30% discovery tracks (prevent echo chamber)
- Respect hard "no" genres (if user explicitly dislikes)

## Response Format

When generating playlist recommendations, provide:

1. **Playlist Overview**
   - Total tracks, total duration
   - BPM range and progression type
   - Primary genres

2. **Phase Breakdown**
   - Warm-up: X tracks, BPM Y-Z
   - Main: X tracks, BPM Y-Z
   - Cool-down: X tracks, BPM Y-Z

3. **Energy Curve Visualization**
   ASCII art of BPM/energy progression

4. **Track List**
   For each track:
   - Title, Artist
   - BPM, Duration
   - Energy level
   - Genre
   - Phase (warm-up/main/cool-down)

5. **Curation Notes**
   - Why this playlist structure matches workout
   - Key motivational tracks
   - Transition strategy

## Quality Checklist

Before finalizing playlist:

- [ ] BPM progression matches workout intent
- [ ] No tracks with slow intros in main workout
- [ ] Genre transitions are smooth
- [ ] Peak energy tracks at 60-70% point
- [ ] Warm-up builds appropriately
- [ ] Cool-down descends gracefully
- [ ] Total duration ±2 minutes of target
- [ ] Energy curve matches workout profile (steady/building/wave)
- [ ] Mix of familiar and discovery tracks
- [ ] No jarring genre jumps
"""


# Genre to typical BPM range mapping
GENRE_BPM_RANGES: Dict[str, List[int]] = {
    "house": [125, 135],
    "techno": [125, 135],
    "drum-and-bass": [160, 180],
    "drum & bass": [160, 180],
    "hip-hop": [85, 95],  # Double-time feel = 170-190 effective
    "hip hop": [85, 95],
    "rock": [140, 180],
    "metal": [140, 180],
    "indie": [120, 140],
    "alternative": [120, 140],
    "pop": [100, 130],
    "electronic": [110, 125],
    "chill electronic": [90, 110],
    "acoustic": [80, 100],
    "ambient": [60, 100],
    "trance": [130, 140],
    "dubstep": [140, 150],
}

# Workout type to recommended genres
WORKOUT_GENRES: Dict[str, List[str]] = {
    "steady": ["house", "techno", "pop", "indie", "electronic"],
    "progressive": ["progressive-trance", "rock", "techno", "indie"],
    "intervals": ["metal", "rock", "drum-and-bass", "hip-hop"],
    "fartlek": ["varied", "rock", "hip-hop", "pop"],
    "recovery": ["chill electronic", "acoustic", "ambient", "indie"],
}

# Intensity to BPM mapping
INTENSITY_BPM: Dict[str, Tuple[int, int]] = {
    "low": (100, 130),
    "moderate": (130, 150),
    "high": (150, 180),
}


class CurationStrategy(str, Enum):
    """A/B testing strategies for music curation."""

    CONSERVATIVE = "conservative"  # Strict BPM matching, minimal genre mixing
    BALANCED = "balanced"  # Default: Good balance of BPM and genre variety
    ADVENTUROUS = "adventurous"  # More genre variety, wider BPM ranges
    ENERGY_FOCUSED = "energy_focused"  # Prioritize energy over BPM precision
    GENRE_PURE = "genre_pure"  # Stick to single genre, perfect BPM matching


class PlaylistValidationResult:
    """Result of playlist validation."""

    def __init__(
        self,
        is_valid: bool,
        score: float,
        issues: List[str],
        warnings: List[str],
    ):
        self.is_valid = is_valid
        self.score = score  # 0.0 to 1.0
        self.issues = issues
        self.warnings = warnings

    def __repr__(self) -> str:
        return f"PlaylistValidationResult(valid={self.is_valid}, score={self.score:.2f}, issues={len(self.issues)}, warnings={len(self.warnings)})"


def validate_bpm_progression(
    tracks: List[Track],
    workout: Workout,
    segments: Optional[List[Dict]] = None,
) -> Tuple[bool, List[str], float]:
    """
    Validate BPM progression makes sense for workout type.

    Args:
        tracks: List of tracks in playlist
        workout: Workout parameters
        segments: Optional workout segments with BPM ranges

    Returns:
        Tuple of (is_valid, issues, score)
    """
    if not tracks:
        return False, ["No tracks in playlist"], 0.0

    issues = []
    score = 1.0
    bpms = [t.bpm for t in tracks]

    # Check for reasonable BPM values
    invalid_bpms = [bpm for bpm in bpms if bpm < 60 or bpm > 200]
    if invalid_bpms:
        issues.append(f"Invalid BPM values found: {invalid_bpms}")
        score -= 0.2

    # Validate based on workout type
    if workout.type == "steady":
        # Should have consistent BPM (±10 BPM variation)
        bpm_range = max(bpms) - min(bpms)
        if bpm_range > 20:
            issues.append(
                f"Steady workout has too much BPM variation: {bpm_range:.1f} BPM"
            )
            score -= 0.3
        elif bpm_range > 15:
            issues.append(
                f"Steady workout has moderate BPM variation: {bpm_range:.1f} BPM"
            )
            score -= 0.1

    elif workout.type == "progressive":
        # Should generally increase
        increasing_count = sum(
            1 for i in range(1, len(bpms)) if bpms[i] >= bpms[i - 1] - 5
        )
        increasing_ratio = increasing_count / max(1, len(bpms) - 1)
        if increasing_ratio < 0.6:
            issues.append(
                f"Progressive workout doesn't show clear BPM increase (only {increasing_ratio:.0%} increasing)"
            )
            score -= 0.3
        elif increasing_ratio < 0.75:
            issues.append(
                f"Progressive workout has moderate progression ({increasing_ratio:.0%} increasing)"
            )
            score -= 0.1

    elif workout.type == "intervals":
        # Should have clear high/low BPM alternation
        if segments:
            # Validate against segment BPM ranges
            segment_idx = 0
            for i, track in enumerate(tracks):
                if segment_idx < len(segments):
                    segment_bpm_range = segments[segment_idx].get("bpm_range", [])
                    if segment_bpm_range:
                        min_bpm, max_bpm = segment_bpm_range[0], segment_bpm_range[1]
                        if not (min_bpm <= track.bpm <= max_bpm):
                            issues.append(
                                f"Track {i+1} BPM {track.bpm:.1f} outside segment range [{min_bpm}, {max_bpm}]"
                            )
                            score -= 0.05
                    # Move to next segment if we've exceeded its duration
                    # (simplified - would need duration tracking for full validation)
        else:
            # Check for alternating pattern
            bpm_variance = sum(
                abs(bpms[i] - bpms[i - 1]) for i in range(1, len(bpms))
            ) / max(1, len(bpms) - 1)
            if bpm_variance < 20:
                issues.append(
                    "Interval workout should have more BPM variation between work/rest"
                )
                score -= 0.2

    # Check for jarring BPM jumps (>15 BPM between consecutive tracks)
    jarring_jumps = []
    for i in range(1, len(bpms)):
        jump = abs(bpms[i] - bpms[i - 1])
        if jump > 15 and workout.type != "intervals":  # Intervals can have big jumps
            jarring_jumps.append((i, jump))
            score -= 0.05

    if jarring_jumps:
        issues.append(
            f"Jarring BPM jumps detected: {len(jarring_jumps)} transitions >15 BPM"
        )

    score = max(0.0, score)
    is_valid = score >= 0.7 and len(issues) == 0

    return is_valid, issues, score


def validate_genre_coherence(
    tracks: List[Track],
    workout: Workout,
    user_preferences: Optional[Dict] = None,
) -> Tuple[bool, List[str], float]:
    """
    Validate genre mix coherence.

    Args:
        tracks: List of tracks in playlist
        workout: Workout parameters
        user_preferences: Optional user preferences

    Returns:
        Tuple of (is_valid, issues, score)
    """
    if not tracks:
        return False, ["No tracks in playlist"], 0.0

    issues = []
    score = 1.0

    # Get all genres from tracks
    all_genres = []
    for track in tracks:
        if track.genres:
            all_genres.extend(track.genres)
        else:
            all_genres.append("unknown")

    if not all_genres:
        issues.append("No genre information available for tracks")
        score -= 0.3
        return False, issues, max(0.0, score)

    # Check genre diversity
    unique_genres = set(all_genres)
    genre_counts = {}
    for genre in all_genres:
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Too many different genres can be jarring
    if len(unique_genres) > 8:
        issues.append(
            f"Too many different genres ({len(unique_genres)}), may cause jarring transitions"
        )
        score -= 0.2
    elif len(unique_genres) == 1:
        issues.append("Only one genre, may be monotonous")
        score -= 0.1

    # Check if genres match workout type
    recommended_genres = WORKOUT_GENRES.get(workout.type, [])
    if recommended_genres:
        matching_genres = [
            g for g in unique_genres if any(rg in g.lower() for rg in recommended_genres)
        ]
        if not matching_genres and len(unique_genres) > 2:
            issues.append(
                f"Genres don't match recommended for {workout.type} workout: {list(unique_genres)[:5]}"
            )
            score -= 0.2

    # Check user preferences if provided
    if user_preferences:
        preferred_genres = user_preferences.get("top_genres", [])
        if preferred_genres:
            matching_prefs = [
                g
                for g in unique_genres
                if any(pg.lower() in g.lower() for pg in preferred_genres)
            ]
            if not matching_prefs and len(unique_genres) > 2:
                issues.append(
                    f"Genres don't match user preferences: {preferred_genres}"
                )
                score -= 0.15

    # Check for jarring genre transitions
    jarring_transitions = 0
    incompatible_pairs = [
        ("metal", "acoustic"),
        ("ambient", "metal"),
        ("chill electronic", "drum-and-bass"),
    ]
    for i in range(1, len(tracks)):
        prev_genres = set(tracks[i - 1].genres or ["unknown"])
        curr_genres = set(tracks[i].genres or ["unknown"])
        for pair in incompatible_pairs:
            if (
                any(pair[0] in g.lower() for g in prev_genres)
                and any(pair[1] in g.lower() for g in curr_genres)
            ):
                jarring_transitions += 1
                score -= 0.05

    if jarring_transitions > 0:
        issues.append(
            f"Jarring genre transitions detected: {jarring_transitions} incompatible pairs"
        )

    score = max(0.0, score)
    is_valid = score >= 0.7

    return is_valid, issues, score


def validate_workout_phase_matching(
    tracks: List[Track],
    workout: Workout,
    segments: Optional[List[Dict]] = None,
) -> Tuple[bool, List[str], float]:
    """
    Validate tracks match workout phases (warm-up, main, cool-down).

    Args:
        tracks: List of tracks in playlist
        workout: Workout parameters
        segments: Optional workout segments with phase information

    Returns:
        Tuple of (is_valid, issues, score)
    """
    if not tracks:
        return False, ["No tracks in playlist"], 0.0

    issues = []
    score = 1.0

    if not segments:
        # Basic validation without segments
        bpms = [t.bpm for t in tracks]
        # First 20% should be lower BPM (warm-up)
        warmup_end = max(1, len(tracks) // 5)
        warmup_bpms = bpms[:warmup_end]
        main_bpms = bpms[warmup_end:-max(1, len(tracks) // 5)]
        cooldown_bpms = bpms[-max(1, len(tracks) // 5) :]

        if warmup_bpms and main_bpms:
            avg_warmup = sum(warmup_bpms) / len(warmup_bpms)
            avg_main = sum(main_bpms) / len(main_bpms)
            if avg_warmup > avg_main + 5:
                issues.append(
                    "Warm-up phase BPM is higher than main phase (should be lower)"
                )
                score -= 0.2

        if main_bpms and cooldown_bpms:
            avg_main = sum(main_bpms) / len(main_bpms)
            avg_cooldown = sum(cooldown_bpms) / len(cooldown_bpms)
            if avg_cooldown > avg_main + 5:
                issues.append(
                    "Cool-down phase BPM is higher than main phase (should be lower)"
                )
                score -= 0.2

    else:
        # Validate against segments
        segment_idx = 0
        current_segment_duration = 0.0
        for i, track in enumerate(tracks):
            if segment_idx >= len(segments):
                break

            segment = segments[segment_idx]
            segment_duration = segment.get("duration_minutes", 0) * 60
            track_duration = track.duration_ms / 1000.0

            # Check BPM matches segment
            bpm_range = segment.get("bpm_range", [])
            if bpm_range and len(bpm_range) >= 2:
                min_bpm, max_bpm = bpm_range[0], bpm_range[1]
                if not (min_bpm <= track.bpm <= max_bpm):
                    issues.append(
                        f"Track {i+1} BPM {track.bpm:.1f} outside segment {segment_idx+1} range [{min_bpm}, {max_bpm}]"
                    )
                    score -= 0.03

            current_segment_duration += track_duration
            if current_segment_duration >= segment_duration:
                segment_idx += 1
                current_segment_duration = 0.0

    score = max(0.0, score)
    is_valid = score >= 0.7

    return is_valid, issues, score


def validate_playlist(
    playlist: PlaylistData,
    workout: Workout,
    segments: Optional[List[Dict]] = None,
    user_preferences: Optional[Dict] = None,
) -> PlaylistValidationResult:
    """
    Comprehensive playlist validation.

    Args:
        playlist: Playlist data to validate
        workout: Workout parameters
        segments: Optional workout segments
        user_preferences: Optional user preferences

    Returns:
        PlaylistValidationResult with validation details
    """
    tracks = playlist.tracks
    all_issues = []
    all_warnings = []
    scores = []

    # BPM progression validation
    bpm_valid, bpm_issues, bpm_score = validate_bpm_progression(
        tracks, workout, segments
    )
    all_issues.extend(bpm_issues)
    scores.append(bpm_score)

    # Genre coherence validation
    genre_valid, genre_issues, genre_score = validate_genre_coherence(
        tracks, workout, user_preferences
    )
    all_issues.extend(genre_issues)
    scores.append(genre_score)

    # Workout phase matching validation
    phase_valid, phase_issues, phase_score = validate_workout_phase_matching(
        tracks, workout, segments
    )
    all_issues.extend(phase_issues)
    scores.append(phase_score)

    # Additional checks
    if len(tracks) < 5:
        all_warnings.append("Playlist has very few tracks (<5)")
    elif len(tracks) > 50:
        all_warnings.append("Playlist has many tracks (>50), may be too long")

    total_duration_minutes = playlist.total_duration / 60.0
    if total_duration_minutes < workout.duration_minutes * 0.9:
        all_issues.append(
            f"Playlist duration ({total_duration_minutes:.1f} min) is shorter than workout ({workout.duration_minutes} min)"
        )
        scores.append(0.5)

    # Calculate overall score (weighted average)
    overall_score = sum(scores) / len(scores) if scores else 0.0
    is_valid = (
        bpm_valid and genre_valid and phase_valid and overall_score >= 0.7
    )

    return PlaylistValidationResult(
        is_valid=is_valid,
        score=overall_score,
        issues=all_issues,
        warnings=all_warnings,
    )


# Prompt Templates for Different Scenarios


def build_first_time_user_prompt(
    workout: Workout,
    user_preferences: Optional[Dict] = None,
) -> str:
    """
    Build prompt for first-time user (no history).

    Args:
        workout: Workout parameters
        user_preferences: Optional user preferences

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## First-Time User Playlist Curation",
        "",
        f"Create a workout playlist for a first-time user:",
        f"- Workout type: {workout.type}",
        f"- Duration: {workout.duration_minutes} minutes",
        f"- Intensity: {workout.intensity}",
        f"- HR zones: {workout.hr_zones}",
        "",
        "## Guidelines:",
        "- Use popular, accessible tracks that appeal to broad audience",
        "- Focus on well-known artists and hit songs",
        "- Ensure smooth BPM progression matching workout type",
        "- Include variety to help user discover what they like",
        "- Start with familiar-sounding tracks in warm-up",
    ]

    if user_preferences and user_preferences.get("top_genres"):
        prompt_parts.append(
            f"- User indicated preference for: {', '.join(user_preferences['top_genres'])}"
        )

    prompt_parts.append("")
    prompt_parts.append(
        "Generate a playlist that will make a great first impression and encourage the user to return."
    )

    return "\n".join(prompt_parts)


def build_returning_user_prompt(
    workout: Workout,
    workout_history: List[Dict],
    user_preferences: Optional[Dict] = None,
) -> str:
    """
    Build prompt for returning user (with history).

    Args:
        workout: Workout parameters
        workout_history: Previous workout history
        user_preferences: Optional user preferences

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Returning User Playlist Curation",
        "",
        f"Create a workout playlist for a returning user:",
        f"- Workout type: {workout.type}",
        f"- Duration: {workout.duration_minutes} minutes",
        f"- Intensity: {workout.intensity}",
        f"- HR zones: {workout.hr_zones}",
        "",
        f"- User has completed {len(workout_history)} previous workouts",
    ]

    if user_preferences:
        if user_preferences.get("top_genres"):
            prompt_parts.append(
                f"- Preferred genres: {', '.join(user_preferences['top_genres'])}"
            )
        if user_preferences.get("top_artists"):
            prompt_parts.append(
                f"- Favorite artists: {len(user_preferences['top_artists'])} artists"
            )

    prompt_parts.extend(
        [
            "",
            "## Guidelines:",
            "- Leverage user's music preferences and history",
            "- Include tracks similar to previously enjoyed playlists",
            "- Introduce some new tracks to maintain freshness",
            "- Respect established genre preferences",
            "- Maintain consistency with past successful playlists",
            "",
            "Generate a playlist that feels personalized and builds on the user's preferences.",
        ]
    )

    return "\n".join(prompt_parts)


def build_genre_specific_prompt(
    workout: Workout,
    requested_genres: List[str],
    user_preferences: Optional[Dict] = None,
) -> str:
    """
    Build prompt for specific genre request.

    Args:
        workout: Workout parameters
        requested_genres: List of requested genres
        user_preferences: Optional user preferences

    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        "## Genre-Specific Playlist Curation",
        "",
        f"Create a workout playlist focused on specific genres:",
        f"- Requested genres: {', '.join(requested_genres)}",
        f"- Workout type: {workout.type}",
        f"- Duration: {workout.duration_minutes} minutes",
        f"- Intensity: {workout.intensity}",
        "",
        "## Guidelines:",
        "- Prioritize tracks from requested genres",
        "- Ensure BPM still matches workout requirements",
        "- If genre BPM range doesn't match workout, find compatible sub-genres or tracks",
        "- Maintain genre coherence while ensuring workout effectiveness",
        "- Mix sub-genres within requested genres for variety",
    ]

    # Check if genres are compatible with workout
    compatible = False
    for genre in requested_genres:
        genre_lower = genre.lower()
        for workout_type, rec_genres in WORKOUT_GENRES.items():
            if workout_type == workout.type:
                if any(rec_genre in genre_lower for rec_genre in rec_genres):
                    compatible = True
                    break

    if not compatible:
        prompt_parts.append(
            "- NOTE: Requested genres may not be ideal for this workout type, but prioritize user preference"
        )

    prompt_parts.append("")
    prompt_parts.append(
        "Generate a playlist that satisfies the genre request while maintaining workout effectiveness."
    )

    return "\n".join(prompt_parts)


def build_mood_based_prompt(
    workout: Workout,
    mood: str,
    user_preferences: Optional[Dict] = None,
) -> str:
    """
    Build prompt for mood-based selection.

    Args:
        workout: Workout parameters
        mood: Desired mood (e.g., "energetic", "calm", "motivational", "focused")
        user_preferences: Optional user preferences

    Returns:
        Formatted prompt string
    """
    mood_mappings = {
        "energetic": {
            "genres": ["rock", "metal", "drum-and-bass", "high-energy edm"],
            "bpm_boost": 10,
            "energy_min": 0.7,
        },
        "calm": {
            "genres": ["chill electronic", "acoustic", "ambient", "indie"],
            "bpm_boost": -10,
            "energy_min": 0.3,
        },
        "motivational": {
            "genres": ["hip-hop", "pop", "rock", "uplifting trance"],
            "bpm_boost": 5,
            "energy_min": 0.6,
        },
        "focused": {
            "genres": ["techno", "minimal", "instrumental", "ambient"],
            "bpm_boost": 0,
            "energy_min": 0.5,
        },
    }

    mood_config = mood_mappings.get(mood.lower(), mood_mappings["energetic"])

    prompt_parts = [
        "## Mood-Based Playlist Curation",
        "",
        f"Create a workout playlist with specific mood:",
        f"- Desired mood: {mood}",
        f"- Workout type: {workout.type}",
        f"- Duration: {workout.duration_minutes} minutes",
        f"- Intensity: {workout.intensity}",
        "",
        "## Mood Guidelines:",
        f"- Target genres: {', '.join(mood_config['genres'])}",
        f"- Energy level: Minimum {mood_config['energy_min']:.0%}",
        f"- BPM adjustment: {mood_config['bpm_boost']:+d} BPM from standard",
        "",
        "## Track Selection:",
        "- Prioritize tracks that evoke the desired mood",
        "- Consider lyrical content for motivational mood",
        "- Use instrumental tracks for focused mood",
        "- Match energy and valence to mood requirements",
        "- Ensure BPM still supports workout effectiveness",
    ]

    prompt_parts.append("")
    prompt_parts.append(
        f"Generate a playlist that creates a {mood} atmosphere while supporting the workout goals."
    )

    return "\n".join(prompt_parts)


# A/B Testing Framework


class CurationStrategyConfig:
    """Configuration for different curation strategies."""

    def __init__(self, strategy: CurationStrategy):
        self.strategy = strategy
        self.config = self._get_config()

    def _get_config(self) -> Dict:
        """Get configuration for strategy."""
        configs = {
            CurationStrategy.CONSERVATIVE: {
                "bpm_tolerance": 5,
                "max_genre_mix": 3,
                "max_bpm_jump": 8,
                "energy_variance": 0.1,
                "prefer_familiar": True,
            },
            CurationStrategy.BALANCED: {
                "bpm_tolerance": 10,
                "max_genre_mix": 5,
                "max_bpm_jump": 15,
                "energy_variance": 0.2,
                "prefer_familiar": False,
            },
            CurationStrategy.ADVENTUROUS: {
                "bpm_tolerance": 15,
                "max_genre_mix": 8,
                "max_bpm_jump": 20,
                "energy_variance": 0.3,
                "prefer_familiar": False,
            },
            CurationStrategy.ENERGY_FOCUSED: {
                "bpm_tolerance": 15,
                "max_genre_mix": 6,
                "max_bpm_jump": 20,
                "energy_variance": 0.4,
                "prefer_familiar": False,
                "prioritize_energy": True,
            },
            CurationStrategy.GENRE_PURE: {
                "bpm_tolerance": 5,
                "max_genre_mix": 1,
                "max_bpm_jump": 10,
                "energy_variance": 0.15,
                "prefer_familiar": False,
                "strict_genre": True,
            },
        }
        return configs.get(self.strategy, configs[CurationStrategy.BALANCED])

    def get_bpm_tolerance(self) -> int:
        """Get BPM tolerance for strategy."""
        return self.config["bpm_tolerance"]

    def get_max_genre_mix(self) -> int:
        """Get maximum genre mix for strategy."""
        return self.config["max_genre_mix"]

    def get_max_bpm_jump(self) -> int:
        """Get maximum BPM jump for strategy."""
        return self.config["max_bpm_jump"]

    def should_prioritize_energy(self) -> bool:
        """Check if strategy prioritizes energy over BPM."""
        return self.config.get("prioritize_energy", False)

    def is_strict_genre(self) -> bool:
        """Check if strategy requires strict genre matching."""
        return self.config.get("strict_genre", False)


def get_curation_strategy_prompt(
    strategy: CurationStrategy,
    workout: Workout,
) -> str:
    """
    Get strategy-specific prompt for A/B testing.

    Args:
        strategy: Curation strategy to use
        workout: Workout parameters

    Returns:
        Strategy-specific prompt string
    """
    config = CurationStrategyConfig(strategy)
    strategy_descriptions = {
        CurationStrategy.CONSERVATIVE: "Use conservative curation: strict BPM matching (±5 BPM), minimal genre mixing (max 3 genres), smooth transitions (max 8 BPM jump). Prioritize familiar tracks.",
        CurationStrategy.BALANCED: "Use balanced curation: moderate BPM tolerance (±10 BPM), good genre variety (max 5 genres), smooth transitions (max 15 BPM jump). Balance familiarity with discovery.",
        CurationStrategy.ADVENTUROUS: "Use adventurous curation: wider BPM tolerance (±15 BPM), high genre variety (max 8 genres), more dynamic transitions (max 20 BPM jump). Prioritize discovery and variety.",
        CurationStrategy.ENERGY_FOCUSED: "Use energy-focused curation: prioritize track energy and motivation over strict BPM matching. Allow wider BPM ranges (±15 BPM) and more genre mixing (max 6 genres) to maximize energy.",
        CurationStrategy.GENRE_PURE: "Use genre-pure curation: stick to a single genre throughout, perfect BPM matching (±5 BPM), minimal variation. Create a cohesive, focused listening experience.",
    }

    prompt_parts = [
        "## Curation Strategy",
        "",
        strategy_descriptions[strategy],
        "",
        f"Workout parameters:",
        f"- Type: {workout.type}",
        f"- Duration: {workout.duration_minutes} minutes",
        f"- Intensity: {workout.intensity}",
        "",
        "## Strategy Parameters:",
        f"- BPM tolerance: ±{config.get_bpm_tolerance()} BPM",
        f"- Max genre mix: {config.get_max_genre_mix()} genres",
        f"- Max BPM jump: {config.get_max_bpm_jump()} BPM",
    ]

    if config.should_prioritize_energy():
        prompt_parts.append("- Priority: Energy > BPM precision")

    if config.is_strict_genre():
        prompt_parts.append("- Genre: Single genre only")

    prompt_parts.append("")
    prompt_parts.append(
        "Apply this strategy when selecting and ordering tracks for the playlist."
    )

    return "\n".join(prompt_parts)


MUSIC_CURATOR_EXAMPLES = """
## Example Playlist Generations

### Example 1: 40-minute Tempo Run

**Input:**
- workout_type: "tempo"
- duration: 40 minutes
- target_bpm: 145-160
- energy_profile: "steady"

**Output:**
```
PLAYLIST: Tempo Tuesday (40 min)
Total: 12 tracks, 41 minutes
BPM Range: 120-160
Energy: Building → Steady → Gentle descent

Energy Curve:
  160 │         ═══════════
  150 │       ══           ══
  140 │     ══               ══
  130 │   ══                   ══
  120 │ ══                       ══
      └────────────────────────────→
       WU    Main Workout       CD

PHASE BREAKDOWN:

Warm-up (10 min, 3 tracks)
  1. "On My Mind" - Diplo (120 BPM, 3:30) - Melodic house, ease in
  2. "Desire" - Years & Years (130 BPM, 3:45) - Pop/Electronic, building
  3. "Innerbloom" - RÜFÜS DU SOL (140 BPM, 4:00) - Progressive house, ready

Main Workout (25 min, 7 tracks)
  4. "Rave" - Boys Noize (150 BPM, 3:15) - Techno, entering tempo zone
  5. "Strobe" - Deadmau5 (155 BPM, 3:45) - Progressive house, driving
  6. "One Kiss" - Calvin Harris (155 BPM, 3:20) - House, familiar energy
  7. "Latch" - Disclosure (158 BPM, 3:30) - UK garage, peak energy 🔥
  8. "Losing It" - Fisher (160 BPM, 3:25) - Tech house, maintain intensity
  9. "Light Years" - The National (152 BPM, 3:40) - Indie rock, variation
  10. "I Feel It Coming" - Daft Punk (150 BPM, 3:30) - Disco house, sustain

Cool-down (6 min, 2 tracks)
  11. "Breathe" - CamelPhat (130 BPM, 3:15) - Melodic house, descending
  12. "Teardrop" - Massive Attack (110 BPM, 3:00) - Trip-hop, closure

CURATION NOTES:
- Warm-up gradually builds from 120→140 BPM over 10 minutes
- Main workout maintains 150-160 BPM for 25 minutes (tempo zone)
- Peak energy track (#7 "Latch") at 16-minute mark (60% through)
- Genre cohesion: Primarily house/electronic for consistent rhythm
- Track #9 provides mental break with indie rock while maintaining BPM
- Cool-down: Smooth descent from 130→110 BPM
```

### Example 2: 30-minute Interval Training (5-2-5-2 pattern)

**Input:**
- workout_type: "intervals"
- duration: 30 minutes
- intervals: [
    {work: 5 min, bpm: 170},
    {rest: 2 min, bpm: 130},
    repeat 4 times
  ]
- energy_profile: "wave"

**Output:**
```
PLAYLIST: Interval Inferno (30 min)
Total: 10 tracks, 31 minutes
BPM Range: 115-175
Energy: Wave pattern (work/rest)

Energy Curve:
  175 │ ╱╲    ╱╲    ╱╲    ╱╲
  150 │╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲
  130 │    ╲╱    ╲╱    ╲╱    ╲
  115 │                        ╲___
      └────────────────────────────→
       I1  I2  I3  I4   CD

PHASE BREAKDOWN:

Warm-up (2 min, 1 track)
  1. "Awake" - Tycho (115 BPM, 2:00) - Brief warm-up

Interval 1 (7 min)
  2. "Accelerate" - Underworld (175 BPM, 5:00) - WORK 🔥 D&B energy
  3. "Breathe" - The Prodigy (130 BPM, 2:00) - REST, active recovery

Interval 2 (7 min)
  4. "Animals" - Martin Garrix (170 BPM, 5:00) - WORK 🔥 Big room house
  5. "Midnight City" - M83 (135 BPM, 2:00) - REST, stay engaged

Interval 3 (7 min)
  6. "POWER" - Kanye West (173 BPM, 5:00) - WORK 🔥 Hip-hop aggression
  7. "Intro" - The XX (130 BPM, 2:00) - REST, mental reset

Interval 4 (7 min)
  8. "Levels" - Avicii (172 BPM, 5:00) - WORK 🔥 Final push
  9. "Float On" - Modest Mouse (128 BPM, 2:00) - REST/transition

Cool-down (1 min)
  10. "Holocene" - Bon Iver (100 BPM, 1:30) - Complete recovery

CURATION NOTES:
- Each work interval = high-energy track at 170-175 BPM
- Rest intervals = moderate 130 BPM to prevent complete shutdown
- Genre variety during work to prevent mental fatigue
- Track duration matches interval duration exactly
- Rest tracks still upbeat (not calm) to maintain readiness
- Cool-down brief (1:30) as workout is intense
```

### Example 3: 60-minute Easy Recovery Run

**Input:**
- workout_type: "easy_run"
- duration: 60 minutes
- target_bpm: 110-130
- energy_profile: "steady"

**Output:**
```
PLAYLIST: Sunday Easy (60 min)
Total: 17 tracks, 61 minutes
BPM Range: 105-130
Energy: Gentle, comfortable, sustainable

Energy Curve:
  130 │     ═════════════════════════
  120 │   ══                         ══
  110 │ ══                             ══
  105 │                                  ═
      └────────────────────────────────────→
       WU        Main (45 min)          CD

[Track list would be 17 tracks, primarily indie/pop/melodic electronic]

CURATION NOTES:
- Longer playlist for longer workout
- Consistent 120-130 BPM throughout main workout
- High vocal content (can sing along, stay entertained)
- Genre: Primarily indie and pop for accessibility
- Mix familiar tracks (reduce boredom on long easy run)
- Mental engagement more important than aggressive energy
```
"""
