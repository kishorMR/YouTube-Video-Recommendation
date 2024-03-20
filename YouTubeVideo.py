# Add necessary imports
from googleapiclient.discovery import build
from textblob import TextBlob 
from IPython.display import HTML

# Add your YouTube API key
Api_key = 'Your Key'

# Define score_comments function
def score_comments(comments):
    # Calculate sentiment score of comments
    comments_text = ' '.join(comments)
    sentiment_score = TextBlob(comments_text).sentiment.polarity

    # Define keywords and calculate keyword score
    keyword_score = sum(1 for keyword in keywords if keyword in comments_text.lower())

    # Calculate overall comments score
    comments_score = (0.6 * sentiment_score) + (0.4 * keyword_score)
    return comments_score

# Define score_video function
def score_video(video_info, suggested_video_links, min_views, max_views):
    max_score = float('-inf')
    best_video_info = None
    best_link = None

    # Iterate through suggested videos
    for i, link in enumerate(suggested_video_links):
        # Calculate normalized views
        views = int(video_info[i]['views']) if video_info[i]['views'] != 'N/A' else 0
        n_views = (views - min_views) / (max_views - min_views)

        # Calculate comments score
        comments_score = score_comments(video_info[i]['comments_list'])
        
        # Calculate final score
        final_score = (0.3 * n_views) + (0.2 * (likes / views if views != 0 else 0)) + (0.1 * (comments / views if views != 0 else 0)) + (0.4 * comments_score)
        
        if final_score > max_score:
            max_score = final_score
            best_video_info = video_info[i]
            best_link = link

    return best_video_info, max_score, best_link

# Try block to catch errors
try:
    # Build YouTube API service
    youtube = build('youtube', 'v3', developerKey=Api_key)

    # Get user input for search query
    search_query = input('Enter search query: ')

    # Make search request to YouTube API
    search_request = youtube.search().list(
        q=search_query,
        part='snippet',
        type='video',
        maxResults=10
    )
    search_response = search_request.execute()

    # Extract video IDs from search response
    video_ids = [item['id']['videoId'] for item in search_response['items']]

    # Initialize list to store video information
    videos_info = []

    # Loop through each video ID to get video information
    for video_id in video_ids:
        # Make video request to YouTube API
        video_request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        video_response = video_request.execute()
        video_info = video_response['items'][0]

        # Extract relevant video information
        video_title = video_info['snippet']['title']
        video_duration = video_info['contentDetails']['duration']
        video_likes = video_info['statistics'].get('likeCount', 'N/A')
        video_comments = video_info['statistics'].get('commentCount', 'N/A')
        video_views = video_info['statistics'].get('viewCount', 'N/A')

        # Make comments request to get video comments
        comments_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=None
        )
        comments_response = comments_request.execute()
        video_comments_list = [comment['snippet']['topLevelComment']['snippet']['textDisplay'] for comment in comments_response['items']]

        # Append video information to videos_info list
        videos_info.append({'id': video_id, 'title': video_title, 'duration': video_duration, 'likes': video_likes, 'comments': video_comments, 'comments_list': video_comments_list, 'views': video_views})

    # Calculate min and max views
    min_views = min(int(video_info['views']) for video_info in videos_info)
    max_views = max(int(video_info['views']) for video_info in videos_info)

    # Generate suggested video links
    suggested_video_links = ['https://www.youtube.com/watch?v=' + video_id for video_id in video_ids]

    # Score videos and find the best one
    best_video_info, max_score, best_link = score_video(videos_info, suggested_video_links, min_views, max_views)

    # Print information about the best video
    print("Best Video:")
    print("Title:", best_video_info['title'])
    print("Duration:", best_video_info['duration'])
    print("Likes:", best_video_info['likes'])
    print("Comments:", best_video_info['comments'])
    print("Views:", best_video_info['views'])
    print("Link:", best_link)
    print("Score:", max_score)

except Exception as e:
    # Handle exceptions
    print('An error occurred:', str(e))

# Embed the best video using HTML iframe
best_video_id = best_video_info['id']
display(HTML(f"""<iframe width="560" height="315" src="https://www.youtube.com/embed/{best_video_id}" frameborder="0" allowfullscreen></iframe>"""))
