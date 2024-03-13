import gradio as gr
from typing import List
import requests
import pytz
import logging
local_tz = pytz.timezone('Asia/Shanghai')
# log = logging.getLogger(__name__)

# LOG_FORMAT = "%(levelname) -5s %(asctime)s" "-1d: %(message)s"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')


prompt = """你是一个大数据和AI领域的专家，用中文回答大数据和AI的相关问题。你的回答需要满足以下要求:
1. 你的回答必须是中文
2. 回答限制在100个字以内"""
# conv = Conversation(prompt, 6)
# def answer(question, history=[]):
#     history.append(question)
#     message = conv.ask(question)
#     history.append(message)
#     responses = [(u,b) for u,b in zip(history[::2], history[1::2])]
#     print(responses)
#     return responses, history


from openai import OpenAI

base_url = "http://127.0.0.1:8000/v1/"
client = OpenAI(api_key="EMPTY", base_url=base_url)


def simple_chat(query, chatbot, history=[], use_stream=True):
    chatbot.append((query,""))

    messages = [
        {
            "role": "user",
            "content": query
        }
    ]
    if len(history)>11:
        history = history[:1]+history[-10:]
    history = history +messages

    messages = history
    #'role': 'assistant',
    response = client.chat.completions.create(
        model="chatglm3-6b",
        messages=messages,
        stream=use_stream,
        temperature=0.8,
        max_tokens=32768,
        presence_penalty=1.1,
        top_p=0.8)
    
    if response:
        if use_stream:
            answer = ""
            
            history.append({
                    "role":"assistant",
                    "content": answer
                })
            for chunk in response:
                # print(chunk.choices[0].delta.content)
                output = chunk.choices[0].delta.content
                answer +=output
                # print(output)
                chatbot[-1] = (query, answer)
                history[-1]["content"] = answer
                

                yield "", chatbot, history
            print("history count:",len(history))
            # print(history)
        else:
            content = response.choices[0].message.content
            print(content)
    else:
        print("Error:", response.status_code)


        
def simple_client(prompt:str,chatbot,history:List=None,use_stream=True):
    chatbot.append((prompt,""))
    url = "http://127.0.0.1:8000/" # 外网
    post_data = {"prompt":prompt,"history":history,"stream":use_stream}
    params = {}
    with requests.post(url, json=post_data, params=params, timeout=200,stream=True)as response:

        # print(response.content.decode("utf-8"))
        answer = ""
        history.append({
                "role":"assistant",
                "content": answer
            })
        logger.info(f"history len:{len(history)}")
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                try:
                    output = chunk.decode("utf-8")
                except Exception as ex:
                    logger.info(ex)
                # answer +=output
                # print(output)
                chatbot[-1] = (prompt, output)
                history[-1]["content"] = output
                
                yield "", chatbot, history


with gr.Blocks(css="#chatbot{height:300px} .overflow-y-auto{height:500px}") as rxbot:
    chatbot = gr.Chatbot(elem_id="chatbot",height=600)
    state = gr.State([{
            "role": "system",
            "content": "You are ChatGLM3, a large language model trained by Zhipu.AI. Follow the user's "
                       "instructions carefully. Respond using markdown.",
        }])
    with gr.Row():
        txt = gr.Textbox(show_label=False, placeholder="请输入你的问题")
    # txt.submit(simple_chat, [txt, chatbot, state], [txt, chatbot, state])
    txt.submit(simple_client, [txt, chatbot, state], [txt, chatbot, state])

    
rxbot.launch(share=True)