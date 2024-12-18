import pandas as pd
import random

def true_accounts(file_path, sheet_name, true_count=5):
    try:
        # 讀取 Excel 文件，指定使用 openpyxl 引擎
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
        print("文件讀取成功！")
    except Exception as e:
        print(f"讀取文件失敗：{e}")
        return

    column_name = "點擊操作_1"  # 設定要修改的列名

    # 檢查指定的列是否存在
    if column_name not in df.columns:
        print(f"列 '{column_name}' 不存在，請檢查 Excel 文件。")
        return

    # 初始化該列為 False
    df[column_name] = "false"

    # 獲取該列的索引，並確保是整數類型
    available_indices = df.index.tolist()

    # 確保 true_count 和 len(available_indices) 都是整數
    true_count = min(true_count, len(available_indices))

    # 隨機選擇 true_count 個索引
    true_indices = random.sample(available_indices, true_count)

    # 設置指定索引為 True
    df.loc[true_indices, column_name] = "true"

    # 保存結果
    output_path = file_path
    df.to_excel(output_path, sheet_name=sheet_name, index=False)

    print(f"操作完成，結果已保存至 {output_path}")

# 使用範例
# true_accounts(r'C:\Users\user\Desktop\SuChenAI\Factbook-RPA-clickurl\data\fb_account_data.xlsx', '點擊', int(input("請輸入要設置為 true 的數量： ")))
