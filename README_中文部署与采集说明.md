# PH Infra Watch · Project Atlas V7.1

**仅用于公开项目索引和跟进研究**，不是实时工程招标或投资尽调数据库。

本版本在 V7 地图上新增：① 项目时间筛选；② GitHub Actions 每日两次采集公开 RSS 线索、同一工作流部署 Pages；③ 项目关联企业名录、企业介绍与来源。

## 1. 项目和企业数据结构

```text
v7_1.html                          新网页（不会覆盖现有首页）
data/projects.json                 已核对项目库，266 条记录
/data/companies.json                项目对应的企业/主体名录，227 个名称，其中 7 个有官方来源简介
/data/leads.json                    自动采集的待核验线索（初始为空）
/data/collection_status.json        最近采集的成功/失败情况（初始未运行）
config/sources.json                 12 组 RSS 检索源配置
scripts/collect_public_feeds.py     RSS/Atom 抓取、去重、记录来源与发布时间
scripts/build_companies.py          从已确认项目建立企业角色目录
.github/workflows/collect-public-leads.yml  定时采集及 Pages 发布工作流
```

**项目库与采集线索严格分开**。新闻和 RSS 线索缺少经确认的项目工地、规模或企业角色时，只能出现在右侧“公开线索”，不会自动变成项目地图点位。

## 2. 最简单的上传方式（推荐 GitHub Desktop）

1. 下载 GitHub Desktop（https://desktop.github.com/），登录 GitHub。
2. `File → Clone repository`，选择 `xinleiyang007/ph-infra-watch`，将仓库克隆到电脑。
3. 解压此 ZIP，将 **`v7_1.html`、`data`、`config`、`scripts`、`.github`** 复制进克隆的项目根目录。
4. 注意：若仓库原有 `data/projects.json` 有自行追加的真实项目，**请先备份并合并**，不要盲目覆盖。
5. GitHub Desktop 左下方输入说明 `Add V7.1 time filter, company directory and public-feed collector`，点击 `Commit to main`，再点击 `Push origin`。
6. 在 GitHub 网页中进入仓库 `Settings → Pages → Build and deployment → Source`，选 **GitHub Actions**。本包工作流负责同次采集和部署，不再依赖 `Deploy from a branch`。
7. 进入仓库 `Actions → Collect PH project leads and publish Atlas → Run workflow → main → Run workflow`，等待两项工作（采集和部署）结束，并确认绿色对勾。
8. 浏览器打开 https://xinleiyang007.github.io/ph-infra-watch/v7_1.html 。该地址只有在你完成上传、工作流部署后才有效。

**不要删除或覆盖原来的 `index.html`。** V7.1 使用独立的 `v7_1.html` 测试地址；现有首页会原样随工作流发布。测试后如需换首页，才能另行复制 `v7_1.html` 为 `index.html`。

如果只使用 GitHub 网页上传，需要逐一创建包含路径的文件：
- `v7_1.html`
- `data/companies.json`、`data/leads.json`、`data/collection_status.json`、必要时 `data/projects.json`
- `config/sources.json`
- `scripts/collect_public_feeds.py`、`scripts/build_companies.py`
- `.github/workflows/collect-public-leads.yml`

`Add file → Create new file` 的文件名输入完整路径（如 `.github/workflows/collect-public-leads.yml`）即可由 GitHub 创建对应子目录。上传 ZIP 本身不会自动解压成为网站文件。

## 3. 时间筛选怎么理解

- 左侧“时间字段”默认选择 **资料日期**，数据由 `source_date` 提供。DOE 的 `2026-09-30` 是项目清单快照日，不能说明项目在 9 月开工。
- 若选择 **项目实际里程碑日期**，仅使用项目 `project_date` 或 `milestone_date` 字段。当前 266 条数据中大多没有独立核实的项目里程碑日期，故选择近 90 天时可能显示 0 条，这是正确的空值处理。
- 支持最近 7/30/90/365 天、自定义起止日期、仅未知日期以及显示未知日期记录。
- 自动采集线索按 RSS 的新闻 **发布时间** 筛选，不等于工程开工日期。

