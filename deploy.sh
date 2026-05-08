#!/bin/bash
# Deployment script for Fact-Check Agent on Streamlit Cloud

echo "🚀 Deploying Fact-Check Agent..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo "OPENAI_API_KEY=your_openai_key_here"
    echo "SERPER_API_KEY=your_serper_key_here"
    exit 1
fi

# Check if required environment variables are set
if ! grep -q "OPENAI_API_KEY" .env; then
    echo "❌ Error: OPENAI_API_KEY not found in .env file"
    exit 1
fi

if ! grep -q "SERPER_API_KEY" .env; then
    echo "❌ Error: SERPER_API_KEY not found in .env file"
    exit 1
fi

echo "✅ Environment configuration validated"

# Create necessary directories
mkdir -p uploads
mkdir -p sample_outputs

echo "✅ Directory structure ready"

# Test imports
echo "🧪 Testing application imports..."
python -c "import app; print('✅ App imports successfully!')" || {
    echo "❌ Import test failed"
    exit 1
}

echo "🎉 Deployment preparation complete!"
echo ""
echo "To deploy on Streamlit Cloud:"
echo "1. Push this code to GitHub"
echo "2. Go to share.streamlit.io"
echo "3. Connect your GitHub repository"
echo "4. Set the main file path to: app.py"
echo "5. Add your environment variables in the Secrets section:"
echo "   - OPENAI_API_KEY"
echo "   - SERPER_API_KEY"
echo ""
echo "Your app will be live at: https://your-app-name.streamlit.app"