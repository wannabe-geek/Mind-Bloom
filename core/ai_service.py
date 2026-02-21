from google import genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def get_reflection(self, journal_content, user=None, history=None, mood_context=None):
        """
        Generates a calm AI reflection based on journal content, with historical context and persona.
        """
        if not self.client:
            return "AI service is currently unavailable. Reflect on your thoughts and breathe deeply."

        history_str = ""
        if history:
            history_str = "USER RECENT HISTORY (Memory):\n" + "\n".join([f"- {h}" for h in history])

        mood_str = f"CURRENT MOOD PROFILE: {mood_context}" if mood_context else ""

        # Use User's selected persona
        persona_map = {
            'ZEN': "ZEN GUIDE: Focus on mindfulness, breath, and the present moment. Be minimalist.",
            'STRATEGIST': "PRACTICAL STRATEGIST: Focus on actionable steps, energy management, and clear goals.",
            'LISTENER': "EMPATHETIC LISTENER: Focus on validation, emotional resonance, and kindness.",
            'CATALYST': "GROWTH CATALYST: Focus on long-term patterns, breakthroughs, and cognitive reframing."
        }
        
        persona_code = user.profile.ai_persona if user and hasattr(user, 'profile') else 'ZEN'
        active_mode = persona_map.get(persona_code, persona_map['ZEN'])

        prompt = f"""
        Identity: MindBloom's AI Companion (Growth Mentor). 
        Mode: {active_mode}
        Context: {history_str} | {mood_str}
        
        Recent Thought: "{journal_content}"
        
        Response: Provide a warm, high-insight reflection (2-3 sentences). Acknowledge patterns or growth. Avoid generic talk.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return "I'm here for you. Take your time to process these thoughts."

    def get_breakthrough_analysis(self, journal_history):
        """
        Analyzes a list of journal entries to identify recurring patterns and growth.
        """
        if not self.client or not journal_history:
            return None

        history_text = "\n".join([f"- {j.content}" for j in journal_history])
        
        prompt = f"""
        Analyze the following journal entries for a mental health breakthrough or significant growth pattern.
        
        JOURNAL ENTRIES:
        {history_text}
        
        Task:
        1. Identify ONE major recurring theme or positive breakthrough.
        2. Provide a 1-sentence "Growth Milestone" for the user.
        3. If no significant breakthrough is found, provide a gentle encouragement for continued reflection.
        
        Format: Return a JSON-friendly response (string only) with:
        BREAKTHROUGH: [Insight]
        MILESTONE: [Milestone]
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API Error in Breakthrough: {str(e)}")
            return None

    def get_mood_suggestion(self, mood, energy, stress, history_trends=None):
        """
        Suggests focus levels based on daily check-in and recent trends.
        """
        if not self.client:
            return "Listen to your body today. You know best what you need."

        trend_str = f"RECENT TRENDS: {history_trends}" if history_trends else ""

        prompt = f"""
        User Mind Check-in:
        Mood: {mood}/10
        Energy: {energy}/10
        Stress: {stress}/10
        {trend_str}
        
        Suggest a gentle focus level for the day and one piece of advice that acknowledges their current state. 
        If energy is low, be protective. If stress is high, be grounding.
        Keep it brief and calm.
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return "Take it one step at a time today."

ai_service = AIService()