如你之后确认某个项目的开工日期，可在项目记录增加 `"project_date":"2026-11-15"`，并在 `source_url` 或资料说明里提供支持该日期的证据；不要随意推断。

## 4. 自动采集做什么 / 不做什么

工作流在菲律宾时间大致 **10:17、22:17** 运行（UTC 02:17、14:17），也可在 GitHub `Actions` 手动运行。GitHub 可能延迟或跳过定时任务，因此不是硬实时。无需额外付费的 AI API 或数据库，使用 Python 标准库即可运行。

配置中有 12 组检索源：DOE、PPP Center、BCDA、DICT、PhilGEPS 等公开网页的 **Google News 站点限制 RSS 索引**，以及菲律宾风电、光伏、储能、充电桩、数据中心、弱电/光纤的主题 RSS 搜索。它们是可访问的公开信息发现入口，**并不表示能直接扫描世界上所有公开网站，或保证收全机构公告**。Google News 搜索可能延迟、遗漏或停止提供链接；Google News 链接有时为中转链接。

自动收集：标题、发布时间、发现时间、来源/检索主题、可访问链接与简短摘录；按标题及发布源做近似去重；保留过往人工复核状态；记录每个来源成功/失败情况。

不会自动收集或推断：施工现场精确坐标、投资方股权、EPC 合同、分包商、未公开的联系方式、付费/登录页面内容。新增线索需要人工核实以后才能写入 `data/projects.json`。

失败处理：若全部信息源均不可访问，不会删除之前已收集的线索；工作流会以旧数据完成部署并记录提醒。

## 5. 企业名录

`data/companies.json` 由现有项目的 `owner`、`investors`、`contractors`、`subcontractors` 字段建立。对相同名称归集关联项目和角色。**原始项目只注明 DOE 合同登记公司时，不会自动认定为股东或 EPC。**

- 227 个企业/项目主体 **名称**，不等于 227 家去重法律实体（别名、项目公司和联合体可能重叠）。
- 7 个名称附有官方企业来源的中文概要；其余显示“在当前项目库中作为某角色出现”的项目关联说明，明确标为非官方介绍。
- 未来确认更多企业的官网及简介后，在 `data/companies.json` 的对应企业添加 `description`、`description_source_url`、`website`、`description_status`。`build_companies.py` 在后续更新时会保留这些手工补充字段。

## 6. 重要的 GitHub Pages 设置

GitHub 官方明确：**工作流使用 `GITHUB_TOKEN` 提交代码不会触发另一轮 GitHub Pages branch build**。因此本包工作流在同次任务内用 `actions/upload-pages-artifact` 与 `actions/deploy-pages` 部署静态网页。务必在 `Settings → Pages` 将 Source 改为 **GitHub Actions**。如果你保留 `Deploy from a branch`，数据可能更新了但网页不会同步发布。

确保仓库的 Actions 获准运行、`github-pages` 环境未设置阻止自动部署的审批门槛。GitHub Actions 免费用量受 GitHub 计划及仓库类型限制；GitHub Pages 免费政策也随仓库可见性和套餐变化。

## 7. 如何检查是否真正采集成功

- GitHub `Actions` 工作流运行详情应能看到每一来源的 `ok / error`。
- 打开 `https://xinleiyang007.github.io/ph-infra-watch/data/collection_status.json` 查看 `success_sources`。
- 打开 `https://xinleiyang007.github.io/ph-infra-watch/data/leads.json` 查看 `leads[]`。
- 页面右侧“公开线索”应出现待核验记录，项目数量 **仍应是原有的 266**，直到你另行审核并更新项目库。

**手工本地测试：** `python -m unittest discover -s tests -v`。若要自行运行采集，使用 `python scripts/collect_public_feeds.py`，要求执行电脑能联网。本站提供的采集脚本已通过离线 RSS 测试，外部实际访问需部署到 GitHub Actions 后验证。
