import requests
import re
import pandas as pd
 
 
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": "qgqp_b_id=18c28b304dff3b8ce113d0cca03e6727; websitepoptg_api_time=1703860143525; st_si=92728505415389; st_asi=delete; HAList=ty-100-HSI-%u6052%u751F%u6307%u6570; st_pvi=46517537371152; st_sp=2023-10-29%2017%3A00%3A19; st_inirUrl=https%3A%2F%2Fcn.bing.com%2F; st_sn=8; st_psi=20231229230312485-113200301321-2076002087"
}
 
 
def get_html(cmd, page):
    url = f"https://7.push2.eastmoney.com/api/qt/clist/get?cb=jQuery112409467675731682619_1703939377395&pn={page}&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&wbp2u=|0|0|0|web&fid={cmd}&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152&_=1703939377396"
    response = requests.get(url, headers=header)
    data = response.text
    left_data = re.search(r'^.*?(?=\()', data).group()
    data = re.sub(left_data + '\(', '', data)
    # right_data = re.search(r'\)', data).group()
    data = re.sub('\);', '', data)
    data = eval(data)
    return data
 
 
cmd = {
    "沪深京A股": "f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
    "上证A股": "f3&fs=m:1+t:2,m:1+t:23",
    "深证A股": "f3&fs=m:0+t:6,m:0+t:80",
    "北证A股": "f3&fs=m:0+t:81+s:2048",
    "新股": "f26&fs=m:0+f:8,m:1+f:8",
    "创业板": "f3&fs=m:0+t:80",
    "科创板": "f3&fs=m:1+t:23",
    "沪股通": "f26&fs=b:BK0707",
    "深股通": "f26&fs=b:BK0804",
    "B股": "f3&fs=m:0+t:7,m:1+t:3",
    "风险警示板": "f3&fs=m:0+f:4,m:1+f:4",
}
 
null = "null"
for i in cmd.keys():
    page = 0
    stocks = []
    while True:
        page += 1
        data = get_html(cmd[i], page)
        if data['data'] != null:
            print("正在爬取"+i+"第"+str(page)+"页")
            df = data['data']['diff']
            for index in df:
                dict = {
                        "代码": index["f12"],
                        "名称": index['f14'],
                        "最新价": index['f2'],
                        "涨跌幅": index['f3'],
                        "涨跌额": index['f4'],
                        "成交量（手）": index['f5'],
                        "成交额": index['f6'],
                        "振幅(%)": index['f7'],
                        "最高": index['f15'],
                        "最低": index['f16'],
                        "今开": index['f17'],
                        "昨收": index['f18'],
                        "量比": index['f10'],
                        "换手率": index['f8'],
                        "市盈率(动态)": index['f9'],
                        "市净率": index['f23'],
                    }
                stocks.append(dict)
        else:
            break
    df = pd.DataFrame(stocks)
    df.to_excel("./data/"+"股票_"+i+".xlsx", index=False)