<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { NConfigProvider, NLayout, NFlex, NLayoutSider, NLayoutContent, NMessageProvider, darkTheme } from 'naive-ui'
const route = useRoute()
const includeSider = computed(() => {
  return !['/LoginView', '/ConfigSetting'].includes(route.path)
})
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <div class="layout">
        <n-flex vertical size="large">
          <n-layout has-sider>
            <!-- <n-layout-sider v-if="includeSider" collapse-mode="width" :collapsed-width="0" :width="200"
              show-trigger="arrow-circle" bordered>
              <SidebarMenu />
            </n-layout-sider> -->
            <n-layout-content>
              <RouterView />
            </n-layout-content>
          </n-layout>
        </n-flex>
      </div>
    </n-message-provider>
  </n-config-provider>
</template>

<style scoped lang="less">
.layout,
.n-config-provider {
  width: 100%;
  height: 100%;

  .n-flex,
  .n-layout {
    width: 100%;
    height: 100%;
  }

  .layout-sidebar {
    width: 100%;
    height: 100%;
  }
}
</style>
