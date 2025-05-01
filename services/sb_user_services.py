



def fetch_user_profile(supabase_client, user_id):
    """
    Fetches a user's profile from the Supabase user_profiles table.

    Args:
        supabase_client: The initialized Supabase client instance.
        user_id: The UUID of the user whose profile to fetch.

    Returns:
        A dictionary containing user profile data (user_id, onboarding_step)
        or None if the profile is not found or an error occurs.
    """
    if not user_id:
        return None

    try:
        # Query the user_profiles table for the profile matching the user_id
        response = supabase_client.table('user_profiles') \
            .select('user_id, onboarding_step') \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        # Supabase client might return data even if not found, check response structure
        # Adjust this check based on the exact behavior of your Supabase client version
        if response and response.data:
             return response.data
        else:
             return None

    except Exception as e:
        print(f"Error fetching user profile for ID {user_id} in helper: {e}")
        # In a real application, you might want more specific error handling
        return None