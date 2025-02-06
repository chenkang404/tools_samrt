from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from openai import OpenAI
import asyncio
import uvicorn
import datetime
import random

app = FastAPI()

# 配置多个模型实例
model_configs = [
    {"base_url": "http://219.147.99.17:40019/v1", "model": "Qwen2-5-14B"},  # 模型 1
    {"base_url": "http://219.147.99.17:40019/v1", "model": "Qwen2-5-14B"},  # 模型 2
    {"base_url": "http://219.147.99.17:40019/v1", "model": "Qwen2-5-14B"},  # 模型 3
]

# 初始化 OpenAI 客户端字典
clients = {}
for config in model_configs:
    clients[config["base_url"]] = OpenAI(
        api_key="token-vulcan",  # 输入你的 API Key
        base_url=config["base_url"],
    )

# # 初始化 OpenAI 客户端
# client = OpenAI(
#     api_key="token-vulcan",  # 输入你的 API Key
#     base_url="http://219.147.99.17:40019/v1"
# )

@app.post('/chat')
async def chat(request: Request):
    data = await request.json()
    messages = data.get('messages', [])

    async def generate_response():
        try:
            # 负载均衡策略：随机选择一个模型
            chosen_config = random.choice(model_configs)
            client = clients[chosen_config["base_url"]]
            model = chosen_config["model"]
            print("message input to model...")
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=messages,
                stream=True,
            )
            # async for line in completion.iter_lines():
            for chunk in completion:  # 使用 iter_lines() 方法
                content = chunk.choices[0].delta.content
                if content:
                        if content == "[DONE]":
                            print(f"[{datetime.datetime.now()}] DONE marker received")
                            break  # 结束循环
                        else:
                            yield f"data: {content}\n\n".encode('utf-8')  # 编码为 UTF-8

            print(f"[{datetime.datetime.now()}] generate_response finished")

        except Exception as e:
            print(f"[{datetime.datetime.now()}] Error in generate_response: {e}")
            yield b"data: [ERROR]\n\n"  # 可选：发送 [ERROR] 标记

    return StreamingResponse(generate_response(), media_type='text/event-stream')

if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8001)
    """
    # async for line in completion.iter_lines():
    # 使用上述代码会报错，因为completion type:<class 'openai.Stream'>不支持async for
    所以只能是同步请求(即阻塞形式的)，如果想使用异步请求大模型服务的话，需要用fastAPI进行模型服务部署
    """
