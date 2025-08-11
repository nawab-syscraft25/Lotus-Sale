"""
Lotus Electronics Terms & Conditions and Privacy Policy Search Tool
Provides accurate information about company policies, terms, and privacy guidelines.
"""

import os
import re
import json
from typing import Dict, List, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

try:
    from pinecone import Pinecone
    from sentence_transformers import SentenceTransformer
    from textblob import TextBlob
    from langchain_google_genai import ChatGoogleGenerativeAI
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Missing dependencies for T&C search: {e}")
    DEPENDENCIES_AVAILABLE = False

class TermsConditionsInput(BaseModel):
    """Input schema for Terms & Conditions search."""
    query: str = Field(
        description="User's question about terms, conditions, privacy policy, or company policies. "
                   "Examples: 'return policy', 'warranty terms', 'data privacy', 'refund conditions'"
    )
    max_results: int = Field(
        default=3,
        description="Maximum number of relevant policy sections to return (1-5)"
    )

class TermsConditionsSearchTool:
    """Tool for searching Lotus Electronics Terms & Conditions and Privacy Policy."""
    
    def __init__(self):
        self.is_available = DEPENDENCIES_AVAILABLE
        self.index = None
        self.model = None
        self.llm = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize Pinecone, embedding model, and LLM for content refinement."""
        if not self.is_available:
            return
            
        try:
            # Configuration
            self.pinecone_api_key = os.getenv(
                "PINECONE_API_KEY",
                "pcsk_3G8JGb_R6CJ2jquYjF1Rvx9HKtDGhZz24hqA5vAa6stE3LQ5AHPM3Ayr2NEKFJRH4YYgBe"
            )
            self.index_name = "lotus-tc"
            
            # Initialize embedding model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize Pinecone
            pc = Pinecone(api_key=self.pinecone_api_key)
            self.index = pc.Index(self.index_name)
            
            # Initialize LLM for content refinement
            google_api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyAvGjCSwrbYHCphNJrBI2JHOc1Ga_2SP-k")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.3,
                google_api_key=google_api_key
            )
            
            print("✅ Terms & Conditions search tool initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize T&C search tool: {e}")
            self.is_available = False
    
    def clean_text(self, text: str) -> str:
        """Remove extra spaces and line breaks from PDF text."""
        return re.sub(r'\s+', ' ', text).strip()
    
    def correct_spelling(self, text: str) -> str:
        """Correct simple typos in the query."""
        try:
            return str(TextBlob(text).correct())
        except:
            return text  # Return original if correction fails
    
    def refine_policy_content(self, raw_content: str, user_query: str) -> str:
        """
        Use LLM to refine and clean up raw policy content for better user readability.
        
        Args:
            raw_content: Raw policy text from Pinecone
            user_query: User's original question for context
            
        Returns:
            Refined, clean, and user-friendly policy content
        """
        if not self.llm or not raw_content.strip():
            return raw_content
        
        try:
            refinement_prompt = f"""
You are a customer service assistant for Lotus Electronics. Clean up and refine this raw policy text to make it clear and user-friendly.

User's Question: "{user_query}"

Raw Policy Text:
{raw_content}

Instructions:
1. Fix spelling errors, spacing issues, and formatting problems
2. Make the text clear and easy to understand
3. Keep all important policy details intact
4. Use proper punctuation and grammar
5. Make it conversational but professional
6. Ensure it directly addresses the user's question
7. Remove any OCR artifacts or garbled text

