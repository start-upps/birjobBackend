const cron = require('node-cron');
const { prisma } = require('./database');
const { cache } = require('./redis');
const logger = require('./logger');

// Track job execution to prevent overlapping
const jobExecution = new Map();

/**
 * Simple health check job
 * Runs every 5 minutes to check system health
 */
const healthCheck = cron.schedule(
  '*/5 * * * *', // Every 5 minutes
  async () => {
    const jobName = 'healthCheck';
    
    if (jobExecution.has(jobName)) {
      return;
    }
    
    jobExecution.set(jobName, Date.now());
    
    try {
      // Check database connectivity
      await prisma.$queryRaw`SELECT 1`;
      
      // Log memory usage periodically
      const memUsage = process.memoryUsage();
      logger.debug('System Health Check', {
        memory: {
          rss: `${Math.round(memUsage.rss / 1024 / 1024)} MB`,
          heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)} MB`
        },
        uptime: `${Math.round(process.uptime())} seconds`
      });
      
    } catch (error) {
      logger.error('Health check failed:', error);
    } finally {
      jobExecution.delete(jobName);
    }
  },
  {
    scheduled: false
  }
);

/**
 * Cache cleanup job
 * Runs every hour to clean up expired cache entries
 */
const cleanupCache = cron.schedule(
  '0 * * * *', // Every hour
  async () => {
    const jobName = 'cleanupCache';
    
    if (jobExecution.has(jobName)) {
      return;
    }
    
    jobExecution.set(jobName, Date.now());
    
    try {
      // This is handled automatically by Redis TTL, but we can do manual cleanup if needed
      logger.debug('Cache cleanup check completed');
    } catch (error) {
      logger.error('Error in cache cleanup:', error);
    } finally {
      jobExecution.delete(jobName);
    }
  },
  {
    scheduled: false
  }
);

/**
 * Database cleanup job
 * Runs every Sunday at 2 AM to clean up old logs
 */
const cleanupDatabase = cron.schedule(
  '0 2 * * 0', // Sunday at 2 AM
  async () => {
    const jobName = 'cleanupDatabase';
    
    if (jobExecution.has(jobName)) {
      logger.warn(`${jobName} is already running, skipping...`);
      return;
    }
    
    jobExecution.set(jobName, Date.now());
    logger.info(`Starting ${jobName}...`);
    
    try {
      const retentionDays = parseInt(process.env.LOG_RETENTION_DAYS) || 90;
      const cutoffDate = new Date(Date.now() - retentionDays * 24 * 60 * 60 * 1000);
      
      // Clean up old search logs
      const searchLogsDeleted = await prisma.search_logs.deleteMany({
        where: {
          timestamp: {
            lt: cutoffDate
          }
        }
      });
      
      // Clean up old visitor logs
      const visitorLogsDeleted = await prisma.visitor_logs.deleteMany({
        where: {
          timestamp: {
            lt: cutoffDate
          }
        }
      });
      
      logger.info(`Database cleanup completed:`, {
        searchLogsDeleted: searchLogsDeleted.count,
        visitorLogsDeleted: visitorLogsDeleted.count,
        cutoffDate: cutoffDate.toISOString()
      });
      
    } catch (error) {
      logger.error('Error in database cleanup:', error);
    } finally {
      jobExecution.delete(jobName);
    }
  },
  {
    scheduled: false,
    timezone: process.env.TIMEZONE || 'Asia/Baku'
  }
);

/**
 * Initialize cron jobs
 */
const initializeCronJobs = () => {
  logger.info('Initializing cron jobs...');
  
  // Start jobs based on environment
  if (process.env.ENABLE_CRON_JOBS !== 'false') {
    
    // Always enable these jobs
    healthCheck.start();
    cleanupCache.start();
    
    // Enable cleanup jobs in production
    if (process.env.NODE_ENV === 'production') {
      cleanupDatabase.start();
      logger.info('Database cleanup job started');
    }
    
    logger.info('Cron jobs initialized');
  } else {
    logger.info('Cron jobs disabled by configuration');
  }
};

/**
 * Gracefully stop all cron jobs
 */
const stopCronJobs = () => {
  logger.info('Stopping cron jobs...');
  
  healthCheck.stop();
  cleanupCache.stop();
  cleanupDatabase.stop();
  
  logger.info('All cron jobs stopped');
};

/**
 * Get status of all cron jobs
 */
const getCronJobStatus = () => {
  return {
    jobs: [
      {
        name: 'healthCheck',
        status: healthCheck.getStatus(),
        schedule: '*/5 * * * *',
        description: 'System health monitoring'
      },
      {
        name: 'cleanupCache',
        status: cleanupCache.getStatus(),
        schedule: '0 * * * *',
        description: 'Clean up expired cache entries'
      },
      {
        name: 'cleanupDatabase',
        status: cleanupDatabase.getStatus(),
        schedule: '0 2 * * 0',
        description: 'Clean up old logs and data'
      }
    ],
    runningJobs: Array.from(jobExecution.entries()).map(([name, startTime]) => ({
      name,
      startTime: new Date(startTime).toISOString(),
      duration: Date.now() - startTime
    })),
    timezone: process.env.TIMEZONE || 'Asia/Baku',
    enabled: process.env.ENABLE_CRON_JOBS !== 'false'
  };
};

/**
 * Startup tasks (simplified)
 */
const startupTasks = async () => {
  if (process.env.NODE_ENV === 'development') {
    logger.info('Running startup tasks...');
    
    try {
      // Test database connection
      await prisma.$queryRaw`SELECT 1`;
      logger.info('Database connection verified');
      
      logger.info('Startup tasks completed');
      
    } catch (error) {
      logger.error('Startup tasks failed:', error);
    }
  }
};

module.exports = {
  initializeCronJobs,
  stopCronJobs,
  getCronJobStatus,
  startupTasks
};