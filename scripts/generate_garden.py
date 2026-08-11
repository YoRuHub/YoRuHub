#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import random

def get_contributions(username, token):
    """GitHub GraphQL APIから過去53週間のコントリビューションデータを取得する"""
    to_date = datetime.utcnow()
    # 過去53週間分取得して1年分のカレンダーにする
    from_date = to_date - timedelta(weeks=53)
    to_str = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    from_str = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = json.dumps({
        "query": query,
        "variables": {
            "login": username,
            "from": from_str,
            "to": to_str
        }
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=data,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            response = json.loads(res.read().decode("utf-8"))
            if "errors" in response:
                print("GraphQL Errors:", response["errors"], file=sys.stderr)
                return None
            return response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except urllib.error.URLError as e:
        print("API request failed:", e, file=sys.stderr)
        return None

def generate_mock_data():
    """ローカルテスト用の1年分のモックデータを生成する"""
    print("Using mock data for generation...", file=sys.stderr)
    weeks = []
    # 53週間分
    start_date = datetime.now() - timedelta(weeks=53)
    start_date -= timedelta(days=start_date.weekday()) # 日曜日開始に合わせる
    
    current_date = start_date
    for w in range(53):
        days = []
        for d in range(7):
            rand = random.random()
            if rand < 0.6:
                count = 0
            elif rand < 0.85:
                count = random.randint(1, 2)
            elif rand < 0.96:
                count = random.randint(3, 5)
            else:
                count = random.randint(6, 15)
                
            days.append({
                "contributionCount": count,
                "date": current_date.strftime("%Y-%m-%d"),
                "weekday": d
            })
            current_date += timedelta(days=1)
        weeks.append({"contributionDays": days})
    return {"weeks": weeks}

def build_svg(calendar_data):
    """GitHub UI完全準拠の1年分（53週）のコントリビューション箱庭SVGをビルドする"""
    weeks = calendar_data["weeks"]
    # 53週分に制限
    if len(weeks) > 53:
        weeks = weeks[-53:]
        
    # レイアウトパラメータ
    cell_size = 15
    gap = 3
    padding_left = 40   # 曜日ラベル用スペース
    padding_right = 20
    header_height = 30  # 月ラベル用スペース
    footer_height = 40  # 凡例用スペース
    
    cols = len(weeks)
    rows = 7
    
    width = padding_left + cols * (cell_size + gap) + padding_right
    height = header_height + rows * (cell_size + gap) + footer_height
    
    svg_header = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <style>
    .bg {{ fill: #0d1117; rx: 8px; }}
    .label-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 10px; fill: #7d8590; }}
    .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 11px; fill: #8b949e; }}
    @keyframes sway {{
      0%, 100% {{ transform: rotate(-4deg); }}
      50% {{ transform: rotate(4deg); }}
    }}
    .sway {{ animation: sway 3.5s ease-in-out infinite; }}
  </style>
  <rect width="{width}" height="{height}" class="bg" />
"""

    svg_body = []
    
    # 曜日ラベルを描画 (Mon, Wed, Fri のみ表示するのがGitHub標準)
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for day_idx, label in day_labels.items():
        y_pos = header_height + day_idx * (cell_size + gap) + 11
        svg_body.append(f'  <text x="10" y="{y_pos}" class="label-text">{label}</text>')

    # 月ラベルを描画 (月が変わる最初の週の上に月名を配置する)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1
    for col in range(cols):
        # その週の最初の日の日付から月を取得
        first_day_of_week = weeks[col]["contributionDays"][0]
        date_obj = datetime.strptime(first_day_of_week["date"], "%Y-%m-%d")
        current_month = date_obj.month
        
        if current_month != last_month:
            x_pos = padding_left + col * (cell_size + gap)
            month_label = month_names[current_month - 1]
            svg_body.append(f'  <text x="{x_pos}" y="20" class="label-text">{month_label}</text>')
            last_month = current_month

    # セル（庭のマス）と植物を描画
    for row in range(rows):
        for col in range(cols):
            # データが存在しない場合のプレースホルダ（年の最初や最後の不完全な週）
            if row >= len(weeks[col]["contributionDays"]):
                continue
                
            day_data = weeks[col]["contributionDays"][row]
            count = day_data["contributionCount"]
            
            x = padding_left + col * (cell_size + gap)
            y = header_height + row * (cell_size + gap)
            
            # 各セルの原点（底面中央）を揺らぎの中心点とする
            origin_x = x + (cell_size / 2)
            origin_y = y + cell_size - 1
            
            # 自然な揺らぎ設定
            delay = round((col * 0.08 + row * 0.12) % 3.0, 2)
            duration = round(2.8 + (col % 4) * 0.3, 2)
            
            # コミット数に応じたマスの背景色（GitHubの緑と調和する土/草色の四角）
            # コミット0: 茶色の土
            # コミット1-2: やや緑がかった茶色
            # コミット3-5: 薄い緑（芝生）
            # コミット6+: 濃い緑（満開の芝生）
            if count == 0:
                bg_color = "#322319" # 暗い茶色
            elif count <= 2:
                bg_color = "#3d321d" # 黄緑がかった茶色
            elif count <= 5:
                bg_color = "#244519" # 薄い緑
            else:
                bg_color = "#163c0f" # 濃い緑
                
            cell_rect = f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2" fill="{bg_color}" />'
            
            # マスの中の植物
            plant_element = ""
            if count == 0:
                # 0コミットは土のみ（中央に小さな盛り土ドットを配置して土感を出す）
                plant_element = f'<rect x="{x+6}" y="{y+12}" width="3" height="1" fill="#4e342e" />'
            elif count <= 2:
                # 芽 (Sprout) - 2ピクセル程度の極小デザイン
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{origin_x}px {origin_y}px;"><line x1="{x+7.5}" y1="{y+14}" x2="{x+7.5}" y2="{y+9}" stroke="#a3e635" stroke-width="1.5" stroke-linecap="round" /><path d="M{x+7.5},{y+9} Q{x+4.5},{y+8} {x+5.5},{y+6} Z" fill="#84cc16" /><path d="M{x+7.5},{y+9} Q{x+10.5},{y+8} {x+9.5},{y+6} Z" fill="#84cc16" /></g>"""
            elif count <= 5:
                # 茎と蕾 (Bud) - マスに収まる高さのデザイン
                bud_color = "#f472b6" if count % 2 == 0 else "#fbbf24"
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{origin_x}px {origin_y}px;"><line x1="{x+7.5}" y1="{y+14}" x2="{x+7.5}" y2="{y+6}" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round" /><circle cx="{x+7.5}" cy="{y+5}" r="2" fill="{bud_color}" /><path d="M{x+7.5},{y+10} Q{x+4.5},{y+9} {x+5.5},{y+8} Z" fill="#22c55e" /></g>"""
            else:
                # 花 (Flower) - ドット絵風の綺麗な花びら
                if count >= 10:
                    flower_color = "#ec4899" # ピンク
                    center_color = "#facc15"
                elif count >= 8:
                    flower_color = "#3b82f6" # 青
                    center_color = "#ffffff"
                else:
                    flower_color = "#f97316" # オレンジ
                    center_color = "#facc15"
                    
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{origin_x}px {origin_y}px;"><line x1="{x+7.5}" y1="{y+14}" x2="{x+7.5}" y2="{y+5}" stroke="#22c55e" stroke-width="1.8" /><circle cx="{x+7.5}" cy="{y+5}" r="2.5" fill="{flower_color}" /><circle cx="{x+5}" cy="{y+5}" r="1.5" fill="{flower_color}" /><circle cx="{x+10}" cy="{y+5}" r="1.5" fill="{flower_color}" /><circle cx="{x+7.5}" cy="{y+2.5}" r="1.5" fill="{flower_color}" /><circle cx="{x+7.5}" cy="{y+7.5}" r="1.5" fill="{flower_color}" /><circle cx="{x+7.5}" cy="{y+5}" r="1.2" fill="{center_color}" /></g>"""
                
            svg_body.append(f"{cell_rect}{plant_element}")

    # 凡例 (Legend) の描画位置
    legend_y = height - footer_height + 25
    legend_x_start = width - padding_right - 180
    
    svg_footer = f"""
  <!-- Legend -->
  <text x="{padding_left}" y="{legend_y}" class="legend-text">🌱 Contribution Garden (Past 53 weeks)</text>
  <g transform="translate({legend_x_start}, {legend_y - 10})">
    <!-- 0 -->
    <rect x="0" y="0" width="12" height="12" rx="1.5" fill="#322319" />
    <rect x="5" y="10" width="2" height="1" fill="#4e342e" />
    
    <!-- 1-2 -->
    <g transform="translate(35, 0)">
      <rect x="0" y="0" width="12" height="12" rx="1.5" fill="#3d321d" />
      <line x1="6" y1="11" x2="6" y2="7" stroke="#a3e635" stroke-width="1.2" />
      <circle cx="6" cy="6" r="1" fill="#84cc16" />
    </g>
    
    <!-- 3-5 -->
    <g transform="translate(70, 0)">
      <rect x="0" y="0" width="12" height="12" rx="1.5" fill="#244519" />
      <line x1="6" y1="11" x2="6" y2="5" stroke="#4ade80" stroke-width="1.2" />
      <circle cx="6" cy="4" r="1.2" fill="#fbbf24" />
    </g>
    
    <!-- 6+ -->
    <g transform="translate(105, 0)">
      <rect x="0" y="0" width="12" height="12" rx="1.5" fill="#163c0f" />
      <line x1="6" y1="11" x2="6" y2="4" stroke="#22c55e" stroke-width="1.5" />
      <circle cx="6" cy="4" r="2" fill="#ec4899" />
      <circle cx="6" cy="4" r="0.8" fill="#facc15" />
    </g>
    
    <text x="-15" y="10" class="label-text">Less</text>
    <text x="125" y="10" class="label-text">More</text>
  </g>
</svg>
"""

    return svg_header + "".join(svg_body) + svg_footer

def main():
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not username:
        username = "YoRuHub"
        
    token = os.environ.get("GITHUB_TOKEN")
    
    calendar_data = None
    if token:
        print(f"Fetching contribution data for {username}...", file=sys.stderr)
        calendar_data = get_contributions(username, token)
        
    if not calendar_data:
        calendar_data = generate_mock_data()
        
    svg_content = build_svg(calendar_data)
    
    output_dir = "dist"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "garden-contribution-graph.svg")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"Successfully generated garden SVG at {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
