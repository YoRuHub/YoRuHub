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
    start_date = datetime.now() - timedelta(weeks=53)
    start_date -= timedelta(days=start_date.weekday())
    
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
    """リアルな🌱と見やすい華やかな花のデザインで1年分（53週）の庭SVGをビルドする"""
    weeks = calendar_data["weeks"]
    if len(weeks) > 53:
        weeks = weeks[-53:]
        
    # 各マスのサイズを少し広げて 16px * 16px（隙間 3.5px）にし視認性とグラフィック表現力を向上
    cell_size = 16
    gap = 3.5
    padding_left = 42
    padding_right = 20
    header_height = 32
    footer_height = 38
    
    cols = len(weeks)
    rows = 7
    
    width = int(padding_left + cols * (cell_size + gap) + padding_right)
    height = int(header_height + rows * (cell_size + gap) + footer_height)
    
    svg_header = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <style>
    .bg {{ fill: #0b0f17; rx: 10px; }}
    .label-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10.5px; font-weight: 500; fill: #7d8590; }}
    .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #8b949e; }}
    @keyframes sway {{
      0%, 100% {{ transform: rotate(-4deg); }}
      50% {{ transform: rotate(4deg); }}
    }}
    .sway {{ animation: sway 3.5s ease-in-out infinite; }}
  </style>
  <rect width="{width}" height="{height}" class="bg" />
"""

    svg_body = []
    
    # 曜日ラベル (Mon, Wed, Fri)
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for day_idx, label in day_labels.items():
        y_pos = header_height + day_idx * (cell_size + gap) + 12
        svg_body.append(f'  <text x="10" y="{y_pos:.1f}" class="label-text">{label}</text>')

    # 月ラベル
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1
    for col in range(cols):
        first_day_of_week = weeks[col]["contributionDays"][0]
        date_obj = datetime.strptime(first_day_of_week["date"], "%Y-%m-%d")
        current_month = date_obj.month
        
        if current_month != last_month:
            x_pos = padding_left + col * (cell_size + gap)
            month_label = month_names[current_month - 1]
            svg_body.append(f'  <text x="{x_pos:.1f}" y="20" class="label-text">{month_label}</text>')
            last_month = current_month

    # 各セルと描画要素
    for row in range(rows):
        for col in range(cols):
            if row >= len(weeks[col]["contributionDays"]):
                continue
                
            day_data = weeks[col]["contributionDays"][row]
            count = day_data["contributionCount"]
            
            x = padding_left + col * (cell_size + gap)
            y = header_height + row * (cell_size + gap)
            
            origin_x = x + (cell_size / 2)
            origin_y = y + cell_size - 1
            
            delay = round((col * 0.07 + row * 0.11) % 3.0, 2)
            duration = round(2.7 + (col % 4) * 0.3, 2)
            
            # マスの背景色（落ち着いた上質な土〜芝生トーン）
            if count == 0:
                bg_color = "#211814" # 洗練された深みのある暗茶色（土）
            elif count <= 2:
                bg_color = "#2a2417" # 芽吹きを感じる萌芽色
            elif count <= 5:
                bg_color = "#183818" # 豊かな芝生緑
            else:
                bg_color = "#0f4216" # 鮮やかな深緑
                
            cell_rect = f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size}" height="{cell_size}" rx="3" fill="{bg_color}" />'
            
            plant_element = ""
            if count == 0:
                # 0コミット：土のみ（無駄なドットは排除して美しいグリッドに）
                pass
            elif count <= 2:
                # 芽 (Sprout) - 本物の 🌱 (ふっくらした2枚の葉と曲線的な茎)
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{origin_x:.1f}px {origin_y:.1f}px;"><path d="M{x+8:.1f},{y+15:.1f} Q{x+8:.1f},{y+10:.1f} {x+7.5:.1f},{y+6.5:.1f}" stroke="#70a825" stroke-width="1.8" fill="none" stroke-linecap="round" /><path d="M{x+7.5:.1f},{y+7:.1f} C{x+3.5:.1f},{y+6:.1f} {x+2.5:.1f},{y+2.5:.1f} {x+7:.1f},{y+3.5:.1f} Z" fill="#9fe832" /><path d="M{x+7.5:.1f},{y+7:.1f} C{x+11.5:.1f},{y+6:.1f} {x+12.5:.1f},{y+2.5:.1f} {x+8.5:.1f},{y+3.5:.1f} Z" fill="#78c41d" /></g>"""
            elif count <= 5:
                # 蕾・若葉 (Bud)
                bud_color = "#ff69b4" if count % 2 == 0 else "#ffcc00"
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{origin_x:.1f}px {origin_y:.1f}px;"><path d="M{x+8:.1f},{y+15:.1f} Q{x+7.5:.1f},{y+10:.1f} {x+8:.1f},{y+5.5:.1f}" stroke="#3bb852" stroke-width="1.8" fill="none" stroke-linecap="round" /><path d="M{x+7.8:.1f},{y+10.5:.1f} C{x+3.8:.1f},{y+9.5:.1f} {x+3.5:.1f},{y+7.5:.1f} {x+7.5:.1f},{y+8.5:.1f} Z" fill="#2ca043" /><circle cx="{x+8:.1f}" cy="{y+4.5:.1f}" r="2.8" fill="{bud_color}" /><circle cx="{x+8:.1f}" cy="{y+4.5:.1f}" r="1.3" fill="#ffffff" opacity="0.7" /></g>"""
            else:
                # 満開の花 (Flower) - 大きくパッと目を引く見やすい花びらデザイン
                if count >= 10:
                    flower_color = "#ff2a85" # 鮮やかローズピンク
                    center_color = "#fff066"
                elif count >= 8:
                    flower_color = "#38bdf8" # 爽やかなシアンブルー
                    center_color = "#ffffff"
                else:
                    flower_color = "#ff8c00" # 鮮やかなサンセットオレンジ
                    center_color = "#ffe600"
                    
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{origin_x:.1f}px {origin_y:.1f}px;"><path d="M{x+8:.1f},{y+15:.1f} L{x+8:.1f},{y+6.5:.1f}" stroke="#22c55e" stroke-width="2.2" stroke-linecap="round" /><path d="M{x+8:.1f},{y+11.5:.1f} C{x+3.5:.1f},{y+10.5:.1f} {x+3.5:.1f},{y+8.5:.1f} {x+7.5:.1f},{y+9.5:.1f} Z" fill="#15803d" /><g transform="translate({x+8:.1f}, {y+5.5:.1f})"><circle cx="0" cy="-3" r="2.3" fill="{flower_color}" /><circle cx="3" cy="-1" r="2.3" fill="{flower_color}" /><circle cx="2" cy="3" r="2.3" fill="{flower_color}" /><circle cx="-2" cy="3" r="2.3" fill="{flower_color}" /><circle cx="-3" cy="-1" r="2.3" fill="{flower_color}" /><circle cx="0" cy="0" r="2.0" fill="{center_color}" /></g></g>"""
                
            svg_body.append(f"{cell_rect}{plant_element}")

    # 凡例 (Legend) - Less / More テキストを削除してクリーンな表示に
    legend_y = height - footer_height + 24
    legend_x_start = width - padding_right - 145
    
    svg_footer = f"""
  <!-- Legend -->
  <text x="{padding_left}" y="{legend_y:.1f}" class="legend-text">🌱 Contribution Garden (Past 53 weeks)</text>
  <g transform="translate({legend_x_start:.1f}, {legend_y - 12:.1f})">
    <!-- 0: 土 -->
    <rect x="0" y="0" width="13" height="13" rx="2.5" fill="#211814" />
    
    <!-- 1-2: 芽 -->
    <g transform="translate(32, 0)">
      <rect x="0" y="0" width="13" height="13" rx="2.5" fill="#2a2417" />
      <path d="M6.5,11 Q6.5,8 6,5" stroke="#70a825" stroke-width="1.3" fill="none" />
      <path d="M6,5.5 C3,5 2.5,2.5 6,3 Z" fill="#9fe832" />
      <path d="M6,5.5 C9,5 9.5,2.5 7,3 Z" fill="#78c41d" />
    </g>
    
    <!-- 3-5: 蕾 -->
    <g transform="translate(64, 0)">
      <rect x="0" y="0" width="13" height="13" rx="2.5" fill="#183818" />
      <line x1="6.5" y1="11" x2="6.5" y2="4.5" stroke="#3bb852" stroke-width="1.3" />
      <circle cx="6.5" cy="4" r="2" fill="#ffcc00" />
    </g>
    
    <!-- 6+: 満開の花 -->
    <g transform="translate(96, 0)">
      <rect x="0" y="0" width="13" height="13" rx="2.5" fill="#0f4216" />
      <line x1="6.5" y1="11" x2="6.5" y2="5" stroke="#22c55e" stroke-width="1.5" />
      <circle cx="6.5" cy="4" r="2.5" fill="#ff2a85" />
      <circle cx="6.5" cy="4" r="1" fill="#fff066" />
    </g>
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
