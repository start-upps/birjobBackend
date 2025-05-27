const nodemailer = require('nodemailer');
const logger = require('../utils/logger');

// Email service configuration
const EMAIL_CONFIG = {
  service: process.env.EMAIL_SERVICE || 'gmail',
  host: process.env.EMAIL_HOST || 'smtp.gmail.com',
  port: parseInt(process.env.EMAIL_PORT) || 587,
  secure: process.env.EMAIL_SECURE === 'true',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASSWORD
  }
};

// Create transporter
let transporter = null;

if (EMAIL_CONFIG.auth.user && EMAIL_CONFIG.auth.pass) {
  try {
    transporter = nodemailer.createTransporter(EMAIL_CONFIG);
    logger.info('✅ Email service initialized');
  } catch (error) {
    logger.error('❌ Failed to initialize email service:', error);
  }
} else {
  logger.warn('⚠️ Email service not configured - missing credentials');
}

/**
 * Send email notification
 * @param {Object} options - Email options
 * @param {string} options.to - Recipient email
 * @param {string} options.subject - Email subject
 * @param {string} options.body - Email body (text)
 * @param {string} options.html - Email body (HTML)
 * @param {Object} options.data - Additional data
 * @returns {Promise<Object>} - Send result
 */
async function sendEmailNotification(options) {
  if (!transporter) {
    logger.warn('Email service not available - notification not sent');
    return {
      success: false,
      error: 'Email service not configured',
      skipped: true
    };
  }

  const {
    to,
    subject,
    body,
    html,
    data = {},
    from = process.env.EMAIL_FROM || 'BirJob <noreply@birjob.az>'
  } = options;

  if (!to || !subject || (!body && !html)) {
    throw new Error('Missing required email parameters: to, subject, and body/html');
  }

  try {
    const mailOptions = {
      from,
      to,
      subject,
      text: body,
      html: html || generateHTMLFromText(body, subject, data)
    };

    const result = await transporter.sendMail(mailOptions);
    
    logger.context.notification('email_sent', to, true);
    
    return {
      success: true,
      messageId: result.messageId,
      to,
      subject
    };

  } catch (error) {
    logger.error('Error sending email notification:', {
      to,
      subject,
      error: error.message
    });
    
    return {
      success: false,
      error: error.message,
      to,
      subject
    };
  }
}

/**
 * Send job alert email with multiple jobs
 * @param {Object} options - Job alert options
 * @param {string} options.to - Recipient email
 * @param {Array} options.jobs - Array of matching jobs
 * @param {Array} options.keywords - Matched keywords
 * @param {string} options.period - Alert period (daily/weekly)
 * @returns {Promise<Object>} - Send result
 */
async function sendJobAlertEmail(options) {
  const {
    to,
    jobs,
    keywords = [],
    period = 'daily'
  } = options;

  if (!jobs || jobs.length === 0) {
    return {
      success: false,
      error: 'No jobs to send'
    };
  }

  const subject = `🔔 ${jobs.length} New Job${jobs.length > 1 ? 's' : ''} Found - ${period.charAt(0).toUpperCase() + period.slice(1)} Alert`;
  
  const html = generateJobAlertHTML({
    jobs,
    keywords,
    period,
    recipientEmail: to
  });

  const text = generateJobAlertText({
    jobs,
    keywords,
    period
  });

  return await sendEmailNotification({
    to,
    subject,
    body: text,
    html,
    data: {
      jobCount: jobs.length,
      keywords,
      period
    }
  });
}

/**
 * Send welcome email to new users
 * @param {Object} options - Welcome email options
 * @param {string} options.to - Recipient email
 * @param {string} options.name - User name (optional)
 * @returns {Promise<Object>} - Send result
 */
async function sendWelcomeEmail(options) {
  const { to, name } = options;
  
  const subject = '🎉 Welcome to BirJob!';
  const html = generateWelcomeHTML({ name, email: to });
  const text = generateWelcomeText({ name });

  return await sendEmailNotification({
    to,
    subject,
    body: text,
    html,
    data: {
      type: 'welcome',
      userEmail: to
    }
  });
}

