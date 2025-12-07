import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append("/opt/mealie/lib/python3.12/site-packages")

from mealie.db.db_setup import session_context
from mealie.repos.all_repositories import get_repositories
from mealie.services.recipe.recipe_service import OpenAIRecipeService
from mealie.lang.providers import local_provider

async def main():
    print("DEBUG: Starting verification script...")
    with session_context() as session:
        from mealie.db.models.users.users import User as UserModel
        user_model = session.query(UserModel).first()
        
        if not user_model:
            print("DEBUG: No users found!")
            return
            
        print(f"DEBUG: Using user {user_model.email} Group: {user_model.group_id}")
        
        # We need the Pydantic model for the service
        from mealie.schema.user.user import PrivateUser
        user = PrivateUser.model_validate(user_model)
        
        household = user_model.household
        
        # Test 1: Normal User context (with group_id in repo)
        repos = get_repositories(session, group_id=user.group_id, household_id=user.household_id)
        translator = local_provider("en-US")
        service = OpenAIRecipeService(repos, user, household, translator)
        
        slug = "bananna-nut-bread-cookies-2"
        print(f"DEBUG: Processing {slug} with Normal Context...")
        try:
            result = await service.auto_tag_recipe(slug)
            print("DEBUG: Normal Context Completed.")
        except Exception as e:
            print(f"DEBUG: Normal Context Failed: {e}")
            import traceback
            traceback.print_exc()

        # Test 2: Admin Context (NO group_id in repo) ~ SIMULATING THE BUG
        print("DEBUG: Simulating Admin Context (no group_id in repo)...")
        admin_repos = get_repositories(session, group_id=None, household_id=None)
        admin_service = OpenAIRecipeService(admin_repos, user, household, translator)
        
        try:
            # We use the same recipe, it should work now because we inject group_id from recipe
            result = await admin_service.auto_tag_recipe(slug)
            print("DEBUG: Admin Context Completed.")
        except Exception as e:
            print(f"DEBUG: Admin Context Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
