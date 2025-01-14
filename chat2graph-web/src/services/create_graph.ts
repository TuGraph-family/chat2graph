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
            id: data.id
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
        let { success, data, message } = await httpClient.delete(`/sessions/${session_id}`, {
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return {
            success,
            message
        }
    },
    sendMessage: async (params: { session_id: string, message: string }): Promise<{ success: boolean, message: string, data:any }> => {
        let { success, message, data } = await httpClient.post('/messages', {
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        return { success, message, data }
                  
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