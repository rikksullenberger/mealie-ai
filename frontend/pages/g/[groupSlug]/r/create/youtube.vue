<template>
  <div>
    <v-form
      ref="domYouTubeForm"
      @submit.prevent="createFromYouTube(youtubeUrl)"
    >
      <div>
        <v-card-title class="headline">
          {{ $t('new-recipe.import-from-youtube') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('recipe.import-from-youtube-description') }}</p>
          <v-text-field
            v-model="youtubeUrl"
            :label="$t('new-recipe.youtube-url')"
            :prepend-inner-icon="$globals.icons.linkVariantPlus"
            validate-on="blur"
            autofocus
            variant="solo-filled"
            clearable
            class="rounded-lg mt-2"
            rounded
            :rules="[validators.url]"
            :hint="$t('new-recipe.youtube-url-hint')"
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
              :disabled="!youtubeUrl"
              rounded
              block
              type="submit"
              :loading="loading"
            >
              {{ loading ? $t('new-recipe.importing-from-youtube') : $t('new-recipe.import') }}
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

    const youtubeUrl = ref<string>("");
    const includeImage = ref<boolean>(false);
    const autoTag = ref<boolean>(false);
    const domYouTubeForm = ref<VForm | null>(null);

    function handleResponse(response: AxiosResponse<string> | null) {
      if (response?.status !== 201) {
        state.error = true;
        state.errorMessage = response?.data ? String(response.data) : "Failed to import recipe from YouTube";
        state.loading = false;
        return;
      }

      navigateToRecipe(response.data, groupSlug.value, `/g/${groupSlug.value}/r/create/youtube`);
    }

    async function createFromYouTube(url: string) {
      if (!url) {
        return;
      }

      if (!domYouTubeForm.value?.validate()) {
        return;
      }

      state.loading = true;
      state.error = false;
      state.errorMessage = "";

      try {
        const { response } = await api.recipes.createOneFromYouTube(url.trim(), includeImage.value, autoTag.value);
        handleResponse(response);
      } catch (error: any) {
        state.error = true;
        state.errorMessage = error?.response?.data?.detail?.message || error?.message || "Failed to import recipe from YouTube";
        state.loading = false;
      }
    }

    return {
      youtubeUrl,
      includeImage,
      autoTag,
      stayInEditMode,
      parseRecipe,
      domYouTubeForm,
      createFromYouTube,
      ...toRefs(state),
      validators,
    };
  },
});
</script>
