<template>
  <div class="siderbar-menu-component">
    <div class="logo">Chat TuGraph</div>
    <n-menu v-model:value="activeKey" :options="menuOptions" />
    <div class="setting">
      <n-icon size="30" @click="changeTheme">
        <moon-stars v-if="configStore.theme === 'light'" />
        <sun v-if="configStore.theme === 'dark'" />
      </n-icon>
      <n-icon size="30" @click="viewSetting">
        <settings />
      </n-icon>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watchEffect, h } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { NIcon, NMenu } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import type { Component } from 'vue'
import { MoonStars, Settings, Sun } from '@vicons/tabler'
import { useConfigStore } from '@/stores/config_setting'
const configStore = useConfigStore()
const route = useRoute()
const router = useRouter()
let activeKey = ref<string | null>('CreateGraph')
const menuOptions: MenuOption[] = [
  //   {
  //   label: () => h(
  //     RouterLink,
  //     {
  //       to: {
  //         name: 'InstallDB'
  //       }
  //     },
  //     { default: () => '安装部署' }
  //   ),
  //   key: 'InstallDB'
  // },
  {
    label: () => h(
      RouterLink,
      {
        to: {
          name: 'CreateGraph'
        }
      },
      { default: () => '构图助手' }
    ),
    key: 'CreateGraph'
  }, {
    label: () => h(
      RouterLink,
      {
        to: {
          name: 'AnalysisGraph'
        }
      },
      { default: () => '分析助手' }
    ),
    key: 'AnalysisGraph'
  },
  //  {
  //   label: () => h(
  //     RouterLink,
  //     {
  //       to: {
  //         name: 'ExportSolution'
  //       }
  //     },
  //     { default: () => '导出方案' }
  //   ),
  //   key: 'ExportSolution'
  // }
]

watchEffect(() => {
  activeKey.value = route.name as string;
});

function changeTheme() {
  let theme: "dark" | "light" = configStore.theme === 'light' ? 'dark' : 'light'
  configStore.updateTheme(theme)
}

function viewSetting() {
  router.push({ name: 'ConfigSetting' })
}
</script>

<style scoped lang="less">
.siderbar-menu-component {
  width: calc(100% - 1.25rem);
  height: calc(100% - .625rem);
  padding: .3125rem .625rem;
  position: relative;
}

.logo {
  padding: 1.25rem;
  font-size: 1.3em;
  text-align: center;
  font-weight: bold;
  white-space: nowrap;
}

.setting {
  position: absolute;
  bottom: 0;
  width: calc(100% - 1.25rem);
  height: 3.75rem;
  display: flex;
  align-items: center;
  justify-content: center;

  .n-icon {
    cursor: pointer;
    margin: 0 0.625rem;
  }
}
</style>
