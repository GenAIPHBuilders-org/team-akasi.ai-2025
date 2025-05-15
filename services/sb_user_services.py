def fetch_user_profile(supabase_client, user_id):
    """
    Fetches a user's profile from the Supabase user_profiles table.

    Args:
        supabase_client: The initialized Supabase client instance.
        user_id: The UUID of the user whose profile to fetch.

    Returns:
        A dictionary containing user profile data (user_id, onboarding_step)
        or default values if the profile is not found or an error occurs.
    """
    if not user_id:
        return {'user_id': None, 'onboarding_step': 'personal_info'}

    try:
        # Query the user_profiles table for the profile matching the user_id
        response = supabase_client.table('user_profiles') \
            .select('*') \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        # Return the data or an empty dict with default values
        return response.data or {'user_id': user_id, 'onboarding_step': 'personal_info'}

    except Exception as e:
        print(f"Error fetching user profile for ID {user_id} in helper: {e}")
        # Return default values to keep app functional
        return {'user_id': user_id, 'onboarding_step': 'personal_info'}