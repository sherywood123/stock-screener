# 🎯 Japan Stock Screener - How to Save and Run

## 🔥 **Quick Start (Easiest Method)**

### 1. **Save the Files**
Create a new folder for your project and save these 3 files:

**File 1: `japan_stock_screener_fixed.py`**
```python
# Copy the entire content from the fixed version above
# (The one that starts with "import streamlit as st")
```

**File 2: `setup_and_run.py`**
```python
# Copy the setup script content above
# (The one that starts with "#!/usr/bin/env python3")
```

### 2. **Get Your API Key**
- Go to [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs)
- Sign up for a free account
- Get your API key from your dashboard

### 3. **Run the Setup Script**
Open your terminal/command prompt in the folder where you saved the files:

```bash
python setup_and_run.py
```

This script will:
- ✅ Install all required packages
- ✅ Help you set up your API key
- ✅ Launch the application

---

## 📋 **Manual Method (Step by Step)**

### **Step 1: Save the Python File**

#### Option A: Copy and Paste
1. **Create a new file** called `japan_stock_screener_fixed.py`
2. **Copy the entire content** from the fixed version I provided above
3. **Paste it** into your file
4. **Save** the file

#### Option B: Download (if you have access to the workspace)
- Right-click and download `japan_stock_screener_fixed.py`

### **Step 2: Install Required Packages**
Open your terminal/command prompt and run:
```bash
pip install streamlit requests pandas
```

### **Step 3: Set Up Your API Key**
You need to get an API key from [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs)

#### **Method A: Environment Variable**
**Windows:**
```cmd
set FMP_API_KEY=your_api_key_here
```

**Mac/Linux:**
```bash
export FMP_API_KEY=your_api_key_here
```

#### **Method B: Streamlit Secrets (Recommended)**
1. Create a folder called `.streamlit` in the same directory as your Python file
2. Create a file called `secrets.toml` inside the `.streamlit` folder
3. Add this line to `secrets.toml`:
```toml
FMP_API_KEY = "your_api_key_here"
```

### **Step 4: Run the Application**
```bash
streamlit run japan_stock_screener_fixed.py
```

---

## 🌐 **What Happens When You Run It**

1. **Browser Opens**: A new tab opens in your browser
2. **Web Interface**: You see a clean web interface
3. **Stock Screening**: You can adjust parameters and click "开始筛选" (Start Screening)
4. **Results**: Filtered stocks appear with their financial metrics

---

## 🛠️ **Troubleshooting**

### **"Module not found" Error**
```bash
pip install streamlit requests pandas
```

### **"API key not found" Error**
- Make sure you've set up your API key correctly
- Check that your API key is valid
- Verify the `.streamlit/secrets.toml` file exists and has the correct format

### **"No stocks found" Error**
- Try adjusting the screening parameters (make them less restrictive)
- Check that your API key is working
- Verify your internet connection

### **Application Won't Start**
- Make sure you saved the file as `japan_stock_screener_fixed.py`
- Check that you're in the correct directory
- Verify Python is installed correctly

---

## 📱 **How to Use the Application**

1. **Set Parameters**: Adjust the screening criteria in the sidebar
   - 最大PE (Maximum PE Ratio)
   - 最大PB (Maximum PB Ratio)  
   - 最小股息率 (Minimum Dividend Yield)
   - 最小净现金/市值比例 (Minimum Net Cash to Market Cap Ratio)

2. **Start Screening**: Click "开始筛选" button

3. **Monitor Progress**: Watch the progress bar and status updates

4. **View Results**: Browse through the filtered stocks

5. **Export Data**: Results are automatically saved to CSV

---

## 🔐 **Security Note**
The fixed version uses secure API key handling - your API key is never hardcoded in the source code!

---

## 🆘 **Need Help?**
If you encounter any issues:
1. Check the troubleshooting section above
2. Verify all files are saved correctly
3. Ensure your API key is valid
4. Try the automatic setup script first

---

## 📂 **File Structure**
```
your-project-folder/
├── japan_stock_screener_fixed.py    # Main application
├── setup_and_run.py                 # Setup script (optional)
├── .streamlit/                      # Streamlit config folder
│   └── secrets.toml                 # API key storage
└── 筛选结果.csv                     # Results file (created automatically)
```

**That's it! You're ready to screen Japanese stocks! 🚀**