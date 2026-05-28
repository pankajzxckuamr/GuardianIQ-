/* src/services/shared/apiClient.ts */
import { generateRequestId } from "./requestId";

interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

class ApiClient {
  private async request<T = any>(url: string, config: RequestConfig = {}): Promise<T> {
    const token = localStorage.getItem("guardianiq_token");
    const headers = new Headers(config.headers || {});
    
    if (!headers.has("Content-Type") && !(config.body instanceof FormData)) {
      if (config.body instanceof URLSearchParams) {
        headers.set("Content-Type", "application/x-www-form-urlencoded");
      } else {
        headers.set("Content-Type", "application/json");
      }
    }
    
    if (!headers.has("X-Request-ID")) {
      headers.set("X-Request-ID", generateRequestId());
    }

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    let fetchUrl = url;
    if (config.params) {
      const query = new URLSearchParams();
      for (const [key, val] of Object.entries(config.params)) {
        if (val !== undefined && val !== null) {
          query.set(key, String(val));
        }
      }
      const qStr = query.toString();
      if (qStr) {
        fetchUrl += (url.includes("?") ? "&" : "?") + qStr;
      }
    }

    const fetchConfig: RequestInit = {
      ...config,
      headers,
    };

    const response = await fetch(fetchUrl, fetchConfig);

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem("guardianiq_token");
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }
      if (response.status === 403) {
        window.location.href = "/unauthorized";
        throw new Error("Forbidden");
      }

      let errorMessage = `Request failed with status ${response.status}`;
      try {
        const errBody = await response.json();
        errorMessage = errBody.message || errBody.detail || errorMessage;
      } catch (e) {
        // Fallback to text if JSON parsing fails
        try {
          const errText = await response.clone().text();
          if (errText) errorMessage = errText;
        } catch (e2) {}
      }
      throw new Error(errorMessage);
    }

    const text = await response.text();
    if (!text) {
      return {} as T;
    }

    const body = JSON.parse(text);
    // Mimicking the old logic: return body.data ?? body
    return body.data ?? body;
  }

  get<T = any>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, { ...config, method: "GET" });
  }

  post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, {
      ...config,
      method: "POST",
      body: data instanceof URLSearchParams || data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, {
      ...config,
      method: "PUT",
      body: data instanceof URLSearchParams || data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  delete<T = any>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, { ...config, method: "DELETE" });
  }
}

const apiClient = new ApiClient();
export default apiClient;
