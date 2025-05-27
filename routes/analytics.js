const express = require('express');
const { body, query, validationResult } = require('express-validator');
const UAParser = require('ua-parser-js');
const geoip = require('geoip-lite');
const { prisma } = require('../utils/database');
const { cache, keys, CACHE_DURATIONS } = require('../utils/redis');
const logger = require('../utils/logger');
const { 
  asyncHandler, 
  ValidationError 
} = require('../middleware/errorHandler');

const router = express.Router();

// Validation middleware
const validateSearchLog = [
  body('query').trim().isLength({ min: 1, max: 200 }).withMessage('Query is required'),
  body('resultCount').optional().isInt({ min: 0 }),
  body('searchDuration').optional().isInt({ min: 0 }),
  body('clickedResult').optional().isBoolean(),
  body('deviceType').optional().isIn(['desktop', 'mobile', 'tablet']),
  body('sessionId').optional().trim(),
  body('searchSource').optional().trim()
];

const validateVisitorLog = [
  body('visitorId').optional().trim(),
  body('sessionId').optional().trim(),
  body('path').optional().trim(),
  body('referrer').optional().trim(),
  body('deviceType').optional().isIn(['desktop', 'mobile', 'tablet'])
];

// Helper function to check validation results
const checkValidation = (req) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new ValidationError('Invalid request parameters', errors.array());
  }
};

// Helper function to extract device info from user agent
const extractDeviceInfo = (userAgent) => {
  const parser = new UAParser(userAgent);
  const result = parser.getResult();
  
  return {
    browser: result.browser.name || 'Unknown',
    browserVersion: result.browser.version || 'Unknown',
    operatingSystem: result.os.name || 'Unknown',
    osVersion: result.os.version || 'Unknown',
    deviceType: result.device.type || 'desktop',
    deviceVendor: result.device.vendor || null,
    deviceModel: result.device.model || null
  };
};

// Helper function to extract location info from IP
const extractLocationInfo = (ip) => {
  try {
    const geo = geoip.lookup(ip);
    if (geo) {
      return {
        country: geo.country || null,
        city: geo.city || null,
        region: geo.region || null,
        timezone: geo.timezone || null
      };
    }
  } catch (error) {
    logger.error('Error extracting location info:', error);
  }
  
  return {
    country: null,
    city: null,
    region: null,
    timezone: null
  };
};

// POST /api/v1/analytics/search - Log search analytics
router.post('/search',
  validateSearchLog,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const {
      query,
      resultCount,
      searchDuration,
      clickedResult = false,
      deviceType,
      sessionId,
      searchSource = 'api',
      searchType = 'basic',
      hasFilters = false,
      filterTypes,
      previousQuery,
      isRetry = false,
      isRefinement = false
    } = req.body;
    
    try {
      const ip = req.ip || req.connection.remoteAddress;
      const userAgent = req.get('User-Agent');
      
      // Extract device and location info
      const deviceInfo = extractDeviceInfo(userAgent);
      const locationInfo = extractLocationInfo(ip);
      
      // Create search log entry
      const searchLog = await prisma.search_logs.create({
        data: {
          query: query.toLowerCase().trim(),
          searchType,
          resultCount,
          clickedResult,
          
          // User identification
          ip,
          sessionId,
          visitorId: req.get('X-Visitor-ID') || null,
          
          // Device and browser info
          userAgent,
          browser: deviceInfo.browser,
          browserVersion: deviceInfo.browserVersion,
          operatingSystem: deviceInfo.operatingSystem,
          osVersion: deviceInfo.osVersion,
          deviceType: deviceType || deviceInfo.deviceType,
          deviceVendor: deviceInfo.deviceVendor,
          deviceModel: deviceInfo.deviceModel,
          
          // Location info
          country: locationInfo.country,
          city: locationInfo.city,
          region: locationInfo.region,
          timezone: locationInfo.timezone,
          
          // Request context
          path: req.get('Referer') || null,
          referrer: req.get('Referer') || null,
          language: req.get('Accept-Language')?.split(',')[0] || null,
          
          // Search context
          searchDuration,
          searchSource,
          previousQuery,
          isRetry,
          isRefinement,
          hasFilters,
          filterTypes: filterTypes ? JSON.stringify(filterTypes) : null,
          
          // Timing
          searchStartTime: searchDuration ? new Date(Date.now() - searchDuration) : null,
          searchEndTime: new Date(),
          timestamp: new Date()
        }
      });
      
      // Update search analytics cache
      await cache.del('analytics:search:*');
      
      logger.context.analytics('search_logged', {
        query,
        resultCount,
        sessionId,
        deviceType: deviceType || deviceInfo.deviceType
      });
      
      res.status(201).json({
        success: true,
        data: {
          logId: searchLog.id,
          timestamp: searchLog.timestamp
        },
        message: 'Search analytics logged',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error logging search analytics:', error);
      throw error;
    }
  })
);

