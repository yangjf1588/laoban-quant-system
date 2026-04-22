# GitHub 协作规范

**版本**: V1.0
**时间**: 2026-04-22
**作者**: 大龙

---

## 仓库信息

- **仓库名**: `laoban-quant-system`
- **本地路径**: `~/Desktop/X/laoban-quant-system`
- **状态**: 本地已初始化，等待远程配置

---

## 分支策略

| 分支 | 用途 | 谁用 |
|------|------|------|
| `main` | 主分支，稳定代码 | 大龙维护 |
| `feature/xxx` | 功能开发分支 | 小爱/小猪 |
| `hotfix/xxx` | 紧急修复 | 大龙 |

---

## 工作流程

### 1. 获取最新代码
```bash
git checkout main
git pull origin main
```

### 2. 创建功能分支
```bash
git checkout -b feature/选股系统
```

### 3. 提交代码
```bash
git add .
git commit -m "feat: 添加选股逻辑"
```

### 4. 推送到远程
```bash
git push origin feature/选股系统
```

### 5. 创建PR（Pull Request）
- 在GitHub网页创建PR
- 描述改动内容
- 等待大龙审核合并

---

## 提交规范

### Commit Message 格式
```
<type>: <subject>

<body>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档
- `style`: 格式调整
- `refactor`: 重构
- `test`: 测试
- `chore`: 杂项

### 示例
```
feat: 添加AKShare数据采集脚本

- 新增stock_list采集
- 新增日K线采集
- 支持SQLite存储
```

---

## 冲突处理

1. 先拉取main最新代码
2. 合并到功能分支
3. 解决冲突
4. 重新提交

```bash
git fetch origin
git rebase origin/main
```

---

## 待配置（等老板提供Token）

1. 创建GitHub仓库
2. 配置远程地址
3. 添加协作者权限

---

## 权限配置

| 角色 | 权限 |
|------|------|
| 老板 | Owner |
| 大龙 | Admin |
| 小爱 | Write |
| 小猪 | Write |
