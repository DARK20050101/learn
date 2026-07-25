# 拾光刷题系统公网部署前审计报告

审计日期：2026-07-25  
审计方式：只读代码与配置检查；未执行数据库操作、迁移或公网发布。

## 一、审计结论

当前项目具备完整的应用代码、前端生产构建能力、PostgreSQL模型和Alembic迁移，
但尚未达到“直接部署到公网”的状态。

核心业务可以部署，主要阻塞项集中在部署基础设施和全新数据库初始化：

1. 项目没有Dockerfile、Compose、`.dockerignore`、生产反向代理配置。
2. 全新数据库不能可靠地直接执行 `alembic upgrade head`。
3. 生产环境没有强制校验 `SECRET_KEY`、数据库密码和环境模式。
4. 当前本地脚本运行的是Vite开发服务器，不是生产静态文件服务。
5. 尚未配置HTTPS、备份、监控、日志轮转和部署回滚。

结论：**暂不建议直接暴露到公网。完成P0项后，可先部署单用户灰度版本。**

## 二、当前目录与启动方式

### 2.1 后端

后端采用：

- FastAPI
- Async SQLAlchemy
- asyncpg
- Alembic
- Uvicorn

主要结构：

```text
app/
├── api/
├── models/
├── routers/
├── schemas/
├── services/
├── config.py
├── database.py
└── main.py
```

本地开发启动：

```powershell
E:\1a\.venv\Scripts\uvicorn.exe app.main:app --reload
```

局域网脚本使用：

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

生产环境不能使用 `--reload`。建议由systemd、Docker或其他进程管理器托管Uvicorn，
并只让反向代理访问后端端口。

### 2.2 前端

前端采用Vue3、TypeScript、Vite和Tailwind。

本地开发：

```powershell
cd frontend
npm run dev
```

生产构建：

```powershell
cd frontend
npm ci
npm run build
```

构建结果位于 `frontend/dist/`。公网环境应由Nginx或Caddy提供该目录，
不能使用Vite开发服务器承载真实流量。

前端API基址：

```ts
import.meta.env.VITE_API_BASE_URL || "/api/v1"
```

没有写死公网IP。推荐生产环境继续使用同域相对路径 `/api/v1`，
由Nginx将 `/api/` 代理到FastAPI，可避免额外CORS复杂度。

### 2.3 PostgreSQL与Alembic

数据库连接从 `DATABASE_URL` 读取，Alembic的 `env.py` 会用同一配置覆盖
`alembic.ini` 中的默认地址。

常规迁移命令：

```text
alembic upgrade head
```

当前迁移链终点：

```text
20260725_0011
```

题库导入工具包括：

```text
python -m scripts.import_questions ...
python -m scripts.release_questions <candidate.json> --dry-run
python -m scripts.release_questions <candidate.json>
```

## 三、数据库初始化阻塞问题

### 3.1 全新数据库不能直接升级到head

这是当前最高风险。

`20260723_0009_link_questions_kp_v11.py` 要求数据库已经存在固定ID为1–60的题目；
如果不存在会主动失败。

`20260723_0010_backfill_knowledge_status_ids.py` 要求已经存在固定ID为1–18的
`knowledge_status`，并绑定指定用户ID、学科和旧知识点名称；如果不存在同样会失败。

但早期Alembic迁移没有自动创建这些60题、用户和18条学习状态。因此在空数据库执行：

```text
alembic upgrade head
```

会在数据迁移阶段失败。当前本机能成功，是因为数据库已经按历史开发顺序准备过数据。

### 3.2 生产初始化建议

短期上线可选择：

1. 从当前已验证的head数据库制作“脱敏生产基线备份”。
2. 保留表结构、Alembic版本、知识点目录、110道题及题目关联。
3. 排除测试用户、JWT相关信息、答题记录、AI分析、每日任务和训练会话。
4. 在隔离数据库完整演练一次恢复，并验证110题和110条primary关联。

长期正确做法：

- 为全新环境建立独立的Alembic baseline/squashed revision。
- baseline直接创建当前head结构。
- 将知识点目录和110题作为可重复执行的reference-data seed处理。
- 不再让全新安装依赖历史用户ID、题目ID和学习记录。
- 已运行的旧迁移文件不要直接重写，以免破坏现有数据库升级历史。

在该问题解决前，不应把“启动容器时自动执行 `alembic upgrade head`”作为全新生产库
初始化方案。

## 四、Docker支持检查

当前不存在：

| 文件 | 状态 |
|---|---|
| 根目录 `Dockerfile` | 不存在 |
| `frontend/Dockerfile` | 不存在 |
| `docker-compose.yml` / `compose.yml` | 不存在 |
| `.dockerignore` | 不存在 |
| 生产Nginx配置 | 不存在 |

建议新增：

```text
Dockerfile                 # FastAPI生产镜像
frontend/Dockerfile        # Node构建 + Nginx静态服务
compose.yml                # backend/frontend/postgres及持久卷
.dockerignore
frontend/.dockerignore
deploy/nginx.conf
deploy/.env.production.example
deploy/backup-postgres.sh
```