// POST /api/v1/analytics/visitor - Log visitor analytics
router.post('/visitor',
  validateVisitorLog,
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const {
      visitorId,
      sessionId,
      path,
      referrer,
      deviceType,
      screenWidth,
      screenHeight,
      viewportWidth,
      viewportHeight,
      colorDepth,
      connectionType,
      battery,
      referrerSource,
      utmSource,
      utmMedium,
      utmCampaign,
      utmContent,
      utmTerm,
      entryPage,
      landingTime
    } = req.body;
    
    try {
      const ip = req.ip || req.connection.remoteAddress;
      const userAgent = req.get('User-Agent');
      
      // Extract device and location info
      const deviceInfo = extractDeviceInfo(userAgent);
      const locationInfo = extractLocationInfo(ip);
      
      // Create visitor log entry
      const visitorLog = await prisma.visitor_logs.create({
        data: {
          ip,
          visitorId,
          sessionId,
          
          // Device and browser info
          userAgent,
          browser: deviceInfo.browser,
          browserVersion: deviceInfo.browserVersion,
          operatingSystem: deviceInfo.operatingSystem,
          osVersion: deviceInfo.osVersion,
          deviceType: deviceType || deviceInfo.deviceType,
          deviceVendor: deviceInfo.deviceVendor,
          deviceModel: deviceInfo.deviceModel,
          
          // Location info
          country: locationInfo.country,
          city: locationInfo.city,
          region: locationInfo.region,
          timezone: locationInfo.timezone,
          language: req.get('Accept-Language')?.split(',')[0] || null,
          
          // Page context
          path,
          referrer,
          query: req.query ? JSON.stringify(req.query) : null,
          
          // Screen and viewport
          screenWidth,
          screenHeight,
          viewportWidth,
          viewportHeight,
          colorDepth,
          
          // Connection info
          connectionType,
          battery,
          
          // Marketing attribution
          referrerSource,
          utmSource,
          utmMedium,
          utmCampaign,
          utmContent,
          utmTerm,
          entryPage,
          landingTime: landingTime ? new Date(landingTime) : null,
          
          timestamp: new Date()
        }
      });
      
      // Update visitor analytics cache
      await cache.del('analytics:visitor:*');
      
      logger.context.analytics('visitor_logged', {
        visitorId,
        sessionId,
        path,
        deviceType: deviceType || deviceInfo.deviceType
      });
      
      res.status(201).json({
        success: true,
        data: {
          logId: visitorLog.id,
          timestamp: visitorLog.timestamp
        },
        message: 'Visitor analytics logged',
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error logging visitor analytics:', error);
      throw error;
    }
  })
);

