import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class StockAnalyzer:
    """股票数据分析类，用于获取并可视化股票交易量数据"""
    
    def __init__(self, api_key, symbol, days=7):
        """
        初始化股票分析器
        :param api_key: AlphaVantage API密钥
        :param symbol: 股票代码 (例如: '600104')
        :param days: 要显示的交易天数，默认7天
        """
        self.api_key = api_key
        self.symbol = symbol.upper()  # 统一转换为大写
        self.days = days
        self.data = None
        self.base_url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
        
    def fetch_data(self):
        """从API获取股票数据"""
        url = f"{self.base_url}&symbol={self.symbol}&outputsize=full&apikey={self.api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            raw_data = response.json()
            
            if 'Error Message' in raw_data:
                raise ValueError(f"API错误: {raw_data['Error Message']}")
                
            self._parse_data(raw_data)
            
        except requests.RequestException as e:
            raise ConnectionError(f"网络请求失败: {str(e)}")
            
    def _parse_data(self, raw_data):
        """解析API返回的原始数据"""
        time_series = raw_data.get('Time Series (Daily)', {})
        if not time_series:
            raise ValueError("API返回数据格式异常")
            
        df = pd.DataFrame.from_dict(time_series, orient='index')
        df = df.astype(float)
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df.index = pd.to_datetime(df.index)
        self.data = df.sort_index()
        
    def plot_volume(self):
        """绘制并显示最近N天的交易量柱状图（不自动保存）"""
        if self.data is None:
            raise ValueError("请先调用fetch_data()获取数据")
            
        # 使用默认英文字体配置
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 获取最近N天数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days)
        recent_data = self.data.loc[start_date:end_date]
        
        plt.figure(figsize=(12, 6))
        recent_data['volume'].plot(kind='bar', color='skyblue')
        plt.title(f'{self.symbol} {self.days} Days Trading Volume')
        plt.xlabel('Date')
        plt.ylabel('Volume')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--')
        
        plt.show()

# 示例用法
if __name__ == "__main__":
    import argparse
    
    # 配置命令行参数
    parser = argparse.ArgumentParser(description='股票交易量分析工具')
    parser.add_argument('symbol', type=str, help='股票代码（例如: 600104）')
    args = parser.parse_args()
    
    # 创建分析器实例
    analyzer = StockAnalyzer(api_key="IM6CFDN2PCLSHEC3", symbol=args.symbol, days=7)
    
    try:
        analyzer.fetch_data()
        analyzer.plot_volume()
    except Exception as e:
        print(f"操作失败: {str(e)}")
    finally:
        # 添加退出提示
        input("\n按回车键退出...")
