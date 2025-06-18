from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Cấu hình Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Không hiển thị trình duyệt
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)

# Mở trang FootballTransfers
url = "https://www.footballtransfers.com/en/players/values"
driver.get(url)
time.sleep(10)  # Tăng thời gian đợi cho chắc chắn trang đã load xong

# Lưu toàn bộ nội dung HTML để kiểm tra nếu cần
with open("page_source.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

# Bắt đầu quét dữ liệu
players_data = []
try:
    # Giả định selector (bạn cần kiểm tra page_source.html để tìm đúng class thực tế)
    rows = driver.find_elements(By.CSS_SELECTOR, "div.player-list-item")  # Gợi ý tên khác có thể đúng
    print("Find {len(rows)} player.")

    for row in rows:
        try:
            player = row.find_element(By.CSS_SELECTOR, ".player-name").text.strip()
            squad = row.find_element(By.CSS_SELECTOR, ".team-name").text.strip()
            minutes_str = row.find_element(By.CSS_SELECTOR, ".minutes-played").text.strip()
            etv_str = row.find_element(By.CSS_SELECTOR, ".etv-value").text.strip()

            minutes = float(minutes_str.replace(',', ''))
            etv = float(etv_str.replace('€', '').replace('m', '').replace('M', ''))
            if minutes > 900:
                players_data.append({'Player': player, 'Squad': squad, 'Min': minutes, 'ETV': etv})
        except Exception as e:
            print("Player handling error:", e)
finally:
    driver.quit()

# Ghi ra file CSV
df = pd.DataFrame(players_data)
df.to_csv("transfer_values.csv", index=False)
print(f"Saved {len(df)} player in file transfer_values.csv.")

