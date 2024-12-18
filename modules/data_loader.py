import pandas as pd
import random
import re
import os

class DataLoader:
    def __init__(self, excel_path):  # 初始化 DataLoader 類，設置 Excel 文件路徑
        self.excel_path = excel_path  # 設置 Excel 文件路徑
        
    def load_account_data(self):  # 讀取並解析 Excel 文件中的帳號資料
        """讀取並解析 Excel 文件中的帳號資料。"""
        # 分別讀取 "發文", "留言", "爬蟲", "點擊" 和 "跳轉" 三個 tab 的資料
        sheet_names = ["發文", "留言", "爬蟲", "點擊", "跳轉"]  # 設置要讀取的 tab 名稱
        sheets = pd.read_excel(self.excel_path, sheet_name=sheet_names)  # 讀取 Excel 文件中的指定 tab
    
        post_accounts = []  # 用於存放發文的帳號資料
        comment_accounts = []  # 用於存放留言的帳號資料
        crawl_accounts = [] # 用於存放爬蟲的帳號資料
        click_accounts = [] # 用於存放點擊的帳號資料
        navigate_accounts = [] # 用於存放跳轉的帳號資料

        errors = []  # 用於累積所有錯誤訊息

        # 遍歷每個 tab 的資料
        for sheet_name, df in sheets.items():  # 遍歷每個 tab 的資料
            for row_idx, row in df.iterrows():  # 遍歷每個 tab 中的每一行
                # 基本帳號資訊
                try:
                    account_info = {  # 構建帳號資訊
                        "account": row["帳號"],  # 帳號
                        "password": row["密碼"],  # 密碼
                        "secret_key": row["密鑰"],  # 密鑰
                        "host": row["Host"],  # Host
                        "port": row["Port"],  # Port
                        "proxy_username": row["Proxy_帳號"],  # Proxy 帳號
                        "proxy_password": row["Proxy_密碼"],  # Proxy 密碼
                        "source": sheet_name,  # 來源
                    }
                    
                    # 檢查每一個必要欄位是否有空值
                    for key, value in account_info.items():  # 遍歷帳號資訊中的每一個欄位
                        if pd.isna(value) or value == "":  # 如果欄位為空值或空字串
                            errors.append(
                                f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的必要欄位 '{key}' 為空，請檢查資料完整性。"
                            )
                            

                except KeyError as e:  # 如果找不到必要的行
                    errors.append(
                        f"[{sheet_name}] 錯誤：在第 {row_idx + 2} 列找不到必要的行 '{e.args[0]}'。請檢查行名稱是否正確。"  # 打印找不到必要的行
                    )
                    continue  # 跳過此列並處理下一列

                # 根據 tab 名稱解析對應的操作資料
                if sheet_name == "發文":  # 如果 tab 名稱為 "發文"
                    posts = self._parse_posts(row, row_idx, errors, sheet_name)  # 解析發文資料
                    account_info["posts"] = posts  # 將發文資料加入帳號資訊
                    post_accounts.append(account_info)  # 將帳號資訊加入發文帳號列表

                elif sheet_name == "留言":
                    comments = self._parse_comments(row, row_idx, errors, sheet_name)  # 解析留言資料
                    account_info["comments"] = comments  # 將留言資料加入帳號資訊
                    comment_accounts.append(account_info)  # 將帳號資訊加入留言帳號列表
                
                elif sheet_name == "爬蟲":
                    crawls = self._parse_crawls(row, row_idx, errors, sheet_name)  # 解析爬蟲資料
                    account_info["crawls"] = crawls  # 將爬蟲資料加入帳號資訊
                    crawl_accounts.append(account_info)  # 將帳號資訊加入爬蟲帳號列表
                    
                elif sheet_name == "點擊":
                    clicks = self._parse_clicks(row, row_idx, errors, sheet_name)  # 解析爬蟲資料
                    account_info["clicks"] = clicks  # 將爬蟲資料加入帳號資訊
                    click_accounts.append(account_info)  # 將帳號資訊加入爬蟲帳號列表
                    
                elif sheet_name == "跳轉":
                    navigates = self._parse_navigates(row, row_idx, errors, sheet_name)  # 解析爬蟲資料
                    account_info["navigates"] = navigates  # 將爬蟲資料加入帳號資訊
                    navigate_accounts.append(account_info)  # 將帳號資訊加入爬蟲帳號列表
            # print(f'click_accounts: {click_accounts}')

        # true_account_num = eval(input("請輸入帳號數量:"))
        # click_accounts = set_true_count(click_accounts, true_account_num)

        # 若有錯誤，則顯示並停止程式    
        if errors:  # 如果存在錯誤  
            print("發現以下錯誤，請修正後再重新執行：")  # 打印錯誤訊息
            for error in errors:  # 遍歷每個錯誤
                print(error)  # 打印錯誤訊息
            raise Exception("資料格式錯誤，程序已停止執行。")  # 拋出錯誤

        return post_accounts, comment_accounts, crawl_accounts, click_accounts, navigate_accounts  # 返回發文、留言和爬蟲帳號列表
    
    def _parse_posts(self, row, row_idx, errors, sheet_name):
        """解析發文資料。"""
        posts = []  # 用於存放發文資料
        index = 1  # 發文組的編號索引
        
        while True:
            # 定義當前發文組所需的欄位
            expected_columns = [
                f"發文類型_{index}", f"社團連結_{index}", f"發文操作_{index}",  # 發文類型、社團連結、發文操作
                f"發文時間_{index}", f"發文文字_{index}", f"發文圖片_{index}"  # 發文時間、發文文字、發文圖片
            ]

            # 檢查每個欄位是否存在
            if not all(col in row.index for col in expected_columns):  # 如果欄位不存在
                break  # 跳出迴圈

            # 構建發文組訊息
            action_value = row.get(f"發文操作_{index}", "FALSE")  # 獲取發文操作值
            action = action_value == "TRUE" or action_value is True  # 將發文操作值轉換為布林值 
            post_type = str(row.get(f"發文類型_{index}", "個人")).strip()  # 獲取發文類型值
            group_url = str(row.get(f"社團連結_{index}", "")) if not pd.isna(row.get(f"社團連結_{index}", "")) else ""  # 獲取社團連結值
            time_value = (
                row.get(f"發文時間_{index}", None).strftime("%Y/%m/%d %H:%M:%S")  # 將發文時間值轉換為指定格式
                if isinstance(row.get(f"發文時間_{index}", None), pd.Timestamp)  # 檢查發文時間值是否為 Pandas Timestamp 類型
                else row.get(f"發文時間_{index}", None)  # 如果發文時間值不是 Pandas Timestamp 類型，則直接使用原值
            )

            # 將 NaN 轉換為空字符串
            content = str(row.get(f"發文文字_{index}", "")).strip() if not pd.isna(row.get(f"發文文字_{index}", "")) else ""  # 獲取發文文字值
            image_path = str(row.get(f"發文圖片_{index}", "")).strip() if not pd.isna(row.get(f"發文圖片_{index}", "")) else ""  # 獲取發文圖片值

            # 圖片存在檢查
            if image_path:  # 如果發文圖片存在
                image_files = [img.strip() for img in image_path.split(",")]  # 將發文圖片值分割成單個圖片
                for image in image_files:  # 遍歷每個圖片
                    image_full_path = os.path.join(os.path.abspath("images"), image)  # 構建圖片完整路徑
                    if not os.path.isfile(image_full_path):  # 檢查圖片是否存在
                        errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的發文圖片 '{image}' 在資料夾中找不到，請確認圖片檔案是否存在。")

            # 規則檢查
            # 規則一: 發文類型 "個人" 時，社團連結應為空；"社團" 時，社團連結不能為空
            if post_type == "個人" and group_url:  # 如果發文類型為 "個人" 且社團連結不為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的發文類型為 '個人'，社團連結應為空。")
            elif post_type == "社團" and not group_url:  # 如果發文類型為 "社團" 且社團連結為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的發文類型為 '社團'，社團連結不能為空。")

            # 規則二: 發文文字和發文圖片至少需要一個
            if content == "" and image_path == "":  # 如果發文文字和發文圖片皆為空      
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中發文文字和發文圖片皆為空，至少需要填入一項。")

            # 規則三: 發文類型只能為 "個人" 或 "社團"
            if post_type not in ["個人", "社團"]:  # 如果發文類型不是 "個人" 或 "社團"
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中發文類型 '{post_type}' 無效，僅允許 '個人' 或 '社團'。")

            # 規則四: 發文操作只能為 "TRUE" 或 "FALSE"
            if action_value not in ["TRUE", "FALSE", True, False]:
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的發文操作 '{action_value}' 無效，僅允許 'TRUE' 或 'FALSE'。")

            # 規則五: 發文時間不能為空
            if pd.isna(time_value) or time_value == "":  # 如果發文時間為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的發文時間不能為空，請填寫正確的時間。")
            
            # 規則六: 發文圖片格式檢查，如果包含多個圖片，則應使用逗號隔開
            if image_path:  # 如果發文圖片存在
                images = [img.strip() for img in image_path.split(",")]  # 將發文圖片值分割成單個圖片
                if len(images) > 1:  # 只有當有多個圖片時才檢查格式
                    for img in images:  # 遍歷每個圖片
                        if not re.match(r".+\.(jpg|jpeg|png|gif|bmp|webp)$", img, re.IGNORECASE):  # 檢查圖片格式是否正確   
                            errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的發文圖片 '{img}' 格式不正確。多張圖片應以逗號分隔，例如 'image1.jpg, image2.jpg'。")

            # 如果該組發文操作為 TRUE，將其加入列表
            if action:  # 如果發文操作為 TRUE
                post = {  # 構建發文資料
                    "type": post_type,  # 發文類型
                    "group_url": group_url,  # 社團連結
                    "action": action,  # 發文操作
                    "time": time_value,  # 發文時間
                    "content": content,  # 發文文字
                    "image_path": image_path  # 發文圖片
                }
                posts.append(post)  # 將發文資料加入發文列表

            index += 1  # 移動到下一組

        return posts
    
    def _parse_comments(self, row, row_idx, errors, sheet_name):
        """解析留言資料。"""
        comments = []
        index = 1  # 留言組的編號索引

        while True:
            # 定義當前留言組所需的欄位
            expected_columns = [
                f"按讚操作_{index}", f"留言操作_{index}", f"分享操作_{index}",  # 按讚操作、留言操作、分享操作
                f"留言時間_{index}", f"留言網址_{index}", f"留言內容_{index}"  # 留言時間、留言網址、留言內容   
            ]

            # 檢查每個欄位是否存在
            if not all(col in row.index for col in expected_columns):
                break  # 如果欄位不存在，跳出迴圈

            # 構建留言組訊息
            like_value = str(row.get(f"按讚操作_{index}", "FALSE")).upper()  # 獲取按讚操作值
            like_action = like_value == "TRUE" or like_value is True  # 將按讚操作值轉換為布林值
            comment_value = str(row.get(f"留言操作_{index}", "FALSE")).upper()  # 獲取留言操作值
            comment_action = comment_value == "TRUE" or comment_value is True  # 將留言操作值轉換為布林值
            share_value = str(row.get(f"分享操作_{index}", "FALSE")).upper()  # 獲取分享操作值
            share_action = share_value == "TRUE" or share_value is True  # 將分享操作值轉換為布林值 

            comment_time = (
                row.get(f"留言時間_{index}", None).strftime("%Y/%m/%d %H:%M:%S")  # 將留言時間值轉換為指定格式
                if isinstance(row.get(f"留言時間_{index}", None), pd.Timestamp)  # 檢查留言時間值是否為 Pandas Timestamp 類型
                else row.get(f"留言時間_{index}", None)  # 如果留言時間值不是 Pandas Timestamp 類型，則直接使用原值
            )
            comment_url = str(row.get(f"留言網址_{index}", "")).strip()  # 獲取留言網址值
            comment_content = str(row.get(f"留言內容_{index}", "")).strip()  # 獲取留言內容值

            # 規則檢查
            
            # 規則一: 按讚、留言、分享操作只能是 "TRUE" 或 "FALSE"
            for action_value, action_name in zip(  # 遍歷按讚、留言、分享操作
                [like_value, comment_value, share_value],  # 按讚、留言、分享操作值
                ["按讚操作", "留言操作", "分享操作"]  # 按讚、留言、分享操作名稱
            ):
                if action_value not in ["TRUE", "FALSE"]:  # 如果操作值不是 "TRUE" 或 "FALSE"
                    errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的 {action_name} '{action_value}' 無效，僅允許 'TRUE' 或 'FALSE'。")

            # 規則二: 留言時間不能為空
            if pd.isna(comment_time) or comment_time == "":  # 如果留言時間為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的留言時間不能為空，請填寫正確的時間。")

            # 規則三: 留言網址不能為空
            if (
                comment_url is None or  # 檢查是否為 None
                str(comment_url).strip().lower() == "nan" or  # 排除字符串 "nan"
                str(comment_url).strip() == "" or  # 檢查是否為空字符串
                pd.isna(comment_url)  # 檢查是否為 Pandas 的 NaN
            ):
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中留言網址為空。")

            # 規則四: 留言內容不能為空 (僅當留言操作為 True 時檢查)
            if comment_action and (
                comment_content is None or  # 檢查是否為 None
                str(comment_content).strip().lower() == "nan" or  # 排除字符串 "nan"
                str(comment_content).strip() == "" or  # 檢查是否為空字符串
                pd.isna(comment_content)  # 檢查是否為 Pandas 的 NaN
            ):
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中留言內容為空。")

            # 如果操作為 TRUE，加入留言列表
            if like_action or comment_action or share_action:  # 如果按讚、留言、分享操作為 TRUE
                comment = {  # 構建留言資料
                    "like_action": like_action,  # 按讚操作
                    "comment_action": comment_action,  # 留言操作
                    "share_action": share_action,  # 分享操作
                    "time": comment_time,  # 留言時間
                    "url": comment_url,  # 留言網址
                    "content": comment_content  # 留言內容
                }
                comments.append(comment)  # 將留言資料加入留言列表  

            index += 1  # 移動到下一組
        return comments
    
    def _parse_crawls(self, row, row_idx, errors, sheet_name):
        """解析爬蟲資料。"""
        crawls = []
        index = 1  # 爬蟲組的編號索引

        while True:
            # 定義當前爬蟲組所需的欄位
            expected_columns = [ 
                f"爬蟲類型_{index}",  # 爬蟲類型
                f"爬蟲連結_{index}",  # 爬蟲連結
                f"爬蟲操作_{index}",  # 爬蟲操作
                f"爬蟲時間_{index}",  # 爬蟲時間
            ]

            # 檢查每個欄位是否存在
            if not all(col in row.index for col in expected_columns):  # 如果欄位不存在
                break  # 跳出迴圈

            # 構建爬蟲組訊息
            action_value = row.get(f"爬蟲操作_{index}", "FALSE")  # 獲取爬蟲操作值
            action = action_value == "TRUE" or action_value is True  # 將爬蟲操作值轉換為布林值
            crawl_type = str(row.get(f"爬蟲類型_{index}", "")).strip()  # 獲取爬蟲類型值
            crawl_url = str(row.get(f"爬蟲連結_{index}", "")).strip()  # 獲取爬蟲連結值
            crawl_time = (
                row.get(f"爬蟲時間_{index}", None).strftime("%Y/%m/%d %H:%M:%S")  # 將爬蟲時間值轉換為指定格式
                if isinstance(row.get(f"爬蟲時間_{index}", None), pd.Timestamp)  # 檢查爬蟲時間值是否為 Pandas Timestamp 類型
                else row.get(f"爬蟲時間_{index}", None)  # 如果爬蟲時間值不是 Pandas Timestamp 類型，則直接使用原值
            )

            # 規則檢查
            # 規則一: 爬蟲類型只能為 "爬文章" 或 "爬社團名單"
            if crawl_type not in ["爬文章", "爬社團名單"]:  # 如果爬蟲類型不是 "爬文章" 或 "爬社團名單"     
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的爬蟲類型 '{crawl_type}' 無效，僅允許 '爬文章' 或 '爬社團名單'。")

            # 規則二: 爬蟲連結不能為空
            if pd.isna(crawl_url) or crawl_url == "":  # 如果爬蟲連結為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中爬蟲連結為空，請填寫正確的連結。")

            # 規則三: 爬蟲操作只能為 "TRUE" 或 "FALSE"
            if action_value not in ["TRUE", "FALSE", True, False]:  # 如果爬蟲操作值不是 "TRUE" 或 "FALSE"
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的爬蟲操作 '{action_value}' 無效，僅允許 'TRUE' 或 'FALSE'。")

            # 規則四: 爬蟲時間不能為空
            if pd.isna(crawl_time) or crawl_time == "":  # 如果爬蟲時間為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中爬蟲時間不能為空，請填寫正確的時間。")

            # 如果爬蟲操作為 TRUE，加入爬蟲列表
            if action:
                crawl = {
                    "type": crawl_type,  # 爬蟲類型
                    "url": crawl_url,  # 爬蟲連結
                    "action": action,  # 爬蟲操作
                    "time": crawl_time  # 爬蟲時間
                }
                crawls.append(crawl)  # 將爬蟲資料加入爬蟲列表

            index += 1  # 移動到下一組

        return crawls

    def _parse_clicks(self, row, row_idx, errors, sheet_name):
        """解析點擊資料。"""
        clicks = []
        index = 1  # 點擊組的編號索引

        while True:
            # 定義當前點擊組所需的欄位
            expected_columns = [ 
                f"點擊連結_{index}",  # 點擊連結
                f"點擊操作_{index}",  # 點擊操作
            ]
            
            # 檢查每個欄位是否存在
            if not all(col in row.index for col in expected_columns):  # 如果欄位不存在
                break  # 跳出迴圈

            # 構建點擊組訊息
            action_value = row.get(f"點擊操作_{index}", "FALSE")  # 獲取點擊操作值
            action = action_value == "TRUE" or action_value is True  # 將點擊操作值轉換為布林值
            click_url = str(row.get(f"點擊連結_{index}", "")).strip()  # 獲取點擊連結值
            
            # 規則檢查
            # 規則一: 點擊連結不能為空
            if pd.isna(click_url) or click_url == "":  # 如果點擊連結為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中點擊連結為空，請填寫正確的連結。")

            # 規則二: 點擊操作只能為 "TRUE" 或 "FALSE"
            if action_value not in ["TRUE", "FALSE", True, False]:  # 如果點擊操作值不是 "TRUE" 或 "FALSE"
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的點擊操作 '{action_value}' 無效，僅允許 'TRUE' 或 'FALSE'。")

            # 如果點擊操作為 TRUE，加入點擊列表
            if action:
                click = {
                    "url": click_url,  # 點擊連結
                    "action": action  # 點擊操作
                }
                clicks.append(click)  # 將點擊資料加入爬蟲列表

            index += 1  # 移動到下一組
        print(f"clicks : {clicks}")
        return clicks
    
    def _parse_navigates(self, row, row_idx, errors, sheet_name):
        """解析點擊資料。"""
        navigates = []
        index = 1  # 點擊組的編號索引

        while True:
            # 定義當前點擊組所需的欄位
            expected_columns = [ 
                f"跳轉連結_{index}",  # 點擊連結
                f"跳轉外部連結_{index}",  # 點擊連結
                f"跳轉操作_{index}",  # 點擊操作
            ]
            
            # 檢查每個欄位是否存在
            if not all(col in row.index for col in expected_columns):  # 如果欄位不存在
                break  # 跳出迴圈

            # 構建點擊組訊息
            action_value = row.get(f"跳轉操作_{index}", "FALSE")  # 獲取跳轉操作值
            action = action_value == "TRUE" or action_value is True  # 將跳轉操作值轉換為布林值
            navigate_url = str(row.get(f"跳轉連結_{index}", "")).strip()  # 獲取跳轉連結值
            navigate_out_url = str(row.get(f"跳轉外部連結_{index}", "")).strip()  # 獲取跳轉外部連結值
            
            # 規則檢查
            # 規則一: 跳轉連結不能為空
            if pd.isna(navigate_url) or navigate_url == "":  # 如果跳轉連結為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中跳轉連結為空，請填寫正確的連結。")
                
            # 規則二: 跳轉外部連結不能為空
            if pd.isna(navigate_out_url) or navigate_out_url == "":  # 如果跳轉外部連結為空
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組中跳轉外部連結為空，請填寫正確的連結。")

            # 規則二: 點擊操作只能為 "TRUE" 或 "FALSE"
            if action_value not in ["TRUE", "FALSE", True, False]:  # 如果點擊操作值不是 "TRUE" 或 "FALSE"
                errors.append(f"[{sheet_name}] 錯誤：第 {row_idx + 2} 列的第 {index} 組的點擊操作 '{action_value}' 無效，僅允許 'TRUE' 或 'FALSE'。")

            # 如果點擊操作為 TRUE，加入點擊列表
            if action:
                navigate = {
                    "url": navigate_url,  # 點擊連結
                    "out_url": navigate_out_url,  # 點擊連結
                    "action": action  # 點擊操作
                }
                navigates.append(navigate)  # 將點擊資料加入爬蟲列表

            index += 1  # 移動到下一組
        return navigates