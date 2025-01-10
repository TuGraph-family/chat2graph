<template>
    <div class="assistant-message">
        <div class="icon">
            <n-avatar round size="large" :src="assistantImg" />
        </div>
        <div class="content">
            <n-card embedded>
                <div v-for="(item, index) in content" :key="index">
                    <div v-if="item.type === 'text'" class="markdown-body" v-html="renderMarkdown(item.content)"></div>
                    <div v-else class="json-content">
                        <n-tag type="warning">
                            {{ item.type.toUpperCase() }}
                        </n-tag>
                        <div style="position: absolute; top: 0.625rem;right: 0.625rem;">
                            <n-button type="primary"
                                @click="importToGraph({ type: item.type, content: item.content })">导入</n-button>
                        </div>
                        <pre v-html="highlightJson(item.content)"></pre>
                    </div>
                </div>
            </n-card>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { defineProps, ref } from 'vue'
import { NAvatar, NCard, NTag, NButton, NModal } from 'naive-ui'
import assistantImg from '../assets/assistant.png'
import hljs from 'highlight.js'
import { marked } from 'marked'
import 'highlight.js/styles/monokai-sublime.css'
import 'github-markdown-css/github-markdown.css'
const props = defineProps<{
    content: { type: 'text' | 'schema' | 'vertex' | 'edge', content: string }[]
}>()
let showModal = ref(false)
let importData = ref({ type: '', content: '' })
function highlightJson(content: string) {
    try {
        const json = JSON.parse(content)
        const jsonString = JSON.stringify(json, null, 2)
        return hljs.highlight(jsonString, { language: 'json' }).value
    } catch (e) {
        return hljs.highlight(content, { language: 'json' }).value
    }
}
function renderMarkdown(content: string) {
    return marked(content)
}
function importToGraph(data: { type: string, content: string }) {
    showModal.value = true
    importData.value = data
}
</script>

<style scoped lang="less">
.assistant-message {
    padding: 20px;
    border-radius: 8px;
    display: flex;
    width: 90%;
    // flex-grow: 0;
}

.icon {
    flex-shrink: 0;
}

.content {
    margin-left: 0.625rem;
    min-width: 70%;
}

.assistant-message .content-item {
    margin-bottom: 0.625rem;
}

.assistant-message .text {
    font-size: 0.875rem;
    color: #333;
}

.assistant-message .schema,
.assistant-message .vertex,
.assistant-message .edge {
    font-family: monospace;
    padding: 0.625rem;
    border-radius: 0.25rem;
}

.json-content {
    font-family: monospace;
    background-color: #2e2e2e;
    padding: 0.625rem;
    border-radius: 0.25rem;
    color: #ccc;
    margin: 10px 0;
    max-height: 400px;
    overflow-y: auto;
    position: relative;

    &::-webkit-scrollbar {
        display: none;
        /* Chrome, Safari, Opera */
    }
}

pre {
    background: #2e2e2e;
    padding: 10px;
    border-radius: 5px;
    overflow: auto;
    font-family: monospace;
}

.markdown-body {
    font-family: Arial, sans-serif;
    padding: 0.625rem;
    border-radius: 0.25rem;
    margin: 10px 0;
    max-height: 400px;
    overflow-y: auto;
    background-color: unset;
    color: unset;
    word-wrap: break-word;
    word-break: break-all;

    &::-webkit-scrollbar {
        display: none;
        /* Chrome, Safari, Opera */
    }
}
</style>
