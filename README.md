# 商标续展代理进度服务

商标续展代理业务管理系统 API 服务，提供商标管理、续展业务、进度跟踪、提醒通知等核心功能。

## 原始需求

> 请开发商标续展代理进度服务，使用 FastAPI 和 PostgreSQL 管理客户、商标号、国际类别、有效期、宽展期、代理委托、官费、材料版本、提交记录、受理回执、补正、驳回和证书归档。客户上传营业执照、委托书和商标清单，代理人核对续展期限、类别、主体变更和费用，财务确认官费与服务费，系统跟踪官方状态和补正要求。服务要处理临期提醒、批量续展、材料覆盖、重复提交、费用未付、官方回传延迟和客户主体不一致，代理人需要看到每个商标卡在哪个环节。

## 技术栈

- **后端框架**: FastAPI 0.115.0
- **数据库**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0.35
- **数据验证**: Pydantic 2.9.2
- **认证**: JWT (python-jose)
- **密码加密**: passlib[bcrypt]
- **任务调度**: APScheduler 3.10.4
- **Python 版本**: 3.11+

## 项目结构

```
wl-370/
├── app/
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   ├── database.py    # 数据库连接
│   │   └── security.py    # 安全认证
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic 模式
│   ├── services/          # 业务逻辑
│   │   ├── reminder_service.py    # 提醒管理服务
│   │   ├── business_service.py    # 核心业务逻辑服务
│   │   └── progress_service.py    # 进度看板服务
│   ├── routers/           # API 路由
│   │   ├── reminders.py   # 提醒 API 路由
│   │   ├── business.py    # 核心业务 API 路由
│   │   └── progress.py    # 进度看板 API 路由
│   └── utils/             # 工具函数
├── main.py                # 应用入口
├── requirements.txt       # Python 依赖
├── pyproject.toml         # Poetry 配置
├── .env.example           # 环境变量示例
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
└── .dockerignore          # Docker 忽略文件
```

## 核心功能模块

### 1. 提醒管理服务 (reminder_service.py)

- **CRUD 操作**: list、get、create、update、delete 提醒
- **批量生成临期提醒**: `generate_expiry_reminders()` - 检查有效期180天内的商标生成提醒
- **批量生成补正提醒**: `generate_correction_reminders()` - 检查即将到期的补正生成提醒
- **发送提醒**: `send_reminder()` - 标记提醒为已发送
- **确认提醒**: `acknowledge_reminder()` - 确认收到提醒

### 2. 核心业务逻辑服务 (business_service.py)

- **临期提醒检测**: `check_expiring_trademarks()` - 检查有效期180天内的商标
- **材料覆盖检测**: `check_materials_coverage()` - 检测材料是否已覆盖所有商标
- **重复提交检测**: `check_duplicate_submissions()` - 检测是否存在重复提交
- **费用未付检测**: `check_unpaid_fees()` - 检测费用是否未付
- **主体不一致检测**: `check_subject_changes()` - 检测客户主体是否变更
- **商标提交验证**: `validate_trademark_for_submission()` - 综合验证商标是否可提交
- **批量续展**: `batch_renew_trademarks()` - 支持批量选择商标进行续展提交
- **提交前检查**: 综合检查材料、费用、重复提交、主体变更

### 3. 进度看板服务 (progress_service.py)

- **8个业务环节追踪**:
  1. 材料准备
  2. 代理人审核
  3. 费用确认
  4. 提交申请
  5. 官方受理
  6. 补正处理
  7. 审核通过
  8. 证书归档

- **环节状态**: 未开始、进行中、已完成、阻塞
- **阻塞原因检测**: 自动识别各环节阻塞原因
- **停留时间计算**: 计算每个环节的停留天数
- **多维度过滤**: 支持按代理人、客户、状态、是否阻塞过滤
- **统计分析**: `get_progress_statistics()` - 进度统计、各环节平均耗时、阻塞商标排行

## API 接口列表

所有 API 路径均以 `/api` 开头。

### 提醒管理 API (`/api/reminders`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reminders` | 获取提醒列表（支持分页、过滤） |
| GET | `/api/reminders/{id}` | 获取提醒详情 |
| POST | `/api/reminders` | 创建提醒 |
| PUT | `/api/reminders/{id}` | 更新提醒 |
| DELETE | `/api/reminders/{id}` | 删除提醒 |
| POST | `/api/reminders/generate-expiry` | 批量生成临期提醒 |
| POST | `/api/reminders/generate-correction` | 批量生成补正提醒 |
| POST | `/api/reminders/{id}/send` | 发送提醒 |
| POST | `/api/reminders/{id}/acknowledge` | 确认提醒 |

### 核心业务 API (`/api/business`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/business/expiring-trademarks` | 获取临期商标列表 |
| POST | `/api/business/check-materials-coverage` | 材料覆盖检测 |
| POST | `/api/business/check-duplicate-submissions` | 重复提交检测 |
| POST | `/api/business/check-unpaid-fees` | 费用未付检测 |
| POST | `/api/business/check-subject-changes` | 主体变更检测 |
| GET | `/api/business/validate/{trademark_id}` | 单商标提交验证 |
| POST | `/api/business/batch-validate` | 批量商标验证 |
| POST | `/api/business/batch-renew` | 批量续展提交 |
| POST | `/api/business/pre-submission-check` | 提交前综合检查 |

