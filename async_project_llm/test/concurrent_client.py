import asyncio
import aiohttp
import json
import time
import datetime

async def send_request(session, url, messages):
    start_time = time.time()  # 记录请求开始时间
    response_data = {
        'status_code': None,
        'response_text': None,
        'error_message': None
    }
    try:
        async with session.post(url, json={'messages': messages}) as response:
            response_data['status_code'] = response.status
            if response.status == 200:
                response_text = ""
                async for chunk in response.content.iter_any():
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8', errors='replace')
                        if decoded_chunk.startswith('data:'):
                            data = decoded_chunk[5:].strip()
                            if data == '[DONE]':
                                break
                            else:
                                response_text += data
                response_data['response_text'] = response_text
            else:
                error_text = await response.text()
                response_data['error_message'] = f'Request failed with status code: {response.status}, {error_text}'
    except aiohttp.ClientError as e:
        response_data['error_message'] = f"Aiohttp client error: {e}"
    except asyncio.TimeoutError:
        response_data['error_message'] = "Request timed out"
    except Exception as e:
        response_data['error_message'] = f"An unexpected error occurred: {e}"
    finally:
        end_time = time.time()  # 记录请求结束时间
        response_data['request_time'] = f"{end_time - start_time:.2f} seconds"
        response_data['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 添加时间戳
        return response_data  # 返回字典


async def test_concurrent_requests(num_requests, url, messages):
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, url, messages[i]) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)  # 使用 gather 获取结果

        for i, result in enumerate(results):
            print(f"Request {i+1} results:")
            print(result)  # 打印每个请求的结果


if __name__ == '__main__':
    num_requests = 5  # 发送请求的数量
    url = 'http://0.0.0.0:8001/chat'  # 替换为你的服务地址
    messages = [
        {"role": "user", "content": "你好"}
    ]
    messages_group = []
    countries = ["中国", "美国", "英国", "法国", "德国", "日本", "韩国", "加拿大", "澳大利亚", "巴西"]
    for country in countries:
        messages = [
                 {"role": "user", "content": f"介绍一下{country}"}
                    ]
        messages_group.append(messages)
        

    time_s = datetime.datetime.now() # 记录测试开始时间
    asyncio.run(test_concurrent_requests(num_requests, url, messages_group))
    print(f"all query time used:{datetime.datetime.now()-time_s}")  # 记录测试结束时间