import { request } from '@umijs/max';

/**
 * 获取所有Knowledgebase
*/
export async function getKnowledgebases(
) {
    return request<API.Result_Knowledgebases_>('/api/knowledgebases', {
        method: 'GET'
    });
}


/**
 * 创建Knowledgebase
 */
export async function createKnowledgebase(
    body?: {
        name?: string,
        knowledge_type?: "graph" | "vector",
        session_id?: string,
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>('/api/knowledgebases', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        data: body,
        ...(options || {}),
    });
}


/**
 * 通过ID获取Knowledgebase
 */
export async function getKnowledgebasesById(
    params?: {
        knowledgebases_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>(`/api/knowledgebases/${params?.knowledgebases_id}`, {
        method: 'GET',
        ...(options || {}),
    },);
}


/**
 * 删除Knowledgebase
*/
export async function deleteKnowledgebases(
    params?: {
        knowledgebases_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>(`api/knowledgebases/${params?.knowledgebases_id}`, {
        method: 'DELETE',
        ...(options || {}),
    });
}


/**
 * 上传文件
 */
export async function uploadFile(
    body?: {
        file?: Blob;
        config?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>(`/api/files/upload`, {
        method: 'POST',
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        data: body,
        ...(options || {}),
    });
}


/**
 * 编辑KnowledgeBase    
 */
export async function editKnowledgebase(
    params?: {
        knowledgebases_id?: string;
    },
    body?: {
        name?: string,
        description?: string,
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>(`/api/knowledgebases/${params?.knowledgebases_id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        data: body,
        ...(options || {}),
    });
}


/**
 * 删除文件
 */
export async function deleteFile(
    params?: {
        file_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>(`/api/files/delete/${params?.file_id}`, {
        method: 'DELETE',
        ...(options || {}),
    });
}
