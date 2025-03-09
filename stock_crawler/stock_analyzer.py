import os
import pandas as pd
import configparser
from openai import OpenAI
from pathlib import Path

def load_config():
    config = configparser.ConfigParser()
    config.read('stock_crawler/config.ini')
    return config

def analyze_stock_data(df, batch_size=200, top_n=3):
    config = load_config()
    client = OpenAI(
        api_key=config['LLM']['api_key'],
        base_url=config['LLM']['base_url']
    )
    
    batch_results = []
    
    # 分批次处理数据
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        
        # 生成股票列表
        stock_list = "\n".join([f"{idx+1}. {row['代码']} {row['名称']}" 
                              for idx, row in batch_df.head(top_n).iterrows()])
        
        prompt = f"""请严格按以下要求分析第{i//batch_size+1}批股票数据（共{len(batch_df)}只）：
1. 从以下维度评估：
   - 短期趋势（3日/5日涨跌幅）
   - 量能变化（对比20日成交量均值）
   - 估值水平（行业PE/PB分位值）
   - 资金热度（换手率及量比）
   - 技术形态（关键支撑/压力位）

2. 优质标的（前{top_n}）：
{stock_list}

3. 分析要求：
   ★核心优势（35字关键指标）
   ⚠️主要风险（20字明确风险点）

股票数据：
{batch_df.to_csv(index=False)}

请按格式返回：
【第{i//batch_size+1}批优选】
1. 代码 名称
   ★优势: ...
   ⚠️风险: ..."""

        try:
            response = client.chat.completions.create(
                model=config['LLM']['model'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                timeout=30
            )
            result = response.choices[0].message.content.strip()
            if not result or "优选" not in result:
                raise ValueError("大模型返回格式异常")
            batch_results.append(result)
        except Exception as e:
            print(f"⚠️ 第{i//batch_size+1}批分析异常: {str(e)}")
            batch_results.append(f"【第{i//batch_size+1}批异常】{str(e)}")
    
    # 最终汇总分析
    final_prompt = f"""请从各批次优选股票中评选最终前3名：

{chr(10).join(batch_results)}

评选标准：
1. 技术面（量价配合、趋势形态）40%
2. 基本面（估值合理性）30%
3. 市场关注度（成交量）20%
4. 风险收益比 10%

请用以下格式返回：
🏆 今日终极优选：
🥇 [代码] [名称] - 核心亮点+风险提示
🥈 [代码] [名称] - 核心亮点+风险提示
🥉 [代码] [名称] - 核心亮点+风险提示"""

    final_response = client.chat.completions.create(
        model=config['LLM']['model'],
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.2
    )
    return f"{final_response.choices[0].message.content}\n※ 数据来源：{len(batch_results)*top_n}只候选股"

def process_all_files():
    data_dir = Path('data')
    results = []
    
    for excel_file in data_dir.glob('*.xlsx'):
        try:
            df = pd.read_excel(excel_file)
            
            # 数据有效性检查
            required_columns = ['代码', '名称', '涨跌幅', '成交量（手）', '市盈率(动态)', '市净率']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("文件缺少必要列")
                
            if df.empty or df['代码'].isnull().all():
                raise ValueError("数据无效")
            
            print(f"\n正在分析 {excel_file.stem} ({len(df)}只)...")
            analysis = analyze_stock_data(df)
            
            results.append(f"# {excel_file.stem.replace('_', ' ')}分析\n{analysis}")
            print(f"✓ 完成分析")
            
        except Exception as e:
            print(f"\n⚠️ 分析失败: {str(e)}")
            results.append(f"# {excel_file.stem.replace('_', ' ')}分析\n❌ 失败原因: {str(e)}")
    
    with open('stock_analysis_report.md', 'w') as f:
        f.write("# 每日股票潜力分析报告\n\n" + "\n\n".join(results))

if __name__ == "__main__":
    process_all_files()
    print("分析完成！结果已保存至 stock_analysis_report.md")
