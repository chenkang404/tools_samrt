import os
os.environ['CUDA_VISIBLE_DEVICES'] = "0,1"
from fastapi import FastAPI, Request
from transformers import AutoTokenizer, AutoModel
import uvicorn, json, datetime
from pydantic import BaseModel, Field
from typing import Literal,List,Optional
from fastapi.responses import StreamingResponse
import torch

import logging
import pytz

local_tz = pytz.timezone('Asia/Shanghai')
# log = logging.getLogger(__name__)

# LOG_FORMAT = "%(levelname) -5s %(asctime)s" "-1d: %(message)s"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

DEVICE = "cuda"
DEVICE_ID = "0"
CUDA_DEVICE = f"{DEVICE}:{DEVICE_ID}" if DEVICE_ID else DEVICE


def torch_gc():
    if torch.cuda.is_available():
        with torch.cuda.device(CUDA_DEVICE):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()



async def predict_stream(gen_params):

    prompt = gen_params["prompt"]
    history = gen_params["history"]
    top_p = gen_params["top_p"]
    temperature = gen_params["temperature"]
    logger.info(f"prompt:{prompt}")

    for response, history in  model.stream_chat(tokenizer,prompt,history, top_p=top_p if top_p else 0.85,
                            temperature=temperature if temperature else 0.95):
        # logger.info(f"response:{response}")
        yield response

async def predict(gen_params):
    prompt = gen_params["prompt"]
    history = gen_params["history"]
    top_p = gen_params["top_p"]
    temperature = gen_params["temperature"]
    logger.info(f"prompt:{prompt}")

    response,history = model.chat(tokenizer,prompt,history, top_p=top_p if top_p else 0.85,
                            temperature=temperature if temperature else 0.95)
    
    return response,history

app = FastAPI()


@app.post("/")
async def create_item(request: Request):
    global model, tokenizer
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    prompt = json_post_list.get('prompt')
    history = json_post_list.get('history')
    top_p = json_post_list.get('top_p')
    temperature = json_post_list.get('temperature')
    stream_is = json_post_list.get("stream")
    logger.info(f"stream_is:{stream_is}")
    #把下面的返回重新写到一个async函数中
    gen_params = dict(
        prompt= prompt,
        temperature=temperature,
        top_p=top_p,
        history= history,
    )
    if stream_is:
        return StreamingResponse(predict_stream(gen_params))
    else:
        response = predict(gen_params)
        now = datetime.datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")
        answer = {
            "response": response,
            "history": history,
            "status": 200,
            "time": time
        }
        log = "[" + time + "] " + '", prompt:"' + prompt + '", response:"' + repr(response) + '"'
        logger.info(log)
        torch_gc()
        return answer
        

        



if __name__ == '__main__':
    model_dir = "../../Models/chatglm3-6b/"
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_dir, trust_remote_code=True,device_map="auto")
    model.eval()
    uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)


