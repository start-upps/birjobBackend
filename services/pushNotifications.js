const admin = require('firebase-admin');
const apn = require('apn');
const logger = require('../utils/logger');

// Initialize Firebase Admin SDK for Android push notifications
let firebaseApp = null;
if (process.env.FIREBASE_PROJECT_ID && process.env.FIREBASE_PRIVATE_KEY) {
  try {
    const serviceAccount = {
      type: 'service_account',
      project_id: process.env.FIREBASE_PROJECT_ID,
      private_key_id: process.env.FIREBASE_PRIVATE_KEY_ID,
      private_key: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\n'),
      client_email: process.env.FIREBASE_CLIENT_EMAIL,
      client_id: process.env.FIREBASE_CLIENT_ID,
      auth_uri: 'https://accounts.google.com/o/oauth2/auth',
      token_uri: 'https://oauth2.googleapis.com/token',
      auth_provider_x509_cert_url: 'https://www.googleapis.com/oauth2/v1/certs',
      client_x509_cert_url: process.env.FIREBASE_CLIENT_CERT_URL
    };

    firebaseApp = admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      projectId: process.env.FIREBASE_PROJECT_ID
    });
    
    logger.info('✅ Firebase Admin SDK initialized for push notifications');
  } catch (error) {
    logger.error('❌ Failed to initialize Firebase Admin SDK:', error);
  }
}

// Initialize Apple Push Notification service for iOS
let apnProvider = null;
if (process.env.APPLE_TEAM_ID && process.env.APPLE_KEY_ID && process.env.APPLE_PRIVATE_KEY) {
  try {
    const options = {
      token: {
        key: process.env.APPLE_PRIVATE_KEY.replace(/\\n/g, '\n'),
        keyId: process.env.APPLE_KEY_ID,
        teamId: process.env.APPLE_TEAM_ID
      },
      production: process.env.NODE_ENV === 'production'
    };

    apnProvider = new apn.Provider(options);
    logger.info('✅ Apple Push Notification service initialized');
  } catch (error) {
    logger.error('❌ Failed to initialize Apple Push Notification service:', error);
  }
}

/**
 * Send push notification to a single device
 * @param {Object} options - Notification options
 * @param {string} options.deviceToken - Device token
 * @param {string} options.platform - 'ios' or 'android'
 * @param {string} options.title - Notification title
 * @param {string} options.body - Notification body
 * @param {Object} options.data - Custom data payload
 * @param {Object} options.sound - Sound configuration
 * @param {number} options.badge - Badge count (iOS only)
 * @returns {Promise<Object>} - Result object with success status
 */
async function sendPushNotification(options) {
  const {
    deviceToken,
    platform,
    title,
    body,
    data = {},
    sound = 'default',
    badge,
    priority = 'high',
    ttl = 3600 // Time to live in seconds
  } = options;

  if (!deviceToken || !platform || !title || !body) {
    throw new Error('Missing required parameters: deviceToken, platform, title, body');
  }

  try {
    let result = {};

    if (platform === 'ios') {
      result = await sendIOSNotification({
        deviceToken,
        title,
        body,
        data,
        sound,
        badge,
        priority,
        ttl
      });
    } else if (platform === 'android') {
      result = await sendAndroidNotification({
        deviceToken,
        title,
        body,
        data,
        priority,
        ttl
      });
    } else {
      throw new Error(`Unsupported platform: ${platform}`);
    }

    logger.context.notification('push_sent', deviceToken.substring(0, 10) + '...', result.success);
    
    return result;

  } catch (error) {
    logger.error('Error sending push notification:', {
      platform,
      error: error.message,
      deviceToken: deviceToken.substring(0, 10) + '...'
    });
    
    return {
      success: false,
      error: error.message,
      platform
    };
  }
}

/**
 * Send iOS push notification using APNs
 */
