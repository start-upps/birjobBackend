const express = require('express');
const { getHealthStatus: getDbHealth, getDatabaseStats, getLatestJobInfo } = require('../utils/database');
const { getHealthStatus: getRedisHealth, getStats: getRedisStats } = require('../utils/redis');
const logger = require('../utils/logger');
const { asyncHandler } = require('../middleware/errorHandler');

const router = express.Router();

// Basic health check - minimal response for load balancers
router.get('/', asyncHandler(async (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
}));

// Detailed health check - comprehensive system status
router.get('/detailed', asyncHandler(async (req, res) => {
  const startTime = Date.now();
  
  try {
    // Get health status from all services
    const [dbHealth, redisHealth] = await Promise.all([
      getDbHealth(),
      getRedisHealth()
    ]);
    
    const responseTime = Date.now() - startTime;
    const uptime = process.uptime();
    
    // Determine overall status
    const isHealthy = dbHealth.status === 'healthy' && redisHealth.status === 'healthy';
    
    const healthData = {
      status: isHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      responseTime: `${responseTime}ms`,
      uptime: {
        seconds: Math.floor(uptime),
        formatted: formatUptime(uptime)
      },
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      services: {
        database: dbHealth,
        redis: redisHealth,
        api: {
          status: 'healthy',
          port: process.env.PORT || 3000,
          cors: process.env.NODE_ENV === 'production' ? 'restricted' : 'permissive'
        }
      },
      system: {
        nodejs: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: {
          used: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)} MB`,
          total: `${Math.round(process.memoryUsage().heapTotal / 1024 / 1024)} MB`,
          rss: `${Math.round(process.memoryUsage().rss / 1024 / 1024)} MB`
        },
        cpu: {
          loadAverage: os.loadavg?.() || 'N/A',
          usage: process.cpuUsage()
        }
      }
    };
    
    // Add warnings if any service is degraded
    if (!isHealthy) {
      healthData.warnings = [];
      if (dbHealth.status !== 'healthy') {
        healthData.warnings.push('Database connection issues detected');
      }
      if (redisHealth.status !== 'healthy') {
        healthData.warnings.push('Redis connection issues detected');
      }
    }
    
    const statusCode = isHealthy ? 200 : 503;
    res.status(statusCode).json(healthData);
    
  } catch (error) {
    logger.error('Health check failed:', error);
    
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Health check failed',
      message: error.message
    });
  }
}));

// Database-specific health check
router.get('/database', asyncHandler(async (req, res) => {
  try {
    const [dbHealth, dbStats, latestJobInfo] = await Promise.all([
      getDbHealth(),
      getDatabaseStats(),
      getLatestJobInfo()
    ]);
    
    res.json({
      status: dbHealth.status,
      timestamp: new Date().toISOString(),
      connection: dbHealth,
      statistics: dbStats,
      latestData: latestJobInfo
    });
    
  } catch (error) {
    logger.error('Database health check failed:', error);
    
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Database health check failed',
      message: error.message
    });
  }
}));

// Redis-specific health check
router.get('/redis', asyncHandler(async (req, res) => {
  try {
    const [redisHealth, redisStats] = await Promise.all([
      getRedisHealth(),
      getRedisStats()
    ]);
    
    res.json({
      status: redisHealth.status,
      timestamp: new Date().toISOString(),
      connection: redisHealth,
      statistics: redisStats
    });
    
  } catch (error) {
    logger.error('Redis health check failed:', error);
    
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Redis health check failed',
      message: error.message
    });
  }
}));

// API metrics and statistics
router.get('/metrics', asyncHandler(async (req, res) => {
  try {
    const [dbStats, redisStats, latestJobInfo] = await Promise.all([
      getDatabaseStats(),
      getRedisStats(),
      getLatestJobInfo()
    ]);
    
    const metrics = {
      timestamp: new Date().toISOString(),
      uptime: {
        seconds: Math.floor(process.uptime()),
        formatted: formatUptime(process.uptime())
      },
      system: {
        memory: {
          heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          heapTotal: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
          rss: Math.round(process.memoryUsage().rss / 1024 / 1024),
          external: Math.round(process.memoryUsage().external / 1024 / 1024)
        },
        cpu: process.cpuUsage()
      },
      database: {
        ...dbStats,
        latestJob: latestJobInfo
      },
      cache: {
        status: redisStats.connected ? 'active' : 'inactive',
        dbSize: redisStats.dbSize || 0
      },
      api: {
        version: process.env.npm_package_version || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
        port: process.env.PORT || 3000
      }
    };
    
    res.json({
      success: true,
      data: metrics,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    logger.error('Metrics collection failed:', error);
    
    res.status(500).json({
      success: false,
      error: 'Metrics collection failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}));

// Readiness probe - for Kubernetes/Docker orchestration
router.get('/ready', asyncHandler(async (req, res) => {
  try {
    // Quick checks to ensure the application is ready to serve requests
    const [dbHealth, redisHealth] = await Promise.all([
      getDbHealth(),
      getRedisHealth()
    ]);
    
    const isReady = dbHealth.status === 'healthy' && redisHealth.status === 'healthy';
    
    if (isReady) {
      res.json({
        status: 'ready',
        timestamp: new Date().toISOString(),
        services: {
          database: 'ready',
          redis: 'ready',
          api: 'ready'
        }
      });
    } else {
      res.status(503).json({
        status: 'not_ready',
        timestamp: new Date().toISOString(),
        services: {
          database: dbHealth.status,
          redis: redisHealth.status,
          api: 'ready'
        }
      });
    }
    
  } catch (error) {
    logger.error('Readiness check failed:', error);
    
    res.status(503).json({
      status: 'not_ready',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
}));

// Liveness probe - for Kubernetes/Docker orchestration
router.get('/live', (req, res) => {
  // Simple liveness check - if this endpoint responds, the app is alive
  res.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Performance test endpoint
router.get('/performance', asyncHandler(async (req, res) => {
  const startTime = Date.now();
  const iterations = parseInt(req.query.iterations) || 100;
  
  try {
    // Simulate some work
    const results = [];
    
    for (let i = 0; i < Math.min(iterations, 1000); i++) {
      const iterationStart = Date.now();
      
      // Simulate async work
      await new Promise(resolve => setTimeout(resolve, 1));
      
      results.push({
        iteration: i + 1,
        duration: Date.now() - iterationStart
      });
    }
    
    const totalTime = Date.now() - startTime;
    const avgTime = results.reduce((sum, r) => sum + r.duration, 0) / results.length;
    
    res.json({
      success: true,
      data: {
        totalIterations: results.length,
        totalTime: `${totalTime}ms`,
        averageTime: `${avgTime.toFixed(2)}ms`,
        minTime: `${Math.min(...results.map(r => r.duration))}ms`,
        maxTime: `${Math.max(...results.map(r => r.duration))}ms`,
        throughput: `${(results.length / (totalTime / 1000)).toFixed(2)} ops/sec`
      },
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    logger.error('Performance test failed:', error);
    
    res.status(500).json({
      success: false,
      error: 'Performance test failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}));

// Helper function to format uptime
function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);
  
  return parts.join(' ');
}

// Add OS module for system info
const os = require('os');

module.exports = router;