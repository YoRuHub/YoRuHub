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
            if rand < 0.55:
                count = 0
            elif rand < 0.82:
                count = random.randint(1, 2)
            elif rand < 0.94:
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

def get_flower_svg(cx, cy, flower_type, main_color, center_color):
    """異なる形状のランダムな花を生成するSVGヘルパー"""
    if flower_type == 0:
        # 5弁花 (Cherry Blossom / Daisy)
        return f"""<g transform="translate({cx:.2f}, {cy:.2f})">
          <circle cx="0" cy="-2.5" r="2.1" fill="{main_color}" />
          <circle cx="2.4" cy="-0.8" r="2.1" fill="{main_color}" />
          <circle cx="1.5" cy="2.1" r="2.1" fill="{main_color}" />
          <circle cx="-1.5" cy="2.1" r="2.1" fill="{main_color}" />
          <circle cx="-2.4" cy="-0.8" r="2.1" fill="{main_color}" />
          <circle cx="0" cy="0" r="1.7" fill="{center_color}" />
        </g>"""
    elif flower_type == 1:
        # 4弁花 (Clover flower / Hydrangea)
        return f"""<g transform="translate({cx:.2f}, {cy:.2f})">
          <circle cx="0" cy="-2.4" r="2.2" fill="{main_color}" />
          <circle cx="2.4" cy="0" r="2.2" fill="{main_color}" />
          <circle cx="0" cy="2.4" r="2.2" fill="{main_color}" />
          <circle cx="-2.4" cy="0" r="2.2" fill="{main_color}" />
          <circle cx="0" cy="0" r="1.6" fill="{center_color}" />
        </g>"""
    elif flower_type == 2:
        # チューリップ (Tulip)
        return f"""<g transform="translate({cx:.2f}, {cy:.2f})">
          <path d="M-2.8,-3.2 C-3.8,0 -2.3,3.2 0,3.2 C2.3,3.2 3.8,0 2.8,-3.2 C1.8,-1 0.9,0 0,-1.4 C-0.9,0 -1.8,-1 -2.8,-3.2 Z" fill="{main_color}" />
          <circle cx="0" cy="-0.4" r="1.2" fill="{center_color}" />
        </g>"""
    elif flower_type == 3:
        # 8弁 デイジー (8-petal Daisy)
        petals = "".join([f'<circle cx="{r*cos:.1f}" cy="{r*sin:.1f}" r="1.4" fill="{main_color}" />' 
                         for r, cos, sin in [(2.2, 0, -1), (2.2, 0.707, -0.707), (2.2, 1, 0), (2.2, 0.707, 0.707),
                                             (2.2, 0, 1), (2.2, -0.707, 0.707), (2.2, -1, 0), (2.2, -0.707, -0.707)]])
        return f"""<g transform="translate({cx:.2f}, {cy:.2f})">{petals}<circle cx="0" cy="0" r="1.6" fill="{center_color}" /></g>"""
    else:
        # 星型スターフラワー (Star Bloom)
        return f"""<g transform="translate({cx:.2f}, {cy:.2f})">
          <path d="M0,-4.2 L1.1,-1.1 L4.2,0 L1.1,1.1 L0,4.2 L-1.1,1.1 L-4.2,0 L-1.1,-1.1 Z" fill="{main_color}" />
          <circle cx="0" cy="0" r="1.4" fill="{center_color}" />
        </g>"""

