import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import db_manager
from app.core.redis_client import redis_client
from app.services.push_notifications import PushNotificationService
import json
import re

logger = logging.getLogger(__name__)

class JobMatchEngine:
    """Core job matching engine that processes new jobs against device subscriptions"""
    
    def __init__(self):
        self.push_service = PushNotificationService()
        self.logger = logging.getLogger(__name__)
    
    async def process_new_jobs(self):
        """Main matching engine - processes all jobs since scraper runs every 4-5 hours"""
        try:
            # Since scraper truncates and refreshes all data every 4-5 hours,
            # we need to process ALL jobs, not just recent ones
            all_jobs = await self.get_all_jobs()
            if not all_jobs:
                self.logger.info("No jobs to process")
                return
            
            self.logger.info(f"Processing {len(all_jobs)} jobs against subscriptions")
            
            # Get all active subscriptions
            active_subscriptions = await self.get_active_subscriptions()
            
            if not active_subscriptions:
                self.logger.info("No active subscriptions found")
                return
            
            # Clean up old matches for jobs that no longer exist
            await self.cleanup_orphaned_matches()
            
            self.logger.info(f"Found {len(active_subscriptions)} active subscriptions")
            for sub in active_subscriptions:
                self.logger.info(f"  User {sub['user_id']} (device {sub['device_id']}): keywords={sub['keywords']}")
            
            matches_created = 0
            jobs_processed = 0
            for job in all_jobs:
                jobs_processed += 1
                if jobs_processed % 1000 == 0:  # Log progress every 1000 jobs
                    self.logger.info(f"Processed {jobs_processed}/{len(all_jobs)} jobs, created {matches_created} matches")
                    
                if await self.match_job_to_subscriptions(job, active_subscriptions):
                    matches_created += 1
            
            self.logger.info(f"Processing complete: {jobs_processed} jobs processed, {matches_created} new matches created")
                
        except Exception as e:
            self.logger.error(f"Error in match engine: {e}", exc_info=True)
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from scraper schema (since scraper refreshes all data)"""
        try:
            query = """
                SELECT id, title, company, apply_link, source, created_at
                FROM scraper.jobs_jobpost 
                ORDER BY created_at DESC
            """
            jobs = await db_manager.execute_query(query)
            return [dict(job) for job in jobs] if jobs else []
            
        except Exception as e:
            self.logger.error(f"Error fetching all jobs: {e}")
            return []
    
    async def cleanup_orphaned_matches(self):
        """Remove job matches for jobs that no longer exist (deleted by scraper truncate)"""
        try:
            query = """
                DELETE FROM iosapp.job_matches 
                WHERE job_id NOT IN (
                    SELECT id::text FROM scraper.jobs_jobpost
                )
            """
            result = await db_manager.execute_command(query)
            self.logger.info("Cleaned up orphaned job matches")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up orphaned matches: {e}")
    
    async def get_new_jobs_since(self, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get new jobs from scraper schema since cutoff time (legacy method)"""
        try:
            query = """
                SELECT id, title, company, apply_link, source, created_at
                FROM scraper.jobs_jobpost 
                WHERE created_at > $1
                ORDER BY created_at DESC
            """
            jobs = await db_manager.execute_query(query, cutoff_time)
            return [dict(job) for job in jobs] if jobs else []
            
        except Exception as e:
            self.logger.error(f"Error fetching new jobs: {e}")
            return []
    
    async def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all active user subscriptions with device tokens"""
        try:
            query = """
                SELECT 
                    ks.id,
                    ks.user_id,
                    u.device_id,
                    ks.keywords,
                    ks.source_filters as sources,
                    ks.location_filters,
                    dt.device_token
                FROM iosapp.keyword_subscriptions ks
                JOIN iosapp.users u ON ks.user_id = u.id
                JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                WHERE ks.is_active = true 
                AND u.is_active = true
                AND dt.is_active = true
            """
            subscriptions = await db_manager.execute_query(query)
            return [dict(sub) for sub in subscriptions] if subscriptions else []
            
        except Exception as e:
            self.logger.error(f"Error fetching active subscriptions: {e}")
            return []
    
    async def match_job_to_subscriptions(self, job: Dict[str, Any], subscriptions: List[Dict[str, Any]]) -> bool:
        """Match a single job against all active subscriptions. Returns True if any matches created."""
        # Only use title and company for matching since description column doesn't exist
        job_text = f"{job.get('title', '')} {job.get('company', '')}".lower()
        matches_created = False
        
        for subscription in subscriptions:
            try:
                # Check if match already exists for this job+user combination (replaces Redis check)
                if await self.match_already_exists(subscription['user_id'], job['id']):
                    continue
                
                # Apply source filter if specified
                if (subscription.get('sources') and 
                    job.get('source') not in subscription['sources']):
                    continue
                
                # Apply location filters if specified
                if not self.check_location_filters(job, subscription.get('location_filters')):
                    continue
                
                # Check keyword matches
                matched_keywords = []
                for keyword in subscription['keywords']:
                    if keyword.lower() in job_text:
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    # Calculate relevance score
                    relevance_score = self.calculate_relevance(
                        job, matched_keywords, subscription['keywords']
                    )
                    
                    # Only proceed if relevance score meets minimum threshold
                    if relevance_score >= 0.1:  # Lowered threshold for better matching
                        # Store match in database
                        match_id = await self.store_job_match(
                            uuid.UUID(subscription['user_id']),
                            job['id'],
                            matched_keywords,
                            relevance_score
                        )
                        
                        # Send push notification
                        await self.push_service.send_job_match_notification(
                            subscription['device_token'],
                            subscription['user_id'],
                            job,
                            matched_keywords,
                            match_id
                        )
                        
                        # Record metrics
                        logger.info(f"Match created for device {device_id}, job {job_id}")
                        matches_created = True
                        
                        self.logger.info(
                            f"Match created: job {job['id']} -> user {subscription['user_id']} "
                            f"(score: {relevance_score:.2f})"
                        )
                        
            except Exception as e:
                self.logger.error(
                    f"Error processing job {job['id']} for subscription {subscription['id']}: {e}"
                )
        
        return matches_created
    
    async def match_already_exists(self, user_id: str, job_id: str) -> bool:
        """Check if a match already exists for this user+job combination"""
        try:
            query = """
                SELECT 1 FROM iosapp.job_matches 
                WHERE user_id = $1 AND job_id = $2 
                LIMIT 1
            """
            result = await db_manager.execute_query(query, user_id, str(job_id))
            return len(result) > 0 if result else False
            
        except Exception as e:
            self.logger.error(f"Error checking existing match: {e}")
            return False
    
    def check_location_filters(self, job: Dict[str, Any], location_filters: Optional[Dict]) -> bool:
        """Check if job matches location filters"""
        if not location_filters:
            return True
            
        # TODO: Implement location filtering logic
        # This would check job location against cities filter and remote_only flag
        # For now, return True (accept all jobs)
        return True
    
    def calculate_relevance(self, job: Dict[str, Any], matched_keywords: List[str], 
                          all_keywords: List[str]) -> float:
        """Calculate relevance score (0.0 to 1.0)"""
        # Base score: percentage of keywords matched
        base_score = len(matched_keywords) / len(all_keywords)
        
        # Bonus for title matches (more important than description matches)
        title = job.get('title', '').lower()
        title_matches = sum(1 for kw in matched_keywords if kw.lower() in title)
        title_bonus = (title_matches / len(matched_keywords)) * 0.3
        
        # Bonus for company name matches
        company = job.get('company', '').lower()
        company_matches = sum(1 for kw in matched_keywords if kw.lower() in company)
        company_bonus = (company_matches / len(matched_keywords)) * 0.1
        
        # Apply recency bonus based on created_at (posted_at doesn't exist)
        recency_bonus = 0.0
        if job.get('created_at'):
            job_created = job['created_at']
            # Use naive datetime comparison since database uses naive timestamps
            hours_old = (datetime.now() - job_created).total_seconds() / 3600
            if hours_old < 24:  # Jobs less than 24 hours old get bonus
                recency_bonus = (24 - hours_old) / 24 * 0.1
        
        total_score = base_score + title_bonus + company_bonus + recency_bonus
        return min(1.0, total_score)
    
    async def store_job_match(self, user_id: uuid.UUID, 
                            job_id: int, matched_keywords: List[str], 
                            relevance_score: float) -> str:
        """Store job match in database"""
        try:
            match_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO iosapp.job_matches 
                (id, user_id, job_id, matched_keywords, match_score)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await db_manager.execute_command(
                query,
                uuid.UUID(match_id),
                user_id,
                str(job_id),
                matched_keywords,
                float(relevance_score) * 100  # Convert to 0-100 scale
            )
            
            return match_id
            
        except Exception as e:
            self.logger.error(f"Error storing job match: {e}")
            raise e

class JobMatchScheduler:
    """Scheduler for running job matching at regular intervals"""
    
    def __init__(self, interval_minutes: int = 240):  # Changed to 4 hours (240 minutes) to align with scraper
        self.interval_minutes = interval_minutes
        self.match_engine = JobMatchEngine()
        self.running = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the job matching scheduler"""
        self.running = True
        self.logger.info(f"Starting job match scheduler (interval: {self.interval_minutes} minutes)")
        
        # Run once immediately on startup
        try:
            self.logger.info("Running initial job matching on startup...")
            await self.match_engine.process_new_jobs()
        except Exception as e:
            self.logger.error(f"Error in initial job matching: {e}")
        
        while self.running:
            try:
                self.logger.info(f"Waiting {self.interval_minutes} minutes until next matching run...")
                await asyncio.sleep(self.interval_minutes * 60)  # Convert to seconds
                
                self.logger.info("Running scheduled job matching...")
                await self.match_engine.process_new_jobs()
            except Exception as e:
                self.logger.error(f"Error in job match scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop(self):
        """Stop the job matching scheduler"""
        self.running = False
        self.logger.info("Job match scheduler stopped")

class ProfileBasedJobMatcher:
    """Enhanced job matching using user profile keywords with intelligent scoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_match_score(self, job: Dict[str, Any], user_keywords: List[str]) -> Dict[str, Any]:
        """
        Calculate sophisticated match score between job and user keywords
        Returns match details with score, matched keywords, and reasons
        """
        if not user_keywords:
            return {
                "score": 0,
                "matched_keywords": [],
                "match_reasons": [],
                "keyword_relevance": {}
            }
        
        # Job content to search
        job_title = (job.get("title", "") or "").lower()
        job_description = (job.get("description", "") or "").lower()
        job_requirements = (job.get("requirements", "") or "").lower()
        job_company = (job.get("company", "") or "").lower()
        
        # Combine all job text for comprehensive matching
        job_text = f"{job_title} {job_description} {job_requirements} {job_company}"
        
        matched_keywords = []
        keyword_relevance = {}
        match_reasons = []
        total_score = 0
        
        for keyword in user_keywords:
            keyword_lower = keyword.lower().strip()
            if not keyword_lower:
                continue
                
            keyword_score = 0
            keyword_matches = []
            
            # 1. Title matching (highest weight - 40 points)
            if keyword_lower in job_title:
                title_score = self._calculate_keyword_relevance(keyword_lower, job_title)
                keyword_score += title_score * 40
                keyword_matches.append(f"title ({title_score:.1f}x)")
            
            # 2. Requirements matching (high weight - 30 points)
            if keyword_lower in job_requirements:
                req_score = self._calculate_keyword_relevance(keyword_lower, job_requirements)
                keyword_score += req_score * 30
                keyword_matches.append(f"requirements ({req_score:.1f}x)")
            
            # 3. Description matching (medium weight - 20 points)
            if keyword_lower in job_description:
                desc_score = self._calculate_keyword_relevance(keyword_lower, job_description)
                keyword_score += desc_score * 20
                keyword_matches.append(f"description ({desc_score:.1f}x)")
            
            # 4. Company matching (low weight - 10 points)
            if keyword_lower in job_company:
                company_score = self._calculate_keyword_relevance(keyword_lower, job_company)
                keyword_score += company_score * 10
                keyword_matches.append(f"company ({company_score:.1f}x)")
            
            # 5. Fuzzy/partial matching (bonus points)
            fuzzy_score = self._calculate_fuzzy_match(keyword_lower, job_text)
            if fuzzy_score > 0:
                keyword_score += fuzzy_score * 5
                keyword_matches.append(f"related terms ({fuzzy_score:.1f}x)")
            
            if keyword_score > 0:
                matched_keywords.append(keyword)
                keyword_relevance[keyword] = {
                    "score": round(keyword_score, 2),
                    "matches": keyword_matches
                }
                total_score += keyword_score
                
                # Add specific match reasons
                if keyword_score >= 30:
                    match_reasons.append(f"Strong match for '{keyword}' in job requirements")
                elif keyword_score >= 20:
                    match_reasons.append(f"Good match for '{keyword}' in job title/description")
                else:
                    match_reasons.append(f"Relevant match for '{keyword}'")
        
        # Normalize score to 0-100 range
        max_possible_score = len(user_keywords) * 100  # Each keyword can score max 100 points
        normalized_score = min(100, (total_score / max_possible_score) * 100) if max_possible_score > 0 else 0
        
        # Add bonus for multiple keyword matches
        if len(matched_keywords) > 1:
            bonus = min(20, len(matched_keywords) * 2)  # Up to 20 bonus points
            normalized_score = min(100, normalized_score + bonus)
            match_reasons.append(f"Bonus for matching {len(matched_keywords)} keywords")
        
        return {
            "score": round(normalized_score, 1),
            "matched_keywords": matched_keywords,
            "match_reasons": match_reasons[:5],  # Limit to top 5 reasons
            "keyword_relevance": keyword_relevance,
            "total_keywords": len(user_keywords),
            "matched_count": len(matched_keywords)
        }
    
    def _calculate_keyword_relevance(self, keyword: str, text: str) -> float:
        """Calculate how relevant a keyword is in the given text"""
        if not keyword or not text:
            return 0.0
        
        # Count occurrences
        occurrences = text.lower().count(keyword.lower())
        if occurrences == 0:
            return 0.0
        
        # Base score for presence
        score = 1.0
        
        # Bonus for multiple occurrences (diminishing returns)
        if occurrences > 1:
            score += min(0.5, (occurrences - 1) * 0.2)
        
        # Bonus for word boundaries (exact word match vs substring)
        word_pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(word_pattern, text.lower()):
            score += 0.3
        
        # Bonus for position (early appearance in text)
        first_occurrence = text.lower().find(keyword.lower())
        if first_occurrence >= 0:
            # Earlier appearance gets higher bonus
            position_bonus = max(0, 0.2 - (first_occurrence / len(text)) * 0.2)
            score += position_bonus
        
        return min(2.0, score)  # Cap at 2.0x multiplier
    
    def _calculate_fuzzy_match(self, keyword: str, text: str) -> float:
        """Calculate fuzzy matching score for related terms"""
        if not keyword or not text or len(keyword) < 3:
            return 0.0
        
        # Simple fuzzy matching - look for related terms
        fuzzy_score = 0.0
        
        # Partial word matching
        if len(keyword) >= 4:
            # Look for keyword as substring in words
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if keyword in word or word in keyword:
                    if abs(len(word) - len(keyword)) <= 2:  # Similar length
                        fuzzy_score += 0.3
        
        # Common programming variations
        variations = self._get_keyword_variations(keyword)
        for variation in variations:
            if variation in text.lower():
                fuzzy_score += 0.4
        
        return min(1.0, fuzzy_score)
    
    def _get_keyword_variations(self, keyword: str) -> List[str]:
        """Get common variations of a keyword"""
        variations = []
        keyword_lower = keyword.lower()
        
        # Common tech variations
        tech_variations = {
            "javascript": ["js", "node", "nodejs", "frontend", "backend"],
            "python": ["py", "django", "flask", "fastapi", "backend"],
            "java": ["spring", "backend", "enterprise"],
            "react": ["reactjs", "frontend", "ui", "web"],
            "angular": ["angularjs", "frontend", "typescript"],
            "vue": ["vuejs", "frontend"],
            "docker": ["containerization", "devops"],
            "kubernetes": ["k8s", "devops", "orchestration"],
            "aws": ["amazon", "cloud", "devops"],
            "azure": ["microsoft", "cloud"],
            "gcp": ["google", "cloud"],
            "sql": ["database", "mysql", "postgresql", "oracle"],
            "nosql": ["mongodb", "redis", "elasticsearch"],
            "api": ["rest", "graphql", "microservices"],
            "frontend": ["ui", "ux", "web", "client"],
            "backend": ["server", "api", "database"],
            "fullstack": ["full-stack", "frontend", "backend"],
            "devops": ["ci", "cd", "infrastructure", "deployment"],
            "mobile": ["ios", "android", "app"],
            "ios": ["swift", "mobile", "app"],
            "android": ["kotlin", "java", "mobile", "app"]
        }
        
        if keyword_lower in tech_variations:
            variations.extend(tech_variations[keyword_lower])
        
        # Check reverse mapping
        for key, values in tech_variations.items():
            if keyword_lower in values:
                variations.append(key)
        
        return list(set(variations))  # Remove duplicates
    
    async def get_profile_matches(self, device_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get job matches for a user based on their profile keywords"""
        try:
            # Get user's profile keywords
            profile_query = """
                SELECT match_keywords, additional_job_preferences
                FROM iosapp.users 
                WHERE device_id = $1
            """
            
            profile_result = await db_manager.execute_query(profile_query, [device_id])
            
            if not profile_result:
                return {
                    "matches": [],
                    "total_count": 0,
                    "error": "User profile not found"
                }
            
            profile = profile_result[0]
            match_keywords = profile.get("match_keywords", [])
            
            # Handle JSON parsing
            if isinstance(match_keywords, str):
                match_keywords = json.loads(match_keywords)
            elif match_keywords is None:
                match_keywords = []
            
            if not match_keywords:
                return {
                    "matches": [],
                    "total_count": 0,
                    "message": "No keywords set for matching"
                }
            
            # Get all jobs for matching
            jobs_query = """
                SELECT id, title, company, location, salary, description, 
                       requirements, source, created_at
                FROM scraper.jobs_jobpost
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            
            jobs_result = await db_manager.execute_query(jobs_query, [limit * 3, offset])  # Get more jobs for better filtering
            
            # Score and rank jobs
            scored_jobs = []
            for job in jobs_result:
                match_details = self.calculate_match_score(job, match_keywords)
                
                if match_details["score"] > 0:  # Only include jobs with some relevance
                    scored_jobs.append({
                        "job_id": job["id"],
                        "title": job["title"],
                        "company": job["company"],
                        "location": job["location"],
                        "salary": job["salary"],
                        "description": job["description"][:300] + "..." if len(job["description"]) > 300 else job["description"],
                        "source": job["source"],
                        "posted_at": job["created_at"].isoformat(),
                        "match_score": match_details["score"],
                        "matched_keywords": match_details["matched_keywords"],
                        "match_reasons": match_details["match_reasons"],
                        "keyword_relevance": match_details["keyword_relevance"]
                    })
            
            # Sort by match score and take requested limit
            scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
            final_matches = scored_jobs[:limit]
            
            return {
                "matches": final_matches,
                "total_count": len(final_matches),
                "user_keywords": match_keywords,
                "matching_stats": {
                    "total_jobs_evaluated": len(jobs_result),
                    "jobs_with_matches": len(scored_jobs),
                    "average_score": round(sum(job["match_score"] for job in scored_jobs) / len(scored_jobs), 1) if scored_jobs else 0,
                    "top_score": max(job["match_score"] for job in scored_jobs) if scored_jobs else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting profile matches: {e}")
            return {
                "matches": [],
                "total_count": 0,
                "error": str(e)
            }

# Global scheduler instance
job_scheduler = JobMatchScheduler()

# Global profile matcher instance
profile_matcher = ProfileBasedJobMatcher()