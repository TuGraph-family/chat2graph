import { httpClient } from '@/utils/http_client';
let url = '/assistant/message'
interface SessionRequest {
    name: string;
}

interface SessionResponse {
    name: string
    id: string
}

export interface SchemaConfig {
    ip: string,
    port: string,
    user: string,
    pwd: string,
    graph_name: string,
    schema: string
}

export interface DataConfig {
    ip: string,
    port: string,
    user: string,
    pwd: string,
    graph_name: string,
    json_data: string
}

export interface SessionItem {
    "created_at": string,
    "id": string,
    "name": string
}
export const createGraphService = {
    createSession: async (sessionRequest: SessionRequest): Promise<SessionResponse> => {
        let { success, data, message } = await httpClient.post('/sessions', {
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(sessionRequest),
        });
        return {
            name: data.name,
            id: data.thread_id
        }
    },
    getSessions: async (): Promise<Array<SessionItem>> => {
        let { success, data, message } = await httpClient.get('/sessions', {
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return data
    },
    getMessagesBySessionID: async (session_id: string): Promise<any[]> => {
        let { success, data, message } = await httpClient.get(`/messages/${session_id}`, {
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return data
    },
    deleteSession: async (session_id: string): Promise<{ success: boolean, message: string }> => {
        let { success, data, message } = await httpClient.delete(`/assistant/session/${session_id}`, {
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return {
            success,
            message
        }
    },
    sendMessage: async (params: { assistant_id: string, thread_id: string, message: string }, onMessage: (message: string) => void) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            if (response.body) {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let message = '';

                // async function handleStream(result: ReadableStreamReadResult<Uint8Array>): Promise<void> {
                //     if (result.done) {
                //         console.log('Stream completed.');
                //         return;
                //     }
                //     const text = decoder.decode(result.value);
                //     message += text;
                //     onMessage(message);  // 通过回调函数传递消息
                //     const nextResult = await reader.read();
                //     return handleStream(nextResult);
                // }

                // const initialResult = await reader.read();
                // await handleStream(initialResult);

                return { success: true, data: message }; // 返回最终数据
            }
        } catch (error: any) {
            console.error('Error:', error);
            return { success: false, message: error.message };
        }
    },
    importSchema: async (params: SchemaConfig): Promise<{ success: boolean, message: string }> => {
        let { success, message } = await httpClient.post('/db/import_schema', {
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        return { success, message }
    },
    importVertex: async (params: DataConfig): Promise<{ success: boolean, message: string }> => {
        let { success, message } = await httpClient.post('/db/import_vertex', {
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        return { success, message }
    },
    importEdge: async (params: DataConfig): Promise<{ success: boolean, message: string }> => {
        let { success, message } = await httpClient.post('/db/import_edge', {
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        return { success, message }
    },
};