import { request } from "@umijs/max";


export async function getJobResults(
    params: {
        job_id?: string;
    },
    options?: { [key: string]: any },
) {
    return request<API.Result_Job_>(`/api/jobs/${params.job_id}/get_job_results`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        ...(options || {}),
    },);
}