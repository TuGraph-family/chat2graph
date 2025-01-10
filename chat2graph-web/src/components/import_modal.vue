<template>
    <div class="import-modal-component">
        <n-card title="数据库配置">
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
                <n-form-item path="graph_name" label="图名称">
                    <n-input v-model:value="model.graph_name" />
                </n-form-item>
            </n-form>
            <div style="display: flex; justify-content: flex-end">
                <n-button round type="primary" @click="importData" style="margin-right:0.625rem">
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
import { useMessage, NForm, NFormItem, NInput, NSelect, NCard, NButton, type FormRules, type FormItemRule, type FormInst } from 'naive-ui'
import { useCreateGraphStore } from '@/stores/create_graph'
const props = defineProps<{
    schema: {
        type: string;
        content: string;
    };
}>()
const emit = defineEmits(['update:show'])
const createGraphStore = useCreateGraphStore()
const messageBox = useMessage()
let graph_name = createGraphStore.current_session.session_name
const model = ref({
    ip: '127.0.0.1',
    port: '7687',
    user: 'admin',
    pwd: '73@TuGraph',
    graph_name: graph_name || ''
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
function extractJSON(str: string) {
    const cleanedStr = str.replace(/```json\s*|```/g, '');

    const jsonRegex = /{[\s\S]*}/;
    const match = cleanedStr.match(jsonRegex);
    if (match) {
        try {
            const jsonObject = JSON.parse(match[0]);
            return jsonObject;
        } catch (error) {
            console.error('Invalid JSON:', error);
            return null;
        }
    }
    console.error('No JSON found');
    return null;
}

function importData(e: MouseEvent) {
    e.preventDefault()
    formRef.value?.validate(async (errors) => {
        let data = extractJSON(props.schema.content)

        if (!data) {
            messageBox.error('不符合json标准')
            return
        }
        data = JSON.stringify(data)
        if (!errors) {
            if (props.schema.type === 'schema') {
                let { success, message } = await createGraphStore.importSchema({ ...model.value, schema: data })
                if (success) {
                    messageBox.success('导入成功')
                } else {
                    messageBox.error(message)
                }
            }
            if (props.schema.type === 'vertex') {
                let { success, message } = await createGraphStore.importVertex({ ...model.value, json_data: data })
                if (success) {
                    messageBox.success('导入成功')
                } else {
                    messageBox.error(message)
                }
            }
            if (props.schema.type === 'edge') {
                let { success, message } = await createGraphStore.importEdge({ ...model.value, json_data: data })
                if (success) {
                    messageBox.success('导入成功')
                } else {
                    messageBox.error(message)
                }
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
.import-modal-component {
    padding: 1.875rem;
}
</style>
