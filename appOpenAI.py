from flask import Flask, render_template, request, jsonify, send_file
import openai
import uuid
import io

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = ''

# Simple in-memory cache
html_cache = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_html():
    prompt = request.json['prompt']
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates HTML, Javascript and CSS code."},
                {"role": "user", "content": f"Generate HTML, Javascript and CSS for a webpage that {prompt}. Provide only the code, no explanations. All CSS and Javascript are written in the same HTML body"}
            ]
        )
        
        generated_html = response.choices[0].message['content']
        
        # Generate a unique key for this HTML
        cache_key = str(uuid.uuid4())
        
        # Store the generated HTML in the cache
        html_cache[cache_key] = generated_html
        
        print(f"Generated HTML cached with key: {cache_key}")
        
        return jsonify({'html': generated_html, 'cacheKey': cache_key})
    except openai.error.OpenAIError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit', methods=['POST'])
def edit_html():
    cache_key = request.json['cacheKey']
    edit_instruction = request.json['instruction']
    selected_html = request.json['selectedHTML']
    selected_css = request.json['selectedCSS']

    # Retrieve the original HTML from the cache
    original_html = html_cache.get(cache_key)
    if not original_html:
        return jsonify({'error': 'Original HTML not found in cache'}), 404

    try:
        # Use OpenAI to edit the HTML
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that edits HTML and CSS code based on instructions."},
                {"role": "user", "content": f"""
                Original full HTML:
                {original_html}

                Selected element HTML:
                {selected_html}

                Selected element CSS:
                {selected_css}

                Edit instruction: {edit_instruction}

                Please make the requested changes to the selected HTML and CSS based on the edit instruction.
                Then, incorporate these changes into the full HTML. Provide only the modified full HTML code, no explanations.
                """}
            ]
        )
        
        edited_html = response.choices[0].message['content']
        
        # Update the cache with the edited HTML
        html_cache[cache_key] = edited_html
        
        return jsonify({'html': edited_html, 'cacheKey': cache_key})
    except openai.error.OpenAIError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/export', methods=['GET'])
def export_html():
    cache_key = request.args.get('cacheKey')
    if not cache_key or cache_key not in html_cache:
        return jsonify({'error': 'Invalid or missing cache key'}), 400
    
    html_content = html_cache[cache_key]
    
    # Create a file-like object in memory
    mem_file = io.BytesIO()
    mem_file.write(html_content.encode('utf-8'))
    mem_file.seek(0)
    
    return send_file(
        mem_file,
        as_attachment=True,
        download_name='exported_webpage.html',
        mimetype='text/html'
    )

@app.route('/cache-imported', methods=['POST'])
def cache_imported_html():
    data = request.json
    html_content = data.get('html')
    cache_key = data.get('cacheKey')
    
    if not html_content or not cache_key:
        return jsonify({'success': False, 'error': 'Missing HTML content or cache key'}), 400
    
    html_cache[cache_key] = html_content
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)