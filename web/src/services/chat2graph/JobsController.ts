import { request } from "@umijs/max";


export async function getJobResults(
    params: {
        job_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Job_>(`/api/jobs/${params.job_id}/message`, {
        method: 'GET',
        ...(options || {}),
    },);
}