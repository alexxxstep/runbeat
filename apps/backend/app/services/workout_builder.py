from app.schemas.conversation import ConversationState, ConversationUpdate
from loguru import logger
import re

class WorkoutBuilder:
    """
    A service to guide the user through creating a workout conversationally.
    This version uses natural language understanding to parse user messages.
    """

    async def process_message(
        self, state: ConversationState, user_message: str
    ) -> ConversationUpdate:
        """
        Processes a user's message, updates the state, and returns the next response.
        """
        state.history.append({"role": "user", "content": user_message})

        # Detect language for the response
        lang = "en" if re.search(r'[a-zA-Z]', user_message) else "uk"

        # Parse the user message to extract workout parameters
        parsed_params = self._parse_user_message(user_message)
        if parsed_params:
            state.collected_parameters.update(parsed_params)

        # Determine the next step and generate a response
        response_message = self._get_next_response(state, lang)

        state.history.append({"role": "assistant", "content": response_message})
        return ConversationUpdate(new_state=state, response_message=response_message)

    def _parse_user_message(self, message: str) -> dict:
        """
        A simple rule-based parser to extract workout parameters from a message.
        This simulates a more complex LLM-based parser.
        """
        params = {}
        message_lower = message.lower()

        # Parse duration
        duration_match = re.search(r'(\d+)\s*(хв|хвилин|min|minutes)', message_lower)
        if duration_match:
            params["duration_minutes"] = int(duration_match.group(1))

        # Parse intensity
        if any(k in message_lower for k in ["легк", "easy"]):
            params["intensity"] = "low"
        elif any(k in message_lower for k in ["середн", "moderate", "темпов"]):
            params["intensity"] = "moderate"
        elif any(k in message_lower for k in ["важк", "висок", "high", "hard"]):
            params["intensity"] = "high"

        # Default workout type for now
        if params.get("duration_minutes") or params.get("intensity"):
            params["type"] = "steady" # default

        # Parse genres
        # A simple placeholder. A real implementation would be more robust.
        possible_genres = ["rock", "pop", "classic", "electronic", "рок", "поп", "класика", "електро"]
        found_genres = [g for g in possible_genres if g in message_lower]
        if found_genres:
            params["genres"] = found_genres

        logger.debug(f"Parsed parameters: {params} from message: '{message}'")
        return params

    def _get_next_response(self, state: ConversationState, lang: str) -> str:
        """
        Determines the next response based on the collected parameters.
        """
        collected = state.collected_parameters

        # 1. Check if goal (type, duration, intensity) is defined
        if not all(k in collected for k in ["type", "duration_minutes", "intensity"]):
            state.last_question = "goal_clarification"
            if lang == "uk":
                return "Чудово! Щоб підібрати воркаут, уточніть, будь ласка, його тривалість та інтенсивність (наприклад, 'легка пробіжка 30 хвилин')."
            else:
                return "Great! To create a workout, please specify its duration and intensity (e.g., '30 minute easy run')."

        # 2. Check if music genres are defined
        if "genres" not in collected or not collected["genres"]:
            state.last_question = "genres"
            if lang == "uk":
                return "Зрозуміло. Якій музиці ви надаєте перевагу? Можна назвати кілька жанрів."
            else:
                return "Got it. What kind of music do you prefer? You can list a few genres."

        # 3. If everything is collected, ask for confirmation
        state.last_question = "final_confirmation"

        duration = collected.get('duration_minutes')
        intensity_map_uk = {"low": "легка", "moderate": "середня", "high": "висока"}
        intensity_map_en = {"low": "low", "moderate": "moderate", "high": "high"}
        intensity_uk = intensity_map_uk.get(collected.get('intensity'), 'не вказано')
        intensity_en = intensity_map_en.get(collected.get('intensity'), 'not specified')
        genres = ", ".join(collected.get('genres', []))

        if lang == "uk":
            return f"Ось що я зрозумів: пробіжка, інтенсивність – {intensity_uk}, тривалість – {duration} хвилин, під музику в стилі {genres}. Створюємо воркаут?"
        else:
            return f"Here's what I've got: a run with {intensity_en} intensity for {duration} minutes, with {genres} music. Shall I create the workout?"
