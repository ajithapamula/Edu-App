# weekend_mocktest/core/content_service.py
"""
Content Service - FIXED VERSION
Reads summaries from MongoDB collections based on user type.
- dev → Developer collection (Python/Coding)
- non_dev → Non-Developer collection (SAP/Business)

FIXED: No longer over-filters SAP content for non-dev
"""

import logging
from typing import Optional
from .database import get_db_manager

logger = logging.getLogger(__name__)


class ContentService:
    """Service to get context from MongoDB summaries"""
    
    # Only block content with CLEAR programming language indicators
    # NOT generic terms like "function", "module", "data" which are also used in SAP
    STRICT_PROGRAMMING_INDICATORS = [
        # Programming languages
        'python', 'java ', 'javascript', 'c++', 'c#', 'ruby', 'php',
        # Python-specific syntax
        'def ', 'import ', 'from ', 'class ', 'return ', 'print(',
        'lambda', '__init__', '__name__', 'self.', '>>>', 'pip install',
        # Code patterns
        'for i in range', 'while true', 'if __name__', 'try:', 'except:',
        # Framework/library names
        'pandas', 'numpy', 'tensorflow', 'pytorch', 'django', 'flask',
        # File extensions in code context
        '.py', '.js', '.java',
    ]
    
    # SAP-specific terms that should NEVER be filtered
    SAP_WHITELIST = [
        'sap', 'erp', 'mm', 'sd', 'fico', 'hr', 'pp', 'wm', 'qm',
        'abap', 'hana', 'fiori', 's/4hana', 'netweaver',
        'procurement', 'sales', 'distribution', 'finance', 'controlling',
        'material', 'vendor', 'customer', 'purchase order', 'sales order',
        'general ledger', 'accounts payable', 'accounts receivable',
        'cost center', 'profit center', 'business process',
        'master data', 'transactional data', 'organizational structure'
    ]
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def _is_programming_content(self, text: str) -> bool:
        """
        Check if text contains CLEAR programming content.
        Returns False for SAP/Business content even if it uses words like 'function'.
        """
        text_lower = text.lower()
        
        # If it contains SAP-specific terms, it's NOT programming content
        for sap_term in self.SAP_WHITELIST:
            if sap_term in text_lower:
                return False
        
        # Only flag as programming if it has STRICT programming indicators
        for indicator in self.STRICT_PROGRAMMING_INDICATORS:
            if indicator in text_lower:
                return True
        
        return False
    
    def get_context_for_questions(self, user_type: str) -> str:
        """
        Get context from appropriate MongoDB collection.
        
        FIXED: For non-dev, only filters content with CLEAR programming indicators,
        not generic terms that also appear in SAP context.
        """
        logger.info("=" * 60)
        if user_type == "dev":
            logger.info("🟢 DEVELOPER TRACK - Reading Python/Coding summaries")
        else:
            logger.info("🟠 NON-DEVELOPER TRACK - Reading SAP/Business summaries")
        logger.info("=" * 60)
        
        # Get summaries from correct collection
        summaries = self.db_manager.get_weekly_summaries(user_type)
        
        if not summaries:
            logger.warning(f"⚠️ No summaries found for {user_type}")
            return self._get_default_context(user_type)
        
        logger.info(f"📄 Found {len(summaries)} documents in collection")
        
        # Build context from summaries
        context_parts = []
        valid_count = 0
        
        for i, doc in enumerate(summaries, 1):
            summary_text = doc.get("summary", "")
            if not summary_text:
                continue
            
            # For dev: use all summaries (they should be Python content)
            # For non-dev: ONLY filter if it has STRICT programming indicators
            if user_type == "non_dev":
                if self._is_programming_content(summary_text):
                    # Double check - if it mentions SAP, keep it anyway
                    if 'sap' in summary_text.lower():
                        logger.info(f"  ✅ Doc {i}: SAP content (keeping despite some code terms)")
                        context_parts.append(summary_text)
                        valid_count += 1
                    else:
                        logger.warning(f"  🚫 Doc {i}: FILTERED (clear programming content)")
                        logger.warning(f"      Preview: {summary_text[:50]}...")
                else:
                    # Not programming content - use it
                    logger.info(f"  ✅ Doc {i}: {summary_text[:50]}...")
                    context_parts.append(summary_text)
                    valid_count += 1
            else:
                # Developer track - use all content
                logger.info(f"  ✅ Doc {i}: {summary_text[:50]}...")
                context_parts.append(summary_text)
                valid_count += 1
        
        if not context_parts:
            logger.warning(f"⚠️ No valid summaries after filtering!")
            logger.warning(f"⚠️ Using DEFAULT context for {user_type}")
            return self._get_default_context(user_type)
        
        context = "\n\n".join(context_parts)
        
        logger.info("=" * 60)
        if user_type == "dev":
            logger.info(f"🟢 DEVELOPER Context Ready: {len(context)} chars from {valid_count} Python summaries")
        else:
            logger.info(f"🟠 NON-DEVELOPER Context Ready: {len(context)} chars from {valid_count} SAP summaries")
        logger.info("=" * 60)
        
        return context
    
    def _get_default_context(self, user_type: str) -> str:
        """Get default context when no summaries available"""
        if user_type == "dev":
            return """
            Python Programming Fundamentals:
            - Variables, data types, operators
            - Control flow: if/else, loops
            - Functions and modules
            - Object-oriented programming
            - File handling
            - Exception handling
            - List comprehensions
            - Decorators and generators
            """
        else:
            # SAP/Business default context
            return """
            SAP ERP Fundamentals and Business Processes:
            
            SAP MM (Materials Management):
            - Procurement process: Requisition → Purchase Order → Goods Receipt → Invoice → Payment
            - Vendor management and evaluation
            - Inventory management and stock movements
            
            SAP SD (Sales and Distribution):
            - Sales cycle: Inquiry → Quotation → Sales Order → Delivery → Billing → Payment
            - Customer master data management
            - Pricing and conditions
            
            SAP FICO (Finance and Controlling):
            - General Ledger accounting
            - Accounts Payable and Receivable
            - Cost centers and profit centers
            - Asset accounting
            
            SAP HR (Human Resources):
            - Organizational management
            - Personnel administration
            - Time management and payroll
            
            SAP PP (Production Planning):
            - Material Requirements Planning (MRP)
            - Production orders and scheduling
            - Capacity planning
            
            Key Concepts:
            - Master data vs Transactional data
            - Integration between SAP modules
            - Organizational structure in SAP
            - Business process workflows
            """


# Singleton
_content_service = None

def get_content_service() -> ContentService:
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service