import os
from agents import Agent, Runner, OpenAIChatCompletionsModel, RunConfig, function_tool, result
import chainlit as cl
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv

# 🔄 Load environment variables
load_dotenv()

# 🔐 Get API key from .env
gemini_api_key = os.getenv("Gemini_Api_Key")

# 🔗 Initialize custom OpenAI client for Gemini API
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# 🧠 Define model using external client
model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

# ⚙️ Configuration for runner (NO model_provider anymore)
configuration = RunConfig(
    model=model,
    tracing_disabled=True
)

# 💘 Matching logic
@function_tool
async def Finder_Couple(persona_data):
    """
    Match the user's data with database and return the best match.
    """
    people_data = [
        # 👇 Inserted people_data truncated for brevity
        {
            "name": "Sara",
            "gender": "female",
            "whatsapp_no": "923111111112",
            "age": "24",
            "relationship_status": "single",
            "profession": "Graphic Designer",
            "location": "Lahore",
            "education": "Bachelor of Fine Arts",
            "hobbies": "Painting, Music",
            "languages": "English, Urdu",
        },
        # ✂️ ... [rest of your people_data here — same as before]
        {
            "name": "Kinza",
            "gender": "female",
            "whatsapp_no": "923111111158",
            "age": "25",
            "relationship_status": "single",
            "profession": "Event Planner",
            "location": "Karachi",
            "education": "BBA",
            "hobbies": "Decorating, Traveling",
            "languages": "English, Urdu",
        }
    ]

    user_gender = persona_data.get("gender", "").lower()
    user_location = persona_data.get("location", "").lower()

    if user_gender not in ["male", "female"]:
        return {"message": "Invalid gender. Please specify 'male' or 'female'."}

    target_gender = "female" if user_gender == "male" else "male"

    matches = [p for p in people_data if p["gender"] == target_gender and p["relationship_status"] == "single"]
    city_matches = [p for p in matches if p["location"].lower() == user_location]

    best_match = city_matches[0] if city_matches else matches[0] if matches else None

    if best_match:
        whatsapp_link = f"https://wa.me/{best_match['whatsapp_no']}?text=Salam!%20Aap%20ka%20match%20mil%20gaya%20hai!"
        return {
            "message": f"✅ Best match found!\nClick here to contact your Partner: {whatsapp_link}",
            "match": best_match
        }
    else:
        return {"message": "❌ Sorry, no match found at the moment."}

# 🤵‍♂️ Uncle Agent
Shadi_Walah_Uncle = Agent(
    name="Shadi Walah Uncle",
    instructions="""
    You are Shadi Walah Uncle.
    When you receive full user details (name, gender, location, age, WhatsApp number, etc.),
    you MUST call the Finder_Couple tool to find the best match for marriage and return the result.
    Do not answer any unrelated questions.
    """,
    tools=[Finder_Couple]
)

# 🧕 Aunty Agent
Shadi_Wali_Aunty = Agent(
    name="Shadi Wali Aunty",
    instructions="""
    You are Shadi Wali Aunty — part Cupid, part detective, full drama! 🕵️‍♀️💘
    Your mission is to help people find their perfect rishta.

    Ask users nicely (with sass and love) to share:
    - Name
    - Gender
    - Age
    - Location
    - WhatsApp Number
    - Profession
    - Hobbies
    - Education
    - Languages

    Once you have all the info, pass it to Shadi Walah Uncle to find the best match.
    
    ❌ Don't respond to anything not related to shadi.
    ✅ Always be dramatic, funny, and warm like a true aunty!
    """,
    handoffs=[Shadi_Walah_Uncle]
)


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])
    await cl.Message(content="""
🎯 **Welcome to RishtaGPT – Powered by Shadi Wali Aunty™!** 💘🧕  
Your career is on LinkedIn. But what about your **love life**? 👀💍

I’m **Shadi Wali Aunty** — HR of hearts, CEO of rishtas, and a matchmaking machine. 🕵️‍♀️✨  
Whether you’re a Software Engineer or a Civil Engineer, Aunty has a match for you! 😉

📋 Just send me your:
- Name  
- Gender  
- Age  
- City  
- WhatsApp Number  
- Profession  
- Hobbies  
- Education  
- Languages  

And I’ll find you a partner faster than your recruiter finds candidates! 🚀💞  

No time-wasters. No awkward aunties. Just one cute API and lots of pyaar. ❤️

🗣️ Type your details below & let’s begin your *LinkedIn-approved* love story! 📱💌
    """).send()

# 💬 On Message
@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history") or []
    history.append({"role": "user", "content": message.content})

    runner = Runner.run_streamed(
        Shadi_Wali_Aunty,
        input=history,
        run_config=configuration,
        context={"history": history}
    )

    msg = cl.Message(content="")
    await msg.send()

    async for event in runner.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            await msg.stream_token(event.data.delta)

    history.append({"role": "assistant", "content": runner.final_output})
    cl.user_session.set("history", history)
