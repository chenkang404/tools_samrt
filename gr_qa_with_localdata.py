import os
import gradio as gr
import requests
from typing import List
import pdfminer.high_level as pdfminer
from docx import Document
from openai import OpenAI

import json
import shutil
import logging
import uuid



LOG_FORMAT = "%(levelname) -5s %(asctime)s" "-1d: %(message)s"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT)


UPLOAD_ROOT_PATH = os.path.join(os.path.dirname(__file__), "content")

global selected_file_path
selected_file_path = ""

webui_title = """
# 🎉产品咨询🎉

"""
init_message = f"""欢迎使用 产品咨询！

请在右侧上传文件，目前支持上传pdf,docx,txt类型文件。
"""



def get_f_list():
    lst_default = ["还未上传过文件"]
    if not os.path.exists(UPLOAD_ROOT_PATH):
        return lst_default
    lst = os.listdir(UPLOAD_ROOT_PATH)
    if not lst:
        return lst_default
    lst.sort()
    return [""] + lst


f_list = get_f_list()
logger.info(f"f_list:{f_list}")

history : List = None



def predict_long(prompt:str,history:List=None):
    url = "you llm api url"
    post_data = {"prompt":prompt,"history":history}
    params = {}
    response = requests.post(url, json=post_data, params=params, timeout=200)
    
    if response.status_code == 200:
        result = json.loads(response.content)
        logger.info("answer finish")
        return result
    else:
        return {"error": "Prediction failed"}



# 启动Gradio应用前的准备工作
def process_file(file):
    # 根据文件类型选择适当的解析方法，这里支持PDF、docx和txt文件
    if file.endswith(".pdf"):
        # 解析PDF文件
        # 这里你可以使用适当的PDF解析库，比如PyMuPDF或pdfplumber
        parsed_text  = pdfminer.extract_text(file)
    elif file.endswith(".docx"):
        # 解析docx文件
        # 这里你可以使用python-docx库等
        doc = Document(file)
        parsed_text = ''.join(paragraph.text for paragraph in doc.paragraphs)
        
    elif file.endswith(".txt"):
        # 直接读取txt文件
        with open(file,"r",encoding="utf-8") as f:
            parsed_text = f.read()
    else:
        # 其他文件类型的处理方式，根据实际需求进行调整
        return "Unsupported file type"
    return parsed_text[:20000]

def get_answer_shot(query,file_path,Chatbot):
    contents = []
    for file in file_path:
        file_content = process_file(file)
        contents.append(file_content)
    all_contents = "#".join(contents)
    prompt = f"现在我将给你一份文档，我会询问和这篇文档相关的问题。query:{query}，文档内容为：{all_contents}"
    result_3 = client_api(prompt)
    return Chatbot+[[None,result_3]] , ""

def limit_historys(historys):
    if len(historys)>8:
        historys_new = historys[-4:]
        historys_new.insert(0,historys[0])
        # print(len(historys_new))
        return historys_new
    else:
        return historys

def get_answer_long(query,file_path,chatbot,history):
    global selected_file_path
    selected_file_path = ""
    
    # logger.info(f"file_path:{file_path}")
    if file_path == UPLOAD_ROOT_PATH:
        answer = "请先添加文件"
        return chatbot+[[query,answer]],"",None
    contents = []
    for file in file_path:
        file_content = process_file(file)
        contents.append(file_content)
    all_contents = "#".join(contents)

    if file_path != selected_file_path:
        history = None
        selected_file_path = file_path
    
    if history is None:
        logger.info(f"输入大模型文档：{os.path.split(file_path[0])[-1]}")
        prompt = f"现在我将给你一份文档，我会询问和这篇文档相关的问题。文档内容为:{all_contents}"
        logger.info(f"prompt string len:{len(prompt)}")
        result = predict_long(prompt,history)
        history = limit_historys(result["history"])



    logger.info(f"history len:{len(history)}")
    logger.info(f"user:{query}")
    result_out = predict_long(query,history)
    answer = result_out["response"]
    history = limit_historys(result_out["history"])
    return chatbot+[[query,answer]],"",history



def change_file_name_input(select_file,chatbot):
    select_path = os.path.join(UPLOAD_ROOT_PATH,select_file)
    file_status = f"已经选择:{select_file}"
    logger.info(f"select file:{select_file}")
    logger.info(f"select path:{select_path}")
    return [select_path],  chatbot+[[None,file_status]]



def get_file_store(files,chatbot,f_list):
    filelist = []
    if not os.path.exists(os.path.join(UPLOAD_ROOT_PATH)):
        os.makedirs(os.path.join(UPLOAD_ROOT_PATH))
    add_file = []
    for file in files:
        filename = os.path.split(file.name)[-1]
        add_file.append(filename)
        shutil.move(file.name, os.path.join(UPLOAD_ROOT_PATH, filename))
        filelist.append(os.path.join(UPLOAD_ROOT_PATH, filename))
    logger.info(filelist)
    file_status = f"已上传{'、'.join(os.path.split(file)[-1] for file in files)}"
    return gr.update(visible=True,choices=add_file+f_list, value=add_file[0]), filelist, chatbot+[[None,file_status]]



block_css = """.importantButton {
    background: linear-gradient(45deg, #7e0570,#5d1c99, #6e00ff) !important;
    border: none !important;
}
.importantButton:hover {
    background: linear-gradient(45deg, #ff00e0,#8500ff, #6e00ff) !important;
    border: none !important;
}"""


with gr.Blocks(css=block_css) as demo:
    file_path, file_status, f_list, history = gr.State(UPLOAD_ROOT_PATH), gr.State(""),  gr.State(f_list), gr.State(history)


    gr.Markdown(webui_title)
    with gr.Tab("对话"):
        with gr.Row():
            with gr.Column(scale=10):
                chatbot = gr.Chatbot([[None, init_message],],
                                        elem_id="chat-box",
                                        show_label=False)
                query = gr.Textbox(show_label=False,
                                    placeholder="请输入提问内容，按回车进行提交")
            with gr.Column(scale=5):
                gr.Markdown("添加文件")
                with gr.Row():
                    with gr.Tab("上传文件"):
                        files = gr.File(label="添加文件",
                                        file_types=['.txt', '.docx', '.pdf'],
                                        file_count="multiple",
                                        show_label=False
                                        )
                        load_file_button = gr.Button("上传文件")

                    with gr.Tab("选择文件"):
                         select_file = gr.Dropdown(f_list.value,
                                            label="请选择要解析的文件",
                                            interactive=True,
                                            value=f_list.value[0] if len(f_list.value) > 1 else None)

                    
            load_file_button.click(get_file_store,
                                    show_progress=True,
                                    inputs=[files,chatbot,f_list],
                                    outputs=[select_file,file_path,chatbot]
                                    )
            
            select_file.change(fn=change_file_name_input,
                               inputs=[select_file,chatbot],
                               outputs=[file_path,chatbot])
            
           
            
            query.submit(fn=get_answer_long,
                            inputs=[query,file_path,chatbot,history],
                            outputs=[chatbot,query,history])
                    

                    


# demo.queue(concurrency_count=3)
demo.launch(server_name='0.0.0.0',
        server_port=8000,
        show_api=False,
        share=True,
        inbrowser=False)