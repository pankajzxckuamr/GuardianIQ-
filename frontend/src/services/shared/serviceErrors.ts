/* src/services/shared/serviceErrors.ts */
export class ServiceError extends Error {
  public status: number;
  public requestId?: string;

  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ServiceError";
    this.status = status;
    this.requestId = requestId;
  }
}

export async function parseErrorResponse(res: Response): Promise<ServiceError> {
  let message = `Request failed with status ${res.status}`;
  let requestId: string | undefined;
  try {
    const body = await res.json();
    message = body.message || body.detail || message;
    requestId = body.request_id;
  } catch {
    /* ignore parse errors */
  }
  return new ServiceError(message, res.status, requestId);
}
