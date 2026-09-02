# 🎰 新加坡彩票风水分析 · Singapore Lottery Fengshui Tracker

实时追踪新加坡 TOTO 和 4D 开奖号码，结合风水五行理论进行分析预测。

**Live demo** → deploy to GitHub Pages (see setup below)

---

## ✨ 功能 Features

| 功能 | 说明 |
|------|------|
| 🎱 TOTO 开奖 | 显示最新10期开奖号码 |
| 🀄 4D 开奖 | 显示最新6期含头/二/三奖及安慰奖 |
| 📊 频率分析 | 1-49全号码出现频率，热号冷号排行 |
| ☯ 风水预测 | 结合五行干支理论，生成下期推荐号码 |
| 🔄 自动更新 | GitHub Actions 在摇奖日自动抓取更新 |

---

## 🚀 快速部署 Quick Setup

### 第一步：Fork / Clone

```bash
git clone https://github.com/YOUR_USERNAME/sg-lottery.git
cd sg-lottery
```

### 第二步：启用 GitHub Pages

1. 进入 GitHub repo → **Settings** → **Pages**
2. Source 选 **Deploy from a branch**
3. Branch 选 `main`，folder 选 `/ (root)`
4. Save → 几分钟后网站上线

### 第三步：启用 GitHub Actions (自动更新)

Actions 默认已启用。工作流在以下时间自动运行：

- **TOTO 摇奖日**：每周一、四晚 22:30 UTC (新加坡时间次日 06:30)
- **4D 摇奖日**：每周三、六、日晚 22:30 UTC
- **每日保底**：每天 10:00 UTC

查看 `.github/workflows/update-results.yml` 可修改时间。

### 第四步：手动更新数据

```bash
pip install requests beautifulsoup4 lxml
python scraper.py
git add data/results.json
git commit -m "Update results"
git push
```

---

## 🗂️ 文件结构 File Structure

```
sg-lottery/
├── index.html              # 主网站 (单文件，无需构建)
├── scraper.py              # 数据爬取脚本
├── data/
│   └── results.json        # 开奖数据 (自动更新)
├── .github/
│   └── workflows/
│       └── update-results.yml   # 自动更新工作流
└── README.md
```

---

## ☯ 风水算法说明 Fengshui Algorithm

预测号码基于以下模型综合计算：

**五行对应（Wood/Fire/Earth/Metal/Water）**
```
木 (1,2,11,12,21,22,31,32,41,42)
火 (3,4,13,14,23,24,33,34,43,44)
土 (5,6,15,16,25,26,35,36,45,46)
金 (7,8,17,18,27,28,37,38,47,48)
水 (9,10,19,20,29,30,39,40,49)
```

**预测逻辑**
1. 根据当前月份确定主导五行（干支月柱）
2. 计算历史数据中各元素号码出现频率
3. 优先推荐「主气」与「受生元素」中的高频号码
4. 加入黄金比例谐波修正（0.618调整因子）
5. 综合置信度 = 热号与主气重合度

> ⚠️ 彩票属于随机事件，任何预测均为娱乐性质，不构成投注建议。

---

## 📝 数据说明

- 数据来源：Singapore Pools 官方网站
- 爬虫使用 `requests` + `BeautifulSoup4`
- 若爬取失败（网站结构变化），自动使用演示数据
- `data/results.json` 格式：

```json
{
  "last_updated": "2025-01-15 22:35:00 UTC",
  "toto": [
    {
      "draw": "3920",
      "date": "2025-01-13",
      "numbers": [5, 12, 23, 31, 38, 45],
      "additional": 7
    }
  ],
  "four_d": [
    {
      "draw": "3001",
      "date": "2025-01-12",
      "first": ["1234"],
      "second": ["5678"],
      "third": ["9012"],
      "starter": ["..."],
      "consolation": ["..."]
    }
  ]
}
```

---

## 🛠️ 技术栈

- **前端**：纯 HTML/CSS/JavaScript（零依赖，无需构建）
- **字体**：Noto Serif SC + Noto Sans SC (Google Fonts)
- **数据更新**：Python + GitHub Actions
- **托管**：GitHub Pages (免费)

---

*⚠️ 免责声明：本项目纯属娱乐，风水预测不构成任何投资或投注建议。请理性购彩。*
