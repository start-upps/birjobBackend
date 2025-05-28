const logger = require('../utils/logger');

// Custom error classes
class AppError extends Error {
  constructor(message, statusCode = 500, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.name = this.constructor.name;
    
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, details = []) {
    super(message, 400);
    this.details = details;
    this.name = 'ValidationError';
  }
}

class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404);
    this.name = 'NotFoundError';
  }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized access') {
    super(message, 401);
    this.name = 'UnauthorizedError';
  }
}

class ForbiddenError extends AppError {
  constructor(message = 'Forbidden access') {
    super(message, 403);
    this.name = 'ForbiddenError';
  }
}

class ConflictError extends AppError {
  constructor(message = 'Resource conflict') {
    super(message, 409);
    this.name = 'ConflictError';
  }
}

class RateLimitError extends AppError {
  constructor(message = 'Too many requests') {
    super(message, 429);
    this.name = 'RateLimitError';
  }
}

// Error response formatter
const formatErrorResponse = (error, req) => {
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  const baseResponse = {
    success: false,
    error: {
      name: error.name,
      message: error.message,
      statusCode: error.statusCode || 500,
      timestamp: new Date().toISOString(),
      requestId: req.id || 'N/A'
    }
  };

  // Add additional details in development
  if (isDevelopment) {
    baseResponse.error.stack = error.stack;
    baseResponse.error.path = req.path;
    baseResponse.error.method = req.method;
  }

  // Add validation details if available
  if (error.details && error.details.length > 0) {
    baseResponse.error.details = error.details;
  }

  return baseResponse;
};

// Handle specific error types
const handlePrismaError = (error) => {
  switch (error.code) {
    case 'P2002':
      return new ConflictError('A record with this information already exists');
    case 'P2025':
      return new NotFoundError('Record');
    case 'P2003':
      return new ValidationError('Invalid foreign key constraint');
    case 'P2004':
      return new ValidationError('A constraint failed on the database');
    default:
      logger.error('Unhandled Prisma error:', { code: error.code, message: error.message });
      return new AppError('Database operation failed', 500);
  }
};

const handleValidationError = (error) => {
  if (error.details) {
    const details = error.details.map(detail => ({
      field: detail.path ? (Array.isArray(detail.path) ? detail.path.join('.') : detail.path) : 'unknown',
      message: detail.message,
      value: detail.context?.value || detail.value
    }));
    return new ValidationError('Validation failed', details);
  }
  return new ValidationError(error.message);
};

const handleJWTError = (error) => {
  switch (error.name) {
    case 'JsonWebTokenError':
      return new UnauthorizedError('Invalid token');
    case 'TokenExpiredError':
      return new UnauthorizedError('Token expired');
    case 'NotBeforeError':
      return new UnauthorizedError('Token not active');
    default:
      return new UnauthorizedError('Authentication failed');
  }
};

// Main error handler middleware
const errorHandler = (error, req, res, next) => {
  let processedError = error;

  // Log the error
  logger.errors.trackAPIError(error, req, res);

  // Handle specific error types
  if (error.code && error.code.startsWith('P')) {
    // Prisma error
    processedError = handlePrismaError(error);
  } else if (error.name === 'ValidationError' && error.details) {
    // Joi validation error
    processedError = handleValidationError(error);
  } else if (error.name && error.name.includes('JWT')) {
    // JWT error
    processedError = handleJWTError(error);
  } else if (error.name === 'CastError') {
    // MongoDB cast error (if using MongoDB)
    processedError = new ValidationError('Invalid data format');
  } else if (error.code === 'ECONNREFUSED') {
    // Database connection error
    processedError = new AppError('Service temporarily unavailable', 503);
  } else if (error.code === 'ENOTFOUND') {
    // Network error
    processedError = new AppError('External service unavailable', 503);
  } else if (error.type === 'entity.parse.failed') {
    // JSON parse error
    processedError = new ValidationError('Invalid JSON format');
  } else if (error.type === 'entity.too.large') {
    // Payload too large
    processedError = new ValidationError('Request payload too large');
  } else if (!processedError.isOperational) {
    // Programming error - don't expose details
    logger.error('Programming error:', error);
    processedError = new AppError('Internal server error', 500);
  }

  // Set default status code if not set
  if (!processedError.statusCode) {
    processedError.statusCode = 500;
  }

  // Format and send error response
  const errorResponse = formatErrorResponse(processedError, req);
  
  // Add retry information for temporary errors
  if (processedError.statusCode >= 500 && processedError.statusCode < 600) {
    errorResponse.error.retryAfter = '60'; // seconds
    res.set('Retry-After', '60');
  }

  res.status(processedError.statusCode).json(errorResponse);
};

// 404 handler for unmatched routes
const notFoundHandler = (req, res) => {
  const error = new NotFoundError(`Route ${req.method} ${req.originalUrl}`);
  const errorResponse = formatErrorResponse(error, req);
  
  logger.context.api(req.method, req.originalUrl, 404, 0);
  
  res.status(404).json(errorResponse);
};

// Async error wrapper
const asyncHandler = (fn) => {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// Request timeout handler
const timeoutHandler = (timeout = 30000) => {
  return (req, res, next) => {
    req.setTimeout(timeout, () => {
      const error = new AppError('Request timeout', 408);
      next(error);
    });
    next();
  };
};

// Rate limiting error handler
const rateLimitHandler = (req, res) => {
  const error = new RateLimitError('Too many requests, please try again later');
  const errorResponse = formatErrorResponse(error, req);
  
  logger.context.security('rate_limit_exceeded', 'medium', req.ip, {
    path: req.path,
    method: req.method,
    userAgent: req.get('User-Agent')
  });
  
  res.status(429).json(errorResponse);
};

// Health check for error handling system
const getErrorStats = () => {
  const stats = logger.manager.getStats();
  return {
    logFiles: stats,
    errorTypes: {
      operational: 'Handled gracefully',
      programming: 'Logged and masked',
      validation: 'Detailed feedback provided',
      database: 'Transformed to user-friendly messages'
    },
    responseFormat: 'Consistent JSON structure',
    securityFeatures: [
      'Stack traces hidden in production',
      'Sensitive data masking',
      'Rate limit tracking',
      'Security event logging'
    ]
  };
};

module.exports = {
  // Error classes
  AppError,
  ValidationError,
  NotFoundError,
  UnauthorizedError,
  ForbiddenError,
  ConflictError,
  RateLimitError,
  
  // Middleware
  errorHandler,
  notFoundHandler,
  asyncHandler,
  timeoutHandler,
  rateLimitHandler,
  
  // Utilities
  getErrorStats
};