# ModelArk Video Generator

BytePlus ModelArk AI Video Generation Desktop Application

## Quick Start

### 1. Configuration

Create a `config.txt` file in the same directory as the executable:

```
your-api-key-here
ep-xxxxx
```

**Line 1:** Your BytePlus API Key
**Line 2:** Video generation endpoint ID (format: `ep-xxxxx`)

You can copy `config.txt.example` as a template.

### 2. Getting Your Credentials

1. **API Key:**
   - Visit BytePlus Console: https://console.byteplus.com
   - Navigate to API Keys section
   - Create or copy your API key

2. **Endpoint ID:**
   - Go to ModelArk console
   - Navigate to "Online Inference" section
   - Create a video generation endpoint
   - Copy the endpoint ID (starts with `ep-`)

### 3. Running the Application

- **Windows:** Double-click `ModelArkVideoGenerator.exe`
- The application will automatically open in your browser at `http://127.0.0.1:5001`
- If the browser doesn't open automatically, manually visit the URL

### 4. Using the Application

1. Enter your video description in the prompt field
2. Click "Generate Video"
3. Wait for the video to be generated (usually 30-60 seconds)
4. Click "Preview" to watch the generated video
5. Use "Download" to save the video to your computer

## System Requirements

- **Windows:** Windows 10/11 64-bit
- **macOS:** macOS 10.14 or later
- **Linux:** Modern Linux distribution with GUI
- No Python installation required - all dependencies are included

## Features

- ✅ Text-to-Video generation
- ✅ Task status monitoring with auto-refresh
- ✅ Video preview in browser
- ✅ Download generated videos
- ✅ Task history management
- ✅ Background task processing

## Troubleshooting

### Application won't start

- Check if port 5001 is already in use
- Make sure `config.txt` exists and is properly formatted
- Verify your API key and endpoint ID are valid

### Video generation fails

- Verify your BytePlus account has sufficient credits
- Check if the endpoint ID is correct and active
- Review the error message in the task list

### Browser doesn't open automatically

- Manually visit: http://127.0.0.1:5001
- Check if your default browser is set correctly
- Try a different browser if issues persist

## File Structure

```
├── ModelArkVideoGenerator.exe  # Main executable
├── config.txt                   # Your configuration (create this)
├── config.txt.example           # Configuration template
└── README.md                    # This file
```

## Support

For issues and questions:
- GitHub: https://github.com/Guangpop/ModelArkVideoAPI
- BytePlus Documentation: https://docs.byteplus.com

## License

This application uses BytePlus ModelArk API. Please review BytePlus terms of service for API usage.
