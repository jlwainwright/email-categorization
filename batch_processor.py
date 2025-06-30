#!/usr/bin/env python3
"""
Batch Email Processor
---------------------
Efficient batch processing of emails with parallel API calls,
similarity grouping, and optimized resource usage.
"""

import time
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import difflib

@dataclass
class EmailBatch:
    """Represents a batch of emails for processing."""
    emails: List[Dict[str, Any]]
    batch_id: str
    created_at: datetime
    processing_status: str = "pending"  # pending, processing, completed, failed
    results: List[Dict[str, Any]] = None

@dataclass
class BatchResult:
    """Result of batch processing."""
    batch_id: str
    success_count: int
    error_count: int
    total_count: int
    processing_time: float
    api_calls_saved: int
    errors: List[Dict[str, str]]

class EmailSimilarityGrouper:
    """Groups similar emails for optimized batch processing."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def _calculate_similarity(self, email1: Dict[str, Any], email2: Dict[str, Any]) -> float:
        """Calculate similarity between two emails."""
        # Create text representations for comparison
        text1 = f"{email1.get('from', '')} {email1.get('subject', '')} {email1.get('content', '')[:200]}"
        text2 = f"{email2.get('from', '')} {email2.get('subject', '')} {email2.get('content', '')[:200]}"
        
        # Use difflib for text similarity
        similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
        # Additional similarity factors
        
        # Same sender
        if email1.get('from', '').lower() == email2.get('from', '').lower():
            similarity += 0.1
        
        # Similar subject patterns
        subject1 = email1.get('subject', '').lower()
        subject2 = email2.get('subject', '').lower()
        
        if subject1 and subject2:
            # Check for common patterns like "Re:", "Fwd:", etc.
            clean_subject1 = subject1.replace('re:', '').replace('fwd:', '').replace('fw:', '').strip()
            clean_subject2 = subject2.replace('re:', '').replace('fwd:', '').replace('fw:', '').strip()
            
            if clean_subject1 == clean_subject2:
                similarity += 0.2
        
        # Similar content length
        len1 = len(email1.get('content', ''))
        len2 = len(email2.get('content', ''))
        
        if len1 > 0 and len2 > 0:
            length_similarity = 1 - abs(len1 - len2) / max(len1, len2)
            if length_similarity > 0.8:
                similarity += 0.1
        
        return min(similarity, 1.0)
    
    def group_emails(self, emails: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group similar emails together."""
        if len(emails) <= 1:
            return [emails] if emails else []
        
        groups = []
        used_emails = set()
        
        for i, email in enumerate(emails):
            if i in used_emails:
                continue
            
            # Start a new group with this email
            group = [email]
            used_emails.add(i)
            
            # Find similar emails
            for j, other_email in enumerate(emails[i+1:], i+1):
                if j in used_emails:
                    continue
                
                similarity = self._calculate_similarity(email, other_email)
                if similarity >= self.similarity_threshold:
                    group.append(other_email)
                    used_emails.add(j)
            
            groups.append(group)
        
        return groups

