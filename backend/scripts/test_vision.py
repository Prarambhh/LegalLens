import asyncio
import os
import base64
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load env from .env file (assuming running from backend dir)
load_dotenv(".env")
api_key = os.getenv("GROQ_API_KEY")

async def test_vision():
    if not api_key:
        print("Error: GROQ_API_KEY not found in .env")
        return

    print("Initializing Vision Model...")
    try:
        vision_llm = ChatGroq(
            model="llama-3.2-90b-vision-preview",
            api_key=api_key,
            temperature=0
        )
        
        # specific image path provided in user context or use a dummy small image
        # I'll create a tiny valid PNG in base64 to avoid file path dependency issues
        # 1x1 white pixel PNG
        dummy_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
        file_ext = "png"
        data_url = f"data:image/{file_ext};base64,{dummy_png_base64}"
        
        print("Sending request to Groq Vision...")
        messages = [
            (
                "user",
                [
                    {"type": "text", "text": "What is in this image? Reply with 'It is a white pixel'."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            )
        ]
        
        response = await vision_llm.ainvoke(messages)
        print("Success!")
        print("Response:", response.content)
        
    except Exception as e:
        print("\n❌ Error occurred:")
        print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vision())