Compose应至少包含：

- `postgres`：持久卷、健康检查，不对公网开放5432。
- `backend`：仅内网访问PostgreSQL，运行FastAPI。
- `frontend`：Nginx提供静态文件，并代理 `/api/`。
- 一次性 `migrate` 或 `bootstrap` 任务，但必须先解决全新数据库迁移链问题。

密钥不得写入镜像、Compose文件或Git仓库。

## 五、生产环境风险

### P0：上线前必须处理

#### 1. 默认SECRET_KEY可以在生产启动

`config.py` 内存在开发默认值：

```text
development-secret-key-change-me-please-123456
```

虽然长度满足校验，但生产环境忘记设置时仍能启动，攻击者可据此伪造JWT。

建议：

- `ENVIRONMENT=production` 时禁止使用默认密钥。
- 使用密码管理器生成至少32字节随机值。
- 密钥仅通过服务器Secret或环境变量注入。
- 轮换密钥会使现有JWT失效，应安排维护窗口。

#### 2. 数据库默认凭据不适合公网

代码和示例使用 `postgres:postgres`。生产必须：

- 使用独立数据库用户。
- 使用高强度随机密码。
- 仅授予应用数据库所需权限。
- PostgreSQL只监听内网或容器网络。
- 云数据库启用TLS。
- 禁止公网暴露5432。

#### 3. 全新数据库初始化链不完整

见第三章。这是部署自动化和灾难恢复的直接阻塞项。

#### 4. 必须启用HTTPS

登录密码和JWT不能通过明文HTTP传输。需要：

- 域名。
- 80跳转443。
- Let's Encrypt证书自动续期。
- TLS 1.2以上。
- HSTS在验证稳定后启用。

#### 5. 生产前端必须使用静态构建

禁止将 `npm run dev` 或5173端口暴露公网。必须执行 `npm run build`，
再由Nginx/Caddy服务 `dist/`。

#### 6. 备份与恢复尚未落地

至少需要：

- 每日自动 `pg_dump`。
- 备份加密并存储到不同磁盘或对象存储。
- 明确保留周期。
- 上线前完成一次恢复演练。
- 题库正式发布前额外创建备份点。

### P1：首轮灰度前建议处理

#### 1. 生产配置缺少强校验

除SECRET_KEY外，还应在生产模式校验：

- `DEBUG=false`
- `DATABASE_URL`不是默认值
- `LLM_ENABLED=true` 时必须提供 `LLM_API_KEY`
- CORS不得使用任意来源

当前 `DEBUG` 默认false是安全的，但没有防止生产环境误设为true。

#### 2. CORS策略

当前仅在 `BACKEND_CORS_ORIGINS` 非空时启用CORS，并允许凭据、全部方法和全部请求头。

推荐采用同域部署：

```text
https://study.example.com/
https://study.example.com/api/v1/
```

这种方式通常不需要CORS。若前后端跨域，只允许确切的HTTPS前端域名，
不要配置 `*`。

#### 3. LLM API Key管理

当前Key仅由后端读取，前端不会接触，架构正确。生产应：

- 通过Secret注入。
- 不写入日志和错误响应。
- 设置供应商消费限额和告警。
- 使用专用项目Key，便于单独撤销。
- 保持 `LLM_ENABLED=false` 作为无Key时的明确模式。

现有AI失败降级不会阻断答题，但后台AI分析使用应用进程内任务；
进程重启时任务可能丢失。单用户MVP可暂时接受，后续再引入持久任务队列。

#### 4. 健康检查过浅

`GET /health` 只返回固定JSON，不验证数据库。可能出现“服务健康但数据库不可用”。

建议增加独立readiness检查数据库连通性，同时保留轻量liveness检查。

#### 5. 认证与滥用保护

当前JWT有效期默认24小时，前端保存在localStorage，且注册/登录没有显式限流。

灰度期至少应：

- Nginx层限制登录、注册和AI接口请求频率。
- 设置请求体大小限制。
- 监控连续401、注册激增和AI费用。
- 确认是否真的需要开放公网注册；单用户测试可关闭公开入口或仅邀请注册。

#### 6. 日志与错误追踪

目前缺少明确的生产日志策略。建议：

- Uvicorn访问日志和应用错误日志输出到stdout。
- 容器或systemd负责日志轮转。
- 日志不记录密码、JWT、LLM Key及完整学生答案。
- 接入轻量错误告警。

### P2：稳定后处理

- 数据库连接池参数按并发量显式配置。
- 增加部署CI/CD和迁移前自动备份。
- Python依赖增加可复现锁定方案；前端已有 `package-lock.json`。
- 增加安全响应头和内容安全策略。
- 评估JWT撤销/刷新机制。
- 将进程内AI后台任务升级为可恢复队列。

## 六、推荐部署架构

推荐单域名、反向代理架构：

