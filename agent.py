from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)
from Jarvis_prompts import behavior_prompts, Reply_prompts
from Jarvis_google_search import google_search, get_current_datetime
from jarvis_get_whether import get_weather
from Jarvis_window_CTRL import open, close, folder_file
from Jarvis_file_opner import Play_file, folder_file
from keyboard_mouse_CTRL import move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool, press_key_tool, swipe_gesture_tool, press_hotkey_tool, control_volume_tool
from jarvis_news_fetcher import get_latest_news


load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=behavior_prompts,
                         tools=[
                            google_search,
                            get_current_datetime,
                            get_weather,
                            open,  # এই টুলটি অ্যাপ ওপেন করার জন্য
                            close,
                            folder_file,  # এই টুলটি ফোল্ডার ওপেন করার জন্য
                            Play_file,  # এই টুলটি ফাইল চালানোর জন্য যেমন MP4, MP3, PDF, PPT, img, png ইত্যাদি
                            move_cursor_tool,  # এই টুলটি কার্সর সরানোর জন্য
                            mouse_click_tool,  # এই টুলটি মাউস ক্লিক করার জন্য
                            scroll_cursor_tool,  # এই টুলটি স্ক্রল করার জন্য
                            type_text_tool,  # এই টুলটি লেখার জন্য
                            press_key_tool,  # এই টুলটি কীবোর্ড কী প্রেস করার জন্য
                            press_hotkey_tool,  # এই টুলটি শর্টকাট কী প্রেস করার জন্য
                            control_volume_tool,  # এই টুলটি ভলিউম কন্ট্রোল করার জন্য
                            swipe_gesture_tool,  # এই টুলটি স্ক্রিনে সুইপ জেসচার করার জন্য
                            get_latest_news
                         ]
                         )


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon"
        )
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            video_enabled=True
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=Reply_prompts
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
