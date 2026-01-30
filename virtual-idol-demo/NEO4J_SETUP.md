# Neo4j AuraDB 注册指南（2分钟完成）

## 步骤 1: 注册账户

1. 打开浏览器，访问：https://neo4j.com/cloud/aura/
2. 点击 "Start Free" 按钮
3. 填写注册信息：
   - Email: 你的邮箱
   - Password: 设置密码
   - 或者使用 Google/GitHub 账号登录

## 步骤 2: 创建数据库

1. 登录后会看到控制台
2. 点击 "Create Database" 或 "New Instance"
3. 选择配置：
   - **Instance Type**: "Free" (免费版)
   - **Version**: 选择最新的 Neo4j 5.x
   - **Region**: 选择离你最近的区域（如 Singapore 或 Tokyo）
4. 给数据库起个名字，如：`virtual-idol-db`
5. 点击 "Create"

## 步骤 3: 获取连接信息

创建完成后，你会看到连接信息，类似：

```
Connection URL:
bolt://12345678.databases.neo4j.io:7687

Username:
neo4j

Password:
(点击显示后会看到生成的密码，如：abc123xyz456)
```

**⚠️ 重要**: 密码只会显示一次！请务必复制保存。

## 步骤 4: 复制连接信息

把这三项信息复制下来：
1. URI: `bolt://xxx.databases.neo4j.io:7687`
2. Username: `neo4j`
3. Password: `xxx`

---

## 下一步

把这些信息告诉我，我会帮你配置到项目中！
