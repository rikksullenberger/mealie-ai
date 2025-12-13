<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card>
      <v-card-title class="headline">
        <v-icon start>mdi-creation</v-icon>
        Remix Recipe
        <v-spacer></v-spacer>
        <v-btn icon variant="text" @click="dialog = false"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>
      <v-card-text>
        <p class="mb-4 text-body-1">
          Generate a new variation of this recipe using AI. The original recipe will be preserved.
        </p>

        <v-text-field
            v-model="prompt"
            label="Instruction (e.g. 'Make it vegan', 'Spicy')"
            variant="outlined"
            autofocus
            hide-details="auto"
            class="mb-3"
            @keyup.enter="remix"
        ></v-text-field>
        
        <div class="d-flex flex-wrap gap-2 mb-4">
            <v-chip 
              v-for="p in presets" 
              :key="p.text" 
              @click="prompt = p.value"
              link
              color="primary"
              variant="outlined"
            >
              {{ p.text }}
            </v-chip>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
        <v-btn color="primary" @click="remix" :loading="loading" :disabled="!prompt">
          <v-icon start>mdi-wand</v-icon>
          Remix
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import { useUserApi } from "~/composables/api";
import { useRouter, useRoute } from "vue-router";
import { alert } from "~/composables/use-toast";

const props = defineProps<{
    slug: string
}>()

const dialog = defineModel<boolean>({ default: false })
const prompt = ref('')
const loading = ref(false)
const router = useRouter()
const route = useRoute()
const api = useUserApi();
const $auth = useMealieAuth();

const groupSlug = computed(() => (route.params.groupSlug as string) || $auth.user.value?.groupSlug || "");

const presets = [
  { text: 'Vegan', value: 'Make this recipe Vegan' },
  { text: 'Gluten Free', value: 'Make this recipe Gluten Free' },
  { text: 'Southwestern', value: 'Make this recipe Southwestern style' },
  { text: 'Healthy', value: 'Make a healthier version of this recipe' },
  { text: 'Keto', value: 'Make this recipe Keto friendly' },
];

const remix = async () => {
    if (!prompt.value) return;
    
    loading.value = true
    try {
        const { data: newSlug } = await api.recipes.remix(props.slug, prompt.value)
        dialog.value = false
        alert.success("Recipe Remix Successful!");
        
        console.log('Redirecting to:', `/g/${groupSlug.value}/r/${newSlug}`)
        await router.push(`/g/${groupSlug.value}/r/${newSlug}`)
        
        // Inform user that image is being generated
        setTimeout(() => {
            alert.info("AI image is being generated for this recipe. It will appear in a few seconds.");
        }, 500);
    } catch (e: any) {
        console.error("Remix failed", e);
        const detail = e.response?.data?.detail || "Failed to remix recipe";
        alert.error(detail);
    } finally {
        loading.value = false
    }
}
</script>
