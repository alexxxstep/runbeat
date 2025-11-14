"""
Rule-based parser for workout intent extraction.

Uses regex patterns and keyword matching to extract workout parameters
from user messages without requiring AI.
"""
import re
from typing import Optional, Dict, List, Tuple
from loguru import logger

from app.schemas.llm_responses import WorkoutIntent


class RuleBasedParser:
    """Rule-based parser for extracting workout intent from messages."""

    # Duration patterns (in order of specificity)
    # Format: (pattern, multiplier) where multiplier is applied to extracted number
    DURATION_PATTERNS = [
        (r'(\d+)\s*хвилин', 1),  # "55 хвилин" → 55
        (r'(\d+)\s*хв', 1),  # "55 хв" → 55
        (r'(\d+)\s*год', 60),  # "1 годину" → 60 minutes
        (r'(\d+)\s*годин', 60),  # "1 годину" → 60 minutes
        ('півгодини', 30),  # "півгодини" → 30 minutes (fixed string)
        ('пів години', 30),  # "пів години" → 30 minutes (fixed string)
        ('година', 60),  # "година" → 60 minutes (fixed string)
        ('годину', 60),  # "годину" → 60 minutes (fixed string)
    ]

    # Intensity keywords mapped to BPM ranges
    INTENSITY_KEYWORDS = {
        'low': {
            'keywords': [
                'легкий', 'легка', 'легку', 'легкому', 'легке',
                'easy', 'recovery', 'відновлення', 'відновлювальна',
                'спокійний', 'спокійна', 'спокійну',
            ],
            'bpm_range': (110, 130),
        },
        'moderate': {
            'keywords': [
                'темповий', 'tempo', 'помірний', 'moderate',
                'середній', 'середня', 'середню',
            ],
            'bpm_range': (130, 160),
        },
        'high': {
            'keywords': [
                'швидкий', 'fast', 'інтервали', 'intervals',
                'висока', 'високий', 'інтенсивне', 'інтенсивна',
                'швидко', 'агресивний', 'агресивна',
            ],
            'bpm_range': (160, 180),
        },
    }

    # Workout type keywords
    WORKOUT_TYPE_KEYWORDS = {
        'continuous': [
            'біг', 'пробіжка', 'run', 'running', 'steady',
            'стабільний', 'стабільна', 'постійний', 'постійна',
        ],
        'intervals': [
            'інтервали', 'intervals', 'інтервальний', 'інтервальна',
            'інтервальна пробіжка',
        ],
        'fartlek': [
            'фартлек', 'fartlek',
        ],
        'recovery': [
            'відновлення', 'recovery', 'відновлювальний', 'відновлювальна',
        ],
    }

    # Music genre keywords
    MUSIC_GENRE_KEYWORDS = {
        'rock': ['рок', 'rock', 'рок-музика', 'рок-музику'],
        'electronic': ['електроніка', 'electronic', 'електронна', 'електронну', 'електроніку'],
        'hip-hop': ['хіп-хоп', 'hip-hop', 'hip hop', 'реп', 'rap'],
        'pop': ['поп', 'pop', 'поп-музика'],
        'metal': ['метал', 'metal'],
        'techno': ['техно', 'techno'],
        'house': ['хаус', 'house'],
        'jazz': ['джаз', 'jazz'],
        'classical': ['класика', 'classical', 'класична'],
    }

    # Music description keywords
    MUSIC_DESCRIPTION_KEYWORDS = [
        'мотивуюча', 'мотивуючу', 'мотивуючий',
        'агресивна', 'агресивний', 'агресивну',
        'спокійна', 'спокійний', 'спокійну',
        'енергійна', 'енергійний', 'енергійну',
        'ритмічна', 'ритмічний', 'ритмічну',
        'мелодійна', 'мелодійний',
    ]

    def parse(self, message: str) -> Optional[WorkoutIntent]:
        """
        Parse workout intent from message using rules.

        Args:
            message: User's message

        Returns:
            WorkoutIntent if parsing successful, None otherwise
        """
        message_lower = message.lower().strip()

        # Extract duration
        duration = self._extract_duration(message_lower)

        # Extract intensity
        intensity_info = self._extract_intensity(message_lower)

        # Extract workout type
        workout_type = self._extract_workout_type(message_lower)

        # Extract music preferences
        music_genres = self._extract_music_genres(message_lower)
        music_prompt = self._extract_music_prompt(message_lower, message)

        # Determine if we have enough information
        has_duration = duration is not None and duration >= 5
        has_intensity = intensity_info is not None

        # Special case: if workout type is explicitly mentioned (like "фартлек", "інтервали"),
        # we can infer intensity from workout type even if not explicitly stated
        if workout_type == 'intervals' or workout_type == 'fartlek':
            # Intervals and fartlek are typically high intensity
            if not has_intensity:
                intensity_info = {
                    'level': 'high',
                    'bpm_range': (160, 180),
                }
                has_intensity = True

        # If we have both duration and intensity, create intent
        if has_duration and has_intensity:
            bpm_min, bpm_max = intensity_info['bpm_range']
            confidence = 0.95  # High confidence for rule-based parsing

            # Check if intervals are needed
            intervals = None
            if workout_type == 'intervals':
                # For intervals, we need more info, so mark as needing clarification
                needs_clarification = True
                clarification_question = "Який буде інтервал роботи/відпочинку?"
            else:
                needs_clarification = False
                clarification_question = None

            intent = WorkoutIntent(
                workout_type=workout_type or 'continuous',
                duration_minutes=duration,
                target_bpm_min=bpm_min,
                target_bpm_max=bpm_max,
                intervals=intervals,
                energy_profile='steady' if workout_type != 'intervals' else 'wave',
                mood=None,
                music_genres=music_genres if music_genres else None,
                music_prompt=music_prompt,
                confidence=confidence,
                needs_clarification=needs_clarification,
                clarification_question=clarification_question,
            )

            logger.info(
                f"Rule-based parsing successful: "
                f"type={intent.workout_type}, duration={duration}, "
                f"bpm={bpm_min}-{bpm_max}, confidence={confidence}"
            )

            return intent

        # If we have partial info, return None to let AI handle it
        logger.debug(
            f"Rule-based parsing incomplete: "
            f"duration={duration}, intensity={intensity_info is not None}"
        )
        return None

    def _extract_duration(self, message: str) -> Optional[int]:
        """Extract duration in minutes from message."""
        for pattern, multiplier in self.DURATION_PATTERNS:
            # Check if pattern is a regex string (starts with r' and contains capture group)
            if isinstance(pattern, str) and pattern.startswith(r'(\d+'):
                # Regex pattern with capture group
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    number = int(match.group(1))
                    return number * multiplier
            elif isinstance(pattern, str) and not pattern.startswith('r'):
                # Fixed string pattern (like "півгодини")
                if pattern in message:
                    return multiplier

        return None

    def _extract_intensity(self, message: str) -> Optional[Dict[str, Tuple[int, int]]]:
        """Extract intensity and return BPM range."""
        for intensity_level, data in self.INTENSITY_KEYWORDS.items():
            for keyword in data['keywords']:
                if keyword in message:
                    return {
                        'level': intensity_level,
                        'bpm_range': data['bpm_range'],
                    }

        return None

    def _extract_workout_type(self, message: str) -> Optional[str]:
        """Extract workout type from message."""
        # Check in order of specificity (more specific first)
        for workout_type, keywords in self.WORKOUT_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message:
                    return workout_type

        return None

    def _extract_music_genres(self, message: str) -> Optional[List[str]]:
        """Extract music genres from message."""
        genres = []
        for genre, keywords in self.MUSIC_GENRE_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                # But also check if keyword is in message (for compound words like "хіп-хоп")
                if keyword in message:
                    # Check if this genre is already added
                    if genre not in genres:
                        genres.append(genre)
                    break  # Only check each genre once

        return genres if genres else None

    def _extract_music_prompt(self, message_lower: str, original_message: str) -> Optional[str]:
        """Extract music description/prompt from message."""
        # Look for music-related phrases
        music_phrases = [
            'під', 'для', 'з', 'музика', 'музику', 'музики',
        ]

        # Check if message contains music-related keywords
        has_music_context = any(
            phrase in message_lower for phrase in music_phrases)

        if not has_music_context:
            return None

        # Extract descriptive words
        descriptions = []
        for keyword in self.MUSIC_DESCRIPTION_KEYWORDS:
            if keyword in message_lower:
                descriptions.append(keyword)

        if descriptions:
            # Return the first description found
            return descriptions[0]

        return None
