<template>
  <div class="home">
    <div class="sidebar-container">
      <Sidebar />
    </div>
    <div class="content-container">
      <Content />
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue';
import Content from '@/components/Content.vue';
</script>

<style scoped>
.home {
  display: flex;
  width: 100%;
  height: 100%;
}

.sidebar-container {
  width: 250px;
  border-right: 1px solid #ccc;
}

.content-container {
  flex: 1;
  padding: 16px;
}
</style>
