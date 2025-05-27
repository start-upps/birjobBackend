const express = require('express');
const { body, query, validationResult } = require('express-validator');
const { prisma } = require('../utils/database');
const { cache, keys, CACHE_DURATIONS } = require('../utils/redis');
const logger = require('../utils/logger');
const { 
  asyncHandler, 
  ValidationError, 
  NotFoundError 
} = require('../middleware/errorHandler');

const router = express.Router();

// Import notification services
const { sendPushNotification, sendBulkNotifications } = require('./pushNotifications');
const { sendEmailNotification } = require('./emailService');
// Validation middleware
const validateEmail = [
  query('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required')
];

const validateNotificationRequest = [
  body('email').isEmail().normalizeEmail(),
  body('title').trim().isLength({ min: 1, max: 100 }),
  body('body').trim().isLength({ min: 1, max: 200 }),
  body('data').optional().isObject()
];

const validateDeviceToken = [
  body('email').isEmail().normalizeEmail(),
  body('deviceToken').trim().isLength({ min: 10 }).withMessage('Valid device token required'),
  body('platform').isIn(['ios', 'android']).withMessage('Platform must be ios or android'),
  body('appVersion').optional().trim(),
  body('deviceModel').optional().trim()
];

// Helper function to check validation results
const checkValidation = (req) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new ValidationError('Invalid request parameters', errors.array());
  }
};

