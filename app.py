from flask import Flask, request, jsonify, send_from_directory
import boto3
import pandas as pd

app = Flask(__name__)

# Load the movies dataset globally
movies_df = pd.read_csv('data/movies.csv')

# AWS Personalize client setup
personalize_runtime = boto3.client(
    'personalize-runtime',
    region_name='AWS_REGION',  # Replace with your AWS region
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_ACCESS_KEY'
)

CAMPAIGN_ARN = 'YOUR_CAMPAIGN_ARN_HERE'  # Replace this with your campaign arn


# Add the home route
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')  # Serve the HTML file


@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    # Get recommendations using AWS Personalize
    try:
        response = personalize_runtime.get_recommendations(
            campaignArn=CAMPAIGN_ARN,
            userId=user_id
        )
        # Extract the item list and take the top 2 recommendations
        item_list = response['itemList']

        if not item_list:
            return jsonify({'error': 'No recommendations found for this user ID.'}), 404

        top_recommendations = item_list[:5]  # Get the top 2 recommendations

        recommended_movies = []
        for item in top_recommendations:
            movie_id = item['itemId']
            score = item['score']  # Get the score
            # Convert to percentage (scaled for clarity)
            # score_percentage = round(score * 100000)

            # Fetch movie details from the movies dataset
            movie_details = movies_df[movies_df['ITEM_ID'] == int(movie_id)]
            if not movie_details.empty:
                title = movie_details['TITLE'].values[0]
                genre = movie_details['GENRE'].values[0]
                recommended_movies.append({
                    "item_id": movie_id,
                    "title": title,
                    "genre": genre,
                    "score": score
                })

        return jsonify({
            "user_id": user_id,
            "recommendations": recommended_movies
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
