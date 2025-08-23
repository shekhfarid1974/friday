import os
import asyncio
import uuid
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, Worker
from livekit.agents.pipeline import AgentSession
from livekit.plugins import google, silero
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

# --- Setup ChromaDB for memory ---
CHROMA_PATH = os.getenv("CHROMA_PATH", "./memory")
memory_store = Chroma(
    collection_name="assistant_memory",
    persist_directory=CHROMA_PATH
)

# --- Create Gemini LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",  # or gemini-1.5-pro if enabled
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# --- Define entrypoint for LiveKit Agent ---
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=google.STT(api_key=os.getenv("GOOGLE_API_KEY")),
        tts=google.TTS(api_key=os.getenv("GOOGLE_API_KEY")),
        llm=llm,
    )

    await ctx.connect(session, auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    user_id = ctx.job.metadata.get("user_id", "default-user")

    # Load previous memory for user (using a generic query, e.g., "memory")
    docs = memory_store.similarity_search("memory", k=5)
    if docs:
        remembered = " ".join([d.page_content for d in docs])
        session.context.chat_ctx.append(
            {"role": "system", "content": f"Here are past things about the user: {remembered}"}
        )
    else:
        session.context.chat_ctx.append(
            {"role": "system", "content": "This is my first time meeting the user."}
        )

    @session.on("chat_message")
    async def on_chat_message(msg):
        text = msg.text

        # Save message to memory with a unique ID
        memory_store.add_texts([text], ids=[f"{user_id}-{uuid.uuid4()}"])

        # Keep conversation in context
        session.context.chat_ctx.append({"role": "user", "content": text})

    await session.start()

# --- Worker setup ---
if __name__ == "__main__":
    worker = Worker(WorkerOptions(entrypoint_fnc=entrypoint))
    cli.run_app(worker)
