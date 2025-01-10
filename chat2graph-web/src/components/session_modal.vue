<template>
  <div class="session-modal-component">
    <div class="session-modal-name">会话名称</div>
    <n-input v-model:value="session_name" type="text" placeholder="请输入会话名称" />
    <div class="session-modal-btns">
      <n-button strong secondary type="success" @click="createNewSession"> 创建 </n-button>
      <n-button strong secondary type="warning" @click="cancel"> 取消 </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue'
import { NInput, NButton, useMessage } from 'naive-ui'
import { useCreateGraphStore } from '@/stores/create_graph'
let session_name = ref('')
const message = useMessage()
const createGraphStore = useCreateGraphStore()
const emit = defineEmits(['update:show'])
async function createNewSession() {
  try {
    if (!session_name.value) {
      message.warning('会话名称不能为空！')
      return
    }
    const sessionData = await createGraphStore.createSession({ session_name: session_name.value })
    if (sessionData.thread_id) {
      let list = await createGraphStore.getSessions()
      createGraphStore.updateSessions(list)
      await createGraphStore.updateCurrentSession(sessionData)
      closeModal(false)
    }
  } catch (error) {
    console.error('Failed to create session:', error)
  }
}

function cancel() {
  closeModal(false)
}

function closeModal(status: boolean) {
  emit('update:show', status)
}
</script>

<style scoped lang="less">
.session-modal-component {
  .session-modal-name {
    font-size: 1.125rem;
    margin-bottom: 0.625rem;
    font-weight: 700;
  }

  .session-modal-btns {
    margin-top: 0.625rem;
    display: flex;
    justify-content: flex-end;

    .n-button {
      width: 6.25rem;
      margin-left: 0.625rem;
    }
  }
}
</style>