// GET /api/v1/analytics/search-stats - Get search analytics
router.get('/search-stats',
  [
    query('period').optional().isIn(['today', 'week', 'month', 'year']),
    query('limit').optional().isInt({ min: 1, max: 100 })
  ],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { period = 'week', limit = 20 } = req.query;
    const cacheKey = keys.analytics('search', period);
    
    // Try cache first
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
      // Calculate date range
      const now = new Date();
      let startDate;
      
      switch (period) {
        case 'today':
          startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          break;
        case 'week':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        case 'year':
          startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
          break;
        default:
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      }
      
      const [
        totalSearches,
        uniqueQueries,
        topQueries,
        deviceBreakdown,
        locationBreakdown,
        averageResults,
        searchTrends
      ] = await Promise.all([
        prisma.search_logs.count({
          where: { timestamp: { gte: startDate } }
        }),
        
        prisma.search_logs.groupBy({
          by: ['query'],
          where: { timestamp: { gte: startDate } },
          _count: { query: true }
        }).then(results => results.length),
        
        prisma.search_logs.groupBy({
          by: ['query'],
          where: { timestamp: { gte: startDate } },
          _count: { query: true },
          orderBy: { _count: { query: 'desc' } },
          take: parseInt(limit)
        }),
        
        prisma.search_logs.groupBy({
          by: ['deviceType'],
          where: { 
            timestamp: { gte: startDate },
            deviceType: { not: null }
          },
          _count: { deviceType: true }
        }),
        
        prisma.search_logs.groupBy({
          by: ['country'],
          where: { 
            timestamp: { gte: startDate },
            country: { not: null }
          },
          _count: { country: true },
          orderBy: { _count: { country: 'desc' } },
          take: 10
        }),
        
        prisma.search_logs.aggregate({
          where: { 
            timestamp: { gte: startDate },
            resultCount: { not: null }
          },
          _avg: { resultCount: true }
        }),
        
        prisma.$queryRaw`
          SELECT 
            DATE(timestamp) as date,
            COUNT(*) as search_count
          FROM search_logs 
          WHERE timestamp >= ${startDate}
          GROUP BY DATE(timestamp)
          ORDER BY date DESC
          LIMIT 30
        `
      ]);
      
      const statsData = {
        period: {
          name: period,
          startDate: startDate.toISOString(),
          endDate: now.toISOString()
        },
        summary: {
          totalSearches,
          uniqueQueries,
          averageResultsPerSearch: averageResults._avg.resultCount || 0,
          searchesPerDay: period === 'today' ? totalSearches : Math.round(totalSearches / getDaysDifference(startDate, now))
        },
        topQueries: topQueries.map(q => ({
          query: q.query,
          searchCount: q._count.query
        })),
        deviceBreakdown: deviceBreakdown.map(d => ({
          device: d.deviceType,
          count: d._count.deviceType,
          percentage: Math.round((d._count.deviceType / totalSearches) * 100)
        })),
        topCountries: locationBreakdown.map(l => ({
          country: l.country,
          searchCount: l._count.country
        })),
        dailyTrends: searchTrends.map(trend => ({
          date: trend.date,
          searchCount: Number(trend.search_count)
        })),
        lastUpdated: new Date().toISOString()
      };
      
      await cache.set(cacheKey, statsData, CACHE_DURATIONS.ANALYTICS);
      
      res.json({
        success: true,
        data: statsData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching search analytics:', error);
      throw error;
    }
  })
);

