/**
 * Frontend error logging service for sending errors to backend.
 */
import { api } from './api';

interface ErrorLogData {
  level: 'ERROR' | 'CRITICAL' | 'WARNING';
  message: string;
  error_type?: string;
  error_details?: Record<string, any>;
  stack_trace?: string;
  user_id?: string;
  request_path?: string;
  request_method?: string;
  request_body?: Record<string, any>;
  response_status?: number;
}

class ErrorLogger {
  private isEnabled: boolean = true;
  private queue: ErrorLogData[] = [];
  private isProcessing: boolean = false;

  constructor() {
    // Disable in development to avoid noise
    this.isEnabled = import.meta.env.PROD || import.meta.env.VITE_ENABLE_ERROR_LOGGING === 'true';
  }

  /**
   * Log error to backend.
   */
  async logError(
    error: Error | string,
    context?: {
      user_id?: string;
      request_path?: string;
      request_method?: string;
      request_body?: Record<string, any>;
      response_status?: number;
      error_details?: Record<string, any>;
    }
  ): Promise<void> {
    if (!this.isEnabled) {
      console.error('Error (not logged to backend):', error);
      return;
    }

    try {
      const errorData: ErrorLogData = {
        level: 'ERROR',
        message: typeof error === 'string' ? error : error.message,
        error_type: typeof error === 'string' ? undefined : error.constructor.name,
        stack_trace: typeof error === 'string' ? undefined : error.stack,
        ...context,
      };

      // Add to queue and process
      this.queue.push(errorData);
      await this.processQueue();
    } catch (err) {
      // Don't fail if error logging fails
      console.error('Failed to log error to backend:', err);
    }
  }

  /**
   * Log warning to backend.
   */
  async logWarning(
    message: string,
    context?: {
      user_id?: string;
      request_path?: string;
      error_details?: Record<string, any>;
    }
  ): Promise<void> {
    if (!this.isEnabled) {
      console.warn('Warning (not logged to backend):', message);
      return;
    }

    try {
      const errorData: ErrorLogData = {
        level: 'WARNING',
        message,
        ...context,
      };

      this.queue.push(errorData);
      await this.processQueue();
    } catch (err) {
      console.error('Failed to log warning to backend:', err);
    }
  }

  /**
   * Process error queue.
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    try {
      // Process all queued errors
      const errorsToProcess = [...this.queue];
      this.queue = [];

      // Send errors to backend (fire and forget)
      for (const errorData of errorsToProcess) {
        try {
          // Use fetch directly to avoid circular dependencies
          const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          await fetch(`${apiUrl}/api/v1/error-logs/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(errorData),
          }).catch(() => {
            // Silently fail - don't block the app
          });
        } catch (err) {
          // Silently fail
          console.debug('Failed to send error to backend:', err);
        }
      }
    } finally {
      this.isProcessing = false;
    }
  }
}

export const errorLogger = new ErrorLogger();

// Global error handler
if (typeof window !== 'undefined') {
  // Handle unhandled errors
  window.addEventListener('error', (event) => {
    errorLogger.logError(event.error || event.message, {
      error_details: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      },
    });
  });

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    errorLogger.logError(
      event.reason instanceof Error
        ? event.reason
        : new Error(String(event.reason)),
      {
        error_details: {
          type: 'unhandledrejection',
        },
      }
    );
  });
}