/**
 * Send notification summary email
 * @param {Object} options - Summary options
 * @param {string} options.to - Recipient email
 * @param {Object} options.stats - Notification statistics
 * @param {string} options.period - Summary period
 * @returns {Promise<Object>} - Send result
 */
async function sendNotificationSummary(options) {
  const { to, stats, period = 'weekly' } = options;
  
  const subject = `📊 Your ${period.charAt(0).toUpperCase() + period.slice(1)} BirJob Summary`;
  const html = generateSummaryHTML({ stats, period, email: to });
  const text = generateSummaryText({ stats, period });

  return await sendEmailNotification({
    to,
    subject,
    body: text,
    html,
    data: {
      type: 'summary',
      period,
      stats
    }
  });
}

/**
 * Send bulk emails to multiple recipients
 * @param {Array} emails - Array of email objects
 * @returns {Promise<Object>} - Bulk send results
 */
async function sendBulkEmails(emails) {
  if (!Array.isArray(emails) || emails.length === 0) {
    throw new Error('Emails array is required and must not be empty');
  }

  const results = {
    total: emails.length,
    successful: 0,
    failed: 0,
    errors: []
  };

  logger.info(`Starting bulk email send to ${emails.length} recipients`);

  // Process emails in smaller batches to avoid overwhelming the SMTP server
  const batchSize = 10;
  const batches = [];
  
  for (let i = 0; i < emails.length; i += batchSize) {
    batches.push(emails.slice(i, i + batchSize));
  }

  for (const batch of batches) {
    const batchPromises = batch.map(async (emailOptions) => {
      try {
        const result = await sendEmailNotification(emailOptions);
        
        if (result.success) {
          results.successful++;
        } else if (!result.skipped) {
          results.failed++;
          results.errors.push({
            to: emailOptions.to,
            error: result.error
          });
        }
        
        return result;
        
      } catch (error) {
        results.failed++;
        results.errors.push({
          to: emailOptions.to,
          error: error.message
        });
        
        return { success: false, error: error.message };
      }
    });

    await Promise.all(batchPromises);
    
    // Small delay between batches to avoid rate limiting
    if (batches.indexOf(batch) < batches.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }

  logger.info(`Bulk email send completed: ${results.successful} successful, ${results.failed} failed`);
  
  return results;
}

/**
 * Generate HTML email template from text
 */
function generateHTMLFromText(text, subject, data = {}) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${subject}</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #007AFF, #0056CC); color: white; padding: 30px 20px; text-align: center; }
        .content { padding: 30px 20px; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }
        .button { display: inline-block; padding: 12px 24px; background: #007AFF; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 4px; white-space: pre-wrap; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🚀 BirJob</h1>
          <p>${subject}</p>
        </div>
        <div class="content">
          <pre>${text}</pre>
        </div>
        <div class="footer">
          <p>Best regards,<br>The BirJob Team</p>
          <p><a href="https://birjob.az">Visit BirJob</a> | <a href="https://birjob.az/unsubscribe">Unsubscribe</a></p>
        </div>
      </div>
    </body>
    </html>
  `;
}

/**
 * Generate job alert HTML email
 */
function generateJobAlertHTML(options) {
  const { jobs, keywords, period, recipientEmail } = options;
  
  const jobsHTML = jobs.map(job => `
    <div style="border: 1px solid #e1e5e9; border-radius: 8px; padding: 20px; margin: 15px 0; background: #fafbfc;">
      <h3 style="margin: 0 0 10px 0; color: #1a1a1a;">${job.title}</h3>
      <p style="margin: 5px 0; color: #666; font-size: 16px;"><strong>${job.company}</strong></p>
      ${job.source ? `<p style="margin: 5px 0; color: #888; font-size: 14px;">Source: ${job.source}</p>` : ''}
      <p style="margin: 10px 0 0 0; color: #888; font-size: 14px;">Posted: ${new Date(job.created_at).toLocaleDateString()}</p>
      <a href="${job.apply_link}" style="display: inline-block; padding: 10px 20px; background: #007AFF; color: white; text-decoration: none; border-radius: 6px; margin-top: 15px;">Apply Now</a>
    </div>
  `).join('');

  const keywordsHTML = keywords.length > 0 ? `
    <div style="margin: 20px 0; padding: 15px; background: #e8f4f8; border-radius: 6px;">
      <p style="margin: 0; font-size: 14px; color: #666;">
        <strong>Matched Keywords:</strong> ${keywords.join(', ')}
      </p>
    </div>
  ` : '';

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>New Job Alert</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f5f5f5;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #007AFF, #0056CC); color: white; padding: 30px 20px; text-align: center;">
          <h1 style="margin: 0; font-size: 28px;">🔔 New Job Alert!</h1>
          <p style="margin: 10px 0 0 0; font-size: 16px;">We found ${jobs.length} new job${jobs.length > 1 ? 's' : ''} matching your criteria</p>
        </div>
        <div style="padding: 30px 20px;">
          ${keywordsHTML}
          ${jobsHTML}
          <div style="margin: 30px 0; text-align: center;">
            <a href="https://birjob.az/jobs" style="display: inline-block; padding: 15px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 8px; font-size: 16px;">View All Jobs</a>
          </div>
        </div>
        <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666;">
          <p>You're receiving this because you have job alerts enabled.</p>
          <p><a href="https://birjob.az/profile">Manage your alerts</a> | <a href="https://birjob.az/unsubscribe?email=${encodeURIComponent(recipientEmail)}">Unsubscribe</a></p>
        </div>
      </div>
    </body>
    </html>
  `;
}

/**
 * Generate job alert text email
 */
function generateJobAlertText(options) {
  const { jobs, keywords, period } = options;
  
  let text = `🔔 NEW JOB ALERT - ${period.toUpperCase()}\n\n`;
  text += `We found ${jobs.length} new job${jobs.length > 1 ? 's' : ''} matching your criteria!\n\n`;
  
  if (keywords.length > 0) {
    text += `Matched Keywords: ${keywords.join(', ')}\n\n`;
  }
  
  text += 'JOBS:\n';
  text += '=' .repeat(50) + '\n\n';
  
  jobs.forEach((job, index) => {
    text += `${index + 1}. ${job.title}\n`;
    text += `   Company: ${job.company}\n`;
    if (job.source) text += `   Source: ${job.source}\n`;
    text += `   Posted: ${new Date(job.created_at).toLocaleDateString()}\n`;
    text += `   Apply: ${job.apply_link}\n\n`;
  });
  
  text += 'Visit https://birjob.az for more jobs!\n\n';
  text += 'Best regards,\nThe BirJob Team';
  
  return text;
}

/**
 * Generate welcome email HTML
 */
function generateWelcomeHTML(options) {
  const { name, email } = options;
  const displayName = name || email.split('@')[0];
  
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Welcome to BirJob</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f5f5f5;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #007AFF, #0056CC); color: white; padding: 40px 20px; text-align: center;">
          <h1 style="margin: 0; font-size: 32px;">🎉 Welcome to BirJob!</h1>
          <p style="margin: 15px 0 0 0; font-size: 18px;">Hi ${displayName}, you're all set!</p>
        </div>
        <div style="padding: 40px 20px;">
          <h2 style="color: #1a1a1a; margin-top: 0;">What's next?</h2>
          
          <div style="margin: 25px 0;">
            <h3 style="color: #007AFF; margin: 0 0 10px 0;">📝 Set up job alerts</h3>
            <p style="margin: 0; color: #666;">Add keywords to get notified when matching jobs are posted.</p>
          </div>
          
          <div style="margin: 25px 0;">
            <h3 style="color: #007AFF; margin: 0 0 10px 0;">🔍 Browse jobs</h3>
            <p style="margin: 0; color: #666;">Explore thousands of job opportunities from 50+ sources.</p>
          </div>
          
          <div style="margin: 25px 0;">
            <h3 style="color: #007AFF; margin: 0 0 10px 0;">📱 Download our app</h3>
            <p style="margin: 0; color: #666;">Get instant notifications and search on the go.</p>
          </div>
          
          <div style="text-align: center; margin: 40px 0;">
            <a href="https://birjob.az/setup" style="display: inline-block; padding: 15px 30px; background: #007AFF; color: white; text-decoration: none; border-radius: 8px; font-size: 16px; margin: 10px;">Get Started</a>
          </div>
        </div>
        <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666;">
          <p>Need help? Reply to this email or visit our <a href="https://birjob.az/help">Help Center</a></p>
          <p>Best regards,<br>The BirJob Team</p>
        </div>
      </div>
    </body>
    </html>
  `;
}

/**
 * Generate welcome email text
 */
function generateWelcomeText(options) {
  const { name } = options;
  const displayName = name || 'there';
  
  return `
🎉 WELCOME TO BIRJOB!

Hi ${displayName},

Welcome to BirJob - Azerbaijan's leading job search platform! You're now part of a community that helps job seekers find their dream opportunities.

WHAT'S NEXT?

📝 Set up job alerts
Add keywords to get notified when matching jobs are posted.

🔍 Browse jobs  
Explore thousands of job opportunities from 50+ sources.

📱 Download our app
Get instant notifications and search on the go.

Get started: https://birjob.az/setup

Need help? Just reply to this email or visit our Help Center at https://birjob.az/help

Best regards,  
The BirJob Team

https://birjob.az
  `.trim();
}

/**
 * Generate summary email HTML and text
 */
function generateSummaryHTML(options) {
  const { stats, period, email } = options;
  
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Your ${period} BirJob Summary</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background-color: #f5f5f5;">
      <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 40px 20px;">
        <h1 style="color: #007AFF; text-align: center;">📊 Your ${period} Summary</h1>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
          <h3>Activity Summary:</h3>
          <ul>
            <li>Job alerts sent: ${stats.alertsSent || 0}</li>
            <li>Jobs matched: ${stats.jobsMatched || 0}</li>
            <li>Keywords active: ${stats.activeKeywords || 0}</li>
          </ul>
        </div>
        <div style="text-align: center; margin: 30px 0;">
          <a href="https://birjob.az/profile" style="display: inline-block; padding: 15px 30px; background: #007AFF; color: white; text-decoration: none; border-radius: 8px;">Manage Settings</a>
        </div>
      </div>
    </body>
    </html>
  `;
}

function generateSummaryText(options) {
  const { stats, period } = options;
  
  return `
📊 YOUR ${period.toUpperCase()} BIRJOB SUMMARY

Activity Summary:
- Job alerts sent: ${stats.alertsSent || 0}
- Jobs matched: ${stats.jobsMatched || 0}  
- Keywords active: ${stats.activeKeywords || 0}

Manage your settings: https://birjob.az/profile

Best regards,
The BirJob Team
  `.trim();
}

/**
 * Test email functionality
 * @param {string} to - Test recipient
 * @returns {Promise<Object>} - Test result
 */
async function testEmailService(to) {
  return await sendEmailNotification({
    to,
    subject: 'BirJob Email Service Test',
    body: 'This is a test email from the BirJob API email service. If you receive this, the email service is working correctly!',
    data: {
      type: 'test',
      timestamp: new Date().toISOString()
    }
  });
}

/**
 * Get email service health status
 * @returns {Object} - Service health status
 */
function getServiceHealth() {
  return {
    available: !!transporter,
    configured: !!(EMAIL_CONFIG.auth.user && EMAIL_CONFIG.auth.pass),
    service: EMAIL_CONFIG.service,
    host: EMAIL_CONFIG.host,
    port: EMAIL_CONFIG.port,
    secure: EMAIL_CONFIG.secure,
    timestamp: new Date().toISOString()
  };
}

module.exports = {
  sendEmailNotification,
  sendJobAlertEmail,
  sendWelcomeEmail,
  sendNotificationSummary,
  sendBulkEmails,
  testEmailService,
  getServiceHealth
};