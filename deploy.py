import os
import boto3
import time
import argparse
from botocore.exceptions import ClientError

def create_bucket_if_not_exists(s3_client, bucket_name, region=None):
    """Create an S3 bucket if it doesn't already exist"""
    try:
        if region is None:
            region = 'us-east-1'
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"Created bucket: {bucket_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"Bucket already exists: {bucket_name}")
        else:
            print(f"Error creating bucket: {e}")
            return False
    return True

def configure_website(s3_client, bucket_name):
    """Configure the bucket for website hosting"""
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
    try:
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=website_configuration
        )
        print(f"Configured bucket {bucket_name} for website hosting")
    except ClientError as e:
        print(f"Error configuring website: {e}")
        return False
    return True

def set_bucket_policy(s3_client, bucket_name):
    """Set bucket policy to allow public read access"""
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'PublicReadGetObject',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': f'arn:aws:s3:::{bucket_name}/*'
        }]
    }
    
    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name, 
            Policy=str(bucket_policy).replace("'", '"')
        )
        print(f"Set public read policy on {bucket_name}")
    except ClientError as e:
        print(f"Error setting bucket policy: {e}")
        return False
    return True

def generate_static_files():
    """Generate static HTML/CSS/JS files from the Flask app"""
    print("Generating static files...")
    
    # Create directories if they don't exist
    os.makedirs('dist', exist_ok=True)
    os.makedirs('dist/static/css', exist_ok=True)
    os.makedirs('dist/static/js', exist_ok=True)
    os.makedirs('dist/static/fonts', exist_ok=True)
    
    # Copy the latest messages.json to dist
    if os.path.exists('data/messages.json'):
        import shutil
        os.makedirs('dist/data', exist_ok=True)
        shutil.copy2('data/messages.json', 'dist/data/messages.json')
    
    # Copy font files if they exist
    import glob
    font_files = glob.glob('static/fonts/*')
    if font_files:
        for font_file in font_files:
            import shutil
            shutil.copy2(font_file, os.path.join('dist/static/fonts', os.path.basename(font_file)))
        print(f"Copied {len(font_files)} font files to dist/static/fonts")
    
    # Create a simple index.html that embeds the iframe code
    with open('dist/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord Discussions Embed</title>
    <style>
        body { margin: 0; padding: 0; font-family: sans-serif; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { margin-bottom: 30px; }
        .instructions { margin-bottom: 30px; }
        code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
        iframe { width: 100%; height: 600px; border: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Discord Discussions Embed</h1>
        <div class="instructions">
            <p>Below is a preview of the Discord discussions embed. To add this to your WordPress site, use the following iframe code:</p>
            <pre><code>&lt;iframe src="https://BUCKET_NAME.s3-website-REGION.amazonaws.com/discord.html" width="100%" height="600" frameborder="0" scrolling="yes"&gt;&lt;/iframe&gt;</code></pre>
        </div>
        <iframe src="discord.html"></iframe>
    </div>
</body>
</html>''')
    
    # Copy the templates/index.html to discord.html in dist
    with open('templates/index.html', 'r') as src:
        with open('dist/discord.html', 'w') as dst:
            # Read the template and modify paths to be relative
            content = src.read()
            content = content.replace('/static/', 'static/')
            dst.write(content)
    
    # Create a simple error page
    with open('dist/error.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error</title>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .error { text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="error">
        <h1>Oops!</h1>
        <p>Something went wrong. Please try again later.</p>
    </div>
</body>
</html>''')
    
    # Copy the static CSS and JS files
    with open('static/css/style.css', 'r') as src:
        with open('dist/static/css/style.css', 'w') as dst:
            dst.write(src.read())
    
    with open('static/js/script.js', 'r') as src:
        with open('dist/static/js/script.js', 'w') as dst:
            # Modify the API endpoint to use the JSON file directly
            content = src.read()
            content = content.replace("fetch('/api/discussions')", "fetch('data/messages.json')")
            content = content.replace("renderDiscussions(data.discussions)", 
                                    "const discussions = [];\n" +
                                    "    for (const channelId in data.channels) {\n" +
                                    "        const channel = data.channels[channelId];\n" +
                                    "        if (channel.messages && channel.messages.length > 0) {\n" +
                                    "            discussions.push(formatDiscussion(channelId, channel));\n" +
                                    "        }\n" +
                                    "    }\n" +
                                    "    renderDiscussions(discussions);")
            
            # Add a function to format the discussions
            content += "\n\nfunction formatDiscussion(channelId, channel) {\n" + \
                    "    const messages = channel.messages;\n" + \
                    "    const latestMessages = messages.slice(Math.max(messages.length - 5, 0));\n" + \
                    "    const latestTimestamp = new Date(latestMessages[0].timestamp);\n" + \
                    "    const hoursAgo = Math.floor((new Date() - latestTimestamp) / (1000 * 60 * 60));\n" + \
                    "    \n" + \
                    "    return {\n" + \
                    "        id: channelId,\n" + \
                    "        title: channel.name,\n" + \
                    "        category: channel.category,\n" + \
                    "        tags: [channel.category, channel.name],\n" + \
                    "        content: latestMessages[0].content,\n" + \
                    "        message_count: messages.length,\n" + \
                    "        reaction_count: latestMessages.reduce((total, msg) => total + msg.reactions.length, 0),\n" + \
                    "        time_ago: hoursAgo + 'h ago'\n" + \
                    "    };\n" + \
                    "}"
            
            dst.write(content)
            
    print("Static files generated in 'dist' directory")

def upload_directory(s3_client, directory_path, bucket_name):
    """Upload all files in directory to S3 bucket"""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, directory_path)
            s3_path = relative_path.replace('\\', '/')  # For Windows compatibility
            
            # Set the appropriate content type
            content_type = 'text/html'
            if s3_path.endswith('.css'):
                content_type = 'text/css'
            elif s3_path.endswith('.js'):
                content_type = 'application/javascript'
            elif s3_path.endswith('.json'):
                content_type = 'application/json'
            elif s3_path.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif s3_path.endswith('.png'):
                content_type = 'image/png'
            elif s3_path.endswith('.jpg') or s3_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
                
            try:
                s3_client.upload_file(
                    local_path, 
                    bucket_name, 
                    s3_path,
                    ExtraArgs={'ContentType': content_type}
                )
                print(f"Uploaded {local_path} to {bucket_name}/{s3_path}")
            except ClientError as e:
                print(f"Error uploading {local_path}: {e}")
                return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Deploy Discord bot UI to AWS S3')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    bucket_name = args.bucket
    region = args.region
    
    # Generate static files
    generate_static_files()
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name=region)
    
    # Create and configure bucket
    if not create_bucket_if_not_exists(s3_client, bucket_name, region):
        return
    
    if not configure_website(s3_client, bucket_name):
        return
    
    if not set_bucket_policy(s3_client, bucket_name):
        return
    
    # Upload files
    if not upload_directory(s3_client, 'dist', bucket_name):
        return
    
    # Get the website URL
    if region == 'us-east-1':
        website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
    else:
        website_url = f"http://{bucket_name}.s3-website.{region}.amazonaws.com"
    
    print("\nDeployment complete!")
    print(f"Website URL: {website_url}")
    print("\nTo embed in WordPress, use the following iframe code:")
    print(f'<iframe src="{website_url}/discord.html" width="100%" height="600" frameborder="0" scrolling="yes"></iframe>')

if __name__ == '__main__':
    main() 