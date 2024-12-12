from bs4 import BeautifulSoup
from collections import defaultdict
import json
import os



# 用于提取 `padding-left` 值的函数
def extract_padding_left(style):
    """从 style 属性提取 padding-left 的值"""
    if style:
        try:
            for item in style.split(";"):
                if "padding-left" in item:
                    return int(item.split(":")[1].strip().replace("pt", ""))
        except Exception:
            return 0
    return 0

home_path = "./HTML_ZZ_name"
for file in os.listdir("./HTML_ZZ_name")[:1]:
    file_path = os.path.join(home_path,file)

    save_file = file.strip(".html")
    save_path_file = os.path.join("./save",save_file)
    if not os.path.exists(save_path_file):
            os.mkdir(save_path_file)
    # 加载 HTML 文件
    print(file_path)
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # 遍历表格
    tables = soup.find_all("table",class_="table")  # 替换为实际表格 ID
    for table in tables:
        # 初始化树结构
        tree = []
        node_stack = {"questions":[],
                    "level":[],
                    "conclustions":[]}
        conc_names = []
        for one_ in table.find_all("tr")[0].find_all("th")[1:]:
            conc_names.append(one_.get_text(strip=True))
        for idx, tr in enumerate(table.find_all("tr")[1:]):  # 跳过表头
            cols = tr.find_all("td")
                # 提取字段
            if len(cols)>=2:
                values = []
                for cols_ in cols[1:]:
                    value = cols_.get_text(strip=True)
                    if value=="":
                        continue
                    values.append(value)
                div = cols[0].find("div", class_="p")
                label = div.get_text(strip=True) if div else None
                style = cols[0].find("div", style=lambda x: x and "padding-left" in x).get("style", "")
                padding_left = extract_padding_left(style)
                precedingrows = cols[0].find("div", class_="precedingrows")
                precedingrows_text = precedingrows.get_text(strip=True) if precedingrows else f"{idx+1}"
                
                # 创建当前节点
                node = {
                    "node_id":idx+1,
                    "label": label,
                    "value": value,
                    "children": [],
                    "padding_left":padding_left,
                    "precedingrows":precedingrows_text
                }
                if len(values)==0:
                    # print(padding_left)
                    # print(node_stack)
                    if  len(node_stack["level"])>0:
                        if padding_left>node_stack["level"][-1]:
                            node_stack["level"].append(padding_left)
                            node_stack["questions"].append(label)
                        else:
                            # node_stack["questions"].pop()
                            # node_stack["level"].pop()
                            # print(padding_left)
                            # print(node_stack)
                            while padding_left<=node_stack["level"][-1]:
                                # print(padding_left)
                                # print(node_stack)
                                node_stack["questions"].pop()
                                node_stack["level"].pop()
                                if len(node_stack["level"])==0:
                                    break
                                
                            node_stack["level"].append(padding_left)
                            node_stack["questions"].append(label)
                    else:
                        node_stack["level"].append(padding_left)
                        node_stack["questions"].append(label)
                if len(values)!=0:
                    # print(padding_left)
                    # print(node_stack)
                    if len(node_stack["level"])>0:
                        while padding_left<=node_stack["level"][-1]:
                            node_stack["questions"].pop()
                            node_stack["level"].pop()
                            if len(node_stack["level"])==0:
                                    break
                    # print(padding_left)
                    # print(node_stack)
                    node_stack["level"].append(padding_left)
                    node_stack["questions"].append(label)
                    conc_save = [{conc_names[i]:values[i]} for i in range(len(values))]
                    node_stack["conclustions"].append(conc_save)
                    # print(node_stack)
                    tree.append(node_stack)
                    # node_stack["questions"].pop()
                    node_stack = {"questions":node_stack["questions"].copy(),
                                "level":node_stack["level"].copy(),
                    "conclustions":[]}
            
        
        
        to_save_file_path = os.path.join(save_path_file,"#".join(conc_names)+".json") 
        with open(to_save_file_path,"w")as f:
            json.dump(tree,f,ensure_ascii=False,indent=2)
                    
                

# 打印结果
# print(json.dumps(tree, ensure_ascii=False, indent=2))
