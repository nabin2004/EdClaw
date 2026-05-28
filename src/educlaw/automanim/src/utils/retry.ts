/**
 * Retry utility with exponential backoff and jitter
 */
export interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitter: boolean;
}

export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {}
): Promise<T> {
  const opts: RetryOptions = {
    maxRetries: 3,
    baseDelayMs: 1000,
    maxDelayMs: 30000,
    jitter: true,
    ...options,
  };

  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === opts.maxRetries) {
        break;
      }

      const delay = calculateDelay(attempt, opts);
      console.warn(`Retry attempt ${attempt + 1}/${opts.maxRetries} after ${delay}ms. Error: ${lastError.message}`);
      await sleep(delay);
    }
  }

  throw lastError;
}

function calculateDelay(attempt: number, opts: RetryOptions): number {
  const exponentialDelay = opts.baseDelayMs * Math.pow(2, attempt);
  const cappedDelay = Math.min(exponentialDelay, opts.maxDelayMs);
  
  if (opts.jitter) {
    const jitterAmount = cappedDelay * 0.1; // 10% jitter
    return cappedDelay - jitterAmount / 2 + Math.random() * jitterAmount;
  }
  
  return cappedDelay;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
