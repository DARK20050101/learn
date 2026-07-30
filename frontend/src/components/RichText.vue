<script setup lang="ts">
import { computed } from 'vue'
import katex from 'katex'

const props = withDefaults(defineProps<{ text: string | null | undefined; block?: boolean }>(), {
  block: false,
})

function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;').replaceAll('\n', '<br>')
}

function safeImageUrl(value: string) {
  const url = value.trim()
  return /^(https?:\/\/|\/)/i.test(url) ? url : ''
}

function render(value: string) {
  const pattern = /(!\[[^\]\n]*\]\([^)]+\)|\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g
  let cursor = 0
  let html = ''
  for (const match of value.matchAll(pattern)) {
    const index = match.index ?? 0
    html += escapeHtml(value.slice(cursor, index))
    const token = match[0]
    if (token.startsWith('![')) {
      const image = /^!\[([^\]\n]*)\]\(([^)]+)\)$/.exec(token)
      const url = image ? safeImageUrl(image[2]) : ''
      html += url
        ? `<img class="question-image" src="${escapeHtml(url)}" alt="${escapeHtml(image?.[1] ?? '')}" loading="lazy">`
        : escapeHtml(token)
      cursor = index + token.length
      continue
    }
    const displayMode = token.startsWith('$$')
    const expression = token.slice(displayMode ? 2 : 1, displayMode ? -2 : -1)
    html += katex.renderToString(expression, {
      displayMode, output: 'html', strict: false, throwOnError: false, trust: false,
    })
    cursor = index + token.length
  }
  return html + escapeHtml(value.slice(cursor))
}

const html = computed(() => render(props.text ?? ''))
</script>

<template>
  <component :is="block ? 'div' : 'span'" class="rich-text" v-html="html"/>
</template>

<style scoped>
.rich-text :deep(.katex-display) {
  margin: 0.75rem 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.25rem 0;
}
.rich-text :deep(.katex) { font-size: 1em; }
.rich-text :deep(.question-image) {
  display: block;
  width: auto;
  max-width: 100%;
  max-height: 70vh;
  margin: 1rem auto;
  border-radius: 0.875rem;
  object-fit: contain;
}
</style>
