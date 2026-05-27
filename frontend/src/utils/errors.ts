/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  error_code: string;
  status: number;
  fieldErrors?: Record<string, string>;

  constructor(message: string, error_code: string, status: number, fieldErrors?: Record<string, string>) {
    super(message);
    this.name = 'ApiError';
    this.error_code = error_code;
    this.status = status;
    this.fieldErrors = fieldErrors;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Parses a Fetch Response into an ApiError.
 * Reads StandardResponse error shape from body and maps Pydantic validation errors (422).
 */
export async function parseApiError(response: Response): Promise<ApiError> {
  const status = response.status;
  let error_code = status.toString();
  let message = response.statusText || 'An unexpected error occurred';
  let fieldErrors: Record<string, string> | undefined;

  try {
    const body = await response.json();
    if (body) {
      error_code = body.error_code || error_code;
      message = body.message || message;
      
      // Handle Pydantic validation errors
      if (Array.isArray(body.detail)) {
        fieldErrors = {};
        body.detail.forEach((err: any) => {
          if (err.loc && err.loc.length > 0) {
            const field = err.loc[err.loc.length - 1];
            fieldErrors![field] = err.msg;
          }
        });
      }
    }
  } catch (e) {
    // If parsing JSON fails, stick with status defaults
  }

  return new ApiError(message, error_code, status, fieldErrors);
}

/**
 * Type guard to check if an unknown error is an ApiError.
 */
export function isApiError(e: unknown): e is ApiError {
  return e instanceof ApiError;
}

/**
 * Safely extracts a field error from the fieldErrors map.
 */
export function getFieldError(errors: Record<string, string> | undefined, field: string): string | undefined {
  if (!errors) return undefined;
  return errors[field];
}