```text
手机浏览器
    │ HTTPS 443
    ▼
Nginx / Caddy
    ├── /          → frontend/dist
    └── /api/      → FastAPI:8000
                         │
                         ├── PostgreSQL（私网）
                         └── LLM API（HTTPS出站）
```

公网只开放：

- 80（仅跳转HTTPS）
- 443
- SSH管理端口（仅管理员IP或VPN）

不开放：

- 5173
- 8000
- 5432

## 七、方案A：本机虚拟机部署

### 适用场景

- 极少量受控测试用户。
- 临时验证公网流程。
- 可以接受家中电脑和网络必须持续在线。

### 建议结构

- Ubuntu虚拟机。
- Nginx/Caddy提供HTTPS和前端静态文件。
- FastAPI由systemd运行。
- PostgreSQL运行在虚拟机内或独立内网主机。
- 路由器只转发80/443到虚拟机。

### 前置条件

- 运营商提供可入站公网IPv4或可用IPv6。
- 如果处于CGNAT，普通路由器端口转发无效，需要合规的公网隧道或云入口。
- 配置动态DNS或固定公网IP。
- Windows宿主机、虚拟机和路由器三层防火墙都要最小开放。
- 宿主机不能休眠，断电和宽带故障会直接导致服务不可用。

### 风险

- 家庭公网IP暴露。
- 可用性低。
- 数据备份和磁盘故障风险高。
- 网络上行带宽有限。
- 运维复杂度并不比小型云服务器低。

结论：只适合短期封闭测试，不建议承载长期真实学生数据。

## 八、方案B：云服务器部署

### 推荐方案

- 国内或目标用户网络质量良好的云服务器。
- Ubuntu LTS。
- 起步配置可用2核CPU、2–4GB内存、40GB以上SSD。
- Docker Compose部署应用，或Nginx + systemd原生部署。
- PostgreSQL优先使用云托管数据库；控制成本时可先与应用同机，但必须使用持久卷和异机备份。

### 部署步骤

1. 准备域名、服务器、防火墙和HTTPS证书。
2. 解决数据库baseline问题并完成空环境恢复演练。
3. 创建生产Secret和独立数据库账号。
4. 构建后端镜像与前端静态镜像。
5. 恢复脱敏reference data或运行新的生产bootstrap。
6. 验证Alembic版本、110题和110条primary关联。
7. 启动后端，再启动反向代理。
8. 执行健康检查、登录、每日6题、错题本、专项训练和学习报告冒烟测试。
9. 开启数据库备份、日志轮转、磁盘和服务告警。
10. 只邀请一个真实学生灰度使用，稳定后再扩大。

### 国内公网注意事项

若服务器和域名部署在中国大陆，通常需要完成ICP备案，并遵守云厂商接入要求。
如果使用境外服务器，可免去部分接入流程，但青海西宁用户的延迟和稳定性可能更差。
具体合规要求应在购买服务器和绑定域名前向云厂商确认。

结论：**方案B是推荐方案。**

## 九、需要新增的部署文件

建议按以下顺序实施：

### Phase Deploy 1：生产安全配置

- 增加production配置强校验。
- 设计脱敏baseline/bootstrap。
- 明确生产数据库恢复流程。
- 增加数据库readiness检查。

### Phase Deploy 2：容器化

- 后端Dockerfile。
- 前端多阶段Dockerfile。
- Compose。
- Nginx配置。
- `.dockerignore`。
- 生产环境变量模板。

### Phase Deploy 3：部署演练

- 在全新临时环境完成从零部署。
- 验证迁移、110题、关联、登录和训练闭环。
- 完成备份恢复和版本回滚演练。

### Phase Deploy 4：公网灰度

- 配置域名和HTTPS。
- 限制注册和请求频率。
- 启用日志与告警。
- 单用户灰度3–7天。

## 十、公网上线准入清单

以下项目全部完成后才建议开放：

- [ ] 全新环境数据库初始化可重复执行
- [ ] 生产数据库不包含测试用户和个人学习记录
- [ ] 110题和110条primary关联验证通过
- [ ] SECRET_KEY为随机生产密钥
- [ ] 数据库使用独立强密码账号
- [ ] DEBUG关闭
- [ ] LLM Key仅服务端注入
- [ ] 前端使用生产构建
- [ ] 仅开放80/443
- [ ] HTTPS有效且自动续期
- [ ] PostgreSQL不暴露公网
- [ ] 每日备份和恢复演练完成
- [ ] 登录、注册、AI接口具备基础限流
- [ ] 错误日志和服务告警可用
- [ ] 手机端完整冒烟测试通过

## 十一、最终建议

不要直接把当前Windows局域网启动方式搬到公网。

推荐先处理数据库baseline和生产Secret校验，然后补齐Docker Compose与Nginx。
在全新临时服务器完整演练后，再使用云服务器进行单用户灰度。当前最先要做的实施项是：

**设计并验证“当前head结构 + 110题reference data”的脱敏生产数据库初始化方案。**
