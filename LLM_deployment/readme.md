<!--
 * @Author: chenkang404 763711755@qq.com
 * @Date: 2024-03-13 11:39:00
 * @LastEditors: chenkang404 763711755@qq.com
 * @LastEditTime: 2024-03-13 11:45:18
 * @FilePath: \tools_samrt\LLM_deployment\readme.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
大模型流式部署即调用说明
* api_server_streaming.py是未采用openai模块的streaming部署，steaming_QA_greadio.py是其调用方式
* openai_api_server_streaming.py是采用了openai模块的steaming部署，openai_streaming_QA_gradio.py是其调用方式。该部署方式参考自https://github.com/THUDM/ChatGLM3的openai_api_demo