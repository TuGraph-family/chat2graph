import { defineStore } from 'pinia'
import { analyticGraphService, type SessionRequest, type AnalySessionItem } from '@/services/analytic_graph'
import { parseContent } from '@/utils/parse_content'
export interface AnalyticGraphState {
    current_session: AnalySessionItem,
    sessions: Array<AnalySessionItem>,
    message_list: any[]
}



export const useAnalyticGraphStore = defineStore('analyticGraph', {
    state: (): AnalyticGraphState => ({
        current_session: {
            graph_name: '',
            id: '',
            ip: '',
            port: '',
            user: '',
            pwd: '',
            created_at: '',
            schema: '',
        },
        sessions: [],
        message_list: []
    }),
    getters: {},
    actions: {
        async createSession(params: SessionRequest) {
            let { success, data, message } = await analyticGraphService.createSession(params)
            return {
                success, data, message
            }
        },
        updateCurrentSession(params: AnalySessionItem) {
            this.current_session = params
        },
        async getSessions(): Promise<Array<AnalySessionItem>> {
            let res = await analyticGraphService.getSessions()
            return res
        },
        updateSessions(params: Array<AnalySessionItem>) {
            this.sessions = params
        },
        async getSessionHistory(params: { session_id: string }) {
            let res = await analyticGraphService.getMessagesBySessionID(params.session_id)
            let mergedData = res.reduce((acc, item, index) => {
                if (index > 0 && item.role === acc[acc.length - 1].role) {
                    acc[acc.length - 1].content += `\n${item.content}`
                } else {
                    acc.push({ ...item }) // 创建新的对象避免引用问题
                }
                return acc
            }, [])

            // 处理 parse_content
            let data = mergedData.map((item: any) => {
                item.parse_content = parseContent(item.content)
                return item
            })

            this.updateMessageList(data)
            return data
        },
        updateMessageList(data: any[]) {
            this.message_list = data
        },
        async deleteSession(session_id: string) {
            let res = await analyticGraphService.deleteSession(session_id)
            return res
        }
    }
})