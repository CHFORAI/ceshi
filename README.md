# 智能数据分析应用

一个基于 FastAPI + React + Qwen LLM 的智能数据分析应用，支持自然语言查询数据库、生成 SQL、可视化数据和创建仪表盘。

## 项目结构

```
.
├── backend/            # 后端服务 (FastAPI + LangChain + SQLite + Qwen)
│   ├── app/            # 应用代码
│   ├── README.md       # 后端说明文档
│   └── requirements.txt # 后端依赖
├── frontend/           # 前端应用 (React + TypeScript)
│   ├── src/            # 前端源码
│   ├── README.md       # 前端说明文档
│   └── package.json    # 前端依赖
├── scripts/            # 脚本文件
│   ├── init_demo_db.py # 初始化演示数据库
│   └── test_stream.py  # 测试流功能
└── data.db             # SQLite 数据库文件
```

## 技术栈

### 后端

- **FastAPI**: 高性能的 Python Web 框架
- **LangChain**: LLM 应用开发框架
- **SQLite**: 轻量级嵌入式数据库
- **Qwen**: 阿里云通义千问大语言模型

### 前端

- **React**: 现代前端 UI 库
- **TypeScript**: 类型安全的 JavaScript 超集
- **Vite**: 快速的前端构建工具

## 功能特性

- 📊 **自然语言数据分析**: 使用 Qwen LLM 将自然语言转换为 SQL 查询
- 💬 **实时聊天界面**: 支持流式响应，提供流畅的用户体验
- 📁 **会话管理**: 创建、重命名和删除会话，保存聊天历史
- 📈 **数据可视化**: 自动生成图表和仪表盘
- 🔍 **智能 SQL 生成**: 基于数据库 schema 智能生成 SQL 查询
- 🛠 **错误处理**: 完善的错误处理和用户反馈

## 快速开始

### 1. 准备环境

#### 后端环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 前端环境

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 2. 配置环境变量

在后端目录创建 `.env` 文件，添加以下配置：

```env
# 通义千问 API 密钥
DASHSCOPE_API_KEY=your_api_key

# SQLite 数据库路径
SQLITE_PATH=c:\path\to\data.db

# 模型配置
DASHSCOPE_MODEL=qwen3-72b-instruct

# 应用配置
MAX_ROWS=1000
SQL_TIMEOUT_S=30
```

### 3. 初始化数据库

```bash
# 运行初始化脚本
python scripts/init_demo_db.py
```

### 4. 启动服务

#### 启动后端服务

```bash
# 进入后端目录
cd backend

# 启动 FastAPI 服务
uvicorn app.main:app --reload --port 8000
```

#### 启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动开发服务器
npm run dev
```

### 5. 访问应用

- 前端应用: `http://localhost:5173`
- 后端 API 文档: `http://localhost:8000/docs`

## API 端点

### 健康检查

- `GET /api/health` - 检查服务健康状态

### 会话管理

- `GET /api/sessions` - 获取所有会话
- `POST /api/sessions` - 创建新会话
- `PATCH /api/sessions/{id}` - 重命名会话
- `DELETE /api/sessions/{id}` - 删除会话

### 聊天功能

- `POST /api/chat/{sessionId}/stream` - 流式聊天接口 (SSE)

## 使用示例

1. **创建会话**: 点击 "New Session" 按钮创建新的会话
2. **输入查询**: 在聊天输入框中输入自然语言查询，例如：
   - "显示所有用户的年龄分布"
   - "计算每个部门的平均工资"
   - "找出销售额最高的前10个产品"
3. **查看结果**: 系统会自动生成 SQL 查询，执行查询并展示结果，同时可能生成可视化图表

## 项目架构

### 后端架构

- **app/main.py**: FastAPI 应用入口，定义 API 端点
- **app/agent.py**: LLM 代理逻辑，处理自然语言到 SQL 的转换
- **app/llm\_qwen.py**: Qwen 模型客户端，处理与通义千问的交互
- **app/schema\_introspect.py**: 数据库 schema 分析，为 LLM 提供 schema 信息
- **app/session\_store.py**: 会话管理，处理会话的创建、更新和删除
- **app/db.py**: 数据库连接和初始化
- **app/config.py**: 应用配置管理

### 前端架构

- **src/ui/App.tsx**: 应用主组件
- **src/ui/Dashboard.tsx**: 仪表盘组件
- **src/state/store.ts**: 状态管理
- **src/protocol.ts**: 前后端通信协议

## 贡献指南

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情见 [LICENSE](LICENSE) 文件

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能的 Python Web 框架
- [React](https://react.dev/) - 现代前端 UI 库
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架
- [Qwen](https://help.aliyun.com/document_detail/25000004.html) - 阿里云通义千问大语言模型

## 联系方式

如果您有任何问题或建议，请通过以下方式联系我们：

- 提交 [Issue](https://github.com/yourusername/your-repo/issues)
- 发送邮件到:2749207584\@qq.com

***

**享受智能数据分析的乐趣！** 🚀