### 进度看板 API (`/api/progress`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/progress/board` | 获取进度看板列表 |
| GET | `/api/progress/trademark/{id}` | 获取单商标详细进度 |
| GET | `/api/progress/statistics` | 获取进度统计数据 |
| GET | `/api/progress/stages` | 获取环节和状态选项 |
| GET | `/api/progress/blocked` | 获取阻塞商标列表 |
| GET | `/api/progress/by-agent/{agent_id}` | 按代理人筛选进度 |
| GET | `/api/progress/by-customer/{customer_id}` | 按客户筛选进度 |

## 启动方式

### 前置要求

- Python 3.11+
- PostgreSQL 15+
- pip 或 poetry

### 启动步骤

#### 方式一：直接运行（推荐开发环境）

##### 1. 安装依赖

使用 pip：
```bash
pip install -r requirements.txt
```

或使用 poetry：
```bash
poetry install
```

##### 2. 配置环境变量

复制环境变量示例文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接等参数：
```env
# 数据库配置
# PostgreSQL 配置（Docker 部署时使用）
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=trademark_renewal

# 数据库 URL 覆盖（可选），或启用 SQLite 作为本地开发数据库
# DATABASE_URL=sqlite:///./trademark_renewal.db
USE_SQLITE=True

# 应用配置
APP_HOST=127.0.0.1
APP_PORT=8000
APP_ENV=development

# JWT 配置
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

> **说明**：设置 `USE_SQLITE=True` 后，系统自动使用本地 SQLite 数据库，无需安装 PostgreSQL。如果 PostgreSQL 不可用，系统也会自动降级到 SQLite。

##### 3. 初始化数据库（创建表和示例数据）

```bash
python init_db.py
```

将创建 3 个默认用户：
- `admin` / `admin123`（管理员）
- `agent` / `agent123`（代理人）
- `finance` / `finance123`（财务）

以及 1 个示例客户和 2 个示例商标。

##### 4. 启动服务

```bash
python main.py
```

或使用 uvicorn：
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

访问地址：http://127.0.0.1:8000

API 文档地址：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 方式二：Docker 一键启动（推荐生产环境）

##### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

##### 1. 配置环境变量

```bash
cp .env.example .env
```

##### 2. 一键启动

```bash
docker compose up --build
```

后台运行：
```bash
docker compose up --build -d
```

##### 3. 停止服务

```bash
docker compose down
```

查看日志：
```bash
docker compose logs -f
```

访问地址：
- 应用服务: http://localhost:8000
- API 文档: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## API 调用示例

### 1. 批量生成临期提醒

```bash
curl -X POST "http://localhost:8000/api/reminders/generate-expiry?days_threshold=180&only_pending=true"
```

### 2. 检测材料覆盖

```bash
curl -X POST "http://localhost:8000/api/business/check-materials-coverage" \
  -H "Content-Type: application/json" \
  -d "[1, 2, 3]"
```

### 3. 批量续展提交

```bash
curl -X POST "http://localhost:8000/api/business/batch-renew" \
  -H "Content-Type: application/json" \
  -d '{
    "trademark_ids": [1, 2, 3],
    "submission_channel": "online",
    "skip_validation": false
  }'
```

### 4. 获取进度看板

```bash
curl "http://localhost:8000/api/progress/board?page=1&page_size=20&is_blocked=true"
```

### 5. 获取进度统计

```bash
curl "http://localhost:8000/api/progress/statistics"
```

## 数据库表说明

核心数据表：
- `trademarks` - 商标信息表
- `customers` - 客户信息表
- `users` - 用户表（代理人、管理员）
- `reminders` - 提醒表
- `fees` - 费用表
- `material_versions` - 材料版本表
- `submission_records` - 提交记录表
- `acceptance_receipts` - 受理通知书表
- `corrections` - 补正记录表
- `certificate_archives` - 证书归档表
- `agency_entrustments` - 代理委托书表

## 注意事项

1. **临期提醒**: 默认检测有效期180天内的商标，可通过 `days_threshold` 参数调整
2. **批量续展**: 提交前会自动验证材料、费用、重复提交、主体变更，可设置 `skip_validation=true` 跳过
3. **进度看板**: 环节状态根据相关记录自动判断，阻塞原因自动识别
4. **重复提交检测**: 默认检测30天窗口内的重复提交，可通过 `days_window` 参数调整
5. **环境变量**: 生产环境请务必修改 `JWT_SECRET_KEY` 和数据库密码
6. **文件上传**: 上传目录默认为 `./uploads`，请确保目录存在并有写入权限

## 健康检查

```bash
curl http://localhost:8000/health
```

响应示例：
```json
{
  "status": "healthy",
  "message": "商标续展服务运行正常"
}
```
