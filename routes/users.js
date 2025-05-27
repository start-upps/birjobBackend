const express = require('express');
const { body, query, validationResult } = require('express-validator');
const { prisma } = require('../utils/database');
const { cache, keys, CACHE_DURATIONS } = require('../utils/redis');
const logger = require('../utils/logger');
const { 
  asyncHandler, 
  ValidationError, 
  NotFoundError, 
  ConflictError 
} = require('../middleware/errorHandler');

const router = express.Router();

// Validation middleware
const validateEmail = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required')
];

const validateKeyword = [
  body('keyword')
    .trim()
    .isLength({ min: 2, max: 50 })
    .withMessage('Keyword must be between 2 and 50 characters')
    .matches(/^[a-zA-Z0-9\s\+\#\-\.]+$/)
    .withMessage('Keyword contains invalid characters')
];

const validateSource = [
  body('source')
    .trim()
    .isLength({ min: 2, max: 50 })
    .withMessage('Source must be between 2 and 50 characters')
];

const validateEmailQuery = [
  query('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required')
];

// Helper function to check validation results
const checkValidation = (req) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new ValidationError('Invalid request parameters', errors.array());
  }
};

// Helper function to ensure user exists
const ensureUserExists = async (email) => {
  let user = await prisma.users.findUnique({
    where: { email }
  });
  
  if (!user) {
    user = await prisma.users.create({
      data: { email },
      select: {
        id: true,
        email: true,
        createdAt: true,
        lastNotifiedAt: true
      }
    });
    logger.info(`New user created: ${email}`);
  }
  
  return user;
};

