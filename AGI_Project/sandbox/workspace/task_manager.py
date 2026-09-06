import json
import os

DATA_FILE = 'tasks.json'

class TaskManager:
    def __init__(self, filepath=DATA_FILE):
        self.filepath = filepath
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.tasks = data
                    else:
                        self.tasks = []
            except (json.JSONDecodeError, IOError):
                self.tasks = []
        else:
            self.tasks = []

    def save_tasks(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, indent=4)
            return True
        except IOError as e:
            print(f'Error saving tasks: {e}')
            return False

    def add_task(self, title):
        title = str(title).strip()
        if not title:
            print('Error: Task title cannot be empty.')
            return False
        task = {
            'id': len(self.tasks) + 1,
            'title': title,
            'completed': False
        }
        self.tasks.append(task)
        self._reindex()
        self.save_tasks()
        print(f'Task added: "{title}"')
        return True

    def remove_task(self, task_id):
        try:
            t_id = int(task_id)
        except (ValueError, TypeError):
            print('Error: Invalid task ID. Please provide an integer.')
            return False
        
        for i, task in enumerate(self.tasks):
            if task['id'] == t_id:
                removed = self.tasks.pop(i)
                self._reindex()
                self.save_tasks()
                print(f'Task removed: "{removed["title"]}"')
                return True
        print(f'Error: Task ID {t_id} not found.')
        return False

    def mark_complete(self, task_id):
        try:
            t_id = int(task_id)
        except (ValueError, TypeError):
            print('Error: Invalid task ID. Please provide an integer.')
            return False
        
        for task in self.tasks:
            if task['id'] == t_id:
                task['completed'] = True
                self.save_tasks()
                print(f'Task marked as complete: "{task["title"]}"')
                return True
        print(f'Error: Task ID {t_id} not found.')
        return False

    def display_tasks(self):
        if not self.tasks:
            print('No tasks found.')
            return
        print('\
--- Task List ---')
        for task in self.tasks:
            status = '[X]' if task.get('completed') else '[ ]'
            print(f"{task['id']}. {status} {task['title']}")
        print('-----------------\
')

    def _reindex(self):
        for idx, task in enumerate(self.tasks, start=1):
            task['id'] = idx
