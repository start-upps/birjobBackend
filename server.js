require('dotenv').config();
require('express-async-errors');

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

// Import utilities and middleware
const logger = require('./utils/logger');
const errorHandler = require('./middleware/errorHandler');
const { prisma } = require('./utils/database');
const redis = require('./utils/redis');

// Import routes
const jobRoutes = require('./routes/jobs');
const userRoutes = require('./routes/users');
const notificationRoutes = require('./routes/notifications');
const analyticsRoutes = require('./routes/analytics');
const mobileRoutes = require('./routes/mobile');
const healthRoutes = require('./routes/health');

const app = express();
const PORT = process.env.PORT || 3000;

// Trust proxy for accurate IP addresses
app.set('trust proxy', 1);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

// CORS configuration
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://birjob.az', 'https://www.birjob.az'] 
    : ['http://localhost:3000', 'http://localhost:3001'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-Device-ID']
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // Limit each IP to 1000 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: 15 * 60
  },
  standardHeaders: true,
  legacyHeaders: false,
});

const strictLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Stricter limit for sensitive endpoints
  message: {
    error: 'Rate limit exceeded for this endpoint.',
    retryAfter: 15 * 60
  }
});

app.use('/api/', limiter);

// Middleware
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
if (process.env.NODE_ENV !== 'production') {
  app.use(morgan('dev'));
} else {
  app.use(morgan('combined', {
    stream: { write: message => logger.info(message.trim()) }
  }));
}

// API versioning
const API_VERSION = '/api/v1';

// Health check (no rate limiting)
app.use('/api/health', healthRoutes);

// API routes
app.use(`${API_VERSION}/jobs`, jobRoutes);
app.use(`${API_VERSION}/users`, userRoutes);
app.use(`${API_VERSION}/notifications`, strictLimiter, notificationRoutes);
app.use(`${API_VERSION}/analytics`, analyticsRoutes);
app.use(`${API_VERSION}/mobile`, mobileRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'BirJob Mobile Backend API',
    version: '1.0.0',
    status: 'active',
    timestamp: new Date().toISOString(),
    endpoints: {
      health: '/api/health',
      jobs: `${API_VERSION}/jobs`,
      users: `${API_VERSION}/users`,
      notifications: `${API_VERSION}/notifications`,
      analytics: `${API_VERSION}/analytics`,
      mobile: `${API_VERSION}/mobile`
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    message: `Route ${req.method} ${req.originalUrl} not found`,
    availableEndpoints: [
      'GET /api/health',
      `GET ${API_VERSION}/jobs`,
      `GET ${API_VERSION}/users`,
      `GET ${API_VERSION}/notifications`,
      `POST ${API_VERSION}/analytics`,
      `GET ${API_VERSION}/mobile`
    ]
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Graceful shutdown
const gracefulShutdown = async () => {
  logger.info('Starting graceful shutdown...');
  
  try {
    // Stop cron jobs first
    stopCronJobs();
    
    await prisma.$disconnect();
    logger.info('Database disconnected');
    
    if (redis.isReady) {
      await redis.quit();
      logger.info('Redis disconnected');
    }
    
    logger.info('Graceful shutdown completed');
    process.exit(0);
  } catch (error) {
    logger.error('Error during shutdown:', error);
    process.exit(1);
  }
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Import cron jobs
const { initializeCronJobs, stopCronJobs, startupTasks } = require('./utils/cronJobs');

// Start server
const startServer = async () => {
  try {
    // Test database connection
    await prisma.$connect();
    logger.info('Database connected successfully');
    
    // Test Redis connection
    await redis.ping();
    logger.info('Redis connected successfully');
    
    // Run startup tasks
    await startupTasks();
    
    // Initialize cron jobs
    initializeCronJobs();
    
    app.listen(PORT, () => {
      logger.info(`🚀 BirJob Mobile Backend running on port ${PORT}`);
      logger.info(`📱 API Base URL: http://localhost:${PORT}${API_VERSION}`);
      logger.info(`🔍 Health Check: http://localhost:${PORT}/api/health`);
      logger.info(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`🕐 Timezone: ${process.env.TIMEZONE || 'Asia/Baku'}`);
    });
    
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Handle unhandled promise rejections
process.on('unhandledRejection', (err) => {
  logger.error('Unhandled Promise Rejection:', err);
  gracefulShutdown();
});

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  logger.error('Uncaught Exception:', err);
  gracefulShutdown();
});

startServer();

module.exports = app;