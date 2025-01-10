<template>
    <div class="analytic-modal-component">
        <n-card title="选择分析图谱">
            <n-form ref="formRef" :model="model" :rules="rules">
                <n-form-item path="ip" label="IP地址">
                    <n-input v-model:value="model.ip" />
                </n-form-item>
                <n-form-item path="port" label="端口">
                    <n-input v-model:value="model.port" />
                </n-form-item>
                <n-form-item path="user" label="账号">
                    <n-input v-model:value="model.user" />
                </n-form-item>
                <n-form-item path="pwd" label="密码">
                    <n-input v-model:value="model.pwd" />
                </n-form-item>
                <n-form-item path="graph_name" label="图名称（请确保图存在TuGraphDB中）">
                    <n-input v-model:value="model.graph_name" />
                </n-form-item>
            </n-form>
            <div style="display: flex; justify-content: flex-end">
                <n-button round type="primary" @click="createAnalySession" style="margin-right:0.625rem">
                    确认
                </n-button>
                <n-button round type="info" @click="closeModal(false)">
                    取消
                </n-button>
            </div>
        </n-card>
    </div>
</template>

<script setup lang="ts">
import { ref, defineEmits, defineProps } from 'vue'
import { useAnalyticGraphStore } from '@/stores/analytic_store'
import { useMessage, NForm, NFormItem, NInput, NSelect, NCard, NButton, type FormRules, type FormItemRule, type FormInst } from 'naive-ui'
const emit = defineEmits(['update:show'])
const analyticGraphStore = useAnalyticGraphStore()
const messageBox = useMessage()
const model = ref({
    ip: '127.0.0.1',
    port: '7687',
    user: 'admin',
    pwd: '73@TuGraph',
    graph_name: ''
})

const formRef = ref<FormInst | null>(null)
const rules: FormRules = {
    ip: [
        {
            required: true,
            validator(rule: FormItemRule, value: string) {
                if (!value) {
                    return new Error('请输入数据库IP地址')
                }
                return true
            },
            trigger: ['blur']
        }
    ],
    port: [
        {
            required: true,
            validator(rule: FormItemRule, value: string) {
                if (!value) {
                    return new Error('请输入数据库端口')
                }
                return true
            },
            trigger: ['blur']
        }
    ],
    user: [
        {
            required: true,
            validator(rule: FormItemRule, value: string) {
                if (!value) {
                    return new Error('请输入用户名')
                }
                return true
            },
            trigger: ['blur']
        }
    ],
    pwd: [
        {
            required: true,
            validator(rule: FormItemRule, value: string) {
                if (!value) {
                    return new Error('请输入密码')
                }
                return true
            },
            trigger: ['blur']
        }
    ],
    graph_name: [
        {
            required: true,
            validator(rule: FormItemRule, value: string) {
                if (!value) {
                    return new Error('请输入图名称')
                }
                return true
            },
            trigger: ['blur']
        }
    ]
}

function createAnalySession(e: MouseEvent) {
    e.preventDefault()
    formRef.value?.validate(async (errors) => {
        if (!errors) {
            let { success, message } = await analyticGraphStore.createSession(model.value)
            if (success) {
                let list = await analyticGraphStore.getSessions()
                analyticGraphStore.updateSessions(list)
                await analyticGraphStore.updateCurrentSession(list[0])
                closeModal(false)
                messageBox.success('导入成功')

                closeModal(false)
            } else {
                messageBox.error(message)
            }
        } else {
            messageBox.error('信息验证失败')
        }
    })
}
function closeModal(status: boolean) {
    emit('update:show', status)
}

</script>


<style scoped>
.analytic-modal-component {
    padding: 1.875rem;
}
</style>
