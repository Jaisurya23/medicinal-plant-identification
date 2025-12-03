from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, create_user, verify_password, save_dataset, get_all_datasets, get_all_users, add_plant, get_all_plants, get_plant_by_id, update_plant, delete_plant, get_plant_by_name
import os
from werkzeug.utils import secure_filename
from train_model import train_medicinal_plant_model
from datetime import datetime
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random key in production

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'zip'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Model and dataset paths
DATASET_PATH = "dataset/"
MODEL_PATH = "models/plant_model.h5"
LABELS_PATH = "models/labels.json"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists('static'):
    os.makedirs('static')

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize database on app startup
init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm')
        
        # Validate input
        if not all([name, email, username, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('user_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('user_register.html')
        
        # Create user in database
        success, message = create_user(username, email, name, password)
        
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('user_login'))
        else:
            flash(message, 'error')
            return render_template('user_register.html')
    
    return render_template('user_register.html')

@app.route('/register_sucess')
def register_success():
    return render_template('register_complete.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
      # In production, use environment variables or a secure method
    if request.method == 'POST':
        username = 'admin'
        password = 'admin'
        username = request.form.get('username')
        password = request.form.get('password')

        # Here you would normally validate the admin credentials
        print("Admin Username:", username)
        print("Admin Password:", password)
        if username != 'admin' or password != 'admin':
            flash('Invalid admin credentials.', 'error')
            return render_template('admin_login.html')

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('user_login.html')
        
        # Verify credentials against database
        success, result = verify_password(username, password)
        
        if success:
            session['user_id'] = result['id']
            session['username'] = result['username']
            session['name'] = result['name']
            flash(f'Welcome, {result["name"]}!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash(result, 'error')  # result contains error message
            return render_template('user_login.html')
    
    return render_template('user_login.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('user_login'))
    
    return render_template('user_dashboard.html', name=session.get('name'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/admin_dashboard')
def admin_dashboard():
    """Admin dashboard - shows admin control panel."""
    # Note: In production, implement proper admin authentication
    return render_template('admin_dashboard.html')

@app.route('/admin/view_users')
def view_users():
    """View all registered users."""
    users = get_all_users()
    return render_template('admin_view_user.html', users=users)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/upload_dataset', methods=['GET', 'POST'])
def upload_dataset():
    if request.method == 'POST':
        # Check if file is in request
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return render_template('admin_upload_dataset.html')
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('admin_upload_dataset.html')
        
        if not allowed_file(file.filename):
            flash(f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
            return render_template('admin_upload_dataset.html')
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            flash(f'File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f} MB limit.', 'error')
            return render_template('admin_upload_dataset.html')
        
        # Save file
        original_filename = secure_filename(file.filename)
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + original_filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            
            # Save to database
            username = session.get('username', 'admin')
            success, message = save_dataset(filename, original_filename, filepath, file_size, username)
            
            if success:
                flash(f'File "{original_filename}" uploaded successfully!', 'success')
                return redirect(url_for('upload_dataset'))
            else:
                flash(message, 'error')
                return render_template('admin_upload_dataset.html')
        
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
            return render_template('admin_upload_dataset.html')
    
    # GET request - show upload form with existing datasets
    datasets = get_all_datasets()
    return render_template('admin_upload_dataset.html', datasets=datasets)

@app.route('/admin/manage_plants', methods=['GET', 'POST'])
def manage_plants():
    if request.method == 'POST':
        plant_name = request.form.get('plant_name')
        botanical_name = request.form.get('botanical_name')
        benefits = request.form.get('benefits')
        
        # Validate input
        if not all([plant_name, botanical_name, benefits]):
            flash('All fields are required.', 'error')
            plants = get_all_plants()
            return render_template('admin_manage_plants.html', plants=plants)
        
        # Add plant to database
        success, message = add_plant(plant_name, botanical_name, benefits)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('manage_plants'))
        else:
            flash(message, 'error')
            plants = get_all_plants()
            return render_template('admin_manage_plants.html', plants=plants)
    
    # GET request - show all plants
    plants = get_all_plants()
    return render_template('admin_manage_plants.html', plants=plants)

@app.route('/admin/manage_plants/edit/<int:plant_id>', methods=['GET', 'POST'])
def edit_plant(plant_id):
    plant = get_plant_by_id(plant_id)
    
    if plant is None:
        flash('Plant not found.', 'error')
        return redirect(url_for('manage_plants'))
    
    if request.method == 'POST':
        plant_name = request.form.get('plant_name')
        botanical_name = request.form.get('botanical_name')
        benefits = request.form.get('benefits')
        
        # Validate input
        if not all([plant_name, botanical_name, benefits]):
            flash('All fields are required.', 'error')
            return render_template('admin_edit_plant.html', plant=plant)
        
        # Update plant in database
        success, message = update_plant(plant_id, plant_name, botanical_name, benefits)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('manage_plants'))
        else:
            flash(message, 'error')
            return render_template('admin_edit_plant.html', plant=plant)
    
    # GET request - show edit form
    return render_template('admin_edit_plant.html', plant=plant)

@app.route('/admin/manage_plants/delete/<int:plant_id>', methods=['POST'])
def delete_plant_route(plant_id):
    success, message = delete_plant(plant_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('manage_plants'))

@app.route('/admin/train_model')
def train_model():
    """Train the ML model on the current dataset."""
    try:
        message = train_medicinal_plant_model()
        flash(message, 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f'Error during training: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/view_dataset')
def view_dataset():
    """View dataset structure and statistics."""
    datasets = get_all_datasets()
    
    # Count images in dataset directory
    image_count = {}
    if os.path.exists(DATASET_PATH):
        for plant_dir in os.listdir(DATASET_PATH):
            plant_path = os.path.join(DATASET_PATH, plant_dir)
            if os.path.isdir(plant_path):
                images = [f for f in os.listdir(plant_path) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                image_count[plant_dir] = len(images)
    
    return render_template('admin_view_dataset.html', 
                         datasets=datasets, 
                         image_count=image_count)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Predict plant type from uploaded image using trained model."""
    import json
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image as keras_image
    
    prediction = None
    image_filename = None
    
    if request.method == 'POST':
        try:
            # Check if model exists
            if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
                flash('Model has not been trained yet. Please train the model first.', 'error')
                return render_template('predict.html')
            
            # Check if file is in request
            if 'file' not in request.files:
                flash('No file selected.', 'error')
                return render_template('predict.html')
            
            file = request.files['file']
            
            if file.filename == '':
                flash('No file selected.', 'error')
                return render_template('predict.html')
            
            if not allowed_file(file.filename):
                flash('File type not allowed. Only JPG, JPEG, PNG, GIF are accepted.', 'error')
                return render_template('predict.html')
            
            # Save uploaded file
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + original_filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file.save(filepath)
            
            # Load model and labels
            model = load_model(MODEL_PATH)
            with open(LABELS_PATH, 'r') as f:
                labels = json.load(f)
            
            # Prepare image for prediction
            img = keras_image.load_img(filepath, target_size=(224, 224))
            img_array = keras_image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            # Make prediction
            predictions_array = model.predict(img_array, verbose=0)[0]
            
            # Get predicted class
            predicted_class_idx = np.argmax(predictions_array)
            predicted_class_name = labels[str(predicted_class_idx)]
            confidence = float(predictions_array[predicted_class_idx]) * 100
            
            # Get all predictions with percentages
            all_predictions = {}
            for idx, label in labels.items():
                all_predictions[label] = float(predictions_array[int(idx)]) * 100
            
            # Sort by confidence
            all_predictions = dict(sorted(all_predictions.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True))
            
            prediction = {
                'plant_name': predicted_class_name,
                'confidence': round(confidence, 2),
                'all_predictions': all_predictions
            }
            
            image_filename = filename
            
        except Exception as e:
            flash(f'Error during prediction: {str(e)}', 'error')
            return render_template('predict.html')
    
    return render_template('predict.html', prediction=prediction, image_filename=image_filename)

@app.route('/user/upload')
def user_upload():
    if 'user_id' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('user_login'))

    return render_template('user_upload.html')

@app.route('/user/predict', methods=['POST'])
def user_predict():
    """Handle user plant image prediction with detailed plant information."""
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('user_login'))
    
    import json
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image as keras_image
    
    try:
        # Check if model exists
        if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
            flash('Model has not been trained yet. Please contact admin.', 'error')
            return redirect(url_for('user_upload'))
        
        # Check if file is in request
        if 'plant_image' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('user_upload'))
        
        file = request.files['plant_image']
        
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('user_upload'))
        
        # Validate file type
        allowed_image_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_image_extensions):
            flash('File type not allowed. Only JPG, JPEG, PNG, GIF are accepted.', 'error')
            return redirect(url_for('user_upload'))
        
        # Save uploaded file to static/uploads for display
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + original_filename
        filepath = os.path.join('static/uploads', filename)
        
        file.save(filepath)
        
        # Load model and labels
        model = load_model(MODEL_PATH)
        with open(LABELS_PATH, 'r') as f:
            labels = json.load(f)
        
        # Prepare image for prediction
        img = keras_image.load_img(filepath, target_size=(224, 224))
        img_array = keras_image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        # Make prediction
        predictions_array = model.predict(img_array, verbose=0)[0]
        
        # Get predicted class
        predicted_class_idx = np.argmax(predictions_array)
        predicted_class_name = labels[str(predicted_class_idx)]
        confidence = float(predictions_array[predicted_class_idx]) * 100
        
        # Get plant information from database using improved lookup
        plant_info = get_plant_by_name(predicted_class_name)
        
        # Get top 3 predictions
        top_predictions = []
        for idx, prob in enumerate(predictions_array):
            plant_name = labels[str(idx)]
            percentage = float(prob) * 100
            top_predictions.append({
                'name': plant_name,
                'confidence': round(percentage, 2)
            })
        
        # Sort by confidence and get top 3
        top_predictions = sorted(top_predictions, key=lambda x: x['confidence'], reverse=True)[:3]
        
        result = {
            'predicted_plant': predicted_class_name,
            'confidence': round(confidence, 2),
            'image_path': filename,
            'plant_info': plant_info,
            'top_predictions': top_predictions
        }
        
        return render_template('user_prediction_result.html', result=result)
        
    except Exception as e:
        flash(f'Error during prediction: {str(e)}', 'error')
        return redirect(url_for('user_upload'))

@app.route('/user/plants')
def plants_list():
    plants = get_all_plants()  # Fetch from database
    return render_template('user_plant_list.html', plants=plants)



if __name__ == '__main__':
    app.run(debug=True)