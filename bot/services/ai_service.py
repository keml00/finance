import httpx
from bot.config import get_settings

settings = get_settings()


async def ai_analyze(prompt: str, context: str = "") -> str:
    """Send prompt to AI and get analysis response."""

    system_prompt = (
        "Ты — профессиональный финансовый консультант FinAI. "
        "Отвечай кратко, конкретно, с цифрами. "
        "Используй emoji для наглядности. "
        "Давай практичные советы по финансам."
    )

    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if context:
        messages.append({"role": "user", "content": f"Контекст финансов пользователя:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    # Try DeepSeek first
    if settings.deepseek_api_key:
        return await _call_deepseek(messages)

    # Try OpenRouter
    if settings.openrouter_api_key:
        return await _call_openrouter(messages)

    # Try Gemini
    if settings.gemini_api_key:
        return await _call_gemini(prompt, context)

    return "⚠️ AI не настроен. Добавьте API ключ в .env"


async def _call_deepseek(messages: list) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
            },
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_openrouter(messages: list) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "messages": messages,
                "max_tokens": 1000,
            },
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def _call_gemini(prompt: str, context: str) -> str:
    full_prompt = f"Контекст: {context}\n\nВопрос: {prompt}" if context else prompt
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.gemini_api_key}",
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
            },
        )
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def get_financial_advice(stats: dict) -> str:
    context = (
        f"Доходы за месяц: {stats['total_income']}₽\n"
        f"Расходы за месяц: {stats['total_expense']}₽\n"
        f"Баланс: {stats['balance']}₽\n"
        f"Средний расход в день: {stats['avg_daily_expense']:.0f}₽\n"
    )

    if stats.get("categories"):
        context += "Топ расходов:\n"
        for cat in stats["categories"][:5]:
            context += f"  {cat['icon']} {cat['name']}: {cat['total']}₽\n"

    return await ai_analyze(
        "Проанализируй мои финансы за месяц. Дай 3-4 коротких совета по оптимизации расходов.",
        context=context,
    )
