import json
from typing import List, Optional
import httpx
from app.models.schemas import ChatMessage, Booking_Info
from app.config import settings
from app.logger import logger


class LLM_Client:
    def __init__(self, provider: str):
        self.provider = provider

        if provider == "groq":
            self.api_key = settings.groq_api_key
            self.model = settings.groq_chat_model
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        else:
            raise ValueError(f"Problem with LLM provider {provider}")

    async def generate_response(
        self,
        query: str,
        context: str,
        chat_history: List[ChatMessage],
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        temperature = temperature or settings.llm_temperature
        max_tokens = max_tokens or settings.llm_max_tokens

        if self.provider == "groq":
            return await self.generate_res_groq(
                query, context, chat_history, temperature, max_tokens
            )

    async def generate_res_groq(
        self,
        query: str,
        context: str,
        chat_history: List[ChatMessage],
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions based on the provided context. "
                "i want you to witty enough to be proffesional."
                "Use the context to answer the user's question accurately. "
                "If the context doesn't contain relevant information, say so politely. And provide the info that u can provide like ur services."
                "You can also help schedule interview bookings.\n\n"
                f"Context:\n{context}"
            ),
        }

        messages = [system_message]

        for msg in chat_history[-5:]:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": query})

        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=60.0,
            )
            res.raise_for_status()
            data = res.json()
            answer = data["choices"][0]["message"]["content"]

            provider_name = "Groq"
            logger.info(f"Generated {provider_name} response ({len(answer)} chars)")
            return answer

    # extract Booking info
    async def extract_booking_info(self, text: str) -> Optional[Booking_Info]:
        extraction_prompt = (
            "Extract interview booking information from the following text. "
            "Return ONLY a JSON object with these exact fields (use null if not found):\n\n"
            "{\n"
            '  "name": "candidate full name or null",\n'
            '  "email": "email@example.com or null",\n'
            '  "date": "YYYY-MM-DD format or null",\n'
            '  "time": "HH:MM in 24-hour format or null",\n'
            '  "additional_notes": "any extra info or null"\n'
            "}\n\n"
            "IMPORTANT TIME CONVERSION:\n"
            "- Convert 2:00 PM to 14:00\n"
            "- Convert 9:00 AM to 09:00\n"
            "- Always use 24-hour HH:MM format\n\n"
            "IMPORTANT DATE CONVERSION:\n"
            "- Convert 'December 15, 2025' to '2025-12-15'\n"
            "- Always use YYYY-MM-DD format\n\n"
            "If NO booking information is present, return: {}\n\n"
            f"Text to analyze:\n{text}\n\n"
            "Return ONLY the JSON object, no other text:"
        )

        try:
            if self.provider == "groq":
                response = await self.extract_booking_info_groq(extraction_prompt)
            response = response.strip()

            if not response:
                logger.info("Empty response from LLM for booking extraction")
                return None
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            logger.info(f"Cleaned booking extraction response: {response}")

            try:
                booking_data = json.loads(response)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in booking extraction: {response[:100]}")
                return None
            if not booking_data or all(
                v is None or v == "" for v in booking_data.values()
            ):
                logger.info("no booking info was found in extraction")
                return None
            logger.info(f"Extracted Booking data: {booking_data}")
            return Booking_Info(**booking_data)
        except Exception as e:
            logger.warning(f"Failed to extract booking info: {e}", exc_info=True)
            return None

    async def extract_booking_info_groq(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a JSON extraction bot. You ONLY output valid JSON. Never add explanations or extra text.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 500,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Raw Extract response: {result[:200]}")
            return result


def get_llm_client() -> LLM_Client:
    provider = settings.llm_provider

    if provider == "groq" and not settings.groq_api_key:
        raise ValueError("Groq API key required")

    return LLM_Client(provider=provider)
