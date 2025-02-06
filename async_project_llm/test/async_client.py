import asyncio
import aiohttp
import json

async def test_sse_chat_async():
    url = 'http://0.0.0.0:8001/chat'
    messages = [{"role": "user", "content": "介绍一下北京"}]
    headers = {'Content-Type': 'application/json'}

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post(url, headers=headers, data=json.dumps({'messages': messages})) as response:
                print(f"Response status: {response.status}") # 打印状态码
                if response.status == 200:
                    async for chunk in response.content.iter_any():
                        if chunk:
                            decoded_chunk = chunk.decode('utf-8', errors='replace')
                            # print(f"Received chunk: {decoded_chunk}") # 打印每个chunk
                            if decoded_chunk.startswith('data:'):
                                data = decoded_chunk[5:].strip()
                                if data == '[DONE]':
                                    print('Stream finished')
                                    break
                                else:
                                    print('Received data:', data)
                else:
                    print(f'Request failed with status code: {response.status}')
                    error_text = await response.text()
                    print(f"Error response: {error_text}") # 打印错误响应内容
    except aiohttp.ClientError as e:
        print(f"Aiohttp client error: {e}")
    except asyncio.TimeoutError:
        print("Request timed out")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    
    asyncio.run(test_sse_chat_async())