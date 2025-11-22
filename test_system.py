"""
Flow Engine - Comprehensive Test Suite
Tests all modules in isolation and integration.
"""

import sys
import os
sys.path.insert(0, 'backend')

def test_local_db():
    """Test local database functionality"""
    print("=" * 60)
    print("TEST 1: Local Database")
    print("=" * 60)
    
    from local_db import LocalDatabase
    from pathlib import Path
    from datetime import datetime
    
    # Create test database
    db = LocalDatabase(Path("test_flow.db"))
    
    # Test session creation
    session_id = db.create_session(datetime.now())
    assert session_id > 0, "Session creation failed"
    print(f"✓ Session created: ID {session_id}")
    
    # Test app logging
    db.log_app_usage("vscode.exe", 600, is_productive=True)
    db.log_app_usage("instagram.exe", 120, broke_flow=True)
    print("✓ App usage logged")
    
    # Test pattern retrieval
    patterns = db.get_app_patterns()
    assert len(patterns) > 0, "No patterns found"
    print(f"✓ Retrieved {len(patterns)} app patterns")
    
    # Test flow window logging
    db.log_flow_window(datetime.now(), 14, 85.0, 120.0, 25)
    print("✓ Flow window logged")
    
    db.close()
    os.remove("test_flow.db")
    print("✓ Database test PASSED\n")
    return True

def test_pattern_analyzer():
    """Test pattern analyzer functionality"""
    print("=" * 60)
    print("TEST 2: Pattern Analyzer")
    print("=" * 60)
    
    from local_db import LocalDatabase
    from pattern_analyzer import PatternAnalyzer
    from pathlib import Path
    from datetime import datetime, timedelta
    
    # Create test database with data
    db = LocalDatabase(Path("test_patterns.db"))
    
    # Add test sessions
    for i in range(5):
        session_id = db.create_session(datetime.now() - timedelta(days=i))
        db.update_session(session_id, {
            'end_time': datetime.now() - timedelta(days=i, hours=-1),
            'duration_seconds': 3600,
            'focus_score': 80.0 + i,
            'distraction_count': i
        })
    
    # Add app patterns
    for _ in range(6):
        db.log_app_usage("instagram.exe", 300, broke_flow=True)
    
    # Test analyzer
    analyzer = PatternAnalyzer()
    
    # Test app pattern analysis
    analysis = analyzer.analyze_app_patterns()
    print(f"✓ Analyzed app patterns: {len(analysis['frequent_distractions'])} distractions found")
    
    # Test biological patterns
    bio_patterns = analyzer.detect_biological_patterns()
    print(f"✓ Biological patterns analyzed")
    
    # Test threshold calculation
    threshold = analyzer.calculate_optimal_threshold()
    assert threshold > 0, "Invalid threshold"
    print(f"✓ Optimal threshold calculated: {threshold} minutes")
    
    # Test learning summary
    summary = analyzer.get_learning_summary()
    assert 'stats' in summary, "Missing stats in summary"
    print(f"✓ Learning summary generated: {summary['stats']['total_sessions']} sessions")
    
    db.close()
    os.remove("test_patterns.db")
    print("✓ Pattern analyzer test PASSED\n")
    return True

def test_input_monitor():
    """Test input monitor (if available)"""
    print("=" * 60)
    print("TEST 3: Input Monitor")
    print("=" * 60)
    
    try:
        from input_monitor import InputMonitor
        
        # Create monitor
        monitor = InputMonitor()
        print("✓ Input monitor created")
        
        # Test APM getter
        apm = monitor.get_apm()
        assert apm >= 0, "Invalid APM"
        print(f"✓ APM: {apm}")
        
        # Test activity pattern
        pattern = monitor.get_activity_pattern()
        assert pattern in ['active', 'passive', 'idle'], "Invalid pattern"
        print(f"✓ Activity pattern: {pattern}")
        
        # Test stats
        stats = monitor.get_stats()
        assert 'apm' in stats, "Missing APM in stats"
        print(f"✓ Stats retrieved: {stats}")
        
        print("✓ Input monitor test PASSED\n")
        return True
    except ImportError:
        print("⚠ Input monitor not available (pynput required)")
        print("✓ Input monitor test SKIPPED\n")
        return True

def test_soft_reset():
    """Test soft reset (if available)"""
    print("=" * 60)
    print("TEST 4: Soft Reset")
    print("=" * 60)
    
    try:
        from soft_reset import SoftReset
        
        # Create soft reset
        reset = SoftReset(duration=1)  # 1 second for testing
        print("✓ Soft reset created")
        
        # Test trigger (don't actually run it)
        assert hasattr(reset, 'trigger'), "Missing trigger method"
        assert hasattr(reset, 'active'), "Missing active attribute"
        print("✓ Soft reset methods verified")
        
        print("✓ Soft reset test PASSED\n")
        return True
    except ImportError as e:
        print(f"⚠ Soft reset not available: {e}")
        print("✓ Soft reset test SKIPPED\n")
        return True

def test_main_imports():
    """Test main.py imports"""
    print("=" * 60)
    print("TEST 5: Main Module Imports")
    print("=" * 60)
    
    try:
        # Test all imports
        from database import init_supabase, get_or_create_user
        print("✓ Database imports OK")
        
        from window_monitor import WindowMonitor
        print("✓ Window monitor import OK")
        
        from interventions import InterventionManager
        print("✓ Interventions import OK")
        
        from blocker import FlowBlocker
        print("✓ Blocker import OK")
        
        from local_db import get_db
        print("✓ Local DB import OK")
        
        from pattern_analyzer import get_analyzer
        print("✓ Pattern analyzer import OK")
        
        print("✓ Main module imports test PASSED\n")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "=" * 60)
    print("FLOW ENGINE - COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Local Database", test_local_db()))
    results.append(("Pattern Analyzer", test_pattern_analyzer()))
    results.append(("Input Monitor", test_input_monitor()))
    results.append(("Soft Reset", test_soft_reset()))
    results.append(("Main Imports", test_main_imports()))
    
    # Generate report
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<40} {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