// GET /api/v1/analytics/visitor-stats - Get visitor analytics
router.get('/visitor-stats',
  [query('period').optional().isIn(['today', 'week', 'month', 'year'])],
  asyncHandler(async (req, res) => {
    checkValidation(req);
    
    const { period = 'week' } = req.query;
    const cacheKey = keys.analytics('visitor', period);
    
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
      const now = new Date();
      let startDate;
      
      switch (period) {
        case 'today':
          startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          break;
        case 'week':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        case 'year':
          startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
          break;
        default:
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      }
      
      const [
        totalVisitors,
        uniqueVisitors,
        pageViews,
        topPages,
        deviceStats,
        browserStats,
        countryStats,
        referrerStats,
        dailyVisitors
      ] = await Promise.all([
        prisma.visitor_logs.count({
          where: { timestamp: { gte: startDate } }
        }),
        
        prisma.visitor_logs.groupBy({
          by: ['visitorId'],
          where: { 
            timestamp: { gte: startDate },
            visitorId: { not: null }
          }
        }).then(results => results.length),
        
        prisma.visitor_logs.count({
          where: { 
            timestamp: { gte: startDate },
            path: { not: null }
          }
        }),
        
        prisma.visitor_logs.groupBy({
          by: ['path'],
          where: { 
            timestamp: { gte: startDate },
            path: { not: null }
          },
          _count: { path: true },
          orderBy: { _count: { path: 'desc' } },
          take: 10
        }),
        
        prisma.visitor_logs.groupBy({
          by: ['deviceType'],
          where: { 
            timestamp: { gte: startDate },
            deviceType: { not: null }
          },
          _count: { deviceType: true }
        }),
        
        prisma.visitor_logs.groupBy({
          by: ['browser'],
          where: { 
            timestamp: { gte: startDate },
            browser: { not: null }
          },
          _count: { browser: true },
          orderBy: { _count: { browser: 'desc' } },
          take: 5
        }),
        
        prisma.visitor_logs.groupBy({
          by: ['country'],
          where: { 
            timestamp: { gte: startDate },
            country: { not: null }
          },
          _count: { country: true },
          orderBy: { _count: { country: 'desc' } },
          take: 10
        }),
        
        prisma.visitor_logs.groupBy({
          by: ['referrerSource'],
          where: { 
            timestamp: { gte: startDate },
            referrerSource: { not: null }
          },
          _count: { referrerSource: true },
          orderBy: { _count: { referrerSource: 'desc' } },
          take: 5
        }),
        
        prisma.$queryRaw`
          SELECT 
            DATE(timestamp) as date,
            COUNT(DISTINCT visitor_id) as unique_visitors,
            COUNT(*) as page_views
          FROM visitor_logs 
          WHERE timestamp >= ${startDate}
          GROUP BY DATE(timestamp)
          ORDER BY date DESC
          LIMIT 30
        `
      ]);
      
      const statsData = {
        period: {
          name: period,
          startDate: startDate.toISOString(),
          endDate: now.toISOString()
        },
        summary: {
          totalVisitors,
          uniqueVisitors,
          pageViews,
          avgPageViewsPerVisitor: uniqueVisitors > 0 ? Math.round(pageViews / uniqueVisitors) : 0
        },
        topPages: topPages.map(p => ({
          path: p.path,
          views: p._count.path
        })),
        deviceStats: deviceStats.map(d => ({
          device: d.deviceType,
          count: d._count.deviceType,
          percentage: Math.round((d._count.deviceType / totalVisitors) * 100)
        })),
        browserStats: browserStats.map(b => ({
          browser: b.browser,
          count: b._count.browser
        })),
        topCountries: countryStats.map(c => ({
          country: c.country,
          visitors: c._count.country
        })),
        trafficSources: referrerStats.map(r => ({
          source: r.referrerSource,
          visitors: r._count.referrerSource
        })),
        dailyTrends: dailyVisitors.map(day => ({
          date: day.date,
          uniqueVisitors: Number(day.unique_visitors),
          pageViews: Number(day.page_views)
        })),
        lastUpdated: new Date().toISOString()
      };
      
      await cache.set(cacheKey, statsData, CACHE_DURATIONS.ANALYTICS);
      
      res.json({
        success: true,
        data: statsData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching visitor analytics:', error);
      throw error;
    }
  })
);

// Helper function to calculate days difference
function getDaysDifference(startDate, endDate) {
  const timeDiff = endDate.getTime() - startDate.getTime();
  return Math.ceil(timeDiff / (1000 * 3600 * 24));
}

module.exports = router;