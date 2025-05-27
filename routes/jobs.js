const express = require('express');
const { body, query, validationResult } = require('express-validator');
const { prisma } = require('../utils/database');
const { cache, keys, CACHE_DURATIONS } = require('../utils/redis');
const logger = require('../utils/logger');
const { asyncHandler, ValidationError, NotFoundError } = require('../middleware/errorHandler');

const router = express.Router();

// Validation middleware
const validatePagination = [
  query('page')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Page must be a positive integer'),
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100')
];

const validateJobSearch = [
  query('search')
    .optional()
    .trim()
    .isLength({ min: 2, max: 100 })
    .withMessage('Search term must be between 2 and 100 characters'),
  query('source')
    .optional()
    .trim()
    .isLength({ max: 50 })
    .withMessage('Source must not exceed 50 characters'),
  query('company')
    .optional()
    .trim()
    .isLength({ max: 100 })
    .withMessage('Company must not exceed 100 characters')
];

// Helper function to check validation results
const checkValidation = (req) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new ValidationError('Invalid request parameters', errors.array());
  }
};

// Helper function to build job search query
const buildJobQuery = (search, source, company) => {
  const where = {};
  
  if (search) {
    where.OR = [
      { title: { contains: search, mode: 'insensitive' } },
      { company: { contains: search, mode: 'insensitive' } }
    ];
  }
  
  if (source) {
    where.source = { contains: source, mode: 'insensitive' };
  }
  
  if (company) {
    where.company = { contains: company, mode: 'insensitive' };
  }
  
  return where;
};