def build_svg(calendar_data):
    """マスの完全中央から生える植物とリアルな土質感グラデーションSVGをビルドする"""
    weeks = calendar_data["weeks"]
    if len(weeks) > 53:
        weeks = weeks[-53:]
        
    cell_size = 16
    gap = 3.5
    padding_left = 42
    padding_right = 20
    header_height = 32
    footer_height = 28
    
    cols = len(weeks)
    rows = 7
    
    width = int(padding_left + cols * (cell_size + gap) + padding_right)
    height = int(header_height + rows * (cell_size + gap) + footer_height)
    
    svg_header = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <!-- リアルな土・草地のラジアルグラデーション (中央から外側へ立体感を演出) -->
    <radialGradient id="soil-0" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#34241a" />
      <stop offset="100%" stop-color="#1a110c" />
    </radialGradient>
    <radialGradient id="soil-1" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#3d301c" />
      <stop offset="100%" stop-color="#1f180e" />
    </radialGradient>
    <radialGradient id="soil-2" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#234c1b" />
      <stop offset="100%" stop-color="#10260c" />
    </radialGradient>
    <radialGradient id="soil-3" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#18591b" />
      <stop offset="100%" stop-color="#09300c" />
    </radialGradient>
  </defs>

  <style>
    .bg {{ fill: #0b0f17; rx: 10px; }}
    .label-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10.5px; font-weight: 500; fill: #7d8590; }}
    .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #8b949e; }}
    @keyframes sway {{
      0%, 100% {{ transform: rotate(-3.5deg); }}
      50% {{ transform: rotate(3.5deg); }}
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

    # パレット
    flower_colors = ["#ff2a85", "#ff7a00", "#38bdf8", "#a855f7", "#ec4899", "#ff4757", "#2ed573", "#f59e0b"]
    center_colors = ["#fff066", "#ffffff", "#ffe600", "#facc15"]

    # 各セルと描画要素
    for row in range(rows):
        for col in range(cols):
            if row >= len(weeks[col]["contributionDays"]):
                continue
                
            day_data = weeks[col]["contributionDays"][row]
            count = day_data["contributionCount"]
            
            x = padding_left + col * (cell_size + gap)
            y = header_height + row * (cell_size + gap)
            
            # **【マス完全中央での上下左右バランス計算】**
            cx = x + (cell_size / 2.0)  # x + 8.0 (左右真ん中)
            cy = y + (cell_size / 2.0)  # y + 8.0 (上下真ん中)
            by = y + cell_size - 3.2    # 植物の茎の起点 (y + 12.8: マス中心部から生えるバランス)
            
            delay = round((col * 0.07 + row * 0.11) % 3.0, 2)
            duration = round(2.7 + (col % 4) * 0.3, 2)
            
            # リアルなグラデーション土の指定
            if count == 0:
                soil_id = "soil-0"
            elif count <= 2:
                soil_id = "soil-1"
            elif count <= 5:
                soil_id = "soil-2"
            else:
                soil_id = "soil-3"
                
            cell_rect = f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size}" height="{cell_size}" rx="3.5" fill="url(#{soil_id})" />'
            
            # 土の質感をより表現する微小な粒子ドット（0コミット時含む質感演出）
            soil_texture = ""
            if count == 0:
                # 土粒子ドットで非平坦な土感を演出
                d1_x, d1_y = x + 4, y + 11
                d2_x, d2_y = x + 11, y + 5
                soil_texture = f'<circle cx="{d1_x}" cy="{d1_y}" r="0.6" fill="#4d3525" opacity="0.5" /><circle cx="{d2_x}" cy="{d2_y}" r="0.6" fill="#120b07" opacity="0.6" />'

            plant_element = ""
            if count == 0:
                pass
            elif count <= 2:
                # 芽 (Sprout) - マスの中央 (cx, cy) に上下左右ぴったり収まる設計！
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{cx:.2f}px {by:.2f}px;"><path d="M{cx:.2f},{by:.2f} Q{cx:.2f},{cy+1.0:.1f} {cx:.2f},{cy-1.5:.1f}" stroke="#6eb014" stroke-width="1.8" fill="none" stroke-linecap="round" /><path d="M{cx:.2f},{cy-1.0:.1f} C{cx-3.8:.2f},{cy-2.2:.1f} {cx-3.8:.2f},{cy-5.0:.1f} {cx-.2:.2f},{cy-4.0:.1f} Z" fill="#9ce82b" /><path d="M{cx:.2f},{cy-1.0:.1f} C{cx+3.8:.2f},{cy-2.2:.1f} {cx+3.8:.2f},{cy-5.0:.1f} {cx+.2:.2f},{cy-4.0:.1f} Z" fill="#75c419" /></g>"""
            elif count <= 5:
                # 蕾 (Bud) - マス中央バランス
                bud_color = "#ff69b4" if (col + row) % 2 == 0 else "#ffcc00"
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{cx:.2f}px {by:.2f}px;"><path d="M{cx:.2f},{by:.2f} Q{cx-.5:.2f},{cy+2.0:.1f} {cx:.2f},{cy-2.5:.1f}" stroke="#3bb852" stroke-width="1.8" fill="none" stroke-linecap="round" /><path d="M{cx:.2f},{cy+2.5:.1f} C{cx-3.6:.2f},{cy+1.5:.1f} {cx-3.6:.2f},{cy-.5:.1f} {cx-.3:.2f},{cy+.5:.1f} Z" fill="#2ca043" /><circle cx="{cx:.2f}" cy="{cy-3.5:.1f}" r="2.6" fill="{bud_color}" /><circle cx="{cx:.2f}" cy="{cy-3.5:.1f}" r="1.1" fill="#ffffff" opacity="0.85" /></g>"""
            else:
                # 満開の花 (Flower) - マス中央バランス ＋ マルチ形状・多配色
                hash_val = (col * 13 + row * 7 + count * 3)
                flower_type = hash_val % 5
                main_color = flower_colors[hash_val % len(flower_colors)]
                center_color = center_colors[(hash_val // 2) % len(center_colors)]
                
                flower_svg = get_flower_svg(cx, cy - 3.2, flower_type, main_color, center_color)
                
                plant_element = f"""<g class="sway" style="animation-delay:{delay}s;animation-duration:{duration}s;transform-origin:{cx:.2f}px {by:.2f}px;"><path d="M{cx:.2f},{by:.2f} L{cx:.2f},{cy-1.5:.1f}" stroke="#22c55e" stroke-width="2.0" stroke-linecap="round" /><path d="M{cx:.2f},{cy+3.0:.1f} C{cx-3.8:.2f},{cy+2.0:.1f} {cx-3.8:.2f},{cy+0.0:.1f} {cx-.5:.2f},{cy+1.0:.1f} Z" fill="#15803d" />{flower_svg}</g>"""
                
            svg_body.append(f"{cell_rect}{soil_texture}{plant_element}")

    # 下部タイトル
    legend_y = height - 10.0
    
    svg_footer = f"""
  <!-- Footer Title Only -->
  <text x="{padding_left}" y="{legend_y:.1f}" class="legend-text">🌱 Contribution Garden (Past 53 weeks)</text>
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