class BatchEmailProcessor:
    """Handles batch processing of emails with parallel execution."""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 3, similarity_threshold: float = 0.7):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.similarity_grouper = EmailSimilarityGrouper(similarity_threshold)
        
        # Processing state
        self.active_batches = {}
        self.completed_batches = []
        self.processing_stats = {
            'total_emails_processed': 0,
            'total_batches_processed': 0,
            'total_api_calls_saved': 0,
            'total_processing_time': 0,
            'average_batch_size': 0
        }
        
        # Thread safety
        self.lock = threading.Lock()
    
    def _generate_batch_id(self) -> str:
        """Generate unique batch ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _create_batches(self, emails: List[Dict[str, Any]]) -> List[EmailBatch]:
        """Create batches from emails with similarity grouping."""
        if not emails:
            return []
        
        # Group similar emails
        similarity_groups = self.similarity_grouper.group_emails(emails)
        
        batches = []
        current_batch_emails = []
        
        for group in similarity_groups:
            # If adding this group would exceed batch size, finalize current batch
            if current_batch_emails and len(current_batch_emails) + len(group) > self.batch_size:
                batch = EmailBatch(
                    emails=current_batch_emails.copy(),
                    batch_id=self._generate_batch_id(),
                    created_at=datetime.now()
                )
                batches.append(batch)
                current_batch_emails = []
            
            # Add group to current batch
            current_batch_emails.extend(group)
            
            # If current batch is at capacity, finalize it
            if len(current_batch_emails) >= self.batch_size:
                batch = EmailBatch(
                    emails=current_batch_emails.copy(),
                    batch_id=self._generate_batch_id(),
                    created_at=datetime.now()
                )
                batches.append(batch)
                current_batch_emails = []
        
        # Add remaining emails as final batch
        if current_batch_emails:
            batch = EmailBatch(
                emails=current_batch_emails,
                batch_id=self._generate_batch_id(),
                created_at=datetime.now()
            )
            batches.append(batch)
        
        return batches
    
    def _process_single_batch(self, batch: EmailBatch, sentiment_func, categorize_func, 
                             config) -> BatchResult:
        """Process a single batch of emails."""
        start_time = time.time()
        results = []
        errors = []
        api_calls_saved = 0
        
        try:
            batch.processing_status = "processing"
            
            print(f"🔄 Processing batch {batch.batch_id} ({len(batch.emails)} emails)")
            
            # Group emails by content similarity for API optimization
            content_groups = defaultdict(list)
            
            for email in batch.emails:
                # Create content hash for grouping
                content_key = f"{email.get('from', '')}|{email.get('subject', '')}|{email.get('content', '')[:100]}"
                content_hash = hashlib.md5(content_key.encode()).hexdigest()
                content_groups[content_hash].append(email)
            
            # Process each content group
            for content_hash, email_group in content_groups.items():
                try:
                    # Use first email as representative for API calls
                    representative_email = email_group[0]
                    
                    # Get sentiment (once per group)
                    sentiment_text = representative_email.get('text_content') or representative_email.get('content', '')
                    sentiment = sentiment_func(sentiment_text, config)
                    
                    # Enhanced email data for categorization
                    enhanced_email_data = {
                        'from': representative_email['from'],
                        'subject': representative_email['subject'],
                        'content': representative_email['content'],
                        'has_html': representative_email.get('has_html', False),
                        'attachments_count': len(representative_email.get('attachments', [])),
                        'text_content': representative_email.get('text_content', ''),
                        'html_content': representative_email.get('html_content', '')
                    }
                    
                    # Get category (once per group)
                    category = categorize_func(enhanced_email_data, sentiment, config)
                    
                    # Apply results to all emails in group
                    for email in email_group:
                        email_result = {
                            'email': email,
                            'sentiment': sentiment,
                            'category': category,
                            'processing_time': time.time() - start_time,
                            'cached_result': len(email_group) > 1  # True if shared result
                        }
                        results.append(email_result)
                    
                    # Track API calls saved
                    if len(email_group) > 1:
                        api_calls_saved += (len(email_group) - 1) * 2  # 2 API calls per email (sentiment + categorization)
                    
                    print(f"   ✅ Processed {len(email_group)} similar email(s) → {category}")
                    
                except Exception as e:
                    # Handle errors for this group
                    error_msg = str(e)
                    print(f"   ❌ Error processing email group: {error_msg}")
                    
                    for email in email_group:
                        errors.append({
                            'email_subject': email.get('subject', 'Unknown'),
                            'email_from': email.get('from', 'Unknown'),
                            'error': error_msg
                        })
                        
                        # Add fallback result
                        email_result = {
                            'email': email,
                            'sentiment': 'NEUTRAL',
                            'category': 'General Inquiries',
                            'processing_time': time.time() - start_time,
                            'error': error_msg
                        }
                        results.append(email_result)
            
            batch.processing_status = "completed"
            batch.results = results
            
        except Exception as e:
            batch.processing_status = "failed"
            error_msg = str(e)
            print(f"❌ Batch {batch.batch_id} failed: {error_msg}")
            
            # Create error results for all emails
            for email in batch.emails:
                errors.append({
                    'email_subject': email.get('subject', 'Unknown'),
                    'email_from': email.get('from', 'Unknown'),
                    'error': error_msg
                })
                
                email_result = {
                    'email': email,
                    'sentiment': 'NEUTRAL',
                    'category': 'General Inquiries',
                    'processing_time': time.time() - start_time,
                    'error': error_msg
                }
                results.append(email_result)
        
        processing_time = time.time() - start_time
        
        return BatchResult(
            batch_id=batch.batch_id,
            success_count=len(results) - len(errors),
            error_count=len(errors),
            total_count=len(batch.emails),
            processing_time=processing_time,
            api_calls_saved=api_calls_saved,
            errors=errors
        )
    
    def process_emails_batch(self, emails: List[Dict[str, Any]], sentiment_func, 
                           categorize_func, config) -> List[BatchResult]:
        """Process emails in batches with parallel execution."""
        if not emails:
            return []
        
        print(f"🚀 Starting batch processing for {len(emails)} emails")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Max workers: {self.max_workers}")
        print(f"   Similarity threshold: {self.similarity_grouper.similarity_threshold}")
        
        # Create batches
        batches = self._create_batches(emails)
        print(f"   Created {len(batches)} batches")
        
        # Process batches in parallel
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches for processing
            future_to_batch = {
                executor.submit(
                    self._process_single_batch, 
                    batch, 
                    sentiment_func, 
                    categorize_func, 
                    config
                ): batch for batch in batches
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    result = future.result()
                    batch_results.append(result)
                    
                    with self.lock:
                        self.active_batches[batch.batch_id] = batch
                        self.completed_batches.append(result)
                    
                except Exception as e:
                    print(f"❌ Batch {batch.batch_id} failed with exception: {e}")
                    
                    # Create error result
                    error_result = BatchResult(
                        batch_id=batch.batch_id,
                        success_count=0,
                        error_count=len(batch.emails),
                        total_count=len(batch.emails),
                        processing_time=0,
                        api_calls_saved=0,
                        errors=[{'email_subject': 'Batch Error', 'email_from': 'System', 'error': str(e)}]
                    )
                    batch_results.append(error_result)
        
        # Update processing stats
        self._update_processing_stats(batch_results)
        
        # Print summary
        self._print_batch_summary(batch_results)
        
        return batch_results
    
    def _update_processing_stats(self, batch_results: List[BatchResult]):
        """Update processing statistics."""
        with self.lock:
            total_emails = sum(result.total_count for result in batch_results)
            total_time = sum(result.processing_time for result in batch_results)
            total_api_calls_saved = sum(result.api_calls_saved for result in batch_results)
            
            self.processing_stats['total_emails_processed'] += total_emails
            self.processing_stats['total_batches_processed'] += len(batch_results)
            self.processing_stats['total_api_calls_saved'] += total_api_calls_saved
            self.processing_stats['total_processing_time'] += total_time
            
            if self.processing_stats['total_batches_processed'] > 0:
                self.processing_stats['average_batch_size'] = (
                    self.processing_stats['total_emails_processed'] / 
                    self.processing_stats['total_batches_processed']
                )
    
    def _print_batch_summary(self, batch_results: List[BatchResult]):
        """Print batch processing summary."""
        total_emails = sum(result.total_count for result in batch_results)
        total_success = sum(result.success_count for result in batch_results)
        total_errors = sum(result.error_count for result in batch_results)
        total_time = sum(result.processing_time for result in batch_results)
        total_api_calls_saved = sum(result.api_calls_saved for result in batch_results)
        
        print(f"\n📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*50}")
        print(f"📧 Total emails processed: {total_emails}")
        print(f"✅ Successful: {total_success}")
        print(f"❌ Errors: {total_errors}")
        print(f"⏱️  Total processing time: {total_time:.2f}s")
        print(f"💾 API calls saved: {total_api_calls_saved}")
        print(f"📦 Batches created: {len(batch_results)}")
        
        if total_emails > 0:
            success_rate = (total_success / total_emails) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        if total_api_calls_saved > 0:
            savings_percentage = (total_api_calls_saved / (total_emails * 2)) * 100
            print(f"💰 API call efficiency: {savings_percentage:.1f}% savings")
        
        print(f"{'='*50}\n")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        with self.lock:
            return self.processing_stats.copy()
    
    def get_batch_status(self, batch_id: str) -> Optional[EmailBatch]:
        """Get status of a specific batch."""
        with self.lock:
            return self.active_batches.get(batch_id)

# Global batch processor instance
batch_processor = BatchEmailProcessor()

def process_emails_in_batches(emails: List[Dict[str, Any]], sentiment_func, 
                             categorize_func, config, batch_size: int = 10) -> List[Dict[str, Any]]:
    """
    Process emails in batches and return flattened results.
    
    Args:
        emails: List of email dictionaries
        sentiment_func: Function to analyze sentiment
        categorize_func: Function to categorize emails  
        config: Configuration object
        batch_size: Size of each batch
        
    Returns:
        List of processed email results
    """
    global batch_processor
    batch_processor.batch_size = batch_size
    
    batch_results = batch_processor.process_emails_batch(
        emails, sentiment_func, categorize_func, config
    )
    
    # Flatten results
    all_results = []
    for batch_result in batch_results:
        # Get the actual email results from the batch
        if batch_result.batch_id in batch_processor.active_batches:
            batch = batch_processor.active_batches[batch_result.batch_id]
            if batch.results:
                all_results.extend(batch.results)
    
    return all_results

if __name__ == "__main__":
    # Test the batch processor
    print("Testing Batch Email Processor...")
    
    # Create test emails
    test_emails = []
    for i in range(15):
        test_emails.append({
            'from': f'sender{i % 3}@example.com',  # Create some similarity
            'subject': f'Test Email {i}' if i % 3 != 0 else 'Test Email Duplicate',
            'content': f'This is test email content {i}',
            'has_html': i % 2 == 0,
            'attachments': []
        })
    
    def mock_sentiment(text, config):
        return 'POSITIVE'
    
    def mock_categorize(email_data, sentiment, config):
        return 'General Inquiries'
    
    # Test batch processing
    results = process_emails_in_batches(
        test_emails, mock_sentiment, mock_categorize, {}, batch_size=5
    )
    
    print(f"Processed {len(results)} emails in batches")
    
    # Show stats
    stats = batch_processor.get_processing_stats()
    print("Processing Stats:", stats)