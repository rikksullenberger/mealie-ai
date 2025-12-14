<template>
  <v-footer
    color="primary"
    padless
    app
  >
    <v-row
      justify="center"
      align="center"
      dense
      no-gutters
    >
      <v-col
        class="py-2 text-center white--text"
        cols="12"
      >
        <v-btn
          color="white"
          icon
          href="https://github.com/rikksullenberger/mealie-ai"
          target="_blank"
        >
          <v-icon>
            {{ $globals.icons.github }}
          </v-icon>
          <v-tooltip
            activator="parent"
            location="top"
          >
            View Source Code (AGPL-3.0)
          </v-tooltip>
        </v-btn>
        <a
          href="https://github.com/rikksullenberger/mealie-ai"
          target="_blank"
          class="white--text text-decoration-none ml-2"
        >
          Source Code
        </a>
        •
        {{ new Date().getFullYear() }} — <strong> Mealie AI </strong>
      </v-col>
    </v-row>
  </v-footer>
</template>

<script lang="ts">
export default defineNuxtComponent({
  setup() {
    return {};
  },
});
</script>
