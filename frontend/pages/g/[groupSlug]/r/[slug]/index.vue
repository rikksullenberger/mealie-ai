<template>
  <div>
    <RecipePage
      v-if="recipe"
      v-model="recipe"
    />
  </div>
</template>

<script setup lang="ts">
import { whenever } from "@vueuse/core";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useAsyncKey } from "~/composables/use-utils";
import RecipePage from "~/components/Domain/Recipe/RecipePage/RecipePage.vue";
import { usePublicExploreApi } from "~/composables/api/api-client";
import { useRecipe } from "~/composables/recipes";
import type { Recipe } from "~/lib/api/types/recipe";
import { usePageState, PageMode } from "~/composables/recipe-page/shared-state";

const $auth = useMealieAuth();
const { isOwnGroup } = useLoggedInState();
const route = useRoute();
const title = ref(route.meta?.title as string || "");
useSeoMeta({ title });

const router = useRouter();
const slug = route.params.slug as string;

const recipe = ref<Recipe | null>(null);
function loadRecipe() {
  const { recipe: data } = useRecipe(slug);
  watch(data, (value) => {
    recipe.value = value;
  });
}

async function loadPublicRecipe() {
  const groupSlug = computed(() => route.params.groupSlug as string || $auth.user.value?.groupSlug || "");
  const api = usePublicExploreApi(groupSlug.value);
  const { data } = await useAsyncData(useAsyncKey(), async () => {
    const { data, error } = await api.explore.recipes.getOne(slug);
    if (error) {
      console.error("error loading recipe -> ", error);
      router.push(`/g/${groupSlug.value}`);
    }

    return data;
  });
  recipe.value = data.value;
}

if (isOwnGroup.value) {
  loadRecipe();
}
else {
  onMounted(loadPublicRecipe);
}

// Check for edit query parameter and enter edit mode if present
const pageState = usePageState(slug);
onMounted(() => {
  if (route.query.edit === "true") {
    pageState.setMode(PageMode.EDIT);
  }
});

whenever(
  () => recipe.value,
  () => {
    if (recipe.value && recipe.value.name) {
      title.value = recipe.value.name;
    }
  },
);
</script>
