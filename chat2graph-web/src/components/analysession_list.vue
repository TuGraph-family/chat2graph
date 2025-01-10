<template>
    <div class="analysession-list">
        <div class="analysession-card" v-for="item in sessions">
            <n-card size="small" :class="{ 'active': item.id == current_session.id }" @click="selectSession(item)">
                图谱：{{ item.graph_name }}<br>
                时间：{{ new Date(parseInt(item.created_at) * 1000).toLocaleString() }}
            </n-card>
            <div class="del-btn" @click="deleteSession(item.id)">
                <n-icon size="20" color="red">
                    <Trash />
                </n-icon>
            </div>
        </div>

    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NCard, NIcon } from 'naive-ui'
import { useAnalyticGraphStore } from '@/stores/analytic_store'
import type { AnalySessionItem, SessionRequest } from '@/services/analytic_graph'
import { Trash } from '@vicons/tabler'
const analyGraphStore = useAnalyticGraphStore()
let sessions = computed(() => {
    return analyGraphStore.sessions
})
let current_session = computed(() => {
    return analyGraphStore.current_session
})

async function initSessionsList() {
    let list = await analyGraphStore.getSessions()
    analyGraphStore.updateSessions(list)
    if (!current_session.value.id && sessions.value.length) {
        analyGraphStore.updateCurrentSession({
            graph_name: list[0].graph_name,
            id: list[0].id,
            ip: list[0].ip,
            port: list[0].port,
            user: list[0].user,
            pwd: list[0].pwd,
            created_at: list[0].created_at,
            schema: list[0].schema
        })
    }

}
initSessionsList()
async function selectSession(item: AnalySessionItem) {
    analyGraphStore.updateMessageList([])
    analyGraphStore.updateCurrentSession({
        graph_name: item.graph_name,
        id: item.id,
        ip: item.ip,
        port: item.port,
        user: item.user,
        pwd: item.pwd,
        created_at: item.created_at,
        schema: item.schema
    })
}

async function deleteSession(session_id: string) {
    let { success, message } = await analyGraphStore.deleteSession(session_id)
    if (success) {
        let list = await analyGraphStore.getSessions()
        analyGraphStore.updateSessions(list)
        analyGraphStore.updateMessageList([])
        if (current_session.value.id == session_id && sessions.value.length) {
            analyGraphStore.updateCurrentSession({
                graph_name: list[0].graph_name,
                id: list[0].id,
                ip: list[0].ip,
                port: list[0].port,
                user: list[0].user,
                pwd: list[0].pwd,
                created_at: list[0].created_at,
                schema: list[0].schema
            })
        }
        if (!sessions.value.length) {
            analyGraphStore.updateCurrentSession({
                graph_name: '',
                id: '',
                ip: '',
                port: '',
                user: '',
                pwd: '',
                created_at: '',
                schema: ''
            })
        }
    }
}
</script>

<style scoped lang="less">
.analysession-list {
    width: 100%;
    height: 100%;
    overflow: auto;

    .analysession-card {
        position: relative;
        z-index: 1;

        .del-btn {
            cursor: pointer;
            position: absolute;
            bottom: 0;
            right: 0.3125rem;
            z-index: 2;
        }
    }

    .n-card {
        margin-top: 0.625rem;
        cursor: pointer;

        &.active {
            border-color: green;
        }
    }
}
</style>