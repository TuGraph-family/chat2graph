import { request } from '@umijs/max';

/** 此处后端没有提供注释 GET /api/sessions */
export async function getSessions(
  params: {
    page?: number;
    size?: number;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Sessions_>('/api/sessions', {
    method: 'GET',
    params: params,
    ...(options || {}),
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

/**
 * 通过 id 获取 job ids
*/
export async function getJobIdById(
  params: {
    session_id?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_JobIds_>(`/api/sessions/${params.session_id}/job_id`, {
    method: 'GET',
    ...(options || {}),
  });
}


/**
 * 通过 sessionid 获取 jobId
*/
export async function getJobIdsBySessionId(
  params: {
    session_id?: string;
  },
  body: {
    instruction_message?: {
      payload?: string;
      message_type?: string;
      assigned_expert_name?: string;
    },
    attached_messages?: {
      file_id?: string,
      message_type: string,
    }[];

  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Chat_>(`/api/sessions/${params.session_id}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  });
}


/**
 * 通过 sessionid 获取 message views
*/
export async function getMessagesBySessionId(
  params: {
    session_id?: string;
  },
  options?: { [key: string]: any },
) {
  return request<API.Result_Messages_>(`/api/sessions/${params.session_id}/messages`, {
    method: 'GET',
    ...(options || {}),
  });
}