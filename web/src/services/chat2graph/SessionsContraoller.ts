import { request } from '@umijs/max';

/** 此处后端没有提供注释 GET /api/sessions */
export async function getSessions () {
  return request<API.Result_Sessions_>('/api/sessions', {
    method: 'GET',
  });
}

/**
 * 创建 session
*/
export async function createSession(
  body?: {
    name?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Session_>('/api/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}

/**
 * 通过 ID 获取 session
*/
export async function getSessionById(
  params: {
    session_id?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Session_>(`/api/sessions/${params.session_id}`, {
    method: 'GET',
    ...(options || {}),
  },);
}

/**
 * 更新 session
*/
export async function updateSession(
  params: {
    session_id?: string;
  },
  body: {
    name?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Session_>(`/api/sessions/${params.session_id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  },);
}

/**
 * 删除 session
*/
export async function deleteSession(
  params: {
    session_id?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Session_>(`/api/sessions/${params.session_id}`, {
    method: 'DELETE',
    ...(options || {}),
  });
}
