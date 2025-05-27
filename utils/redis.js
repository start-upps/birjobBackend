const { createClient } = require('redis');
const logger = require('./logger');

// Redis client configuration
const redis = createClient({
  url: process.env.UPSTASH_REDIS_REST_URL || process.env.REDIS_URL,
  password: process.env.UPSTASH_REDIS_REST_TOKEN,
  socket: {
    connectTimeout: 10000,
    lazyConnect: true,
  },
  retry_unfulfilled_commands: true,
  retry_delay: (attempt) => Math.min(attempt * 50, 500),
});

// Cache duration constants (in seconds)
const CACHE_DURATIONS = {
  JOBS_LIST: 5 * 60,        // 5 minutes
  JOBS_SEARCH: 3 * 60,      // 3 minutes
  JOBS_METADATA: 15 * 60,   // 15 minutes
  USER_DATA: 30 * 60,       // 30 minutes
  ANALYTICS: 60 * 60,       // 1 hour
  SOURCES: 24 * 60 * 60,    // 24 hours
  COMPANIES: 12 * 60 * 60,  // 12 hours
  TRENDS: 6 * 60 * 60,      // 6 hours
};

// Redis event handlers
redis.on('connect', () => {
  logger.info('✅ Redis connecting...');
});

redis.on('ready', () => {
  logger.info('✅ Redis connected and ready');
});

redis.on('error', (error) => {
  logger.error('❌ Redis error:', error);
});

redis.on('end', () => {
  logger.info('Redis connection ended');
});

redis.on('reconnecting', () => {
  logger.info('Redis reconnecting...');
});

// Connect to Redis
const connectRedis = async () => {
  try {
    if (!redis.isOpen) {
      await redis.connect();
    }
    logger.info('Redis connection established');
    return true;
  } catch (error) {
    logger.error('Failed to connect to Redis:', error);
    throw error;
  }
};

// Redis health check
const getHealthStatus = async () => {
  try {
    const start = Date.now();
    const pong = await redis.ping();
    const responseTime = Date.now() - start;
    
    return {
      status: pong === 'PONG' ? 'healthy' : 'unhealthy',
      responseTime: `${responseTime}ms`,
      connection: redis.isReady ? 'active' : 'inactive'
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error.message,
      connection: 'failed'
    };
  }
};

// Cache operations
const cache = {
  // Get data from cache
  get: async (key) => {
    try {
      const data = await redis.get(key);
      if (data) {
        logger.debug(`Cache HIT: ${key}`);
        return JSON.parse(data);
      }
      logger.debug(`Cache MISS: ${key}`);
      return null;
    } catch (error) {
      logger.error(`Cache GET error for key ${key}:`, error);
      return null;
    }
  },

  // Set data in cache
  set: async (key, data, ttl = CACHE_DURATIONS.JOBS_LIST) => {
    try {
      await redis.setEx(key, ttl, JSON.stringify(data));
      logger.debug(`Cache SET: ${key} (TTL: ${ttl}s)`);
    } catch (error) {
      logger.error(`Cache SET error for key ${key}:`, error);
    }
  },

  // Delete from cache
  del: async (key) => {
    try {
      await redis.del(key);
      logger.debug(`Cache DELETE: ${key}`);
    } catch (error) {
      logger.error(`Cache DELETE error for key ${key}:`, error);
    }
  },

  // Delete multiple keys
  delPattern: async (pattern) => {
    try {
      const keys = await redis.keys(pattern);
      if (keys.length > 0) {
        await redis.del(keys);
        logger.debug(`Cache DELETE PATTERN: ${pattern} (${keys.length} keys)`);
      }
    } catch (error) {
      logger.error(`Cache DELETE PATTERN error for ${pattern}:`, error);
    }
  },

  // Check if key exists
  exists: async (key) => {
    try {
      return await redis.exists(key);
    } catch (error) {
      logger.error(`Cache EXISTS error for key ${key}:`, error);
      return false;
    }
  },

  // Get TTL for a key
  ttl: async (key) => {
    try {
      return await redis.ttl(key);
    } catch (error) {
      logger.error(`Cache TTL error for key ${key}:`, error);
      return -1;
    }
  },

  // Increment counter
  incr: async (key, ttl = 3600) => {
    try {
      const multi = redis.multi();
      multi.incr(key);
      multi.expire(key, ttl);
      const results = await multi.exec();
      return results[0];
    } catch (error) {
      logger.error(`Cache INCR error for key ${key}:`, error);
      return 0;
    }
  }
};

// Cache key generators
const keys = {
  jobs: (params = {}) => {
    const { search, source, company, page = 1, limit = 20 } = params;
    return `jobs:${search || 'all'}:${source || 'all'}:${company || 'all'}:${page}:${limit}`;
  },
  
  jobsMetadata: () => 'jobs:metadata',
  
  sources: () => 'jobs:sources',
  
  companies: () => 'jobs:companies',
  
  trends: () => 'jobs:trends',
  
  userKeywords: (email) => `user:${email}:keywords`,
  
  userSources: (email) => `user:${email}:sources`,
  
  userNotifications: (email) => `user:${email}:notifications`,
  
  analytics: (type, period) => `analytics:${type}:${period}`,
  
  rateLimit: (ip, endpoint) => `ratelimit:${ip}:${endpoint}`,
  
  session: (sessionId) => `session:${sessionId}`,
  
  deviceToken: (userId) => `device:${userId}:token`
};

// Cache warming functions
const warmCache = {
  // Warm frequently accessed data
  jobs: async () => {
    logger.info('Warming jobs cache...');
    try {
      // This would be called from your job routes
      // when data is fetched from database
      logger.info('Jobs cache warmed');
    } catch (error) {
      logger.error('Error warming jobs cache:', error);
    }
  },

  metadata: async () => {
    logger.info('Warming metadata cache...');
    try {
      // Warm sources, companies, etc.
      logger.info('Metadata cache warmed');
    } catch (error) {
      logger.error('Error warming metadata cache:', error);
    }
  }
};

// Cache statistics
const getStats = async () => {
  try {
    const info = await redis.info();
    const dbSize = await redis.dbSize();
    
    return {
      connected: redis.isReady,
      dbSize,
      info: info.split('\r\n').reduce((acc, line) => {
        if (line.includes(':')) {
          const [key, value] = line.split(':');
          acc[key] = value;
        }
        return acc;
      }, {})
    };
  } catch (error) {
    logger.error('Error getting Redis stats:', error);
    return { error: error.message };
  }
};

// Graceful disconnect
const disconnect = async () => {
  try {
    if (redis.isOpen) {
      await redis.quit();
      logger.info('Redis disconnected gracefully');
    }
  } catch (error) {
    logger.error('Error disconnecting from Redis:', error);
    throw error;
  }
};

// Initialize Redis connection
connectRedis().catch(error => {
  logger.error('Failed to initialize Redis:', error);
});

module.exports = {
  redis,
  cache,
  keys,
  warmCache,
  CACHE_DURATIONS,
  getHealthStatus,
  getStats,
  disconnect
};