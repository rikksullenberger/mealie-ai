<template>
  <BaseDialog
    v-model="showDialog"
    :title="$t('recipe.generate-image')"
    :icon="$globals.icons.autoFix"
    width="500"
  >
    <v-card-text>
      <p class="mb-2">
        {{ $t('recipe.generate-image-description') }}
      </p>

      <v-textarea
        v-model="prompt"
        :label="$t('recipe.generate-image-hint')"
        :prepend-inner-icon="$globals.icons.robot"
        variant="outlined"
        rows="3"
        auto-grow
        hide-details="auto"
        class="mb-3"
      />
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <BaseButton
        text
        @click="showDialog = false"
      >
        {{ $t('general.cancel') }}
      </BaseButton>
      <BaseButton
        color="primary"
        :loading="loading"
        :disabled="!prompt"
        @click="generate"
      >
        {{ $t('new-recipe.generate') }}
      </BaseButton>
    </v-card-actions>
  </BaseDialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";

const props = defineProps<{
  slug: string;
}>();

const emit = defineEmits<{
  (e: "image-updated", key: string): void;
}>();

const showDialog = defineModel<boolean>({ default: false });

const api = useUserApi();
const i18n = useI18n();

const prompt = ref("");
const loading = ref(false);

async function generate() {
  loading.value = true;
  try {
    const response = await api.recipes.regenerateAiImage(props.slug, prompt.value);
    emit("image-updated", response.data);
    showDialog.value = false;
    alert.success(i18n.t("recipe.recipe-image-updated"));
  }
  catch (e: any) {
    alert.error(e.response?.data?.detail?.message || i18n.t("general.error"));
  }
  finally {
    loading.value = false;
  }
}
</script>
