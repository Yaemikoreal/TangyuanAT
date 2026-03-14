"""
监控 API 测试
"""

import pytest
import json


class TestMonitoringHealthAPI:
    """系统健康状态 API 测试"""
    
    def test_get_health_status(self, client):
        """测试获取健康状态"""
        response = client.get('/api/monitoring/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'status' in data['data']
        assert 'score' in data['data']
        assert 'components' in data['data']
    
    def test_health_components(self, client):
        """测试健康组件"""
        response = client.get('/api/monitoring/health')
        data = json.loads(response.data)
        
        components = data['data']['components']
        assert 'database' in components
        assert 'gateway' in components
        
        # 检查数据库组件
        assert 'status' in components['database']
        assert 'type' in components['database']
        
        # 检查网关组件
        assert 'status' in components['gateway']


class TestMonitoringDatabaseAPI:
    """数据库监控 API 测试"""
    
    def test_get_database_status(self, client):
        """测试获取数据库状态"""
        response = client.get('/api/monitoring/database')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_database_status_fields(self, client):
        """测试数据库状态字段"""
        response = client.get('/api/monitoring/database')
        data = json.loads(response.data)
        
        db_data = data['data']
        assert 'status' in db_data
        assert 'type' in db_data
        assert 'size_bytes' in db_data
        assert 'latency_ms' in db_data
        assert 'tables' in db_data
    
    def test_database_tables_count(self, client):
        """测试数据库表统计"""
        response = client.get('/api/monitoring/database')
        data = json.loads(response.data)
        
        tables = data['data']['tables']
        assert 'agents' in tables
        assert 'work_logs' in tables
        assert 'chat_history' in tables


class TestMonitoringGatewayAPI:
    """网关监控 API 测试"""
    
    def test_get_gateway_status(self, client):
        """测试获取网关状态"""
        response = client.get('/api/monitoring/gateway')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_gateway_status_fields(self, client):
        """测试网关状态字段"""
        response = client.get('/api/monitoring/gateway')
        data = json.loads(response.data)
        
        gw_data = data['data']
        assert 'status' in gw_data
        assert 'timestamp' in gw_data


class TestMonitoringResourcesAPI:
    """系统资源监控 API 测试"""
    
    def test_get_system_resources(self, client):
        """测试获取系统资源"""
        response = client.get('/api/monitoring/resources')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_resource_fields(self, client):
        """测试资源字段"""
        response = client.get('/api/monitoring/resources')
        data = json.loads(response.data)
        
        resources = data['data']
        assert 'cpu' in resources
        assert 'memory' in resources
        assert 'disk' in resources
        assert 'process' in resources
        assert 'timestamp' in resources
    
    def test_cpu_metrics(self, client):
        """测试 CPU 指标"""
        response = client.get('/api/monitoring/resources')
        data = json.loads(response.data)
        
        cpu = data['data']['cpu']
        assert 'percent' in cpu
        assert 'count' in cpu
        assert cpu['percent'] >= 0
        assert cpu['percent'] <= 100
    
    def test_memory_metrics(self, client):
        """测试内存指标"""
        response = client.get('/api/monitoring/resources')
        data = json.loads(response.data)
        
        memory = data['data']['memory']
        assert 'total_gb' in memory
        assert 'used_gb' in memory
        assert 'percent' in memory
        assert memory['percent'] >= 0
        assert memory['percent'] <= 100
    
    def test_disk_metrics(self, client):
        """测试磁盘指标"""
        response = client.get('/api/monitoring/resources')
        data = json.loads(response.data)
        
        disk = data['data']['disk']
        assert 'total_gb' in disk
        assert 'used_gb' in disk
        assert 'percent' in disk
        assert disk['percent'] >= 0
        assert disk['percent'] <= 100
    
    def test_process_metrics(self, client):
        """测试进程指标"""
        response = client.get('/api/monitoring/resources')
        data = json.loads(response.data)
        
        process = data['data']['process']
        assert 'memory_mb' in process
        assert process['memory_mb'] >= 0


class TestMonitoringLogsAPI:
    """日志聚合 API 测试"""
    
    def test_get_error_logs(self, client):
        """测试获取错误日志"""
        response = client.get('/api/monitoring/logs/errors')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'count' in data
    
    def test_get_log_aggregation(self, client):
        """测试日志聚合统计"""
        response = client.get('/api/monitoring/logs/aggregate')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_log_aggregation_fields(self, client):
        """测试日志聚合字段"""
        response = client.get('/api/monitoring/logs/aggregate')
        data = json.loads(response.data)
        
        agg = data['data']
        assert 'by_action' in agg
        assert 'by_agent' in agg
        assert 'by_day' in agg


class TestMonitoringHistoryAPI:
    """资源历史 API 测试"""
    
    def test_get_resource_history(self, client):
        """测试获取资源历史"""
        response = client.get('/api/monitoring/resources/history')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
    
    def test_resource_history_limit(self, client):
        """测试资源历史限制"""
        response = client.get('/api/monitoring/resources/history?limit=10')
        data = json.loads(response.data)
        
        # 验证返回的是列表
        assert isinstance(data['data'], list)