import os
import pandas as pd
import configparser
from openai import OpenAI
from pathlib import Path
import concurrent.futures
from tqdm import tqdm


def load_config():
    config = configparser.ConfigParser()
    config.read('stock_crawler/config.ini')
    return config


def analyze_batch(batch_df, batch_num, config, batch_size, top_n):
    client = OpenAI(
        api_key=config['LLM']['api_key'],
        base_url=config['LLM']['base_url']
    )
    # 生成股票列表
    stock_list = "\n".join([f"{idx + 1}. {row['代码']} {row['名称']}"
                            for idx, row in batch_df.head(top_n).iterrows()])

    prompt = f"""请严格按以下要求分析第{batch_num}批股票数据（共{len(batch_df)}只）：
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
【第{batch_num}批优选】
1. 代码 名称
   ★优势: ...
   ⚠️风险: ..."""

    try:
        response = client.chat.completions.create(
            model=config['LLM']['model'],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            timeout=300
        )
        result = response.choices[0].message.content.strip()
        if not result or "优选" not in result:
            raise ValueError("大模型返回格式异常")
        return result
    except Exception as e:
        print(f"⚠️ 第{batch_num}批分析异常: {str(e)}")
        return f"【第{batch_num}批异常】{str(e)}"


def analyze_file(excel_file, config, batch_size=200, top_n=3):
    try:
        df = pd.read_excel(excel_file)

        # 数据有效性检查
        required_columns = ['代码', '名称', '涨跌幅', '成交量（手）', '市盈率(动态)', '市净率']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("文件缺少必要列")

        if df.empty or df['代码'].isnull().all():
            raise ValueError("数据无效")

        batch_results = []
        total_batches = (len(df) + batch_size - 1) // batch_size
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            # 分批次处理数据
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i + batch_size]
                batch_num = i // batch_size + 1
                future = executor.submit(analyze_batch, batch_df, batch_num, config, batch_size, top_n)
                futures.append(future)

            # 获取所有线程的结果
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                batch_results.append(result)

        # 提取各批次优选股票的代码
        selected_stock_codes = []
        for result in batch_results:
            if "优选" in result:
                lines = result.split('\n')
                for line in lines:
                    if line.strip().startswith('1. '):
                        code = line.split(' ')[1]
                        selected_stock_codes.append(code)

        # 筛选出优选股票的数据
        selected_df = df[df['代码'].isin(selected_stock_codes)]

        return selected_df, batch_results
    except Exception as e:
        print(f"\n⚠️ 分析失败: {str(e)}")
        return None, []


def process_all_files():
    data_dir = Path('data')
    config = load_config()
    all_dfs = []
    all_batch_results = []
    excel_files = list(data_dir.glob('*.xlsx'))
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for excel_file in excel_files:
            future = executor.submit(analyze_file, excel_file, config)
            futures.append(future)

        # 使用 tqdm 显示进度条
        with tqdm(total=len(futures), desc="分析进度") as pbar:
            for future in concurrent.futures.as_completed(futures):
                df, batch_results = future.result()
                if df is not None:
                    all_dfs.append(df)
                    all_batch_results.extend(batch_results)
                pbar.update(1)

    # 合并所有优选股票的原始数据
    all_data = pd.concat(all_dfs, ignore_index=True)

    # 最终汇总分析
    final_prompt = f"""请从各批次优选股票中评选最终前3名：

{chr(10).join(all_batch_results)}

以下是各批次优选股票的原始数据：
{all_data.to_csv(sep=chr(9), na_rep='nan')}

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

    client = OpenAI(
        api_key=config['LLM']['api_key'],
        base_url=config['LLM']['base_url']
    )
    final_response = client.chat.completions.create(
        model=config['LLM']['model'],
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.2
    )

    results = [f"# 最终分析\n{final_response.choices[0].message.content}\n※ 数据来源：{len(all_batch_results) * 3}只候选股"]

    with open('stock_analysis_report.md', 'w') as f:
        f.write("# 每日股票潜力分析报告\n\n" + "\n\n".join(results))


if __name__ == "__main__":
    process_all_files()
    print("分析完成！结果已保存至 stock_analysis_report.md")