// GET /api/v1/users/profile - Get user profile
router.get('/profile', 
  validateEmailQuery,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.query;
    const cacheKey = `user:${email}:profile`;
    
    // Try cache first
    let cachedProfile = await cache.get(cacheKey);
    if (cachedProfile) {
      return res.json({
        success: true,
        data: cachedProfile,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const user = await prisma.users.findUnique({
        where: { email },
        select: {
          id: true,
          email: true,
          createdAt: true,
          lastNotifiedAt: true,
          keywords: {
            select: {
              id: true,
              keyword: true,
              createdAt: true
            },
            orderBy: { createdAt: 'desc' }
          },
          sourcePreferences: {
            select: {
              id: true,
              source: true,
              createdAt: true
            },
            orderBy: { createdAt: 'desc' }
          },
          notifications: {
            select: {
              id: true,
              sentAt: true,
              isRead: true,
              matchedKeyword: true
            },
            orderBy: { sentAt: 'desc' },
            take: 10 // Last 10 notifications
          },
          _count: {
            select: {
              keywords: true,
              sourcePreferences: true,
              notifications: true
            }
          }
        }
      });
      
      if (!user) {
        // Create user if doesn't exist
        const newUser = await ensureUserExists(email);
        const profileData = {
          user: {
            id: newUser.id,
            email: newUser.email,
            memberSince: newUser.createdAt,
            lastNotified: newUser.lastNotifiedAt
          },
          keywords: [],
          sourcePreferences: [],
          recentNotifications: [],
          stats: {
            totalKeywords: 0,
            totalSources: 0,
            totalNotifications: 0,
            unreadNotifications: 0
          }
        };
        
        await cache.set(cacheKey, profileData, CACHE_DURATIONS.USER_DATA);
        
        return res.json({
          success: true,
          data: profileData,
          cached: false,
          timestamp: new Date().toISOString()
        });
      }
      
      const unreadNotifications = user.notifications.filter(n => !n.isRead).length;
      
      const profileData = {
        user: {
          id: user.id,
          email: user.email,
          memberSince: user.createdAt,
          lastNotified: user.lastNotifiedAt
        },
        keywords: user.keywords.map(k => ({
          id: k.id,
          keyword: k.keyword,
          addedAt: k.createdAt
        })),
        sourcePreferences: user.sourcePreferences.map(s => ({
          id: s.id,
          source: s.source,
          addedAt: s.createdAt
        })),
        recentNotifications: user.notifications.map(n => ({
          id: n.id,
          sentAt: n.sentAt,
          isRead: n.isRead,
          matchedKeyword: n.matchedKeyword
        })),
        stats: {
          totalKeywords: user._count.keywords,
          totalSources: user._count.sourcePreferences,
          totalNotifications: user._count.notifications,
          unreadNotifications
        }
      };
      
      await cache.set(cacheKey, profileData, CACHE_DURATIONS.USER_DATA);
      
      res.json({
        success: true,
        data: profileData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching user profile for ${email}:`, error);
      throw error;
    }
  })
);

// GET /api/v1/users/keywords - Get user keywords
router.get('/keywords',
  validateEmailQuery,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.query;
    const cacheKey = keys.userKeywords(email);
    
    let cachedKeywords = await cache.get(cacheKey);
    if (cachedKeywords) {
      return res.json({
        success: true,
        data: cachedKeywords,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const user = await prisma.users.findUnique({
        where: { email },
        select: {
          keywords: {
            select: {
              id: true,
              keyword: true,
              createdAt: true
            },
            orderBy: { createdAt: 'desc' }
          }
        }
      });
      
      const keywordsList = user?.keywords || [];
      
      const responseData = {
        keywords: keywordsList.map(k => ({
          id: k.id,
          keyword: k.keyword,
          addedAt: k.createdAt
        })),
        totalKeywords: keywordsList.length,
        maxKeywords: 20, // Limit per user
        canAddMore: keywordsList.length < 20
      };
      
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.USER_DATA);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching keywords for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/users/keywords - Add keyword
router.post('/keywords',
  [...validateEmail, ...validateKeyword],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email, keyword } = req.body;
    
    try {
      // Ensure user exists
      const user = await ensureUserExists(email);
      
      // Check if keyword already exists for this user
      const existingKeyword = await prisma.keywords.findUnique({
        where: {
          userId_keyword: {
            userId: user.id,
            keyword: keyword.toLowerCase()
          }
        }
      });
      
      if (existingKeyword) {
        throw new ConflictError('Keyword already exists for this user');
      }
      
      // Check keyword limit
      const keywordCount = await prisma.keywords.count({
        where: { userId: user.id }
      });
      
      if (keywordCount >= 20) {
        throw new ValidationError('Maximum of 20 keywords allowed per user');
      }
      
      // Add keyword
      const newKeyword = await prisma.keywords.create({
        data: {
          userId: user.id,
          keyword: keyword.toLowerCase()
        },
        select: {
          id: true,
          keyword: true,
          createdAt: true
        }
      });
      
      // Clear cache
      await cache.del(keys.userKeywords(email));
      await cache.del(`user:${email}:profile`);
      
      logger.info(`Keyword added for user ${email}: ${keyword}`);
      
      res.status(201).json({
        success: true,
        data: {
          keyword: {
            id: newKeyword.id,
            keyword: newKeyword.keyword,
            addedAt: newKeyword.createdAt
          }
        },
        message: 'Keyword added successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error adding keyword for ${email}:`, error);
      throw error;
    }
  })
);

// DELETE /api/v1/users/keywords - Remove keyword
router.delete('/keywords',
  [
    body('email').isEmail().normalizeEmail(),
    body('keyword').trim().notEmpty()
  ],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email, keyword } = req.body;
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const deletedKeyword = await prisma.keywords.delete({
        where: {
          userId_keyword: {
            userId: user.id,
            keyword: keyword.toLowerCase()
          }
        }
      });
      
      // Clear cache
      await cache.del(keys.userKeywords(email));
      await cache.del(`user:${email}:profile`);
      
      logger.info(`Keyword removed for user ${email}: ${keyword}`);
      
      res.json({
        success: true,
        data: {
          deletedKeyword: deletedKeyword.keyword
        },
        message: 'Keyword removed successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      if (error.code === 'P2025') {
        throw new NotFoundError('Keyword');
      }
      logger.error(`Error removing keyword for ${email}:`, error);
      throw error;
    }
  })
);

