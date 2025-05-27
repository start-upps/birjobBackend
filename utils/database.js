const { PrismaClient } = require('@prisma/client');
const logger = require('./logger');

// Prisma client configuration
const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development' 
    ? ['query', 'info', 'warn', 'error']
    : ['error'],
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
});

// Connection event handlers
prisma.$on('query', (e) => {
  if (process.env.NODE_ENV === 'development') {
    logger.debug(`Query: ${e.query}`);
    logger.debug(`Params: ${e.params}`);
    logger.debug(`Duration: ${e.duration}ms`);
  }
});

prisma.$on('info', (e) => {
  logger.info(`Prisma Info: ${e.message}`);
});

prisma.$on('warn', (e) => {
  logger.warn(`Prisma Warning: ${e.message}`);
});

prisma.$on('error', (e) => {
  logger.error(`Prisma Error: ${e.message}`);
});

// Test database connection
const testConnection = async () => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    logger.info('✅ Database connection test successful');
    return true;
  } catch (error) {
    logger.error('❌ Database connection test failed:', error);
    throw error;
  }
};

// Database health check
const getHealthStatus = async () => {
  try {
    const start = Date.now();
    await prisma.$queryRaw`SELECT 1`;
    const responseTime = Date.now() - start;
    
    return {
      status: 'healthy',
      responseTime: `${responseTime}ms`,
      connection: 'active'
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error.message,
      connection: 'failed'
    };
  }
};

// Get database statistics
const getDatabaseStats = async () => {
  try {
    const [
      jobCount,
      userCount,
      keywordCount,
      notificationCount,
      searchLogCount
    ] = await Promise.all([
      prisma.jobs_jobpost.count(),
      prisma.users.count(),
      prisma.keywords.count(),
      prisma.notifications.count(),
      prisma.search_logs.count()
    ]);

    return {
      jobs: jobCount,
      users: userCount,
      keywords: keywordCount,
      notifications: notificationCount,
      searchLogs: searchLogCount,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    logger.error('Error fetching database stats:', error);
    throw error;
  }
};

// Get latest job information
const getLatestJobInfo = async () => {
  try {
    const latestJob = await prisma.jobs_jobpost.findFirst({
      orderBy: { created_at: 'desc' },
      select: {
        created_at: true,
        source: true
      }
    });

    const jobSources = await prisma.jobs_jobpost.groupBy({
      by: ['source'],
      _count: {
        source: true
      },
      orderBy: {
        _count: {
          source: 'desc'
        }
      }
    });

    return {
      latestJobDate: latestJob?.created_at || null,
      latestJobSource: latestJob?.source || null,
      totalSources: jobSources.length,
      sourceBreakdown: jobSources.map(s => ({
        source: s.source,
        count: s._count.source
      }))
    };
  } catch (error) {
    logger.error('Error fetching latest job info:', error);
    throw error;
  }
};

// Clean up old logs (utility function for maintenance)
const cleanupOldLogs = async (daysToKeep = 90) => {
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

    const [searchLogsDeleted, visitorLogsDeleted] = await Promise.all([
      prisma.search_logs.deleteMany({
        where: {
          timestamp: {
            lt: cutoffDate
          }
        }
      }),
      prisma.visitor_logs.deleteMany({
        where: {
          timestamp: {
            lt: cutoffDate
          }
        }
      })
    ]);

    logger.info(`Cleanup completed: ${searchLogsDeleted.count} search logs, ${visitorLogsDeleted.count} visitor logs deleted`);
    
    return {
      searchLogsDeleted: searchLogsDeleted.count,
      visitorLogsDeleted: visitorLogsDeleted.count,
      cutoffDate
    };
  } catch (error) {
    logger.error('Error during log cleanup:', error);
    throw error;
  }
};

// Graceful disconnect
const disconnect = async () => {
  try {
    await prisma.$disconnect();
    logger.info('Database disconnected gracefully');
  } catch (error) {
    logger.error('Error disconnecting from database:', error);
    throw error;
  }
};

module.exports = {
  prisma,
  testConnection,
  getHealthStatus,
  getDatabaseStats,
  getLatestJobInfo,
  cleanupOldLogs,
  disconnect
};