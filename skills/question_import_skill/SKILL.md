# 题目批量导入 Skill — question_import_skill

## 功能概述
将 CSV 格式的题库文件批量导入到 SQLite 数据库，自动校验格式、去重、建立知识点关联。

## 适用场景
- 学生从外部题库批量导入题目
- 初始化或扩充 Agent 的题库

## 不适用场景
- 手动逐题输入

## 输入参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| csv_path | string | 是 | CSV 文件路径 |
| subject_id | integer | 是 | 目标学科 ID |
| dry_run | boolean | 否 | 仅校验不写入(默认false) |