async function sendIOSNotification(options) {
  if (!apnProvider) {
    throw new Error('Apple Push Notification service not initialized');
  }

  const {
    deviceToken,
    title,
    body,
    data = {},
    sound = 'default',
    badge,
    priority = 'high',
    ttl = 3600
  } = options;

  try {
    const notification = new apn.Notification();
    
    // Basic notification properties
    notification.alert = {
      title,
      body
    };
    
    notification.sound = sound;
    notification.topic = process.env.APPLE_BUNDLE_ID || 'com.birjob.app';
    
    if (badge !== undefined) {
      notification.badge = badge;
    }
    
    // Custom data payload
    if (Object.keys(data).length > 0) {
      notification.payload = data;
    }
    
    // Priority and expiry
    notification.priority = priority === 'high' ? 10 : 5;
    notification.expiry = Math.floor(Date.now() / 1000) + ttl;
    
    // Send notification
    const result = await apnProvider.send(notification, deviceToken);
    
    if (result.sent && result.sent.length > 0) {
      return {
        success: true,
        platform: 'ios',
        messageId: result.sent[0].messageId || null,
        sent: result.sent.length,
        failed: result.failed.length
      };
    } else if (result.failed && result.failed.length > 0) {
      const failure = result.failed[0];
      throw new Error(`APNs error: ${failure.error || 'Unknown error'}`);
    } else {
      throw new Error('Unknown APNs response');
    }

  } catch (error) {
    logger.error('iOS push notification error:', error);
    throw error;
  }
}

/**
 * Send Android push notification using FCM
 */
async function sendAndroidNotification(options) {
  if (!firebaseApp) {
    throw new Error('Firebase Admin SDK not initialized');
  }

  const {
    deviceToken,
    title,
    body,
    data = {},
    priority = 'high',
    ttl = 3600
  } = options;

  try {
    const message = {
      token: deviceToken,
      notification: {
        title,
        body
      },
      data: {
        ...data,
        // Convert all data values to strings (FCM requirement)
        ...Object.keys(data).reduce((acc, key) => {
          acc[key] = String(data[key]);
          return acc;
        }, {})
      },
      android: {
        priority: priority === 'high' ? 'high' : 'normal',
        ttl: ttl * 1000, // Convert to milliseconds
        notification: {
          icon: 'ic_notification',
          color: '#007AFF',
          sound: 'default',
          channelId: 'job_alerts'
        }
      }
    };

    const response = await admin.messaging().send(message);
    
    return {
      success: true,
      platform: 'android',
      messageId: response,
      fcmResponse: response
    };

  } catch (error) {
    logger.error('Android push notification error:', error);
    
    // Handle specific FCM errors
    if (error.code === 'messaging/registration-token-not-registered') {
      return {
        success: false,
        error: 'Device token no longer valid',
        platform: 'android',
        shouldRemoveToken: true
      };
    } else if (error.code === 'messaging/invalid-registration-token') {
      return {
        success: false,
        error: 'Invalid device token format',
        platform: 'android',
        shouldRemoveToken: true
      };
    }
    
    throw error;
  }
}

/**
 * Send push notifications to multiple devices
 * @param {Array} notifications - Array of notification objects
 * @returns {Promise<Object>} - Bulk send results
 */
