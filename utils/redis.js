const logger = require('./logger');

// Redis client configuration
let redis = null;
let isRedisAvailable = false;

// Try to configure Redis if available
if (process.env.REDIS_URL && process.env.REDIS_URL.startsWith('redis')) {
  try {
    const { createClient } = require('redis');
    
    redis = createClient({
      url: process.env.REDIS_URL,
      socket: {
        connectTimeout: 10000,
        lazyConnect: true,
      },
      retry_unfulfilled_commands: true,
      retry_delay: (attempt) => Math.min(attempt * 50, 500),
    });

    redis.on('error', (error) => {
      logger.error('❌ Redis error:', error.message);
      isRedisAvailable = false;
    });

    redis.on('connect', () => {
      logger.info('✅ Redis connecting...');
    });

    redis.on('ready', () => {
      logger.info('✅ Redis connected and ready');
      isRedisAvailable = true;
    });

    redis.on('end', () => {
      logger.info('Redis connection ended');
      isRedisAvailable = false;
    });

    logger.info('Using standard Redis configuration');
  } catch (error) {
    logger.error('Failed to create Redis client:', error.message);
    redis = null;
  }
} else {
  logger.warn('⚠️ No Redis configuration found - caching will be disabled');
  logger.info('To enable Redis, set REDIS_URL (e.g., redis://localhost:6379)');
}

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

// Connect to Redis
const connectRedis = async () => {
  if (!redis) {
    logger.warn('Redis not configured - skipping connection');
    return false;
  }

  try {
    if (!redis.isOpen) {
      await redis.connect();
    }
    logger.info('Redis connection established');
    isRedisAvailable = true;
    return true;
  } catch (error) {
    logger.error('Failed to connect to Redis:', error.message);
    isRedisAvailable = false;
    return false;
  }
};

// Redis health check
const getHealthStatus = async () => {
  if (!redis || !isRedisAvailable) {
    return {
      status: 'disabled',
      message: 'Redis not configured or unavailable',
      connection: 'not_configured'
    };
  }

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

// Cache operations with fallback when Redis is not available
const cache = {
  // Get data from cache
  get: async (key) => {
    if (!redis || !isRedisAvailable) {
      logger.debug(`Cache SKIP (no Redis): ${key}`);
      return null;
    }

    try {
      const data = await redis.get(key);
      if (data) {
        logger.debug(`Cache HIT: ${key}`);
        return JSON.parse(data);
      }
      logger.debug(`Cache MISS: ${key}`);
      return null;
    } catch (error) {
      logger.error(`Cache GET error for key ${key}:`, error.message);
      return null;
    }
  },

  // Set data in cache
  set: async (key, data, ttl = CACHE_DURATIONS.JOBS_LIST) => {
    if (!redis || !isRedisAvailable) {
      logger.debug(`Cache SKIP (no Redis): ${key}`);
      return;
    }

    try {
      await redis.setEx(key, ttl, JSON.stringify(data));
      logger.debug(`Cache SET: ${key} (TTL: ${ttl}s)`);
    } catch (error) {
      logger.error(`Cache SET error for key ${key}:`, error.message);
    }
  },

  // Delete from cache
  del: async (key) => {
    if (!redis || !isRedisAvailable) {
      return;
    }

    try {
      await redis.del(key);
      logger.debug(`Cache DELETE: ${key}`);
    } catch (error) {
      logger.error(`Cache DELETE error for key ${key}:`, error.message);
    }
  },

  // Delete multiple keys
  delPattern: async (pattern) => {
    if (!redis || !isRedisAvailable) {
      return;
    }

    try {
      const keys = await redis.keys(pattern);
      if (keys.length > 0) {
        await redis.del(keys);
        logger.debug(`Cache DELETE PATTERN: ${pattern} (${keys.length} keys)`);
      }
    } catch (error) {
      logger.error(`Cache DELETE PATTERN error for ${pattern}:`, error.message);
    }
  },

  // Check if key exists
  exists: async (key) => {
    if (!redis || !isRedisAvailable) {
      return false;
    }

    try {
      return await redis.exists(key);
    } catch (error) {
      logger.error(`Cache EXISTS error for key ${key}:`, error.message);
      return false;
    }
  },

  // Get TTL for a key
  ttl: async (key) => {
    if (!redis || !isRedisAvailable) {
      return -1;
    }

    try {
      return await redis.ttl(key);
    } catch (error) {
      logger.error(`Cache TTL error for key ${key}:`, error.message);
      return -1;
    }
  },

  // Increment counter
  incr: async (key, ttl = 3600) => {
    if (!redis || !isRedisAvailable) {
      return 0;
    }

    try {
      const multi = redis.multi();
      multi.incr(key);
      multi.expire(key, ttl);
      const results = await multi.exec();
      return results[0];
    } catch (error) {
      logger.error(`Cache INCR error for key ${key}:`, error.message);
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
  
  sources: () => 'jobs:sources',
  companies: () => 'jobs:companies',
  trends: () => 'jobs:trends',
  userKeywords: (email) => `user:${email}:keywords`,
  userSources: (email) => `user:${email}:sources`,
  userNotifications: (email) => `user:${email}:notifications`,
  analytics: (type, period) => `analytics:${type}:${period}`,
  deviceToken: (userId) => `device:${userId}:token`
};

// Get cache statistics
const getStats = async () => {
  if (!redis || !isRedisAvailable) {
    return { 
      connected: false, 
      status: 'Redis not configured or unavailable' 
    };
  }

  try {
    const ping = await redis.ping();
    return {
      connected: ping === 'PONG',
      status: 'active'
    };
  } catch (error) {
    logger.error('Error getting Redis stats:', error.message);
    return { error: error.message };
  }
};

// Graceful disconnect
const disconnect = async () => {
  if (!redis) return;
  
  try {
    if (redis.isOpen) {
      await redis.quit();
      logger.info('Redis disconnected gracefully');
    }
  } catch (error) {
    logger.error('Error disconnecting from Redis:', error.message);
  }
};

// Initialize Redis connection (optional)
if (redis) {
  connectRedis().catch(error => {
    logger.warn('Redis connection failed, continuing without cache:', error.message);
  });
}

module.exports = {
  redis,
  cache,
  keys,
  CACHE_DURATIONS,
  getHealthStatus,
  getStats,
  disconnect,
  isRedisAvailable: () => isRedisAvailable
};