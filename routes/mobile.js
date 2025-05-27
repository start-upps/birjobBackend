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

// Validation middleware
const validateAppInfo = [
  body('platform').isIn(['ios', 'android']).withMessage('Platform must be ios or android'),
  body('appVersion').trim().isLength({ min: 1, max: 20 }).withMessage('App version is required'),
  body('buildNumber').optional().trim(),
  body('deviceModel').optional().trim(),
  body('osVersion').optional().trim()
];

const validateFeedback = [
  body('email').optional().isEmail().normalizeEmail(),
  body('type').isIn(['bug', 'feature', 'general', 'rating']).withMessage('Invalid feedback type'),
  body('subject').trim().isLength({ min: 5, max: 100 }).withMessage('Subject must be 5-100 characters'),
  body('message').trim().isLength({ min: 10, max: 1000 }).withMessage('Message must be 10-1000 characters'),
  body('rating').optional().isInt({ min: 1, max: 5 }).withMessage('Rating must be 1-5'),
  body('deviceInfo').optional().isObject(),
  body('appVersion').optional().trim()
];

// Helper function to check validation results
const checkValidation = (req) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new ValidationError('Invalid request parameters', errors.array());
  }
};

// GET /api/v1/mobile/config - Get mobile app configuration
router.get('/config',
  [query('platform').isIn(['ios', 'android'])],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { platform } = req.query;
    const cacheKey = `mobile:config:${platform}`;
    
    // Try cache first
    let cachedConfig = await cache.get(cacheKey);
    if (cachedConfig) {
      return res.json({
        success: true,
        data: cachedConfig,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      // Get basic app configuration
      const config = {
        app: {
          name: 'BirJob',
          currentVersion: platform === 'ios' ? '1.0.0' : '1.0.0',
          minimumVersion: platform === 'ios' ? '1.0.0' : '1.0.0',
          updateRequired: false,
          updateUrl: platform === 'ios' 
            ? 'https://apps.apple.com/app/birjob/id123456789'
            : 'https://play.google.com/store/apps/details?id=com.birjob.app'
        },
        features: {
          pushNotifications: true,
          jobAlerts: true,
          savedJobs: true,
          jobFiltering: true,
          darkMode: true,
          analytics: true,
          offlineMode: false
        },
        api: {
          baseUrl: process.env.API_BASE_URL || 'https://api.birjob.az/api/v1',
          timeout: 30000,
          retryAttempts: 3,
          cacheTimeout: 300 // 5 minutes
        },
        notifications: {
          defaultEnabled: true,
          maxKeywords: 20,
          dailyDigestTime: '09:00',
          weeklyDigestEnabled: true
        },
        search: {
          maxResultsPerPage: 20,
          autoCompleteEnabled: true,
          searchHistoryEnabled: true,
          maxSearchHistory: 50
        },
        ui: {
          theme: 'system', // 'light', 'dark', 'system'
          accentColor: '#007AFF',
          animations: true,
          hapticFeedback: platform === 'ios',
          swipeGestures: true
        },
        support: {
          email: 'support@birjob.az',
          website: 'https://birjob.az',
          privacyPolicy: 'https://birjob.az/privacy',
          termsOfService: 'https://birjob.az/terms',
          faqUrl: 'https://birjob.az/faq'
        }
      };
      
      // Platform-specific configurations
      if (platform === 'ios') {
        config.ios = {
          appStoreId: '123456789',
          reviewPromptThreshold: 10, // After 10 app uses
          backgroundRefreshInterval: 3600, // 1 hour
          biometricsEnabled: true
        };
      } else if (platform === 'android') {
        config.android = {
          packageName: 'com.birjob.app',
          targetSdkVersion: 34,
          workManagerEnabled: true,
          adaptiveIconEnabled: true
        };
      }
      
      await cache.set(cacheKey, config, 4 * 60 * 60); // 4 hours
      
      res.json({
        success: true,
        data: config,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching mobile config for ${platform}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/mobile/app-launch - Track app launch
router.post('/app-launch',
  validateAppInfo,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const {
      platform,
      appVersion,
      buildNumber,
      deviceModel,
      osVersion,
      isFirstLaunch = false,
      sessionId,
      userId
    } = req.body;
    
    try {
      // Log app launch analytics
      const launchData = {
        platform,
        appVersion,
        buildNumber,
        deviceModel,
        osVersion,
        isFirstLaunch,
        sessionId,
        userId,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        timestamp: new Date()
      };
      
      // Store in analytics (you might want to create a separate table for app launches)
      logger.context.analytics('app_launch', launchData);
      
      // Update app usage statistics
      const dailyKey = `app:launches:${platform}:${new Date().toISOString().split('T')[0]}`;
      await cache.incr(dailyKey, 24 * 60 * 60); // Expire after 24 hours
      
      // Check if app update is required
      const currentVersion = appVersion;
      const minimumVersion = '1.0.0'; // This could come from database
      const updateRequired = compareVersions(currentVersion, minimumVersion) < 0;
      
      res.json({
        success: true,
        data: {
          sessionStarted: true,
          updateRequired,
          welcomeMessage: isFirstLaunch ? 'Welcome to BirJob!' : 'Welcome back!',
          serverTime: new Date().toISOString(),
          features: {
            newJobsAvailable: true,
            maintenanceMode: false
          }
        },
        message: 'App launch tracked successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error tracking app launch:', error);
      throw error;
    }
  })
);

// GET /api/v1/mobile/jobs/featured - Get featured jobs for mobile
router.get('/jobs/featured',
  [
    query('limit').optional().isInt({ min: 1, max: 50 }),
    query('userEmail').optional().isEmail()
  ],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { limit = 10, userEmail } = req.query;
    const cacheKey = `mobile:featured:${limit}:${userEmail || 'anonymous'}`;
    
    let cachedJobs = await cache.get(cacheKey);
    if (cachedJobs) {
      return res.json({
        success: true,
        data: cachedJobs,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      // Get user keywords if email provided
      let userKeywords = [];
      if (userEmail) {
        const user = await prisma.users.findUnique({
          where: { email: userEmail },
          include: { keywords: true }
        });
        userKeywords = user?.keywords.map(k => k.keyword) || [];
      }
      
      // Get featured jobs (recent, from popular sources, or matching user keywords)
      let featuredJobs;
      
      if (userKeywords.length > 0) {
        // Get jobs matching user keywords
        featuredJobs = await prisma.jobs_jobpost.findMany({
          where: {
            OR: userKeywords.map(keyword => ({
              OR: [
                { title: { contains: keyword, mode: 'insensitive' } },
                { company: { contains: keyword, mode: 'insensitive' } }
              ]
            }))
          },
          orderBy: { created_at: 'desc' },
          take: parseInt(limit),
          select: {
            id: true,
            title: true,
            company: true,
            apply_link: true,
            source: true,
            created_at: true
          }
        });
      } else {
        // Get recent jobs from popular sources
        featuredJobs = await prisma.jobs_jobpost.findMany({
          where: {
            created_at: {
              gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // Last 7 days
            }
          },
          orderBy: { created_at: 'desc' },
          take: parseInt(limit),
          select: {
            id: true,
            title: true,
            company: true,
            apply_link: true,
            source: true,
            created_at: true
          }
        });
      }
      
      const responseData = {
        jobs: featuredJobs.map(job => ({
          id: job.id,
          title: job.title,
          company: job.company,
          applyLink: job.apply_link,
          source: job.source,
          postedAt: job.created_at,
          postedRelative: getRelativeTime(job.created_at),
          isFeatured: true,
          matchReason: userKeywords.length > 0 ? 'keyword_match' : 'recent'
        })),
        metadata: {
          totalJobs: featuredJobs.length,
          isPersonalized: userKeywords.length > 0,
          lastUpdated: new Date().toISOString()
        }
      };
      
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.JOBS_LIST);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching featured jobs:', error);
      throw error;
    }
  })
);

// POST /api/v1/mobile/feedback - Submit app feedback
router.post('/feedback',
  validateFeedback,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const {
      email,
      type,
      subject,
      message,
      rating,
      deviceInfo,
      appVersion,
      attachments
    } = req.body;
    
    try {
      // Store feedback in database (you might want to create a feedback table)
      const feedbackData = {
        email: email || 'anonymous',
        type,
        subject,
        message,
        rating,
        deviceInfo: deviceInfo ? JSON.stringify(deviceInfo) : null,
        appVersion,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        status: 'new',
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      // For now, log the feedback (in production, you'd save to database)
      logger.info('Mobile feedback received:', feedbackData);
      
      // Send email notification to support team
      // await sendSupportNotification(feedbackData);
      
      res.status(201).json({
        success: true,
        data: {
          feedbackId: `fb_${Date.now()}`,
          status: 'received',
          estimatedResponse: type === 'bug' ? '24 hours' : '48 hours'
        },
        message: 'Feedback submitted successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error submitting feedback:', error);
      throw error;
    }
  })
);

// GET /api/v1/mobile/stats/user - Get user-specific mobile stats
router.get('/stats/user',
  [query('email').isEmail().normalizeEmail()],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.query;
    const cacheKey = `mobile:stats:${email}`;
    
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
        where: { email },
        select: {
          id: true,
          createdAt: true,
          lastNotifiedAt: true,
          keywords: { select: { keyword: true } },
          sourcePreferences: { select: { source: true } },
          notifications: {
            select: { id: true, isRead: true, sentAt: true },
            orderBy: { sentAt: 'desc' },
            take: 50
          }
        }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      // Calculate user statistics
      const now = new Date();
      const memberSince = user.createdAt;
      const daysSinceMember = Math.floor((now - memberSince) / (1000 * 60 * 60 * 24));
      
      const last30Days = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      const recentNotifications = user.notifications.filter(n => n.sentAt >= last30Days);
      const unreadNotifications = user.notifications.filter(n => !n.isRead);
      
      const statsData = {
        user: {
          memberSince: memberSince,
          daysMember: daysSinceMember,
          lastNotified: user.lastNotifiedAt
        },
        activity: {
          totalKeywords: user.keywords.length,
          totalSources: user.sourcePreferences.length,
          totalNotifications: user.notifications.length,
          unreadNotifications: unreadNotifications.length,
          notificationsLast30Days: recentNotifications.length
        },
        engagement: {
          notificationReadRate: user.notifications.length > 0 
            ? Math.round(((user.notifications.length - unreadNotifications.length) / user.notifications.length) * 100)
            : 0,
          averageNotificationsPerWeek: daysSinceMember > 0 
            ? Math.round((user.notifications.length / daysSinceMember) * 7)
            : 0
        },
        keywords: user.keywords.map(k => k.keyword),
        preferredSources: user.sourcePreferences.map(s => s.source),
        recommendations: {
          addMoreKeywords: user.keywords.length < 5,
          enableMoreSources: user.sourcePreferences.length === 0,
          updateProfile: !user.lastNotifiedAt
        }
      };
      
      await cache.set(cacheKey, statsData, CACHE_DURATIONS.USER_DATA);
      
      res.json({
        success: true,
        data: statsData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching user stats for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/mobile/crash-report - Report app crashes
router.post('/crash-report',
  [
    body('platform').isIn(['ios', 'android']),
    body('appVersion').trim().notEmpty(),
    body('crashLog').trim().isLength({ min: 10, max: 5000 }),
    body('deviceInfo').optional().isObject(),
    body('userEmail').optional().isEmail()
  ],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const {
      platform,
      appVersion,
      crashLog,
      deviceInfo,
      userEmail,
      timestamp: crashTimestamp,
      stackTrace
    } = req.body;
    
    try {
      const crashReport = {
        platform,
        appVersion,
        crashLog,
        deviceInfo: deviceInfo ? JSON.stringify(deviceInfo) : null,
        userEmail: userEmail || 'anonymous',
        crashTimestamp: crashTimestamp ? new Date(crashTimestamp) : new Date(),
        stackTrace,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        reportedAt: new Date()
      };
      
      // Log crash report (in production, save to database and alert dev team)
      logger.error('Mobile app crash reported:', crashReport);
      
      // Track crash statistics
      const crashKey = `crashes:${platform}:${new Date().toISOString().split('T')[0]}`;
      await cache.incr(crashKey, 24 * 60 * 60);
      
      res.status(201).json({
        success: true,
        data: {
          reportId: `crash_${Date.now()}`,
          status: 'received'
        },
        message: 'Crash report received',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error processing crash report:', error);
      throw error;
    }
  })
);

// Helper functions
function getRelativeTime(date) {
  const now = new Date();
  const diff = now - new Date(date);
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (minutes < 60) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  } else if (hours < 24) {
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  } else if (days < 7) {
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  } else {
    return new Date(date).toLocaleDateString();
  }
}

function compareVersions(version1, version2) {
  const v1parts = version1.split('.').map(Number);
  const v2parts = version2.split('.').map(Number);
  
  for (let i = 0; i < Math.max(v1parts.length, v2parts.length); i++) {
    const v1part = v1parts[i] || 0;
    const v2part = v2parts[i] || 0;
    
    if (v1part < v2part) return -1;
    if (v1part > v2part) return 1;
  }
  
  return 0;
}

module.exports = router;