async function sendBulkNotifications(notifications) {
  if (!Array.isArray(notifications) || notifications.length === 0) {
    throw new Error('Notifications array is required and must not be empty');
  }

  const results = {
    total: notifications.length,
    successful: 0,
    failed: 0,
    errors: [],
    invalidTokens: []
  };

  logger.info(`Starting bulk notification send to ${notifications.length} devices`);

  // Process notifications in batches to avoid overwhelming the services
  const batchSize = 100;
  const batches = [];
  
  for (let i = 0; i < notifications.length; i += batchSize) {
    batches.push(notifications.slice(i, i + batchSize));
  }

  for (const batch of batches) {
    const batchPromises = batch.map(async (notification) => {
      try {
        const result = await sendPushNotification(notification);
        
        if (result.success) {
          results.successful++;
        } else {
          results.failed++;
          results.errors.push({
            deviceToken: notification.deviceToken.substring(0, 10) + '...',
            error: result.error,
            platform: notification.platform
          });
          
          if (result.shouldRemoveToken) {
            results.invalidTokens.push(notification.deviceToken);
          }
        }
        
        return result;
        
      } catch (error) {
        results.failed++;
        results.errors.push({
          deviceToken: notification.deviceToken.substring(0, 10) + '...',
          error: error.message,
          platform: notification.platform
        });
        
        return { success: false, error: error.message };
      }
    });

    // Wait for current batch to complete before processing next batch
    await Promise.all(batchPromises);
    
    // Small delay between batches to avoid rate limiting
    if (batches.indexOf(batch) < batches.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  logger.info(`Bulk notification send completed: ${results.successful} successful, ${results.failed} failed`);
  
  return results;
}

/**
 * Send job alert notifications to users based on their keywords
 * @param {Array} jobs - Array of job objects
 * @param {Array} users - Array of user objects with their keywords and device tokens
 * @returns {Promise<Object>} - Send results
 */
async function sendJobAlertNotifications(jobs, users) {
  if (!Array.isArray(jobs) || !Array.isArray(users)) {
    throw new Error('Jobs and users arrays are required');
  }

  const notifications = [];

  // Match jobs with user keywords and create notifications
  for (const user of users) {
    if (!user.deviceToken || !user.keywords || user.keywords.length === 0) {
      continue;
    }

    const matchingJobs = jobs.filter(job => {
      return user.keywords.some(keyword => {
        const keywordLower = keyword.toLowerCase();
        return job.title.toLowerCase().includes(keywordLower) ||
               job.company.toLowerCase().includes(keywordLower);
      });
    });

    if (matchingJobs.length > 0) {
      // Create notification for this user
      const job = matchingJobs[0]; // Send notification for the first matching job
      const matchedKeyword = user.keywords.find(keyword => {
        const keywordLower = keyword.toLowerCase();
        return job.title.toLowerCase().includes(keywordLower) ||
               job.company.toLowerCase().includes(keywordLower);
      });

      notifications.push({
        deviceToken: user.deviceToken,
        platform: user.platform || 'ios',
        title: '🚨 New Job Alert!',
        body: `${job.title} at ${job.company}`,
        data: {
          type: 'job_alert',
          jobId: String(job.id),
          jobTitle: job.title,
          company: job.company,
          matchedKeyword: matchedKeyword,
          totalMatches: String(matchingJobs.length)
        },
        badge: user.unreadNotifications || 1
      });
    }
  }

  if (notifications.length === 0) {
    return {
      total: 0,
      successful: 0,
      failed: 0,
      message: 'No matching jobs found for any users'
    };
  }

  // Send bulk notifications
  const results = await sendBulkNotifications(notifications);
  
  logger.info(`Job alert notifications sent: ${results.successful} successful out of ${results.total}`);
  
  return results;
}

/**
 * Test push notification functionality
 * @param {string} deviceToken - Device token to test
 * @param {string} platform - Platform (ios/android)
 * @returns {Promise<Object>} - Test result
 */
async function testPushNotification(deviceToken, platform) {
  return await sendPushNotification({
    deviceToken,
    platform,
    title: 'BirJob Test Notification',
    body: 'This is a test notification from BirJob API',
    data: {
      type: 'test',
      timestamp: new Date().toISOString()
    }
  });
}

/**
 * Get push notification service health status
 * @returns {Object} - Health status of notification services
 */
function getServiceHealth() {
  return {
    ios: {
      available: !!apnProvider,
      provider: apnProvider ? 'APNs' : 'Not configured',
      environment: process.env.NODE_ENV === 'production' ? 'production' : 'sandbox'
    },
    android: {
      available: !!firebaseApp,
      provider: firebaseApp ? 'FCM' : 'Not configured',
      projectId: process.env.FIREBASE_PROJECT_ID || 'Not configured'
    },
    timestamp: new Date().toISOString()
  };
}

module.exports = {
  sendPushNotification,
  sendBulkNotifications,
  sendJobAlertNotifications,
  testPushNotification,
  getServiceHealth
};