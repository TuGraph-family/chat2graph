<template>
    <div class="user-message">
        <div class="content">
            <n-card>
                <div v-for="(item, index) in content" :key="index">
                    {{ item.content }}
                </div>
            </n-card>
        </div>
        <div class="icon">
            <n-avatar round size="large" :src="userImg" />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { defineProps } from 'vue'
import { NAvatar, NCard } from 'naive-ui'
import userImg from '../assets/user.png'


// 定义接收的外部参数
const props = defineProps<{
    content: { type: 'text' | 'schema' | 'vertex' | 'edge', content: string }[]
}>()

</script>

<style scoped lang="less">
.user-message {
    padding: 20px;
    border-radius: 8px;
    display: flex;
}

.icon {
    flex-shrink: 0;
}

.content {
    margin-right: 0.625rem;
}

.user-message .content-item {
    margin-bottom: 0.625rem;
}

.user-message .text {
    font-size: 0.875rem;
    color: #333;
}

.user-message .schema,
.user-message .vertex,
.user-message .edge {
    font-family: monospace;
    background-color: #e6e6e6;
    padding: 0.625rem;
    border-radius: 0.25rem;
    color: #444;
}
</style>
