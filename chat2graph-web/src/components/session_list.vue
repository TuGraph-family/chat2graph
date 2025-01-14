<template>
    <div class="session-list">
        <div class="session-card" v-for="item in sessions">
            <n-card size="small" :class="{ 'active': item.id == current_session.id }"
                @click="selectSession(item)">
                标题：{{ item.name }}<br>
                时间：{{ item.created_at }}
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
import { useCreateGraphStore } from '@/stores/create_graph'
import type { SessionItem } from '@/services/create_graph'
import { Trash } from '@vicons/tabler'
let sessions = computed(() => {
    return createGraphStore.sessions
})
let current_session = computed(() => {
    return createGraphStore.current_session
})
const createGraphStore = useCreateGraphStore()
async function initSessionsList() {
    let list = await createGraphStore.getSessions()
    createGraphStore.updateSessions(list)
    if (!current_session.value.id && sessions.value.length) {
        createGraphStore.updateCurrentSession({ name: list[0].name, id: list[0].id })
    }

}
initSessionsList()
async function selectSession(item: SessionItem) {
    createGraphStore.updateMessageList([])
    createGraphStore.updateCurrentSession({ name: item.name, id: item.id })
}

async function deleteSession(session_id: string) {
    let { success, message } = await createGraphStore.deleteSession(session_id)
    if (success) {
        let list = await createGraphStore.getSessions()
        createGraphStore.updateSessions(list)
        createGraphStore.updateMessageList([])
        if (current_session.value.id == session_id && sessions.value.length) {
            createGraphStore.updateCurrentSession({ name: list[0].name, id: list[0].id })
        }
        if (!sessions.value.length) {
            createGraphStore.updateCurrentSession({ name: '', id: '' })
        }
    }
}
</script>

<style scoped lang="less">
.session-list {
    width: 100%;
    height: 100%;
    overflow: auto;

    .session-card {
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