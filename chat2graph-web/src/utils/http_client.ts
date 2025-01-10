const baseUrl = '/api';

export interface HttpResponse {
    "data": any,
    "message": string,
    "success": boolean
}

// 定义接口以方便后续扩展和类型安全
interface RequestOptions {
    headers?: HeadersInit;
    body?: BodyInit | null;
}

class HttpClient {
    // 基础URL，可以是API服务器的地址
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    // GET请求
    async get(endpoint: string, options?: RequestOptions): Promise<HttpResponse> {
        return this.request(endpoint, { method: 'GET', ...options });
    }

    // POST请求
    async post(endpoint: string, options?: RequestOptions): Promise<HttpResponse> {
        return this.request(endpoint, { method: 'POST', ...options });
    }

    // PUT请求
    async put(endpoint: string, options?: RequestOptions): Promise<HttpResponse> {
        return this.request(endpoint, { method: 'PUT', ...options });
    }

    // DELETE请求
    async delete(endpoint: string, options?: RequestOptions): Promise<HttpResponse> {
        return this.request(endpoint, { method: 'DELETE', ...options });
    }

    // 私有方法执行请求
    private async request(endpoint: string, options?: RequestOptions & { method: string }): Promise<HttpResponse> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: options?.method,
            headers: options?.headers,
            body: options?.body,
        });

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 假设服务器总是返回JSON格式的数据
        return response.json();
    }
}

// 创建HttpClient实例，此处您需要替换成您的API基础URL
const httpClient = new HttpClient(baseUrl);

// 导出实例
export { httpClient };