// GET /api/v1/jobs - Get job listings with search and pagination
router.get('/', 
  [...validatePagination, ...validateJobSearch],
  asyncHandler(async (req, res) => {
    const timer = logger.performance.startTimer('jobs_list');
    
    checkValidation(req);
    
    const {
      search,
      source,
      company,
      page = 1,
      limit = 20
    } = req.query;
    
    const pageNum = parseInt(page);
    const limitNum = parseInt(limit);
    const offset = (pageNum - 1) * limitNum;
    
    // Generate cache key
    const cacheKey = keys.jobs({ search, source, company, page: pageNum, limit: limitNum });
    
    // Try to get from cache
    let cachedData = await cache.get(cacheKey);
    if (cachedData) {
      logger.context.cache('GET', cacheKey, true);
      return res.json({
        success: true,
        data: cachedData,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    // Build query
    const where = buildJobQuery(search, source, company);
    
    try {
      // Get jobs and total count in parallel
      const [jobs, totalJobs] = await Promise.all([
        prisma.jobs_jobpost.findMany({
          where,
          orderBy: { created_at: 'desc' },
          skip: offset,
          take: limitNum,
          select: {
            id: true,
            title: true,
            company: true,
            apply_link: true,
            source: true,
            created_at: true
          }
        }),
        prisma.jobs_jobpost.count({ where })
      ]);
      
      // Calculate pagination metadata
      const totalPages = Math.ceil(totalJobs / limitNum);
      const hasNextPage = pageNum < totalPages;
      const hasPreviousPage = pageNum > 1;
      
      // Get metadata for mobile app
      const [sources, companies, latestJob] = await Promise.all([
        prisma.jobs_jobpost.groupBy({
          by: ['source'],
          where: { source: { not: null } },
          _count: { source: true },
          orderBy: { _count: { source: 'desc' } }
        }),
        prisma.jobs_jobpost.groupBy({
          by: ['company'],
          _count: { company: true },
          orderBy: { _count: { company: 'desc' } },
          take: 50 // Top 50 companies
        }),
        prisma.jobs_jobpost.findFirst({
          orderBy: { created_at: 'desc' },
          select: { created_at: true }
        })
      ]);
      
      const responseData = {
        jobs: jobs.map(job => ({
          id: job.id,
          title: job.title,
          company: job.company,
          applyLink: job.apply_link,
          source: job.source,
          postedAt: job.created_at,
          // Add relative time for mobile
          postedRelative: getRelativeTime(job.created_at)
        })),
        metadata: {
          totalJobs,
          currentPage: pageNum,
          totalPages,
          hasNextPage,
          hasPreviousPage,
          itemsPerPage: limitNum,
          resultsFrom: offset + 1,
          resultsTo: Math.min(offset + limitNum, totalJobs)
        },
        sources: sources.map(s => ({
          name: s.source,
          count: s._count.source
        })),
        topCompanies: companies.map(c => ({
          name: c.company,
          count: c._count.company
        })),
        lastUpdated: latestJob?.created_at || null,
        searchQuery: {
          search: search || null,
          source: source || null,
          company: company || null
        }
      };
      
      // Cache the response
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.JOBS_LIST);
      
      const duration = timer.end();
      logger.context.api(req.method, req.path, 200, duration);
      logger.context.db('SELECT', 'jobs_jobpost', duration, jobs.length);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching jobs:', error);
      throw error;
    }
  })
);

// GET /api/v1/jobs/:id - Get specific job details
router.get('/:id',
  asyncHandler(async (req, res) => {
    const timer = logger.performance.startTimer('job_detail');
    const jobId = parseInt(req.params.id);
    
    if (isNaN(jobId)) {
      throw new ValidationError('Invalid job ID');
    }
    
    const cacheKey = `job:${jobId}`;
    
    // Try cache first
    let cachedJob = await cache.get(cacheKey);
    if (cachedJob) {
      return res.json({
        success: true,
        data: cachedJob,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const job = await prisma.jobs_jobpost.findUnique({
        where: { id: jobId },
        select: {
          id: true,
          title: true,
          company: true,
          apply_link: true,
          source: true,
          created_at: true
        }
      });
      
      if (!job) {
        throw new NotFoundError('Job');
      }
      
      // Get similar jobs from same company
      const similarJobs = await prisma.jobs_jobpost.findMany({
        where: {
          company: job.company,
          id: { not: jobId }
        },
        take: 5,
        orderBy: { created_at: 'desc' },
        select: {
          id: true,
          title: true,
          created_at: true
        }
      });
      
      const responseData = {
        job: {
          id: job.id,
          title: job.title,
          company: job.company,
          applyLink: job.apply_link,
          source: job.source,
          postedAt: job.created_at,
          postedRelative: getRelativeTime(job.created_at)
        },
        similarJobs: similarJobs.map(j => ({
          id: j.id,
          title: j.title,
          postedAt: j.created_at,
          postedRelative: getRelativeTime(j.created_at)
        })),
        company: {
          name: job.company,
          totalJobs: similarJobs.length + 1
        }
      };
      
      // Cache for 15 minutes
      await cache.set(cacheKey, responseData, 15 * 60);
      
      const duration = timer.end();
      logger.context.api(req.method, req.path, 200, duration);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error(`Error fetching job ${jobId}:`, error);
      throw error;
    }
  })
);

// GET /api/v1/jobs/sources - Get all available job sources
router.get('/meta/sources',
  asyncHandler(async (req, res) => {
    const cacheKey = keys.sources();
    
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
      const sources = await prisma.jobs_jobpost.groupBy({
        by: ['source'],
        where: { source: { not: null } },
        _count: { source: true },
        orderBy: { _count: { source: 'desc' } }
      });
      
      const responseData = {
        sources: sources.map(s => ({
          name: s.source,
          count: s._count.source,
          percentage: 0 // Will be calculated below
        })),
        totalSources: sources.length,
        lastUpdated: new Date().toISOString()
      };
      
      // Calculate percentages
      const totalJobs = responseData.sources.reduce((sum, s) => sum + s.count, 0);
      responseData.sources.forEach(source => {
        source.percentage = Math.round((source.count / totalJobs) * 100);
      });
      
      responseData.totalJobs = totalJobs;
      
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.SOURCES);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching sources:', error);
      throw error;
    }
  })
);

// GET /api/v1/jobs/companies - Get all companies
router.get('/meta/companies',
  asyncHandler(async (req, res) => {
    const cacheKey = keys.companies();
    
    let cachedCompanies = await cache.get(cacheKey);
    if (cachedCompanies) {
      return res.json({
        success: true,
        data: cachedCompanies,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      const companies = await prisma.jobs_jobpost.groupBy({
        by: ['company'],
        _count: { company: true },
        orderBy: { _count: { company: 'desc' } },
        take: 100 // Top 100 companies
      });
      
      const responseData = {
        companies: companies.map(c => ({
          name: c.company,
          jobCount: c._count.company
        })),
        totalCompanies: companies.length,
        lastUpdated: new Date().toISOString()
      };
      
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.COMPANIES);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching companies:', error);
      throw error;
    }
  })
);

// GET /api/v1/jobs/trends - Get job market trends
router.get('/meta/trends',
  asyncHandler(async (req, res) => {
    const cacheKey = keys.trends();
    
    let cachedTrends = await cache.get(cacheKey);
    if (cachedTrends) {
      return res.json({
        success: true,
        data: cachedTrends,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }
    
    try {
      // Get trends for the last 30 days
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      
      const [
        dailyTrends,
        sourceBreakdown,
        topCompanies,
        totalStats
      ] = await Promise.all([
        // Daily job posting trends
        prisma.$queryRaw`
          SELECT 
            DATE(created_at) as date,
            COUNT(*) as job_count
          FROM jobs_jobpost 
          WHERE created_at >= ${thirtyDaysAgo}
          GROUP BY DATE(created_at)
          ORDER BY date DESC
          LIMIT 30
        `,
        
        // Source breakdown
        prisma.jobs_jobpost.groupBy({
          by: ['source'],
          where: {
            created_at: { gte: thirtyDaysAgo },
            source: { not: null }
          },
          _count: { source: true },
          orderBy: { _count: { source: 'desc' } }
        }),
        
        // Top hiring companies
        prisma.jobs_jobpost.groupBy({
          by: ['company'],
          where: { created_at: { gte: thirtyDaysAgo } },
          _count: { company: true },
          orderBy: { _count: { company: 'desc' } },
          take: 20
        }),
        
        // Total statistics
        prisma.jobs_jobpost.aggregate({
          _count: { id: true },
          where: { created_at: { gte: thirtyDaysAgo } }
        })
      ]);
      
      const responseData = {
        period: {
          days: 30,
          from: thirtyDaysAgo.toISOString(),
          to: new Date().toISOString()
        },
        summary: {
          totalJobs: totalStats._count.id,
          averagePerDay: Math.round(totalStats._count.id / 30),
          topSource: sourceBreakdown[0]?.source || 'N/A',
          topCompany: topCompanies[0]?.company || 'N/A'
        },
        dailyTrends: dailyTrends.map(day => ({
          date: day.date,
          jobCount: Number(day.job_count)
        })),
        sourceBreakdown: sourceBreakdown.map(s => ({
          source: s.source,
          count: s._count.source,
          percentage: Math.round((s._count.source / totalStats._count.id) * 100)
        })),
        topCompanies: topCompanies.map(c => ({
          company: c.company,
          jobCount: c._count.company
        })),
        lastUpdated: new Date().toISOString()
      };
      
      await cache.set(cacheKey, responseData, CACHE_DURATIONS.TRENDS);
      
      res.json({
        success: true,
        data: responseData,
        cached: false,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      logger.error('Error fetching trends:', error);
      throw error;
    }
  })
);

// Helper function to calculate relative time
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

module.exports = router;