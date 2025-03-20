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
    return request<API.Result_Knowledgebase_>(`/api/knowledgebases/${params?.knowledgebases_id}`, {
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
        filename?: string;  // 添加文件名参数
    },
    options?: { [key: string]: any },
) {
    const formData = new FormData();
    if (body?.file) {
        formData.append('file', body.file, body?.filename || 'untitled');  // 使用文件名
    }

    return request<API.Result_Upload_>(`/api/files`, {
        method: 'POST',
        data: formData,  // 直接传递 FormData 对象
        ...(options || {}),
    });
}



/**
 * 知识库加载文件
 */
export async function setKnowledgebasesConfig(
    params?: {
        knowledgebases_id?: string,
        file_id?: string;
    },
    body?: {
        config?: any;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Upload_>(`/api/knowledgebases/${params?.knowledgebases_id}/files/${params?.file_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
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
        knowledgebases_id?: string,
        file_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Knowledgebase_>(`/api/knowledgebases/${params?.knowledgebases_id}/files/${params?.file_id}`, {
        method: 'DELETE',
        ...(options || {}),
    });
}
