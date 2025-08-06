#!/usr/bin/env python3
"""
Pinecone API Key Setup for Lotus Electronics Chatbot
This script helps you configure and test your Pinecone connection.
"""

import os
import json

def get_pinecone_info():
    """Get information about Pinecone setup"""
    print("🔍 Pinecone Configuration Status")
    print("="*50)
    
    # Check environment variable
    env_key = os.getenv("PINECONE_API_KEY")
    if env_key:
        print(f"✅ Environment variable set: PINECONE_API_KEY=***{env_key[-4:]}")
    else:
        print("❌ No PINECONE_API_KEY environment variable found")
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ Found .env file: {env_file}")
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if 'PINECONE_API_KEY' in content:
                    print("✅ PINECONE_API_KEY found in .env file")
                else:
                    print("❌ No PINECONE_API_KEY in .env file")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print("❌ No .env file found")
    
    print(f"\n📋 Current Pinecone Settings:")
    print(f"   Index: all-products-lotus")
    print(f"   Host: https://all-products-lotus-imbj1oj.svc.aped-4627-b74a.pinecone.io")

def create_env_file():
    """Create a .env file with Pinecone configuration"""
    print(f"\n🔧 Creating .env file...")
    
    api_key = input("Enter your Pinecone API key: ").strip()
    if not api_key:
        print("❌ No API key provided")
        return False
    
    env_content = f"""# Lotus Electronics Chatbot Environment Variables
# Pinecone Configuration
PINECONE_API_KEY={api_key}

# Google AI Configuration  
GOOGLE_API_KEY={os.getenv('GOOGLE_API_KEY', 'AIzaSyAvGjCSwrbYHCphNJrBI2JHOc1Ga_2SP-k')}

# Tavily Configuration
TAVILY_API_KEY={os.getenv('TAVILY_API_KEY', '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')}

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("\n📝 To use the .env file, install python-dotenv:")
        print("   pip install python-dotenv")
        print("\n📝 Then add this to the top of chat.py:")
        print("   from dotenv import load_dotenv")
        print("   load_dotenv()")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_pinecone_connection():
    """Test Pinecone connection with current settings"""
    print(f"\n🧪 Testing Pinecone Connection...")
    
    try:
        from tools.product_search_tool import ProductSearchTool
        
        # Create tool instance (this will test the connection)
        tool = ProductSearchTool()
        
        if tool.is_available:
            print("✅ Pinecone connection successful!")
            
            # Test search
            print("\n🔍 Testing product search...")
            results = tool.search_products("test product", top_k=1)
            if results:
                print(f"✅ Search test successful! Found {len(results)} results")
            else:
                print("⚠️  Search returned no results (this might be normal)")
        else:
            print("❌ Pinecone connection failed - using fallback mode")
            print("   The chatbot will work with sample products")
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")

def show_fallback_info():
    """Show information about fallback mode"""
    print(f"\n🔄 Fallback Mode Information")
    print("="*50)
    print("When Pinecone is unavailable, the chatbot will:")
    print("✅ Continue to work normally")
    print("✅ Show sample products for common searches")
    print("✅ Maintain all other functionality (Redis memory, JSON responses)")
    print("⚠️  Limited product catalog (sample products only)")
    print("⚠️  No real-time inventory or pricing")
    
    print(f"\n📦 Available Sample Products:")
    print("   • Samsung 1.5 Ton 3 Star Split AC - ₹32,000")
    print("   • HP Pavilion Gaming Laptop - ₹65,000") 
    print("   • Sony WH-CH720N Wireless Headphones - ₹8,500")

def main():
    """Main setup function"""
    print("🏪 Lotus Electronics - Pinecone Setup Utility")
    print("="*60)
    
    # Show current status
    get_pinecone_info()
    
    # Show menu
    while True:
        print(f"\n📋 Setup Options:")
        print("1. Create .env file with API key")
        print("2. Test current Pinecone connection")  
        print("3. Show fallback mode info")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            create_env_file()
        elif choice == '2':
            test_pinecone_connection()
        elif choice == '3':
            show_fallback_info()
        elif choice == '4':
            break
        else:
            print("❌ Invalid option")
    
    print(f"\n🎉 Setup complete!")
    print(f"\n📝 Next steps:")
    print("1. Make sure Redis is running: docker run -d -p 6379:6379 redis:alpine")
    print("2. Start your Flask app: python app.py")
    print("3. The chatbot will work even if Pinecone is unavailable!")

if __name__ == "__main__":
    main()