Provide only the refined policy text, no additional commentary:
"""
            
            response = self.llm.invoke(refinement_prompt)
            refined_content = response.content.strip()
            
            # Validate that the refined content is reasonable
            if len(refined_content) > 50 and len(refined_content) < len(raw_content) * 3:
                return refined_content
            else:
                print(f"⚠️ LLM refinement produced unusual result, using original")
                return raw_content
                
        except Exception as e:
            print(f"⚠️ Error refining policy content: {e}")
            return raw_content
    
    def search_policies(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Search Terms & Conditions and Privacy Policy documents.
        
        Args:
            query: User's question about policies
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing relevant policy sections
        """
        if not self.is_available or not self.index or not self.model:
            return {
                "success": False,
                "error": "Terms & Conditions search service is currently unavailable",
                "policy_sections": []
            }
        
        try:
            # Correct spelling
            corrected_query = self.correct_spelling(query)
            if max_results <= 2:  # Only show debug info for test runs
                print(f"🔍 Searching for: '{corrected_query}'")
            
            # Embed the query
            query_embedding = self.model.encode(corrected_query).tolist()
            if max_results <= 2:  # Only show debug info for test runs
                print(f"📊 Query embedding dimension: {len(query_embedding)}")
            
            # Query Pinecone - match the working search_tc.py exactly
            results = self.index.query(
                vector=query_embedding,
                top_k=min(max_results, 5),
                include_metadata=True
            )
            
            if max_results <= 2:  # Only show debug info for test runs
                print(f"🔍 Raw Pinecone results: {len(results.get('matches', []))} matches found")
            
            # Process results - include ALL matches like the working version
            policy_sections = []
            for i, match in enumerate(results.get('matches', [])):
                score = match.get('score', 0.0)
                metadata = match.get('metadata', {})
                text = self.clean_text(metadata.get('text', ''))
                
                if max_results <= 2:  # Only show debug info for test runs
                    print(f"   Match {i+1}: Score={score:.4f}, Text length={len(text)}")
                
                # Include all results with text, no score filtering like search_tc.py
                if text:
                    # Refine the content using LLM for better readability
                    refined_content = self.refine_policy_content(text, corrected_query)
                    
                    policy_sections.append({
                        "relevance_score": round(score, 4),
                        "content": refined_content,
                        "raw_content": text,  # Keep original for debugging if needed
                        "section_type": metadata.get('section_type', 'general'),
                        "document": metadata.get('document', 'terms_conditions')
                    })
            
            return {
                "success": True,
                "query": corrected_query,
                "policy_sections": policy_sections,
                "total_found": len(policy_sections)
            }
            
        except Exception as e:
            print(f"❌ Error searching T&C: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "policy_sections": []
            }

# Initialize the tool instance
tc_search_tool = TermsConditionsSearchTool()

@tool("search_terms_conditions", args_schema=TermsConditionsInput)
def search_terms_conditions(query: str, max_results: int = 3) -> str:
    """
    Search Lotus Electronics Terms & Conditions and Privacy Policy documents.
    
    Use this tool when customers ask about:
    - Return and refund policies
    - Warranty terms and conditions
    - Privacy policy and data protection
    - Shipping and delivery terms
    - Customer rights and responsibilities
    - Payment terms and security
    - Company policies and guidelines
    
    Args:
        query: Customer's question about terms, conditions, or privacy policy
        max_results: Number of relevant policy sections to return (1-5)
        
    Returns:
        JSON string containing relevant policy information
    """
    
    # Validate inputs
    if not query or not query.strip():
        return json.dumps({
            "success": False,
            "error": "Please provide a specific question about our terms and conditions",
            "policy_sections": []
        })
    
    max_results = max(1, min(max_results, 5))  # Ensure between 1-5
    
    # Perform search
    result = tc_search_tool.search_policies(query.strip(), max_results)
    
    # Add helpful context for the chatbot
    if result.get("success") and result.get("policy_sections"):
        result["guidance"] = "I found relevant information in our policies. Please review these sections for complete details."
    elif result.get("success") and not result.get("policy_sections"):
        result["guidance"] = "I couldn't find specific information about that in our current policy documents. Please contact our customer service for detailed assistance."
    else:
        result["guidance"] = "I'm unable to search our policy documents right now. Please contact our customer service team for policy-related questions."
    
    return json.dumps(result, ensure_ascii=False, indent=2)

# Test function for standalone usage
def test_search():
    """Test function for the Terms & Conditions search tool."""
    test_queries = [
        "return policy",
        "warranty terms", 
        "privacy policy",
        "refund conditions",
        "data protection"
    ]
    
    print("🧪 Testing Terms & Conditions Search Tool")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        # Call the underlying search function directly instead of the LangChain tool
        result = tc_search_tool.search_policies(query, 2)
        
        if result.get("success"):
            print(f"✅ Found {result.get('total_found', 0)} relevant sections")
            for i, section in enumerate(result.get("policy_sections", [])[:1], 1):
                content_preview = section.get("content", "")[:100] + "..."
                print(f"   {i}. Score: {section.get('relevance_score')} - {content_preview}")
        else:
            print(f"❌ Error: {result.get('error')}")
        print("-" * 30)

if __name__ == "__main__":
    test_search()
