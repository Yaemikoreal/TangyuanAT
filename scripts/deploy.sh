#!/bin/bash
# TangyuanAT 部署脚本
# 用法: ./deploy.sh [staging|production] [version]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
PROJECT_NAME="tangyuanat"
IMAGE_NAME="ghcr.io/yaemikoreal/${PROJECT_NAME}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   TangyuanAT 部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "环境: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "版本: ${YELLOW}${VERSION}${NC}"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: docker-compose 未安装${NC}"
    exit 1
fi

# 加载环境变量
if [ -f ".env.${ENVIRONMENT}" ]; then
    echo -e "${GREEN}加载环境变量: .env.${ENVIRONMENT}${NC}"
    export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    echo -e "${GREEN}加载环境变量: .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

# 拉取最新镜像
echo ""
echo -e "${BLUE}[1/5] 拉取镜像...${NC}"
if [ "$VERSION" = "latest" ]; then
    docker-compose pull tangyuanat || true
else
    docker pull ${IMAGE_NAME}:${VERSION} || true
fi

# 停止旧容器
echo ""
echo -e "${BLUE}[2/5] 停止旧容器...${NC}"
docker-compose down --remove-orphans

# 启动新容器
echo ""
echo -e "${BLUE}[3/5] 启动新容器...${NC}"
if [ "$VERSION" = "latest" ]; then
    docker-compose up -d
else
    IMAGE_TAG=${VERSION} docker-compose up -d
fi

# 等待健康检查
echo ""
echo -e "${BLUE}[4/5] 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${BLUE}[5/5] 检查服务状态...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 部署成功!${NC}"
    echo ""
    echo -e "服务地址: ${YELLOW}http://localhost:5000${NC}"
    echo ""
    docker-compose ps
else
    echo -e "${RED}❌ 部署失败，请检查日志${NC}"
    docker-compose logs --tail=50
    exit 1
fi

# 显示日志
echo ""
echo -e "${BLUE}查看日志 (Ctrl+C 退出):${NC}"
echo -e "docker-compose logs -f"
echo ""

# 发送通知（如果配置了飞书 webhook）
if [ -n "$FEISHU_DEPLOY_WEBHOOK" ]; then
    curl -X POST "$FEISHU_DEPLOY_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"msg_type\": \"interactive\",
            \"card\": {
                \"header\": {
                    \"title\": {\"tag\": \"plain_text\", \"content\": \"✅ TangyuanAT 部署成功\"},
                    \"template\": \"green\"
                },
                \"elements\": [
                    {
                        \"tag\": \"div\",
                        \"fields\": [
                            {\"is_short\": true, \"text\": {\"tag\": \"lark_md\", \"content\": \"**环境:** ${ENVIRONMENT}\"}},
                            {\"is_short\": true, \"text\": {\"tag\": \"lark_md\", \"content\": \"**版本:** ${VERSION}\"}},
                            {\"is_short\": true, \"text\": {\"tag\": \"lark_md\", \"content\": \"**时间:** $(date '+%Y-%m-%d %H:%M:%S')\"}}
                        ]
                    }
                ]
            }
        }" 2>/dev/null || true
fi