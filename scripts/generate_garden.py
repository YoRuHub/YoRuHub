#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import random

def get_contributions(username, token):
    """GitHub GraphQL APIから直近12週間（84日）のコントリビューションデータを取得する"""
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
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
        "variables": {"login": username}
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=data,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            if "errors" in response:
                print("GraphQL Errors:", response["errors"], file=sys.stderr)
                return None
            return response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except urllib.error.URLError as e:
        print("API request failed:", e, file=sys.stderr)
        return None

def generate_mock_data():
    """APIリクエストが失敗した場合やローカルテスト用のモックデータを生成する"""
    print("Using mock data for generation...", file=sys.stderr)
    weeks = []
    start_date = datetime.now() - timedelta(weeks=12)
    # 直近の月曜日あたりから開始するように調整
    start_date -= timedelta(days=start_date.weekday())
    
    current_date = start_date
    for w in range(12):
        days = []
        for d in range(7):
            # コミット数をランダムに分散（0が多い、たまに花が咲くように）
            rand = random.random()
            if rand < 0.5:
                count = 0
            elif rand < 0.8:
                count = random.randint(1, 2)
            elif rand < 0.95:
                count = random.randint(3, 5)
            else:
                count = random.randint(6, 12)
                
            days.append({
                "contributionCount": count,
                "date": current_date.strftime("%Y-%m-%d"),
                "weekday": d
            })
            current_date += timedelta(days=1)
        weeks.append({"contributionDays": days})
    return {"weeks": weeks}

def build_svg(calendar_data):
    """取得したデータから風に揺れる箱庭SVGをビルドする"""
    # 直近12週間分を取得
    weeks = calendar_data["weeks"]
    if len(weeks) > 12:
        weeks = weeks[-12:]
        
    # SVGパラメータ
    cell_size = 40
    padding = 20
    header_height = 40
    footer_height = 30
    
    cols = len(weeks)
    rows = 7 # 日〜土
    
    width = cols * cell_size + padding * 2
    height = rows * cell_size + padding * 2 + header_height + footer_height
    
    svg_header = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <style>
    .bg {{
      fill: #0d1117;
      rx: 10px;
    }}
    .title {{
      font-family: 'Segoe UI', Ubuntu, sans-serif;
      font-weight: 600;
      font-size: 16px;
      fill: #e6edf3;
    }}
    .legend-text {{
      font-family: 'Segoe UI', Ubuntu, sans-serif;
      font-size: 11px;
      fill: #7d8590;
    }}
    @keyframes sway {{
      0%, 100% {{ transform: rotate(-3deg); }}
      50% {{ transform: rotate(3deg); }}
    }}
    .sway {{
      animation: sway 3s ease-in-out infinite;
    }}
  </style>
  <rect width="{width}" height="{height}" class="bg" />
  <text x="{padding}" y="{padding + 20}" class="title">My Contribution Garden 🌸</text>
