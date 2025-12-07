<template>
  <div>
    <v-form
      ref="domAiForm"
      @submit.prevent="generateRecipe(prompt)"
    >
      <div>
        <v-card-title class="headline">
          {{ $t('new-recipe.generate-with-ai') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('new-recipe.generate-with-ai-description') }}</p>
          <v-textarea
            v-model="prompt"
            :label="$t('new-recipe.describe-recipe-hint')"
            :prepend-inner-icon="$globals.icons.robot"
            validate-on="blur"
            autofocus
            variant="solo-filled"
            clearable
            class="rounded-lg mt-2"
            rounded
            rows="4"
            :rules="[validators.required]"
            :hint="$t('new-recipe.describe-recipe-hint')"
            persistent-hint
          />
        </v-card-text>
        <v-checkbox
          v-model="stayInEditMode"
          color="primary"
          hide-details
          :label="$t('recipe.stay-in-edit-mode')"
        />
        <v-checkbox
          v-model="parseRecipe"
          color="primary"
          hide-details
          :label="$t('recipe.parse-recipe-ingredients-after-import')"
        />
        <v-checkbox
          v-model="includeImage"
          color="primary"
          hide-details
          :label="$t('new-recipe.generate-image')"
        />
        <v-checkbox
          v-model="autoTag"
          color="primary"
          hide-details
          :label="$t('new-recipe.auto-tag-recipe')"
        />
        <v-card-actions class="justify-center">
          <div style="width: 250px">
            <BaseButton
              :disabled="!prompt"
              rounded
              block
              type="submit"
              :loading="loading"
            >
              {{ loading ? $t('new-recipe.generating') : $t('new-recipe.generate') }}
            </BaseButton>
          </div>
        </v-card-actions>
      </div>
    </v-form>
    <v-expand-transition>
      <v-alert
        v-if="error"
        color="error"
        class="mt-6 white--text"
      >
        <v-card-title class="ma-0 pa-0">
          <v-icon
            start
            color="white"
            size="x-large"
          >
            {{ $globals.icons.alertCircle }}
          </v-icon>
          {{ $t("general.exception") }}
        </v-card-title>
        <v-divider class="my-3 mx-2" />
        <p>
          {{ errorMessage }}
        </p>
      </v-alert>
    </v-expand-transition>
  </div>
</template>

<script lang="ts">
import type { AxiosResponse } from "axios";
import { useUserApi } from "~/composables/api";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import { validators } from "~/composables/use-validators";
import type { VForm } from "~/types/auto-forms";

export default defineNuxtComponent({
  setup() {
    definePageMeta({
      key: route => route.path,
    });
    const state = reactive({
      error: false,
      errorMessage: "",
      loading: false,
    });

    const $auth = useMealieAuth();
    const api = useUserApi();
    const route = useRoute();
    const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");

    const {
      stayInEditMode,
      parseRecipe,
      navigateToRecipe,
    } = useNewRecipeOptions();

    const prompt = ref<string>("");
    const includeImage = ref<boolean>(false);
    const autoTag = ref<boolean>(false);

    function handleResponse(response: AxiosResponse<string> | null) {
      if (response?.status !== 201) {
        state.error = true;
        state.errorMessage = response?.data ? String(response.data) : "Failed to generate recipe";
        state.loading = false;
        return;
      }

      navigateToRecipe(response.data, groupSlug.value, `/g/${groupSlug.value}/r/create/ai`);
    }

    const domAiForm = ref<VForm | null>(null);

    async function generateRecipe(userPrompt: string) {
      if (!userPrompt) {
        return;
      }

      if (!domAiForm.value?.validate()) {
        return;
      }

      state.loading = true;
      state.error = false;
      state.errorMessage = "";

      try {
        const { response } = await api.recipes.createOneFromAI(userPrompt, includeImage.value, autoTag.value);
        handleResponse(response);
      } catch (error: any) {
        state.error = true;
        state.errorMessage = error?.response?.data?.detail?.message || error?.message || "Failed to generate recipe";
        state.loading = false;
      }
    }

    return {
      prompt,
      includeImage,
      autoTag,
      stayInEditMode,
      parseRecipe,
      domAiForm,
      generateRecipe,
      ...toRefs(state),
      validators,
    };
  },
});
</script>
