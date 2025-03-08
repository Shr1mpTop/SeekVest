import os
import pandas as pd
import configparser
from openai import OpenAI
from pathlib import Path

def load_config():
    config = configparser.ConfigParser()
    config.read('stock_crawler/config.ini')
    return config

def analyze_stock_data(df):
    config = load_config()
    client = OpenAI(
        api_key=config['LLM']['api_key'],
        base_url=config['LLM']['base_url']
    )
    
    prompt = f"""请分析以下股票数据，找出今日最具潜力的3只股票，按潜力排序。分析时请综合考虑：
    - 涨跌幅（近期趋势）
    - 成交量（市场关注度）
    - 市盈率/市净率（估值水平）
    - 换手率（资金活跃度）
    - 量比（短期交易动能）
    
股票数据：
{df.to_csv(index=False)}

请用以下格式返回分析结果：
1. [股票代码] [股票名称] 
   核心优势: (50字内简要说明主要优势)
   风险提示: (30字内说明主要风险)
2. ..."""
    
    response = client.chat.completions.create(
        model=config['LLM']['model'],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def process_all_files():
    data_dir = Path('data')
    results = []
    
    for excel_file in data_dir.glob('*.xlsx'):
        try:
            df = pd.read_excel(excel_file)
            print(f"正在分析 {excel_file.name}...")
            analysis = analyze_stock_data(df)
            results.append(f"# {excel_file.name} 分析结果\n{analysis}")
        except Exception as e:
            print(f"处理文件 {excel_file} 出错: {str(e)}")
    
    with open('stock_analysis_report.md', 'w') as f:
        f.write("# 每日股票潜力分析报告\n\n" + "\n\n".join(results))

if __name__ == "__main__":
    process_all_files()
    print("分析完成！结果已保存至 stock_analysis_report.md")