"""

    svg_body = ""
    
    # 曜日ラベル (S, M, T, W, T, F, S)
    # 7行描画
    for row in range(rows):
        for col in range(cols):
            day_data = weeks[col]["contributionDays"][row] if row < len(weeks[col]["contributionDays"]) else None
            if not day_data:
                continue
                
            count = day_data["contributionCount"]
            
            x = padding + col * cell_size
            y = padding + header_height + row * cell_size
            
            # 各マスの原点 (20, 35) を sway の transform-origin とする
            origin_x = x + 20
            origin_y = y + 35
            
            # アニメーションのディレイをグリッドの位置でずらして自然な揺らぎにする
            delay = round((col * 0.15 + row * 0.1) % 3.0, 2)
            # 揺れの周期も少しランダムにするための追加クラスやインラインスタイル
            duration = round(2.5 + (col % 3) * 0.4, 2)
            
            # 土は全てのマスに描画
            soil = f'<ellipse cx="{x+20}" cy="{y+35}" rx="14" ry="4" fill="#4e342e" opacity="0.8" />'
            
            plant_element = ""
            if count == 0:
                # 土のみ
                pass
            elif count <= 2:
                # 芽 (Sprout)
                plant_element = f"""
    <g class="sway" style="animation-delay: {delay}s; animation-duration: {duration}s; transform-origin: {origin_x}px {origin_y}px;">
      <!-- 双葉の茎 -->
      <path d="M{x+20},{y+35} Q{x+19},{y+28} {x+19},{y+24}" stroke="#a3e635" stroke-width="2.5" fill="none" stroke-linecap="round" />
      <!-- 左の葉 -->
      <path d="M{x+19},{y+24} Q{x+13},{y+22} {x+15},{y+19} Q{x+20},{y+20} {x+19},{y+24} Z" fill="#84cc16" />
      <!-- 右の葉 -->
      <path d="M{x+19},{y+24} Q{x+25},{y+22} {x+23},{y+19} Q{x+18},{y+20} {x+19},{y+24} Z" fill="#84cc16" />
    </g>"""
            elif count <= 5:
                # 茎・若葉・蕾 (Bud)
                # 蕾の色を少し変化させる
                bud_color = "#f472b6" if count % 2 == 0 else "#fbbf24"
                plant_element = f"""
    <g class="sway" style="animation-delay: {delay}s; animation-duration: {duration}s; transform-origin: {origin_x}px {origin_y}px;">
      <!-- 少し成長した茎 -->
      <path d="M{x+20},{y+35} Q{x+18},{y+26} {x+20},{y+18}" stroke="#4ade80" stroke-width="2.5" fill="none" stroke-linecap="round" />
      <!-- 途中の葉 -->
      <path d="M{x+19},{y+27} Q{x+12},{y+26} {x+14},{y+23} Q{x+18},{y+24} {x+19},{y+27} Z" fill="#22c55e" />
      <path d="M{x+20},{y+23} Q{x+28},{y+22} {x+26},{y+19} Q{x+21},{y+20} {x+20},{y+23} Z" fill="#22c55e" />
      <!-- 蕾 -->
      <circle cx="{x+20}" cy="{y+16}" r="3.5" fill="{bud_color}" />
    </g>"""
            else:
                # 満開の花 (Flower)
                # コミット数に応じて花の色をバリエーション豊かにする
                if count >= 10:
                    flower_color = "#ec4899" # 濃いピンク (Rose)
                    center_color = "#facc15" # 黄色
                elif count >= 8:
                    flower_color = "#3b82f6" # 青 (Bluebell)
                    center_color = "#ffffff" # 白
                else:
                    flower_color = "#f97316" # オレンジ (Marigold)
                    center_color = "#facc15" # 黄色
                    
                plant_element = f"""
    <g class="sway" style="animation-delay: {delay}s; animation-duration: {duration}s; transform-origin: {origin_x}px {origin_y}px;">
      <!-- 太い茎 -->
      <path d="M{x+20},{y+35} Q{x+21},{y+24} {x+20},{y+15}" stroke="#22c55e" stroke-width="3" fill="none" stroke-linecap="round" />
      <!-- 葉っぱ -->
      <path d="M{x+20},{y+25} Q{x+11},{y+24} {x+13},{y+20} Q{x+19},{y+21} {x+20},{y+25} Z" fill="#15803d" />
      <path d="M{x+20},{y+21} Q{x+29},{y+20} {x+27},{y+16} Q{x+21},{y+17} {x+20},{y+21} Z" fill="#15803d" />
      <!-- 花びら -->
      <circle cx="{x+20}" cy="{y+10}" r="4" fill="{flower_color}" />
      <circle cx="{x+20}" cy="{y+20}" r="4" fill="{flower_color}" />
      <circle cx="{x+15}" cy="{y+15}" r="4" fill="{flower_color}" />
      <circle cx="{x+25}" cy="{y+15}" r="4" fill="{flower_color}" />
      <!-- 花の中心 -->
      <circle cx="{x+20}" cy="{y+15}" r="3" fill="{center_color}" />
    </g>"""
                
            svg_body += f"""  <!-- Cell {col},{row} (Commits: {count}) -->
  {soil}{plant_element}
"""

    # 凡例 (Legend)
    legend_y = height - padding
    legend_x_start = width - padding - 180
    
    svg_footer = f"""
  <!-- Legend -->
  <text x="{padding}" y="{legend_y}" class="legend-text">🌱 Left to right: Older to Newer weeks</text>
  
  <g transform="translate({legend_x_start}, {legend_y - 12})">
    <ellipse cx="10" cy="10" rx="6" ry="2" fill="#4e342e" opacity="0.8" />
    <text x="20" y="13" class="legend-text">0</text>
    
    <g transform="translate(40, 0)">
      <ellipse cx="10" cy="10" rx="6" ry="2" fill="#4e342e" opacity="0.8" />
      <path d="M10,10 Q9,5 9,2" stroke="#a3e635" stroke-width="1.5" fill="none" />
      <text x="20" y="13" class="legend-text">1-2</text>
    </g>
    
    <g transform="translate(85, 0)">
      <ellipse cx="10" cy="10" rx="6" ry="2" fill="#4e342e" opacity="0.8" />
      <path d="M10,10 Q9,5 10,1" stroke="#4ade80" stroke-width="1.5" fill="none" />
      <circle cx="10" cy="0" r="1.5" fill="#f472b6" />
      <text x="20" y="13" class="legend-text">3-5</text>
    </g>
    
    <g transform="translate(130, 0)">
      <ellipse cx="10" cy="10" rx="6" ry="2" fill="#4e342e" opacity="0.8" />
      <path d="M10,10 Q10,5 10,1" stroke="#22c55e" stroke-width="2" fill="none" />
      <circle cx="10" cy="0" r="2.5" fill="#ec4899" />
      <circle cx="10" cy="0" r="1.0" fill="#facc15" />
      <text x="20" y="13" class="legend-text">6+</text>
    </g>
  </g>
</svg>
"""

    return svg_header + svg_body + svg_footer

def main():
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    # フォールバック用に、現在のディレクトリのリポジトリ名やgit configから推測することも可能
    if not username:
        username = "YoRuHub" # デフォルト
        
    token = os.environ.get("GITHUB_TOKEN")
    
    calendar_data = None
    if token:
        print(f"Fetching contribution data for {username}...", file=sys.stderr)
        calendar_data = get_contributions(username, token)
        
    if not calendar_data:
        calendar_data = generate_mock_data()
        
    svg_content = build_svg(calendar_data)
    
    # 出力先ディレクトリの準備
    output_dir = "dist"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "garden-contribution-graph.svg")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"Successfully generated garden SVG at {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