// GET /api/v1/users/sources - Get user source preferences
router.get('/sources',
  validateEmailQuery,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.query;
    const cacheKey = keys.userSources(email);
    
    let cachedSources = await cache.get(cacheKey);
    if (cachedSources) {
      return res.json({
        success: true,
        data: cachedSources,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const user = await prisma.users.findUnique({
        where: { email },
        select: {
          sourcePreferences: {
            select: {
              id: true,
              source: true,
              createdAt: true
            },
            orderBy: { createdAt: 'desc' }
          }
        }
      });
      
      // Get all available sources
      const allSources = await prisma.jobs_jobpost.groupBy({
        by: ['source'],
        where: { source: { not: null } },
        _count: { source: true },
        orderBy: { _count: { source: 'desc' } }
      });
      
      const userSources = user?.sourcePreferences || [];
      const userSourceNames = userSources.map(s => s.source);
      
      const responseData = {
        selectedSources: userSources.map(s => ({
          id: s.id,
          source: s.source,
          addedAt: s.createdAt
        })),
        availableSources: allSources.map(s => ({
          source: s.source,
          jobCount: s._count.source,
          isSelected: userSourceNames.includes(s.source)
        })),
        stats: {
          totalSelected: userSources.length,
          totalAvailable: allSources.length
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
      logger.error(`Error fetching sources for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/users/sources - Add source preference
router.post('/sources',
  [...validateEmail, ...validateSource],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email, source } = req.body;
    
    try {
      const user = await ensureUserExists(email);
      
      // Check if source preference already exists
      const existingSource = await prisma.sourcePreferences.findUnique({
        where: {
          userId_source: {
            userId: user.id,
            source
          }
        }
      });
      
      if (existingSource) {
        throw new ConflictError('Source preference already exists');
      }
      
      const newSourcePreference = await prisma.sourcePreferences.create({
        data: {
          userId: user.id,
          source
        },
        select: {
          id: true,
          source: true,
          createdAt: true
        }
      });
      
      // Clear cache
      await cache.del(keys.userSources(email));
      await cache.del(`user:${email}:profile`);
      
      logger.info(`Source preference added for user ${email}: ${source}`);
      
      res.status(201).json({
        success: true,
        data: {
          sourcePreference: {
            id: newSourcePreference.id,
            source: newSourcePreference.source,
            addedAt: newSourcePreference.createdAt
          }
        },
        message: 'Source preference added successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error adding source preference for ${email}:`, error);
      throw error;
    }
  })
);

// DELETE /api/v1/users/sources - Remove source preference
router.delete('/sources',
  [
    body('email').isEmail().normalizeEmail(),
    body('source').trim().notEmpty()
  ],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email, source } = req.body;
    
    try {
      const user = await prisma.users.findUnique({
        where: { email }
      });
      
      if (!user) {
        throw new NotFoundError('User');
      }
      
      const deletedSource = await prisma.sourcePreferences.delete({
        where: {
          userId_source: {
            userId: user.id,
            source
          }
        }
      });
      
      // Clear cache
      await cache.del(keys.userSources(email));
      await cache.del(`user:${email}:profile`);
      
      logger.info(`Source preference removed for user ${email}: ${source}`);
      
      res.json({
        success: true,
        data: {
          deletedSource: deletedSource.source
        },
        message: 'Source preference removed successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      if (error.code === 'P2025') {
        throw new NotFoundError('Source preference');
      }
      logger.error(`Error removing source preference for ${email}:`, error);
      throw error;
    }
  })
);

// POST /api/v1/users/register - Register/create user
router.post('/register',
  validateEmail,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { email } = req.body;
    
    try {
      const user = await ensureUserExists(email);
      
      res.status(201).json({
        success: true,
        data: {
          user: {
            id: user.id,
            email: user.email,
            memberSince: user.createdAt
          }
        },
        message: 'User registered successfully',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error registering user ${email}:`, error);
      throw error;
    }
  })
);

module.exports = router;