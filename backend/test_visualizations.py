"""
Test script to create sample data and test visualizations
"""
from app.db.conn import db_session
from app.models import Session, SessionStatus, Client
from datetime import datetime, timedelta
import uuid
from app.routes.bootstrap import LOCAL_CLIENT_ID
from app.db.repository import ClientRepository

# def create_test_data():
def create_test_data():
    print("Creating test data...")

    with db_session() as db:
        # STEP 1: Create or get the client FIRST
        print(f"Ensuring client exists with ID: {LOCAL_CLIENT_ID}")
        client = Client(client_id=LOCAL_CLIENT_ID, client_name="Test User")
        db.add(client)
        db.flush()

        print(f"✅ Client ready: {client.client_name} (ID: {client.client_id})")
        
        # STEP 2: Create test sessions
        test_sessions = [
            {"topic": "Math Homework",       "focused": 1200, "distracted": 300, "avg_attention": 85.5},
            {"topic": "Reading Assignment",  "focused": 1800, "distracted": 600, "avg_attention": 75.0},
            {"topic": "Coding Practice",     "focused": 2400, "distracted": 200, "avg_attention": 92.3},
            {"topic": "Writing Essay",       "focused": 900,  "distracted": 900, "avg_attention": 50.0},
            {"topic": "Study Group",         "focused": 1500, "distracted": 400, "avg_attention": 78.9},
        ]

        created_sessions = []

        for i, data in enumerate(test_sessions):
            created_at = datetime.utcnow() - timedelta(days=i)
            completed_at = created_at + timedelta(hours=1)

            session = Session(
                client_id=LOCAL_CLIENT_ID,
                session_topic=data["topic"],
                status=SessionStatus.COMPLETED,
                created_at=created_at,
                completed_at=completed_at,
                seconds_focused=data["focused"],
                seconds_distracted=data["distracted"],
                avg_attention=data["avg_attention"],
            )

            db.add(session)
            db.flush()
            created_sessions.append(session)
            print(f"✅ Created: {session.session_topic} (ID: {session.session_id})")

        db.commit()
        print(f"\n✅ Created {len(created_sessions)} test sessions!")
        return created_sessions

def test_data_retrieval():
    from app.models import Session

    print("\n" + "="*60)
    print("Testing Data Retrieval")
    print("="*60)

    with db_session() as db:
        sessions = db.query(Session).order_by(Session.created_at.desc()).limit(5).all()

        print(f"\nFound {len(sessions)} sessions:")
        for s in sessions:
            print(f"\n  📊 {s.session_topic}")
            print(f"     Focused: {s.seconds_focused}s ({s.seconds_focused//60}m)")
            print(f"     Distracted: {s.seconds_distracted}s ({s.seconds_distracted//60}m)")
            print(f"     Avg Attention: {s.avg_attention}%")
            print(f"     Session ID: {s.session_id}")

        return sessions

def test_visualization_generation(session_id):
    """Test generating a visualization"""
    print("\n" + "="*60)
    print("Testing Visualization Generation")
    print("="*60)
    
    from app.services.visualization_service import visualization_service
    
    with db_session() as db:
        session = db.query(Session).filter(
            Session.session_id == session_id
        ).first()
        
        if not session:
            print("❌ Session not found!")
            return
        
        print(f"\n📊 Generating charts for: {session.session_topic}")
        
        # Test 1: Pie chart
        try:
            print("\n1. Generating pie chart...")
            pie_chart = visualization_service.generate_focus_distribution_chart(
                session.seconds_focused,
                session.seconds_distracted
            )
            print(f"✅ Pie chart generated! Length: {len(pie_chart)} chars")
            print(f"   Preview: {pie_chart[:100]}...")
        except Exception as e:
            print(f"❌ Pie chart failed: {e}")
        
        # Test 2: Bar chart with multiple sessions
        try:
            print("\n2. Generating comparison chart...")
            sessions = db.query(Session).order_by(Session.created_at.desc()).limit(5).all()
            session_data = [
                {
                    "session_topic": s.session_topic,
                    "avg_attention": s.avg_attention,
                    "focused_seconds": s.focused_seconds
                }
                for s in sessions
            ]
            bar_chart = visualization_service.generate_session_comparison_chart(session_data)
            print(f"✅ Bar chart generated! Length: {len(bar_chart)} chars")
            print(f"   Preview: {bar_chart[:100]}...")
        except Exception as e:
            print(f"❌ Bar chart failed: {e}")
        
        # Test 3: Gemini analysis
        try:
            print("\n3. Testing Gemini analysis...")
            data = {
                "focused_seconds": session.seconds_focused,
                "distracted_seconds": session.seconds_distracted,
                "avg_attention": session.avg_attention,
                "topic": session.session_topic
            }
            analysis = visualization_service.analyze_data_with_gemini(
                data,
                "Analyze my focus performance"
            )
            print(f"✅ Gemini analysis complete!")
            print(f"   Chart type: {analysis['chart_type']}")
            print(f"   Title: {analysis['title']}")
            print(f"   Insights:")
            for insight in analysis['insights']:
                print(f"     • {insight}")
        except Exception as e:
            print(f"❌ Gemini analysis failed: {e}")

def cleanup_test_data():
    """Remove test data"""
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)
    
    response = input("\nDo you want to delete the test sessions? (y/n): ")
    
    if response.lower() == 'y':
        with db_session() as db:
            # Delete sessions created in the last hour (our test data)
            count = db.query(Session).filter(
                Session.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).delete()
            db.commit()
            print(f"✅ Deleted {count} test sessions")
    else:
        print("Test data kept in database")

if __name__ == "__main__":
    print("="*60)
    print("VISUALIZATION TESTING SCRIPT")
    print("="*60)
    
    # Step 1: Create test data
    sessions = create_test_data()

    with db_session() as db:
        s = db.query(Session).order_by(Session.created_at.desc()).first()
        print(s.session_topic, s.seconds_focused, s.seconds_distracted, s.avg_attention)
    
    # Step 2: Test retrieval
    retrieved_sessions = test_data_retrieval()
    
    # Step 3: Test visualization generation
    if retrieved_sessions:
        test_visualization_generation(retrieved_sessions[0].session_id)
    
    # Step 4: Cleanup
    cleanup_test_data()
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
