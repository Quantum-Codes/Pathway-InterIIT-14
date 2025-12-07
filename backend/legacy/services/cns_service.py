from sqlalchemy.orm import Session
from app.models.cns_match import CNSDatabase, CNSMatch
from app.models.user import User
from typing import Optional
import time
from difflib import SequenceMatcher


def get_databases(db: Session):
    """Get all CNS databases"""
    databases = db.query(CNSDatabase).filter(CNSDatabase.enabled == True).all()
    return {"databases": databases}


def search_cns(
    db: Session,
    name: str,
    type: Optional[str] = "BOTH",
    country: Optional[str] = None,
    fuzzy: bool = True,
    min_confidence: float = 0.7
):
    """Search CNS databases for sanctions/watchlist matches"""
    start_time = time.time()
    
    query = db.query(CNSMatch)
    
    # Apply filters
    if type != "BOTH":
        query = query.filter(CNSMatch.entity_type == type)
    
    if country:
        query = query.filter(CNSMatch.country == country)
    
    # Get all potential matches
    all_matches = query.all()
    
    # Calculate confidence scores
    matches = []
    for match in all_matches:
        if fuzzy:
            confidence = SequenceMatcher(None, name.upper(), match.name.upper()).ratio()
            
            # Check aka_names too
            if match.aka_names:
                for aka in match.aka_names:
                    aka_confidence = SequenceMatcher(None, name.upper(), aka.upper()).ratio()
                    confidence = max(confidence, aka_confidence)
        else:
            confidence = 1.0 if name.upper() == match.name.upper() else 0.0
        
        if confidence >= min_confidence:
            match_dict = {
                "match_id": match.id,
                "name": match.name,
                "confidence": round(confidence, 2),
                "source": match.source,
                "database_id": match.database_id,
                "list_type": match.list_type,
                "entity_type": match.entity_type,
                "country": match.country,
                "date_of_birth": match.date_of_birth,
                "aka_names": match.aka_names,
                "added_date": match.added_date,
                "program": match.program,
                "remarks": match.remarks,
                "risk_level": match.risk_level
            }
            matches.append((confidence, match_dict))
    
    # Sort by confidence
    matches.sort(reverse=True, key=lambda x: x[0])
    sorted_matches = [m[1] for m in matches]
    
    # Get databases searched
    databases = db.query(CNSDatabase).filter(CNSDatabase.enabled == True).all()
    db_names = [d.name for d in databases]
    
    search_time = int((time.time() - start_time) * 1000)
    
    return {
        "query": name,
        "total_matches": len(sorted_matches),
        "search_time_ms": search_time,
        "databases_searched": db_names,
        "matches": sorted_matches
    }


def batch_check_users(db: Session, user_ids: list[int]):
    """Batch check multiple users against CNS"""
    results = []
    matches_found = 0
    
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue
        
        # Search for this user
        search_result = search_cns(db, user.applicant_name, fuzzy=True, min_confidence=0.8)
        
        match_found = search_result["total_matches"] > 0
        if match_found:
            matches_found += 1
            highest = search_result["matches"][0]
            result = {
                "user_id": user_id,
                "user_name": user.applicant_name,
                "match_found": True,
                "match_count": search_result["total_matches"],
                "highest_confidence": highest["confidence"],
                "risk_level": highest["risk_level"]
            }
        else:
            result = {
                "user_id": user_id,
                "user_name": user.applicant_name,
                "match_found": False,
                "match_count": 0,
                "highest_confidence": None,
                "risk_level": None
            }
        
        results.append(result)
    
    return {
        "total_checked": len(user_ids),
        "matches_found": matches_found,
        "results": results
    }


def seed_sample_cns_data(db: Session):
    """Seed some sample CNS data for testing"""
    # Check if data already exists
    existing = db.query(CNSDatabase).first()
    if existing:
        return
    
    # Create sample databases
    databases = [
        CNSDatabase(
            id="ofac_sdn",
            name="OFAC SDN List",
            full_name="Office of Foreign Assets Control - Specially Designated Nationals",
            description="List of individuals and entities whose assets are blocked",
            country="USA",
            record_count=15420,
            enabled=True
        ),
        CNSDatabase(
            id="un_sanctions",
            name="UN Sanctions List",
            full_name="United Nations Consolidated Sanctions List",
            description="Consolidated list of all UN sanctions",
            country="INTERNATIONAL",
            record_count=8934,
            enabled=True
        ),
        CNSDatabase(
            id="eu_sanctions",
            name="EU Sanctions List",
            full_name="European Union Consolidated Sanctions List",
            description="Consolidated list of EU restrictive measures",
            country="EU",
            record_count=6521,
            enabled=True
        )
    ]
    
    for db_record in databases:
        db.add(db_record)
    
    # Create sample matches
    matches = [
        CNSMatch(
            id="CNS-00001",
            name="SUSPICIOUS ENTITY",
            confidence=0.95,
            source="OFAC SDN List",
            database_id="ofac_sdn",
            list_type="SANCTIONS",
            entity_type="INDIVIDUAL",
            country="USA",
            date_of_birth="1980-05-15",
            aka_names=["SUSPECT PERSON", "S ENTITY"],
            added_date="2020-05-15",
            program="SDGT - Specially Designated Global Terrorist",
            remarks="Involved in financial crimes",
            risk_level="HIGH"
        )
    ]
    
    for match in matches:
        db.add(match)
    
    db.commit()
