<template>
  <div class="create-graph-view">
    <n-flex vertical size="large">
      <n-layout has-sider sider-placement="left">
        <n-layout-sider collapse-mode="width" :collapsed-width="0" :width="200" show-trigger="arrow-circle" bordered>
          <div class="create-graph-view-sidebar">
            <n-button strong secondary type="primary" @click="showModal = true">
              创建对话
            </n-button>
            <div>
              <SessinList />
            </div>
          </div>
        </n-layout-sider>
        <n-layout-content content-style="padding: 10px;position:relative;z-index: 0;">
          <div class="chat-container" v-if="current_session.id">
            <div class="chat-message" ref="chatMessageDom">
              <div>
                <div v-for="item in message_list">
                  <div :class="item.role" v-if="item.role === 'user'">
                    <UserMessage :content="[{type:'text',content:item.message}]" />
                  </div>
                  <div :class="item.role" v-if="item.role === 'system'">
                    <AssistantMessage :content="[{type:'text',content:item.message}]" />
                  </div>
                </div>
              </div>
            </div>
            <div class="chat-box">
              <n-input v-model:value="textValue" round type="textarea" placeholder="给“ChatTuGraph”发送消息..."
                :autosize="{ minRows: 3, maxRows: 6 }" @keyup="handleKeydown" />
              <div class="send-btn">
                <n-button v-if="isLoadingMessage" circle icon-placement="right" @click="stopLoadMessage">
                  <template #icon>
                    <n-icon>
                      <PlayerStop />
                    </n-icon>
                  </template>
                </n-button>
                <n-button v-else circle icon-placement="right" @click="sendMessage">
                  <template #icon>
                    <n-icon>
                      <send />
                    </n-icon>
                  </template>
                </n-button>
              </div>
            </div>
          </div>
          <div v-else class="no-session-container">
            <n-empty size="large" description="请先创建一个对话">
              <template #icon>
                <n-icon>
                  <Robot />
                </n-icon>
              </template>
            </n-empty>
          </div>
        </n-layout-content>
       
      </n-layout>
    </n-flex>
    <n-modal v-model:show="showModal">
      <n-card style="width: 37.5rem" :bordered="false" size="medium" role="dialog" aria-modal="true">
        <SessionModal v-model:show="showModal" />
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import SessionModal from '@/components/session_modal.vue'
import SessinList from '@/components/session_list.vue'
import UserMessage from '@/components/user_message.vue'
import AssistantMessage from '@/components/assistant_message.vue'
import { createGraphService } from '@/services/create_graph'
import { useCreateGraphStore } from '@/stores/create_graph'
import { NLayout, NFlex, NLayoutSider, NLayoutContent, NButton, NModal, NCard, NInput, NIcon, NEmpty } from 'naive-ui'
import { Send, Robot, PlayerStop } from '@vicons/tabler'
import { parseContent } from '@/utils/parse_content'
const chatMessageDom = ref<HTMLDivElement | null>(null);
const createGraphStore = useCreateGraphStore()

let isLoadingMessage = ref(false)
let current_session = computed(() => {
  return createGraphStore.current_session
})
watch(current_session, async (newVal) => {
  if (newVal.id) {
    let res = await createGraphStore.getSessionHistory({ session_id: newVal.id })
    createGraphStore.updateMessageList(res)
  }
})


let message_list = computed(() => {
  return createGraphStore.message_list
})
watch(message_list, async () => {
  await nextTick();
  if (chatMessageDom.value) {
    chatMessageDom.value.scrollTop = chatMessageDom.value.scrollHeight;
  }
});
let showModal = ref(false)
let textValue = ref<string>('')

async function sendMessage() {
  const messages = [...message_list.value];
  const question = textValue.value
  textValue.value = ''
  if (question) {
    isLoadingMessage.value = true
    messages.push({ message: question, role: 'user' });
    createGraphStore.updateMessageList(messages)
    let { data } = await createGraphService.sendMessage({ message: question, session_id: current_session.value.id });
    createGraphStore.updateMessageList([...messages,data.assistant_message])
    isLoadingMessage.value = false
  }
}

function handleKeydown(event: KeyboardEvent) {
  const textarea = event.target as HTMLTextAreaElement;
  if (event.key === 'Enter') {
    if (event.altKey || event.metaKey) {
      sendMessage()
    } else {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = textarea.value;
      textarea.value = value.slice(0, start) + '\n' + value.slice(end);
      textarea.selectionStart = textarea.selectionEnd = start + 1;
      event.preventDefault()
    }
  }
}
function stopLoadMessage() {
  isLoadingMessage.value = false
}


</script>

<style scoped lang="less">
.create-graph-view {
  width: 100%;
  height: 100%;

  .n-flex,
  .n-layout {
    width: 100%;
    height: 100%;
  }

  .create-graph-view-sidebar {
    width: calc(100% - 1.25rem);
    height: calc(100% - 1.25rem);
    padding: 0.625rem;

    .n-button {
      width: 100%;
    }
  }

  .chat-container,
  .no-session-container {
    width: 100%;
    height: calc(100% - 6rem);
    overflow-y: auto;
  }

  .no-session-container {
    padding-top: 18.75rem;
    height: calc(100% - 18.75rem);
  }

  .chat-message {
    width: 100%;
    height: 100%;
    overflow-y: auto;
    scrollbar-width: none;
    /* Firefox */
  }

  .chat-message::-webkit-scrollbar {
    display: none;
    /* Chrome, Safari, Opera */
  }

  .user {
    width: 100%;
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.625rem;
  }

  .assistant {
    width: 100%;
    display: flex;
    justify-content: flex-start;
    margin-bottom: 0.625rem;
  }

  .chat-box {
    position: absolute;
    bottom: 0.625rem;
    width: calc(100% - 1.25rem);
    z-index: 1;

    .send-btn {
      position: absolute;
      right: 0.625rem;
      bottom: 0.625rem;
      cursor: pointer;
      z-index: 2;
    }
  }
}
</style>
