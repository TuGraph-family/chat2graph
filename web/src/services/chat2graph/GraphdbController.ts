import { request } from '@umijs/max';

/**
 * 获取所有graphdbs
*/
export async function getGraphdbs(
) {
    return request<API.Result_Graphdbs_>('/api/graphdbs', {
        method: 'GET'
    });
}


/**
* 创建Graphdb
 */
export async function createGraphdbs(
    body?: {
        ip?: string,
        port?: number,
        user?: string,
        pwd?: string,
        desc?: string,
        name?: string,
        is_default_db?: boolean,
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Graphdb_>('/api/graphdbs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        data: body,
        ...(options || {}),
    });
}


/**
 * 通过ID获取graphdb
 */
export async function getGraphdbById(
    params?: {
        graph_db_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Graphdb_>(`/api/graphdbs/${params?.graph_db_id}`, {
        method: 'GET',
        ...(options || {}),
    },);
}


/**
 * 删除graphdbs
*/
export async function deleteGraphdbs(
    params?: {
        graph_db_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Graphdb_>(`/api/graphdbs/${params?.graph_db_id}`, {
        method: 'DELETE',
        ...(options || {}),
    });
}


/**
 * 更新 graphdbs
*/
export async function updateGraphdbs(
    params?: {
        session_id?: string;
    },
    body?: {
        ip?: string,
        port?: number,
        user?: string,
        pwd?: string,
        desc?: string,
        name?: string,
        is_default_db?: boolean,
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Graphdb_>(`/api/graphdbs/${params?.session_id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        data: body,
        ...(options || {}),
    },);
}


