import { defineStore } from 'pinia'
import { createGraphService, type SessionItem, type SchemaConfig, type DataConfig } from '@/services/create_graph'
import { parseContent } from '@/utils/parse_content'


interface CreateGraphState {
    current_session: {
        name: string,
        id: string,
    },
    sessions: Array<SessionItem>,
    message_list: any[]
}

export const useCreateGraphStore = defineStore('createGraph', {
    state: (): CreateGraphState => ({
        current_session: {
            name: '',
            id: ''
        },
        sessions: [],
        message_list: []
    }),
    getters: {},
    actions: {
        async createSession(params: { name: string }): Promise<{ name: string, id: string }> {
            let { name, id } = await createGraphService.createSession({ name: params.name })
            return {
                name, id
            }
        },
        updateCurrentSession(params: { name: string, id: string }) {
            this.current_session = params
        },
        async getSessions(): Promise<Array<SessionItem>> {
            let res = await createGraphService.getSessions()
            return res
        },
        updateSessions(params: Array<SessionItem>) {
            this.sessions = params
        },
        async getSessionHistory(params: { session_id: string }) {
            let res = await createGraphService.getMessagesBySessionID(params.session_id)
            return res
        },
        updateMessageList(data: any[]) {
            this.message_list = data
        },
        async deleteSession(session_id: string) {
            let res = await createGraphService.deleteSession(session_id)
            return res
        },
        async importSchema(data: SchemaConfig) {
            let res = await createGraphService.importSchema(data)
            return res
        },
        async importVertex(data: DataConfig) {
            let res = await createGraphService.importVertex(data)
            return res
        },
        async importEdge(data: DataConfig) {
            let res = await createGraphService.importEdge(data)
            return res
        }
    }
})