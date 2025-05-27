const winston = require('winston');
const path = require('path');

// Custom log format
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
);

// Console format for development
const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({
    format: 'HH:mm:ss'
  }),
  winston.format.align(),
  winston.format.printf(info => {
    const { timestamp, level, message, ...args } = info;
    const ts = timestamp.slice(0, 19).replace('T', ' ');
    return `${timestamp} [${level}]: ${message} ${Object.keys(args).length ? JSON.stringify(args, null, 2) : ''}`;
  })
);

// Create logs directory if it doesn't exist
const fs = require('fs');
const logsDir = path.join(process.cwd(), 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Logger configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { service: 'birjob-mobile-backend' },
  transports: [
    // Error log file
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 10,
      handleExceptions: true,
      handleRejections: true
    }),
    
    // Combined log file
    new winston.transports.File({
      filename: path.join(logsDir, 'combined.log'),
      maxsize: 5242880, // 5MB
      maxFiles: 10
    }),
    
    // API access log
    new winston.transports.File({
      filename: path.join(logsDir, 'access.log'),
      level: 'http',
      maxsize: 5242880, // 5MB
      maxFiles: 5
    })
  ],
  exitOnError: false
});

// Console transport for development
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: consoleFormat,
    handleExceptions: true,
    handleRejections: true
  }));
}

// Create a stream object for Morgan
logger.stream = {
  write: (message) => {
    logger.http(message.trim());
  }
};

// Custom logging methods for different contexts
const contextLogger = {
  // API request logging
  api: (method, path, statusCode, responseTime, userId = null) => {
    logger.info('API Request', {
      method,
      path,
      statusCode,
      responseTime: `${responseTime}ms`,
      userId,
      timestamp: new Date().toISOString()
    });
  },

  // Database operation logging
  db: (operation, table, duration, recordCount = null) => {
    logger.debug('Database Operation', {
      operation,
      table,
      duration: `${duration}ms`,
      recordCount,
      timestamp: new Date().toISOString()
    });
  },

  // Cache operation logging
  cache: (operation, key, hit = null, ttl = null) => {
    logger.debug('Cache Operation', {
      operation,
      key,
      hit,
      ttl: ttl ? `${ttl}s` : null,
      timestamp: new Date().toISOString()
    });
  },

  // Authentication logging
  auth: (action, email, success, ip, userAgent) => {
    logger.info('Authentication', {
      action,
      email,
      success,
      ip,
      userAgent: userAgent?.substring(0, 100),
      timestamp: new Date().toISOString()
    });
  },

  // Push notification logging
  notification: (type, recipient, success, error = null) => {
    logger.info('Notification', {
      type,
      recipient,
      success,
      error: error?.message,
      timestamp: new Date().toISOString()
    });
  },

  // Job scraping logging
  scraper: (source, jobsFound, errors = 0, duration) => {
    logger.info('Scraper Operation', {
      source,
      jobsFound,
      errors,
      duration: `${duration}ms`,
      timestamp: new Date().toISOString()
    });
  },

  // Analytics logging
  analytics: (event, data, userId = null) => {
    logger.info('Analytics Event', {
      event,
      data,
      userId,
      timestamp: new Date().toISOString()
    });
  },

  // Security logging
  security: (event, severity, ip, details) => {
    const logLevel = severity === 'high' ? 'error' : 'warn';
    logger[logLevel]('Security Event', {
      event,
      severity,
      ip,
      details,
      timestamp: new Date().toISOString()
    });
  }
};

// Performance monitoring
const performanceLogger = {
  startTimer: (label) => {
    const start = process.hrtime.bigint();
    return {
      end: () => {
        const end = process.hrtime.bigint();
        const duration = Number(end - start) / 1000000; // Convert to milliseconds
        logger.debug(`Performance: ${label}`, { duration: `${duration.toFixed(2)}ms` });
        return duration;
      }
    };
  },

  logMemoryUsage: () => {
    const memUsage = process.memoryUsage();
    logger.debug('Memory Usage', {
      rss: `${Math.round(memUsage.rss / 1024 / 1024)} MB`,
      heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)} MB`,
      heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)} MB`,
      external: `${Math.round(memUsage.external / 1024 / 1024)} MB`,
      timestamp: new Date().toISOString()
    });
  }
};

// Error tracking
const errorTracker = {
  trackError: (error, context = {}) => {
    logger.error('Application Error', {
      name: error.name,
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString()
    });
  },

  trackAPIError: (error, req, res) => {
    logger.error('API Error', {
      name: error.name,
      message: error.message,
      stack: error.stack,
      method: req.method,
      path: req.path,
      params: req.params,
      query: req.query,
      body: req.body,
      statusCode: res.statusCode,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      timestamp: new Date().toISOString()
    });
  }
};

// Log rotation and cleanup
const logManager = {
  // Clean up old log files
  cleanup: () => {
    const fs = require('fs');
    const path = require('path');
    
    try {
      const files = fs.readdirSync(logsDir);
      const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
      
      files.forEach(file => {
        const filePath = path.join(logsDir, file);
        const stats = fs.statSync(filePath);
        
        if (stats.birthtime.getTime() < thirtyDaysAgo) {
          fs.unlinkSync(filePath);
          logger.info(`Cleaned up old log file: ${file}`);
        }
      });
    } catch (error) {
      logger.error('Error cleaning up log files:', error);
    }
  },

  // Get log statistics
  getStats: () => {
    const fs = require('fs');
    try {
      const files = fs.readdirSync(logsDir);
      const stats = {};
      
      files.forEach(file => {
        const filePath = path.join(logsDir, file);
        const fileStats = fs.statSync(filePath);
        stats[file] = {
          size: `${Math.round(fileStats.size / 1024)} KB`,
          created: fileStats.birthtime,
          modified: fileStats.mtime
        };
      });
      
      return stats;
    } catch (error) {
      logger.error('Error getting log stats:', error);
      return {};
    }
  }
};

// Add all custom methods to logger
Object.assign(logger, {
  context: contextLogger,
  performance: performanceLogger,
  errors: errorTracker,
  manager: logManager
});

module.exports = logger;