// GET /api/v1/notifications - Get user notifications
router.get('/',
  validateEmail,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email, page = 1, limit = 20, unreadOnly = false } = req.query;
    const pageNum = parseInt(page);
    const limitNum = parseInt(limit);
    const offset = (pageNum - 1) * limitNum;
    
    const cacheKey = keys.userNotifications(email) + `:${page}:${limit}:${unreadOnly}`;
    
    // Try cache first
    let cachedNotifications = await cache.get(cacheKey);
    if (cachedNotifications) {
      return res.json({
        success: true,
        data: cachedNotifications,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const whereClause = { userId: user.id };
      if (unreadOnly === 'true') {
        whereClause.isRead = false;
      }
      
      const [notifications, totalCount, unreadCount] = await Promise.all([
        prisma.notifications.findMany({
          where: whereClause,
          orderBy: { sentAt: 'desc' },
          skip: offset,
          take: limitNum,
          include: {
            job: {
              select: {
                id: true,
                title: true,
                company: true,
                source: true,
                created_at: true
              }
            }
          }
        }),
        prisma.notifications.count({ where: whereClause }),
        prisma.notifications.count({ 
          where: { userId: user.id, isRead: false } 
        })
      ]);
      
      const responseData = {
        notifications: notifications.map(n => ({
          id: n.id,
          sentAt: n.sentAt,
          isRead: n.isRead,
          matchedKeyword: n.matchedKeyword,
          job: {
            id: n.job.id,
            title: n.job.title,
            company: n.job.company,
            source: n.job.source,
            postedAt: n.job.created_at
          }
        })),
        metadata: {
          totalNotifications: totalCount,
          unreadCount,
          currentPage: pageNum,
          totalPages: Math.ceil(totalCount / limitNum),
          hasNextPage: pageNum < Math.ceil(totalCount / limitNum),
          hasPreviousPage: pageNum > 1
        }
      };
      
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.USER_DATA);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching notifications for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/notifications/register-device - Register device for push notifications
router.post('/register-device',
  validateDeviceToken,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { 
      email, 
      deviceToken, 
      platform, 
      appVersion, 
      deviceModel 
    } = req.body;
    
    try {
      // Ensure user exists
      let user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        user = await prisma.users.create({
          data: { email }
        });
        logger.info(`New user created for device registration: ${email}`);
      }
      
      // Store device token (you might want to create a separate devices table)
      const deviceKey = keys.deviceToken(user.id);
      const deviceData = {
        userId: user.id,
        email,
        deviceToken,
        platform,
        appVersion,
        deviceModel,
        registeredAt: new Date().toISOString(),
        isActive: true
      };
      
      await cache.set(deviceKey, deviceData, 30 * 24 * 60 * 60); // 30 days
      
      logger.context.notification('device_registered', email, true);
      
      res.status(201).json({
        success: true,
        data: {
          deviceRegistered: true,
          platform,
          registeredAt: deviceData.registeredAt
        },
        message: 'Device registered for push notifications',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error registering device for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/notifications/send - Send immediate notification
router.post('/send',
  validateNotificationRequest,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email, title, body, data = {} } = req.body;
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      // Get device token from cache
      const deviceKey = keys.deviceToken(user.id);
      const deviceData = await cache.get(deviceKey);
      
      let pushResult = null;
      if (deviceData && deviceData.deviceToken) {
        // Send push notification
        pushResult = await sendPushNotification({
          deviceToken: deviceData.deviceToken,
          platform: deviceData.platform,
          title,
          body,
          data
        });
        
        logger.context.notification('push_sent', email, pushResult.success);
      }
      
      // Also send email notification as backup
      const emailResult = await sendEmailNotification({
        to: email,
        subject: title,
        body,
        data
      });
      
      logger.context.notification('email_sent', email, emailResult.success);
      
      res.json({
        success: true,
        data: {
          pushNotification: pushResult ? {
            sent: pushResult.success,
            platform: deviceData.platform
          } : { sent: false, reason: 'No device registered' },
          emailNotification: {
            sent: emailResult.success
          }
        },
        message: 'Notification sent',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error sending notification to ${email}:`, error);
      throw error;
    }
  })
);

// PUT /api/v1/notifications/:id/read - Mark notification as read
router.put('/:id/read',
  asyncHandler(async (req, res) => {
    const notificationId = parseInt(req.params.id);
    
    if (isNaN(notificationId)) {
      throw new ValidationError('Invalid notification ID');
    }
    
    try {
      const notification = await prisma.notifications.update({
        where: { id: notificationId },
        data: { isRead: true },
        include: {
          user: {
            select: { email: true }
          }
        }
      });
      
      // Clear user notifications cache
      const email = notification.user.email;
      await cache.delPattern(`${keys.userNotifications(email)}:*`);
      await cache.del(`user:${email}:profile`);
      
      res.json({
        success: true,
        data: {
          notificationId: notification.id,
          isRead: notification.isRead
        },
        message: 'Notification marked as read',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      if (error.code === 'P2025') {
        throw new NotFoundError('Notification');
      }
      logger.error(`Error marking notification ${notificationId} as read:`, error);
      throw error;
    }
  })
);

// PUT /api/v1/notifications/read-all - Mark all notifications as read for user
router.put('/read-all',
  [body('email').isEmail().normalizeEmail()],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.body;
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const result = await prisma.notifications.updateMany({
        where: { 
          userId: user.id,
          isRead: false
        },
        data: { isRead: true }
      });
      
      // Clear caches
      await cache.delPattern(`${keys.userNotifications(email)}:*`);
      await cache.del(`user:${email}:profile`);
      
      res.json({
        success: true,
        data: {
          updatedCount: result.count
        },
        message: `${result.count} notifications marked as read`,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error marking all notifications as read for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/notifications/test - Test notification endpoint (development only)
router.post('/test',
  [
    body('email').isEmail().normalizeEmail(),
    body('message').optional().trim()
  ],
  asyncHandler(async (req, res) => {
    if (process.env.NODE_ENV === 'production') {
      return res.status(403).json({
        success: false,
        error: 'Test endpoint not available in production'
      });
    }
    
    checkValidation(req);
    
    const { email, message = 'Test notification from BirJob API' } = req.body;
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const deviceKey = keys.deviceToken(user.id);
      const deviceData = await cache.get(deviceKey);
      
      const testNotification = {
        title: 'BirJob Test Notification',
        body: message,
        data: {
          type: 'test',
          timestamp: new Date().toISOString()
        }
      };
      
      let results = {};
      
      if (deviceData && deviceData.deviceToken) {
        results.push = await sendPushNotification({
          deviceToken: deviceData.deviceToken,
          platform: deviceData.platform,
          ...testNotification
        });
      } else {
        results.push = { sent: false, reason: 'No device registered' };
      }
      
      results.email = await sendEmailNotification({
        to: email,
        subject: testNotification.title,
        body: testNotification.body,
        data: testNotification.data
      });
      
      res.json({
        success: true,
        data: {
          testResults: results,
          deviceInfo: deviceData ? {
            platform: deviceData.platform,
            hasToken: !!deviceData.deviceToken
          } : null
        },
        message: 'Test notification sent',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error sending test notification to ${email}:`, error);
      throw error;
    }
  })
);

// GET /api/v1/notifications/stats - Get notification statistics
router.get('/stats',
  validateEmail,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.query;
    const cacheKey = `notifications:stats:${email}`;
    
    let cachedStats = await cache.get(cacheKey);
    if (cachedStats) {
      return res.json({
        success: true,
        data: cachedStats,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const [totalCount, unreadCount, last7Days, topKeywords] = await Promise.all([
        prisma.notifications.count({ where: { userId: user.id } }),
        prisma.notifications.count({ where: { userId: user.id, isRead: false } }),
        prisma.notifications.count({ 
          where: { 
            userId: user.id,
            sentAt: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) }
          }
        }),
        prisma.notifications.groupBy({
          by: ['matchedKeyword'],
          where: { userId: user.id },
          _count: { matchedKeyword: true },
          orderBy: { _count: { matchedKeyword: 'desc' } },
          take: 5
        })
      ]);
      
      const deviceKey = keys.deviceToken(user.id);
      const deviceData = await cache.get(deviceKey);
      
      const statsData = {
        totalNotifications: totalCount,
        unreadNotifications: unreadCount,
        notificationsLast7Days: last7Days,
        topMatchingKeywords: topKeywords.map(k => ({
          keyword: k.matchedKeyword,
          count: k._count.matchedKeyword
        })),
        deviceInfo: deviceData ? {
          platform: deviceData.platform,
          registeredAt: deviceData.registeredAt,
          isActive: deviceData.isActive
        } : null,
        readRate: totalCount > 0 ? Math.round(((totalCount - unreadCount) / totalCount) * 100) : 0
      };
      
      await cache.set(cacheKey, statsData, CACHE_DURATIONS.USER_DATA);
      
      res.json({
        success: true,
        data: statsData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching notification stats for ${email}:`, error);
      throw error;
    }
  })
);

// DELETE /api/v1/notifications/device - Unregister device
router.delete('/device',
  [body('email').isEmail().normalizeEmail()],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.body;
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const deviceKey = keys.deviceToken(user.id);
      await cache.del(deviceKey);
      
      logger.context.notification('device_unregistered', email, true);
      
      res.json({
        success: true,
        data: {
          deviceUnregistered: true
        },
        message: 'Device unregistered from push notifications',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error unregistering device for ${email}:`, error);
      throw error;
    }
  })
);

module.exports = router;