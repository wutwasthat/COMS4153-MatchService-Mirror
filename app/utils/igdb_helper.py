import requests

# Replace these with your own client ID and access token
CLIENT_ID = "lypkh207hr1yfpu07yj2fhwkdon3e3"
ACCESS_TOKEN = "949cfj21cqlggvn5jt6nbnxvlrmxgy"

headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "text/plain"
}
url = "https://api.igdb.com/v4/games"

def fetch_games_data(limit=500, genre=None):
    """
    Fetches game data from the IGDB API based on the specified limit and genre.

    Args:
        limit (int): The maximum number of games to fetch.
        genre (str): The genre to filter games by (optional).

    Returns:
        list[dict]: A list of dictionaries, each containing details about a game.
    """
    # Base query with required fields
    query = f"""
    fields id, name, summary, genres.name, cover.image_id, multiplayer_modes.*; 
    where multiplayer_modes.onlinemax = 2 | multiplayer_modes.offlinemax = 2; 
    limit {limit};
    """
    if genre:
        query += f'where genres.name = "{genre}";'

    # Make the API request
    response = requests.post(url, headers=headers, data=query)

    # Check response status and parse data
    if response.status_code == 200:
        game_data = response.json()
        games_info = []
        for game in game_data:
            # Extract game details
            game_id = game['id']
            name = game['name']
            description = game.get('summary', 'No description available')
            genres = [genre['name'] for genre in game.get('genres', [])]
            
            # Construct image URL
            cover_image_id = game.get('cover', {}).get('image_id')
            image_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover_image_id}.jpg" if cover_image_id else "No image available"
            
            # Append game info to list
            games_info.append({
                "id": game_id,
                "name": name,
                "description": description,
                "genres": genres,
                "image_url": image_url
            })

        return games_info
    else:
        print(f"Failed to fetch data: {response.status_code} - {response.text}")
        return []
