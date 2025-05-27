const cron = require('node-cron');
const { prisma } = require('./database');
const { cache, keys } = require('./redis');
const logger = require('./logger');
const { sendJobAlertNotifications } = require('../routes/pushNotifications');
const { sendJobAlertEmail, sendBulkEmails } = require('../routes/emailService');

// Track job execution to prevent overlapping
const jobExecution = new Map();

/**
 * Job alert notification sender
 * Runs every day at 9 AM to send notifications for new jobs
 */
const sendDailyJobAlerts = cron.schedule(
  process.env.NOTIFICATION_SCHEDULE || '0 9 * * *',
  async () => {
    const jobName = 'sendDailyJobAlerts';
    
    if (jobExecution.has(jobName)) {
      logger.warn(`${jobName} is already running, skipping...`);
      return;
    }
    
    jobExecution.set(jobName, Date.now());
    logger.info(`Starting ${jobName}...`);
    
    try {
      // Get jobs posted in the last 24 hours
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
      
      const newJobs = await prisma.jobs_jobpost.findMany({
        where: {
          created_at: {
            gte: yesterday
          }
        },
        orderBy: {
          created_at: 'desc'
        },
        take: 1000 // Limit to prevent memory issues
      });
      
      if (!newJobs || newJobs.length === 0) {
        logger.info('No new jobs found for daily alerts');
        return;
      }
      
      logger.info(`Found ${newJobs.length} new jobs for daily alerts`);
      
      // Get all users with keywords and their device tokens
      const usersWithKeywords = await prisma.users.findMany({
        where: {
          keywords: {
            some: {}
          }
        },
        include: {
          keywords: true,
          sourcePreferences: true
        }
      });
      
      if (!usersWithKeywords || usersWithKeywords.length === 0) {
        logger.info('No users with keywords found');
        return;
      }
      
      logger.info(`Processing alerts for ${usersWithKeywords.length} users`);
      
      // Track statistics
      let totalNotificationsSent = 0;
      let totalEmailsSent = 0;
      let usersNotified = 0;
      
      // Process users in batches
      const batchSize = 50;
      for (let i = 0; i < usersWithKeywords.length; i += batchSize) {
        const userBatch = usersWithKeywords.slice(i, i + batchSize);
        
        const batchPromises = userBatch.map(async (user) => {
          try {
            // Find matching jobs for this user's keywords
            const userKeywords = user.keywords.map(k => k.keyword.toLowerCase());
            const userSources = user.sourcePreferences.map(s => s.source.toLowerCase());
            
            const matchingJobs = newJobs.filter(job => {
              // Check keyword match
              const keywordMatch = userKeywords.some(keyword => 
                job.title.toLowerCase().includes(keyword) ||
                job.company.toLowerCase().includes(keyword)
              );
              
              // Check source preference (if user has preferences)
              const sourceMatch = userSources.length === 0 || 
                userSources.some(source => 
                  job.source && job.source.toLowerCase().includes(source)
                );
              
              return keywordMatch && sourceMatch;
            });
            
            if (matchingJobs.length === 0) {
              return;
            }
            
            // Create notification records in database
            const notifications = await Promise.all(
              matchingJobs.slice(0, 10).map(async (job) => { // Limit to 10 per user
                const matchedKeyword = userKeywords.find(keyword =>
                  job.title.toLowerCase().includes(keyword) ||
                  job.company.toLowerCase().includes(keyword)
                );
                
                return prisma.notifications.create({
                  data: {
                    userId: user.id,
                    jobId: job.id,
                    matchedKeyword: matchedKeyword || userKeywords[0],
                    isRead: false
                  }
                });
              })
            );
            
            // Get device token from cache
            const deviceKey = keys.deviceToken(user.id);
            const deviceData = await cache.get(deviceKey);
            
            // Send push notification if device is registered
            if (deviceData && deviceData.deviceToken) {
              const pushUsers = [{
                ...user,
                deviceToken: deviceData.deviceToken,
                platform: deviceData.platform,
                keywords: userKeywords,
                unreadNotifications: notifications.length
              }];
              
              const pushResult = await sendJobAlertNotifications(matchingJobs.slice(0, 5), pushUsers);
              totalNotificationsSent += pushResult.successful;
            }
            
            // Send email notification
            const emailResult = await sendJobAlertEmail({
              to: user.email,
              jobs: matchingJobs.slice(0, 10),
              keywords: userKeywords,
              period: 'daily'
            });
            
            if (emailResult.success) {
              totalEmailsSent++;
            }
            
            // Update user's lastNotifiedAt
            await prisma.users.update({
              where: { id: user.id },
              data: { lastNotifiedAt: new Date() }
            });
            
            usersNotified++;
            
            logger.debug(`Processed alerts for user ${user.email}: ${matchingJobs.length} jobs`);
            
          } catch (error) {
            logger.error(`Error processing alerts for user ${user.email}:`, error);
          }
        });
        
        await Promise.all(batchPromises);
        
        // Small delay between batches
        if (i + batchSize < usersWithKeywords.length) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      logger.info(`Daily job alerts completed:`, {
        newJobsFound: newJobs.length,
        usersProcessed: usersWithKeywords.length,
        usersNotified,
        pushNotificationsSent: totalNotificationsSent,
        emailsSent: totalEmailsSent
      });
      
      // Clear relevant caches
      await cache.delPattern('user:*:notifications:*');
      await cache.delPattern('user:*:profile');
      
    } catch (error) {
      logger.error('Error in daily job alerts:', error);
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
 * Weekly digest sender
 * Runs every Monday at 9 AM to send weekly summaries
 */
const sendWeeklyDigest = cron.schedule(
  process.env.WEEKLY_DIGEST_SCHEDULE || '0 9 * * 1',
  async () => {
    const jobName = 'sendWeeklyDigest';
    
    if (jobExecution.has(jobName)) {
      logger.warn(`${jobName} is already running, skipping...`);
      return;
    }
    
    jobExecution.set(jobName, Date.now());
    logger.info(`Starting ${jobName}...`);
    
    try {
      const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      
      // Get weekly statistics for each user
      const usersWithActivity = await prisma.users.findMany({
        where: {
          OR: [
            {
              notifications: {
                some: {
                  sentAt: {
                    gte: oneWeekAgo
                  }
                }
              }
            },
            {
              keywords: {
                some: {}
              }
            }
          ]
        },
        include: {
          keywords: true,
          notifications: {
            where: {
              sentAt: {
                gte: oneWeekAgo
              }
            }
          }
        }
      });
      
      const digestEmails = usersWithActivity.map(user => ({
        to: user.email,
        subject: '📊 Your Weekly BirJob Summary',
        stats: {
          alertsSent: user.notifications.length,
          jobsMatched: user.notifications.length,
          activeKeywords: user.keywords.length,
          weeklyPeriod: {
            start: oneWeekAgo.toISOString(),
            end: new Date().toISOString()
          }
        },
        period: 'weekly'
      }));
      
      if (digestEmails.length > 0) {
        const result = await sendBulkEmails(digestEmails);
        logger.info(`Weekly digest sent to ${result.successful} users`);
      }
      
    } catch (error) {
      logger.error('Error in weekly digest:', error);
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
 * Runs every Sunday at 2 AM to clean up old logs and data
 */
const cleanupDatabase = cron.schedule(
  process.env.CLEANUP_LOGS_SCHEDULE || '0 2 * * 0',
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
      
      // Clean up old notifications (keep for 6 months)
      const sixMonthsAgo = new Date(Date.now() - 180 * 24 * 60 * 60 * 1000);
      const notificationsDeleted = await prisma.notifications.deleteMany({
        where: {
          sentAt: {
            lt: sixMonthsAgo
          },
          isRead: true
        }
      });
      
      // Clean up orphaned records (if any)
      // Add more cleanup logic as needed
      
      logger.info(`Database cleanup completed:`, {
        searchLogsDeleted: searchLogsDeleted.count,
        visitorLogsDeleted: visitorLogsDeleted.count,
        notificationsDeleted: notificationsDeleted.count,
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
 * Health check and monitoring
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
      
      // Check Redis connectivity
      await cache.redis.ping();
      
      // Log memory usage periodically
      logger.performance.logMemoryUsage();
      
      // Check for any long-running jobs
      const now = Date.now();
      for (const [job, startTime] of jobExecution.entries()) {
        const duration = now - startTime;
        if (duration > 30 * 60 * 1000) { // 30 minutes
          logger.warn(`Long-running job detected: ${job} (${Math.round(duration / 60000)} minutes)`);
        }
      }
      
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
 * Startup job to send test notifications (development only)
 */
const startupTasks = async () => {
  if (process.env.NODE_ENV === 'development') {
    logger.info('Running startup tasks...');
    
    try {
      // Warm up caches
      logger.info('Warming up caches...');
      
      // Test database connection
      await prisma.$queryRaw`SELECT 1`;
      logger.info('Database connection verified');
      
      // Test Redis connection
      await cache.redis.ping();
      logger.info('Redis connection verified');
      
      logger.info('Startup tasks completed');
      
    } catch (error) {
      logger.error('Startup tasks failed:', error);
    }
  }
};

/**
 * Initialize all cron jobs
 */
const initializeCronJobs = () => {
  logger.info('Initializing cron jobs...');
  
  // Start jobs based on environment
  if (process.env.ENABLE_CRON_JOBS !== 'false') {
    
    // Always enable these jobs
    healthCheck.start();
    cleanupCache.start();
    
    // Enable notification jobs in production or if explicitly enabled
    if (process.env.NODE_ENV === 'production' || process.env.ENABLE_NOTIFICATIONS === 'true') {
      sendDailyJobAlerts.start();
      sendWeeklyDigest.start();
      logger.info('Notification cron jobs started');
    }
    
    // Enable cleanup jobs in production
    if (process.env.NODE_ENV === 'production') {
      cleanupDatabase.start();
      logger.info('Database cleanup job started');
    }
    
    logger.info('Cron jobs initialized');
    
    // Log next execution times
    logger.info('Next job executions:');
    logger.info(`- Daily alerts: ${sendDailyJobAlerts.getStatus()}`);
    logger.info(`- Weekly digest: ${sendWeeklyDigest.getStatus()}`);
    logger.info(`- Database cleanup: ${cleanupDatabase.getStatus()}`);
  } else {
    logger.info('Cron jobs disabled by configuration');
  }
};

/**
 * Gracefully stop all cron jobs
 */
const stopCronJobs = () => {
  logger.info('Stopping cron jobs...');
  
  sendDailyJobAlerts.stop();
  sendWeeklyDigest.stop();
  cleanupCache.stop();
  cleanupDatabase.stop();
  healthCheck.stop();
  
  logger.info('All cron jobs stopped');
};

/**
 * Get status of all cron jobs
 */
const getCronJobStatus = () => {
  return {
    jobs: [
      {
        name: 'sendDailyJobAlerts',
        status: sendDailyJobAlerts.getStatus(),
        schedule: process.env.NOTIFICATION_SCHEDULE || '0 9 * * *',
        description: 'Send daily job alert notifications'
      },
      {
        name: 'sendWeeklyDigest', 
        status: sendWeeklyDigest.getStatus(),
        schedule: process.env.WEEKLY_DIGEST_SCHEDULE || '0 9 * * 1',
        description: 'Send weekly summary emails'
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
        schedule: process.env.CLEANUP_LOGS_SCHEDULE || '0 2 * * 0',
        description: 'Clean up old logs and data'
      },
      {
        name: 'healthCheck',
        status: healthCheck.getStatus(),
        schedule: '*/5 * * * *',
        description: 'System health monitoring'
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
 * Manually trigger a specific job (for testing/admin purposes)
 */
const triggerJob = async (jobName) => {
  logger.info(`Manually triggering job: ${jobName}`);
  
  switch (jobName) {
    case 'sendDailyJobAlerts':
      await sendDailyJobAlerts.fireOnTick();
      break;
    case 'sendWeeklyDigest':
      await sendWeeklyDigest.fireOnTick();
      break;
    case 'cleanupCache':
      await cleanupCache.fireOnTick();
      break;
    case 'cleanupDatabase':
      await cleanupDatabase.fireOnTick();
      break;
    case 'healthCheck':
      await healthCheck.fireOnTick();
      break;
    default:
      throw new Error(`Unknown job: ${jobName}`);
  }
  
  logger.info(`Job ${jobName} completed`);
};

module.exports = {
  initializeCronJobs,
  stopCronJobs,
  getCronJobStatus,
  triggerJob,
  startupTasks
};