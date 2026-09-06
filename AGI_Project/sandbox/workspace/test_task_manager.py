import os
from task_manager import TaskManager

TEST_FILE = 'test_tasks.json'

def cleanup():
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def run_tests():
    cleanup()
    print('=== Starting TaskManager Tests ===')
    
    # Test 1: Initialization & empty display
    tm = TaskManager(filepath=TEST_FILE)
    assert len(tm.tasks) == 0, 'Test 1 Failed: Task list should be empty initially'
    print('[PASS] Test 1: Empty init')

    # Test 2: Add valid tasks
    assert tm.add_task('Buy groceries') is True
    assert tm.add_task('Read a book') is True
    assert len(tm.tasks) == 2
    assert tm.tasks[0]['title'] == 'Buy groceries' and tm.tasks[0]['completed'] is False
    assert tm.tasks[1]['title'] == 'Read a book' and tm.tasks[1]['completed'] is False
    print('[PASS] Test 2: Add valid tasks')

    # Test 3: Add invalid tasks (empty or whitespace)
    assert tm.add_task('') is False
    assert tm.add_task('   ') is False
    assert len(tm.tasks) == 2
    print('[PASS] Test 3: Reject empty/whitespace task')

    # Test 4: Mark complete
    assert tm.mark_complete(1) is True
    assert tm.tasks[0]['completed'] is True
    # Non-existent ID
    assert tm.mark_complete(99) is False
    # Invalid ID input
    assert tm.mark_complete('invalid_id') is False
    print('[PASS] Test 4: Mark complete (valid, missing, invalid type)')

    # Test 5: Remove task
    assert tm.remove_task(1) is True
    assert len(tm.tasks) == 1
    assert tm.tasks[0]['title'] == 'Read a book'
    assert tm.tasks[0]['id'] == 1  # Reindexed
    # Non-existent ID
    assert tm.remove_task(99) is False
    # Invalid ID type
    assert tm.remove_task('abc') is False
    print('[PASS] Test 5: Remove task & reindexing')

    # Test 6: Persistence test
    tm2 = TaskManager(filepath=TEST_FILE)
    assert len(tm2.tasks) == 1
    assert tm2.tasks[0]['title'] == 'Read a book'
    assert tm2.tasks[0]['completed'] is False
    print('[PASS] Test 6: Persistence verified across instances')

    # Test 7: Corrupt JSON handling
    with open(TEST_FILE, 'w') as f:
        f.write('{ corrupt json')
    tm_corrupt = TaskManager(filepath=TEST_FILE)
    assert tm_corrupt.tasks == []
    print('[PASS] Test 7: Gracefully handled corrupted JSON file')

    cleanup()
    print('=== All Tests Passed Successfully! ===')

if __name__ == '__main__':
    run_tests()
