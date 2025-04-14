interface IAttachedMessageItem {
    id: string,
    job_id: string,
    session_id: string,
    message_type?: string,
    payload?: string,
    timestamp?: number
}


export {
    IAttachedMessageItem
}